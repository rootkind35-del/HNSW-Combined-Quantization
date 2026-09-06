"""Bộ tìm kiếm tự sinh tự động (Automated Query Search & Evaluation Battery).
Tự động sinh các câu truy vấn từ đa lĩnh vực và từ chính nội dung tài liệu,
đánh giá độ chính xác (Precision@K, HitRate@K), độ tương đồng Cosine và độ trễ phục vụ.
"""

import argparse
import json
import os
import sys
import time
import warnings

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
warnings.filterwarnings("ignore")

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, os.path.dirname(__file__))

from ann_data.embedder import SentenceTransformerEmbedder
from search_bridge import load_dataset_and_metadata


# Danh mục câu hỏi kiểm thử đại diện cho các lĩnh vực cốt lõi
PREDEFINED_DOMAINS = [
    {
        "category": "Kinh doanh & Tài chính",
        "query": "thị trường chứng khoán cổ phiếu và đầu tư tài chính",
        "expected_keywords": ["chứng khoán", "cổ phiếu", "tài chính", "ngân hàng", "doanh thu", "kinh tế"]
    },
    {
        "category": "Khoa học & Công nghệ",
        "query": "công nghệ trí tuệ nhân tạo máy tính và phần mềm",
        "expected_keywords": ["máy tính", "công nghệ", "trí tuệ nhân tạo", "phần mềm", "điện tử", "dữ liệu"]
    },
    {
        "category": "Y tế & Sức khỏe",
        "query": "khám chữa bệnh tại bệnh viện y tế và dược phẩm",
        "expected_keywords": ["bệnh viện", "y tế", "thuốc", "điều trị", "bác sĩ", "sức khỏe"]
    },
    {
        "category": "Văn hóa & Lịch sử",
        "query": "lịch sử triều đại nhà trần kháng chiến chống quân nguyên mông",
        "expected_keywords": ["trần", "triều đại", "lịch sử", "kháng chiến", "vua", "quân"]
    },
    {
        "category": "Giáo dục & Đào tạo",
        "query": "giáo dục đại học chương trình đào tạo sinh viên và giảng viên",
        "expected_keywords": ["đại học", "giáo dục", "sinh viên", "đào tạo", "giảng viên", "trường"]
    },
    {
        "category": "Chính sách & Pháp luật",
        "query": "nghị định xử phạt vi phạm hành chính và an toàn giao thông đường bộ",
        "expected_keywords": ["nghị định", "quy định", "hành chính", "xử phạt", "giao thông", "luật"]
    },
    {
        "category": "Nông nghiệp & Môi trường",
        "query": "sản xuất nông nghiệp trồng trọt xuất khẩu lúa gạo và thủy sản",
        "expected_keywords": ["nông nghiệp", "lúa", "thủy sản", "xuất khẩu", "trồng trọt", "nông dân"]
    },
    {
        "category": "Địa lý & Đô thị",
        "query": "quy hoạch phát triển đô thị thành phố hạ tầng giao thông cầu đường",
        "expected_keywords": ["thành phố", "đô thị", "quy hoạch", "hạ tầng", "giao thông", "cầu"]
    }
]


def generate_synthetic_queries_from_corpus(metadata, count: int = 10, seed: int = 42):
    """
    Tự động trích xuất và sinh câu truy vấn trực tiếp từ các văn bản trong kho (Ground Truth Synthetic Queries).
    Giúp đo lường trực tiếp Top-K Recall trên các văn bản đích xác thực.
    """
    rng = np.random.RandomState(seed)
    n = len(metadata)
    selected_indices = rng.choice(n, size=min(count, n), replace=False)

    synthetic_queries = []
    for idx in selected_indices:
        item = metadata[idx]
        title = item.get("title", "").strip()
        preview = item.get("preview", "").strip()

        # Rút gọn thành câu truy vấn ngắn gọn tự nhiên
        words = preview.split()
        if len(words) >= 8:
            q_text = " ".join(words[:8])
        elif title:
            q_text = title[:60]
        else:
            q_text = preview[:60]

        synthetic_queries.append({
            "target_idx": int(idx),
            "target_doc_id": item.get("doc_id", f"doc_{idx}"),
            "target_title": title,
            "category": item.get("category", "Văn hóa & Đời sống"),
            "query": q_text
        })

    return synthetic_queries


