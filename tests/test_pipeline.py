"""Integration tests for the complete DataPipeline."""

import os
import unittest
import numpy as np
from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder
from ann_data.pipeline import DataPipeline


class TestDataPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.output_file = "tests/temp_pipeline_output.dat"
        self.config = PipelineConfig(
            embedding_dim=128,
            batch_size=4,
            max_records=50,
            output_memmap_path=self.output_file,
            minhash_threshold=0.75,
        )
        self.embedder = MockEmbedder(dim=self.config.embedding_dim, seed=99)
        self.pipeline = DataPipeline(config=self.config, embedder=self.embedder)

    def tearDown(self):
        self.pipeline.close()
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_end_to_end_streaming_pipeline(self):
        sample_stream = [
            ("doc1", "<p>Nghiên cứu khoa học máy tính tại Việt Nam.</p>"),
            ("doc2", "<div>Nghiên cứu khoa học máy tính tại Việt Nam.</div>"),  # Duplicate of doc1
            ("doc3", "Mô hình ngôn ngữ lớn đang phát triển rất mạnh mẽ."),
            ("doc4", "https://example.com/spam Đây là bài viết spam liên kết cần lọc bỏ."),
            ("doc5", "   "),  # Empty text, should be skipped
            ("doc6", "Thị trường bất động sản ghi nhận nhiều tín hiệu phục hồi tích cực."),
        ]

        stats = self.pipeline.process_stream(sample_stream, log_interval=2)

        # Verification
        self.assertEqual(stats["total_input"], 6)
        self.assertGreaterEqual(stats["total_duplicates"], 1)
        self.assertEqual(stats["storage_written_records"], stats["total_valid_embedded"])
        
        # Verify physical file existence and correct shape
        self.assertTrue(os.path.exists(self.output_file))
        mmap = np.memmap(
            self.output_file,
            dtype="float32",
            mode="r",
            shape=(self.config.max_records, self.config.embedding_dim),
        )
        # Check that written vectors contain non-zero numbers
        self.assertTrue(np.any(mmap[0] != 0))
        del mmap


if __name__ == "__main__":
    unittest.main()
