import argparse
import sys
import os

# Đảm bảo mã hóa an toàn trên Windows
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))
sys.path.insert(0, BASE_DIR)

from src.ann_data.search.retrieval_evaluator import RetrievalBenchmarkEngine

def main():
    parser = argparse.ArgumentParser(description="Run Universal Retrieval Benchmark")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K results for evaluation")
    parser.add_argument("--output-dir", type=str, default="data/processed/evaluation_results", help="Directory to save output")
    args = parser.parse_args()

    cache_dir = os.path.join(BASE_DIR, "data", "processed")
    engine = RetrievalBenchmarkEngine(cache_dir=cache_dir)
    
    print(f"Bắt đầu chạy đánh giá toàn diện Benchmark với Top-K={args.top_k}...")
    result = engine.run_comprehensive_benchmark(top_k=args.top_k)
    
    report = result["report"]
    
    # In bảng ASCII ra Terminal
    print("\n" + "="*80)
    print(f"{'THUẬT TOÁN':<15} | {'QPS':<10} | {'MEAN LATENCY (ms)':<20} | {'P95 LATENCY (ms)':<20} | {'RECALL@' + str(args.top_k):<10}")
    print("-" * 80)
    for algo in ['flat', 'hnsw', 'ivf_pq', 'two_tier']:
        data = report[algo]
        print(f"{algo:<15} | {data['qps']:<10.2f} | {data['latency_mean_ms']:<20.2f} | {data['latency_p95_ms']:<20.2f} | {data['recall_at_k']:<10.4f}")
    print("="*80)
    
    print(f"\nĐã lưu báo cáo JSON: {result['json_path']}")
    print(f"Đã lưu báo cáo Markdown: {result['md_path']}")

if __name__ == "__main__":
    main()
