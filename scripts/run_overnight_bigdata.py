import os
import sys
import time
import json
import shutil
import numpy as np
import argparse
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from ann_index.two_tier_hnsw import ShardedIVFHNSW
from ann_data.utils import get_logger

logger = get_logger("overnight_stress")

def train_ivf_kmeans(
    vectors: np.ndarray,
    k: int,
    max_iters: int = 15,
) -> np.ndarray:
    """Train coarse IVF centroids using vectorized Euclidean K-Means."""
    n, dim = vectors.shape
    if n <= k:
        repeats = (k // n) + 1
        return np.tile(vectors, (repeats, 1))[:k].astype(np.float32)

    np.random.seed(42)
    init_idx = np.random.choice(n, size=k, replace=False)
    centroids = np.copy(vectors[init_idx]).astype(np.float32)

    x_norm_sq = np.sum(vectors ** 2, axis=1, keepdims=True)

    for _ in range(max_iters):
        c_norm_sq = np.sum(centroids ** 2, axis=1, keepdims=True).T
        dists = x_norm_sq - 2.0 * (vectors @ centroids.T) + c_norm_sq
        labels = np.argmin(dists, axis=1)

        new_centroids = np.zeros_like(centroids)
        for c in range(k):
            mask = (labels == c)
            if np.any(mask):
                new_centroids[c] = np.mean(vectors[mask], axis=0)
            else:
                new_centroids[c] = vectors[np.random.randint(0, n)]

        if np.allclose(centroids, new_centroids, atol=1e-4):
            break
        centroids = new_centroids

    return centroids


def main():
    scales = [10_000_000, 10_500_000, 11_000_000, 11_500_000, 12_000_000, 12_500_000]
    
    output_dir = "data/experiments"
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "overnight_bigdata_results.json")
    md_path = os.path.join(output_dir, "overnight_bigdata_summary.md")
    
    logger.info("Bắt đầu tác vụ nền chuyên sâu qua đêm (Overnight Big Data Stress Test)")
    
    # Sinh 100k vector float32 làm mẫu lặp để tiết kiệm RAM sinh random
    np.random.seed(42)
    dim = 384
    batch_size = 100_000
    logger.info("Đang sinh batch mẫu 100,000 vectors...")
    dummy_batch = np.random.randn(batch_size, dim).astype(np.float32)
    
    queries = np.random.randn(30, dim).astype(np.float32)
    
    experiment_records = []
    
    for n in scales:
        logger.info(f"--- Đang thực thi mốc N = {n:,} ---")
        shards_dir = f"data/experiments/tmp_shards_{n}"
        if os.path.exists(shards_dir):
            shutil.rmtree(shards_dir)
            
        t0 = time.time()
        
        # 1. Train K-Means (Dùng 20,000 mẫu)
        logger.info("1. Đang huấn luyện K-Means (100 shards)...")
        centroids = train_ivf_kmeans(dummy_batch[:20000], k=100, max_iters=10)
        
        # 2. Khởi tạo Router
        logger.info("2. Khởi tạo ShardedIVFHNSW Router...")
        router = ShardedIVFHNSW(
            dim=dim,
            num_shards=100,
            capacity_per_shard=(n // 100) + 10000,
            storage_dir=shards_dir,
            clean_storage=True
        )
        router.centroids = centroids
        
        # 3. Lập chỉ mục
        logger.info(f"3. Lập chỉ mục {n:,} vectors...")
        for i in range(n):
            vec = dummy_batch[i % batch_size]
            router.route_and_insert(i, vec)
            if (i + 1) % 1_000_000 == 0:
                logger.info(f"   Đã insert {i + 1:,} vectors...")
                
        build_time = time.time() - t0
        
        # 4. Đo đạc Memory
        process = psutil.Process(os.getpid())
        ram_mb = process.memory_info().rss / (1024 * 1024)
        
        # 5. Đánh giá tốc độ truy vấn
        logger.info("4. Chạy 30 truy vấn thử nghiệm...")
        latencies = []
        for q in queries:
            tq = time.perf_counter()
            _ = router.distributed_search(q, top_k=10, nprobe=5)
            latencies.append((time.perf_counter() - tq) * 1000)
            
        latency_p50 = np.percentile(latencies, 50)
        latency_p95 = np.percentile(latencies, 95)
        qps = 1000.0 / np.mean(latencies)
        
        logger.info(f"Hoàn thành mốc N={n:,}: Build {build_time/3600:.2f}h, RAM {ram_mb:.2f}MB, QPS {qps:.1f}")
        
        step_record = {
            "scale_n": n,
            "build_time_sec": build_time,
            "ram_mb": ram_mb,
            "latency_p50_ms": latency_p50,
            "latency_p95_ms": latency_p95,
            "qps": qps
        }
        experiment_records.append(step_record)
        
        # Ghi file JSON
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(experiment_records, f, indent=2, ensure_ascii=False)
            
        # Ghi file Markdown
        md_lines = [
            "# Báo cáo Thực nghiệm Máy chủ Big Data HNSW",
            "",
            "Đo đạc trên kiến trúc phân tán (ShardedIVFHNSW) với 100 Shards.",
            "",
            "| Quy mô (N) | RAM System (MB) | Build Time (Giờ) | Latency p50 (ms) | QPS |",
            "| :--- | :--- | :--- | :--- | :--- |"
        ]
        for r in experiment_records:
            md_lines.append(
                f"| {r['scale_n']:,} | {r['ram_mb']:.2f} | {r['build_time_sec']/3600:.2f} | {r['latency_p50_ms']:.2f} | {r['qps']:.1f} |"
            )
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
            
        # Clean up disk
        if os.path.exists(shards_dir):
            shutil.rmtree(shards_dir)
            
    logger.info("TÁC VỤ OVERNIGHT ĐÃ HOÀN TẤT.")

if __name__ == "__main__":
    main()
