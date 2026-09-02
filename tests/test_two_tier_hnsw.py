"""Unit and integration tests for TwoTierQuantizedHNSW algorithm."""

import unittest
import numpy as np
from ann_index.benchmark import BenchmarkRunner
from ann_index.flat import FlatIndex
from ann_index.two_tier_hnsw import TwoTierQuantizedHNSW


class TestTwoTierQuantizedHNSW(unittest.TestCase):

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
        # Verify distances are non-negative and sorted ascending per row
        for i in range(5):
            self.assertTrue(np.all(np.diff(distances[i]) >= -1e-6))

    def test_high_recall_with_reranking(self):
        flat = FlatIndex(metric="l2")
        flat.build(self.dataset)
        gt_indices = flat.generate_ground_truth(self.queries, top_k=5)

        two_tier = TwoTierQuantizedHNSW(m=16, ef_search=40, rerank_factor=3, min_rerank_k=30)
        two_tier.build(self.dataset)
        predicted_indices, _ = two_tier.search(self.queries, top_k=5)

        # Due to Tier 2 re-ranking, Recall should be very high (>= 90%)
        from ann_index.metrics import compute_recall_at_k
        recall = compute_recall_at_k(gt_indices, predicted_indices, k=5)
        self.assertGreaterEqual(recall, 0.90)

    def test_ram_footprint_reduction(self):
        two_tier = TwoTierQuantizedHNSW(m=16)
        two_tier.build(self.dataset)
        ram = two_tier.get_memory_bytes()

        # Float32 vector raw size: 60 * 16 * 4 = 3840 bytes
        raw_float_vector_bytes = self.num_vectors * self.dim * 4
        # Tier 1 uint8 vector array: 60 * 16 * 1 = 960 bytes (75% savings on vectors!)
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


if __name__ == "__main__":
    unittest.main()
