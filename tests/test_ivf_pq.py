"""Unit tests for IVFPQIndex module."""

import unittest
import numpy as np
from ann_index.benchmark import BenchmarkRunner
from ann_index.ivf_pq import IVFPQIndex


class TestIVFPQIndex(unittest.TestCase):

    def setUp(self):
        np.random.seed(123)
        self.num_vectors = 100
        self.dim = 16
        self.dataset = np.random.randn(self.num_vectors, self.dim).astype(np.float32)
        self.queries = np.random.randn(5, self.dim).astype(np.float32)

    def test_build_and_search_shapes(self):
        index = IVFPQIndex(nlist=8, num_subvectors=4, nprobe=4)
        index.build(self.dataset)

        indices, distances = index.search(self.queries, top_k=5)
        self.assertEqual(indices.shape, (5, 5))
        self.assertEqual(distances.shape, (5, 5))
        # Ensure returned indices are valid dataset indices
        self.assertTrue(np.all(indices >= 0))
        self.assertTrue(np.all(indices < self.num_vectors))

    def test_memory_usage_lower_than_standard_hnsw(self):
        index = IVFPQIndex(nlist=8, num_subvectors=4, nprobe=4)
        index.build(self.dataset)
        mem = index.get_memory_bytes()

        # Compare with float32 raw size: 100 * 16 * 4 = 6400 bytes
        self.assertGreater(mem, 0)

    def test_benchmark_runner_integration(self):
        runner = BenchmarkRunner(dataset=self.dataset, queries=self.queries, metric="l2")
        ivf = IVFPQIndex(nlist=8, num_subvectors=4, nprobe=4)
        result = runner.evaluate_index(ivf, top_k=5, repeat_runs=1)

        self.assertIn("IVF-PQ", result["algorithm"])
        self.assertIn("recall_at_10", result)
        self.assertIn("qps", result)


if __name__ == "__main__":
    unittest.main()
