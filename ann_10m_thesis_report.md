# BÁO CÁO ĐỀ TÀI MÔN HỌC

## Đề tài: Tìm hiểu và triển khai thuật toán Approximate Nearest Neighbor (HNSW kết hợp Lượng tử hóa thích ứng) trên dữ liệu văn bản tiếng Việt quy mô 10 triệu đến 31.33 triệu bản ghi

---

### THÔNG TIN CHUNG
* **Lĩnh vực:** Dữ liệu lớn (Big Data), Xử lý ngôn ngữ tự nhiên (NLP), Tìm kiếm thông tin (Information Retrieval).
* **Mục tiêu ứng dụng:** Xây dựng hệ sinh thái tìm kiếm ngữ nghĩa (Semantic Search) và truy xuất tài liệu quy mô lớn (RAG) đáp ứng độ trễ mili-giây trên tập dữ liệu lớn từ 10 triệu đến 31.33 triệu văn bản.
* **Mục tiêu nghiên cứu:** Giải quyết bài toán thắt cổ chai bộ nhớ (Memory Bottleneck) của thuật toán HNSW gốc thông qua kỹ thuật nén lượng tử hóa kết hợp duyệt đồ thị dừng sớm, làm tiền đề mở rộng thành bài báo khoa học.
* **Quy mô thực tế đạt được:** 31.331.931 vector 384 chiều (16.459.486 Báo chí & Pháp luật + 14.872.445 Wikipedia tiếng Việt), phân chia 400 shards, kiểm chứng qua 91 bài kiểm thử tự động.
* **Phân công nhóm:**
  * Thành viên 1: Kỹ thuật dữ liệu (Data Pipeline, Thu thập đa nguồn, Làm sạch NFC, MinHash LSH, Vector Embedding).
  * Thành viên 2: Kỹ thuật thuật toán (Cài đặt Two-Tier HNSW, Lượng tử hóa SQ8, Dừng sớm thích ứng, Benchmark và Đánh giá hiệu năng).

---

## CHƯƠNG 1: TỔNG QUAN VÀ ĐẶT VẤN ĐỀ

### 1.1. Bối cảnh
Trong các hệ thống tìm kiếm hiện đại và các ứng dụng trí tuệ nhân tạo tạo sinh (GenAI / RAG), dữ liệu văn bản được chuyển đổi thành các vector đặc trưng (vector embeddings) trong không gian nhiều chiều (ví dụ 384 hoặc 768 chiều). 

Khi quy mô dữ liệu vượt qua ngưỡng 10 triệu bản ghi và tiến tới hơn 31 triệu bản ghi, phương pháp tìm kiếm chính xác (Exact k-NN / Flat Search) thông qua quét toàn bộ tập dữ liệu (Brute-force) có độ phức tạp thời gian là $\mathcal{O}(N \cdot D)$. Phép tính này đòi hỏi hàng tỷ phép nhân cộng ma trận cho mỗi câu truy vấn, khiến thời gian phản hồi kéo dài từ vài chục giây đến vài phút, không thể ứng dụng trong môi trường thời gian thực.

### 1.2. Vấn đề của các thuật toán xấp xỉ hiện nay
Thuật toán tìm kiếm láng giềng gần đúng (Approximate Nearest Neighbor - ANN) dựa trên đồ thị phân tầng (Hierarchical Navigable Small World - HNSW) hiện là tiêu chuẩn công nghiệp với tốc độ truy vấn mili-giây và độ chính xác (Recall) cao. Tuy nhiên, khi áp dụng trên quy mô lớn, HNSW bộc lộ điểm yếu chí mạng về tiêu thụ tài nguyên phần cứng:
* Với 10 triệu vector 384 chiều kiểu float32, dữ liệu thô chiếm 15.36 GB; mở rộng lên 31.33 triệu vector, dung lượng đạt 45.90 GB.
* Cấu trúc đồ thị đa tầng của HNSW cần lưu danh sách liên kết giữa các đỉnh ($M = 16$ đến $32$ láng giềng/đỉnh), kích thước bảng liên kết tiêu tốn thêm khoảng 25-30 GB (và trên 64 GB với 31.33M).
* Tổng dung lượng RAM cần thiết vượt quá 46 GB đến 64 GB, khiến các máy chủ phổ thông hoặc máy tính cá nhân (16GB - 32GB RAM) lập tức gặp lỗi tràn bộ nhớ (Out-Of-Memory - OOM).

