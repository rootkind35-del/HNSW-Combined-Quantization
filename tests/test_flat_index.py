"""Unit tests for FlatIndex module."""

import unittest
import numpy as np
from ann_index.flat import FlatIndex


class TestFlatIndex(unittest.TestCase):

    def setUp(self):
        self.dim = 8
        self.num_vectors = 20
        np.random.seed(42)
        self.dataset = np.random.randn(self.num_vectors, self.dim).astype(np.float32)

    def test_flat_l2_exact_match(self):
        index = FlatIndex(metric="l2")
        index.build(self.dataset)

        # Query identical to vector 5
        query = self.dataset[5:6]
        indices, distances = index.search(query, top_k=3)

        self.assertEqual(indices[0, 0], 5)
        self.assertAlmostEqual(distances[0, 0], 0.0, places=5)

    def test_flat_cosine_exact_match(self):
        index = FlatIndex(metric="cosine")
        index.build(self.dataset)

        # Query is parallel to vector 3
        query = self.dataset[3:4] * 2.5
        indices, distances = index.search(query, top_k=3)

        self.assertEqual(indices[0, 0], 3)
        self.assertAlmostEqual(distances[0, 0], 0.0, places=5)

    def test_generate_ground_truth(self):
        index = FlatIndex(metric="l2")
        index.build(self.dataset)

        queries = self.dataset[:2]
        gt = index.generate_ground_truth(queries, top_k=5)

        self.assertEqual(gt.shape, (2, 5))
        self.assertEqual(gt[0, 0], 0)
        self.assertEqual(gt[1, 0], 1)

    def test_memory_usage(self):
        index = FlatIndex(metric="l2")
        index.build(self.dataset)
        mem = index.get_memory_bytes()
        # Should be at least dataset bytes: 20 * 8 * 4 = 640 bytes
        self.assertGreaterEqual(mem, 640)


if __name__ == "__main__":
    unittest.main()
