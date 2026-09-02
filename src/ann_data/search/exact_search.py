"""Module tìm kiếm vector vét cạn chính xác tuyệt đối (Exact Flat Search) dựa trên độ tương đồng Cosine."""

from typing import List, Tuple
import numpy as np


class ExactVectorSearch:
    """
    Tìm kiếm k láng giềng gần nhất chính xác tuyệt đối (Brute-force k-NN):
    Sử dụng tích vô hướng sau chuẩn hóa L2 (Cosine Similarity) để làm mốc so sánh Ground Truth
    hoặc phục vụ tìm kiếm chính xác trên tập dữ liệu vừa và nhỏ.
    """

    def __init__(self, vectors: np.ndarray, normalize: bool = True):
        """
        Khởi tạo đối tượng tìm kiếm chính xác.

        Tham số:
            vectors: Ma trận vector kích thước (N, D) biểu diễn tập dữ liệu.
            normalize: Nếu True, áp dụng chuẩn hóa độ dài L2 để tích vô hướng tương đương Cosine Similarity.
        """
        if vectors.ndim != 2:
            raise ValueError(f"Kỳ vọng mảng vector 2 chiều, nhận được kích thước {vectors.shape}")

        self.num_vectors, self.dim = vectors.shape
        self.normalize = normalize

        if self.normalize:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            # Tránh chia cho 0 đối với các vector toàn số 0
            self.vectors = vectors / np.maximum(norms, 1e-12)
        else:
            self.vectors = vectors

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Tìm kiếm Top-K vector có độ tương đồng ngữ nghĩa cao nhất với vector truy vấn.

        Tham số:
            query_vector: Mảng 1 chiều (D,) hoặc 2 chiều (1, D).
            top_k: Số lượng láng giềng cần lấy ra.

        Trả về:
            List[Tuple[int, float]]: Danh sách cặp (chỉ_số, điểm_tương_đồng) sắp xếp giảm dần theo điểm số.
        """
        if self.num_vectors == 0:
            return []

        q = query_vector.flatten()
        if q.shape[0] != self.dim:
            raise ValueError(f"Lệch số chiều truy vấn: kỳ vọng {self.dim}, nhận được {q.shape[0]}")

        if self.normalize:
            q_norm = np.linalg.norm(q)
            q = q / max(q_norm, 1e-12)

        # Tính tích vô hướng giữa toàn bộ N vector dữ liệu và vector truy vấn q
        scores = np.dot(self.vectors, q)

        actual_k = min(top_k, self.num_vectors)
        if actual_k <= 0:
            return []

        if actual_k < self.num_vectors:
            # Sử dụng argpartition độ phức tạp O(N) để lọc ra Top-K ứng viên lớn nhất
            partition_indices = np.argpartition(-scores, actual_k)[:actual_k]
            # Sắp xếp cục bộ K ứng viên này theo thứ tự giảm dần
            sorted_partition = partition_indices[np.argsort(-scores[partition_indices])]
            top_indices = sorted_partition
        else:
            top_indices = np.argsort(-scores)

        results = [(int(idx), float(scores[idx])) for idx in top_indices]
        return results

