import os
import numpy as np
import concurrent.futures
from io_manager import DirectIOManager
from hnsw_quantized import quantize_adc, distance_adc

class LocalShard:
    def __init__(self, shard_id: int, dim: int, max_elements: int, storage_dir: str):
        self.shard_id = shard_id
        
        # --- TIER 1 CỤC BỘ (IN-MEMORY) ---
        self.graph = {} 
        self.entry_point = None 
        
        self.quantized = np.zeros((max_elements, dim), dtype=np.uint8)
        self.scales = np.zeros((max_elements, 1), dtype=np.float16)
        self.offsets = np.zeros((max_elements, 1), dtype=np.float16)
        self.local_count = 0
        
        # --- TIER 2 CỤC BỘ (SSD DIRECT I/O) ---
        os.makedirs(storage_dir, exist_ok=True)
        db_path = os.path.join(storage_dir, f"shard_{shard_id}.bin")
        self.io_manager = DirectIOManager(db_path, dim=dim)
        
    def _calc_distance(self, query: np.ndarray, node_id: int) -> float:
        q_vec = self.quantized[node_id]
        scale = self.scales[node_id][0]
        offset = self.offsets[node_id][0]
        return distance_adc(query, q_vec, scale, offset)

    def _search_local_graph(self, query: np.ndarray, entry_point: int, ef: int, tau: int = 3, epsilon: float = 1e-4):
        candidates = [(self._calc_distance(query, entry_point), entry_point)]
        top_results = candidates[:]
        visited = {entry_point}
        
        fail_count = 0
        current_best_dist = candidates[0][0]
        
        while candidates:
            candidates.sort(key=lambda x: x[0])
            c_dist, c_id = candidates.pop(0)
            
            neighbors = self.graph.get(c_id, [])
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    n_dist = self._calc_distance(query, neighbor)
                    
                    if current_best_dist - n_dist < epsilon:
                        fail_count += 1
                    else:
                        fail_count = 0  
                        current_best_dist = n_dist
                        
                    if fail_count >= tau:
                        break
                        
                    candidates.append((n_dist, neighbor))
                    top_results.append((n_dist, neighbor))
                    
                    top_results.sort(key=lambda x: x[0])
                    if len(top_results) > ef:
                        top_results.pop()
            
            if fail_count >= tau:
                break
                
        return top_results

    def add_node(self, global_id: int, vector: np.ndarray, M: int = 16, ef_construction: int = 32):
        q_vec, scale, offset = quantize_adc(vector.reshape(1, -1))
        
        idx = self.local_count
        self.quantized[idx] = q_vec[0]
        self.scales[idx] = scale[0][0]
        self.offsets[idx] = offset[0][0]
        
        self.graph[idx] = []
        
        if self.entry_point is None:
            self.entry_point = idx
            self.local_count += 1
            self._save_to_ssd(vector)
            return
            
        nearest_neighbors = self._search_local_graph(
            query=vector.astype(np.float32), 
            entry_point=self.entry_point, 
            ef=ef_construction
        )
        
        top_m = nearest_neighbors[:M]
        for _, neighbor_id in top_m:
            self.graph[idx].append(neighbor_id)
            self.graph[neighbor_id].append(idx)
            
        self.local_count += 1
        self._save_to_ssd(vector)

    def _save_to_ssd(self, vector: np.ndarray):
        with open(self.io_manager.filepath, 'ab') as f:
            vector.astype(np.float32).tofile(f)


