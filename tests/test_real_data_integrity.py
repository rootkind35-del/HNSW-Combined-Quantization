"""Integrity verification tests for real news vector and metadata files."""

import json
import os
import unittest
import numpy as np
from scripts.crawl_real_data import crawl_and_index


class TestRealDataIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.output_dir = "data/processed_test"
        cls.vector_file = os.path.join(cls.output_dir, "real_news_vectors.dat")
        cls.meta_file = os.path.join(cls.output_dir, "real_news_metadata.jsonl")
        cls.limit = 5

        # Execute a controlled run to guarantee data is present for verification
        cls.run_result = crawl_and_index(
            limit=cls.limit,
            output_dir=cls.output_dir,
            batch_size=2,
            use_mock_embedder=True,
        )

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary test data directory
        for f in [cls.vector_file, cls.meta_file]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        if os.path.exists(cls.output_dir):
            try:
                os.rmdir(cls.output_dir)
            except OSError:
                pass

    def test_vector_file_structure_and_values(self):
        self.assertTrue(os.path.exists(self.vector_file), "Vector file does not exist")
        self.assertGreater(self.run_result["total_written"], 0, "No records written")

        num_written = self.run_result["total_written"]
        dim = 384

        # Read back memmap
        mmap = np.memmap(self.vector_file, dtype="float32", mode="r", shape=(max(self.limit, 100), dim))
        vectors = np.array(mmap[:num_written])

        # Dimension and shape checks
        self.assertEqual(vectors.shape, (num_written, dim))

        # Check no NaN or Infinite values
        self.assertFalse(np.isnan(vectors).any(), "Found NaN in vector embeddings")
        self.assertFalse(np.isinf(vectors).any(), "Found Inf in vector embeddings")

        # Check vectors are non-trivial (not all zeros)
        for i in range(num_written):
            self.assertTrue(np.any(vectors[i] != 0), f"Vector at index {i} is all zeros")

    def test_metadata_file_consistency(self):
        self.assertTrue(os.path.exists(self.meta_file), "Metadata file does not exist")

        lines = []
        with open(self.meta_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    lines.append(json.loads(stripped))

        num_written = self.run_result["total_written"]
        self.assertEqual(len(lines), num_written, "Metadata count does not match vector count")

        for idx, item in enumerate(lines):
            self.assertEqual(item["vector_idx"], idx, f"Mismatched vector_idx at row {idx}")
            self.assertIn("doc_id", item)
            self.assertIn("title", item)
            self.assertIn("token_count", item)
            self.assertGreater(item["token_count"], 0)


if __name__ == "__main__":
    unittest.main()
