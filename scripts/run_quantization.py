"""Kịch bản dòng lệnh thực thi xử lý lượng tử hóa từ data/crawl/ sang data/quantized/."""

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

from quantizer import QuantizationPipeline
from ann_data.utils import get_logger


def main():
    parser = argparse.ArgumentParser(description="Chạy lượng tử hóa vector từ dữ liệu toàn văn data/crawl/ sang data/quantized/.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/crawl",
        help="Thư mục chứa các tệp shard toàn văn thô",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/quantized",
        help="Thư mục xuất vector lượng tử hóa int8 và metadata",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Giới hạn số lượng đoạn văn bản cần lượng tử hóa",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=512,
        help="Kích thước lô nhúng và lượng tử hóa",
    )
    parser.add_argument(
        "--vector-file",
        type=str,
        default=None,
        help="Đường dẫn tệp vector nhị phân thô trong data/crawl/ nếu muốn lượng tử hóa trực tiếp từ tệp vector",
    )
    parser.add_argument(
        "--use-mock-embedder",
        action="store_true",
        help="Sử dụng MockEmbedder để chạy nhanh xác minh pipeline",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Không sử dụng checkpoint, xử lý lại từ đầu",
    )
    args = parser.parse_args()

    logger = get_logger("run_quantization")
    logger.info("=== BẮT ĐẦU PIPELINE LƯỢNG TỬ HÓA VECTOR ===")
    logger.info("  Đầu vào: %s | Đầu ra: %s | Lô: %d", args.vector_file or args.input_dir, args.output_dir, args.batch_size)

    pipeline = QuantizationPipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        use_mock_embedder=args.use_mock_embedder,
    )

    if args.vector_file:
        results = pipeline.process_vector_file(
            vector_file_path=args.vector_file,
            limit=args.limit,
            batch_size=args.batch_size if args.batch_size > 64 else 50000,
        )
    else:
        results = pipeline.process(limit=args.limit, resume=not args.no_resume)

    logger.info("=== HOÀN TẤT LƯỢNG TỬ HÓA: %d VECTOR INT8 ===", results.get("total_vectors", 0))


if __name__ == "__main__":
    main()
