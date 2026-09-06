"""Kịch bản dòng lệnh thực thi thu thập dữ liệu toàn văn đa nguồn và lưu trữ theo Shard."""

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

from crawler import CrawlerConfig, CrawlerPipeline
from ann_data.utils import get_logger


def main():
    parser = argparse.ArgumentParser(description="Chạy thu thập dữ liệu toàn văn tiếng Việt đa nguồn.")
    parser.add_argument(
        "--source",
        type=str,
        default="rss",
        choices=["rss", "legal", "hf", "all"],
        help="Nguồn dữ liệu cần thu thập (rss, legal, hf, all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Số lượng bản ghi tối đa cần thu thập",
    )
    parser.add_argument(
        "--shard-size",
        type=int,
        default=50000,
        help="Số lượng bản ghi trên mỗi tệp shard",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/crawl",
        help="Thư mục lưu trữ các tệp shard toàn văn",
    )
    args = parser.parse_args()

    logger = get_logger("run_crawler")
    logger.info("=== BẮT ĐẦU THU THẬP DỮ LIỆU TOÀN VĂN ===")
    logger.info("  Nguồn: %s | Giới hạn: %d | Thư mục: %s", args.source.upper(), args.limit, args.output_dir)

    config = CrawlerConfig(output_dir=args.output_dir, shard_size=args.shard_size)
    pipeline = CrawlerPipeline(config=config)

    if args.source == "all":
        pipeline.run_full_crawl(limit=args.limit)
    elif args.source == "rss":
        pipeline.run_rss_crawl(limit=args.limit)
    elif args.source == "legal":
        pipeline.run_legal_crawl(limit=args.limit)
    elif args.source == "hf":
        pipeline.run_hf_streaming(limit=args.limit)

    logger.info("=== HOÀN TẤT THU THẬP DỮ LIỆU ===")


if __name__ == "__main__":
    main()
