"""Công cụ tìm kiếm ngữ nghĩa thông minh (Semantic Search Engine) kết hợp chỉ mục vector và siêu dữ liệu (metadata)."""

import json
import os
from typing import Any, Dict, List, Optional
import numpy as np
from ann_data.cleaner import TextCleaner
from ann_data.embedder import BaseEmbedder, SentenceTransformerEmbedder
from ann_data.search.exact_search import ExactVectorSearch
from ann_data.tokenizer import BaseTokenizer, PyViTokenizer
from ann_data.utils import get_logger


class SemanticSearchEngine:
    """
    Trình điều phối tìm kiếm ngữ nghĩa toàn diện:
    1. Tiền xử lý và tách từ câu truy vấn tiếng Việt.
    2. Sinh vector nhúng truy vấn qua mô hình ngôn ngữ sâu (MiniLM).
    3. Tìm kiếm láng giềng k-NN trên mảng vector ánh xạ bộ nhớ Memmap.
    4. Ánh xạ chỉ số kết quả với siêu dữ liệu JSONL (tiêu đề, bài viết, trích đoạn) để trả về cho người dùng.
    """

    def __init__(
        self,
        vector_file: str,
        metadata_file: str,
        embedder: Optional[BaseEmbedder] = None,
        cleaner: Optional[TextCleaner] = None,
        tokenizer: Optional[BaseTokenizer] = None,
        dim: int = 384,
    ):
        """
        Khởi tạo động cơ tìm kiếm ngữ nghĩa.

        Tham số:
            vector_file: Đường dẫn tệp nhị phân chứa vector (.dat).
            metadata_file: Đường dẫn tệp siêu dữ liệu JSONL chứa thông tin bài báo (.jsonl).
            embedder: Đối tượng mô hình sinh vector nhúng.
            cleaner: Đối tượng làm sạch văn bản tiếng Việt.
            tokenizer: Đối tượng tách từ ghép tiếng Việt.
            dim: Số chiều không gian vector (mặc định 384).
        """
        self.vector_file = vector_file
        self.metadata_file = metadata_file
        self.dim = dim
        self.logger = get_logger("SemanticSearchEngine")

        self.cleaner = cleaner or TextCleaner()
        self.tokenizer = tokenizer or PyViTokenizer()
        self.embedder = embedder or SentenceTransformerEmbedder(dim=self.dim)

        self.metadata: List[Dict[str, Any]] = []
        self.is_large_metadata: bool = False
        self.is_int8: bool = False
        self.num_records: int = 0
        self.scales: Optional[np.ndarray] = None
        self.raw_mmap: Optional[np.memmap] = None
        self.index: Optional[ExactVectorSearch] = None

        self._load_metadata()
        self._load_vector_index()

    def _load_metadata(self) -> None:
        """Đọc và nạp siêu dữ liệu từ tệp JSONL với cơ chế kiểm soát dung lượng bộ nhớ."""
        if not os.path.exists(self.metadata_file):
            raise FileNotFoundError(f"Không tìm thấy tệp siêu dữ liệu: {self.metadata_file}")

        file_size_mb = os.path.getsize(self.metadata_file) / (1024 * 1024)
        if file_size_mb <= 50:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        self.metadata.append(json.loads(stripped))
            self.logger.info("Đã nạp %d bản ghi siêu dữ liệu từ %s", len(self.metadata), self.metadata_file)
        else:
            self.is_large_metadata = True
            self.logger.info("Tệp siêu dữ liệu dung lượng lớn (%.1f MB). Kích hoạt cơ chế trích xuất tuyến tính on-demand.", file_size_mb)

    def _load_vector_index(self) -> None:
        """Đọc tệp nhị phân vector từ đĩa SSD qua ánh xạ memmap và khởi tạo chỉ mục tìm kiếm."""
        if not os.path.exists(self.vector_file):
            raise FileNotFoundError(f"Không tìm thấy tệp vector: {self.vector_file}")

        file_bytes = os.path.getsize(self.vector_file)
        if "int8" in os.path.basename(self.vector_file) or (file_bytes % (self.dim * 4) != 0 and file_bytes % self.dim == 0):
            self.is_int8 = True
            self.num_records = file_bytes // (self.dim * 1)
            self.dtype = "int8"
        else:
            self.is_int8 = False
            self.num_records = file_bytes // (self.dim * 4)
            self.dtype = "float32"

        if self.num_records == 0:
            raise ValueError("Tập vector rỗng, không thể khởi tạo chỉ mục.")

        self.raw_mmap = np.memmap(
            self.vector_file,
            dtype=self.dtype,
            mode="r",
            shape=(self.num_records, self.dim),
        )

        if not self.is_int8 and self.num_records <= 500000:
            vectors = np.array(self.raw_mmap)
            self.index = ExactVectorSearch(vectors=vectors, normalize=True)

        params_file = os.path.join(os.path.dirname(self.vector_file), "quantization_params.json")
        if self.is_int8 and os.path.exists(params_file):
            try:
                with open(params_file, "r", encoding="utf-8") as f:
                    params = json.load(f)
                    self.scales = np.array(params.get("scales", []), dtype=np.float32)
            except Exception:
                self.scales = None

        self.logger.info("Khởi tạo xong chỉ mục vector (%d vector, %d chiều, kiểu %s)", self.num_records, self.dim, self.dtype)

    def get_metadata_for_indices(self, indices: List[int]) -> Dict[int, Dict[str, Any]]:
        """Truy xuất siêu dữ liệu cho danh sách chỉ số vector cần hiển thị."""
        if not self.is_large_metadata and self.metadata:
            return {idx: (self.metadata[idx] if idx < len(self.metadata) else {}) for idx in indices}

        results = {}
        target_set = set(indices)
        if not target_set:
            return results

        max_target = max(target_set)
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            for cur_idx, line in enumerate(f):
                if cur_idx in target_set:
                    results[cur_idx] = json.loads(line)
                if cur_idx >= max_target:
                    break
        return results

    def search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Thực thi tìm kiếm ngữ nghĩa cho câu truy vấn văn bản tự nhiên.

        Tham số:
            query_text: Chuỗi truy vấn văn bản (ví dụ: "giá xăng dầu hôm nay").
            top_k: Số lượng kết quả gần nhất cần truy xuất.

        Trả về:
            Danh sách kết quả bài viết kèm thứ hạng (rank), điểm tương đồng (score), tiêu đề và trích đoạn xem trước.
        """
        if not query_text or not query_text.strip():
            return []

        cleaned_query = self.cleaner.clean(query_text)
        tokenized_query = self.tokenizer.tokenize(cleaned_query)

        # Sinh vector biểu diễn ngữ nghĩa cho câu truy vấn
        query_vectors = self.embedder.encode([tokenized_query])
        if len(query_vectors) == 0:
            return []

        query_vector = query_vectors[0].astype(np.float32)
        norm = np.linalg.norm(query_vector)
        if norm > 1e-12:
            query_vector = query_vector / norm

        if self.is_int8:
            q_scaled = (query_vector * self.scales) if self.scales is not None else query_vector
            chunk_size = 500000
            candidates = []
            cand_scores = []
            for start in range(0, self.num_records, chunk_size):
                end = min(start + chunk_size, self.num_records)
                chunk = self.raw_mmap[start:end].astype(np.float32)
                scores = np.dot(chunk, q_scaled)
                k = min(top_k, len(scores))
                part = np.argpartition(scores, -k)[-k:]
                candidates.extend(start + part)
                cand_scores.extend(scores[part])

            cand_indices = np.array(candidates)
            cand_scores = np.array(cand_scores)
            best = np.argsort(cand_scores)[::-1][:top_k]
            raw_results = [(int(cand_indices[i]), float(cand_scores[i])) for i in best]
        else:
            if self.index is None:
                self.index = ExactVectorSearch(vectors=np.array(self.raw_mmap), normalize=True)
            raw_results = self.index.search(query_vector=query_vector, top_k=top_k)

        target_indices = [idx for idx, _ in raw_results]
        meta_dict = self.get_metadata_for_indices(target_indices)

        enriched_results = []
        for rank, (idx, score) in enumerate(raw_results, start=1):
            meta = meta_dict.get(idx, {})
            preview_text = meta.get("preview") or meta.get("text", "")
            enriched_results.append({
                "rank": rank,
                "vector_idx": idx,
                "score": round(score, 4),
                "title": meta.get("title", "N/A"),
                "preview": preview_text[:200],
                "doc_id": meta.get("doc_id", ""),
            })

        return enriched_results

