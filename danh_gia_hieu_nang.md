# BÁO CÁO PHÂN TÍCH VÀ ĐÁNH GIÁ HIỆU NĂNG THUẬT TOÁN (PERFORMANCE EVALUATION)

Tài liệu này phân chia rõ ràng các tiêu chí cơ bản và nâng cao để đánh giá sự ưu việt của Kiến trúc phân tán (Fault-Tolerant Distributed ANN) so với các giải pháp nguyên thủy. Trọng tâm giải thích nguyên nhân vật lý/toán học đằng sau các con số hiệu năng.

---

## PHẦN 1: CÁC TIÊU CHÍ CƠ BẢN (KHẲNG ĐỊNH TÍNH KHẢ THI)

### 1. Tối ưu hóa dung lượng RAM (Memory Footprint)
- **Biểu đồ chứng minh:** `metric_1_ram.png`
- **Kết quả:** Dung lượng RAM cho 10 triệu vector giảm từ 15.36 GB (Naive Float32) xuống còn 3.84 GB (SQ8 ADC).
- **Nguyên nhân hưởng hiệu năng:** Thay vì lưu các ma trận float32 cồng kềnh, thuật toán Tier 1 áp dụng Lượng tử hóa vô hướng (Scalar Quantization - SQ8). Dữ liệu bị ép xuống định dạng `uint8`, vứt bỏ 3 byte thừa trên mỗi chiều không gian.
- **Đề xuất cải thiện thuật toán:** Áp dụng Product Quantization (PQ) thay vì SQ8 nếu dữ liệu tăng lên mốc 100 triệu, cắt giảm vector 384 chiều thành các mã ngắn (short codes) để ép RAM xuống mức MB thay vì GB.

### 2. Tốc độ truy vấn (Search Latency)
- **Biểu đồ chứng minh:** `metric_2_latency.png`
- **Kết quả:** Brute-force (~5000ms) -> HNSW gốc (~45ms) -> Sharded IVF-HNSW (~12ms).
- **Nguyên nhân hưởng hiệu năng:** 
  - Đạt 45ms: Nhờ cấu trúc phân tầng Navigable Small World, độ phức tạp giảm từ $O(N)$ xuống $O(\log N)$.
  - Đạt 12ms: Nhờ thuật toán K-Means Sharding (IVF). Router ném lệnh xuống đúng 3 Cụm (Shards) chứa dữ liệu liên quan, bỏ qua 70% khối lượng tìm kiếm.

### 3. Độ chính xác khôi phục (Recall@50)
- **Biểu đồ chứng minh:** `metric_3_recall.png`
- **Kết quả:** Tăng từ 82.5% (Nếu chỉ dùng RAM nén) lên 98.7% (Nhờ Re-ranking).
- **Nguyên nhân hưởng hiệu năng:** Khuyết điểm chí tử của Lượng tử hóa là hiện tượng "biến dạng khoảng cách metric". Thuật toán xử lý triệt để bằng cơ chế Re-ranking: Chỉ dùng bản nén để tìm 50 ứng viên thô, sau đó kéo bản `float32` gốc từ SSD lên đo lại Euclid tuyệt đối để lọc ra Top 5.

---

## PHẦN 2: CÁC TIÊU CHÍ NÂNG CAO (PHÂN TÍCH CHUYÊN SÂU & GIẢI QUYẾT ĐIỂM NGHẼN)

### 4. Tiết kiệm Chu kỳ CPU với Adaptive Early-Exit
- **Biểu đồ chứng minh:** `metric_4_cpu.png`
- **Kết quả:** Tiết kiệm được ~42.3% số đỉnh (nodes) phải duyệt thừa.
- **Nguyên nhân hưởng hiệu năng:** Thuật toán Greedy Search nguyên bản của HNSW rất "cố chấp" đâm vào các hố tối ưu cục bộ. Bằng cách thiết lập tham số `tau` và `epsilon`, thuật toán liên tục tự vấn: "Bước nhảy này có thực sự rút ngắn khoảng cách không?". Nếu đi vào ngõ cụt 3 lần liên tiếp, nó tự động cắt tia (Break). Việc này giải phóng bộ nhớ Cache L1/L2 của CPU, nhường điện toán cho luồng khác.

### 5. Triệt tiêu Độ trễ đuôi ổ đĩa (Tail Latency P99)
- **Biểu đồ chứng minh:** `metric_5_io_tail.png`
- **Kết quả:** Độ trễ nhóm 1% truy vấn chậm nhất (P99) giảm từ 250ms (OS Cache Thrashing) xuống còn 18ms (Direct I/O).
- **Nguyên nhân hưởng hiệu năng:** Hàm `memmap` hoặc thao tác đọc file mặc định phó mặc dữ liệu cho Page Cache của Hệ điều hành. Khi HNSW bắn ra 50 yêu cầu đọc ngẫu nhiên (Random Read) rải rác khắp ổ SSD, HĐH bị "ngợp" và liên tục ném dữ liệu rác vào RAM (Thrashing). Kỹ thuật Async Direct I/O gom 50 lệnh thành một lô (batch) đọc bất đồng bộ, kết hợp Application-Level LRU Cache để hãm triệt để độ trễ phần cứng.

---

## PHẦN 3: TỔNG KẾT VÀ ĐỀ XUẤT CẢI THIỆN TRONG TƯƠNG LAI
1. **Thay thế kết nối tĩnh bằng GNN:** (Như đã phân tích ở Chương 5). Mấu nối đồ thị hiện tại vẫn phụ thuộc vào đo lường khoảng cách đơn thuần. Việc nhúng Graph Neural Networks (GNN) để huấn luyện Edges sẽ là bước ngoặt.
2. **Cập nhật mốc trọng tâm động:** Hiện tại Router dùng K-Means tĩnh. Đề xuất huấn luyện mô hình Mini-batch SGD theo thời gian thực (Online Learning) để các Cụm tự động định hình lại khi dữ liệu tiếng Việt có sự thay đổi về trend (Data Drift).

