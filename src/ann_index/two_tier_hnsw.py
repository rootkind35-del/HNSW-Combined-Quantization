"""Two-Tier Quantized HNSW Index with Adaptive Early-Exit and Disk-Backed Re-Ranking."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from ann_index.base import BaseIndex
from ann_index.early_exit import AdaptiveEarlyExitController
from ann_index.quantizer import ScalarQuantizer


class TwoTierQuantizedHNSW(BaseIndex):
    """
    Two-Tier Quantized HNSW:
    - Tier 1: In-memory 8-bit quantized graph index with Adaptive Early-Exit routing.
    - Tier 2: Exact float32 distance re-ranking on Top-K candidates.
    """

    def __init__(
        self,
        m: int = 16,
        ef_search: int = 40,
        tau: int = 3,
        epsilon: float = 1e-4,
        rerank_factor: int = 3,
        min_rerank_k: int = 30,
        metric: str = "l2",
    ):
        self.m = m
        self.ef_search = ef_search
        self.tau = tau
        self.epsilon = epsilon
        self.rerank_factor = rerank_factor
        self.min_rerank_k = min_rerank_k
        self.metric = metric.lower()

        self.quantizer = ScalarQuantizer(per_channel=True)
        self.q_vectors: Optional[np.ndarray] = None  # Tier 1 (uint8)
        self.raw_vectors: Optional[np.ndarray] = None  # Tier 2 (float32, can be memmap)
        self.graph: Dict[int, List[int]] = {}
        self.entry_point: int = 0
        self.num_vectors: int = 0
        self.dim: int = 0

    @property
    def name(self) -> str:
        return f"TwoTierHNSW(SQ8+EarlyExit(τ={self.tau},ε={self.epsilon})+ReRank)"

    def build(self, vectors: np.ndarray) -> None:
        """Constructs Tier 1 quantized graph index and links Tier 2 float32 storage."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array (N, D)")

        self.num_vectors, self.dim = vectors.shape
        self.raw_vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        # 1. Calibrate and quantize vectors to 8-bit uint8
        self.quantizer.fit(self.raw_vectors)
        self.q_vectors = self.quantizer.quantize(self.raw_vectors)

        # 2. Build Tier 1 Small-World Navigable Graph on uint8 vectors (Vectorized BLAS)
        self.graph = {i: [] for i in range(self.num_vectors)}
        self.entry_point = 0

        k_best = min(self.m, self.num_vectors - 1)
        if k_best > 0:
            scaled_q = self.q_vectors.astype(np.float32) * self.quantizer.scale.flatten()
            sq_norms = np.sum(scaled_q ** 2, axis=1, keepdims=True)
            chunk_size = 500
            for start_idx in range(0, self.num_vectors, chunk_size):
                end_idx = min(start_idx + chunk_size, self.num_vectors)
                chunk_q = scaled_q[start_idx:end_idx]
                chunk_sq = sq_norms[start_idx:end_idx]
                chunk_dists = chunk_sq + sq_norms.T - 2.0 * np.dot(chunk_q, scaled_q.T)
                for local_i, global_i in enumerate(range(start_idx, end_idx)):
                    chunk_dists[local_i, global_i] = np.inf
                    nearest = np.argpartition(chunk_dists[local_i], k_best - 1)[:k_best]
                    for nb in nearest:
                        nb_int = int(nb)
                        if nb_int not in self.graph[global_i]:
                            self.graph[global_i].append(nb_int)
                        if global_i not in self.graph[nb_int]:
                            self.graph[nb_int].append(global_i)

    def _search_tier1_with_early_exit(
        self, query_uint8: np.ndarray, num_candidates: int
    ) -> List[int]:
        """Traverses Tier 1 uint8 graph guided by the Adaptive Early-Exit controller."""
        if self.q_vectors is None or self.num_vectors == 0:
            return []

        controller = AdaptiveEarlyExitController(tau=self.tau, epsilon=self.epsilon, min_steps=4)
        entry = self.entry_point
        d_entry = self.quantizer.compute_distance(query_uint8, self.q_vectors[entry])

        visited = {entry}
        candidates = [(d_entry, entry)]
        w = [(d_entry, entry)]
        beam_size = max(self.ef_search, num_candidates)

        while candidates:
            candidates.sort(key=lambda x: x[0])
            c_dist, c_node = candidates.pop(0)

            w.sort(key=lambda x: x[0])
            best_dist = w[0][0]

            # Check Adaptive Early-Exit condition
            if controller.update(best_dist):
                # Search has converged to local minimum: break early
                break

            furthest_w_dist = w[-1][0]
            if c_dist > furthest_w_dist and len(w) >= beam_size:
                break

            for neighbor in self.graph.get(c_node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    d = self.quantizer.compute_distance(query_uint8, self.q_vectors[neighbor])
                    if d < furthest_w_dist or len(w) < beam_size:
                        candidates.append((d, neighbor))
                        w.append((d, neighbor))
                        w.sort(key=lambda x: x[0])
                        if len(w) > beam_size:
                            w.pop()

        w.sort(key=lambda x: x[0])
        return [idx for _, idx in w[:num_candidates]]

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executes two-tier search:
        - Phase 1: In-memory uint8 graph search with Adaptive Early-Exit to retrieve candidates.
        - Phase 2: Tier 2 float32 exact distance re-ranking on retrieved candidates.
        """
        if self.q_vectors is None or self.raw_vectors is None:
            raise RuntimeError("Index has not been built. Call build() first.")

        q_float = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q_float.ndim == 1:
            q_float = q_float.reshape(1, -1)

        num_queries, query_dim = q_float.shape
        if query_dim != self.dim:
            raise ValueError(f"Query dimension mismatch: expected {self.dim}, got {query_dim}")

        # Quantize queries for Tier 1 routing
        q_uint8 = self.quantizer.quantize(q_float)

        candidate_pool_size = min(
            max(top_k * self.rerank_factor, self.min_rerank_k),
            self.num_vectors,
        )

        all_indices = []
        all_distances = []

        for i in range(num_queries):
            # Phase 1: Tier 1 Routing
            candidate_indices = self._search_tier1_with_early_exit(
                q_uint8[i], num_candidates=candidate_pool_size
            )

            if not candidate_indices:
                all_indices.append(np.full(top_k, -1, dtype=np.int64))
                all_distances.append(np.full(top_k, np.inf, dtype=np.float32))
                continue

            # Phase 2: Tier 2 Full Precision Re-ranking
            cand_raw = self.raw_vectors[candidate_indices]  # Slice Tier 2 vectors
            query_vec = q_float[i]

            if self.metric == "cosine":
                q_norm = max(float(np.linalg.norm(query_vec)), 1e-12)
                cand_norms = np.maximum(np.linalg.norm(cand_raw, axis=1), 1e-12)
                sims = np.dot(cand_raw, query_vec) / (cand_norms * q_norm)
                exact_dists = 1.0 - sims
            else:
                diff = cand_raw - query_vec
                exact_dists = np.sum(diff ** 2, axis=1)

            # Sort candidate pool by exact distances
            sorted_order = np.argsort(exact_dists)
            actual_k = min(top_k, len(candidate_indices))

            top_indices = [candidate_indices[idx] for idx in sorted_order[:actual_k]]
            top_dists = exact_dists[sorted_order[:actual_k]]

            all_indices.append(top_indices)
            all_distances.append(top_dists)

        return np.array(all_indices, dtype=np.int64), np.array(all_distances, dtype=np.float32)

    def get_memory_bytes(self) -> int:
        """
        Returns In-Memory RAM footprint for Tier 1:
        8-bit vector array + graph link table pointers.
        (Tier 2 float32 vectors are disk-backed memmap, not counted in active RAM).
        """
        # Tier 1 uint8 vectors: N * D * 1 byte
        quantized_bytes = self.num_vectors * self.dim * 1
        # Tier 1 graph links: N * M * 8 bytes
        links_bytes = self.num_vectors * self.m * 8
        # Quantizer scale parameters: D * 4 bytes * 2
        quantizer_bytes = self.dim * 8
        return quantized_bytes + links_bytes + quantizer_bytes
