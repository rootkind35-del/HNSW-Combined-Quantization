"""Unit tests for ExactVectorSearch and SemanticSearchEngine."""

import json
import os
import unittest
import numpy as np
from ann_data.embedder import MockEmbedder
from ann_data.search.exact_search import ExactVectorSearch
from ann_data.search.semantic_engine import SemanticSearchEngine


class TestExactVectorSearch(unittest.TestCase):

    def test_identical_and_orthogonal_vectors(self):
        # 3 orthogonal unit vectors in 3D
        vectors = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float32)

        searcher = ExactVectorSearch(vectors=vectors, normalize=True)

        # Query identical to vector 0
        q0 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        results = searcher.search(q0, top_k=3)

        # Top 1 must be index 0 with score 1.0
        self.assertEqual(results[0][0], 0)
        self.assertAlmostEqual(results[0][1], 1.0, places=5)

        # Indices 1 and 2 must have score 0.0 (orthogonal)
        self.assertAlmostEqual(results[1][1], 0.0, places=5)
        self.assertAlmostEqual(results[2][1], 0.0, places=5)

    def test_top_k_ordering(self):
        # Vectors with decreasing dot product with query [1, 0]
        vectors = np.array([
            [0.2, 0.9],
            [0.9, 0.1],
            [0.5, 0.5],
        ], dtype=np.float32)

        searcher = ExactVectorSearch(vectors=vectors, normalize=True)
        query = np.array([1.0, 0.0], dtype=np.float32)

        results = searcher.search(query, top_k=2)
        self.assertEqual(len(results), 2)
        # Vector 1 has largest x-component
        self.assertEqual(results[0][0], 1)
        # Vector 2 has next largest x-component
        self.assertEqual(results[1][0], 2)
        # Scores must be strictly non-increasing
        self.assertGreaterEqual(results[0][1], results[1][1])

    def test_dimension_mismatch(self):
        vectors = np.random.randn(5, 10).astype(np.float32)
        searcher = ExactVectorSearch(vectors=vectors)
        wrong_query = np.random.randn(8).astype(np.float32)
        with self.assertRaises(ValueError):
            searcher.search(wrong_query)


class TestSemanticSearchEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = "tests/temp_search_dir"
        os.makedirs(self.test_dir, exist_ok=True)
        self.vector_file = os.path.join(self.test_dir, "test_vectors.dat")
        self.meta_file = os.path.join(self.test_dir, "test_meta.jsonl")
        self.dim = 64

        # Create dummy metadata
        sample_meta = [
            {"vector_idx": 0, "doc_id": "d0", "title": "Bản tin công nghệ trí tuệ nhân tạo"},
            {"vector_idx": 1, "doc_id": "d1", "title": "Thời tiết mưa lớn gây ngập lụt tại Hà Nội"},
            {"vector_idx": 2, "doc_id": "d2", "title": "Thị trường chứng khoán tăng điểm mạnh"},
        ]
        with open(self.meta_file, "w", encoding="utf-8") as f:
            for item in sample_meta:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # Create dummy memmap vectors
        vectors = np.random.randn(3, self.dim).astype(np.float32)
        mmap = np.memmap(self.vector_file, dtype="float32", mode="w+", shape=(3, self.dim))
        mmap[:] = vectors
        mmap.flush()
        del mmap

        self.embedder = MockEmbedder(dim=self.dim, seed=42)
        self.engine = SemanticSearchEngine(
            vector_file=self.vector_file,
            metadata_file=self.meta_file,
            embedder=self.embedder,
            dim=self.dim,
        )

    def tearDown(self):
        for f in [self.vector_file, self.meta_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_search_execution(self):
        results = self.engine.search("trí tuệ nhân tạo", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[1]["rank"], 2)
        self.assertIn("title", results[0])
        self.assertIn("score", results[0])


if __name__ == "__main__":
    unittest.main()