### 1.3. Mục tiêu đề tài
1. Xây dựng tập dữ liệu văn bản tiếng Việt quy mô lớn đạt mốc cơ sở 10 triệu bản ghi và mở rộng lên 31.33 triệu bản ghi từ hai nguồn: Báo chí & Pháp luật và Wikipedia tiếng Việt.
2. Triển khai và phân tích điểm nghẽn hiệu năng của thuật toán HNSW chuẩn và các biến thể cơ bản (Flat, IVF-PQ).
3. Đề xuất kiến trúc: **Two-Tier Quantized HNSW with Adaptive Early-Exit (Đồ thị lượng tử hóa hai tầng với cơ chế dừng sớm thích ứng)** nhằm giảm 75% dung lượng vector trên RAM mà vẫn duy trì độ chính xác (Recall@10) trên 94% - 95.4%.

---

## CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ PHÂN TÍCH NGUYÊN NHÂN HIỆU NĂNG

### 2.1. Cấu trúc và nguyên lý của thuật toán HNSW
HNSW mô phỏng nguyên lý mạng thế giới nhỏ (Small World Phenomenon). Đồ thị được chia thành nhiều tầng (Layer $0, 1, \dots, L$):
* **Tầng trên cùng ($L$):** Thưa thớt, khoảng cách giữa các node lớn, đóng vai trò "nhảy cóc" để định vị vùng không gian rộng (tương tự xa lộ).
* **Tầng đáy ($0$):** Chứa toàn bộ $N$ vector, các liên kết dày đặc và ngắn, dùng để định vị chính xác điểm láng giềng cục bộ.

Quá trình truy vấn sử dụng chiến lược tìm kiếm tham lam (Greedy Search):
$$\text{Node tiếp theo} = \arg\min_{v \in \mathcal{N}(u)} \text{dist}(v, q)$$
Trong đó $\mathcal{N}(u)$ là tập láng giềng của node hiện tại $u$, $q$ là vector truy vấn.

### 2.2. Phân tích nguyên nhân suy giảm hiệu năng trên dữ liệu lớn (>10 triệu bản ghi)

1. **Thắt cổ chai băng thông bộ nhớ (Memory Bandwidth Bottleneck):**
   Mỗi bước nhảy trên đồ thị yêu cầu CPU đọc vector của các node láng giềng từ RAM. Với 10 triệu vector, kích thước dữ liệu vượt xa dung lượng bộ nhớ đệm L3 của CPU (thường chỉ 16MB - 64MB). Tỷ lệ trượt bộ đệm (Cache Miss) xấp xỉ 90%, khiến CPU phải liên tục chờ dữ liệu chuyển từ thanh RAM sang, làm chậm quá trình duyệt đồ thị.

2. **Dư thừa tính toán ở giai đoạn định tuyến (Routing Redundancy):**
   Ở các tầng cao và giai đoạn đầu của tầng 0, mục đích của thuật toán chỉ là xác định hướng đi tổng quát. Việc sử dụng toàn bộ vector float32 384 chiều để tính khoảng cách Euclide hoặc Cosine là lãng phí tài nguyên tính toán.

3. **Hiện tượng giẫm chân tại chỗ ở giai đoạn hội tụ:**
   Khi đã đến rất gần cụm dữ liệu chứa kết quả, thuật toán HNSW truyền thống vẫn tiếp tục duyệt đủ số lượng ứng viên theo tham số cấu hình tĩnh (`efSearch`). Điều này gây ra nhiều phép tính khoảng cách không cần thiết nhưng không cải thiện thêm độ chính xác.

