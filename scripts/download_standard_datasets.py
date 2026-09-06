"""Kịch bản tải và chuẩn bị các tập dữ liệu đối chuẩn chuẩn mực (SIFT10K, SIFT1M) cho nghiên cứu ANN."""

import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.loaders.benchmark_loader import BenchmarkDatasetLoader
from ann_data.utils import get_logger


def main():
    parser = argparse.ArgumentParser(
        description="Tải các tập dữ liệu vector chuẩn mực quốc tế (SIFT10K / SIFT1M) phục vụ đối chuẩn HNSW."
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="sift10k",
        choices=["sift10k", "sift1m"],
        help="Tên tập dữ liệu đối chuẩn cần tải (mặc định: sift10k)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/benchmarks",
        help="Thư mục đích để lưu trữ dữ liệu tải về",
    )
    args = parser.parse_args()

    logger = get_logger("download_standard_datasets")
    logger.info("=== TIẾN HÀNH TẢI VÀ CHUẨN BỊ TẬP DỮ LIỆU ĐỐI CHUẨN: %s ===", args.dataset.upper())

    loader = BenchmarkDatasetLoader(base_dir=args.output_dir)
    data = loader.load_dataset(dataset_name=args.dataset)

    base = data["base"]
    query = data["query"]
    gt = data["groundtruth"]

    logger.info("Hoàn tất thiết lập tập dữ liệu:")
    logger.info("  - Tập Vector cơ sở (Base): %d vector, %d chiều", base.shape[0], base.shape[1])
    logger.info("  - Tập Vector truy vấn (Query): %d câu truy vấn", query.shape[0])
    logger.info("  - Mốc chuẩn (Ground Truth): %d truy vấn, k=%d", gt.shape[0], gt.shape[1])
    logger.info("Dữ liệu sẵn sàng cho các kịch bản đối chuẩn thuật toán.")


if __name__ == "__main__":
    main()
