"""Kịch bản xử lý luồng dữ liệu ngữ liệu lớn (Large-scale Streaming Pipeline) từ Hugging Face kết hợp lưu trữ Memmap và Checkpoint."""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.cleaner import TextCleaner
from ann_data.deduplicator import StreamDeduplicator
from ann_data.embedder import BatchEmbedder, MockEmbedder, SentenceTransformerEmbedder
from ann_data.loaders.hf_loader import HuggingFaceLoader
from ann_data.storage import MemmapStorage
from ann_data.tokenizer import WhitespaceTokenizer
from ann_data.utils import get_logger


class CheckpointManager:
    """
    Quản lý điểm kiểm tra tiến độ (Checkpoint):
    Lưu trữ trạng thái số lượng bản ghi đã xử lý, ID tài liệu cuối cùng và số lượng bản ghi trùng lặp
    để hỗ trợ tiếp tục (resume) quá trình xử lý 10 triệu bản ghi mà không phải chạy lại từ đầu khi xảy ra sự cố.
    """

    def __init__(self, checkpoint_file: str):
        """Khởi tạo bộ quản lý điểm kiểm tra với đường dẫn tệp JSON."""
        self.checkpoint_file = checkpoint_file

    def load(self) -> Dict[str, Any]:
        """Đọc trạng thái đã lưu từ tệp JSON."""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"processed_count": 0, "last_doc_id": "", "duplicates_filtered": 0}

    def save(self, processed_count: int, last_doc_id: str, duplicates_filtered: int) -> None:
        """Ghi trạng thái hiện tại xuống tệp JSON trên đĩa."""
        os.makedirs(os.path.dirname(os.path.abspath(self.checkpoint_file)), exist_ok=True)
        data = {
            "processed_count": processed_count,
            "last_doc_id": last_doc_id,
            "duplicates_filtered": duplicates_filtered,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(self.checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)




def run_large_scale_streaming(
    target_count: int = 1000,
    batch_size: int = 200,
    dataset_name: str = "bkai-foundation-models/vi-corpus",
    output_vector_path: str = "data/processed/hf_large_vectors.dat",
    output_meta_path: str = "data/processed/hf_large_metadata.jsonl",
    checkpoint_file: str = "data/processed/hf_stream_checkpoint.json",
    resume: bool = False,
    use_mock_embedder: bool = False,
) -> Dict[str, Any]:
    """
    Thực thi Pipeline xử lý luồng quy mô lớn với bộ nhớ RAM cố định và cơ chế lưu điểm kiểm tra.

    Tham số:
        target_count: Số lượng bản ghi mục tiêu cần nạp và nhúng.
        batch_size: Kích thước lô trước khi xả ghi vào memmap và đĩa.
        dataset_name: Tên tập dữ liệu trên Hugging Face.
        output_vector_path: Đường dẫn tệp nhị phân vector memmap.
        output_meta_path: Đường dẫn tệp siêu dữ liệu JSONL.
        checkpoint_file: Đường dẫn tệp lưu checkpoint.
        resume: Nếu True, tiếp tục xử lý từ vị trí checkpoint gần nhất.
        use_mock_embedder: Sử dụng vector giả lập để đo đạc thông lượng đường ống I/O.

    Trả về:
        Dict chứa các chỉ số đo lường hiệu năng tổng thể.
    """
    logger = get_logger("stream_hf_large_scale")
    os.makedirs(os.path.dirname(os.path.abspath(output_vector_path)), exist_ok=True)

    ckpt_mgr = CheckpointManager(checkpoint_file)
    ckpt_data = ckpt_mgr.load() if resume else {"processed_count": 0, "last_doc_id": "", "duplicates_filtered": 0}

    already_processed = ckpt_data["processed_count"]
    duplicates_filtered = ckpt_data["duplicates_filtered"]

    logger.info("Khởi tạo Pipeline xử lý luồng quy mô lớn:")
    logger.info("  Bản ghi mục tiêu: %d | Kích thước lô: %d | Chế độ tiếp tục: %s", target_count, batch_size, resume)
    logger.info("  Đã xử lý trước đó: %d | Trùng lặp đã lọc: %d", already_processed, duplicates_filtered)

    # 1. Khởi tạo các thành phần đường ống
    cleaner = TextCleaner()
    tokenizer = WhitespaceTokenizer()
    dedup = StreamDeduplicator(threshold=0.8, num_perm=128)

    dim = 384
    if use_mock_embedder:
        embedder = MockEmbedder(dim=dim)
    else:
        try:
            embedder = SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2")
            dim = embedder.dim
        except Exception:
            logger.warning("Không thể nạp SentenceTransformer. Chuyển sang MockEmbedder.")
            embedder = MockEmbedder(dim=dim)

    # Khởi tạo bộ lưu trữ đĩa Memmap
    mode = "r+" if (resume and os.path.exists(output_vector_path)) else "w+"
    capacity = max(target_count, 20000)
    storage = MemmapStorage(
        file_path=output_vector_path,
        max_records=capacity,
        dim=dim,
        dtype="float32",
        mode=mode,
    )
    if resume and already_processed > 0:
        storage.current_count = already_processed

    # 2. Mở tệp ghi siêu dữ liệu
    meta_mode = "a" if resume else "w"
    meta_file = open(output_meta_path, meta_mode, encoding="utf-8")

    batch_texts: List[str] = []
    batch_metadata: List[Dict[str, Any]] = []

    start_time = time.perf_counter()
    records_added = 0
    items_scanned = 0

    # Danh sách các nguồn ngữ liệu Hugging Face tiếng Việt lớn
    sources = [
        {"dataset_name": "wikimedia/wikipedia", "config_name": "20231101.vi", "text_column": "text"},
        {"dataset_name": "oscar-corpus/OSCAR-2201", "config_name": "unshuffled_deduplicated_vi", "text_column": "text"},
        {"dataset_name": "cc100", "config_name": "vi", "text_column": "text"},
        {"dataset_name": "bkai-foundation-models/vi-corpus", "config_name": None, "text_column": "text"}
    ]

    def multi_source_generator():
        for source in sources:
            loader = HuggingFaceLoader(
                dataset_name=source["dataset_name"],
                config_name=source["config_name"],
                text_column=source["text_column"],
                streaming=True
            )
            logger.info(f"Đang đọc luồng từ: {source['dataset_name']} (cấu hình: {source['config_name']})")
            yield from loader.stream(limit=target_count * 3)
        logger.info("Hoàn tất quét toàn bộ các nguồn ngữ liệu Hugging Face.")

    stream_iter = multi_source_generator()

    try:
        for item in stream_iter:
            items_scanned += 1

            # Bỏ qua các mục đã được xử lý trong checkpoint trước đó
            if resume and items_scanned <= already_processed:
                continue

            if isinstance(item, tuple):
                doc_id, raw_text = item
            elif isinstance(item, dict):
                doc_id = item.get("id", str(items_scanned))
                raw_text = item.get("text", "")
            else:
                continue

            cleaned = cleaner.clean(raw_text)
            if len(cleaned) < 30:
                continue

            tokens = tokenizer.tokenize(cleaned)
            is_dup = dedup.is_duplicate(doc_id, cleaned)
            if is_dup:
                duplicates_filtered += 1
                continue

            # Mẫu hợp lệ mới
            batch_texts.append(cleaned)
            batch_metadata.append({
                "doc_id": doc_id or f"doc_{already_processed + records_added}",
                "title": cleaned[:80].replace("\n", " "),
                "token_count": len(tokens),
            })
            records_added += 1

            # Xả ghi lô khi đủ kích thước
            if len(batch_texts) >= batch_size:
                vectors = embedder.encode(batch_texts)
                storage.append_batch(vectors)

                for meta in batch_metadata:
                    meta_file.write(json.dumps(meta, ensure_ascii=False) + "\n")
                meta_file.flush()

                total_saved = already_processed + records_added
                ckpt_mgr.save(total_saved, batch_metadata[-1]["doc_id"], duplicates_filtered)

                elapsed = time.perf_counter() - start_time
                throughput = records_added / max(elapsed, 0.001)
                logger.info(
                    "Đã ghi lô: Tổng %d / %d bản ghi (Tốc độ: %.1f docs/s, Đã lọc trùng: %d)",
                    total_saved,
                    target_count,
                    throughput,
                    duplicates_filtered,
                )

                batch_texts.clear()
                batch_metadata.clear()

            if (already_processed + records_added) >= target_count:
                break

        # Xả phần vector còn dư cuối cùng
        if batch_texts:
            vectors = embedder.encode(batch_texts)
            storage.append_batch(vectors)
            for meta in batch_metadata:
                meta_file.write(json.dumps(meta, ensure_ascii=False) + "\n")
            meta_file.flush()

            total_saved = already_processed + records_added
            ckpt_mgr.save(total_saved, batch_metadata[-1]["doc_id"], duplicates_filtered)
            batch_texts.clear()
            batch_metadata.clear()

    finally:
        meta_file.close()
        storage.close()

    total_time = time.perf_counter() - start_time
    final_count = already_processed + records_added
    file_size_mb = os.path.getsize(output_vector_path) / (1024 * 1024)

    logger.info("=== STREAMING HOÀN TẤT ===")
    logger.info("  Tổng số vector ghi đĩa: %d", final_count)
    logger.info("  Thời gian thực thi: %.2f giây (Tốc độ TB: %.1f docs/s)", total_time, records_added / max(total_time, 0.001))
    logger.info("  Dung lượng file nhị phân memmap: %.2f MB", file_size_mb)
    logger.info("  Số tài liệu trùng lặp đã loại bỏ: %d", duplicates_filtered)

    return {
        "final_count": final_count,
        "total_time_sec": round(total_time, 2),
        "docs_per_sec": round(records_added / max(total_time, 0.001), 1),
        "file_size_mb": round(file_size_mb, 2),
        "duplicates_filtered": duplicates_filtered,
        "vector_path": output_vector_path,
        "meta_path": output_meta_path,
    }


def main():
    """Hàm chạy dòng lệnh chính."""
    parser = argparse.ArgumentParser(description="Hệ thống xử lý luồng dữ liệu quy mô lớn từ Hugging Face.")
    parser.add_argument("--target-count", type=int, default=1000, help="Số lượng bản ghi mục tiêu cần nạp")
    parser.add_argument("--batch-size", type=int, default=200, help="Kích thước lô xả ghi memmap")
    parser.add_argument("--dataset-name", type=str, default="bkai-foundation-models/vi-corpus", help="Tên ngữ liệu Hugging Face")
    parser.add_argument("--output-vector", type=str, default="data/processed/hf_large_vectors.dat", help="Đường dẫn tệp vector memmap")
    parser.add_argument("--output-meta", type=str, default="data/processed/hf_large_metadata.jsonl", help="Đường dẫn tệp siêu dữ liệu JSONL")
    parser.add_argument("--checkpoint-file", type=str, default="data/processed/hf_stream_checkpoint.json", help="Đường dẫn tệp checkpoint")
    parser.add_argument("--resume", action="store_true", help="Tiếp tục xử lý từ checkpoint gần nhất")
    parser.add_argument("--mock-embedder", action="store_true", help="Sử dụng MockEmbedder để đo kiểm thông lượng đĩa")
    args = parser.parse_args()

    run_large_scale_streaming(
        target_count=args.target_count,
        batch_size=args.batch_size,
        dataset_name=args.dataset_name,
        output_vector_path=args.output_vector,
        output_meta_path=args.output_meta,
        checkpoint_file=args.checkpoint_file,
        resume=args.resume,
        use_mock_embedder=args.mock_embedder,
    )


if __name__ == "__main__":
    main()

