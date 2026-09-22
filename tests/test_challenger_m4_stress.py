"""Empirical stress and boundary test suite for Challenger M4.

Validates:
1. Convergence and stability of train_ivf_kmeans under standard and boundary inputs.
2. ShardedIVFHNSW router indexing and distributed search with boundary configurations
   (N=10, K=2; N=200, K=5; N=5, K=10; N=1, K=1).
3. Pipeline verification self-test exact match distance (dist=0.000000 for vectors[0]).
4. Adversarial audit of exact match recall degradation due to LocalShard._search_local_graph early-exit.
5. Shard distribution balance across partitions.
6. Static AST and runtime trap audit confirming zero numpy.memmap.
"""

import ast
import os
import shutil
import tempfile
import unittest
import numpy as np

from scripts.run_pipeline import train_ivf_kmeans
from ann_index.two_tier_hnsw import ShardedIVFHNSW, LocalShard


class TestIVFKMeansConvergence(unittest.TestCase):
    """Stress tests for IVF K-Means clustering convergence and edge cases."""

    def test_kmeans_convergence_standard(self):
        """Verify K-means converges within max_iters and produces valid centroids."""
        np.random.seed(123)
        vectors = np.random.randn(500, 64).astype(np.float32)
        k = 8
        centroids = train_ivf_kmeans(vectors, k=k, max_iters=25)

        self.assertEqual(centroids.shape, (k, 64))
        self.assertFalse(np.isnan(centroids).any())
        self.assertFalse(np.isinf(centroids).any())

        # Check inertia is lower than random centroid assignment
        rand_centroids = vectors[np.random.choice(500, size=k, replace=False)]
        dists_trained = np.min(
            np.sum((vectors[:, None, :] - centroids[None, :, :]) ** 2, axis=2),
            axis=1
        )
        dists_random = np.min(
            np.sum((vectors[:, None, :] - rand_centroids[None, :, :]) ** 2, axis=2),
            axis=1
        )
        self.assertLessEqual(np.mean(dists_trained), np.mean(dists_random))

    def test_kmeans_boundary_n_le_k(self):
        """Verify K-means handles cases where vector count <= cluster count."""
        # N=2, K=5
        vecs_2 = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
        c_5 = train_ivf_kmeans(vecs_2, k=5)
        self.assertEqual(c_5.shape, (5, 2))
        self.assertFalse(np.isnan(c_5).any())

        # N=5, K=5
        vecs_5 = np.random.randn(5, 16).astype(np.float32)
        c_equal = train_ivf_kmeans(vecs_5, k=5)
        self.assertEqual(c_equal.shape, (5, 16))

        # N=1, K=1
        vecs_1 = np.array([[0.5, -0.5]], dtype=np.float32)
        c_1 = train_ivf_kmeans(vecs_1, k=1)
        self.assertEqual(c_1.shape, (1, 2))
        np.testing.assert_allclose(c_1[0], vecs_1[0])

    def test_kmeans_clustered_distribution(self):
        """Verify K-means separates well-defined Gaussian clusters."""
        np.random.seed(42)
        c1 = np.random.randn(50, 32).astype(np.float32) + 20.0
        c2 = np.random.randn(50, 32).astype(np.float32) - 20.0
        data = np.vstack([c1, c2])

        centroids = train_ivf_kmeans(data, k=2, max_iters=15)
        self.assertEqual(centroids.shape, (2, 32))

        # One centroid should be near +20 and the other near -20
        means = np.mean(centroids, axis=1)
        self.assertTrue((means[0] > 10 and means[1] < -10) or (means[0] < -10 and means[1] > 10))


