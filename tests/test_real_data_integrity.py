"""Integrity verification tests for real news vector and metadata files."""

import json
import os
import unittest
import numpy as np
import shutil
import tempfile
from crawler import CrawlerConfig, CrawlerPipeline
from quantizer import QuantizationPipeline


class TestRealDataIntegrity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp()
        cls.crawl_dir = os.path.join(cls.test_dir, "crawl")
        cls.quant_dir = os.path.join(cls.test_dir, "quantized")
        cls.vector_file = os.path.join(cls.quant_dir, "vectors_int8.dat")
        cls.meta_file = os.path.join(cls.quant_dir, "metadata.jsonl")
        cls.limit = 5

        # 1. Thu thập dữ liệu toàn văn bằng CrawlerPipeline vào crawl_dir
        crawl_cfg = CrawlerConfig(output_dir=cls.crawl_dir, shard_size=100)
        crawler = CrawlerPipeline(config=crawl_cfg)
        crawl_res = crawler.run_rss_crawl(limit=cls.limit)

        # 2. Lượng tử hóa bằng QuantizationPipeline sang quant_dir
        quantizer = QuantizationPipeline(
            input_dir=cls.crawl_dir,
            output_dir=cls.quant_dir,
            dim=384,
            use_mock_embedder=True,
        )
        cls.quant_res = quantizer.process(limit=10)
        cls.total_vectors = cls.quant_res["total_vectors"]

    @classmethod
    def tearDownClass(cls):
        # Clean up temporary test data directory
        if os.path.exists(cls.test_dir):
            try:
                shutil.rmtree(cls.test_dir)
            except OSError:
                pass

    def test_vector_file_structure_and_values(self):
        self.assertTrue(os.path.exists(self.vector_file), "Vector file does not exist")
        self.assertGreater(self.total_vectors, 0, "No records written")

        num_written = self.total_vectors
        dim = 384

        # Read back memmap as int8
        mmap = np.memmap(self.vector_file, dtype="int8", mode="r", shape=(num_written, dim))
        vectors = np.array(mmap)

        # Dimension and shape checks
        self.assertEqual(vectors.shape, (num_written, dim))
        self.assertEqual(vectors.dtype, np.int8)

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

        num_written = self.total_vectors
        self.assertEqual(len(lines), num_written, "Metadata count does not match vector count")

        for idx, item in enumerate(lines):
            self.assertEqual(item["vector_idx"], idx, f"Mismatched vector_idx at row {idx}")
            self.assertIn("doc_id", item)
            self.assertIn("title", item)
            self.assertIn("text", item)
            self.assertIn("token_count", item)
            self.assertGreater(item["token_count"], 0)


if __name__ == "__main__":
    unittest.main()
