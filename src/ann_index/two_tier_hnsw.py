"""Distributed Sharded IVF-HNSW index and Two-Tier Quantized HNSW.

Combines:
- Tier 1: IVF centroid routing and in-memory local HNSW graphs with row-wise SQ8
  asymmetric distance computation (ADC) and adaptive early-exit stopping.
- Tier 2: Direct file I/O SSD storage via DirectIOManager for exact float32
  re-ranking without reliance on memory-mapped files.
"""

from typing import Dict, List, Optional, Tuple, Union
import os
import numpy as np

from ann_index.base import BaseIndex
from ann_index.early_exit import AdaptiveEarlyExitController
from ann_index.hnsw_quantized import distance_adc, exact_distance_l2, quantize_adc
from ann_index.io_manager import DirectIOManager
from ann_index.quantizer import ScalarQuantizer


class LocalShard:
    """A single shard maintaining an in-memory HNSW graph and Direct I/O SSD backing.

    Tier 1 uses row-wise SQ8 quantized vectors with float16 scale and offset anchors
    evaluated via Asymmetric Distance Computation (ADC).
    Tier 2 stores raw float32 vectors on SSD for exact re-ranking.
    """

    def __init__(
        self,
        shard_id: int,
        dim: int,
        max_elements: int,
        storage_dir: str,
        clean_storage: bool = False,
    ) -> None:
        """Initialize local shard.

        Args:
            shard_id: Unique integer identifier for this shard.
            dim: Dimension of vector representations.
            max_elements: Initial capacity for stored vectors.
            storage_dir: Directory where shard binary data is stored.
            clean_storage: Whether to truncate/reset shard storage file on init.
        """
        self.shard_id = shard_id
        self.dim = dim
        self.vector_bytes = dim * 4
        self.max_elements = max(100, max_elements)
        self.storage_dir = storage_dir

        # --- Tier 1 (In-Memory HNSW Graph + Quantized Vectors) ---
        self.graph: Dict[int, List[int]] = {}
        self.entry_point: Optional[int] = None

        self.quantized = np.zeros((self.max_elements, dim), dtype=np.uint8)
        self.scales = np.zeros((self.max_elements, 1), dtype=np.float16)
        self.offsets = np.zeros((self.max_elements, 1), dtype=np.float16)
        self.local_count = 0

        # Global ID mapping: local node_id (0..local_count-1) -> external global_id
        self.id_map: Dict[int, int] = {}

        # --- Tier 2 (Direct I/O SSD Storage) ---
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, f"shard_{shard_id}.bin")
        self.io_manager = DirectIOManager(db_path, dim=dim)
        if clean_storage:
            open(self.io_manager.filepath, "wb").close()
            self.io_manager.lru_cache.clear()

    def _calc_distance(self, query: np.ndarray, node_id: int) -> float:
        """Calculate asymmetric Euclidean distance to a local node."""
        q_vec = self.quantized[node_id]
        scale = self.scales[node_id][0]
        offset = self.offsets[node_id][0]
        return distance_adc(query, q_vec, scale, offset)

    def _ensure_capacity(self) -> None:
        """Expand preallocated storage arrays if local_count reaches max_elements."""
        if self.local_count >= self.max_elements:
            additional = max(1000, self.max_elements)
            new_capacity = self.max_elements + additional
            new_quantized = np.zeros((new_capacity, self.dim), dtype=np.uint8)
            new_quantized[: self.max_elements] = self.quantized
            self.quantized = new_quantized

            new_scales = np.zeros((new_capacity, 1), dtype=np.float16)
            new_scales[: self.max_elements] = self.scales
            self.scales = new_scales

            new_offsets = np.zeros((new_capacity, 1), dtype=np.float16)
            new_offsets[: self.max_elements] = self.offsets
            self.offsets = new_offsets

            self.max_elements = new_capacity

    def _search_local_graph(
        self,
        query: np.ndarray,
        entry_point: int,
        ef: int,
        tau: int = 3,
        epsilon: float = 1e-4,
    ) -> List[Tuple[float, int]]:
        """Search in-memory graph using beam search with adaptive early-exit.

        Args:
            query: Query vector in float32.
            entry_point: Local node ID to start traversal.
            ef: Beam search size.
            tau: Number of non-improving steps triggering early termination.
            epsilon: Minimum distance improvement threshold.

        Returns:
            List of (distance, local_node_id) sorted ascending by distance.
        """
        if entry_point is None or entry_point >= self.local_count:
            return []

        d_entry = self._calc_distance(query, entry_point)
        candidates: List[Tuple[float, int]] = [(d_entry, entry_point)]
        top_results: List[Tuple[float, int]] = [(d_entry, entry_point)]
        visited = {entry_point}

        fail_count = 0
        current_best_dist = d_entry

        while candidates:
            candidates.sort(key=lambda x: x[0])
            c_dist, c_id = candidates.pop(0)

            neighbors = self.graph.get(c_id, [])
            for neighbor in neighbors:
                if neighbor not in visited and neighbor < self.local_count:
                    visited.add(neighbor)
                    n_dist = self._calc_distance(query, neighbor)

                    if current_best_dist - n_dist < epsilon:
                        fail_count += 1
                    else:
                        fail_count = 0
                        current_best_dist = n_dist

                    if fail_count >= tau:
                        break

                    candidates.append((n_dist, neighbor))
                    top_results.append((n_dist, neighbor))
                    top_results.sort(key=lambda x: x[0])
                    if len(top_results) > ef:
                        top_results.pop()

            if fail_count >= tau:
                break

        return top_results

    def add_node(
        self,
        global_id: int,
        vector: np.ndarray,
        M: int = 16,
        ef_construction: int = 32,
    ) -> int:
        """Insert a vector into the local shard graph and direct SSD storage.

        Args:
            global_id: Global document identifier.
            vector: Float32 vector array.
            M: Maximum number of bidirectional connections per node.
            ef_construction: Candidate list size during index construction.

        Returns:
            Assigned local node index.
        """
        vec_float = np.asarray(vector, dtype=np.float32).flatten()
        self._ensure_capacity()

        q_vec, scale, offset = quantize_adc(vec_float.reshape(1, -1))

        idx = self.local_count
        self.quantized[idx] = q_vec[0]
        self.scales[idx] = scale[0][0]
        self.offsets[idx] = offset[0][0]
        self.id_map[idx] = global_id
        self.graph[idx] = []

        if self.entry_point is None:
            self.entry_point = idx
            self.local_count += 1
            self._save_to_ssd(idx, vec_float)
            return idx

        nearest_neighbors = self._search_local_graph(
            query=vec_float,
            entry_point=self.entry_point,
            ef=ef_construction,
        )

        top_m = nearest_neighbors[:M]
        for _, neighbor_id in top_m:
            self.graph[idx].append(neighbor_id)
            if idx not in self.graph[neighbor_id]:
                self.graph[neighbor_id].append(idx)

        self.local_count += 1
        self._save_to_ssd(idx, vec_float)
        return idx

    def _save_to_ssd(self, idx: int, vector: np.ndarray) -> None:
        """Write raw float32 vector bytes at exact offset in storage file."""
        if not os.path.exists(self.io_manager.filepath):
            open(self.io_manager.filepath, "wb").close()
        offset = idx * self.vector_bytes
        with open(self.io_manager.filepath, "r+b") as f:
            f.seek(offset)
            vector.astype(np.float32).tofile(f)
        self.io_manager.lru_cache.put(idx, vector.astype(np.float32))