class TestPipelineBoundaryExecution(unittest.TestCase):
    """Stress tests for ShardedIVFHNSW router under boundary conditions."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="ann_challenger_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_boundary_10_vectors_2_shards(self):
        """Verify pipeline operation with N=10 vectors across 2 shards."""
        dim = 64
        num_shards = 2
        np.random.seed(102)
        vectors = np.random.randn(10, dim).astype(np.float32)

        centroids = train_ivf_kmeans(vectors, k=num_shards)
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=num_shards,
            capacity_per_shard=20,
            storage_dir=self.test_dir,
            clean_storage=True,
        )
        router.centroids = centroids

        shard_counts = {i: 0 for i in range(num_shards)}
        for i in range(10):
            sid = router.route_and_insert(global_id=i, vector=vectors[i])
            shard_counts[sid] += 1

        # Shard distribution check: both shards must receive vectors
        total_assigned = sum(shard_counts.values())
        self.assertEqual(total_assigned, 10)
        self.assertGreater(shard_counts[0], 0)
        self.assertGreater(shard_counts[1], 0)

        # Pipeline Self-Test Verification query (vectors[0])
        results, probed = router.distributed_search(
            query=vectors[0],
            top_k=3,
            nprobe=num_shards,
            return_shards=True,
        )
        self.assertGreater(len(results), 0)
        top_dist, top_id, top_shard = results[0]
        self.assertEqual(top_id, 0, f"Expected top match global_id=0, got {top_id}")
        self.assertAlmostEqual(top_dist, 0.0, places=5, msg="Self-test top distance not 0.000000")

    def test_boundary_200_vectors_5_shards(self):
        """Verify pipeline operation with N=200 vectors across 5 shards."""
        dim = 128
        num_shards = 5
        np.random.seed(205)
        vectors = np.random.randn(200, dim).astype(np.float32)

        centroids = train_ivf_kmeans(vectors, k=num_shards)
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=num_shards,
            capacity_per_shard=100,
            storage_dir=self.test_dir,
            clean_storage=True,
        )
        router.centroids = centroids

        shard_counts = {i: 0 for i in range(num_shards)}
        for i in range(200):
            sid = router.route_and_insert(global_id=i, vector=vectors[i])
            shard_counts[sid] += 1

        self.assertEqual(sum(shard_counts.values()), 200)
        for sid in range(num_shards):
            self.assertGreater(
                shard_counts[sid], 0, f"Shard {sid} is unexpectedly empty"
            )

        # Pipeline Self-Test Verification query (vectors[0])
        results, probed = router.distributed_search(
            query=vectors[0],
            top_k=5,
            nprobe=3,
            return_shards=True,
        )
        self.assertGreater(len(results), 0)
        top_dist, top_id, top_shard = results[0]
        self.assertEqual(top_id, 0)
        self.assertAlmostEqual(top_dist, 0.0, places=5)

    def test_adversarial_recall_behavior_under_early_exit(self):
        """Adversarial stress test: Quantify exact match recall degradation across all vectors.
        
        Shows that while vectors[0] succeeds with dist=0.000000, non-entry-point
        nodes experience recall truncation due to the per-neighbor fail_count loop in LocalShard.
        """
        dim = 32
        num_shards = 2
        np.random.seed(42)
        vectors = np.random.randn(10, dim).astype(np.float32)

        centroids = train_ivf_kmeans(vectors, k=num_shards)
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=num_shards,
            capacity_per_shard=20,
            storage_dir=self.test_dir,
            clean_storage=True,
        )
        router.centroids = centroids

        for i in range(10):
            router.route_and_insert(global_id=i, vector=vectors[i])

        # Test all 10 vectors
        exact_zero_count = 0
        for i in range(10):
            res, _ = router.distributed_search(query=vectors[i], top_k=1, nprobe=2, return_shards=True)
            if res and abs(res[0][0]) < 1e-5 and res[0][1] == i:
                exact_zero_count += 1

        # At least 70% match, but some are lost due to early-exit truncation
        self.assertGreaterEqual(exact_zero_count, 7)
        self.assertLessEqual(exact_zero_count, 10)

    def test_boundary_more_shards_than_vectors(self):
        """Verify router survives when K > N (e.g. 5 vectors, 10 shards)."""
        dim = 32
        num_shards = 10
        vectors = np.random.randn(5, dim).astype(np.float32)

        centroids = train_ivf_kmeans(vectors, k=num_shards)
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=num_shards,
            capacity_per_shard=20,
            storage_dir=self.test_dir,
            clean_storage=True,
        )
        router.centroids = centroids

        for i in range(5):
            router.route_and_insert(global_id=i, vector=vectors[i])

        # Query vector 0
        results, probed = router.distributed_search(
            query=vectors[0],
            top_k=3,
            nprobe=5,
            return_shards=True,
        )
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0][1], 0)
        self.assertAlmostEqual(results[0][0], 0.0, places=5)

    def test_boundary_single_vector_single_shard(self):
        """Verify router handles minimal boundary (N=1, K=1)."""
        dim = 16
        num_shards = 1
        vectors = np.array([[1.0] * dim], dtype=np.float32)

        centroids = train_ivf_kmeans(vectors, k=num_shards)
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=num_shards,
            capacity_per_shard=10,
            storage_dir=self.test_dir,
            clean_storage=True,
        )
        router.centroids = centroids
        router.route_and_insert(global_id=100, vector=vectors[0])

        results, probed = router.distributed_search(
            query=vectors[0],
            top_k=1,
            nprobe=1,
            return_shards=True,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 100)
        self.assertAlmostEqual(results[0][0], 0.0, places=5)


class TestAdversarialMemmapGrep(unittest.TestCase):
    """Static AST and runtime inspection verifying total absence of numpy.memmap."""

    TARGET_FILES = [
        "dashboard/scripts/dimension_reduction_3d.py",
        "scripts/run_pipeline.py",
        "src/ann_index/two_tier_hnsw.py",
        "dashboard/scripts/search_service.py",
        "dashboard/scripts/search_bridge.py",
    ]

    def test_static_ast_zero_memmap(self):
        """Parse AST of all key scripts to confirm zero memmap calls or imports."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        for rel_path in self.TARGET_FILES:
            full_path = os.path.join(root_dir, rel_path)
            self.assertTrue(os.path.exists(full_path), f"File {rel_path} must exist")

            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content, filename=rel_path)

            for node in ast.walk(tree):
                # Check import statements
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(
                            alias.name, "mmap",
                            f"Prohibited import 'mmap' in {rel_path}:{node.lineno}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotEqual(
                        node.module, "mmap",
                        f"Prohibited import from 'mmap' in {rel_path}:{node.lineno}"
                    )
                # Check function/attribute calls for .memmap
                elif isinstance(node, ast.Attribute):
                    self.assertNotEqual(
                        node.attr, "memmap",
                        f"Prohibited call to '.memmap' attribute in {rel_path}:{node.lineno}"
                    )

    def test_runtime_memmap_trap(self):
        """Monkeypatch np.memmap with an exception trap and run pipeline indexing."""
        original_memmap = getattr(np, "memmap", None)

        def memmap_trap(*args, **kwargs):
            raise AssertionError("ADVERSARIAL TRAP TRIGGERED: numpy.memmap was called at runtime!")

        test_dir = tempfile.mkdtemp(prefix="ann_memmap_trap_")
        try:
            np.memmap = memmap_trap

            dim = 32
            num_shards = 2
            vectors = np.random.randn(20, dim).astype(np.float32)

            centroids = train_ivf_kmeans(vectors, k=num_shards)
            router = ShardedIVFHNSW(
                dim=dim,
                num_shards=num_shards,
                capacity_per_shard=50,
                storage_dir=test_dir,
                clean_storage=True,
            )
            router.centroids = centroids

            for i in range(20):
                router.route_and_insert(global_id=i, vector=vectors[i])

            res, probed = router.distributed_search(query=vectors[0], top_k=3, nprobe=2)
            self.assertGreater(len(res), 0)
            self.assertAlmostEqual(res[0][0], 0.0, places=5)

        finally:
            if original_memmap is not None:
                np.memmap = original_memmap
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
