"""Exact Brute-force Flat k-NN Index for Ground Truth generation."""

from typing import Optional, Tuple
import numpy as np
from ann_index.base import BaseIndex


class FlatIndex(BaseIndex):
    """Exact brute-force nearest neighbor search computing all pairwise distances."""

    def __init__(self, metric: str = "l2"):
        """
        Args:
            metric: Distance metric, either 'l2' (Euclidean distance) or 'cosine'.
        """
        if metric.lower() not in ["l2", "cosine", "ip"]:
            raise ValueError(f"Unsupported metric: {metric}. Expected 'l2' or 'cosine'.")
        self.metric = metric.lower()
        self.vectors: Optional[np.ndarray] = None
        self.norms_sq: Optional[np.ndarray] = None

    @property
    def name(self) -> str:
        return f"FlatIndex(metric={self.metric})"

    def build(self, vectors: np.ndarray) -> None:
        """Loads and stores vectors in float32 for brute-force computation."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array (N, D)")

        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        if self.metric == "cosine":
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
            self.vectors = self.vectors / np.maximum(norms, 1e-12)
        elif self.metric == "l2":
            # Precompute squared norms for fast L2 matrix multiplication
            self.norms_sq = np.sum(self.vectors ** 2, axis=1)

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Searches nearest neighbors across all stored vectors."""
        if self.vectors is None:
            raise RuntimeError("Index has not been built. Call build() first.")

        q = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)

        num_queries, query_dim = q.shape
        num_dataset, dataset_dim = self.vectors.shape

        if query_dim != dataset_dim:
            raise ValueError(f"Dimension mismatch: query has {query_dim}, dataset has {dataset_dim}")

        k = min(top_k, num_dataset)
        if k <= 0:
            return np.empty((num_queries, 0), dtype=np.int64), np.empty((num_queries, 0), dtype=np.float32)

        if self.metric == "cosine":
            q_norms = np.linalg.norm(q, axis=1, keepdims=True)
            q_normed = q / np.maximum(q_norms, 1e-12)
            # Dot products range [-1, 1]
            sims = np.dot(q_normed, self.vectors.T)
            # Cosine distance = 1.0 - similarity
            distances = 1.0 - sims
        else:
            # L2 squared distance: ||q - v||^2 = ||q||^2 + ||v||^2 - 2 * q . v^T
            q_sq = np.sum(q ** 2, axis=1, keepdims=True)
            distances = q_sq + self.norms_sq - 2.0 * np.dot(q, self.vectors.T)
            # Clip numerical precision negatives
            distances = np.maximum(distances, 0.0)

        # Retrieve top k smallest distances
        if k < num_dataset:
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
        """Returns only the nearest neighbor indices matrix of shape (num_queries, top_k)."""
        indices, _ = self.search(query_vectors, top_k=top_k)
        return indices

    def get_memory_bytes(self) -> int:
        """Returns byte size of the vector store."""
        if self.vectors is None:
            return 0
        total = self.vectors.nbytes
        if self.norms_sq is not None:
            total += self.norms_sq.nbytes
        return total
