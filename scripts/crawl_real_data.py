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

# Ensure src/ is on python path
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
        logger.info("Using MockEmbedder for fast verification")
    else:
        embedder = SentenceTransformerEmbedder(model_name=config.model_name, dim=config.embedding_dim)
        logger.info("Using SentenceTransformerEmbedder: %s", config.model_name)

    crawler = NewsRssCrawler()
    logger.info("Initialising live crawling from news feeds (target limit: %d articles)...", limit)

    saved_metadata = []
    start_time = time.perf_counter()

    with DataPipeline(config=config, embedder=embedder) as pipeline:
        # Stream from news crawler
        for doc_id, raw_text in crawler.stream(limit=limit):
            processed_text = pipeline.process_item(doc_id, raw_text)
            if processed_text is not None:
                pipeline.batch_embedder.add(processed_text)
                
                # Extract first line as title preview
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
                    "Indexed [%03d]: %s (tokens: %d)",
                    record_meta["vector_idx"],
                    title[:60],
                    record_meta["token_count"],
                )

        pipeline.batch_embedder.flush()

    elapsed = time.perf_counter() - start_time
    total_written = len(saved_metadata)

    # Save metadata to jsonl
    with open(meta_file, "w", encoding="utf-8") as f:
        for item in saved_metadata:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    logger.info("Crawling and indexing finished successfully in %.2f seconds.", elapsed)
    logger.info("Total real articles indexed: %d", total_written)
    logger.info("Vector binary file: %s", vector_file)
    logger.info("Metadata JSONL file: %s", meta_file)

    return {
        "total_written": total_written,
        "vector_file": vector_file,
        "meta_file": meta_file,
        "elapsed_seconds": round(elapsed, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Crawl real news articles and store in memmap.")
    parser.add_argument("--limit", type=int, default=30, help="Number of articles to crawl and index")
    parser.add_argument("--output-dir", type=str, default="data/processed", help="Output directory")
    parser.add_argument("--batch-size", type=int, default=16, help="Batch size for embedding")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Use MockEmbedder for fast offline testing")
    args = parser.parse_args()

    crawl_and_index(
        limit=args.limit,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
        use_mock_embedder=args.use_mock_embedder,
    )


if __name__ == "__main__":
    main()
