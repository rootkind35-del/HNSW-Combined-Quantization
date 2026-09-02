"""Exact Flat Vector Search module using Cosine / Dot-Product similarity."""

from typing import List, Tuple
import numpy as np


class ExactVectorSearch:
    """Performs exact brute-force k-NN search across vector arrays using Cosine Similarity."""

    def __init__(self, vectors: np.ndarray, normalize: bool = True):
        """
        Args:
            vectors: Matrix of shape (N, D) representing dataset embeddings.
            normalize: If True, applies L2-normalization for cosine similarity computation.
        """
        if vectors.ndim != 2:
            raise ValueError(f"Expected 2D array of vectors, got shape {vectors.shape}")

        self.num_vectors, self.dim = vectors.shape
        self.normalize = normalize

        if self.normalize:
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            # Avoid division by zero for any edge-case zero vectors
            self.vectors = vectors / np.maximum(norms, 1e-12)
        else:
            self.vectors = vectors

    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Finds the top-K most similar vectors to the query.

        Args:
            query_vector: 1D array of shape (D,) or 2D of shape (1, D).
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            List[Tuple[int, float]]: List of (index, similarity_score) sorted descending by score.
        """
        if self.num_vectors == 0:
            return []

        q = query_vector.flatten()
        if q.shape[0] != self.dim:
            raise ValueError(f"Query dimension mismatch: expected {self.dim}, got {q.shape[0]}")

        if self.normalize:
            q_norm = np.linalg.norm(q)
            q = q / max(q_norm, 1e-12)

        # Compute dot product similarity for all N vectors
        scores = np.dot(self.vectors, q)

        actual_k = min(top_k, self.num_vectors)
        if actual_k <= 0:
            return []

        if actual_k < self.num_vectors:
            # Use argpartition for O(N) selection of top candidates
            partition_indices = np.argpartition(-scores, actual_k)[:actual_k]
            # Sort only top candidates in descending order
            sorted_partition = partition_indices[np.argsort(-scores[partition_indices])]
            top_indices = sorted_partition
        else:
            top_indices = np.argsort(-scores)

        results = [(int(idx), float(scores[idx])) for idx in top_indices]
        return results
