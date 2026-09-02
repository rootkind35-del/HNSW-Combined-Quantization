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
        self._load_metadata()

        self.index: Optional[ExactVectorSearch] = None
        self._load_vector_index()

    def _load_metadata(self) -> None:
        """Đọc và nạp toàn bộ các bản ghi siêu dữ liệu từ tệp JSONL vào bộ nhớ."""
        if not os.path.exists(self.metadata_file):
            raise FileNotFoundError(f"Không tìm thấy tệp siêu dữ liệu: {self.metadata_file}")

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    self.metadata.append(json.loads(stripped))

        self.logger.info("Đã nạp %d bản ghi siêu dữ liệu từ %s", len(self.metadata), self.metadata_file)

    def _load_vector_index(self) -> None:
        """Đọc tệp nhị phân vector từ đĩa SSD qua ánh xạ memmap và khởi tạo chỉ mục tìm kiếm."""
        if not os.path.exists(self.vector_file):
            raise FileNotFoundError(f"Không tìm thấy tệp vector: {self.vector_file}")

        num_records = len(self.metadata)
        if num_records == 0:
            raise ValueError("Tập siêu dữ liệu rỗng, không thể ánh xạ vector tương ứng.")

        # Đọc lát cắt dữ liệu vector thực tế trên đĩa SSD
        raw_mmap = np.memmap(
            self.vector_file,
            dtype="float32",
            mode="r",
            shape=(num_records, self.dim),
        )
        vectors = np.array(raw_mmap)
        del raw_mmap

        self.index = ExactVectorSearch(vectors=vectors, normalize=True)
        self.logger.info("Khởi tạo xong chỉ mục tìm kiếm vector với kích thước (%d, %d)", num_records, self.dim)

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

        query_vector = query_vectors[0]
        raw_results = self.index.search(query_vector=query_vector, top_k=top_k)

        enriched_results = []
        for rank, (idx, score) in enumerate(raw_results, start=1):
            meta = self.metadata[idx] if idx < len(self.metadata) else {}
            enriched_results.append({
                "rank": rank,
                "vector_idx": idx,
                "score": round(score, 4),
                "title": meta.get("title", "N/A"),
                "preview": meta.get("preview", ""),
                "doc_id": meta.get("doc_id", ""),
            })

        return enriched_results

