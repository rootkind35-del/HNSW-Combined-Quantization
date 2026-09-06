"""Kịch bản dòng lệnh độc lập thực thi lượng tử hóa vector từ data/crawl_wiki/ sang data/quantized_wiki/."""

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

from ann_data.utils import get_logger
from quantizer import QuantizationPipeline


def main():
    parser = argparse.ArgumentParser(
        description="Chạy lượng tử hóa vector từ ngữ liệu Wikipedia data/crawl_wiki/ sang data/quantized_wiki/."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/crawl_wiki",
        help="Thư mục chứa các tệp shard toàn văn Wikipedia",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/quantized_wiki",
        help="Thư mục xuất vector lượng tử hóa int8 và metadata cho Wikipedia",
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
        help="Kích thước lô nhúng và lượng tử hóa trên GPU",
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

    logger = get_logger("run_wiki_quantization")
    logger.info("=== BẮT ĐẦU PIPELINE LƯỢNG TỬ HÓA WIKIPEDIA ===")
    logger.info("  Đầu vào: %s | Đầu ra: %s | Lô: %d", args.input_dir, args.output_dir, args.batch_size)

    pipeline = QuantizationPipeline(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        use_mock_embedder=args.use_mock_embedder,
    )

    results = pipeline.process(limit=args.limit, resume=not args.no_resume)
    logger.info("=== HOÀN TẤT LƯỢNG TỬ HÓA WIKIPEDIA: %d VECTOR INT8 ===", results.get("total_vectors", 0))


if __name__ == "__main__":
    main()