class ShardedIVFHNSW:
    """Distributed Sharded IVF-HNSW Index Router.

    Partitions vector space across K shards using centroid-based clustering.
    Searches candidate shards in parallel, conducts in-memory ADC graph search,
    and performs Tier 2 direct SSD re-ranking against raw float32 vectors.
    """

    def __init__(
        self,
        dim: int,
        num_shards: int,
        capacity_per_shard: int,
        storage_dir: str,
        clean_storage: bool = False,
    ) -> None:
        """Initialize sharded IVF-HNSW router.

        Args:
            dim: Dimensionality of vector representations.
            num_shards: Number of partitions / shards (K).
            capacity_per_shard: Initial capacity per shard.
            storage_dir: Root directory for shard binary files.
            clean_storage: Whether to truncate/reset shard storage files on init.
        """
        self.dim = dim
        self.num_shards = max(1, num_shards)
        self.capacity_per_shard = capacity_per_shard
        self.storage_dir = storage_dir
        self.clean_storage = clean_storage

        np.random.seed(42)
        self.centroids = np.random.randn(num_shards, dim).astype(np.float32)
        self.shards = [
            LocalShard(i, dim, capacity_per_shard, storage_dir, clean_storage=clean_storage)
            for i in range(num_shards)
        ]
        self.last_probed_shards: List[int] = []

    def _get_nearest_shards(self, vector: np.ndarray, nprobe: int) -> List[int]:
        """Find the nearest shard centroids for a given vector.

        Args:
            vector: Query or insert vector.
            nprobe: Number of closest shards to return.

        Returns:
            List of shard indices sorted ascending by distance.
        """
        vec = np.asarray(vector, dtype=np.float32).flatten()
        distances = np.linalg.norm(self.centroids - vec, axis=1)
        actual_nprobe = max(1, min(nprobe, self.num_shards))
        return np.argsort(distances)[:actual_nprobe].tolist()

    def route_and_insert(self, global_id: int, vector: np.ndarray) -> int:
        """Route vector to nearest shard centroid and insert.

        Args:
            global_id: External document identifier.
            vector: Vector array to index.

        Returns:
            Shard ID where vector was placed.
        """
        vec = np.asarray(vector, dtype=np.float32).flatten()
        target_shard_id = self._get_nearest_shards(vec, nprobe=1)[0]
        self.shards[target_shard_id].add_node(global_id, vec)
        return target_shard_id

    def distributed_search(
        self,
        query: np.ndarray,
        top_k: int = 5,
        nprobe: int = 3,
        re_rank_limit: int = 50,
        return_shards: bool = True,
    ) -> Union[Tuple[List[Tuple[float, int, int]], List[int]], List[Tuple[float, int, int]]]:
        """Execute distributed two-tier search across nearest candidate shards.

        Flow:
        1. Select closest nprobe shards via centroid proximity.
        2. Query in-memory HNSW graphs with ADC and early-exit to harvest candidates.
        3. Retrieve raw float32 vectors from SSD via DirectIOManager batch reading.
        4. Re-rank top candidates using exact Euclidean (L2) distance.

        Args:
            query: Query vector (float32).
            top_k: Number of nearest neighbors to return.
            nprobe: Number of shards to probe.
            re_rank_limit: Number of candidate vectors to fetch from disk for re-ranking.
            return_shards: If True, returns (results, probed_shards); otherwise returns results.

        Returns:
            If return_shards is True:
                (final_results, target_shard_ids) where each result item is
                (exact_distance, global_id, shard_id).
            If return_shards is False:
                final_results as list of (exact_distance, global_id, shard_id).
        """
        query_vec = np.asarray(query, dtype=np.float32).flatten()
        target_shard_ids = self._get_nearest_shards(query_vec, nprobe=nprobe)
        self.last_probed_shards = list(target_shard_ids)

        # Step 1 & 2: Search local graphs in candidate shards
        candidate_pool: List[Tuple[float, int, int, int]] = []
        for sid in target_shard_ids:
            shard = self.shards[sid]
            if shard.entry_point is None or shard.local_count == 0:
                continue

            local_results = shard._search_local_graph(
                query_vec,
                shard.entry_point,
                ef=re_rank_limit,
            )
            for dist, local_node_id in local_results:
                global_id = shard.id_map.get(local_node_id, local_node_id)
                candidate_pool.append((dist, local_node_id, global_id, sid))

        if not candidate_pool:
            empty_res: List[Tuple[float, int, int]] = []
            if return_shards:
                return empty_res, target_shard_ids
            return empty_res

        # Sort by ADC distance and retain top candidates for disk retrieval
        candidate_pool.sort(key=lambda x: x[0])
        top_candidates = candidate_pool[:re_rank_limit]

        # Step 3: Fetch exact float32 vectors from SSD via DirectIOManager
        requests_by_shard: Dict[int, List[int]] = {}
        for _, local_node_id, _, sid in top_candidates:
            if sid not in requests_by_shard:
                requests_by_shard[sid] = []
            requests_by_shard[sid].append(local_node_id)

        fetched_vectors: Dict[Tuple[int, int], np.ndarray] = {}
        for sid, node_ids in requests_by_shard.items():
            batch_result = self.shards[sid].io_manager.async_read_batch(node_ids)
            for nid, vec in batch_result.items():
                fetched_vectors[(sid, nid)] = vec

        # Step 4: Re-rank using exact Euclidean (L2) distance
        final_results: List[Tuple[float, int, int]] = []
        for _, local_node_id, global_id, sid in top_candidates:
            exact_vec = fetched_vectors.get((sid, local_node_id))
            if exact_vec is not None:
                exact_dist = exact_distance_l2(query_vec, exact_vec)
            else:
                exact_dist = float("inf")
            final_results.append((exact_dist, global_id, sid))

        final_results.sort(key=lambda x: x[0])
        final_top_k = final_results[:top_k]

        if return_shards:
            return final_top_k, target_shard_ids
        return final_top_k