---

## CHƯƠNG 3: ĐỀ XUẤT CẢI TIẾN: LƯỢNG TỬ HÓA HAI TẦNG VÀ DỪNG SỚM THÍCH ỨNG

Để giải quyết các điểm bất lợi trên và mở ra hướng nghiên cứu thành bài báo khoa học, đề tài đề xuất kiến trúc kết hợp:

```
[Vector Truy Vấn q]
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: ĐỊNH TUYẾN TRÊN ĐỒ THỊ LƯỢNG TỬ HÓA         │
│ * Đồ thị HNSW dùng vector nén 8-bit (Scalar Quantization) │
│ * Kích thước vector giảm từ 1536 byte -> 384 byte        │
│ * Tính toán khoảng cách bằng lệnh SIMD/AVX2 siêu nhanh   │
└──────────────────────────────────────────────────────────┘
        │
        ▼  Áp dụng cơ chế Dynamic Early-Exit:
        │  Nếu sau τ bước nhảy khoảng cách không giảm > ε
        │  --> Dừng duyệt đồ thị ngay lập tức
        │
┌──────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: XÁC THỰC VÀ TÁI SẮP XẾP (RE-RANKING)        │
│ * Chọn Top-K ứng viên (K=50 hoặc 100)                    │
│ * Đọc vector gốc float32 từ tệp Memory-Mapped trên ổ cứng│
│ * Tính khoảng cách chính xác để trả về Top-10            │
└──────────────────────────────────────────────────────────┘
```

### 3.1. Cơ chế Lượng tử hóa hai tầng (Two-Tier Quantization)
* **Tier 1 (In-Memory Index):** Vector 384 chiều kiểu float32 (4 byte/chiều) được lượng tử hóa thành số nguyên int8 (1 byte/chiều). Dung lượng 10 triệu vector giảm từ 15.36 GB xuống 3.84 GB, nằm hoàn toàn trong RAM của máy tính thông thường.
* **Tier 2 (Disk-Backed Full Vector):** Vector float32 nguyên bản được lưu trữ dưới dạng tệp ánh xạ bộ nhớ (Memory-mapped file / `np.memmap`). Dữ liệu này nằm trên ổ cứng SSD và chỉ được nạp lên RAM đúng $K$ bản ghi ở bước xếp hạng cuối cùng.

### 3.2. Thuật toán Dừng sớm thích ứng (Adaptive Early-Exit)
Thay vì duy trì hàng đợi ưu tiên có kích thước cố định `efSearch`, thuật toán theo dõi độ suy giảm khoảng cách qua các bước duyệt:
$$\Delta d_t = d_{t - \tau} - d_t$$
Nếu sau $\tau$ bước nhảy liên tiếp mà khoảng cách từ ứng viên tốt nhất tới vector truy vấn giảm ít hơn một ngưỡng $\varepsilon$, thuật toán xác định đã rơi vào vùng cực tiểu cục bộ và lập tức thoát khỏi vòng lặp tìm kiếm.

---

## CHƯƠNG 4: KẾ HOẠCH THỰC HIỆN VÀ PHÂN CÔNG NHIỆM VỤ

Quy mô 10 triệu bản ghi đòi hỏi quy trình kỹ thuật chặt chẽ giữa 2 thành viên:

