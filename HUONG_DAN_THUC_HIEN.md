# Hướng dẫn Thực hiện — HNSW Combined Quantization

**Phiên bản:** v1.0.0  
**Cập nhật:** Tháng 9, 2026  
**Phạm vi:** Cài đặt, chạy thử, sử dụng dashboard và đánh giá kết quả

---

## Mục lục

1. [Yêu cầu Phần cứng & Phần mềm](#1-yêu-cầu-phần-cứng--phần-mềm)
2. [Tải Dữ liệu (Bắt buộc)](#2-tải-dữ-liệu-bắt-buộc)
3. [Cài đặt Dự án](#3-cài-đặt-dự-án)
4. [Chạy Dashboard Trực quan](#4-chạy-dashboard-trực-quan)
5. [Hướng dẫn Sử dụng Từng Tab](#5-hướng-dẫn-sử-dụng-từng-tab)
6. [Chạy Đánh giá Thuật toán](#6-chạy-đánh-giá-thuật-toán)
7. [Chạy Pipeline Từ Đầu](#7-chạy-pipeline-từ-đầu)
8. [Cấu hình Siêu tham số](#8-cấu-hình-siêu-tham-số)
9. [Chạy Bộ Kiểm thử](#9-chạy-bộ-kiểm-thử)
10. [API Reference](#10-api-reference)
11. [Xử lý Sự cố Thường gặp](#11-xử-lý-sự-cố-thường-gặp)

---

## 1. Yêu cầu Phần cứng & Phần mềm

### Tối thiểu

| Thành phần | Yêu cầu |
|:---|:---|
| RAM | 16 GB (đủ chạy Two-Tier HNSW) |
| Storage | 15 GB NVMe SSD trống (cho index SQ8) |
| CPU | x86_64 với AVX2 |
| Python | 3.11 hoặc cao hơn |
| Node.js | 20 hoặc cao hơn |

### Khuyến nghị

| Thành phần | Khuyến nghị |
|:---|:---|
| RAM | 32 GB+ |
| Storage | 50 GB+ SSD (cho dữ liệu float32 + SQ8 + cache) |
| CPU | Hỗ trợ AVX-512 cho hiệu suất SIMD tốt hơn |

> **Lưu ý:** Standard HNSW trên 16.45M vector cần ~64 GB RAM. Chỉ Two-Tier Quantized HNSW mới chạy được trên máy 16-32 GB.

---

## 2. Tải Dữ liệu (Bắt buộc)

Do giới hạn về dung lượng của GitHub, dữ liệu không được đính kèm trong mã nguồn. Bạn cần tải dữ liệu và đặt đúng vào thư mục `data/`.

👉 **Link tải trọn bộ dữ liệu (Google Drive):**  
[https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

**Cách bố trí thư mục dữ liệu sau khi tải:**
```text
HNSW-Combined-Quantization/
├── data/
│   ├── processed/
│   │   ├── search_index_cache.npz          # 5,000 vector đã chuẩn hóa
│   │   ├── search_index_metadata.json      # Metadata 5,000 tài liệu
│   │   ├── pca_3d_projection.json          # Tọa độ PCA 3D
│   │   └── vectors_3d_cache.json           # Cache đồ thị 3D cho Dashboard
│   ├── raw/
│   │   ├── raw_crawled_news.jsonl          # Dữ liệu văn bản thô
│   │   └── RAW_DATASET_MANIFEST.json
```
*(Chi tiết thêm vui lòng xem file `data/README.md`)*

---

## 3. Cài đặt Dự án

### Bước 1 — Clone và môi trường

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# Tạo virtual environment
python -m venv .venv

# Kích hoạt (Windows)
.venv\Scripts\activate
# Kích hoạt (Linux/macOS)
source .venv/bin/activate
```

### Bước 2 — Cài đặt thư viện Python

```bash
# Cài đặt cơ bản
pip install -e .

# Cài đặt thêm ML + dev tools
pip install -e ".[ml,dev]"
```

### Bước 3 — Cài đặt Node.js cho Dashboard

```bash
cd dashboard
npm install
cd ..
```

### Bước 4 — Kiểm tra cài đặt

```bash
python -c "import numpy, sentence_transformers; print('Python OK')"
node -e "console.log('Node OK')"
```

---

## 4. Chạy Dashboard Trực quan

Hãy chắc chắn rằng bạn đã làm bước **2. Tải Dữ liệu** và đặt chúng vào thư mục `data/processed/`.

### Khởi động Server

```bash
# Mở terminal 1 — Python search microservice
cd dashboard
python scripts/search_service.py
# Service chạy trên port 5005

# Mở terminal 2 — Node.js dashboard server
cd dashboard
npm start
# Server chạy trên port 3000
```

Mở trình duyệt, truy cập: **http://localhost:3000**

---

## 5. Hướng dẫn Sử dụng Từng Tab

### Tab 1 — Tìm kiếm & Execution Inspector

**Mục đích:** Nhập câu truy vấn ngữ nghĩa và xem kết quả tìm kiếm cùng với biểu đồ thực thi 4 giai đoạn.

**Cách sử dụng:**

1. Nhập văn bản vào ô tìm kiếm (ví dụ: `hợp đồng lao động tối thiểu`).
2. Chọn thuật toán: `Two-Tier Quantized HNSW`, `Standard HNSW` hoặc `Distributed Collaborative Filtering`.
3. Chỉnh Top-K slider (5-20 kết quả).
4. Chọn chip danh mục nếu muốn lọc.
5. Nhấn **Tìm kiếm** hoặc Enter.

**Giải thích kết quả hiển thị:**

| Phần | Mô tả |
|:---|:---|
| 4 KPI cards | Elapsed time, Slot time, Bytes shuffled, Bytes spilled |
| S00 — Input | Thời gian chuẩn hóa và nhúng vector |
| S01 — Aggregate | Thời gian duyệt đồ thị SQ8 qua 200 shards |
| S02 — Re-rank | Thời gian đọc SSD và tính lại khoảng cách float32 |
| S03 — Output | Tổng kết quả và thời gian phát sinh response |
| Graph Output | Danh sách kết quả (List view / JSON view) |

**Chuyển đổi dạng xem kết quả:**

- Nhấn `[Dạng Danh Sách]` để xem thẻ card.
- Nhấn `[Dạng JSON]` để xem raw JSON.
- Nhấn `Copy JSON` để sao chép vào clipboard.

**Dynamic SQL:** Phần SQL dưới thanh tìm kiếm tự động cập nhật khi đổi tham số — đây là SQL mô phỏng logic truy vấn động.

---

### Tab 2 — Không gian Vector 3D (Three.js)

**Mục đích:** Trực quan hóa không gian vector nhúng 384-D được chiếu xuống 3 chiều qua PCA.

**Cách sử dụng:**

1. Thực hiện tìm kiếm ở Tab 1 trước.
2. Chuyển sang Tab 2.
3. Các điểm kết quả tìm kiếm được tô màu vàng/đỏ, các điểm nền màu xanh.
4. Di chuột lên điểm bất kỳ để xem tooltip (tiêu đề, danh mục, score, lý do).
5. Nhấn **Xem trên 3D** trên một kết quả để focus vào điểm đó.
6. Panel **HUD Detail** hiển thị đầy đủ thông tin tài liệu được chọn.

**Điều hướng:**
- Kéo chuột để xoay
- Scroll để phóng to/thu nhỏ
- Click phải + kéo để dịch chuyển

---

### Tab 3 — Danh sách Top-K

**Mục đích:** Xem bảng kết quả tìm kiếm đầy đủ với xếp hạng rõ ràng.

**Nội dung hiển thị:**
- Thứ tự xếp hạng (Rank #1 = độ tương đồng cao nhất)
- Độ tương đồng (Similarity Score, thang 0-1)
- Tiêu đề tài liệu
- Đoạn trích dẫn văn bản
- Danh mục (News / Legal)
- Lý do xếp hạng (Reasoning badge)

**Lưu ý:** Kết quả được sắp xếp giảm dần theo `similarity_score`.

---

### Tab 4 — Đánh giá Thuật toán

**Mục đích:** So sánh Two-Tier Quantized HNSW vs Standard HNSW trên các chỉ số QPS, Recall, Latency.

**Cách sử dụng:**

1. Nhấn **Chạy Đánh giá**.
2. Hệ thống chạy 100 câu truy vấn mẫu trên cả 2 thuật toán.
3. Biểu đồ QPS, Latency, Recall hiển thị so sánh trực tiếp.
4. Biểu đồ HNSW Siêu tham số cho phép thay đổi `M`, `ef_construction`, `ef_search` để xem ảnh hưởng.

---

## 6. Chạy Đánh giá Thuật toán bằng CLI

Ngoài việc dùng Dashboard, bạn có thể chạy bằng dòng lệnh:

```bash
# Chạy đánh giá truy xuất trên 2 thuật toán
python scripts/run_retrieval_evaluation.py --top-k 10

# Kết quả lưu tại:
#   data/processed/evaluation_results/benchmark_report_YYYYMMDD_HHMMSS.json
#   data/processed/evaluation_results/benchmark_summary_YYYYMMDD_HHMMSS.md
```

### Scale Stress Test (Chịu tải)

```bash
# Kiểm tra hiệu suất theo quy mô N = 1000, 2500, 5000
python scripts/run_scale_stress_test.py
```

---

## 7. Chạy Pipeline Từ Đầu

Chỉ thực hiện khi bạn muốn làm lại toàn bộ quá trình thu thập và lượng tử hóa:

```bash
# 1. Thu thập dữ liệu báo chí & pháp luật
python scripts/run_crawler.py --target-records 100000 --batch-size 1000

# 2. Lượng tử hóa SQ8
python scripts/run_quantization.py

# 3. Xây dựng bộ đệm tìm kiếm cho Dashboard
python scripts/build_clean_search_cache.py
```

---

## 8. Cấu hình Siêu tham số

File cấu hình: `configs/default_pipeline.json`

| Tham số | Kiểu | Mặc định | Mô tả |
|:---|:---|:---:|:---|
| `dim` | int | 384 | Số chiều vector (chuẩn Sentence-BERT) |
| `max_elements` | int | 10,000,000 | Dung lượng tối đa mỗi phân vùng index |
| `M` | int | 16 | Số liên kết tối đa mỗi node trong HNSW |
| `ef_construction` | int | 100 | Kích thước hàng đợi ứng viên khi xây graph |
| `ef_search` | int | 32 | Kích thước hàng đợi ứng viên khi truy vấn |
| `tau` | int | 3 | Số bước bão hòa dừng sớm (Adaptive Early-Exit) |
| `eps` | float | 0.0001 | Ngưỡng cải thiện tương đối để dừng sớm |
| `rerank_factor` | int | 3 | Hệ số nhân số lượng ứng viên Tier 2 |

---

## 9. Chạy Bộ Kiểm thử

### Kiểm thử Backend Python

```bash
# Chạy toàn bộ 91 bài kiểm thử pytest
pytest tests/ -v
```

### Kiểm thử Frontend UI

```bash
# Kiểm thử render và logic UI (Node.js)
node tests/test_ui_render_harness.js
# Kết quả: 19 passed, 0 failed

# Kiểm thử adversarial stress
node tests/test_adversarial_frontend_stress.js
# Kết quả: 3 adversarial cases, 0 findings
```

---

## 10. API Reference

Server Express của Dashboard chạy trên port 3000.

| Endpoint | Method | Body / Params | Chức năng |
|:---|:---|:---|:---|
| `GET /api/status` | GET | — | Trạng thái index, RAM usage, số bản ghi |
| `POST /api/search` | POST | `{ query, algorithm, top_k, category }` | Thực thi tìm kiếm ngữ nghĩa |
| `POST /api/eval/run` | POST | `{ top_k }` | Chạy benchmark 2 thuật toán |
| `GET /api/eval/history` | GET | — | Danh sách các báo cáo benchmark đã chạy |
| `GET /api/eval/download/:type/:file` | GET | type=report/query, file=filename | Tải JSON/Markdown report |

### Ví dụ gọi API tìm kiếm

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hợp đồng lao động tối thiểu", "algorithm": "two_tier", "top_k": 5}'
```

---

## 11. Xử lý Sự cố Thường gặp

### Lỗi kết nối `Python service not responding`

**Nguyên nhân:** Python microservice (port 5005) chưa chạy.

**Cách xử lý:**
```bash
cd dashboard
python scripts/search_service.py
```

---

### Lỗi `Cannot find module` khi chạy Node

**Nguyên nhân:** Bạn chưa cài đặt package cho thư mục dashboard.

**Cách xử lý:**
```bash
cd dashboard
npm install
```

---

### Lỗi `ModuleNotFoundError` trong Python

**Cách xử lý:** Đảm bảo bạn đã cài toàn bộ môi trường ảo.
```bash
pip install -e ".[ml,dev]"
```

---

### Biểu đồ 3D không hiển thị

**Nguyên nhân:** Trình duyệt không hỗ trợ WebGL hoặc GPU bị vô hiệu hóa.

**Cách xử lý:**
- Thử trình duyệt khác (Chrome/Edge phiên bản mới nhất).
- Bật `Override software rendering list` trong `chrome://flags`.

---

### Out-Of-Memory khi chạy Standard HNSW

**Đây là điều bình thường** với tập 16.45M vector. Standard HNSW cần tới ~64 GB RAM. Hãy chuyển sang sử dụng `Two-Tier Quantized HNSW` để tiết kiệm 75% RAM.
