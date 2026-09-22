import os
import sys
import time
import json
import numpy as np
import psutil

# Fix encoding for Windows terminal
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from ann_index.two_tier_hnsw import ShardedIVFHNSW
from ann_data.utils import get_logger

logger = get_logger("bigdata_stress_test")

def get_process_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def run_bigdata_experiment():
    scales = [10_000_000, 10_500_000, 11_000_000, 11_500_000, 12_000_000, 12_500_000]
    dim = 384
    num_queries = 50
    k_search = 10
    nprobe = 10
    
    # 1. Generate Queries
    np.random.seed(42)
    queries = np.random.randn(num_queries, dim).astype(np.float32)
    norms = np.linalg.norm(queries, axis=1, keepdims=True)
    queries = queries / np.maximum(norms, 1e-12)
    
    # 2. Prepare Storage
    storage_path = os.path.join(BASE_DIR, "data", "experiments", "big_data_shards")
    os.makedirs(storage_path, exist_ok=True)
    
    logger.info("Initializing ShardedIVFHNSW Router for Big Data Stress Test...")
    router = ShardedIVFHNSW(
        dim=dim,
        num_shards=200,
        capacity_per_shard=70000,
        storage_dir=storage_path,
        clean_storage=True,
    )
    
    # Generate dummy centroids just for routing
    logger.info("Generating dummy centroids for 200 shards...")
    router.centroids = np.random.randn(200, dim).astype(np.float32)
    
    results = []
    
    current_size = 0
    total_build_time = 0.0
    
    for target_scale in scales:
        vectors_to_add = target_scale - current_size
        logger.info(f"Target Scale: {target_scale:,}. Need to add {vectors_to_add:,} vectors.")
        
        # Stream insertion in chunks to save RAM
        chunk_size = 50_000
        t0 = time.perf_counter()
        
        for i in range(0, vectors_to_add, chunk_size):
            actual_chunk = min(chunk_size, vectors_to_add - i)
            batch = np.random.randn(actual_chunk, dim).astype(np.float32)
            b_norms = np.linalg.norm(batch, axis=1, keepdims=True)
            batch = batch / np.maximum(b_norms, 1e-12)
            
            for j in range(actual_chunk):
                global_id = current_size + i + j
                router.route_and_insert(global_id, batch[j])
                
            if (i + actual_chunk) % 1_000_000 == 0:
                logger.info(f"  ... inserted {i + actual_chunk:,} / {vectors_to_add:,} vectors.")
                
        build_time = time.perf_counter() - t0
        total_build_time += build_time
        current_size = target_scale
        
        ram_usage = get_process_memory_mb()
        
        logger.info(f"Finished building {target_scale:,}. Iteration Build Time: {build_time:.2f}s. RAM: {ram_usage:.2f} MB")
        
        # 3. Benchmark Queries
        logger.info(f"Benchmarking queries at scale {target_scale:,}...")
        latencies = []
        
        # Warmup
        for q in queries[:5]:
            router.distributed_search(q, top_k=k_search, nprobe=nprobe)
            
        # Actual Measure
        for q in queries:
            t_start = time.perf_counter()
            router.distributed_search(q, top_k=k_search, nprobe=nprobe)
            t_end = time.perf_counter()
            latencies.append((t_end - t_start) * 1000)
            
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        mean_lat = np.mean(latencies)
        qps = 1000.0 / mean_lat if mean_lat > 0 else 0
        
        record = {
            "scale_n": target_scale,
            "ram_mb": ram_usage,
            "total_build_time_sec": total_build_time,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "qps": qps
        }
        results.append(record)
        logger.info(f"QPS: {qps:.1f} | p50: {p50:.2f}ms | p95: {p95:.2f}ms")
        
    # 4. Save Report
    md_lines = [
        "# Báo cáo Chịu tải Big Data (Two-Tier HNSW Sharded Router)",
        "",
        "Kiểm thử thực thi hệ thống Router phân tán với cấu trúc 200 Shards trên luồng dữ liệu 10 triệu đến 12.5 triệu vector.",
        "",
        "| Quy mô (N) | RAM Phân mảnh (MB) | Tổng thời gian Nạp (s) | Latency p50 (ms) | Latency p95 (ms) | QPS |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    
    for r in results:
        n = f"{r['scale_n']:,}"
        md_lines.append(f"| N = {n} | **{r['ram_mb']:.2f} MB** | {r['total_build_time_sec']:.1f}s | **{r['latency_p50_ms']:.2f} ms** | **{r['latency_p95_ms']:.2f} ms** | **{r['qps']:.1f}** |")
        
    report_path = os.path.join(BASE_DIR, "data", "experiments", "big_data_sharded_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    logger.info(f"Hoàn thành toàn bộ Benchmark. Đã lưu {report_path}")

if __name__ == "__main__":
    run_bigdata_experiment()