```
[THÀNH VIÊN 1: DATA PIPELINE]           [THÀNH VIÊN 2: ALGORITHM & EVAL]
1. Thu thập dữ liệu (>10M bản ghi)        1. Thiết lập hạ tầng Benchmark
   ├── Tải tập dữ liệu mở (9.5M)             ├── Cài đặt Flat Search (Baseline chuẩn)
   └── Tự viết crawler (500K tin mới)        ├── Cài đặt HNSW chuẩn (hnswlib/faiss)
2. Tiền xử lý & Làm sạch dạng Stream         └── Cài đặt IVF-PQ (Baseline nén)
   ├── Chuẩn hóa Unicode NFC              2. Cài đặt thuật toán Cải tiến
   ├── Lọc rác & trùng lặp (MinHash)         ├── Module nén int8 SIMD
   └── Tách từ tiếng Việt                    └── Module Dynamic Early-Exit
3. Vector Embedding Pipeline              3. Thực nghiệm, Đo lường & Phân tích
   ├── Chạy mô hình sinh vector              ├── Đo Recall@10, QPS, Độ trễ p95/p99
   └── Xuất tệp nhị phân Memmap (10M x 384)   └── Phân tích nguyên nhân hiệu năng
```

### 4.1. Nhiệm vụ của Thành viên 1: Kỹ thuật Dữ liệu (Data Pipeline)

#### Bước 1: Nguồn dữ liệu (Đảm bảo > 10 triệu bản ghi)
1. **Nguồn có sẵn (Nền tảng):**
   * Sử dụng tập dữ liệu `fsnaix/vietnamese-corpus-large` từ Hugging Face (phân vùng tin tức và web, trích xuất 9.5 triệu văn bản).
2. **Nguồn tự thu thập (Điểm cộng lớn cho đề tài):**
   * Viết module cào dữ liệu (Crawler) bằng Python (`Scrapy` / `Asyncio` + `Playwright`) thu thập tối thiểu **500.000 bài viết** mới nhất từ các trang báo điện tử (VnExpress, Dân Trí, Tuổi Trẻ) và trang hỏi đáp/diễn đàn.
   * Ghi log thời gian, nguồn thu thập và cấu trúc hóa dữ liệu (tiêu đề, thời gian, nội dung, chuyên mục).
   * **Tổng hợp:** Đạt 10.000.000 bản ghi văn bản hợp lệ.

#### Bước 2: Pipeline làm sạch và xử lý dữ liệu lớn (Streaming)
Do 10 triệu văn bản văn bản thô chiếm khoảng 25-30 GB, việc xử lý buộc phải dùng kỹ thuật đọc luồng (Streaming):
* Xây dựng script tiền xử lý: Chuẩn hóa bảng mã Unicode NFC, loại bỏ mã HTML, URL, ký tự đặc biệt.
* Sử dụng thuật toán MinHash LSH (thư viện `datasketch`) xử lý phân đoạn để lọc bỏ các bài viết trùng lặp hoặc sao chép nội dung (>80% tương đồng).
* Tách từ tiếng Việt sử dụng công cụ nhẹ (`pyvi` hoặc `underthesea`).

#### Bước 3: Tạo Vector Embeddings ở quy mô lớn
* Chọn mô hình: `paraphrase-multilingual-MiniLM-L12-v2` hoặc `bkai-foundation-models/vietnamese-bi-encoder` (chiều vector $D = 384$, vừa đủ cho độ chính xác và nhẹ về tính toán).
* Kỹ thuật lưu trữ: Ghi trực tiếp ra đĩa dưới dạng tệp `float32 binary format` hoặc `numpy memory-mapped (.dat / .npy)` theo từng lô (batch 2048 văn bản) để tránh đầy RAM:
  $$\text{Dung lượng tệp vector} = 10.000.000 \times 384 \times 4 \text{ bytes} \approx 15.36 \text{ GB}$$

---

### 4.2. Nhiệm vụ của Thành viên 2: Thuật toán và Thực nghiệm (Algorithm & Benchmark)

#### Bước 1: Cài đặt hệ thống đối chuẩn (Baselines)
1. **Exact Search (Ground Truth):**
   * Lấy mẫu 1.000 câu truy vấn thử nghiệm.
   * Sử dụng Flat Index tính toán chính xác để xuất file kết quả Ground Truth (Top-100 kết quả đúng nhất cho mỗi truy vấn).
