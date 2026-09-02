"""Unit tests for metrics module."""

import unittest
import numpy as np
from ann_index.metrics import compute_latency_stats, compute_recall_at_k


class TestMetrics(unittest.TestCase):

    def test_recall_at_k_perfect(self):
        gt = np.array([
            [0, 1, 2, 3, 4],
            [10, 11, 12, 13, 14],
        ])
        preds = np.array([
            [0, 1, 2, 3, 4],
            [10, 11, 12, 13, 14],
        ])
        recall = compute_recall_at_k(gt, preds, k=5)
        self.assertEqual(recall, 1.0)

    def test_recall_at_k_partial_and_permuted(self):
        gt = np.array([
            [0, 1, 2, 3, 4],
        ])
        # In different order with 3 matches out of 5: [4, 3, 2, 98, 99]
        preds = np.array([
            [4, 3, 2, 98, 99],
        ])
        recall = compute_recall_at_k(gt, preds, k=5)
        self.assertAlmostEqual(recall, 0.6, places=5)

    def test_recall_at_k_zero(self):
        gt = np.array([[1, 2, 3]])
        preds = np.array([[4, 5, 6]])
        recall = compute_recall_at_k(gt, preds, k=3)
        self.assertEqual(recall, 0.0)

    def test_latency_stats(self):
        # 10 queries with known latencies in seconds
        # 1ms, 2ms, 3ms, ..., 10ms
        durations = [i * 0.001 for i in range(1, 11)]
        stats = compute_latency_stats(durations, num_queries=10)

        self.assertAlmostEqual(stats["mean_ms"], 5.5, places=1)
        self.assertAlmostEqual(stats["p50_ms"], 5.5, places=1)
        self.assertGreater(stats["p99_ms"], stats["p50_ms"])
        # Total duration = 0.055s -> QPS = 10 / 0.055 ~= 181.82
        self.assertAlmostEqual(stats["qps"], 181.82, places=1)


if __name__ == "__main__":
    unittest.main()
