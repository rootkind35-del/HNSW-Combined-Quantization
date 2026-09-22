"""Unit and integration tests for Two-Tier Quantized HNSW, ADC, DirectIOManager, and Router."""

import os
import shutil
import sys
import tempfile
import unittest
import numpy as np

# Ensure src and dashboard/scripts are in sys.path
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SRC_DIR = os.path.join(_REPO_ROOT, "src")
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "dashboard", "scripts")
for path in [_SRC_DIR, _SCRIPTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from ann_index.benchmark import BenchmarkRunner
from ann_index.flat import FlatIndex
from ann_index.hnsw_quantized import distance_adc, exact_distance_l2, quantize_adc
from ann_index.io_manager import ApplicationLRUCache, DirectIOManager
from ann_index.two_tier_hnsw import LocalShard, ShardedIVFHNSW, TwoTierQuantizedHNSW
from search_service import perform_search


class TestTwoTierQuantizedHNSW(unittest.TestCase):
    """Regression tests for existing monolithic TwoTierQuantizedHNSW."""

    def setUp(self):
        np.random.seed(1234)
        self.dim = 16
        self.num_vectors = 60
        self.dataset = np.random.randn(self.num_vectors, self.dim).astype(np.float32)
        self.queries = np.random.randn(5, self.dim).astype(np.float32)

    def test_build_and_search_shapes(self):
        index = TwoTierQuantizedHNSW(m=16, ef_search=30, tau=3, epsilon=1e-4)
        index.build(self.dataset)

        indices, distances = index.search(self.queries, top_k=5)
        self.assertEqual(indices.shape, (5, 5))
        self.assertEqual(distances.shape, (5, 5))
        for i in range(5):
            self.assertTrue(np.all(np.diff(distances[i]) >= -1e-6))

    def test_high_recall_with_reranking(self):
        flat = FlatIndex(metric="l2")
        flat.build(self.dataset)
        gt_indices = flat.generate_ground_truth(self.queries, top_k=5)

        two_tier = TwoTierQuantizedHNSW(m=16, ef_search=40, rerank_factor=3, min_rerank_k=30)
        two_tier.build(self.dataset)
        predicted_indices, _ = two_tier.search(self.queries, top_k=5)

        from ann_index.metrics import compute_recall_at_k
        recall = compute_recall_at_k(gt_indices, predicted_indices, k=5)
        self.assertGreaterEqual(recall, 0.90)

    def test_ram_footprint_reduction(self):
        two_tier = TwoTierQuantizedHNSW(m=16)
        two_tier.build(self.dataset)
        ram = two_tier.get_memory_bytes()

        raw_float_vector_bytes = self.num_vectors * self.dim * 4
        tier1_vector_bytes = self.num_vectors * self.dim * 1

        self.assertEqual(tier1_vector_bytes, raw_float_vector_bytes // 4)
        self.assertGreater(ram, tier1_vector_bytes)

    def test_benchmark_runner_integration(self):
        runner = BenchmarkRunner(dataset=self.dataset, queries=self.queries, metric="l2")
        two_tier = TwoTierQuantizedHNSW(m=16, ef_search=30)
        result = runner.evaluate_index(two_tier, top_k=5, repeat_runs=1)

        self.assertIn("TwoTierHNSW", result["algorithm"])
        self.assertGreaterEqual(result["recall_at_10"], 90.0)
        self.assertIn("qps", result)


class TestHNSWQuantizedADC(unittest.TestCase):
    """Tests for Asymmetric Distance Computation and dynamic quantization."""

    def setUp(self):
        np.random.seed(42)
        self.dim = 384
        self.vectors = np.random.randn(20, self.dim).astype(np.float32)
        self.query = np.random.randn(self.dim).astype(np.float32)

    def test_quantize_adc_numerical_properties(self):
        q_vecs, scales, offsets = quantize_adc(self.vectors)
        self.assertEqual(q_vecs.shape, (20, self.dim))
        self.assertEqual(q_vecs.dtype, np.uint8)
        self.assertEqual(scales.shape, (20, 1))
        self.assertEqual(scales.dtype, np.float16)
        self.assertEqual(offsets.shape, (20, 1))
        self.assertEqual(offsets.dtype, np.float16)

        # Dequantization should closely track original values
        reconstructed = (q_vecs.astype(np.float32) * scales.astype(np.float32)) + offsets.astype(np.float32)
        max_error = np.max(np.abs(self.vectors - reconstructed))
        # Quantization error on 256 bins is bounded
        self.assertLess(max_error, 0.05)

    def test_distance_adc_approximation_accuracy(self):
        q_vecs, scales, offsets = quantize_adc(self.vectors)
        for i in range(len(self.vectors)):
            exact_d = exact_distance_l2(self.query, self.vectors[i])
            adc_d = distance_adc(self.query, q_vecs[i], scales[i][0], offsets[i][0])
            self.assertGreater(adc_d, 0.0)
            diff = abs(exact_d - adc_d)
            # Relative difference must be within tight bound
            self.assertLess(diff / max(exact_d, 1e-6), 0.05)


class TestDirectIOManager(unittest.TestCase):
    """Tests for DirectIOManager and ApplicationLRUCache without numpy.memmap."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="direct_io_test_")
        self.file_path = os.path.join(self.test_dir, "test_shard.bin")
        self.dim = 64
        self.io_manager = DirectIOManager(filepath=self.file_path, dim=self.dim, cache_capacity=5)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_write_and_read_single_vector(self):
        np.random.seed(101)
        vec = np.random.randn(self.dim).astype(np.float32)
        idx = self.io_manager.write_vector(vec)
        self.assertEqual(idx, 0)

        # Clear cache to force direct disk read
        self.io_manager.lru_cache.clear()
        read_vec = self.io_manager.get_vector(0)
        np.testing.assert_allclose(read_vec, vec, rtol=1e-6, atol=1e-6)

    def test_lru_cache_operations(self):
        cache = ApplicationLRUCache(capacity=3)
        v1 = np.ones(4, dtype=np.float32)
        v2 = np.ones(4, dtype=np.float32) * 2
        v3 = np.ones(4, dtype=np.float32) * 3
        v4 = np.ones(4, dtype=np.float32) * 4

        cache.put(1, v1)
        cache.put(2, v2)
        cache.put(3, v3)
        self.assertEqual(len(cache), 3)

        # Touch key 1 to move to end
        self.assertIsNotNone(cache.get(1))

        # Put key 4, should evict key 2 (key 1 was touched)
        cache.put(4, v4)
        self.assertIsNone(cache.get(2))
        self.assertIsNotNone(cache.get(1))
        self.assertIsNotNone(cache.get(3))
        self.assertIsNotNone(cache.get(4))

    def test_async_read_batch_multithreaded(self):
        np.random.seed(202)
        batch = np.random.randn(15, self.dim).astype(np.float32)
        indices = self.io_manager.write_batch(batch)
        self.assertEqual(len(indices), 15)

        # Clear cache to test threaded disk reads
        self.io_manager.lru_cache.clear()
        requested_ids = [2, 5, 8, 12]
        results = self.io_manager.async_read_batch(requested_ids)
        self.assertEqual(set(results.keys()), set(requested_ids))
        for vid in requested_ids:
            np.testing.assert_allclose(results[vid], batch[vid], rtol=1e-6, atol=1e-6)

    def test_no_numpy_memmap_in_implementation(self):
        """Verify that numpy.memmap is not referenced or used in DirectIOManager."""
        import inspect
        source = inspect.getsource(DirectIOManager)
        self.assertNotIn("memmap", source.lower())
        cache_source = inspect.getsource(ApplicationLRUCache)
        self.assertNotIn("memmap", cache_source.lower())


class TestShardedIVFHNSW(unittest.TestCase):
    """Tests for ShardedIVFHNSW and LocalShard with global ID mapping."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="sharded_hnsw_test_")
        self.dim = 32
        self.num_shards = 4
        self.router = ShardedIVFHNSW(
            dim=self.dim,
            num_shards=self.num_shards,
            capacity_per_shard=200,
            storage_dir=self.test_dir,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_route_and_insert_with_id_mapping(self):
        np.random.seed(303)
        placed_shards = []
        for i in range(20):
            v = np.random.randn(self.dim).astype(np.float32)
            sid = self.router.route_and_insert(global_id=1000 + i, vector=v)
            placed_shards.append(sid)

        # Verify vectors are distributed across shards
        self.assertGreater(len(set(placed_shards)), 1)

        # Verify global ID mapping in LocalShard
        total_mapped = 0
        for shard in self.router.shards:
            for local_idx, gid in shard.id_map.items():
                self.assertGreaterEqual(gid, 1000)
                total_mapped += 1
        self.assertEqual(total_mapped, 20)

    def test_distributed_search_returns_global_id_and_shard_id(self):
        np.random.seed(404)
        vectors = []
        for i in range(30):
            v = np.random.randn(self.dim).astype(np.float32)
            vectors.append(v)
            self.router.route_and_insert(global_id=i, vector=v)

        query = vectors[5] + np.random.randn(self.dim).astype(np.float32) * 0.01
        res, probed_shards = self.router.distributed_search(
            query=query,
            top_k=3,
            nprobe=3,
            re_rank_limit=20,
            return_shards=True,
        )

        self.assertIsInstance(probed_shards, list)
        self.assertGreater(len(probed_shards), 0)
        self.assertLessEqual(len(probed_shards), 3)

        self.assertGreater(len(res), 0)
        # Each item must be (exact_dist, global_id, shard_id)
        top_dist, top_gid, top_sid = res[0]
        self.assertIsInstance(top_dist, float)
        self.assertIsInstance(top_gid, (int, np.integer))
        self.assertIsInstance(top_sid, (int, np.integer))
        # Distance to near-identical query should be very small
        self.assertLess(top_dist, 0.5)

    def test_early_exit_in_local_shard(self):
        shard = self.router.shards[0]
        np.random.seed(505)
        for i in range(15):
            v = np.random.randn(self.dim).astype(np.float32)
            shard.add_node(global_id=i, vector=v, M=4, ef_construction=10)

        query = np.random.randn(self.dim).astype(np.float32)
        results = shard._search_local_graph(query, entry_point=shard.entry_point, ef=10, tau=2, epsilon=1e-4)
        self.assertGreater(len(results), 0)
        # Results should be sorted ascending by distance
        dists = [r[0] for r in results]
        self.assertEqual(dists, sorted(dists))


class TestSearchServiceIntegration(unittest.TestCase):
    """Integration tests for search_service.py perform_search output contracts."""

    def test_perform_search_contract_and_shard_fields(self):
        resp = perform_search("kiểm tra tìm kiếm", top_k=3)
        self.assertIn("shards_probed", resp)
        self.assertIsInstance(resp["shards_probed"], list)
        self.assertGreater(len(resp["shards_probed"]), 0)

        results = resp["results"]
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)

        for item in results:
            self.assertIn("shard_id", item)
            self.assertIsInstance(item["shard_id"], int)
            self.assertIn("node_id", item)
            self.assertIn("doc_id", item)
            self.assertIn("distance", item)
            self.assertIn("similarity_score", item)

    def test_perform_search_category_filter(self):
        resp = perform_search("công nghệ thông tin", top_k=3, category="Khoa học & Công nghệ")
        self.assertIn("results", resp)
        for item in resp["results"]:
            if item.get("category") != "Văn hóa & Đời sống":
                self.assertEqual(item["category"], "Khoa học & Công nghệ")


if __name__ == "__main__":
    unittest.main()
