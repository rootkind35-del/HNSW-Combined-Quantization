import os
import json
import time
import hashlib
from datetime import datetime
import numpy as np
from typing import List, Dict, Any

from src.ann_index.flat import FlatIndex
from src.ann_index.hnsw import StandardHNSWIndex
from src.ann_index.ivf_pq import IVFPQIndex
from src.ann_index.two_tier_hnsw import TwoTierQuantizedHNSW

try:
    import psutil
except ImportError:
    psutil = None

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

class RetrievalBenchmarkEngine:
    def __init__(self, cache_dir: str = "data/processed"):
        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(BASE_DIR, cache_dir)
        self.cache_dir = cache_dir
        self.vectors_path = os.path.join(cache_dir, "search_index_cache.npz")
        self.metadata_path = os.path.join(cache_dir, "search_index_metadata.json")
        
        # Load data
        print("Loading data for benchmark...")
        data = np.load(self.vectors_path)
        self.vectors = data['vectors']
        if self.vectors.dtype != np.float32:
            self.vectors = self.vectors.astype(np.float32)
            
        with open(self.metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
            
        self.dim = self.vectors.shape[1]
        
        print("Initializing indices...")
        self.indices = {}
        
        # 1. Flat Index (Ground Truth)
        self.indices['flat'] = FlatIndex(metric='cosine')
        self.indices['flat'].build(self.vectors)
        
        # 2. Standard HNSW
        self.indices['hnsw'] = StandardHNSWIndex(space='cosine')
        self.indices['hnsw'].build(self.vectors)
            
        # 3. IVF-PQ
        self.indices['ivf_pq'] = IVFPQIndex(metric='cosine')
        self.indices['ivf_pq'].build(self.vectors)
            
        # 4. Two Tier HNSW
        self.indices['two_tier'] = TwoTierQuantizedHNSW(metric='cosine')
        self.indices['two_tier'].build(self.vectors)
        
        print("All indices initialized.")

    def load_benchmark_queries(self) -> List[Dict[str, str]]:
        return [
            # Kinh tế & Tài chính
            {"text": "tác động của lạm phát đến giá vàng", "category": "Kinh tế & Tài chính"},
            {"text": "thị trường chứng khoán việt nam hôm nay", "category": "Kinh tế & Tài chính"},
            {"text": "lãi suất vay mua nhà ngân hàng", "category": "Kinh tế & Tài chính"},
            {"text": "chiến lược đầu tư bất động sản an toàn", "category": "Kinh tế & Tài chính"},
            # Khoa học & Công nghệ
            {"text": "trí tuệ nhân tạo tạo sinh trong y học", "category": "Khoa học & Công nghệ"},
            {"text": "ngôn ngữ lập trình python cơ bản", "category": "Khoa học & Công nghệ"},
            {"text": "mạng 5g và ứng dụng thực tế", "category": "Khoa học & Công nghệ"},
            {"text": "máy tính lượng tử hoạt động như thế nào", "category": "Khoa học & Công nghệ"},
            # Y tế & Sức khỏe
            {"text": "triệu chứng của bệnh sốt xuất huyết", "category": "Y tế & Sức khỏe"},
            {"text": "cách phòng chống bệnh tiểu đường", "category": "Y tế & Sức khỏe"},
            {"text": "chế độ ăn keto giảm cân hiệu quả", "category": "Y tế & Sức khỏe"},
            {"text": "lợi ích của việc tập yoga mỗi ngày", "category": "Y tế & Sức khỏe"},
            # Giáo dục
            {"text": "phương pháp học tiếng anh giao tiếp", "category": "Giáo dục"},
            {"text": "học phí đại học quốc gia hà nội", "category": "Giáo dục"},
            {"text": "cách cải thiện kỹ năng thuyết trình", "category": "Giáo dục"},
            {"text": "học bổng du học mỹ toàn phần", "category": "Giáo dục"},
            # Giao thông & Đô thị
            {"text": "tình trạng ùn tắc giao thông tại hà nội", "category": "Giao thông & Đô thị"},
            {"text": "dự án tàu điện ngầm tuyến metro", "category": "Giao thông & Đô thị"},
            {"text": "giải pháp giảm thiểu ô nhiễm không khí", "category": "Giao thông & Đô thị"},
            {"text": "quy hoạch đô thị thông minh", "category": "Giao thông & Đô thị"},
            # Lịch sử & Địa lý Việt Nam
            {"text": "trận chiến điện biên phủ trên không", "category": "Lịch sử & Địa lý Việt Nam"},
            {"text": "danh lam thắng cảnh tại đà nẵng", "category": "Lịch sử & Địa lý Việt Nam"},
            {"text": "văn hóa cồng chiêng tây nguyên", "category": "Lịch sử & Địa lý Việt Nam"},
            {"text": "các vương triều phong kiến việt nam", "category": "Lịch sử & Địa lý Việt Nam"},
            {"text": "địa hình đồng bằng sông cửu long", "category": "Lịch sử & Địa lý Việt Nam"}
        ]

    def evaluate_single_query(self, query_text: str, algorithm: str = "two_tier", top_k: int = 5, category: str = "Tất cả", hyperparams: dict = None, export_log: bool = True) -> Dict[str, Any]:
        # Generate random vector to simulate embedding
        query_vector = np.random.randn(self.dim).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)
        
        index = self.indices.get(algorithm)
        if not index:
            raise ValueError(f"Algorithm {algorithm} not found.")

        start_time = time.perf_counter()
        idx_res, dist_res = index.search(query_vector, top_k=top_k)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000

        ram_mb = 0.0
        if psutil:
            process = psutil.Process(os.getpid())
            ram_mb = process.memory_info().rss / (1024 * 1024)

        formatted_results = []
        if len(idx_res) > 0 and len(idx_res[0]) > 0:
            for i, (idx, dist) in enumerate(zip(idx_res[0], dist_res[0])):
                meta = self.metadata[idx] if 0 <= idx < len(self.metadata) else {}
                formatted_results.append({
                    "rank": i + 1,
                    "doc_id": meta.get("doc_id", str(idx)),
                    "title": meta.get("title", f"Document {idx}"),
                    "preview": meta.get("preview", "")[:100],
                    "source": meta.get("source", ""),
                    "score": float(1.0 - dist)
                })

        log_path = ""
        if export_log:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            short_hash = hashlib.md5(query_text.encode('utf-8')).hexdigest()[:8]
            log_path = os.path.join(BASE_DIR, "data", "processed", "query_logs", f"query_{timestamp}_{short_hash}.json")
            log_data = {
                "query": query_text,
                "category": category,
                "algorithm": algorithm,
                "timestamp": timestamp,
                "latency_ms": latency_ms,
                "ram_usage_mb": ram_mb,
                "top_k": top_k,
                "results": formatted_results,
                "log_file_path": log_path
            }
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)

        return {
            "latency_ms": latency_ms,
            "ram_mb": ram_mb,
            "results": formatted_results,
            "log_path": log_path
        }

    def _get_gt(self, query_vector, top_k):
        idx_res, _ = self.indices['flat'].search(query_vector, top_k=top_k)
        if len(idx_res) > 0:
            return idx_res[0].tolist()
        return []

    def run_comprehensive_benchmark(self, top_k: int = 5, queries: List[str] = None) -> Dict[str, Any]:
        benchmark_queries = self.load_benchmark_queries()
        if queries:
            benchmark_queries = [{"text": q, "category": "Custom"} for q in queries]

        algorithms = ['flat', 'hnsw', 'ivf_pq', 'two_tier']
        report = {}

        for algo in algorithms:
            latencies = []
            recalls = []
            top1_sims = []
            
            for q_obj in benchmark_queries:
                q_text = q_obj["text"]
                q_vec = np.random.randn(self.dim).astype(np.float32)
                q_vec = q_vec / np.linalg.norm(q_vec)
                
                gt_ids = set(self._get_gt(q_vec, top_k))
                
                start = time.perf_counter()
                idx_res, dist_res = self.indices[algo].search(q_vec, top_k=top_k)
                end = time.perf_counter()
                
                latencies.append((end - start) * 1000)
                
                res_ids = []
                if len(idx_res) > 0:
                    res_ids = idx_res[0].tolist()
                
                hit_count = sum(1 for rid in res_ids if rid in gt_ids)
                recalls.append(hit_count / top_k if top_k > 0 else 0.0)
                if len(res_ids) > 0:
                    top1_sims.append(1.0 - float(dist_res[0][0]))
                else:
                    top1_sims.append(0.0)

            latencies = np.array(latencies)
            report[algo] = {
                "latency_p50_ms": float(np.percentile(latencies, 50)),
                "latency_p95_ms": float(np.percentile(latencies, 95)),
                "latency_p99_ms": float(np.percentile(latencies, 99)),
                "latency_mean_ms": float(np.mean(latencies)),
                "qps": float(1000.0 / np.mean(latencies)) if np.mean(latencies) > 0 else 0.0,
                "recall_at_k": float(np.mean(recalls)),
                "avg_top1_similarity": float(np.mean(top1_sims)),
                "ram_saving_percent": 0.0
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_json_path = os.path.join(BASE_DIR, "data", "processed", "evaluation_results", f"benchmark_report_{timestamp}.json")
        report_md_path = os.path.join(BASE_DIR, "data", "processed", "evaluation_results", f"benchmark_summary_{timestamp}.md")
        
        os.makedirs(os.path.dirname(report_json_path), exist_ok=True)
        with open(report_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        md_content = f"# Báo cáo Benchmark Tìm kiếm (Top-{top_k})\n\n"
        md_content += f"Thời gian: {timestamp}\n\n"
        md_content += "| Thuật toán | QPS | Độ trễ Mean (ms) | Độ trễ P95 (ms) | Recall@{top_k} |\n"
        md_content += "|---|---|---|---|---|\n"
        for algo in algorithms:
            md_content += f"| {algo} | {report[algo]['qps']:.2f} | {report[algo]['latency_mean_ms']:.2f} | {report[algo]['latency_p95_ms']:.2f} | {report[algo]['recall_at_k']:.4f} |\n"
            
        with open(report_md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        return {
            "report": report,
            "json_path": report_json_path,
            "md_path": report_md_path
        }
