"""Direct I/O SSD storage manager and application-level LRU cache for Tier 2 ANN search.

Provides direct binary seek and read without relying on memory-mapped files,
avoiding OS page cache thrashing and virtual memory exhaustion on large datasets.
"""

from collections import OrderedDict
import concurrent.futures
import os
import threading
from typing import Dict, List, Optional
import numpy as np


class ApplicationLRUCache:
    """Application-level Least Recently Used (LRU) cache for float32 vectors.

    Buffers frequently accessed vectors in user space to mitigate OS page thrashing.
    """

    def __init__(self, capacity: int = 10000) -> None:
        """Initialize cache with specified maximum capacity.

        Args:
            capacity: Maximum number of vectors to retain in cache.
        """
        self.capacity = max(1, capacity)
        self.cache: OrderedDict[int, np.ndarray] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: int) -> Optional[np.ndarray]:
        """Retrieve vector by key, updating its recency position.

        Args:
            key: Vector identifier.

        Returns:
            Cached numpy array if found, else None.
        """
        with self._lock:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

    def put(self, key: int, value: np.ndarray) -> None:
        """Insert or update vector in cache, evicting oldest item if at capacity.

        Args:
            key: Vector identifier.
            value: Float32 vector array.
        """
        with self._lock:
            self.cache[key] = value
            self.cache.move_to_end(key)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self.cache)

    def clear(self) -> None:
        """Clear all cached vectors."""
        with self._lock:
            self.cache.clear()


class DirectIOManager:
    """Direct file I/O manager for Tier 2 SSD storage.

    Executes point seeks and reads directly against binary vector files,
    bypassing memory mapping and utilizing ThreadPoolExecutor for asynchronous batching.
    """

    def __init__(self, filepath: str, dim: int = 384, cache_capacity: int = 10000) -> None:
        """Initialize direct I/O manager.

        Args:
            filepath: Path to raw binary storage file.
            dim: Dimensionality of float32 vectors.
            cache_capacity: Size of in-memory LRU cache.
        """
        self.filepath = filepath
        self.dim = dim
        self.vector_bytes = dim * 4  # 4 bytes per float32 component
        self.lru_cache = ApplicationLRUCache(capacity=cache_capacity)

        dirname = os.path.dirname(self.filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)

        if not os.path.exists(self.filepath):
            with open(self.filepath, "wb") as f:
                pass

    def _read_single_vector(self, vector_id: int) -> np.ndarray:
        """Read a single float32 vector directly from binary file via file seek.

        Args:
            vector_id: 0-based vector index in the binary file.

        Returns:
            Numpy float32 array of shape (dim,).
        """
        offset = vector_id * self.vector_bytes
        with open(self.filepath, "rb") as f:
            f.seek(offset)
            raw_data = f.read(self.vector_bytes)

        if len(raw_data) < self.vector_bytes:
            return np.zeros(self.dim, dtype=np.float32)

        return np.frombuffer(raw_data, dtype=np.float32).copy()

    def get_vector(self, vector_id: int) -> np.ndarray:
        """Get vector with LRU caching. Checks cache first, falls back to disk.

        Args:
            vector_id: 0-based vector index.

        Returns:
            Float32 vector array.
        """
        cached = self.lru_cache.get(vector_id)
        if cached is not None:
            return cached

        vec = self._read_single_vector(vector_id)
        self.lru_cache.put(vector_id, vec)
        return vec

    def async_read_batch(self, vector_ids: List[int]) -> Dict[int, np.ndarray]:
        """Read multiple vectors in parallel using thread pool.

        Args:
            vector_ids: List of vector identifiers to retrieve.

        Returns:
            Dictionary mapping vector_id to float32 numpy array.
        """
        if not vector_ids:
            return {}

        results: Dict[int, np.ndarray] = {}
        unique_ids = list(dict.fromkeys(vector_ids))

        # Check in-memory cache first
        missing_ids: List[int] = []
        for vid in unique_ids:
            cached = self.lru_cache.get(vid)
            if cached is not None:
                results[vid] = cached
            else:
                missing_ids.append(vid)

        if not missing_ids:
            return results

        max_workers = min(16, max(1, len(missing_ids)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {executor.submit(self.get_vector, vid): vid for vid in missing_ids}
            for future in concurrent.futures.as_completed(future_to_id):
                vid = future_to_id[future]
                results[vid] = future.result()

        return results

    def write_vector(self, vector: np.ndarray) -> int:
        """Append a single float32 vector to storage file.

        Args:
            vector: Array of shape (dim,).

        Returns:
            Appended vector index (0-based).
        """
        vec_float = np.asarray(vector, dtype=np.float32).flatten()
        if len(vec_float) != self.dim:
            raise ValueError(f"Vector dim {len(vec_float)} does not match manager dim {self.dim}")

        with open(self.filepath, "ab") as f:
            pos = f.tell()
            vec_float.tofile(f)

        idx = pos // self.vector_bytes
        self.lru_cache.put(idx, vec_float)
        return idx

    def write_batch(self, vectors: np.ndarray) -> List[int]:
        """Append multiple vectors in batch to storage file.

        Args:
            vectors: 2D array of shape (N, dim).

        Returns:
            List of 0-based vector indices.
        """
        arr = np.asarray(vectors, dtype=np.float32)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] != self.dim:
            raise ValueError(f"Vector dim {arr.shape[1]} does not match manager dim {self.dim}")

        with open(self.filepath, "ab") as f:
            start_pos = f.tell()
            arr.tofile(f)

        start_idx = start_pos // self.vector_bytes
        indices = [start_idx + i for i in range(len(arr))]
        for idx, vec in zip(indices, arr):
            self.lru_cache.put(idx, vec)
        return indices
