"""CLI execution script for data pipeline."""

import argparse
import os
import sys

# Ensure src/ is on python path when running script directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.pipeline import DataPipeline
from ann_data.utils import get_logger


def sample_stream_generator(count: int):
    """Generates synthetic Vietnamese text samples for pipeline verification."""
    templates = [
        "Trí tuệ nhân tạo và học máy đang thay đổi cách các doanh nghiệp vận hành.",
        "Nghiên cứu thuật toán láng giềng gần đúng Approximate Nearest Neighbor trên tập dữ liệu lớn.",
        "Hà Nội bước vào mùa thu với tiết trời se lạnh và bầu không khí trong lành.",
        "<p>Tin tức kinh tế: Thị trường chứng khoán ghi nhận phiên tăng điểm mạnh mẽ. Xem thêm tại https://example.com</p>",
        "Tìm kiếm vector ngữ nghĩa kết hợp kỹ thuật nén lượng tử hóa HNSW.",
    ]
    for i in range(count):
        idx = i % len(templates)
        doc_id = f"doc_{i:08d}"
        text = f"{templates[idx]} Bản ghi số {i}."
        yield doc_id, text


def main():
    parser = argparse.ArgumentParser(description="Run the ANN Vietnamese Data Pipeline.")
    parser.add_argument("--config", type=str, default="configs/default_pipeline.json", help="Path to config JSON file")
    parser.add_argument("--sample-size", type=int, default=1000, help="Number of synthetic samples to run")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Use fast MockEmbedder instead of neural model")
    parser.add_argument("--output-memmap", type=str, default=None, help="Override output memmap file path")
    args = parser.parse_args()

    logger = get_logger("run_pipeline")

    if os.path.exists(args.config):
        config = PipelineConfig.from_json(args.config)
        logger.info("Loaded configuration from %s", args.config)
    else:
        config = PipelineConfig()
        logger.info("Using default configuration")

    if args.output_memmap:
        config.output_memmap_path = args.output_memmap
    config.max_records = max(config.max_records, args.sample_size)

    # Instantiate embedder
    if args.use_mock_embedder:
        embedder = MockEmbedder(dim=config.embedding_dim)
        logger.info("Using MockEmbedder (fast simulation mode)")
    else:
        embedder = SentenceTransformerEmbedder(model_name=config.model_name, dim=config.embedding_dim)
        logger.info("Using SentenceTransformerEmbedder: %s", config.model_name)

    logger.info("Initialising DataPipeline with %d sample documents...", args.sample_size)
    stream = sample_stream_generator(args.sample_size)

    with DataPipeline(config=config, embedder=embedder) as pipeline:
        stats = pipeline.process_stream(stream, log_interval=max(1, args.sample_size // 5))

    logger.info("Execution finished successfully.")
    for k, v in stats.items():
        logger.info("  %s: %s", k, v)


if __name__ == "__main__":
    main()
