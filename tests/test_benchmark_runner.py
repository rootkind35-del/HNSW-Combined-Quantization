"""Unit and integration tests for BenchmarkRunner module."""

import unittest
import numpy as np
from ann_index.benchmark import BenchmarkRunner
from ann_index.flat import FlatIndex
from ann_index.hnsw import StandardHNSWIndex


class TestBenchmarkRunner(unittest.TestCase):

    def setUp(self):
        np.random.seed(99)
        self.dim = 8
        self.dataset = np.random.randn(40, self.dim).astype(np.float32)
        self.queries = np.random.randn(5, self.dim).astype(np.float32)
        self.runner = BenchmarkRunner(dataset=self.dataset, queries=self.queries, metric="l2")

    def test_evaluate_flat_index_reaches_100_recall(self):
        flat = FlatIndex(metric="l2")
        result = self.runner.evaluate_index(flat, top_k=5, repeat_runs=1)

        self.assertEqual(result["recall_at_10"], 100.0)
        self.assertIn("latency_p50_ms", result)
        self.assertIn("qps", result)

    def test_run_comparison_generates_markdown_table(self):
        indices = [
            FlatIndex(metric="l2"),
            StandardHNSWIndex(space="l2", m=8, ef_search=20),
        ]
        results = self.runner.run_comparison(indices, top_k=5)
        self.assertEqual(len(results), 2)

        table_md = BenchmarkRunner.format_markdown_table(results)
        self.assertIn("| Thuật toán / Cấu hình |", table_md)
        self.assertIn("FlatIndex", table_md)
        self.assertIn("StandardHNSW", table_md)


if __name__ == "__main__":
    unittest.main()
