"""Unit tests for StandardHNSWIndex module."""

import unittest
import numpy as np
from ann_index.hnsw import StandardHNSWIndex


class TestStandardHNSWIndex(unittest.TestCase):

    def setUp(self):
        self.dim = 16
        self.num_vectors = 50
        np.random.seed(123)
        self.dataset = np.random.randn(self.num_vectors, self.dim).astype(np.float32)

    def test_build_and_search_exact_target(self):
        index = StandardHNSWIndex(space="l2", m=16, ef_construction=100, ef_search=50)
        index.build(self.dataset)

        # Query vector identical to vector 10
        q = self.dataset[10:11]
        indices, distances = index.search(q, top_k=5)

        self.assertEqual(indices.shape, (1, 5))
        # Top 1 neighbor should locate index 10
        self.assertIn(10, indices[0, :3])

    def test_batch_query_shapes(self):
        index = StandardHNSWIndex(space="l2", m=8, ef_search=20)
        index.build(self.dataset)

        queries = np.random.randn(5, self.dim).astype(np.float32)
        indices, distances = index.search(queries, top_k=4)

        self.assertEqual(indices.shape, (5, 4))
        self.assertEqual(distances.shape, (5, 4))

    def test_memory_usage_greater_than_raw_vectors(self):
        index = StandardHNSWIndex(space="l2", m=16)
        index.build(self.dataset)
        mem = index.get_memory_bytes()
        raw_vector_bytes = self.num_vectors * self.dim * 4
        self.assertGreater(mem, raw_vector_bytes)


if __name__ == "__main__":
    unittest.main()
