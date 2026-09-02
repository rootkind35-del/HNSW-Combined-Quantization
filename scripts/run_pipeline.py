"""Kịch bản thực thi Pipeline xử lý dữ liệu lớn tiếng Việt (CLI Execution Pipeline)."""

import argparse
import os
import sys

# Thêm thư mục src/ vào sys.path để import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.pipeline import DataPipeline
from ann_data.utils import get_logger


def sample_stream_generator(count: int):
    """
    Sinh các mẫu văn bản tiếng Việt mẫu để kiểm tra hoạt động của Pipeline.

    Tham số:
        count: Số lượng mẫu văn bản cần sinh.

    Sinh ra:
        Tuple[str, str]: (doc_id, text)
    """
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
    """Hàm chạy dòng lệnh chính khởi động luồng pipeline."""
    parser = argparse.ArgumentParser(description="Chạy Pipeline tiền xử lý và nhúng vector tiếng Việt.")
    parser.add_argument("--config", type=str, default="configs/default_pipeline.json", help="Đường dẫn tệp cấu hình JSON")
    parser.add_argument("--sample-size", type=int, default=1000, help="Số lượng mẫu kiểm tra")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Dùng MockEmbedder để mô phỏng nhanh")
    parser.add_argument("--output-memmap", type=str, default=None, help="Ghi đè đường dẫn tệp xuất memmap")
    args = parser.parse_args()

    logger = get_logger("run_pipeline")

    if os.path.exists(args.config):
        config = PipelineConfig.from_json(args.config)
        logger.info("Đã nạp cấu hình từ %s", args.config)
    else:
        config = PipelineConfig()
        logger.info("Sử dụng cấu hình mặc định")

    if args.output_memmap:
        config.output_memmap_path = args.output_memmap
    config.max_records = max(config.max_records, args.sample_size)

    # Khởi tạo bộ nhúng vector
    if args.use_mock_embedder:
        embedder = MockEmbedder(dim=config.embedding_dim)
        logger.info("Sử dụng MockEmbedder (chế độ mô phỏng nhanh không cần mô hình nơ-ron)")
    else:
        embedder = SentenceTransformerEmbedder(model_name=config.model_name, dim=config.embedding_dim)
        logger.info("Sử dụng SentenceTransformerEmbedder: %s", config.model_name)

    logger.info("Khởi chạy DataPipeline với %d tài liệu mẫu...", args.sample_size)
    stream = sample_stream_generator(args.sample_size)

    with DataPipeline(config=config, embedder=embedder) as pipeline:
        stats = pipeline.process_stream(stream, log_interval=max(1, args.sample_size // 5))

    logger.info("Thực thi pipeline hoàn tất thành công.")
    for k, v in stats.items():
        logger.info("  %s: %s", k, v)


if __name__ == "__main__":
    main()

