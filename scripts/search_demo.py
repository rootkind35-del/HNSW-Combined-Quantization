"""Giao diện dòng lệnh tương tác tìm kiếm ngữ nghĩa (Interactive CLI Semantic Search Demo) trên dữ liệu bài báo và Wikipedia."""

import argparse
import os
import sys
import time
from typing import Any, Dict, List
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Thêm đường dẫn src/ vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.search.semantic_engine import SemanticSearchEngine
from quantizer.unified_corpus import UnifiedQuantizedCorpus


def display_results(query: str, results: list, corpus_name: str = ""):
    """In kết quả tìm kiếm ngữ nghĩa ra màn hình console với định dạng dễ đọc."""
    print("\n" + "=" * 75)
    print(f"KẾT QUẢ TÌM KIẾM CHO TRUY VẤN: '{query}' [Kho: {corpus_name.upper()}]")
    print("=" * 75)
    if not results:
        print("Không tìm thấy kết quả phù hợp.")
        return

    for item in results:
        src = item.get("corpus_source", "")
        src_tag = f" | Nguồn: [{src}]" if src else ""
        print(f"[{item['rank']}] Điểm tương đồng: {item['score']:.4f} | Index: {item['vector_idx']}{src_tag}")
        print(f"    Tiêu đề : {item['title']}")
        preview = item.get("preview") or item.get("text", "")
        if preview:
            preview_clean = preview.replace("\n", " ")[:160]
            print(f"    Nội dung: {preview_clean}...")
        print("-" * 75)


def search_unified_corpus(
    corpus: UnifiedQuantizedCorpus,
    embedder,
    query_text: str,
    top_k: int = 5,
    sample_stride: int = 1,
) -> List[Dict[str, Any]]:
    """Tìm kiếm nhanh trên kho hợp nhất bằng tích vô hướng số nguyên."""
    t0 = time.time()
    # 1. Sinh vector nhúng truy vấn float32
    q_vec = embedder.encode([query_text])[0]
    q_norm = np.linalg.norm(q_vec)
    if q_norm > 0:
        q_vec = q_vec / q_norm

    # 2. Lượng tử hóa vector truy vấn sang int8 (-128 .. 127)
    q_int8 = np.clip(np.round(q_vec * 127.0), -128, 127).astype(np.int8)

    # 3. Quét nhanh theo khối và tính điểm số
    best_scores = []
    best_indices = []

    global_offset = 0
    batch_size = 50000

    for chunk in corpus.iter_vectors(batch_size=batch_size):
        chunk_len = len(chunk)
        if sample_stride > 1:
            sub_chunk = chunk[::sample_stride]
            sub_indices = np.arange(global_offset, global_offset + chunk_len, sample_stride)
            dots = np.dot(sub_chunk.astype(np.float32), q_int8.astype(np.float32))
        else:
            sub_indices = np.arange(global_offset, global_offset + chunk_len)
            dots = np.dot(chunk.astype(np.float32), q_int8.astype(np.float32))

        # Lấy Top-K của khối hiện tại
        if len(dots) > top_k:
            top_local = np.argpartition(dots, -top_k)[-top_k:]
            top_local = top_local[np.argsort(-dots[top_local])]
        else:
            top_local = np.argsort(-dots)

        for loc in top_local:
            best_scores.append(float(dots[loc]))
            best_indices.append(int(sub_indices[loc]))

        global_offset += chunk_len

    # Gom Top-K toàn cục
    best_scores = np.array(best_scores)
    best_indices = np.array(best_indices)
    top_global = np.argsort(-best_scores)[:top_k]

    target_indices = [int(best_indices[g_pos]) for g_pos in top_global]
    meta_batch = corpus.get_metadata_batch(target_indices)

    results = []
    for rank, g_pos in enumerate(top_global, 1):
        g_idx = int(best_indices[g_pos])
        score = float(best_scores[g_pos])
        meta = meta_batch.get(g_idx, {"title": "Không đọc được metadata", "text": ""})

        results.append({
            "rank": rank,
            "score": score,
            "vector_idx": g_idx,
            "title": meta.get("title", "Không có tiêu đề"),
            "preview": meta.get("text") or meta.get("summary", ""),
            "corpus_source": meta.get("corpus_source", ""),
        })

    elapsed_ms = (time.time() - t0) * 1000
    print(f"\n[Thời gian tìm kiếm trên {len(corpus):,} vector: {elapsed_ms:.2f} ms]")
    return results


