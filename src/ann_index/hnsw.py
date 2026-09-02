"""Cài đặt thuật toán HNSW chuẩn (Hierarchical Navigable Small World Index)."""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from ann_index.base import BaseIndex


class FallbackGraphHNSW:
    """
    Cài đặt đồ thị Small-World thuần túy bằng NumPy và Python.
    Được dùng làm cơ chế dự phòng an toàn khi môi trường không có thư viện C++ hnswlib.
    """

    def __init__(self, dim: int, m: int = 16, ef_construction: int = 100, metric: str = "l2"):
        """
        Khởi tạo đồ thị Small-World dự phòng.

        Tham số:
            dim: Số chiều không gian vector đặc trưng.
            m: Số lượng liên kết tối đa của mỗi nút đỉnh trong đồ thị.
            ef_construction: Kích thước danh sách ứng viên trong quá trình dựng đồ thị.
            metric: Độ đo khoảng cách ('l2' hoặc 'cosine').
        """
        self.dim = dim
        self.m = m
        self.ef_construction = ef_construction
        self.metric = metric
        self.vectors: Optional[np.ndarray] = None
        self.graph: Dict[int, List[int]] = {}
        self.entry_point: int = 0

    def _dist(self, u: np.ndarray, v: np.ndarray) -> float:
        """Tính toán khoảng cách giữa hai vector u và v theo độ đo đã cấu hình."""
        if self.metric == "cosine":
            norm_u = max(float(np.linalg.norm(u)), 1e-12)
            norm_v = max(float(np.linalg.norm(v)), 1e-12)
            return 1.0 - float(np.dot(u, v) / (norm_u * norm_v))
        return float(np.sum((u - v) ** 2))

    def build(self, vectors: np.ndarray) -> None:
        """
        Xây dựng đồ thị liên kết hai chiều (bidirectional k-NN small-world graph) cho tập vector.

        Tham số:
            vectors: Mảng 2 chiều chứa các vector float32.
        """
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        n, _ = self.vectors.shape
        self.graph = {i: [] for i in range(n)}
        self.entry_point = 0

        # Dựng đồ thị kết nối láng giềng gần nhất cho từng đỉnh
        for i in range(n):
            diffs = self.vectors - self.vectors[i]
            dists = np.sum(diffs ** 2, axis=1)
            dists[i] = np.inf  # loại trừ chính bản thân nút đang xét

            k_best = min(self.m, n - 1)
            if k_best > 0:
                nearest = np.argpartition(dists, k_best - 1)[:k_best]
                for nb in nearest:
                    nb_int = int(nb)
                    if nb_int not in self.graph[i]:
                        self.graph[i].append(nb_int)
                    if i not in self.graph[nb_int]:
                        self.graph[nb_int].append(i)

    def search_single(self, query: np.ndarray, top_k: int = 10, ef_search: int = 50) -> Tuple[List[int], List[float]]:
        """
        Tìm kiếm láng giềng gần nhất cho 1 câu truy vấn bằng thuật toán Beam Search trên đồ thị.

        Tham số:
            query: Vector truy vấn float32 1 chiều.
            top_k: Số lượng láng giềng kết quả cần lấy.
            ef_search: Độ rộng chùm tìm kiếm (Beam width).

        Trả về:
            Tuple gồm danh sách chỉ số (indices) và danh sách khoảng cách tương ứng.
        """
        if self.vectors is None or len(self.vectors) == 0:
            return [], []

        n = len(self.vectors)
        entry = self.entry_point
        dist_entry = self._dist(query, self.vectors[entry])

        visited = {entry}
        # Danh sách ưu tiên các ứng viên khám phá: [(dist, node_id), ...]
        candidates = [(dist_entry, entry)]
        # Tập hợp W lưu trữ các nút tốt nhất hiện có kích thước ef_search
        w = [(dist_entry, entry)]
        beam_size = max(ef_search, top_k)

        while candidates:
            candidates.sort(key=lambda x: x[0])
            c_dist, c_node = candidates.pop(0)

            w.sort(key=lambda x: x[0])
            furthest_w_dist = w[-1][0]

            # Dừng nếu khoảng cách ứng viên gần nhất đã vượt quá khoảng cách xa nhất trong tập W
            if c_dist > furthest_w_dist and len(w) >= beam_size:
                break

            for neighbor in self.graph.get(c_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    d = self._dist(query, self.vectors[neighbor])
                    if d < furthest_w_dist or len(w) < beam_size:
                        candidates.append((d, neighbor))
                        w.append((d, neighbor))
                        w.sort(key=lambda x: x[0])
                        if len(w) > beam_size:
                            w.pop()

        w.sort(key=lambda x: x[0])
        top_w = w[:top_k]
        return [idx for _, idx in top_w], [dist for dist, _ in top_w]


class StandardHNSWIndex(BaseIndex):
    """
    Chỉ mục thuật toán HNSW chuẩn.
    Hỗ trợ thư viện gốc C++ hnswlib và tự động chuyển sang đồ thị thuần NumPy dự phòng khi không có C++.
    """

    def __init__(
        self,
        space: str = "l2",
        m: int = 16,
        ef_construction: int = 100,
        ef_search: int = 50,
    ):
        """
        Khởi tạo chỉ mục Standard HNSW.

        Tham số:
            space: Độ đo khoảng cách ('l2', 'ip', hoặc 'cosine').
            m: Số lượng cạnh nối tối đa của mỗi nút đỉnh trong đồ thị.
            ef_construction: Kích thước danh sách ứng viên khi xây dựng đồ thị (càng lớn càng chính xác nhưng lâu hơn).
            ef_search: Kích thước danh sách ứng viên trong pha truy vấn tìm kiếm.
        """
        self.space = space.lower()
        self.m = m
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self._hnswlib_index = None
        self._fallback_index: Optional[FallbackGraphHNSW] = None
        self._num_vectors = 0
        self._dim = 0

    @property
    def name(self) -> str:
        backend = "native" if self._hnswlib_index is not None else "fallback_graph"
        return f"StandardHNSW(m={self.m}, ef={self.ef_search}, backend={backend})"

    def build(self, vectors: np.ndarray) -> None:
        """
        Xây dựng cấu trúc đồ thị HNSW trên mảng vector đầu vào.

        Tham số:
            vectors: Mảng 2 chiều kích thước (N, D).
        """
        if vectors.ndim != 2:
            raise ValueError("Mảng vector đầu vào phải là mảng 2 chiều (N, D)")

        self._num_vectors, self._dim = vectors.shape

        # Thử khởi tạo thông qua thư viện tối ưu hnswlib (C++)
        try:
            import hnswlib
            hnsw_space = "l2" if self.space == "l2" else "cosine"
            self._hnswlib_index = hnswlib.Index(space=hnsw_space, dim=self._dim)
            self._hnswlib_index.init_index(
                max_elements=self._num_vectors,
                ef_construction=self.ef_construction,
                M=self.m,
            )
            self._hnswlib_index.add_items(vectors, np.arange(self._num_vectors))
            self._hnswlib_index.set_ef(self.ef_search)
        except Exception:
            # Tự động kích hoạt cơ chế đồ thị dự phòng thuần Python/NumPy
            self._hnswlib_index = None
            self._fallback_index = FallbackGraphHNSW(
                dim=self._dim,
                m=self.m,
                ef_construction=self.ef_construction,
                metric=self.space,
            )
            self._fallback_index.build(vectors)

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Thực hiện tìm kiếm láng giềng gần đúng Top-K cho một lô vector truy vấn.

        Tham số:
            query_vectors: Mảng vector truy vấn float32 (num_queries, D).
            top_k: Số lượng kết quả cần lấy cho mỗi truy vấn.

        Trả về:
            Tuple (indices, distances) kiểu int64 và float32.
        """
        q = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)

        num_queries, _ = q.shape

        if self._hnswlib_index is not None:
            self._hnswlib_index.set_ef(self.ef_search)
            indices, distances = self._hnswlib_index.knn_query(q, k=top_k)
            return indices.astype(np.int64), distances.astype(np.float32)
        elif self._fallback_index is not None:
            all_indices = []
            all_dists = []
            for i in range(num_queries):
                idx_list, dist_list = self._fallback_index.search_single(
                    q[i], top_k=top_k, ef_search=self.ef_search
                )
                all_indices.append(idx_list)
                all_dists.append(dist_list)
            return np.array(all_indices, dtype=np.int64), np.array(all_dists, dtype=np.float32)
        else:
            raise RuntimeError("Chỉ mục chưa được xây dựng. Hãy gọi build() trước.")

    def get_memory_bytes(self) -> int:
        """
        Tính toán tổng dung lượng bộ nhớ RAM (byte) tiêu thụ gồm mảng vector float32 và bảng liên kết đồ thị.
        Công thức: N * D * 4 bytes (vector) + N * M * 8 bytes (con trỏ cạnh nối).
        """
        vector_bytes = self._num_vectors * self._dim * 4
        links_bytes = self._num_vectors * self.m * 8
        return vector_bytes + links_bytes

