"""Chỉ mục tìm kiếm vét cạn chính xác (Exact Brute-force Flat k-NN Index) dùng làm mốc chuẩn (Ground Truth)."""

from typing import Optional, Tuple
import numpy as np
from ann_index.base import BaseIndex


class FlatIndex(BaseIndex):
    """
    Thuật toán tìm kiếm láng giềng gần nhất chính xác tuyệt đối bằng phương pháp vét cạn (Brute-force).
    Tính toán toàn bộ khoảng cách cặp đôi giữa từng vector truy vấn và toàn bộ vector trong cơ sở dữ liệu.
    """

    def __init__(self, metric: str = "l2"):
        """
        Khởi tạo chỉ mục Flat.

        Tham số:
            metric: Độ đo khoảng cách, hỗ trợ 'l2' (khoảng cách Euclid) hoặc 'cosine'.
        """
        if metric.lower() not in ["l2", "cosine", "ip"]:
            raise ValueError(f"Không hỗ trợ độ đo: {metric}. Vui lòng chọn 'l2' hoặc 'cosine'.")
        self.metric = metric.lower()
        self.vectors: Optional[np.ndarray] = None
        self.norms_sq: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return f"FlatIndex(metric={self.metric})"

    def build(self, vectors: np.ndarray) -> None:
        """
        Lưu trữ mảng vector dữ liệu float32 và tính toán trước các chuẩn vector để tăng tốc.

        Tham số:
            vectors: Mảng 2 chiều kích thước (N, D).
        """
        if vectors.ndim != 2:
            raise ValueError("Mảng vector đầu vào phải là mảng 2 chiều (N, D)")

        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        if self.metric == "cosine":
            # Chuẩn hóa L2 trước để chuyển tích vô hướng thành độ đo Cosine
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
            self.vectors = self.vectors / np.maximum(norms, 1e-12)
        elif self.metric == "l2":
            # Tính trước ||v||^2 để áp dụng khai triển ma trận: ||q - v||^2 = ||q||^2 + ||v||^2 - 2 * q.v^T
            self.norms_sq = np.sum(self.vectors ** 2, axis=1)

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Tìm kiếm vét cạn Top-K láng giềng gần nhất cho lô vector truy vấn.

        Tham số:
            query_vectors: Mảng vector truy vấn (num_queries, D).
            top_k: Số lượng láng giềng cần lấy.

        Trả về:
            Tuple (indices, distances) kiểu int64 và float32.
        """
        if self.vectors is None:
            raise RuntimeError("Chỉ mục chưa được xây dựng. Hãy gọi build() trước.")

        q = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)

        num_queries, query_dim = q.shape
        num_dataset, dataset_dim = self.vectors.shape

        if query_dim != dataset_dim:
            raise ValueError(f"Lỗi lệch số chiều: vector truy vấn có {query_dim} chiều, tập dữ liệu có {dataset_dim} chiều")

        k = min(top_k, num_dataset)
        if k <= 0:
            return np.empty((num_queries, 0), dtype=np.int64), np.empty((num_queries, 0), dtype=np.float32)

        if self.metric == "cosine":
            # Chuẩn hóa vector truy vấn và tính khoảng cách Cosine: 1.0 - dot_product
            q_norms = np.linalg.norm(q, axis=1, keepdims=True)
            q_normed = q / np.maximum(q_norms, 1e-12)
            sims = np.dot(q_normed, self.vectors.T)
            distances = 1.0 - sims
        else:
            # Khai triển khoảng cách L2 bình phương bằng phép nhân ma trận BLAS nhanh
            q_sq = np.sum(q ** 2, axis=1, keepdims=True)
            distances = q_sq + self.norms_sq - 2.0 * np.dot(q, self.vectors.T)
            # Khắc phục sai số dấu phẩy động nhỏ gây ra giá trị âm
            distances = np.maximum(distances, 0.0)

        # Lọc ra Top-K khoảng cách nhỏ nhất
        if k < num_dataset:
            # Sử dụng argpartition độ phức tạp O(N) thay vì sắp xếp toàn bộ O(N log N)
            candidate_indices = np.argpartition(distances, k, axis=1)[:, :k]
            row_indices = np.arange(num_queries)[:, None]
            candidate_dists = distances[row_indices, candidate_indices]
            sort_order = np.argsort(candidate_dists, axis=1)
            final_indices = candidate_indices[row_indices, sort_order]
            final_distances = candidate_dists[row_indices, sort_order]
        else:
            final_indices = np.argsort(distances, axis=1)[:, :k]
            row_indices = np.arange(num_queries)[:, None]
            final_distances = distances[row_indices, final_indices]

        return final_indices.astype(np.int64), final_distances.astype(np.float32)

    def generate_ground_truth(self, query_vectors: np.ndarray, top_k: int = 10) -> np.ndarray:
        """Sinh ma trận Ground Truth chỉ số láng giềng kích thước (num_queries, top_k)."""
        indices, _ = self.search(query_vectors, top_k=top_k)
        return indices

    def get_memory_bytes(self) -> int:
        """Trả về tổng dung lượng RAM (byte) đang dùng để lưu mảng vector và bộ đệm chuẩn."""
        if self.vectors is None:
            return 0
        total = self.vectors.nbytes
        if self.norms_sq is not None:
            total += self.norms_sq.nbytes
        return total