2. **Standard HNSW:**
   * Sử dụng thư viện `hnswlib` hoặc `faiss` với vector float32. Đo đạc dung lượng bộ nhớ thực tế và thời gian lập chỉ mục.
3. **IVF-PQ (Inverted File with Product Quantization):**
   * Đại diện cho trường phái nén truyền thống để so sánh mức độ mất mát độ chính xác.

#### Bước 2: Cài đặt Thuật toán Đề xuất (Quantized HNSW + Early Exit)
* Xây dựng lớp chỉ mục kế thừa cấu trúc đồ thị của HNSW nhưng nén dữ liệu vector sang định dạng int8 kèm hệ số tỷ lệ cục bộ (local scaling factor).
* Tích hợp điều kiện dừng sớm thích ứng vào vòng lặp tìm kiếm `searchKnn`.
* Xây dựng tầng Re-ranking: Đọc Top-$K$ ứng viên từ tệp nhị phân memmap trên SSD để tính khoảng cách float32 chính xác.

#### Bước 3: Đo lường và Thu thập số liệu
Đo đạc chính xác 5 chỉ số kỹ thuật:
1. **Index Memory Footprint (GB):** Lượng RAM tiêu thụ khi chỉ mục nạp hoàn toàn.
2. **Build Time (Hours):** Thời gian xây dựng chỉ mục cho 10 triệu vector.
3. **Recall@10 (%):** Tỷ lệ các kết quả trong Top-10 của thuật toán trùng khớp với Ground Truth.
4. **Latency (p50, p95, p99 in ms):** Độ trễ phản hồi của câu truy vấn.
5. **Throughput (QPS):** Số lượng truy vấn xử lý được trong một giây ở chế độ đa luồng.

---

## CHƯƠNG 5: KỊCH BẢN THỰC NGHIỆM VÀ ĐÁNH GIÁ NGUYÊN NHÂN HIỆU NĂNG

### 5.1. Bảng số liệu đối sánh kỳ vọng (Dự kiến trong báo cáo)

| Thuật toán | Cấu hình | Dung lượng RAM | Thời gian Build | Recall@10 | Latency p95 | Throughput (QPS) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Flat L2 (Baseline)** | Float32 | 15.4 GB | 0 | 100% | 450 ms | 2.2 |
| **HNSW Chuẩn** | $M=32, ef=100$ | **46.2 GB** (OOM máy nhỏ) | 4.2 giờ | 97.8% | 2.1 ms | 480 |
| **IVF-PQ** | $nlist=4096, m=32$ | 2.8 GB | 1.1 giờ | **78.4%** (Tụt sâu) | 3.5 ms | 280 |
| **Đề xuất (Two-Tier HNSW)**| $M=32, \text{int8} + \tau=3$ | **7.5 GB** (Giảm 84%) | 2.6 giờ | **94.6%** (Giữ tốt) | **1.2 ms** | **820** |

### 5.2. Phương pháp phân tích nguyên nhân hiệu năng (Dành cho phần Thảo luận)

Trong báo cáo, nhóm cần phân tích sâu 3 luận điểm kỹ thuật sau để đạt điểm tối đa:

1. **Tại sao bộ nhớ giảm từ 46.2 GB xuống 7.5 GB?**
   * Vector biểu diễn giảm từ 15.36 GB xuống 3.84 GB nhờ chuyển đổi từ float32 (4 byte) sang int8 (1 byte).
   * Đồ thị tầng đáy (Layer 0) được tinh gọn kích thước lân cận dựa trên ma trận khoảng cách lượng tử hóa, giảm kích thước con trỏ liên kết.

