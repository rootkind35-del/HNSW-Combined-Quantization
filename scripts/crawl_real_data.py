"""Kịch bản cào tin tức tiếng Việt thực tế từ RSS và lập chỉ mục lưu trữ Memmap."""

import argparse
import json
import os
import sys
import time

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path để import các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.loaders.news_crawler import NewsRssCrawler
from ann_data.pipeline import DataPipeline
from ann_data.utils import get_logger


def crawl_and_index(
    limit: int = 50,
    output_dir: str = "data/processed",
    batch_size: int = 16,
    use_mock_embedder: bool = False,
):
    """
    Thu thập tin tức từ các kênh RSS trực tiếp, xử lý pipeline và lưu trữ vector cùng siêu dữ liệu.

    Tham số:
        limit: Số lượng bài viết tối đa cần cào và lập chỉ mục.
        output_dir: Thư mục lưu trữ kết quả (vector .dat và metadata .jsonl).
        batch_size: Kích thước lô nhúng vector.
        use_mock_embedder: Nếu True, dùng vector giả lập để chạy thử nghiệm nhanh.
    """
    logger = get_logger("crawl_real_data")
    os.makedirs(output_dir, exist_ok=True)

    vector_file = os.path.join(output_dir, "real_news_vectors.dat")
    meta_file = os.path.join(output_dir, "real_news_metadata.jsonl")

    config = PipelineConfig(
        embedding_dim=384,
        batch_size=batch_size,
        max_records=max(limit, 100),
        output_memmap_path=vector_file,
    )

    if use_mock_embedder:
        embedder = MockEmbedder(dim=config.embedding_dim)
        logger.info("Sử dụng MockEmbedder để xác minh nhanh luồng ghi")
    else:
        embedder = SentenceTransformerEmbedder(model_name=config.model_name, dim=config.embedding_dim)
        logger.info("Sử dụng mô hình ngôn ngữ SentenceTransformer: %s", config.model_name)

    crawler = NewsRssCrawler()
    logger.info("Khởi chạy thu thập tin tức thời sự trực tiếp (chỉ tiêu: %d bài viết)...", limit)

    saved_metadata = []
    start_time = time.perf_counter()

    with DataPipeline(config=config, embedder=embedder) as pipeline:
        # Lấy luồng bài viết từ bộ cào tin tức RSS
        for doc_id, raw_text in crawler.stream(limit=limit):
            processed_text = pipeline.process_item(doc_id, raw_text)
            if processed_text is not None:
                pipeline.batch_embedder.add(processed_text)
                
                # Trích xuất dòng đầu tiên làm tiêu đề bài viết
                lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
                title = lines[0] if lines else "Không có tiêu đề"
                preview = lines[1] if len(lines) > 1 else processed_text[:150]

                record_meta = {
                    "vector_idx": len(saved_metadata),
                    "doc_id": doc_id,
                    "title": title,
                    "preview": preview[:200],
                    "token_count": len(processed_text.split()),
                }
                saved_metadata.append(record_meta)
                logger.info(
                    "Đã lập chỉ mục [%03d]: %s (tokens: %d)",
                    record_meta["vector_idx"],
                    title[:60],
                    record_meta["token_count"],
                )

        pipeline.batch_embedder.flush()

    elapsed = time.perf_counter() - start_time
    total_written = len(saved_metadata)

    # Lưu trữ danh sách thông tin bài báo vào tệp JSONL
    with open(meta_file, "w", encoding="utf-8") as f:
        for item in saved_metadata:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("Hoàn tất cào báo và lập chỉ mục trong %.2f giây.", elapsed)
    logger.info("Tổng số bài báo thực tế đã lập chỉ mục: %d", total_written)
    logger.info("Tệp nhị phân vector memmap: %s", vector_file)
    logger.info("Tệp siêu dữ liệu metadata: %s", meta_file)

    return {
        "total_written": total_written,
        "vector_file": vector_file,
        "meta_file": meta_file,
        "elapsed_seconds": round(elapsed, 2),
    }


def main():
    """Hàm thực thi chính khi gọi script từ dòng lệnh."""
    parser = argparse.ArgumentParser(description="Cào tin tức tiếng Việt thực tế và lưu trữ vào memmap.")
    parser.add_argument("--limit", type=int, default=30, help="Số lượng bài viết cần cào")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Thư mục xuất dữ liệu")
    parser.add_argument("--batch-size", type=int, default=16, help="Kích thước lô nhúng")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Sử dụng MockEmbedder khi không có mạng")
    args = parser.parse_args()

    crawl_and_index(
        limit=args.limit,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        use_mock_embedder=args.use_mock_embedder,
    )


if __name__ == "__main__":
    main()

