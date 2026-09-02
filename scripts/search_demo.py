"""Interactive CLI Semantic Search Demo querying news vectors from memmap."""

import argparse
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure src/ is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.search.semantic_engine import SemanticSearchEngine


def display_results(query: str, results: list):
    print("\n" + "=" * 70)
    print(f"KẾT QUẢ TÌM KIẾM CHO TRUY VẤN: '{query}'")
    print("=" * 70)
    if not results:
        print("Không tìm thấy kết quả phù hợp.")
        return

    for item in results:
        print(f"[{item['rank']}] Điểm tương đồng: {item['score']:.4f} | Index: {item['vector_idx']}")
        print(f"    Tiêu đề : {item['title']}")
        if item.get("preview"):
            preview_clean = item["preview"].replace("\n", " ")[:150]
            print(f"    Tóm tắt : {preview_clean}...")
        print("-" * 70)


def main():
    parser = argparse.ArgumentParser(description="Semantic Search Demo on indexed news vectors.")
    parser.add_argument("--query", type=str, default=None, help="Text query to search for")
    parser.add_argument("--vector-file", type=str, default="data/processed/real_news_vectors.dat", help="Path to vector file")
    parser.add_argument("--metadata-file", type=str, default="data/processed/real_news_metadata.jsonl", help="Path to metadata JSONL file")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top candidates to retrieve")
    parser.add_argument("--dim", type=int, default=384, help="Vector dimension")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Use MockEmbedder instead of neural model")
    args = parser.parse_args()

    if not os.path.exists(args.vector_file) or not os.path.exists(args.metadata_file):
        print(f"Error: Required data files not found in {args.vector_file} or {args.metadata_file}.")
        print("Please run 'python scripts/crawl_real_data.py' first.")
        sys.exit(1)

    if args.use_mock_embedder:
        embedder = MockEmbedder(dim=args.dim, seed=42)
    else:
        embedder = SentenceTransformerEmbedder(dim=args.dim)

    engine = SemanticSearchEngine(
        vector_file=args.vector_file,
        metadata_file=args.metadata_file,
        embedder=embedder,
        dim=args.dim,
    )

    if args.query:
        results = engine.search(args.query, top_k=args.top_k)
        display_results(args.query, results)
    else:
        print("\n=== TRÌNH TÌM KIẾM NGỮ NGHĨA BÀI BÁO (Gõ 'exit' hoặc 'quit' để thoát) ===")
        while True:
            try:
                user_query = input("\nNhập câu truy vấn: ").strip()
                if not user_query:
                    continue
                if user_query.lower() in ["exit", "quit", "q"]:
                    print("Kết thúc phiên tìm kiếm.")
                    break
                results = engine.search(user_query, top_k=args.top_k)
                display_results(user_query, results)
            except (KeyboardInterrupt, EOFError):
                print("\nKết thúc.")
                break


if __name__ == "__main__":
    main()
