"""Standard HNSW (Hierarchical Navigable Small World) Index implementation."""

from typing import Dict, List, Optional, Set, Tuple
import numpy as np
from ann_index.base import BaseIndex


class FallbackGraphHNSW:
    """Pure NumPy/Python Small-World Graph index as a resilient fallback when C++ bindings are unavailable."""

    def __init__(self, dim: int, m: int = 16, ef_construction: int = 100, metric: str = "l2"):
        self.dim = dim
        self.m = m
        self.ef_construction = ef_construction
        self.metric = metric
        self.vectors: Optional[np.ndarray] = None
        self.graph: Dict[int, List[int]] = {}
        self.entry_point: int = 0

    def _dist(self, u: np.ndarray, v: np.ndarray) -> float:
        if self.metric == "cosine":
            norm_u = max(float(np.linalg.norm(u)), 1e-12)
            norm_v = max(float(np.linalg.norm(v)), 1e-12)
            return 1.0 - float(np.dot(u, v) / (norm_u * norm_v))
        return float(np.sum((u - v) ** 2))

    def build(self, vectors: np.ndarray) -> None:
        self.vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        n, _ = self.vectors.shape
        self.graph = {i: [] for i in range(n)}
        self.entry_point = 0

        # Construct bidirectional k-NN small-world graph
        for i in range(n):
            diffs = self.vectors - self.vectors[i]
            dists = np.sum(diffs ** 2, axis=1)
            dists[i] = np.inf  # exclude self

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
        if self.vectors is None or len(self.vectors) == 0:
            return [], []

        n = len(self.vectors)
        entry = self.entry_point
        dist_entry = self._dist(query, self.vectors[entry])

        visited = {entry}
        # candidates priority list (dist, node)
        candidates = [(dist_entry, entry)]
        # best found set W of size ef_search
        w = [(dist_entry, entry)]
        beam_size = max(ef_search, top_k)

        while candidates:
            candidates.sort(key=lambda x: x[0])
            c_dist, c_node = candidates.pop(0)

            w.sort(key=lambda x: x[0])
            furthest_w_dist = w[-1][0]

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
    """Standard HNSW index supporting hnswlib native backend with graph fallback."""

    def __init__(
        self,
        space: str = "l2",
        m: int = 16,
        ef_construction: int = 100,
        ef_search: int = 50,
    ):
        """
        Args:
            space: Distance metric ('l2', 'ip', or 'cosine').
            m: Max number of outgoing connections per node.
            ef_construction: Size of dynamic candidate list during construction.
            ef_search: Size of candidate list during query phase.
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
        """Constructs HNSW graph index over vectors."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array (N, D)")

        self._num_vectors, self._dim = vectors.shape

        # Attempt to use native C++ hnswlib if available
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
            # Activate pure Python/NumPy graph fallback
            self._hnswlib_index = None
            self._fallback_index = FallbackGraphHNSW(
                dim=self._dim,
                m=self.m,
                ef_construction=self.ef_construction,
                metric=self.space,
            )
            self._fallback_index.build(vectors)

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Performs approximate nearest neighbor search."""
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
            raise RuntimeError("Index not built. Call build() first.")

    def get_memory_bytes(self) -> int:
        """Computes approximate RAM footprint (vectors + graph link tables)."""
        # Vector raw size: N * D * 4 bytes
        vector_bytes = self._num_vectors * self._dim * 4
        # Graph links size: N * M * 8 bytes (pointers/integers)
        links_bytes = self._num_vectors * self.m * 8
        return vector_bytes + links_bytes
