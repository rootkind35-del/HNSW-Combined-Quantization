"""Product Quantization (PQ) module with Asymmetric Distance Computation (ADC)."""

from typing import Optional
import numpy as np


class ProductQuantizer:
    """
    Decomposes D-dimensional vectors into M orthogonal sub-spaces and quantizes each
    sub-vector into 1-byte codebook indices.
    """

    def __init__(self, num_subvectors: int = 8, num_clusters: int = 256, max_iter: int = 15):
        """
        Args:
            num_subvectors: Number of sub-vector partitions M.
            num_clusters: Number of centroids per subspace codebook (max 256 for 1-byte uint8).
            max_iter: Max iterations for K-Means training.
        """
        if num_clusters > 256:
            raise ValueError("num_clusters cannot exceed 256 for 1-byte uint8 representation")

        self.num_subvectors = num_subvectors
        self.num_clusters = num_clusters
        self.max_iter = max_iter
        self.dim: int = 0
        self.sub_dim: int = 0
        self.codebooks: Optional[np.ndarray] = None  # Shape: (M, num_clusters, sub_dim)
        self.is_fitted: bool = False

    def _fast_kmeans(self, data: np.ndarray, k: int) -> np.ndarray:
        """Lightweight and robust K-Means clustering in pure NumPy."""
        n, d = data.shape
        actual_k = min(k, n)
        if actual_k <= 1:
            return np.mean(data, axis=0, keepdims=True)

        # Initialize centroids randomly without replacement
        init_indices = np.random.choice(n, size=actual_k, replace=False)
        centroids = np.copy(data[init_indices])

        for _ in range(self.max_iter):
            # Compute Euclidean distances to centroids: (N, K)
            diffs = data[:, np.newaxis, :] - centroids[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            labels = np.argmin(dists, axis=1)

            new_centroids = np.zeros_like(centroids)
            for c in range(actual_k):
                mask = (labels == c)
                if np.any(mask):
                    new_centroids[c] = np.mean(data[mask], axis=0)
                else:
                    # Re-initialize empty cluster to random sample
                    new_centroids[c] = data[np.random.randint(0, n)]

            # Check convergence
            if np.allclose(centroids, new_centroids, atol=1e-4):
                break
            centroids = new_centroids

        # If actual_k < k, pad centroids to k by replicating
        if actual_k < k:
            repeats = int(np.ceil(k / actual_k))
            centroids = np.tile(centroids, (repeats, 1))[:k]

        return centroids.astype(np.float32)

    def fit(self, vectors: np.ndarray) -> "ProductQuantizer":
        """Fits independent codebooks for each sub-vector space."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be 2D array of shape (N, D)")

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
        """Encodes float32 vectors into uint8 PQ code matrix of shape (N, M)."""
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("ProductQuantizer must be fitted before encoding")

        n = len(vectors)
        codes = np.zeros((n, self.num_subvectors), dtype=np.uint8)

        for m in range(self.num_subvectors):
            start_col = m * self.sub_dim
            end_col = (m + 1) * self.sub_dim if m < self.num_subvectors - 1 else self.dim
            sub_slice = vectors[:, start_col:end_col]  # (N, sub_dim)
            cb = self.codebooks[m]  # (K, sub_dim)

            # Distances from sub_slice to codebook centroids: (N, K)
            diffs = sub_slice[:, np.newaxis, :] - cb[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            codes[:, m] = np.argmin(dists, axis=1).astype(np.uint8)

        return codes

    def decode(self, codes: np.ndarray) -> np.ndarray:
        """Reconstructs approximate float32 vectors from PQ codes."""
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("ProductQuantizer must be fitted before decoding")

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
        Computes Look-up Table (LUT) of shape (M, num_clusters) measuring distances
        from query sub-vectors to all codebook centroids.
        """
        if not self.is_fitted or self.codebooks is None:
            raise RuntimeError("ProductQuantizer must be fitted before computing distance table")

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
        Computes Asymmetric Distance Computation (ADC) between query and encoded dataset
        using precalculated LUT: sum_{m} LUT[m, codes[i, m]].
        """
        m_range = np.arange(self.num_subvectors)
        return np.sum(lut[m_range, codes], axis=1).astype(np.float32)