class ShardedIVFHNSW:
    def __init__(self, dim: int, num_shards: int, capacity_per_shard: int, storage_dir: str):
        self.dim = dim
        self.num_shards = num_shards
        np.random.seed(42)
        self.centroids = np.random.randn(num_shards, dim).astype(np.float32)
        self.shards = [LocalShard(i, dim, capacity_per_shard, storage_dir) for i in range(num_shards)]

    def _get_nearest_shards(self, vector: np.ndarray, nprobe: int) -> list[int]:
        distances = np.linalg.norm(self.centroids - vector, axis=1)
        return np.argsort(distances)[:nprobe].tolist()

    def route_and_insert(self, global_id: int, vector: np.ndarray):
        target_shard_id = self._get_nearest_shards(vector, nprobe=1)[0]
        self.shards[target_shard_id].add_node(global_id, vector)
        return target_shard_id

    def distributed_search(self, query: np.ndarray, top_k: int, nprobe: int = 3, re_rank_limit: int = 50):
        """
        Truy vấn Phân tán (Distributed Search):
        Gom kết quả cắt tia từ RAM (Tier 1) và truy xuất ổ cứng để xếp hạng lại (Tier 2).
        """
        # Bước 1: Router định tuyến
        target_shard_ids = self._get_nearest_shards(query, nprobe=nprobe)
        print(f"| Router | Đã xác định 3 cụm tiềm năng: Shard {target_shard_ids}")
        
        # Bước 2: Tier 1 - Lục soát đồ thị trên RAM
        candidate_pool = []
        for sid in target_shard_ids:
            shard = self.shards[sid]
            if shard.entry_point is None:
                continue
            # Thuật toán chạy ngắt sớm để đo khoảng cách ADC
            local_results = shard._search_local_graph(query, shard.entry_point, ef=re_rank_limit)
            for dist, node_id in local_results:
                candidate_pool.append((dist, node_id, sid))
                
        # Sắp xếp và chốt 50 ứng viên tiềm năng nhất
        candidate_pool.sort(key=lambda x: x[0])
        top_candidates = candidate_pool[:re_rank_limit]
        
        # Bước 3: Tier 2 - Lấy dữ liệu float32 gốc (Chống Thrashing bằng Direct I/O)
        print(f"| Tier 2 | Tiến hành xuống đĩa (SSD) lấy dải float32 gốc của {len(top_candidates)} ứng viên...")
        requests_by_shard = {}
        for _, node_id, sid in top_candidates:
            if sid not in requests_by_shard:
                requests_by_shard[sid] = []
            requests_by_shard[sid].append(node_id)
            
        fetched_vectors = {}
        for sid, node_ids in requests_by_shard.items():
            batch_result = self.shards[sid].io_manager.async_read_batch(node_ids)
            for nid, vec in batch_result.items():
                fetched_vectors[(sid, nid)] = vec
                
        # Bước 4: Tính Euclid chính xác và Re-ranking
        print(f"| Router | Tính toán Re-ranking chốt Top {top_k} trả về người dùng...")
        final_results = []
        for _, node_id, sid in top_candidates:
            exact_vec = fetched_vectors[(sid, node_id)]
            exact_dist = float(np.linalg.norm(query - exact_vec))
            final_results.append((exact_dist, node_id, sid))
            
        final_results.sort(key=lambda x: x[0])
        return final_results[:top_k]


if __name__ == "__main__":
    print("--- QUY TRÌNH BIG DATA SEARCH TỔNG QUÁT ---")
    router = ShardedIVFHNSW(dim=384, num_shards=10, capacity_per_shard=1000, storage_dir="shards_db")
    
    # 1. Nạp 100 vector ngẫu nhiên
    np.random.seed(99)
    print("\n[HỆ THỐNG] Đang xây dựng dữ liệu (Nhập 100 văn bản)...")
    for i in range(100):
        vec = np.random.randn(384).astype(np.float32)
        router.route_and_insert(global_id=i, vector=vec)
    
    # 2. Truy vấn
    print("\n[NGƯỜI DÙNG] Gửi câu hỏi tìm kiếm...")
    query_vector = np.random.randn(384).astype(np.float32)
    
    # Kích hoạt Search Pipeline
    top_5 = router.distributed_search(query_vector, top_k=5, nprobe=3, re_rank_limit=50)
    
    print("\n=== KẾT QUẢ CHUNG CUỘC ===")
    for rank, (dist, node_id, sid) in enumerate(top_5, 1):
        print(f"Top {rank}: Đỉnh số {node_id:02d} (nằm tại Shard {sid:02d}) | Sai số Euclid tuyệt đối: {dist:.4f}")
