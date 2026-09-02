"""Abstract base class for vector approximate nearest neighbor index structures."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class BaseIndex(ABC):
    """Abstract interface defining required methods for any k-NN index implementation."""

    @abstractmethod
    def build(self, vectors: np.ndarray) -> None:
        """
        Builds or populates the search index using the provided dataset vectors.

        Args:
            vectors: 2D float array of shape (N, D).
        """
        pass

    @abstractmethod
    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Performs nearest neighbor search for a batch of query vectors.

        Args:
            query_vectors: 2D float array of shape (num_queries, D).
            top_k: Number of nearest neighbors to return per query.

        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - indices: 2D integer array of shape (num_queries, top_k)
                - distances: 2D float array of shape (num_queries, top_k)
        """
        pass

    @abstractmethod
    def get_memory_bytes(self) -> int:
        """Returns approximate RAM footprint in bytes."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns readable identifier name for the algorithm configuration."""
        pass
