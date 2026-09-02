"""Inverted File with Product Quantization (IVF-PQ) Index implementation."""

from typing import Dict, List, Optional, Tuple
import numpy as np
from ann_index.base import BaseIndex
from ann_index.pq import ProductQuantizer


class IVFPQIndex(BaseIndex):
    """
    IVF-PQ index combining coarse Voronoi cells (Inverted File) with Product Quantization.
    Represents the traditional subspace compression baseline.
    """

    def __init__(
        self,
        nlist: int = 16,
        num_subvectors: int = 8,
        nprobe: int = 4,
        metric: str = "l2",
    ):
        """
        Args:
            nlist: Number of coarse Voronoi clusters (inverted lists).
            num_subvectors: Number of subspace partitions for Product Quantization.
            nprobe: Number of closest centroids to probe during query search.
            metric: Distance metric ('l2' or 'cosine').
        """
        self.nlist = nlist
        self.num_subvectors = num_subvectors
        self.nprobe = nprobe
        self.metric = metric.lower()

        self.pq = ProductQuantizer(num_subvectors=self.num_subvectors, num_clusters=256)
        self.coarse_centroids: Optional[np.ndarray] = None  # (nlist, D)
        self.inverted_lists: Dict[int, Dict[str, np.ndarray]] = {}
        self.num_vectors: int = 0
        self.dim: int = 0

    @property
    def name(self) -> str:
        return f"IVF-PQ(nlist={self.nlist}, m={self.num_subvectors}, nprobe={self.nprobe})"

    def _train_coarse_centroids(self, vectors: np.ndarray, k: int) -> np.ndarray:
        """Trains coarse Voronoi centroids using K-Means."""
        n, d = vectors.shape
        actual_k = min(k, n)
        init_idx = np.random.choice(n, size=actual_k, replace=False)
        centroids = np.copy(vectors[init_idx])

        for _ in range(15):
            diffs = vectors[:, np.newaxis, :] - centroids[np.newaxis, :, :]
            dists = np.sum(diffs ** 2, axis=2)
            labels = np.argmin(dists, axis=1)

            new_c = np.zeros_like(centroids)
            for c in range(actual_k):
                mask = (labels == c)
                if np.any(mask):
                    new_c[c] = np.mean(vectors[mask], axis=0)
                else:
                    new_c[c] = vectors[np.random.randint(0, n)]

            if np.allclose(centroids, new_c, atol=1e-4):
                break
            centroids = new_c

        return centroids.astype(np.float32)

    def build(self, vectors: np.ndarray) -> None:
        """Constructs IVF-PQ index over dataset vectors."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array of shape (N, D)")

        self.num_vectors, self.dim = vectors.shape
        v = np.ascontiguousarray(vectors, dtype=np.float32)

        # 1. Train coarse centroids
        self.coarse_centroids = self._train_coarse_centroids(v, self.nlist)
        actual_nlist = len(self.coarse_centroids)

        # 2. Assign vectors to closest coarse centroid
        diffs = v[:, np.newaxis, :] - self.coarse_centroids[np.newaxis, :, :]
        dists = np.sum(diffs ** 2, axis=2)
        assigned_labels = np.argmin(dists, axis=1)

        # 3. Compute residuals: r_i = v_i - coarse_centroids[label_i]
        residuals = v - self.coarse_centroids[assigned_labels]

        # 4. Train Product Quantizer on residuals and encode
        self.pq.fit(residuals)
        all_codes = self.pq.encode(residuals)

        # 5. Populate inverted lists
        self.inverted_lists = {}
        for c in range(actual_nlist):
            cluster_mask = np.where(assigned_labels == c)[0]
            if len(cluster_mask) > 0:
                self.inverted_lists[c] = {
                    "ids": cluster_mask.astype(np.int64),
                    "codes": all_codes[cluster_mask],
                }
            else:
                self.inverted_lists[c] = {
                    "ids": np.empty(0, dtype=np.int64),
                    "codes": np.empty((0, self.num_subvectors), dtype=np.uint8),
                }

    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Performs Asymmetric Distance Computation across nprobe closest inverted lists."""
        if self.coarse_centroids is None or not self.inverted_lists:
            raise RuntimeError("Index not built. Call build() first.")

        q_float = np.ascontiguousarray(query_vectors, dtype=np.float32)
        if q_float.ndim == 1:
            q_float = q_float.reshape(1, -1)

        num_queries, _ = q_float.shape
        actual_nprobe = min(self.nprobe, len(self.coarse_centroids))

        all_indices = []
        all_distances = []

        for i in range(num_queries):
            q = q_float[i]

            # 1. Find nprobe closest coarse centroids
            dists_to_centroids = np.sum((self.coarse_centroids - q) ** 2, axis=1)
            probe_clusters = np.argpartition(dists_to_centroids, actual_nprobe - 1)[:actual_nprobe]

            candidate_ids = []
            candidate_dists = []

            # 2. Probe selected inverted lists
            for c in probe_clusters:
                inv = self.inverted_lists[c]
                if len(inv["ids"]) == 0:
                    continue

                # Query residual with respect to cluster centroid: r_q = q - centroid
                r_q = q - self.coarse_centroids[c]

                # Precompute LUT for this cluster
                lut = self.pq.compute_distance_table(r_q)

                # Fast ADC distance computation via LUT look-up
                dists_c = self.pq.asymmetric_distance(lut, inv["codes"])

                candidate_ids.append(inv["ids"])
                candidate_dists.append(dists_c)

            if not candidate_ids:
                all_indices.append(np.full(top_k, -1, dtype=np.int64))
                all_distances.append(np.full(top_k, np.inf, dtype=np.float32))
                continue

            merged_ids = np.concatenate(candidate_ids)
            merged_dists = np.concatenate(candidate_dists)

            # 3. Retrieve Top-K
            k_ret = min(top_k, len(merged_dists))
            best_idx = np.argpartition(merged_dists, k_ret - 1)[:k_ret]
            sorted_order = best_idx[np.argsort(merged_dists[best_idx])]

            res_ids = merged_ids[sorted_order]
            res_dists = merged_dists[sorted_order]

            if len(res_ids) < top_k:
                pad_len = top_k - len(res_ids)
                res_ids = np.pad(res_ids, (0, pad_len), constant_values=-1)
                res_dists = np.pad(res_dists, (0, pad_len), constant_values=np.inf)

            all_indices.append(res_ids)
            all_distances.append(res_dists)

        return np.array(all_indices, dtype=np.int64), np.array(all_distances, dtype=np.float32)

    def get_memory_bytes(self) -> int:
        """
        Computes total RAM consumption:
        Coarse centroids + PQ codebooks + Inverted lists (codes + IDs).
        """
        actual_nlist = len(self.coarse_centroids) if self.coarse_centroids is not None else self.nlist
        coarse_bytes = actual_nlist * self.dim * 4
        # Codebooks: M * 256 * sub_dim * 4 bytes = 256 * D * 4 bytes
        codebook_bytes = 256 * self.dim * 4
        # Inverted lists: N * M (uint8 codes) + N * 8 (int64 IDs)
        lists_bytes = self.num_vectors * (self.num_subvectors * 1 + 8)
        return coarse_bytes + codebook_bytes + lists_bytes
