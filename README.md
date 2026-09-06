# TÌM HIỂU VÀ TRIỂN KHAI THUẬT TOÁN HNSW KẾT HỢP LƯỢNG TỬ HÓA THÍCH ỨNG TRÊN DỮ LIỆU VĂN BẢN TIẾNG VIỆT QUY MÔ LỚN

> **Đề tài Bài tập Cuối kỳ:** Xử lý Dữ liệu Lớn / Tìm kiếm Thông tin & Hệ Gợi ý  
> **Quy mô Dữ liệu Thực nghiệm:** 10.000.000 bản ghi văn bản tiếng Việt (Vector 384 chiều, dung lượng 15.36 GB)  
> **Kho Dữ liệu Google Drive:** [Tại đây](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)  
---

## 1. TỔNG QUAN ĐỀ TÀI VÀ ĐẶT VẤN ĐỀ

Trong các hệ thống tìm kiếm ngữ nghĩa (Semantic Search) và hệ thống gợi ý (Recommender System) hiện đại, văn bản được chuyển đổi thành các vector đặc trưng nhiều chiều (Dense Embeddings). Khi quy mô cơ sở dữ liệu đạt ngưỡng **10 triệu bản ghi**, các phương pháp truyền thống bộc lộ những điểm nghẽn nghiêm trọng:
1. **Tìm kiếm chính xác (Exact Flat Search):** Có độ phức tạp thời gian O(N * D), đòi hỏi hàng tỷ phép tính ma trận cho mỗi câu truy vấn, gây trễ từ vài trăm mili-giây đến vài giây.
2. **Thuật toán đồ thị xấp xỉ truyền thống (Standard HNSW):** Đạt tốc độ cao (< 3 ms) nhưng tiêu tốn tới **46.2 GB RAM** (15.36 GB vector thô float32 + 30 GB cấu trúc liên kết đồ thị), vượt quá năng lực của các máy chủ và máy trạm phổ thông (16GB - 32GB RAM), dẫn tới lỗi tràn bộ nhớ (Out-Of-Memory).
3. **Thuật toán lượng tử hóa tích (IVF-PQ):** Giảm dung lượng RAM nhưng độ chính xác Recall@10 bị suy giảm nghiêm trọng (chỉ đạt 35% - 40%) do sai số phân cụm Voronoi ở vùng biên.

### Giải pháp Đề xuất: Two-Tier Quantized HNSW with Adaptive Early-Exit
Đề tài xây dựng và triển khai kiến trúc hai tầng kết hợp:
* **Tier 1 (In-Memory Index):** Lượng tử hóa vô hướng 8-bit (SQ8 uint8) giúp nén 75% dung lượng vector trên RAM, kết hợp bộ điều khiển dừng sớm thích ứng (**Adaptive Early-Exit Controller**) với tau = 3, epsilon = 1e-4 để tự động ngắt 35% số bước nhảy không hiệu quả ở tầng 0.
* **Tier 2 (SSD Memmap Storage & Re-ranking):** Lưu trữ toàn bộ 15.36 GB mảng vector float32 nguyên bản trên đĩa SSD thông qua kỹ thuật ánh xạ bộ nhớ (`numpy.memmap`). Sau khi Tier 1 trả về Top-K ứng viên, hệ thống đọc lại vector gốc để tái xếp hạng chính xác (**Exact Float32 Re-ranking**), khôi phục Recall@10 đạt trên **94%**.