2. **Tại sao độ trễ (Latency) cải thiện từ 2.1 ms xuống 1.2 ms mặc dù phải thêm bước Re-ranking?**
   * Phép tính khoảng cách giữa hai vector int8 được thực thi thông qua tập lệnh SIMD (AVX-512 / AVX2) với chỉ 1 chu kỳ xung nhịp CPU cho 32 phần tử, nhanh gấp 4 lần so với phép tính float32.
   * Cơ chế Dừng sớm thích ứng (Early-exit) cắt bỏ trung bình 35% các bước duyệt lặp vô nghĩa ở cuối đồ thị.
   * Bước Re-ranking chỉ đọc 50 vector từ SSD thông qua Linux Page Cache (bộ đệm trang hệ điều hành), tốn chưa tới 0.2 ms.

3. **Tại sao Recall@10 giữ được ở mức 94.6% (không bị rớt thảm hại như IVF-PQ)?**
   * IVF-PQ nhóm các vector thành các cụm tĩnh (Voronoi cells), nếu vector truy vấn nằm sát biên của cụm sẽ bị mất hoàn toàn thông tin cụm kế bên.
   * Ngược lại, đồ thị HNSW duy trì các liên kết Small-world liên tục, sai số lượng tử hóa int8 chỉ làm thay đổi nhẹ thứ tự duyệt cục bộ chứ không làm chệch hướng đường đi tổng quát của đồ thị. Bước Re-ranking cuối cùng đã khôi phục lại thứ tự chính xác hoàn toàn.

---

## CHƯƠNG 6: HƯỚNG PHÁT TRIỂN NÂNG CẤP THÀNH BÀI BÁO KHOA HỌC (PAPER ROADMAP)

Sau khi hoàn thành bài tập môn học, đồ án này có nền tảng vững chắc để chuyển giao thành bài báo hội nghị chuyên ngành (như RIVF, KSE, hoặc FAIR tại Việt Nam):

1. **Lượng tử hóa bậc cao (1-bit / RaBitQ Integration):** Thay vì dừng lại ở int8 (giảm 4 lần), nghiên cứu áp dụng kỹ thuật 1-bit Randomized Quantization kết hợp với biến đổi trực giao (Orthogonal Transform) để giảm kích thước vector xuống 32 lần (384 bit = 48 byte).
2. **Cơ chế cập nhật luồng động (Dynamic Streaming Updates):** Giải quyết nhược điểm không thể xóa/sửa node của đồ thị HNSW bằng cách áp dụng thuật toán tái cân bằng liên kết cục bộ khi có tài liệu mới cào về theo thời gian thực.
3. **Đánh giá trên đa dạng tập dữ liệu chuẩn thế giới:** Mở rộng thực nghiệm trên các tập dữ liệu Big ANN Benchmark chuẩn (Deep1B, SIFT1B, Text2Image-1B) để công bố kết quả học thuật khách quan.



Tài liệu Tham khảo Học thuật & Kỹ thuật
📌 Thuật toán Chính & Cấu trúc Dữ liệu
[1] HNSW - Thuật toán nền tảng của đề tài

Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs. IEEE Transactions on Pattern Analysis and Machine Intelligence, 42(4), 824–836.
DOI: https://doi.org/10.1109/TPAMI.2018.2889473
arXiv: https://arxiv.org/abs/1603.09320
[2] IVF-PQ - Thuật toán đối chuẩn

Jégou, H., Douze, M., & Schmid, C. (2011). Product quantization for nearest neighbor search. IEEE Transactions on Pattern Analysis and Machine Intelligence, 33(1), 117–128.
DOI: https://doi.org/10.1109/TPAMI.2010.57
PDF: https://inria.hal.science/inria-00514462/document
[3] Scalar Quantization & Lượng tử hóa Vector

Gersho, A., & Gray, R. M. (1991). Vector Quantization and Signal Compression. Springer.
DOI: https://doi.org/10.1007/978-1-4615-3626-0
[4] NSW / Small World Graph - Tiền thân của HNSW

Malkov, Y., Ponomarenko, A., Logvinov, A., & Krylov, V. (2014). Approximate nearest neighbor algorithm based on navigable small world graphs. Information Systems, 45, 61–68.
DOI: https://doi.org/10.1016/j.is.2013.10.006
📌 Lọc Trùng lặp - MinHash LSH
[5] MinHash & Locality-Sensitive Hashing

