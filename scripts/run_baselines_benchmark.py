"""CLI Benchmark script comparing Flat Exact Search vs Standard HNSW Baselines."""

import argparse
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure src/ is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_index.benchmark import BenchmarkRunner
from ann_index.flat import FlatIndex
from ann_index.hnsw import StandardHNSWIndex
from ann_index.ivf_pq import IVFPQIndex
from ann_index.two_tier_hnsw import TwoTierQuantizedHNSW
from ann_data.utils import get_logger


def load_or_generate_data(
    num_vectors: int,
    num_queries: int,
    dim: int,
    use_real_data: bool = False,
    real_data_path: str = "data/processed/real_news_vectors.dat",
):
    logger = get_logger("run_baselines_benchmark")
    if use_real_data and os.path.exists(real_data_path):
        meta_file = "data/processed/real_news_metadata.jsonl"
        with open(meta_file, "r", encoding="utf-8") as f:
            total_real = sum(1 for line in f if line.strip())

        logger.info("Loading real news vectors from %s (available: %d)", real_data_path, total_real)
        mmap = np.memmap(real_data_path, dtype="float32", mode="r", shape=(total_real, 384))
        dataset = np.array(mmap)
        del mmap

        # Sample queries from dataset with slight noise perturbation
        query_indices = np.random.choice(total_real, size=min(num_queries, total_real), replace=False)
        queries = dataset[query_indices] + np.random.normal(0, 0.01, size=(len(query_indices), 384)).astype(np.float32)
        return dataset, queries

    logger.info("Generating synthetic benchmark data: N=%d, Q=%d, D=%d", num_vectors, num_queries, dim)
    np.random.seed(42)
    dataset = np.random.randn(num_vectors, dim).astype(np.float32)
    queries = np.random.randn(num_queries, dim).astype(np.float32)
    return dataset, queries


def main():
    parser = argparse.ArgumentParser(description="Run ANN Baselines Benchmark (Flat vs HNSW).")
    parser.add_argument("--num-vectors", type=int, default=1000, help="Number of dataset vectors")
    parser.add_argument("--num-queries", type=int, default=50, help="Number of test queries")
    parser.add_argument("--dim", type=int, default=64, help="Vector dimension")
    parser.add_argument("--metric", type=str, default="l2", choices=["l2", "cosine"], help="Distance metric")
    parser.add_argument("--top-k", type=int, default=10, help="Top-K nearest neighbors to retrieve")
    parser.add_argument("--use-real-data", action="store_true", help="Use real news vectors from disk if available")
    parser.add_argument("--output-report", type=str, default=None, help="Save markdown report to file")
    args = parser.parse_args()

    logger = get_logger("run_baselines_benchmark")
    logger.info("=== BẮT ĐẦU CHẠY THỰC NGHIỆM ĐỐI CHUẨN (ANN BASELINES BENCHMARK) ===")

    dataset, queries = load_or_generate_data(
        num_vectors=args.num_vectors,
        num_queries=args.num_queries,
        dim=args.dim,
        use_real_data=args.use_real_data,
    )

    runner = BenchmarkRunner(
        dataset=dataset,
        queries=queries,
        metric=args.metric,
        ground_truth_k=max(args.top_k, 50),
    )

    indices_to_test = [
        FlatIndex(metric=args.metric),
        StandardHNSWIndex(space=args.metric, m=16, ef_construction=100, ef_search=30),
        IVFPQIndex(nlist=16, num_subvectors=min(8, max(1, args.dim // 4)), nprobe=4, metric=args.metric),
        TwoTierQuantizedHNSW(
            m=16,
            ef_search=30,
            tau=3,
            epsilon=1e-4,
            rerank_factor=3,
            min_rerank_k=30,
            metric=args.metric,
        ),
    ]

    logger.info("Đang chạy đánh giá trên %d thuật toán đối chuẩn...", len(indices_to_test))
    results = runner.run_comparison(indices_to_test, top_k=args.top_k)

    table_md = BenchmarkRunner.format_markdown_table(results)

    print("\n" + "=" * 80)
    print("BẢNG SỐ LIỆU ĐỐI SÁNH HIỆU NĂNG THỰC NGHIỆM")
    print("=" * 80)
    print(table_md)
    print("=" * 80 + "\n")

    if args.output_report:
        with open(args.output_report, "w", encoding="utf-8") as f:
            f.write("# Báo cáo Đo lường Hiệu năng Thuật toán Đối chuẩn (Baselines)\n\n")
            f.write(f"- **Tập dữ liệu:** {len(dataset)} vectors (D={dataset.shape[1]})\n")
            f.write(f"- **Số lượng câu truy vấn:** {len(queries)}\n")
            f.write(f"- **Thước đo khoảng cách:** {args.metric}\n\n")
            f.write(table_md + "\n")
        logger.info("Báo cáo đã được lưu tại: %s", args.output_report)


if __name__ == "__main__":
    main()