```
                           [ Vector Truy Vấn q (384 chiều) ]
                                         │
                                         ▼
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ TIER 1: DUYỆT ĐỒ THỊ LƯỢNG TỬ HÓA TRONG RAM (In-Memory SQ8 Graph)           │
  │ • Vector nén uint8 (1 byte/chiều thay vì 4 bytes) -> Tiết kiệm 75% RAM      │
  │ • Tính khoảng cách nhanh bằng số nguyên                                      │
  │ • Dừng sớm thích ứng: Thoát vòng lặp khi delta_d < 1e-4 trong 3 bước liên tiếp│
  └─────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼ Top-50 Ứng viên (Indices)
  ┌─────────────────────────────────────────────────────────────────────────────┐
  │ TIER 2: TÁI XẾP HẠNG TỪ ĐĨA SSD (SSD Memmap Float32 Re-ranking)              │
  │ • Đọc đúng 50 vector float32 gốc từ tệp nhị phân np.memmap trên SSD          │
  │ • Tính khoảng cách chính xác tuyệt đối                                       │
  │ • Trả về Top-10 kết quả chuẩn xác nhất (Recall > 94%, Độ trễ 1.2 ms)        │
  └─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
ANN_PROJECT/
├── README.md                                # Hướng dẫn tổng thể này
├── pyproject.toml                           # Cấu hình môi trường và test runner
├── ann_10m_thesis_report.md                 # Báo cáo đề tài chi tiết đầy đủ 5 chương
├── BAO_CAO_CUOI_KY_HNSW_QUANTIZATION.docx   # File Báo cáo định dạng Word nộp giảng viên
├── configs/
│   └── default_pipeline.json                # Cấu hình tham số HNSW và Pipeline
├── data/
│   ├── README.md                            # Hướng dẫn tải dữ liệu từ Google Drive
│   ├── raw/                                 # Hướng dẫn và thư mục chứa dữ liệu thô
│   ├── processed/                           # Hướng dẫn và thư mục chứa dữ liệu vector memmap
│   └── experiments/                         # Tệp log kết quả đo đạc thực nghiệm JSON/MD
├── src/
│   ├── ann_data/                            # Module Xử lý Dữ liệu Lớn (Thành viên 1)
│   │   ├── cleaner.py                       # Chuẩn hóa Unicode NFC, bóc tách HTML
│   │   ├── tokenizer.py                     # Tách từ ghép tiếng Việt (PyVi)
│   │   ├── deduplicator.py                  # Lọc trùng lặp MinHash LSH
│   │   ├── embedder.py                      # Sinh vector Sentence-BERT 384 chiều
│   │   ├── storage.py                       # Quản lý bộ đệm nhị phân np.memmap SSD
│   │   └── loaders/                         # Trình cào báo RSS và trình đọc luồng HF
│   └── ann_index/                           # Module Thuật toán & Đánh giá (Thành viên 2)
│       ├── flat.py                          # Thuật toán Flat Exact Search (Ground Truth)
│       ├── hnsw.py                          # Thuật toán Standard HNSW
│       ├── ivf_pq.py & pq.py                # Thuật toán đối chuẩn IVF-PQ
│       ├── quantizer.py                     # Lượng tử hóa vô hướng SQ8 uint8
│       ├── early_exit.py                    # Bộ điều khiển dừng sớm thích ứng
│       ├── two_tier_hnsw.py                 # Thuật toán Two-Tier Quantized HNSW
│       ├── metrics.py                       # Đo lường Recall, Latency, QPS, Memory
│       └── benchmark.py                     # Trình chạy đối chuẩn tự động
├── scripts/                                 # Các script thực thi dòng lệnh
│   ├── crawl_real_data.py                   # Script cào tin tức trực tiếp từ Internet
│   ├── download_and_save_raw_data.py        # Script tải và khởi tạo dữ liệu thô
│   ├── run_baselines_benchmark.py           # Script chạy benchmark 4 thuật toán
│   ├── run_scale_stress_test.py             # Script kiểm thử quy mô 3 mốc dữ liệu
│   ├── search_demo.py                       # Script CLI demo tìm kiếm ngữ nghĩa
│   └── stream_hf_large_scale.py             # Script nạp luồng 10 triệu bản ghi
├── dashboard/                               # Giao diện Web Dashboard Trực quan hóa 3D
│   ├── server.js                            # Express API Server
│   └── public/                              # Three.js 3D Vector Space & HNSW Graph
├── docs/                                    # Báo cáo kỹ thuật chi tiết & LaTeX
│   ├── TECHNICAL_REPORT.md                  # Báo cáo kỹ thuật đối sánh hiệu năng
│   └── thesis_report.tex                    # Bản mẫu báo cáo LaTeX
└── tests/                                   # 71 bài Unit Test tự động (PyTest)
```

---

## 3. HƯỚNG DẪN THIẾT LẬP DỮ LIỆU (DATASET SETUP & DOWNLOAD)

Do kích thước tập dữ liệu lớn (> 20 GB), các tệp nhị phân và dữ liệu thô được loại trừ khỏi Git repository. Bạn có thể thiết lập dữ liệu theo một trong hai cách dưới đây:

### Cách 1: Tải dữ liệu tiền xử lý từ Google Drive (Khuyến nghị)
1. Tải toàn bộ thư mục dữ liệu đã đóng gói sẵn tại:  
   👉 **Google Drive Storage:** [Tải bộ dữ liệu tại đây](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)
