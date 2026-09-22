"""Comprehensive empirical stress testing suite for Core ANN Index.

Covers:
1. Concurrency and cache hit/miss churn on DirectIOManager.async_read_batch.
2. ShardedIVFHNSW parameter variations, edge-case vectors, nprobe, top_k, and graph sizes.
3. Early-exit (tau, epsilon) loop termination guarantees under adversarial graph structures.
4. Strict prohibition of numpy.memmap at runtime and static code inspection.
"""

import ast
import inspect
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import numpy as np

# Ensure src is in sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from ann_index.hnsw_quantized import distance_adc, exact_distance_l2, quantize_adc
from ann_index.io_manager import ApplicationLRUCache, DirectIOManager
from ann_index.two_tier_hnsw import LocalShard, ShardedIVFHNSW


class TestDirectIOManagerConcurrency(unittest.TestCase):
    """Stress tests for DirectIOManager and ApplicationLRUCache under concurrent churn."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="stress_io_")
        self.dim = 32
        self.file_path = os.path.join(self.test_dir, "test_store.bin")
        self.io_manager = DirectIOManager(filepath=self.file_path, dim=self.dim, cache_capacity=10)

        # Prepopulate with 100 vectors
        np.random.seed(42)
        self.num_vectors = 100
        self.ground_truth = np.random.randn(self.num_vectors, self.dim).astype(np.float32)
        self.io_manager.write_batch(self.ground_truth)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_async_read_batch_data_integrity(self):
        """Verify data integrity under concurrent batch reads."""
        num_threads = 20
        queries_per_thread = 25
        errors = []

        def worker(tid: int):
            rng = np.random.RandomState(tid * 100 + 1)
            for _ in range(queries_per_thread):
                ids = rng.choice(self.num_vectors, size=8, replace=False).tolist()
                try:
                    res = self.io_manager.async_read_batch(ids)
                    if set(res.keys()) != set(ids):
                        errors.append(f"TID {tid}: Key mismatch")
                        return
                    for vid in ids:
                        if not np.array_equal(res[vid], self.ground_truth[vid]):
                            errors.append(f"TID {tid}: Data mismatch on vid {vid}")
                            return
                except Exception as e:
                    errors.append(f"TID {tid} failed: {type(e).__name__}: {e}")
                    return

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors in concurrent batch read: {errors[:5]}")

    def test_lru_cache_thread_safety_race_condition(self):
        """Stress test ApplicationLRUCache for thread-safety during concurrent eviction/retrieval.

        Identifies whether ApplicationLRUCache raises KeyError when multiple threads
        access and evict entries simultaneously under thread switching.
        """
        old_switch = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        cache = ApplicationLRUCache(capacity=3)
        errors = []

        def reader():
            for _ in range(5000):
                try:
                    _ = cache.get(1)
                except KeyError as e:
                    errors.append(f"KeyError in get: {e}")
                    break
                except Exception as e:
                    errors.append(f"Exception in get: {e}")
                    break

        def writer():
            dummy = np.zeros(4, dtype=np.float32)
            for i in range(5000):
                try:
                    cache.put(i % 10, dummy)
                except Exception as e:
                    errors.append(f"Exception in put: {e}")
                    break

        try:
            threads = [threading.Thread(target=reader) for _ in range(10)] + [
                threading.Thread(target=writer) for _ in range(10)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            sys.setswitchinterval(old_switch)

        # Note: If cache is unsynchronized, KeyError occurs when get() races with put() eviction.
        self.assertEqual(len(errors), 0, f"ApplicationLRUCache is not thread-safe: {errors[:5]}")

    def test_async_read_batch_concurrent_churn_race_condition(self):
        """Stress test DirectIOManager.async_read_batch under heavy thread contention with tiny cache."""
        old_switch = sys.getswitchinterval()
        sys.setswitchinterval(1e-6)
        try:
            io = DirectIOManager(filepath=self.file_path, dim=self.dim, cache_capacity=3)
            errors = []

            def stress_worker():
                rng = np.random.RandomState()
                for _ in range(150):
                    try:
                        ids = rng.choice(20, size=5, replace=False).tolist()
                        res = io.async_read_batch(ids)
                        if len(res) != 5:
                            errors.append(f"Incomplete batch: {len(res)}")
                    except Exception as e:
                        errors.append(f"{type(e).__name__}: {e}")
                        break

            threads = [threading.Thread(target=stress_worker) for _ in range(25)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(len(errors), 0, f"async_read_batch failed under concurrency: {errors[:5]}")
        finally:
            sys.setswitchinterval(old_switch)

    def test_async_read_batch_edge_cases(self):
        """Verify behavior on empty batch, duplicate IDs, and out-of-bounds IDs."""
        # Empty batch
        self.assertEqual(self.io_manager.async_read_batch([]), {})

        # Duplicate IDs in batch
        res_dup = self.io_manager.async_read_batch([5, 5, 12, 12, 5])
        self.assertEqual(set(res_dup.keys()), {5, 12})
        np.testing.assert_allclose(res_dup[5], self.ground_truth[5])
        np.testing.assert_allclose(res_dup[12], self.ground_truth[12])

        # Out-of-bounds vector_id (returns zero vector fallback)
        res_oob = self.io_manager.async_read_batch([99999])
        self.assertIn(99999, res_oob)
        self.assertTrue(np.all(res_oob[99999] == 0.0))


class TestShardedIVFHNSWStressAndEdgeCases(unittest.TestCase):
    """Stress tests for ShardedIVFHNSW across parameter boundaries and edge case inputs."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="stress_hnsw_")
        self.dim = 16
        self.num_shards = 4
        self.router = ShardedIVFHNSW(
            dim=self.dim,
            num_shards=self.num_shards,
            capacity_per_shard=50,
            storage_dir=self.test_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_edge_case_vector_values(self):
        """Test zero vectors, extreme values within float16, and normal vectors."""
        # 1. Zero vector
        zero_vec = np.zeros(self.dim, dtype=np.float32)
        s0 = self.router.route_and_insert(global_id=0, vector=zero_vec)
        self.assertIn(s0, range(self.num_shards))

        # 2. Extreme values within float16 range (e.g., 5000.0)
        extreme_vec = np.full(self.dim, 5000.0, dtype=np.float32)
        s1 = self.router.route_and_insert(global_id=1, vector=extreme_vec)
        self.assertIn(s1, range(self.num_shards))

        # 3. Random normal vectors
        np.random.seed(123)
        for i in range(2, 20):
            v = np.random.randn(self.dim).astype(np.float32)
            self.router.route_and_insert(global_id=i, vector=v)

        # Search for zero vector
        res_zero, _ = self.router.distributed_search(zero_vec, top_k=3, nprobe=4)
        self.assertGreater(len(res_zero), 0)
        # Global ID 0 should be top result with 0.0 distance
        top_dist, top_gid, _ = res_zero[0]
        self.assertEqual(top_gid, 0)
        self.assertAlmostEqual(top_dist, 0.0, places=4)

        # Search for extreme vector
        res_ext, _ = self.router.distributed_search(extreme_vec, top_k=3, nprobe=4)
        self.assertGreater(len(res_ext), 0)
        self.assertEqual(res_ext[0][1], 1)
        self.assertAlmostEqual(res_ext[0][0], 0.0, places=3)

    def test_varied_nprobe(self):
        """Test nprobe=1, nprobe=2, nprobe=num_shards, nprobe > num_shards, nprobe <= 0."""
        np.random.seed(456)
        for i in range(30):
            self.router.route_and_insert(i, np.random.randn(self.dim).astype(np.float32))

        q = np.random.randn(self.dim).astype(np.float32)

        # nprobe = 1
        res1, p1 = self.router.distributed_search(q, top_k=5, nprobe=1)
        self.assertEqual(len(p1), 1)

        # nprobe = 2
        res2, p2 = self.router.distributed_search(q, top_k=5, nprobe=2)
        self.assertEqual(len(p2), 2)

        # nprobe = num_shards
        res_all, p_all = self.router.distributed_search(q, top_k=5, nprobe=self.num_shards)
        self.assertEqual(len(p_all), self.num_shards)

        # nprobe > num_shards (should clamp to num_shards)
        res_over, p_over = self.router.distributed_search(q, top_k=5, nprobe=100)
        self.assertEqual(len(p_over), self.num_shards)

        # nprobe <= 0 (should clamp to 1)
        res_zero, p_zero = self.router.distributed_search(q, top_k=5, nprobe=0)
        self.assertEqual(len(p_zero), 1)
        res_neg, p_neg = self.router.distributed_search(q, top_k=5, nprobe=-5)
        self.assertEqual(len(p_neg), 1)

    def test_varied_top_k(self):
        """Test top_k=0, top_k=1, top_k=10, top_k > indexed count, top_k > re_rank_limit."""
        np.random.seed(789)
        for i in range(15):
            self.router.route_and_insert(i, np.random.randn(self.dim).astype(np.float32))

        q = np.random.randn(self.dim).astype(np.float32)

        # top_k = 0
        res0, _ = self.router.distributed_search(q, top_k=0, nprobe=4)
        self.assertEqual(len(res0), 0)

        # top_k = 1
        res1, _ = self.router.distributed_search(q, top_k=1, nprobe=4)
        self.assertEqual(len(res1), 1)

        # top_k > total vectors (15 vectors in index, top_k=50)
        res_large, _ = self.router.distributed_search(q, top_k=50, nprobe=4, re_rank_limit=50)
        self.assertLessEqual(len(res_large), 15)

        # top_k > re_rank_limit (re_rank_limit=3, top_k=10)
        res_limited, _ = self.router.distributed_search(q, top_k=10, nprobe=4, re_rank_limit=3)
        self.assertLessEqual(len(res_limited), 3)

        # Validate sorting
        dists = [r[0] for r in res_large]
        self.assertEqual(dists, sorted(dists))

    def test_edge_case_graph_sizes(self):
        """Test empty index, single vector, single shard populated, and dynamic capacity expansion."""
        q = np.ones(self.dim, dtype=np.float32)

        # Case 1: Completely empty index
        empty_res, empty_shards = self.router.distributed_search(q, top_k=5)
        self.assertEqual(empty_res, [])
        self.assertGreater(len(empty_shards), 0)

        # Case 2: Exactly 1 vector in index
        self.router.route_and_insert(42, q)
        single_res, _ = self.router.distributed_search(q, top_k=5, nprobe=4)
        self.assertEqual(len(single_res), 1)
        self.assertEqual(single_res[0][1], 42)
        self.assertAlmostEqual(single_res[0][0], 0.0, places=4)

        # Case 3: Dynamic capacity expansion (_ensure_capacity)
        # Initial capacity per shard was 50. Insert 120 vectors directly into shard 0.
        shard0 = self.router.shards[0]
        initial_cap = shard0.max_elements
        self.assertEqual(initial_cap, 100)  # max(100, 50) = 100
        for i in range(120):
            shard0.add_node(global_id=1000 + i, vector=np.random.randn(self.dim).astype(np.float32))

        self.assertGreater(shard0.max_elements, initial_cap)
        self.assertEqual(shard0.local_count, 120 + (1 if shard0.entry_point == 0 else 0))
        # Ensure search works after expansion
        res_exp = shard0._search_local_graph(q, entry_point=shard0.entry_point, ef=20)
        self.assertGreater(len(res_exp), 0)


class TestEarlyExitTerminationGuarantees(unittest.TestCase):
    """Stress tests for early-exit stopping conditions (tau, epsilon) under pathological topologies."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="stress_ee_")
        self.dim = 8
        self.shard = LocalShard(0, dim=self.dim, max_elements=100, storage_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pathological_plateau_graph(self):
        """All nodes have identical vectors; distance delta is always 0.0 < epsilon.

        Early exit should trigger after examining at most tau non-improving steps.
        """
        ident_vec = np.ones(self.dim, dtype=np.float32)
        for i in range(30):
            self.shard.add_node(i, ident_vec, M=16, ef_construction=20)

        query = np.zeros(self.dim, dtype=np.float32)

        # When tau=2, traversal should stop quickly
        results_tau2 = self.shard._search_local_graph(query, entry_point=0, ef=20, tau=2, epsilon=1e-4)
        self.assertGreater(len(results_tau2), 0)
        self.assertLessEqual(len(results_tau2), 4)

        # When tau=10, traversal explores more
        results_tau10 = self.shard._search_local_graph(query, entry_point=0, ef=20, tau=10, epsilon=1e-4)
        self.assertGreaterEqual(len(results_tau10), len(results_tau2))

    def test_extreme_tau_and_epsilon_parameters_terminate(self):
        """Verify graph traversal terminates without infinite loops under boundary parameters."""
        for i in range(25):
            self.shard.add_node(i, np.random.randn(self.dim).astype(np.float32), M=8, ef_construction=10)

        q = np.random.randn(self.dim).astype(np.float32)

        for tau in [0, 1, 2, 10, 1000]:
            for eps in [-10.0, 0.0, 1e-6, 1.0, 1e5]:
                start_time = time.time()
                res = self.shard._search_local_graph(q, entry_point=0, ef=15, tau=tau, epsilon=eps)
                elapsed = time.time() - start_time
                self.assertLess(elapsed, 0.5, f"Search exceeded 0.5s with tau={tau}, eps={eps}!")
                self.assertIsInstance(res, list)

    def test_cyclic_graph_termination(self):
        """Manually construct a directed ring graph to stress visited tracking."""
        self.shard.local_count = 10
        self.shard.entry_point = 0
        self.shard.graph = {i: [(i + 1) % 10] for i in range(10)}
        self.shard.quantized = np.random.randint(0, 255, size=(10, self.dim), dtype=np.uint8)
        self.shard.scales = np.full((10, 1), 0.01, dtype=np.float16)
        self.shard.offsets = np.zeros((10, 1), dtype=np.float16)

        q = np.zeros(self.dim, dtype=np.float32)
        res = self.shard._search_local_graph(q, entry_point=0, ef=10, tau=100)
        # Ring of 10 nodes must terminate after exactly 10 nodes are visited
        self.assertEqual(len(res), 10)


class TestZeroMemmapEnforcement(unittest.TestCase):
    """Verify that numpy.memmap is never invoked at runtime or imported in core modules."""

    def test_runtime_memmap_interception(self):
        """Monkeypatch numpy.memmap and execute complete core indexing workflow."""
        memmap_invoked = False

        def trap(*args, **kwargs):
            nonlocal memmap_invoked
            memmap_invoked = True
            raise AssertionError("CRITICAL: numpy.memmap was invoked at runtime!")

        orig_memmap = np.memmap
        np.memmap = trap

        test_dir = tempfile.mkdtemp(prefix="memmap_trap_")
        try:
            # 1. DirectIOManager operations
            io = DirectIOManager(os.path.join(test_dir, "io.bin"), dim=16, cache_capacity=5)
            idx0 = io.write_vector(np.ones(16, dtype=np.float32))
            io.write_batch(np.random.randn(10, 16).astype(np.float32))
            io.lru_cache.clear()
            _ = io.get_vector(idx0)
            _ = io.async_read_batch([0, 1, 2, 3])

            # 2. ShardedIVFHNSW routing, local graphs, SSD append, and search with re-ranking
            router = ShardedIVFHNSW(
                dim=16, num_shards=3, capacity_per_shard=20, storage_dir=os.path.join(test_dir, "shards")
            )
            for i in range(20):
                router.route_and_insert(i, np.random.randn(16).astype(np.float32))

            # Clear shard LRU caches to force direct binary file seek/read during re-ranking
            for s in router.shards:
                s.io_manager.lru_cache.clear()

            q = np.random.randn(16).astype(np.float32)
            results, probed = router.distributed_search(q, top_k=5, nprobe=3, re_rank_limit=10)

            self.assertFalse(memmap_invoked, "numpy.memmap was invoked during execution!")
            self.assertGreater(len(results), 0)
        finally:
            np.memmap = orig_memmap
            shutil.rmtree(test_dir, ignore_errors=True)

    def test_static_code_inspection_zero_memmap(self):
        """AST inspect core index files to ensure zero imports or references to memmap."""
        core_files = [
            os.path.join(_SRC_DIR, "ann_index", "io_manager.py"),
            os.path.join(_SRC_DIR, "ann_index", "hnsw_quantized.py"),
            os.path.join(_SRC_DIR, "ann_index", "two_tier_hnsw.py"),
        ]

        for filepath in core_files:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertNotIn("numpy.memmap", content, f"Found numpy.memmap in {filepath}")
            self.assertNotIn("np.memmap", content, f"Found np.memmap in {filepath}")
            self.assertNotIn("import mmap", content, f"Found mmap import in {filepath}")

            # Parse AST to inspect all Call and Attribute nodes
            tree = ast.parse(content, filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr == "memmap":
                    self.fail(f"AST node references 'memmap' in {filepath} at line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