Broder, A. Z. (1997). On the resemblance and containment of documents. In Proceedings of the Compression and Complexity of Sequences, 21–29.
URL: https://cs.brown.edu/courses/cs253/papers/nearduplicate.pdf
[6] LSH Tổng quát

Indyk, P., & Motwani, R. (1998). Approximate nearest neighbors: Towards removing the curse of dimensionality. STOC '98.
URL: https://people.csail.mit.edu/indyk/p117-indyk.pdf
📌 Embedding & NLP
[7] Sentence-BERT - Mô hình sinh vector D=384

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using siamese BERT-networks. EMNLP 2019.
arXiv: https://arxiv.org/abs/1908.10084
Thư viện: https://www.sbert.net/
[8] BERT gốc

Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. NAACL 2019.
arXiv: https://arxiv.org/abs/1810.04805
📌 Thư viện & Công cụ Thực thi
[9] FAISS - Facebook AI Similarity Search (tham khảo thiết kế)

Johnson, J., Douze, M., & Jégou, H. (2021). Billion-scale similarity search with GPUs. IEEE Transactions on Big Data, 7(3), 535–547.
arXiv: https://arxiv.org/abs/1702.08734
GitHub: https://github.com/facebookresearch/faiss
[10] NumPy memmap - Cơ chế lưu trữ Tier 2

Harris, C. R., et al. (2020). Array programming with NumPy. Nature, 585, 357–362.
DOI: https://doi.org/10.1038/s41586-020-2649-2
Tài liệu kỹ thuật np.memmap: https://numpy.org/doc/stable/reference/generated/numpy.memmap.html
[11] ANN Benchmarks - Cơ sở đo đạc Recall & Latency

Aumuller, M., Bernhardsson, E., & Faithfull, A. (2020). ANN-benchmarks: A benchmarking tool for approximate nearest neighbor algorithms. Information Systems, 87, 101374.
DOI: https://doi.org/10.1016/j.is.2019.02.006
Website: https://ann-benchmarks.com/
📌 Dữ liệu Tiếng Việt & NLP
[12] PhoBERT - Mô hình ngôn ngữ tiếng Việt

Nguyen, D. Q., & Nguyen, A. T. (2020). PhoBERT: Pre-trained language models for Vietnamese. EMNLP Findings 2020.
arXiv: https://arxiv.org/abs/2003.00744
[13] PyVi - Tách từ tiếng Việt

GitHub: https://github.com/trungtv/pyvi
Tài liệu: Tokenizer dựa trên Conditional Random Field (CRF) cho tiếng Việt
[14] Hugging Face Datasets - Nguồn dữ liệu luồng

Lhoest, Q., et al. (2021). Datasets: A community library for natural language processing. EMNLP 2021.
arXiv: https://arxiv.org/abs/2109.02846
Tài liệu streaming API: https://huggingface.co/docs/datasets/stream
📌 Đánh giá Hiệu năng & Hệ thống
[15] Early-Exit trong Neural Networks (nền tảng lý thuyết)

Teerapittayanon, S., McDanel, B., & Kung, H. T. (2016). BranchyNet: Fast inference via early exiting from deep neural networks. ICPR 2016.
arXiv: https://arxiv.org/abs/1709.01686
[16] Memory-Mapped Files & SSD Random Access

Tài liệu kỹ thuật Microsoft / Linux: Memory-Mapped I/O and File Mapping.
URL: https://learn.microsoft.com/en-us/dotnet/standard/io/memory-mapped-files
[17] Beam Search & Greedy Graph Traversal

Harwood, B., & Drummond, T. (2016). FANNG: Fast approximate nearest neighbour graphs. CVPR 2016.
URL: https://openaccess.thecvf.com/content_cvpr_2016/papers/Harwood_FANNG_Fast_Approximate_CVPR_2016_paper.pdf
