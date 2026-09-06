"""Pipeline lượng tử hóa: Đọc dữ liệu toàn văn từ data/crawl/ và xuất sang data/quantized/."""

import glob
import json
import os
import time
from typing import Any, Dict, List, Optional
import numpy as np
from quantizer.chunker import TextChunker
from quantizer.sq8 import ScalarQuantizer8
from quantizer.storage import QuantizedStorage
from ann_data.embedder import BatchEmbedder, MockEmbedder, SentenceTransformerEmbedder
from ann_data.utils import get_logger

logger = get_logger("quantizer.pipeline")


class QuantizationPipeline:
    """Điều phối toàn bộ quy trình: Đọc dữ liệu cào toàn văn -> Chia đoạn -> Nhúng vector -> Lượng tử hóa int8 -> Lưu đĩa."""

    def __init__(
        self,
        input_dir: str = "data/crawl",
        output_dir: str = "data/quantized",
        dim: int = 384,
        batch_size: int = 512,
        use_mock_embedder: bool = False,
    ):
        self.input_dir = os.path.abspath(input_dir)
        self.output_dir = os.path.abspath(output_dir)
        self.dim = dim
        self.batch_size = batch_size
        self.chunker = TextChunker(chunk_size=300, chunk_overlap=50)
        self.quantizer = ScalarQuantizer8()

        if use_mock_embedder or dim != 384:
            self.embedder = MockEmbedder(dim=self.dim)
        else:
            try:
                self.embedder = SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2")
                self.dim = self.embedder.dim
            except Exception:
                logger.warning("Không thể tải SentenceTransformer. Tự động chuyển sang MockEmbedder.")
                self.embedder = MockEmbedder(dim=self.dim)

    def process(self, limit: Optional[int] = None, resume: bool = True) -> Dict[str, Any]:
        """
        Thực hiện toàn bộ quá trình lượng tử hóa từ các tệp shard trong data/crawl/.
        Hỗ trợ cơ chế checkpoint tự phục hồi và tiếp tục xử lý (resumable processing).

        Tham số:
            limit: Giới hạn số lượng đoạn văn bản tối đa cần lượng tử hóa.
            resume: Nếu True, tự động tiếp tục từ shard đã hoàn tất trước đó nếu có checkpoint.
        """
        shard_files = sorted(glob.glob(os.path.join(self.input_dir, "shard_*.jsonl")))
        if not shard_files:
            logger.warning("Không tìm thấy tệp shard nào trong: %s", self.input_dir)
            return {"total_vectors": 0}

        logger.info("Tìm thấy %d tệp shard trong %s. Bắt đầu xử lý...", len(shard_files), self.input_dir)

        start_time = time.perf_counter()
        checkpoint_file = os.path.join(self.output_dir, "checkpoint.json")
        completed_shards = set()
        total_passages = 0

        # Kiểm tra checkpoint nếu ở chế độ resume
        if resume and os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    ckpt = json.load(f)
                    completed_shards = set(ckpt.get("completed_shards", []))
                    total_passages = ckpt.get("total_vectors", 0)
                    logger.info("Tìm thấy checkpoint: %d shard đã xử lý, %d vector đã lượng tử hóa.", len(completed_shards), total_passages)
            except Exception as e:
                logger.warning("Không thể đọc checkpoint (%s). Khởi tạo lại tiến trình.", str(e))
                completed_shards = set()
                total_passages = 0

        # Ước lượng sức chứa Memmap
        capacity = max(limit * 2, 1000) if limit else 10000000
        mode = "a" if (completed_shards and os.path.exists(os.path.join(self.output_dir, "vectors_int8.dat"))) else "w+"
        storage = QuantizedStorage(output_dir=self.output_dir, dim=self.dim, max_capacity=capacity)
        storage.initialize_storage(mode=mode)

        try:
            # 1. Xác định tham số thang đo SQ8
            if os.path.exists(storage.params_file) and completed_shards:
                try:
                    with open(storage.params_file, "r", encoding="utf-8") as f:
                        params = json.load(f)
                        self.quantizer.load_params(params)
                        logger.info("Đã nạp tham số SQ8 có sẵn từ: %s", storage.params_file)
                except Exception:
                    completed_shards.clear()

            if not self.quantizer.is_fitted:
                logger.info("Đang trích mẫu để xác định tham số thang đo lượng tử hóa (Fitting SQ8)...")
                sample_texts = []
                for s_file in shard_files:
                    with open(s_file, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                item = json.loads(line)
                                chunks = self.chunker.chunk_document(item["doc_id"], item["title"], item["content_full"])
                                for c in chunks:
                                    sample_texts.append(c["text"])
                                    if len(sample_texts) >= 500:
                                        break
                            if len(sample_texts) >= 500:
                                break
                    if len(sample_texts) >= 500:
                        break

                if not sample_texts:
                    logger.error("Dữ liệu thô rỗng, không thể lượng tử hóa.")
                    return {"total_vectors": 0}

                sample_vecs = self.embedder.encode(sample_texts)
                self.quantizer.fit(sample_vecs)
                storage.save_quantization_params(self.quantizer.export_params())
                logger.info("Đã hoàn tất xác định tham số SQ8 trên %d mẫu vector.", len(sample_texts))

            batch_texts: List[str] = []
            batch_meta: List[Dict[str, Any]] = []

            # 2. Xử lý chính từng shard
            shards_to_process = [sf for sf in shard_files if os.path.basename(sf) not in completed_shards]
            total_remaining = len(shards_to_process)
            logger.info("Còn lại %d / %d shard cần xử lý.", total_remaining, len(shard_files))

            for shard_idx, s_file in enumerate(shards_to_process, 1):
                s_name = os.path.basename(s_file)
                s_start = time.perf_counter()
                shard_count = 0

                with open(s_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue

                        doc = json.loads(line)
                        chunks = self.chunker.chunk_document(doc["doc_id"], doc["title"], doc["content_full"])

                        for chunk in chunks:
                            batch_texts.append(chunk["text"])
                            batch_meta.append({
                                "doc_id": chunk["doc_id"],
                                "chunk_id": chunk["chunk_id"],
                                "title": chunk["title"],
                                "text": chunk["text"],
                                "token_count": chunk["token_count"],
                            })

                            if len(batch_texts) >= self.batch_size:
                                float_vecs = self.embedder.encode(batch_texts, batch_size=self.batch_size)
                                int8_vecs = self.quantizer.quantize(float_vecs)
                                storage.append_batch(int8_vecs, batch_meta, flush=False)

                                total_passages += len(batch_texts)
                                shard_count += len(batch_texts)
                                batch_texts = []
                                batch_meta = []

                                if limit and total_passages >= limit:
                                    break

                        if limit and total_passages >= limit:
                            break

                # Xả nốt dữ liệu còn dư trong shard
                if batch_texts and (not limit or total_passages < limit):
                    float_vecs = self.embedder.encode(batch_texts, batch_size=self.batch_size)
                    int8_vecs = self.quantizer.quantize(float_vecs)
                    storage.append_batch(int8_vecs, batch_meta, flush=False)
                    total_passages += len(batch_texts)
                    shard_count += len(batch_texts)
                    batch_texts = []
                    batch_meta = []

                # Xả bộ đệm đĩa và ghi nhận checkpoint cho shard
                storage.flush_buffers()
                completed_shards.add(s_name)
                s_elapsed = time.perf_counter() - s_start
                s_speed = shard_count / max(s_elapsed, 0.001)

                # Lưu checkpoint
                with open(checkpoint_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "completed_shards": sorted(list(completed_shards)),
                        "total_vectors": total_passages,
                        "last_shard": s_name,
                        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }, f, indent=2)

                storage.update_manifest()

                logger.info(
                    "[%d/%d] Shard %s: %d vector trong %.1fs (%.0f vecs/s) | Tổng cộng: %d vector",
                    len(completed_shards),
                    len(shard_files),
                    s_name,
                    shard_count,
                    s_elapsed,
                    s_speed,
                    total_passages,
                )

                if limit and total_passages >= limit:
                    logger.info("Đã đạt giới hạn %d vector theo yêu cầu.", limit)
                    break
        finally:
            storage.close()

        elapsed = time.perf_counter() - start_time
        logger.info(
            "Hoàn tất lượng tử hóa toàn bộ %d vector int8 vào %s trong %.2f giây (Tốc độ trung bình: %.1f vecs/s).",
            total_passages,
            self.output_dir,
            elapsed,
            total_passages / max(elapsed, 0.001),
        )

        return {
            "total_vectors": total_passages,
            "output_dir": self.output_dir,
            "elapsed_seconds": round(elapsed, 2),
        }

    def process_vector_file(
        self,
        vector_file_path: str,
        limit: Optional[int] = None,
        batch_size: int = 50000,
    ) -> Dict[str, Any]:
        """
        Lượng tử hóa trực tiếp tệp vector nhị phân thô (float32 memmap) thành int8 memmap.
        Hỗ trợ quy mô 10 triệu vector mà không gây tràn bộ nhớ RAM.
        """
        if not os.path.exists(vector_file_path):
            raise FileNotFoundError(f"Không tìm thấy tệp vector: {vector_file_path}")

        file_bytes = os.path.getsize(vector_file_path)
        total_vectors_in_file = file_bytes // (self.dim * 4)
        if total_vectors_in_file == 0:
            raise ValueError(f"Tệp vector rỗng hoặc không hợp lệ: {vector_file_path}")

        total_vectors = min(limit, total_vectors_in_file) if limit else total_vectors_in_file
        logger.info(
            "Phát hiện tệp vector nhị phân: %s (%d vector, chiều: %d, dung lượng: %.2f GB)",
            vector_file_path,
            total_vectors,
            self.dim,
            file_bytes / (1024**3),
        )

        start_time = time.perf_counter()
        raw_mmap = np.memmap(
            vector_file_path,
            dtype="float32",
            mode="r",
            shape=(total_vectors_in_file, self.dim),
        )

        # 1. Trích mẫu để fit SQ8 (50.000 vector mẫu)
        sample_size = min(50000, total_vectors)
        logger.info("Đang trích %d vector mẫu để xác định tham số SQ8...", sample_size)
        sample_indices = np.linspace(0, total_vectors - 1, sample_size, dtype=int)
        sample_vecs = raw_mmap[sample_indices]

        self.quantizer.fit(sample_vecs)
        params = self.quantizer.export_params()

        # 2. Khởi tạo QuantizedStorage với sức chứa tương ứng
        storage = QuantizedStorage(
            output_dir=self.output_dir,
            dim=self.dim,
            max_capacity=total_vectors,
        )
        storage.initialize_storage(mode="w+")
        storage.save_quantization_params(params)

        # 3. Lượng tử hóa theo từng lô lớn (mặc định 50.000 vector/lô)
        processed = 0
        for start_idx in range(0, total_vectors, batch_size):
            end_idx = min(start_idx + batch_size, total_vectors)
            float_batch = raw_mmap[start_idx:end_idx]
            int8_batch = self.quantizer.quantize(float_batch)
            storage.append_batch(int8_batch)
            processed += len(float_batch)

            if processed % 500000 == 0 or processed == total_vectors:
                pct = (processed / total_vectors) * 100.0
                elapsed = time.perf_counter() - start_time
                speed = processed / max(elapsed, 0.001)
                logger.info(
                    "Tiến độ lượng tử hóa: %.1f%% (%d / %d) - Tốc độ: %.0f vecs/s",
                    pct,
                    processed,
                    total_vectors,
                    speed,
                )

        storage.close()
        elapsed = time.perf_counter() - start_time
        logger.info(
            "Hoàn tất lượng tử hóa %d vector sang int8 tại %s trong %.2f giây.",
            processed,
            self.output_dir,
            elapsed,
        )
        return {
            "total_vectors": processed,
            "output_dir": self.output_dir,
            "elapsed_seconds": round(elapsed, 2),
        }