class TwoTierQuantizedHNSW(BaseIndex):
    """Monolithic TwoTierQuantizedHNSW retained for backward compatibility."""

    def __init__(
        self,
        m: int = 16,
        ef_search: int = 40,
        tau: int = 3,
        epsilon: float = 1e-4,
        rerank_factor: int = 3,
        min_rerank_k: int = 30,
        metric: str = "l2",
    ) -> None:
        self.m = m
        self.ef_search = ef_search
        self.tau = tau
        self.epsilon = epsilon
        self.rerank_factor = rerank_factor
        self.min_rerank_k = min_rerank_k
        self.metric = metric.lower()

        self.quantizer = ScalarQuantizer(per_channel=True)
        self.q_vectors: Optional[np.ndarray] = None
        self.raw_vectors: Optional[np.ndarray] = None
        self.graph: Dict[int, List[int]] = {}
        self.entry_point: int = 0
        self.num_vectors: int = 0
        self.dim: int = 0

    @property
    def name(self) -> str:
        return f"TwoTierHNSW(SQ8+EarlyExit(τ={self.tau},ε={self.epsilon})+ReRank)"

    def build(self, vectors: np.ndarray) -> None:
        if vectors.ndim != 2:
            raise ValueError("Input vector array must be 2D (N, D)")

        self.num_vectors, self.dim = vectors.shape
        self.raw_vectors = np.ascontiguousarray(vectors, dtype=np.float32)

        self.quantizer.fit(self.raw_vectors)
        self.q_vectors = self.quantizer.quantize(self.raw_vectors)

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

            if controller.update(best_dist):
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
        if self.q_vectors is None or self.raw_vectors is None:
            raise RuntimeError("Index not built. Call build() first.")

        q_float = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q_float.ndim == 1:
            q_float = q_float.reshape(1, -1)

        num_queries, query_dim = q_float.shape
        if query_dim != self.dim:
            raise ValueError(f"Query dim mismatch: expected {self.dim}, got {query_dim}")

        q_uint8 = self.quantizer.quantize(q_float)
        candidate_pool_size = min(
            max(top_k * self.rerank_factor, self.min_rerank_k),
            self.num_vectors,
        )

        all_indices = []
        all_distances = []

        for i in range(num_queries):
            candidate_indices = self._search_tier1_with_early_exit(
                q_uint8[i], num_candidates=candidate_pool_size
            )

            if not candidate_indices:
                all_indices.append(np.full(top_k, -1, dtype=np.int64))
                all_distances.append(np.full(top_k, np.inf, dtype=np.float32))
                continue

            cand_raw = self.raw_vectors[candidate_indices]
            query_vec = q_float[i]

            if self.metric == "cosine":
                q_norm = max(float(np.linalg.norm(query_vec)), 1e-12)
                cand_norms = np.maximum(np.linalg.norm(cand_raw, axis=1), 1e-12)
                sims = np.dot(cand_raw, query_vec) / (cand_norms * q_norm)
                exact_dists = 1.0 - sims
            else:
                diff = cand_raw - query_vec
                exact_dists = np.sum(diff ** 2, axis=1)

            sorted_order = np.argsort(exact_dists)
            actual_k = min(top_k, len(candidate_indices))

            top_indices = [candidate_indices[idx] for idx in sorted_order[:actual_k]]
            top_dists = exact_dists[sorted_order[:actual_k]]

            all_indices.append(top_indices)
            all_distances.append(top_dists)

        return np.array(all_indices, dtype=np.int64), np.array(all_distances, dtype=np.float32)

    def get_memory_bytes(self) -> int:
        quantized_bytes = self.num_vectors * self.dim * 1
        links_bytes = self.num_vectors * self.m * 8
        quantizer_bytes = self.dim * 8
        return quantized_bytes + links_bytes + quantizer_bytes
