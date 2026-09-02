"""Module Lượng tử hóa tích (Product Quantization - PQ) và tính toán khoảng cách bất đối xứng (ADC)."""

from typing import Optional
import numpy as np


class ProductQuantizer:
    """
    Bộ lượng tử hóa tích (Product Quantization - PQ):
    Chia không gian vector D chiều thành M không gian con trực giao (sub-spaces)
    và lượng tử hóa từng vector con thành 1 chỉ số từ điển (codebook centroid) dạng uint8 (1 byte).
    """

    def __init__(self, num_subvectors: int = 8, num_clusters: int = 256, max_iter: int = 15):
        """
        Khởi tạo bộ lượng tử hóa PQ.

        Tham số:
            num_subvectors: Số lượng không gian con M (mặc định 8).
            num_clusters: Số lượng tâm cụm trong mỗi từ điển con (tối đa 256 để biểu diễn vừa 1 byte uint8).
            max_iter: Số vòng lặp K-Means tối đa để huấn luyện từ điển.
        """
        if num_clusters > 256:
            raise ValueError("num_clusters không được vượt quá 256 khi biểu diễn bằng kiểu uint8 1-byte")

        self.num_subvectors = num_subvectors
        self.num_clusters = num_clusters
        self.max_iter = max_iter
        self.dim: int = 0
        self.sub_dim: int = 0
        self.codebooks: Optional[np.ndarray] = None  # Ma trận từ điển: (M, num_clusters, sub_dim)
        self.is_fitted: bool = False

    def _fast_kmeans(self, data: np.ndarray, k: int) -> np.ndarray:
        """
        Thuật toán phân cụm K-Means nhanh thuần NumPy để tìm các tâm cụm đại diện cho không gian con.

        Tham số:
            data: Mảng dữ liệu các vector con (N, sub_dim).
            k: Số lượng tâm cụm cần tìm.

        Trả về:
            Mảng tâm cụm kích thước (k, sub_dim) kiểu float32.
        """
        n, d = data.shape
        actual_k = min(k, n)
        if actual_k <= 1:
            return np.mean(data, axis=0, keepdims=True)

        # Khởi tạo ngẫu nhiên các tâm cụm ban đầu không lặp lại
        init_indices = np.random.choice(n, size=actual_k, replace=False)
        centroids = np.copy(data[init_indices])

        for _ in range(self.max_iter):
            # Tính khoảng cách Euclid tới các tâm cụm: (N, K)
            diffs = data[:, np.newaxis, :] - centroids[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            labels = np.argmin(dists, axis=1)

            new_centroids = np.zeros_like(centroids)
            for c in range(actual_k):
                mask = (labels == c)
                if np.any(mask):
                    new_centroids[c] = np.mean(data[mask], axis=0)
                else:
                    # Khởi tạo lại cụm rỗng bằng một mẫu ngẫu nhiên
                    new_centroids[c] = data[np.random.randint(0, n)]

            # Kiểm tra hội tụ sớm
            if np.allclose(centroids, new_centroids, atol=1e-4):
                break
            centroids = new_centroids

        # Bù đủ k tâm cụm nếu actual_k < k
        if actual_k < k:
            repeats = int(np.ceil(k / actual_k))
            centroids = np.tile(centroids, (repeats, 1))[:k]

        return centroids.astype(np.float32)

    def fit(self, vectors: np.ndarray) -> "ProductQuantizer":
        """
        Huấn luyện các bộ từ điển K-Means độc lập cho từng không gian con.

        Tham số:
            vectors: Mảng vector đầu vào 2 chiều (N, D).

        Trả về:
            Chính đối tượng ProductQuantizer đã được huấn luyện.
        """
        if vectors.ndim != 2:
            raise ValueError("Mảng vector phải là mảng 2 chiều kích thước (N, D)")

        self.dim = vectors.shape[1]
        self.sub_dim = max(1, self.dim // self.num_subvectors)

        all_codebooks = []
        for m in range(self.num_subvectors):
            start_col = m * self.sub_dim
            end_col = (m + 1) * self.sub_dim if m < self.num_subvectors - 1 else self.dim
            sub_slice = vectors[:, start_col:end_col]

            cb_m = self._fast_kmeans(sub_slice, self.num_clusters)
            all_codebooks.append(cb_m)

        self.codebooks = np.array(all_codebooks, dtype=np.float32)
        self.is_fitted = True
        return self

    def encode(self, vectors: np.ndarray) -> np.ndarray:
        """
        Mã hóa các vector float32 thành ma trận mã PQ dạng uint8 kích thước (N, M).

        Tham số:
            vectors: Mảng vector float32 (N, D).

        Trả về:
            Mảng mã PQ kích thước (N, M) kiểu np.uint8.
        """
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("Cần gọi phương thức fit() trước khi mã hóa vector")

        n = len(vectors)
        codes = np.zeros((n, self.num_subvectors), dtype=np.uint8)

        for m in range(self.num_subvectors):
            start_col = m * self.sub_dim
            end_col = (m + 1) * self.sub_dim if m < self.num_subvectors - 1 else self.dim
            sub_slice = vectors[:, start_col:end_col]  # (N, sub_dim)
            cb = self.codebooks[m]  # (K, sub_dim)

            # Tính khoảng cách từ từng vector con tới các tâm cụm: (N, K)
            diffs = sub_slice[:, np.newaxis, :] - cb[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            codes[:, m] = np.argmin(dists, axis=1).astype(np.uint8)

        return codes

    def decode(self, codes: np.ndarray) -> np.ndarray:
        """
        Giải mã và tái tạo lại các vector xấp xỉ kiểu float32 từ ma trận mã PQ.

        Tham số:
            codes: Ma trận mã PQ kiểu uint8 kích thước (N, M).

        Trả về:
            Mảng vector float32 xấp xỉ kích thước (N, D).
        """
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("Cần gọi phương thức fit() trước khi giải mã PQ")

        n = len(codes)
        reconstructed = np.zeros((n, self.dim), dtype=np.float32)

        for m in range(self.num_subvectors):
            start_col = m * self.sub_dim
            end_col = (m + 1) * self.sub_dim if m < self.num_subvectors - 1 else self.dim
            cb = self.codebooks[m]
            reconstructed[:, start_col:end_col] = cb[codes[:, m]]

        return reconstructed

    def compute_distance_table(self, query_vector: np.ndarray) -> np.ndarray:
        """
        Tính bảng tra khoảng cách Look-up Table (LUT) kích thước (M, num_clusters)
        lưu khoảng cách từ từng vector con của truy vấn tới toàn bộ tâm cụm trong từ điển.

        Tham số:
            query_vector: Vector truy vấn float32.

        Trả về:
            Bảng tra LUT kích thước (M, num_clusters) kiểu float32.
        """
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("Cần gọi fit() trước khi tính bảng tra khoảng cách LUT")

        lut = np.zeros((self.num_subvectors, self.num_clusters), dtype=np.float32)
        q = query_vector.flatten()

        for m in range(self.num_subvectors):
            start_col = m * self.sub_dim
            end_col = (m + 1) * self.sub_dim if m < self.num_subvectors - 1 else self.dim
            sub_q = q[start_col:end_col]
            cb = self.codebooks[m]
            lut[m] = np.sum((cb - sub_q) ** 2, axis=1)

        return lut

    def asymmetric_distance(self, lut: np.ndarray, codes: np.ndarray) -> np.ndarray:
        """
        Tính khoảng cách bất đối xứng (Asymmetric Distance Computation - ADC)
        giữa vector truy vấn liên tục và tập dữ liệu đã nén mã PQ qua bảng tra LUT:
        d(q, x) = sum_{m=1}^M LUT[m, codes[i, m]].

        Tham số:
            lut: Bảng tra khoảng cách kích thước (M, num_clusters).
            codes: Ma trận mã PQ kiểu uint8 kích thước (N, M).

        Trả về:
            Mảng 1 chiều chứa khoảng cách ADC xấp xỉ tới từng bản ghi.
        """
        m_range = np.arange(self.num_subvectors)
        return np.sum(lut[m_range, codes], axis=1).astype(np.float32)

