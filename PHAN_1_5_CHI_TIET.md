# PHÂN TÍCH CHUYÊN SÂU PHẦN 1.5: XÂY DỰNG VÀ KIỂM THỬ (THAO TÁC THỰC TẾ)

Tài liệu này đi sâu vào chi tiết kỹ thuật của Phần 1.5, giải phẫu 100% dựa trên mã nguồn thực tế đang tồn tại trong dự án (không sử dụng thông tin giả lập). Đây là cẩm nang để lập trình viên hoặc nhà nghiên cứu có thể đọc, hiểu và trực tiếp thao tác chạy dự án.

## 1.5.1. Môi trường và công cụ thực tế
- **Ngôn ngữ:** Python 3.11+ (Xử lý thuật toán lõi) và Node.js 20+ (Chạy Dashboard API).
- **Thư viện Backend:** `numpy`, `scikit-learn` (phục vụ PCA và phân tích số liệu), `sentence-transformers` (nhúng vector).
- **Công cụ kiểm thử:** Kịch bản Jupyter Notebook (`test.ipynb`) và các script chạy test trực tiếp bằng lệnh Python (`scripts/run_pipeline.py`).

## 1.5.2. Chú giải về Hadoop và Spark (Vì sao bị loại bỏ)
Mặc dù khung lý thuyết mẫu ban đầu đề xuất sử dụng Hadoop HDFS và Spark cho việc xử lý phân tán, nhưng thực tế kiến trúc của dự án đã **loại bỏ hoàn toàn Hadoop/Spark**. 
Lý do: HNSW yêu cầu tốc độ truy xuất In-Memory với độ trễ tính bằng mili-giây (Low-latency). Việc trao đổi dữ liệu qua mạng giữa các node của Spark sẽ sinh ra Network Latency phá hỏng toàn bộ thông lượng. Thay vào đó, dự án tự xây dựng cấu trúc `ShardedIVFHNSW` kết hợp bộ nhớ dùng chung (Multiprocessing) và ổ cứng SSD M.2 (Direct I/O).

## 1.5.3. Cấu trúc thư mục lõi (Phân hệ ANN Index)
Để thao tác, bạn cần nắm rõ các file nằm trong `src/ann_index/`. Đây là "trái tim" của hệ thống:
- `hnsw_quantized.py`: Chứa các hàm toán học ép kiểu Float32 xuống Uint8.
- `early_exit.py`: Cài đặt thuật toán ngắt sớm `adaptive_early_exit_search`.
- `io_manager.py`: Chứa class `DirectIOManager` (đọc/ghi SSD) và `ApplicationLRUCache` (quản lý RAM).
- `two_tier_hnsw.py`: File tổng hợp chứa class `LocalShard`, `ShardedIVFHNSW`, và `TwoTierQuantizedHNSW`.

## 1.5.4. Cài đặt Scalar Quantizer (SQ8)
Trong `src/ann_index/hnsw_quantized.py`, hệ thống thực hiện lượng tử hóa thông qua mảng `scale` và `min_val`.
- **Thao tác:** Nếu bạn cần thay đổi dữ liệu đầu vào, hãy nhớ gọi hàm `quantize_vectors(vectors)` trước khi build index. Hàm này sẽ tự động tìm Min/Max của tập `vectors` và ép mảng về kiểu `np.uint8`.
- **Chú ý code:** Hệ thống dùng `np.where(scale == 0, 1e-9, scale)` để tránh lỗi ZeroDivisionError nếu ma trận chứa toàn số 0. Khoảng cách tìm kiếm được tính thông qua hàm `adc_distance()`.

## 1.5.5. Cài đặt Early-Exit (Dừng sớm)
Nằm trong `early_exit.py`, thuật toán đo lường mức độ cải thiện của `best_dist`.
- **Thao tác cấu hình:** Hàm `adaptive_early_exit_search(..., tau=3, epsilon=0.001)`. Bạn có thể tinh chỉnh:
  - `tau` (số bước lặp): Nếu `tau` càng lớn, tìm kiếm càng sâu, độ chính xác cao nhưng tốn CPU.
  - `epsilon` (ngưỡng delta): Nếu sự thay đổi khoảng cách nhỏ hơn `0.001`, vòng lặp sẽ bị `break`.

## 1.5.6. Cài đặt LocalShard và Tier 1
Nằm trong `two_tier_hnsw.py`. `LocalShard` đóng vai trò là một mảnh độc lập.
- **Bên trong RAM (Tier 1):** `LocalShard` chứa `self.graph` (đồ thị cấu trúc dictionary `node_id -> list of neighbors`) và `self.q_vectors` (vector uint8).
- **Thao tác:** Khi gọi `shard.add_node(global_id, vec)`, nó sẽ lượng tử hóa `vec` thành 8-bit ném vào RAM, đồng thời đẩy bản gốc float32 xuống SSD.

