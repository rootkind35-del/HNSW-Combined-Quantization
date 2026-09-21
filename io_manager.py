import os
import numpy as np
from collections import OrderedDict
import concurrent.futures

class ApplicationLRUCache:
    def __init__(self, capacity: int = 10000):
        """
        Application-level Cache (LRU) lưu trữ các vector float32 được gọi thường xuyên.
        Giúp chống lại hiện tượng Thrashing của OS Page Cache.
        """
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: int):
        if key not in self.cache:
            return None
        # Đưa phần tử vừa được truy cập xuống cuối (coi như mới nhất)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: int, value: np.ndarray):
        self.cache[key] = value
        self.cache.move_to_end(key)
        # Nếu vượt quá dung lượng, xóa phần tử ở đầu (cũ nhất)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

class DirectIOManager:
    def __init__(self, filepath: str, dim: int = 384, cache_capacity: int = 10000):
        """
        Lớp quản lý luồng đọc ổ cứng trực tiếp (Mô phỏng O_DIRECT / io_uring).
        Phục vụ tác vụ Re-ranking của Tier 2.
        """
        self.filepath = filepath
        self.dim = dim
        self.vector_bytes = dim * 4  # Kích thước 1 vector float32
        self.lru_cache = ApplicationLRUCache(capacity=cache_capacity)
        
        if not os.path.exists(self.filepath):
            # Tạo file rỗng nếu chưa tồn tại
            open(self.filepath, 'wb').close()

    def _read_single_vector(self, vector_id: int) -> np.ndarray:
        """Đọc ngẫu nhiên (Random Read) một khối byte duy nhất trực tiếp từ SSD."""
        with open(self.filepath, 'rb') as f:
            # Di chuyển con trỏ đọc (File Seek) tới đúng địa chỉ byte của vector
            f.seek(vector_id * self.vector_bytes)
            raw_data = f.read(self.vector_bytes)
            # Khôi phục thành mảng numpy
            return np.frombuffer(raw_data, dtype=np.float32).copy()

    def get_vector(self, vector_id: int) -> np.ndarray:
        """Lấy vector: Ưu tiên RAM Cache -> Miss Cache thì xuống SSD."""
        cached_vector = self.lru_cache.get(vector_id)
        if cached_vector is not None:
            return cached_vector
        
        # Đọc từ SSD và nạp vào Cache
        vec = self._read_single_vector(vector_id)
        self.lru_cache.put(vector_id, vec)
        return vec

    def async_read_batch(self, vector_ids: list[int]) -> dict:
        """
        Truy xuất bất đồng bộ (Asynchronous I/O) theo Lô (Batch).
        Gom 50 lệnh đọc từ HNSW thành một luồng song song để triệt tiêu độ trễ đĩa.
        """
        results = {}
        # Mô phỏng io_uring bằng ThreadPoolExecutor (I/O bound)
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
            future_to_id = {executor.submit(self.get_vector, vid): vid for vid in vector_ids}
            for future in concurrent.futures.as_completed(future_to_id):
                vid = future_to_id[future]
                results[vid] = future.result()
                
        return results

if __name__ == "__main__":
    # Test mô phỏng
    print("--- KIỂM THỬ DIRECT I/O & LRU CACHE ---")
    io_manager = DirectIOManager("vector_db.bin")
    
    # Giả sử thuật toán HNSW (Tier 1) vừa trả về 5 ID ứng viên ngẫu nhiên
    candidate_ids = [0, 1] # Ta chỉ có 2 vector đang lưu trong file test
    
    print(f"HNSW yêu cầu truy xuất các ID: {candidate_ids}")
    
    # Đọc batch
    batch_results = io_manager.async_read_batch(candidate_ids)
    
    for vid, vec in batch_results.items():
        print(f"\n=> Đã đọc Vector ID {vid} từ Ổ cứng:")
        print(f"Dữ liệu (5 chiều đầu): {vec[:5]}")
        
    # Đọc lại lần 2 để test Cache
    print("\n--- TEST CACHE HIT ---")
    cached_vec = io_manager.get_vector(1)
    print("Lấy Vector ID 1 (Lần này sẽ lấy từ RAM Cache thay vì SSD):")
    print(f"Dữ liệu: {cached_vec[:5]}")