def evaluate_search(queries_list, vectors, metadata, embedder, top_k: int = 5):
    """
    Thực hiện truy vấn lô, tính độ tương đồng Cosine, độ trễ và kiểm tra tính xác thực.
    """
    num_vectors = vectors.shape[0]
    query_texts = [q["query"] for q in queries_list]

    # 1. Đo thời gian nhúng câu hỏi (Embedding Time)
    t_embed_start = time.perf_counter()
    query_embeddings = embedder.encode(query_texts)
    # Chuẩn hóa L2
    norms = np.linalg.norm(query_embeddings, axis=1, keepdims=True)
    query_embeddings = query_embeddings / np.maximum(norms, 1e-12)
    t_embed_total = (time.perf_counter() - t_embed_start) * 1000

    results_detail = []
    latencies = []
    similarities_top1 = []
    keyword_hits = []
    ground_truth_hits = []

    for i, q_item in enumerate(queries_list):
        q_vec = query_embeddings[i]
        t_search_start = time.perf_counter()

        # Tích vô hướng trên vector chuẩn hóa L2 = Cosine Similarity
        sims = np.dot(vectors, q_vec)

        # Lấy Top-K
        top_idx = np.argpartition(sims, -top_k)[-top_k:]
        sorted_top_idx = top_idx[np.argsort(-sims[top_idx])]

        t_search = (time.perf_counter() - t_search_start) * 1000
        latencies.append(t_search)

        top1_idx = sorted_top_idx[0]
        top1_sim = float(sims[top1_idx])
        similarities_top1.append(top1_sim)

        matched_docs = []
        for rank, idx in enumerate(sorted_top_idx, start=1):
            meta = metadata[idx]
            matched_docs.append({
                "rank": rank,
                "index": int(idx),
                "doc_id": meta.get("doc_id", ""),
                "title": meta.get("title", ""),
                "preview": meta.get("preview", "")[:120],
                "category": meta.get("category", ""),
                "source": meta.get("source", ""),
                "cosine_similarity": round(float(sims[idx]), 4)
            })

        # Kiểm tra từ khóa ngữ nghĩa
        exp_keywords = q_item.get("expected_keywords", [])
        combined_text = " ".join([d["title"] + " " + d["preview"] for d in matched_docs]).lower()
        matched_kw_count = sum(1 for kw in exp_keywords if kw in combined_text)
        has_semantic_match = (matched_kw_count > 0) if exp_keywords else True
        keyword_hits.append(has_semantic_match)

        # Kiểm tra nếu là câu hỏi tự sinh có ground truth target_idx
        target_idx = q_item.get("target_idx")
        hit_target = False
        if target_idx is not None:
            top_k_indices = set(int(x) for x in sorted_top_idx)
            hit_target = (target_idx in top_k_indices)
            ground_truth_hits.append(hit_target)

        results_detail.append({
            "query": q_item["query"],
            "category": q_item.get("category", "Tất cả"),
            "latency_ms": round(t_search, 2),
            "top1_similarity": round(top1_sim, 4),
            "semantic_keyword_hit": has_semantic_match,
            "target_doc_hit": hit_target if target_idx is not None else None,
            "top_results": matched_docs
        })

    eval_summary = {
        "num_queries": len(queries_list),
        "top_k": top_k,
        "dataset_size": num_vectors,
        "embedding_time_total_ms": round(t_embed_total, 2),
        "embedding_time_per_query_ms": round(t_embed_total / len(queries_list), 2),
        "avg_search_latency_ms": round(float(np.mean(latencies)), 2),
        "p50_search_latency_ms": round(float(np.percentile(latencies, 50)), 2),
        "p95_search_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        "avg_top1_cosine_similarity": round(float(np.mean(similarities_top1)), 4),
        "min_top1_cosine_similarity": round(float(np.min(similarities_top1)), 4),
        "max_top1_cosine_similarity": round(float(np.max(similarities_top1)), 4),
        "semantic_relevance_rate": round(float(np.mean(keyword_hits)) * 100, 1) if keyword_hits else 100.0,
        "ground_truth_recall_at_k": round(float(np.mean(ground_truth_hits)) * 100, 1) if ground_truth_hits else None,
        "qps": round(1000.0 / max(float(np.mean(latencies)), 0.001), 1),
        "details": results_detail
    }

    return eval_summary