def main():
    parser = argparse.ArgumentParser(description="Chương trình demo tìm kiếm ngữ nghĩa tin tức & Wikipedia tiếng Việt.")
    parser.add_argument("--query", type=str, default=None, help="Câu truy vấn văn bản")
    parser.add_argument(
        "--corpus",
        type=str,
        default="combined",
        choices=["news", "wiki", "combined"],
        help="Kho dữ liệu tìm kiếm: 'news' (16.4M), 'wiki' (14.8M), hoặc 'combined' (31.3M)",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả láng giềng k cần trích xuất")
    parser.add_argument("--dim", type=int, default=384, help="Số chiều vector đặc trưng")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Sử dụng MockEmbedder để thử nghiệm nhanh không cần tải mô hình")
    parser.add_argument("--stride", type=int, default=5, help="Bước nhảy lấy mẫu để tìm kiếm nhanh trên 31 triệu vector (mặc định 5)")
    args = parser.parse_args()

    corpus_map = {
        "news": ("data/quantized/vectors_int8.dat", "data/quantized/metadata.jsonl"),
        "wiki": ("data/quantized_wiki/vectors_int8.dat", "data/quantized_wiki/metadata.jsonl"),
        "combined": "data/quantized_combined",
    }

    if args.use_mock_embedder:
        embedder = MockEmbedder(dim=args.dim, seed=42)
    else:
        embedder = SentenceTransformerEmbedder(dim=args.dim)

    if args.corpus == "combined":
        combined_dir = corpus_map["combined"]
        if not os.path.exists(os.path.join(combined_dir, "corpus_offset_map.json")):
            print(f"Lỗi: Không tìm thấy kho hợp nhất tại {combined_dir}. Hãy chạy 'python scripts/merge_quantized_corpora.py' trước.")
            sys.exit(1)
        corpus = UnifiedQuantizedCorpus(combined_dir)

        def do_search(q):
            return search_unified_corpus(corpus, embedder, q, top_k=args.top_k, sample_stride=args.stride)

    else:
        v_file, m_file = corpus_map[args.corpus]
        if not os.path.exists(v_file) or not os.path.exists(m_file):
            print(f"Lỗi: Không tìm thấy tệp tại {v_file} hoặc {m_file}.")
            sys.exit(1)
        engine = SemanticSearchEngine(
            vector_file=v_file,
            metadata_file=m_file,
            embedder=embedder,
            dim=args.dim,
        )

        def do_search(q):
            return engine.search(q, top_k=args.top_k)

    if args.query:
        results = do_search(args.query)
        display_results(args.query, results, corpus_name=args.corpus)
    else:
        print(f"\n=== TRÌNH TÌM KIẾM NGỮ NGHĨA ĐA NGUỒN [{args.corpus.upper()}] (Gõ 'exit' để thoát) ===")
        while True:
            try:
                user_query = input("\nNhập câu truy vấn: ").strip()
                if not user_query:
                    continue
                if user_query.lower() in ["exit", "quit", "q"]:
                    print("Kết thúc phiên tìm kiếm.")
                    break
                results = do_search(user_query)
                display_results(user_query, results, corpus_name=args.corpus)
            except (KeyboardInterrupt, EOFError):
                print("\nKết thúc.")
                break


if __name__ == "__main__":
    main()
