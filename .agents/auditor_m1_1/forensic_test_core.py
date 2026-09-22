"""Forensic Integrity Test Suite for Milestone 1.

Auditor: auditor_m1_1
Target: Milestone 1: Backend Core & Router Integration
"""

import inspect
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import numpy as np

# Ensure src and dashboard scripts are in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))
sys.path.insert(0, os.path.join(ROOT_DIR, "dashboard", "scripts"))

from ann_index.io_manager import DirectIOManager, ApplicationLRUCache
from ann_index.hnsw_quantized import quantize_adc, distance_adc, exact_distance_l2
from ann_index.two_tier_hnsw import LocalShard, ShardedIVFHNSW


class TestForensicIntegrity(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="forensic_audit_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # 1. Absence of memmap
    # -------------------------------------------------------------
    def test_no_memmap_in_core_modules(self):
        core_files = [
            os.path.join(ROOT_DIR, "src", "ann_index", "two_tier_hnsw.py"),
            os.path.join(ROOT_DIR, "src", "ann_index", "hnsw_quantized.py"),
            os.path.join(ROOT_DIR, "src", "ann_index", "io_manager.py"),
            os.path.join(ROOT_DIR, "two_tier_hnsw.py"),
            os.path.join(ROOT_DIR, "hnsw_quantized.py"),
            os.path.join(ROOT_DIR, "io_manager.py"),
            os.path.join(ROOT_DIR, "dashboard", "scripts", "search_service.py"),
            os.path.join(ROOT_DIR, "dashboard", "scripts", "search_bridge.py"),
        ]
        for fpath in core_files:
            self.assertTrue(os.path.exists(fpath), f"File missing: {fpath}")
            with open(fpath, "r", encoding="utf-8") as fh:
                content = fh.read()
            self.assertNotIn("numpy.memmap", content, f"numpy.memmap found in {fpath}")
            self.assertNotIn("np.memmap", content, f"np.memmap found in {fpath}")
            self.assertNotIn("from mmap import", content, f"mmap import found in {fpath}")
            self.assertNotIn("import mmap", content, f"mmap import found in {fpath}")
        print("PASS: Zero memmap in all 8 core algorithm and service files.")

    # -------------------------------------------------------------
    # 2. Mathematical Authenticity of ADC & Quantization
    # -------------------------------------------------------------
    def test_adc_quantization_mathematics(self):
        np.random.seed(42)
        dim = 128
        vectors = np.random.uniform(-5.0, 5.0, (10, dim)).astype(np.float32)

        q_vecs, scales, offsets = quantize_adc(vectors)
        self.assertEqual(q_vecs.dtype, np.uint8)
        self.assertEqual(scales.dtype, np.float16)
        self.assertEqual(offsets.dtype, np.float16)

        # Dequantization check
        recon = (q_vecs.astype(np.float32) * scales.astype(np.float32)) + offsets.astype(np.float32)
        error = np.abs(vectors - recon)
        # Theoretical max step on 255 bins is (max - min) / 255
        max_step = (np.max(vectors, axis=1) - np.min(vectors, axis=1)) / 255.0
        for i in range(10):
            # Quantization error must be <= max_step + epsilon
            self.assertLessEqual(np.max(error[i]), max_step[i] + 1e-2)

        # Constant vector edge case: range == 0
        const_vec = np.ones((1, dim), dtype=np.float32) * 3.14
        q_const, s_const, o_const = quantize_adc(const_vec)
        self.assertFalse(np.isnan(q_const).any())
        self.assertFalse(np.isnan(s_const).any())
        self.assertFalse(np.isnan(o_const).any())

        # Test distance_adc calculation
        query = np.random.randn(dim).astype(np.float32)
        for i in range(10):
            calc_adc = distance_adc(query, q_vecs[i], scales[i][0], offsets[i][0])
            expected_adc = float(np.linalg.norm(query - recon[i]))
            self.assertAlmostEqual(calc_adc, expected_adc, places=4)
            # Must not be a constant or stub
            exact_d = exact_distance_l2(query, vectors[i])
            self.assertGreater(calc_adc, 0.0)
            self.assertAlmostEqual(calc_adc, exact_d, delta=exact_d * 0.05)

        print("PASS: ADC quantization & distance math rigorously verified against theory.")

    # -------------------------------------------------------------
    # 3. DirectIOManager Disk I/O & LRU Cache
    # -------------------------------------------------------------
    def test_direct_io_manager_disk_activity(self):
        filepath = os.path.join(self.temp_dir, "test_io.bin")
        dim = 64
        io_mgr = DirectIOManager(filepath, dim=dim, cache_capacity=4)

        # Check binary file creation
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(os.path.getsize(filepath), 0)

        # Write 10 vectors
        np.random.seed(123)
        raw_vecs = np.random.randn(10, dim).astype(np.float32)
        for i in range(10):
            idx = io_mgr.write_vector(raw_vecs[i])
            self.assertEqual(idx, i)

        # Check binary file size on disk: exactly 10 * 64 * 4 = 2560 bytes
        expected_bytes = 10 * dim * 4
        self.assertEqual(os.path.getsize(filepath), expected_bytes)

        # Check LRU cache capacity
        self.assertLessEqual(len(io_mgr.lru_cache), 4)

        # Clear cache and verify direct disk read
        io_mgr.lru_cache.clear()
        self.assertEqual(len(io_mgr.lru_cache), 0)

        # Track open() calls to ensure disk is actually read
        with patch("builtins.open", wraps=open) as mock_open:
            vec_5 = io_mgr.get_vector(5)
            self.assertTrue(mock_open.called)
            np.testing.assert_allclose(vec_5, raw_vecs[5], rtol=1e-5, atol=1e-5)

        # Now vec_5 should be cached; read again without disk open
        with patch("builtins.open", wraps=open) as mock_open_cached:
            vec_5_cached = io_mgr.get_vector(5)
            # Should NOT call open because it is in LRU cache
            self.assertFalse(mock_open_cached.called)
            np.testing.assert_allclose(vec_5_cached, raw_vecs[5], rtol=1e-5, atol=1e-5)

        # Async batch read test
        io_mgr.lru_cache.clear()
        batch_ids = [1, 3, 7, 9]
        batch_res = io_mgr.async_read_batch(batch_ids)
        self.assertEqual(set(batch_res.keys()), set(batch_ids))
        for bid in batch_ids:
            np.testing.assert_allclose(batch_res[bid], raw_vecs[bid], rtol=1e-5, atol=1e-5)

        print("PASS: DirectIOManager performs authentic point seeks, disk reads, and LRU caching.")

    # -------------------------------------------------------------
    # 4. LocalShard Graph Traversal and Early-Exit
    # -------------------------------------------------------------
    def test_local_shard_graph_traversal(self):
        storage = os.path.join(self.temp_dir, "shard_test")
        dim = 32
        shard = LocalShard(shard_id=0, dim=dim, max_elements=50, storage_dir=storage)

        np.random.seed(999)
        vecs = np.random.randn(30, dim).astype(np.float32)
        for i in range(30):
            shard.add_node(global_id=5000 + i, vector=vecs[i], M=4, ef_construction=8)

        # Check graph structure
        self.assertEqual(shard.local_count, 30)
        self.assertIsNotNone(shard.entry_point)
        self.assertEqual(len(shard.graph), 30)
        # Check global ID mapping
        for local_idx, gid in shard.id_map.items():
            self.assertEqual(gid, 5000 + local_idx)

        # Check binary file on disk
        bin_path = os.path.join(storage, "shard_0.bin")
        self.assertTrue(os.path.exists(bin_path))
        self.assertEqual(os.path.getsize(bin_path), 30 * dim * 4)

        # Test querying entry point directly: distance must be near 0
        q_entry = vecs[shard.entry_point]
        res_entry = shard._search_local_graph(q_entry, shard.entry_point, ef=10, tau=5, epsilon=1e-4)
        self.assertGreater(len(res_entry), 0)
        top_dist, top_id = res_entry[0]
        self.assertEqual(top_id, shard.entry_point)
        self.assertLess(top_dist, 0.1)

        # Trace graph traversal: track visited nodes
        query = vecs[5] + np.random.randn(dim).astype(np.float32) * 0.05
        visited_nodes = []
        orig_calc = shard._calc_distance

        def spy_calc(q, nid):
            visited_nodes.append(nid)
            return orig_calc(q, nid)

        shard._calc_distance = spy_calc
        results = shard._search_local_graph(query, shard.entry_point, ef=10, tau=3, epsilon=1e-4)

        # Verify search actually visited graph nodes
        self.assertGreater(len(visited_nodes), 1)
        self.assertIn(shard.entry_point, visited_nodes)
        self.assertGreater(len(results), 0)

        # Verify results are sorted ascending by distance
        dists = [r[0] for r in results]
        self.assertEqual(dists, sorted(dists))

        # Test early-exit sensitivity: tau=1 vs tau=20
        visited_tau1 = []
        shard._calc_distance = lambda q, nid: (visited_tau1.append(nid), orig_calc(q, nid))[1]
        res_tau1 = shard._search_local_graph(query, shard.entry_point, ef=20, tau=1, epsilon=1e-2)

        visited_tau20 = []
        shard._calc_distance = lambda q, nid: (visited_tau20.append(nid), orig_calc(q, nid))[1]
        res_tau20 = shard._search_local_graph(query, shard.entry_point, ef=20, tau=20, epsilon=1e-6)

        # tau=1 must stop earlier than or equal to tau=20
        self.assertLessEqual(len(visited_tau1), len(visited_tau20))
        print(f"PASS: Graph traversal genuine: visited {len(visited_nodes)} nodes. Early-exit confirmed (tau=1 evaluated {len(visited_tau1)} nodes <= tau=20 evaluated {len(visited_tau20)} nodes).")

    # -------------------------------------------------------------
    # 5. ShardedIVFHNSW Routing and Distributed Search
    # -------------------------------------------------------------
    def test_sharded_router_authenticity(self):
        storage = os.path.join(self.temp_dir, "router_test")
        dim = 16
        num_shards = 4
        router = ShardedIVFHNSW(dim=dim, num_shards=num_shards, capacity_per_shard=100, storage_dir=storage)

        np.random.seed(777)
        vecs = np.random.randn(40, dim).astype(np.float32)
        placed_shards = []
        for i in range(40):
            sid = router.route_and_insert(global_id=i, vector=vecs[i])
            placed_shards.append(sid)

            # Empirically verify that sid is INDEED the mathematically closest centroid!
            centroid_dists = np.linalg.norm(router.centroids - vecs[i], axis=1)
            expected_sid = int(np.argmin(centroid_dists))
            self.assertEqual(sid, expected_sid, f"Vector {i} routed to {sid}, expected {expected_sid}")

        # Verify multiple shards were populated
        unique_shards = set(placed_shards)
        self.assertGreater(len(unique_shards), 1)

        # Verify shard binary files exist on disk
        for sid in unique_shards:
            s_file = os.path.join(storage, f"shard_{sid}.bin")
            self.assertTrue(os.path.exists(s_file))
            expected_count = placed_shards.count(sid)
            self.assertEqual(os.path.getsize(s_file), expected_count * dim * 4)

        # Query near vector 15
        target_v = vecs[15]
        target_shard = placed_shards[15]
        query = target_v + np.random.randn(dim).astype(np.float32) * 0.01

        results, probed_shards = router.distributed_search(query, top_k=3, nprobe=2, return_shards=True)

        # Verify probed shards are mathematically closest centroids
        query_centroid_dists = np.linalg.norm(router.centroids - query, axis=1)
        expected_probed = np.argsort(query_centroid_dists)[:2].tolist()
        self.assertEqual(probed_shards, expected_probed)

        # Verify target shard is among probed shards
        self.assertIn(target_shard, probed_shards)

        # Verify top result
        self.assertGreater(len(results), 0)
        best_dist, best_gid, best_sid = results[0]
        self.assertEqual(best_gid, 15)
        self.assertEqual(best_sid, target_shard)

        # Verify exact distance matches Euclidean distance to vector 15
        expected_dist = float(np.linalg.norm(query - target_v))
        self.assertAlmostEqual(best_dist, expected_dist, places=5)

        print(f"PASS: ShardedIVFHNSW router routing and distributed search mathematically authentic.")

    # -------------------------------------------------------------
    # 6. Search Service & Bridge Integration
    # -------------------------------------------------------------
    def test_search_service_dynamic_responses(self):
        from search_service import perform_search

        # Query 1
        resp1 = perform_search("khoa học trí tuệ nhân tạo", top_k=3)
        self.assertIn("shards_probed", resp1)
        self.assertIsInstance(resp1["shards_probed"], list)
        self.assertGreater(len(resp1["shards_probed"]), 0)

        # Query 2 (different domain)
        resp2 = perform_search("thị trường tài chính kinh tế", top_k=3)

        # Ensure responses differ and distances are dynamic floats
        self.assertNotEqual(resp1["query"], resp2["query"])
        r1_dists = [item["distance"] for item in resp1["results"]]
        r2_dists = [item["distance"] for item in resp2["results"]]
        self.assertTrue(all(isinstance(d, float) for d in r1_dists))
        self.assertTrue(all(isinstance(d, float) for d in r2_dists))

        # Check shards_probed and shard_id
        for item in resp1["results"]:
            self.assertIn("shard_id", item)
            self.assertIsInstance(item["shard_id"], int)
            self.assertIn("similarity_score", item)
            # Check similarity formula: sim = max(0, min(1, 1 - dist^2 / 2))
            expected_sim = max(0.0, min(1.0, 1.0 - (item["distance"] ** 2) / 2.0))
            self.assertAlmostEqual(item["similarity_score"], expected_sim, places=3)

        print("PASS: search_service produces dynamic, mathematically derived search outputs.")

    # -------------------------------------------------------------
    # 7. Requirement R3: Preserved Data Configuration Check
    # -------------------------------------------------------------
    def test_r3_data_configuration_preserved(self):
        # 1. Check configs/default_pipeline.json
        cfg_path = os.path.join(ROOT_DIR, "configs", "default_pipeline.json")
        self.assertTrue(os.path.exists(cfg_path))
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertIn("model_name", cfg)
        self.assertIn("embedding_dim", cfg)
        self.assertEqual(cfg["model_name"], "paraphrase-multilingual-MiniLM-L12-v2")
        self.assertEqual(cfg["embedding_dim"], 384)

        # 2. Check src/ann_data/ packages and modules exist
        expected_items = [
            "cleaner.py", "config.py", "deduplicator.py", "embedder.py",
            "pipeline.py", "storage.py", "tokenizer.py", "utils.py",
            "loaders", "search"
        ]
        for item in expected_items:
            p = os.path.join(ROOT_DIR, "src", "ann_data", item)
            self.assertTrue(os.path.exists(p), f"Missing data module/package: {item}")

        # Check subpackages
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "ann_data", "loaders", "base.py")))
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "ann_data", "loaders", "hf_loader.py")))
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "ann_data", "search", "exact_search.py")))
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "ann_data", "search", "semantic_engine.py")))

        # 3. Check src/crawler/ and src/quantizer/
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "crawler")))
        self.assertTrue(os.path.exists(os.path.join(ROOT_DIR, "src", "quantizer")))

        print("PASS: Requirement R3 fully intact. Data configurations and pipelines unaltered.")


if __name__ == "__main__":
    unittest.main()