def main():
    parser = argparse.ArgumentParser(description="Đánh giá bộ tìm kiếm tự sinh tự động")
    parser.add_argument("--synthetic-count", type=int, default=10, help="Số lượng câu truy vấn tự sinh từ kho")
    parser.add_argument("--top-k", type=int, default=5, help="Số lượng kết quả lấy ra mỗi truy vấn")
    parser.add_argument("--output-json", type=str, default="", help="Đường dẫn xuất file JSON kết quả")
    args = parser.parse_args()

    print("================================================================================")
    print("  BỘ TÌM KIẾM TỰ SINH TỰ ĐỘNG & ĐÁNH GIÁ ĐỘ CHÍNH XÁC NGỮ NGHĨA (31.33M)")
    print("================================================================================")

    t0 = time.perf_counter()
    print("[1/4] Đang nạp bộ đệm vector và metadata 5.000 bản ghi...")
    res = load_dataset_and_metadata()
    if len(res) == 5:
        vectors, metadata, coords_3d, global_indices, dataset_source = res
    else:
        vectors, metadata, dataset_source = res[:3]
    print(f"      Đã nạp {len(vectors):,} vector ({vectors.shape[1]} chiều). Nguồn: {dataset_source}")

    print("\n[2/4] Khởi tạo mô hình SentenceTransformer ('paraphrase-multilingual-MiniLM-L12-v2')...")
    embedder = SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2", dim=vectors.shape[1])
    print("      Khởi tạo mô hình hoàn tất.")

    print(f"\n[3/4] Sinh câu hỏi tự động:")
    print(f"      - {len(PREDEFINED_DOMAINS)} câu truy vấn chủ đề định sẵn (Kinh tế, AI, Y tế, Lịch sử, v.v.)")
    print(f"      - {args.synthetic_count} câu truy vấn tự sinh ngẫu nhiên từ văn bản trong kho (Ground Truth)")

    synthetic_queries = generate_synthetic_queries_from_corpus(metadata, count=args.synthetic_count, seed=2026)
    all_queries = PREDEFINED_DOMAINS + synthetic_queries

    print(f"\n[4/4] Đang chạy đánh giá thực nghiệm trên {len(all_queries)} câu truy vấn...")
    t_eval_start = time.perf_counter()
    evaluation = evaluate_search(all_queries, vectors, metadata, embedder, top_k=args.top_k)
    t_total_run = time.perf_counter() - t0

    # In kết quả các truy vấn chủ đề
    print("\n" + "="*80)
    print(f"{'STT':<4} | {'CHỦ ĐỀ':<22} | {'TRUY VẤN':<35} | {'SIM':<7} | {'KẾT QUẢ TOP 1':<30}")
    print("-" * 105)
    for idx, item in enumerate(evaluation["details"][:len(PREDEFINED_DOMAINS)], 1):
        top1 = item["top_results"][0] if item["top_results"] else {}
        top1_title = (top1.get("title") or "")[:28]
        top1_sim = item["top1_similarity"]
        cat = item["category"][:20]
        q_short = item["query"][:33]
        print(f"{idx:<4} | {cat:<22} | {q_short:<35} | {top1_sim:<7.4f} | {top1_title:<30}")

    # In kết quả các truy vấn tự sinh từ kho
    if synthetic_queries:
        print("\n" + "-"*80)
        print("KẾT QUẢ TRUY VẤN TỰ SINH TỪ VĂN BẢN (GROUND TRUTH VERIFICATION):")
        print(f"{'STT':<4} | {'TRUY VẤN TỰ SINH':<40} | {'SIM':<7} | {'HIT TARGET':<12} | {'KẾT QUẢ TOP 1':<30}")
        print("-" * 100)
        start_idx = len(PREDEFINED_DOMAINS)
        for s_idx, item in enumerate(evaluation["details"][start_idx:], 1):
            top1 = item["top_results"][0] if item["top_results"] else {}
            top1_title = (top1.get("title") or "")[:28]
            top1_sim = item["top1_similarity"]
            hit = "ĐÚNG" if item["target_doc_hit"] else "KHÁC"
            q_short = item["query"][:38]
            print(f"{s_idx:<4} | {q_short:<40} | {top1_sim:<7.4f} | {hit:<12} | {top1_title:<30}")

    print("\n" + "="*80)
    print("TỔNG HỢP CHỈ SỐ ĐÁNH GIÁ HIỆU NĂNG BỘ TÌM KIẾM:")
    print(f"  - Tổng số truy vấn thử nghiệm:       {evaluation['num_queries']}")
    print(f"  - Độ tương đồng Cosine trung bình:    {evaluation['avg_top1_cosine_similarity']:.4f} (Dải: {evaluation['min_top1_cosine_similarity']:.4f} -> {evaluation['max_top1_cosine_similarity']:.4f})")
    print(f"  - Tỷ lệ phù hợp ngữ nghĩa từ khóa:   {evaluation['semantic_relevance_rate']}%")
    if evaluation.get("ground_truth_recall_at_k") is not None:
        print(f"  - Tỷ lệ Recall@{args.top_k} truy vấn tự sinh: {evaluation['ground_truth_recall_at_k']}%")
    print(f"  - Độ trễ tìm kiếm trung bình:        {evaluation['avg_search_latency_ms']} ms")
    print(f"  - Độ trễ phân vị p50:                 {evaluation['p50_search_latency_ms']} ms")
    print(f"  - Độ trễ phân vị p95:                 {evaluation['p95_search_latency_ms']} ms")
    print(f"  - Tốc độ thông lượng tìm kiếm (QPS): {evaluation['qps']} QPS")
    print(f"  - Tổng thời gian hoàn tất kiểm thử:  {t_total_run:.2f} giây")
    print("="*80)

    # Lưu kết quả ra file JSON
    out_path = args.output_json
    if not out_path:
        out_path = os.path.join(BASE_DIR, "data", "processed", "auto_search_evaluation_results.json")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Đã lưu kết quả chi tiết vào: {out_path}\n")


if __name__ == "__main__":
    main()
