"""Integration tests connecting DataLoaders directly with DataPipeline."""

import os
import unittest
from typing import Generator, Optional, Tuple
from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder
from ann_data.loaders.base import BaseDataLoader
from ann_data.pipeline import DataPipeline


class MockCustomLoader(BaseDataLoader):
    """Synthetic generator imitating a real live web/database data loader."""

    def __init__(self, sample_records):
        self.sample_records = sample_records

    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        count = 0
        for doc_id, text in self.sample_records:
            yield doc_id, text
            count += 1
            if limit is not None and count >= limit:
                break


class TestLoaderPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.output_file = "tests/temp_loader_pipeline_output.dat"
        self.config = PipelineConfig(
            embedding_dim=64,
            batch_size=2,
            max_records=20,
            output_memmap_path=self.output_file,
            minhash_threshold=0.8,
        )
        self.embedder = MockEmbedder(dim=self.config.embedding_dim, seed=7)
        self.pipeline = DataPipeline(config=self.config, embedder=self.embedder)

    def tearDown(self):
        self.pipeline.close()
        if os.path.exists(self.output_file):
            try:
                os.remove(self.output_file)
            except OSError:
                pass

    def test_loader_piped_into_pipeline(self):
        records = [
            (
                "src_01",
                "<b>Tin tức:</b> Đại học Quốc gia Hà Nội chính thức công bố công trình nghiên cứu khoa học máy tính mới nhất hôm nay.",
            ),
            (
                "src_02",
                "<p>Đại học Quốc gia Hà Nội chính thức công bố công trình nghiên cứu khoa học máy tính mới nhất hôm nay.</p>",
            ),
            (
                "src_03",
                "Ứng dụng tìm kiếm vector trên dữ liệu lớn với độ trễ thấp đáp ứng thời gian thực.",
            ),
            (
                "src_04",
                "Thị trường công nghệ tài chính ghi nhận mức đầu tư kỷ lục trong năm nay.",
            ),
        ]
        loader = MockCustomLoader(records)

        # Stream directly from loader into pipeline
        data_stream = loader.stream(limit=4)
        stats = self.pipeline.process_stream(data_stream)

        self.assertEqual(stats["total_input"], 4)
        self.assertGreaterEqual(stats["total_duplicates"], 1)
        self.assertEqual(stats["storage_written_records"], stats["total_valid_embedded"])
        self.assertTrue(os.path.exists(self.output_file))


if __name__ == "__main__":
    unittest.main()
