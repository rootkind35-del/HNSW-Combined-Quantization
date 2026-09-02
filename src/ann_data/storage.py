"""Memory-mapped binary vector storage module."""

import os
from typing import List, Optional, Tuple
import numpy as np


class MemmapStorage:
    """Manages disk-backed contiguous vector storage using numpy.memmap."""

    def __init__(
        self,
        file_path: str,
        max_records: int,
        dim: int,
        dtype: str = "float32",
        mode: str = "w+",
    ):
        self.file_path = file_path
        self.max_records = max_records
        self.dim = dim
        self.dtype = np.dtype(dtype)
        self.mode = mode
        self.current_count = 0
        
        # Ensure target directory exists
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        self._mmap: Optional[np.memmap] = None
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Initializes the memory-mapped array file."""
        self._mmap = np.memmap(
            self.file_path,
            dtype=self.dtype,
            mode=self.mode,
            shape=(self.max_records, self.dim),
        )

    def append_batch(self, vectors: np.ndarray) -> Tuple[int, int]:
        """
        Appends a batch of vectors to the memory-mapped storage.
        
        Returns:
            Tuple[int, int]: (start_index, end_index) of appended records.
        """
        if self._mmap is None:
            raise RuntimeError("Storage is closed.")

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        num_vectors, vector_dim = vectors.shape
        if vector_dim != self.dim:
            raise ValueError(f"Vector dimension mismatch: expected {self.dim}, got {vector_dim}")

        start_idx = self.current_count
        end_idx = start_idx + num_vectors

        if end_idx > self.max_records:
            raise OverflowError(
                f"Storage capacity exceeded: current {start_idx}, adding {num_vectors}, max {self.max_records}"
            )

        self._mmap[start_idx:end_idx] = vectors.astype(self.dtype)
        self.current_count = end_idx
        self.flush()
        return start_idx, end_idx

    def read_slice(self, start_idx: int, end_idx: int) -> np.ndarray:
        """Reads a slice of vectors from storage."""
        if self._mmap is None:
            raise RuntimeError("Storage is closed.")
        return np.array(self._mmap[start_idx:end_idx])

    def read_indices(self, indices: List[int]) -> np.ndarray:
        """Reads multiple specific vector indices from storage."""
        if self._mmap is None:
            raise RuntimeError("Storage is closed.")
        return np.array(self._mmap[indices])

    def flush(self) -> None:
        """Flushes memory-mapped modifications to physical disk."""
        if self._mmap is not None:
            self._mmap.flush()

    def close(self) -> None:
        """Flushes data and releases the memory-map handle."""
        if self._mmap is not None:
            self._mmap.flush()
            del self._mmap
            self._mmap = None

    def __enter__(self) -> "MemmapStorage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