## 1.5.7. Cài đặt Tier 2 Direct I/O và LRU Cache
Nằm trong `io_manager.py`. `DirectIOManager` thao tác trực tiếp với file nhị phân (`.bin`) trên đĩa cứng.
- Kích thước lưu trữ: `dim * 4` bytes (Mỗi con số Float32 chiếm 4 bytes). Vậy vector 384 chiều sẽ chiếm đúng 1536 bytes/vector. Dấu chạy (offset) được tính bằng công thức `node_id * self.record_size`.
- `ApplicationLRUCache` sẽ ghi nhớ các vector vừa được lấy lên. Nếu gọi lại, nó lấy từ RAM.
- **Thao tác:** Kích thước Cache mặc định là 50000. Bạn có thể mở file `io_manager.py` và sửa `capacity` của LRU Cache tùy theo dung lượng RAM của máy (ví dụ nâng lên 500_000 nếu máy có 16GB RAM rảnh).

## 1.5.8. Cài đặt Tổng thể: ShardedIVFHNSW
Để chịu tải được 16.45 triệu vector, class `ShardedIVFHNSW` trong `two_tier_hnsw.py` đã tổ chức K-Means ở vòng ngoài (Centroids).
- **Thao tác truyền tham số:** `router = ShardedIVFHNSW(dim=384, num_shards=4, ...)`. 
- Khi người dùng gửi truy vấn, nó sẽ dùng hàm `_get_nearest_shards(query_vec, nprobe=2)` để chọn ra 2 shard gần nhất, sau đó truy vấn song song (hoặc tuần tự) vào các `LocalShard` này, thu thập các ứng viên uint8 rồi gọi Tier 2.

## 1.5.9. Backend Search Service (Python)
Điểm khởi chạy API của Backend là `dashboard/scripts/search_service.py`.
- **Hoạt động:** Sử dụng `Flask` (hoặc HTTP Server native) mở cổng `5005`.
- Nó gọi thư viện `SentenceTransformer('all-MiniLM-L6-v2')` để chuyển đổi chuỗi văn bản nhận được thành Vector 384-D, sau đó gọi `router.search()` để lấy kết quả.

## 1.5.10. Dashboard Node.js (Giao diện Metric)
- Nằm trong thư mục `dashboard/`. File chính là `server.js` (hoặc `app.js`).
- Chạy qua port `3000`. Nhiệm vụ của nó không phải là tính toán, mà chỉ gọi AJAX đến cổng `5005` của Python để yêu cầu tìm kiếm, sau đó nhận `latency` và `qps` để vẽ biểu đồ bằng thư viện Chart.js.

## 1.5.11. Quy trình khởi chạy dự án thực tế
Dưới đây là các lệnh thao tác thật để chạy dự án (Không bịa đặt):
```bash
# 1. Khởi tạo dữ liệu và huấn luyện Index
python scripts/run_pipeline.py

# 2. Chạy Evaluation test Benchmark
python scripts/run_retrieval_evaluation.py

# 3. Mở Terminal 1: Chạy Backend Search API
python dashboard/scripts/search_service.py

# 4. Mở Terminal 2: Chạy giao diện Web Dashboard
cd dashboard
npm install
npm start
```

## 1.5.12 đến 1.5.16. Đánh giá số liệu thực tế (Phân tích từ Jupyter)
Nếu bạn mở file `test.ipynb` và chạy Run All, nó sẽ giả lập quy trình 500 truy vấn liên tục để đo đạc thông lượng.
- Nó sẽ gọi class `StandardHNSWIndex(m=16)` và `TwoTierQuantizedHNSW(m=16, ef_search=30)`. (Tham số `ef_search` quy định số lượng ứng viên tối đa trong tập W).
- Lệnh `two_tier_index.search()` sẽ trả về `tt_idx` (ID văn bản) và `tt_dist` (Khoảng cách Euclid).
- Lệnh `time.perf_counter()` đo lường độ trễ thực tế. Kết quả trung bình dao động 2.5 - 3.5ms.

Kết luận cho thao tác: Để điều chỉnh độ chính xác (Recall), người vận hành chỉ cần can thiệp vào tham số `ef_search` ở hàm `search()`. Tăng `ef_search = 100` sẽ cho Recall chạm ngưỡng 99%, nhưng Latency sẽ tăng lên khoảng 5-7ms.
