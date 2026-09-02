"""Cài đặt thuật toán IVF-PQ (Inverted File with Product Quantization Index)."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from ann_index.base import BaseIndex
from ann_index.pq import ProductQuantizer


class IVFPQIndex(BaseIndex):
    """
    Chỉ mục IVF-PQ (Inverted File kết hợp Product Quantization):
    Thuật toán đối chuẩn kinh điển kết hợp phân vùng thô Voronoi (danh sách đảo Inverted Lists)
    với nén lượng tử hóa tích trên vector phần dư (residuals).
    Giúp giảm mạnh dung lượng RAM nhưng độ chính xác Recall bị suy giảm do sai số phân cụm ở vùng biên.
    """

    def __init__(
        self,
        nlist: int = 16,
        num_subvectors: int = 8,
        nprobe: int = 4,
        metric: str = "l2",
    ):
        """
        Khởi tạo chỉ mục IVF-PQ.

        Tham số:
            nlist: Số lượng ô phân vùng Voronoi thô (số danh sách đảo inverted lists).
            num_subvectors: Số lượng không gian con M để lượng tử hóa tích PQ.
            nprobe: Số lượng tâm cụm gần nhất được thăm dò (probe) trong quá trình truy vấn.
            metric: Độ đo khoảng cách ('l2' hoặc 'cosine').
        """
        self.nlist = nlist
        self.num_subvectors = num_subvectors
        self.nprobe = nprobe
        self.metric = metric.lower()

        self.pq = ProductQuantizer(num_subvectors=self.num_subvectors, num_clusters=256)
        self.coarse_centroids: Optional[np.ndarray] = None  # Tâm cụm phân vùng thô: (nlist, D)
        self.inverted_lists: Dict[int, Dict[str, np.ndarray]] = {}
        self.num_vectors: int = 0
        self.dim: int = 0

    @property
    def name(self) -> str:
        return f"IVF-PQ(nlist={self.nlist}, m={self.num_subvectors}, nprobe={self.nprobe})"

    def _train_coarse_centroids(self, vectors: np.ndarray, k: int) -> np.ndarray:
        """
        Huấn luyện các tâm cụm thô Voronoi bằng giải thuật K-Means.

        Tham số:
            vectors: Mảng vector đầu vào float32 (N, D).
            k: Số lượng tâm cụm thô cần huấn luyện.

        Trả về:
            Mảng tâm cụm kích thước (k, D) kiểu float32.
        """
        n, d = vectors.shape
        actual_k = min(k, n)
        init_idx = np.random.choice(n, size=actual_k, replace=False)
        centroids = np.copy(vectors[init_idx])

        for _ in range(15):
            diffs = vectors[:, np.newaxis, :] - centroids[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            labels = np.argmin(dists, axis=1)

            new_c = np.zeros_like(centroids)
            for c in range(actual_k):
                mask = (labels == c)
                if np.any(mask):
                    new_c[c] = np.mean(vectors[mask], axis=0)
                else:
                    new_c[c] = vectors[np.random.randint(0, n)]

            if np.allclose(centroids, new_c, atol=1e-4):
                break
            centroids = new_c

        return centroids.astype(np.float32)

    def build(self, vectors: np.ndarray) -> None:
        """
        Xây dựng cấu trúc chỉ mục IVF-PQ:
        1. Huấn luyện tâm cụm thô Voronoi.
        2. Gán từng vector vào tâm cụm gần nhất.
        3. Tính vector phần dư: r_i = v_i - coarse_centroid.
        4. Huấn luyện bộ lượng tử hóa tích PQ trên vector phần dư và mã hóa thành uint8.
        5. Đưa mã uint8 vào các danh sách đảo tương ứng.

        Tham số:
            vectors: Mảng 2 chiều kích thước (N, D).
        """
        if vectors.ndim != 2:
            raise ValueError("Mảng vector đầu vào phải là mảng 2 chiều (N, D)")

        self.num_vectors, self.dim = vectors.shape
        v = np.ascontiguousarray(vectors, dtype=np.float32)

        # 1. Huấn luyện các tâm cụm thô
        self.coarse_centroids = self._train_coarse_centroids(v, self.nlist)
        actual_nlist = len(self.coarse_centroids)

        # 2. Gán các vector vào tâm cụm thô gần nhất
        diffs = v[:, np.newaxis, :] - self.coarse_centroids[np.newaxis, :, :]
        dists = np.sum(diffs ** 2, axis=2)
        assigned_labels = np.argmin(dists, axis=1)

        # 3. Tính toán vector phần dư (residuals)
        residuals = v - self.coarse_centroids[assigned_labels]

        # 4. Huấn luyện bộ lượng tử hóa tích PQ trên phần dư và mã hóa
        self.pq.fit(residuals)
        all_codes = self.pq.encode(residuals)

        # 5. Lưu vào danh sách đảo Inverted Lists
        self.inverted_lists = {}
        for c in range(actual_nlist):
            cluster_mask = np.where(assigned_labels == c)[0]
            if len(cluster_mask) > 0:
                self.inverted_lists[c] = {
                    "ids": cluster_mask.astype(np.int64),
                    "codes": all_codes[cluster_mask],
                }
            else:
                self.inverted_lists[c] = {
                    "ids": np.empty(0, dtype=np.int64),
                    "codes": np.empty((0, self.num_subvectors), dtype=np.uint8),
                }

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Thực hiện tìm kiếm khoảng cách bất đối xứng ADC qua nprobe danh sách đảo gần nhất.

        Tham số:
            query_vectors: Lô vector truy vấn float32 (num_queries, D).
            top_k: Số lượng láng giềng kết quả cần lấy.

        Trả về:
            Tuple (indices, distances) kiểu int64 và float32.
        """
        if self.coarse_centroids is None or not self.inverted_lists:
            raise RuntimeError("Chỉ mục chưa được xây dựng. Hãy gọi build() trước.")

        q_float = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q_float.ndim == 1:
            q_float = q_float.reshape(1, -1)

        num_queries, _ = q_float.shape
        actual_nprobe = min(self.nprobe, len(self.coarse_centroids))

        all_indices = []
        all_distances = []

        for i in range(num_queries):
            q = q_float[i]

            # 1. Tìm nprobe tâm cụm thô gần nhất với truy vấn
            dists_to_centroids = np.sum((self.coarse_centroids - q) ** 2, axis=1)
            probe_clusters = np.argpartition(dists_to_centroids, actual_nprobe - 1)[:actual_nprobe]

            candidate_ids = []
            candidate_dists = []

            # 2. Thăm dò các danh sách đảo được chọn
            for c in probe_clusters:
                inv = self.inverted_lists[c]
                if len(inv["ids"]) == 0:
                    continue

                # Vector phần dư của truy vấn so với tâm cụm: r_q = q - centroid
                r_q = q - self.coarse_centroids[c]

                # Tính trước bảng tra LUT cho cụm này
                lut = self.pq.compute_distance_table(r_q)

                # Tính khoảng cách ADC nhanh qua tra bảng LUT
                dists_c = self.pq.asymmetric_distance(lut, inv["codes"])

                candidate_ids.append(inv["ids"])
                candidate_dists.append(dists_c)

            if not candidate_ids:
                all_indices.append(np.full(top_k, -1, dtype=np.int64))
                all_distances.append(np.full(top_k, np.inf, dtype=np.float32))
                continue

            merged_ids = np.concatenate(candidate_ids)
            merged_dists = np.concatenate(candidate_dists)

            # 3. Trích xuất Top-K nhỏ nhất
            k_ret = min(top_k, len(merged_dists))
            best_idx = np.argpartition(merged_dists, k_ret - 1)[:k_ret]
            sorted_order = best_idx[np.argsort(merged_dists[best_idx])]

            res_ids = merged_ids[sorted_order]
            res_dists = merged_dists[sorted_order]

            if len(res_ids) < top_k:
                pad_len = top_k - len(res_ids)
                res_ids = np.pad(res_ids, (0, pad_len), constant_values=-1)
                res_dists = np.pad(res_dists, (0, pad_len), constant_values=np.inf)

            all_indices.append(res_ids)
            all_distances.append(res_dists)

        return np.array(all_indices, dtype=np.int64), np.array(all_distances, dtype=np.float32)

    def get_memory_bytes(self) -> int:
        """
        Tính toán tổng dung lượng bộ nhớ RAM tiêu thụ:
        Tâm cụm thô + Từ điển PQ + Danh sách đảo (mã uint8 + mảng ID int64).
        """
        actual_nlist = len(self.coarse_centroids) if self.coarse_centroids is not None else self.nlist
        coarse_bytes = actual_nlist * self.dim * 4
        # Kích thước từ điển: M * 256 * sub_dim * 4 bytes = 256 * D * 4 bytes
        codebook_bytes = 256 * self.dim * 4
        # Kích thước danh sách đảo: N * M (uint8) + N * 8 (int64 IDs)
        lists_bytes = self.num_vectors * (self.num_subvectors * 1 + 8)
        return coarse_bytes + codebook_bytes + lists_bytes