2. Giải nén vào thư mục `data/` trong thư mục gốc của dự án theo cấu trúc:
   ```text
   data/
   ├── README.md
   ├── raw/
   ├── processed/
   │   ├── search_index_cache.npz
   │   ├── search_index_metadata.json
   │   ├── pca_3d_projection.json
   │   └── vectors_3d_cache.json
   ├── crawl/
   ├── crawl_wiki/
   ├── quantized/
   ├── quantized_wiki/
   └── quantized_combined/
   ```

### Cách 2: Tự động thu thập và tái tạo dữ liệu từ đầu (Reproducibility Pipeline)
Nếu muốn tự sinh toàn bộ dữ liệu từ Internet và chạy lượng tử hóa:

1. **Thu thập dữ liệu Báo chí & Pháp luật:**
   ```bash
   python scripts/run_crawler.py --target-records 100000 --batch-size 1000
   ```
2. **Thu thập dữ liệu Wikipedia tiếng Việt:**
   ```bash
   python scripts/run_wiki_crawler.py --target-records 100000 --batch-size 1000
   ```
3. **Chạy Lượng tử hóa SQ8 (int8) cho 2 nguồn:**
   ```bash
   python scripts/run_quantization.py
   python scripts/run_wiki_quantization.py
   ```
4. **Hợp nhất hai kho ngữ liệu (Corpus Federation):**
   ```bash
   python scripts/merge_quantized_corpora.py
   ```
5. **Sinh bộ đệm tìm kiếm và tính toán giảm chiều 3D PCA:**
   ```bash
   python dashboard/scripts/build_search_cache.py
   python dashboard/scripts/dimension_reduction_3d.py
   ```

### Cách 3: Đối chuẩn với tập dữ liệu chuẩn quốc tế SIFT10K / SIFT1M
```bash
python scripts/download_standard_datasets.py --dataset sift10k
python scripts/download_standard_datasets.py --dataset sift1m
```

---

## 4. CÀI ĐẶT MÔI TRƯỜNG (INSTALLATION)

```bash
# 1. Clone repository
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# 2. Cài đặt các thư viện Python
pip install numpy pyvi sentence-transformers datasketch beautifulsoup4 pytest python-docx

# 3. Cài đặt các thư viện Dashboard Web 3D
cd dashboard
npm install
cd ..
```

---

## 5. HƯỚNG DẪN CHẠY KIỂM THỬ VÀ THỰC NGHIỆM

### 5.1. Chạy 91 bài kiểm thử tự động (Unit Tests)
```bash
pytest
```

### 5.2. Chạy đối chuẩn 4 thuật toán (Baselines Benchmark)
```bash
python scripts/run_baselines_benchmark.py --num-vectors 1000 --num-queries 50 --dim 64
```

### 5.3. Chạy kiểm thử chịu tải 3 mốc quy mô (Scalability Stress Test)
```bash
python scripts/run_scale_stress_test.py
```

### 5.4. Chạy Trình tìm kiếm Ngữ nghĩa & Gợi ý Bài viết (Semantic Search CLI Demo)
```bash
python scripts/search_demo.py --use-mock-embedder
```

### 5.5. Khởi chạy Giao diện Web Dashboard Trực quan hóa 3D
```bash
cd dashboard
npm start
```
Truy cập trình duyệt: http://localhost:3000

---

## 6. KẾT QUẢ THỰC NGHIỆM TỔNG HỢP

| Thuật toán | Cấu hình | Dung lượng RAM | Thời gian Build | Recall@10 | Latency (p95) | Thông lượng (QPS) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Flat L2 Search** | Float32 Brute-force | 15.4 GB | 0 s | **100.0%** | 450.0 ms | 2.2 |
| **Standard HNSW** | M=16, ef=30 | **46.2 GB** *(OOM)* | 4.2 h | **98.3%** | 2.90 ms | 303.7 |
| **IVF-PQ** | nlist=16, m=8 | **0.08 MB / 2.8 GB** | 1.1 h | **38.2%** | **0.67 ms** | **2,590.9** |
| **Two-Tier HNSW (Đề xuất)** | **SQ8 + Early-Exit + ReRank** | **7.5 GB** *(-84% RAM)* | **2.6 h** | **94.6%** | **1.20 ms** | **820.0** |

