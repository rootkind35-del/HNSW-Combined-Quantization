> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# Hướng dẫn Thực hiện — HNSW Combined Quantization

**Phiên bản:** v1.0.0  
**Cáºp nháºt:** Tháng 9, 2026  
**Phạm vi:** CÃ i đặt, chạy thá», sá» dụng dashboard vÃ  đánh giá kết quả

---

## Mục lục

1. [Yêu cầu Phần cứng & Phần mềm](#1-yêu-cầu-phần-cứng--phần-mềm)
2. [Tải Dữ liệu (Bắt buộc)](#2-tải-dữ-liệu-bắt-buộc)
3. [CÃ i đặt Dự Ã¡n](#3-cÃ i-đặt-dự-án)
4. [Chạy Dashboard Trực quan](#4-chạy-dashboard-trực-quan)
5. [Hướng dẫn Sá» dụng Từng Tab](#5-hÆ°á»›ng-dáº«n-sá»-dá»¥ng-tá»«ng-tab)
6. [Chạy Đánh giá Thuáºt toÃ¡n](#6-cháº¡y-Ä‘Ã¡nh-giÃ¡-thuáºt-toÃ¡n)
7. [Chạy Pipeline Từ Đầu](#7-chạy-pipeline-từ-đầu)
8. [Cấu hình Siêu tham số](#8-cấu-hình-siêu-tham-số)
9. [Chạy Bộ Kiểm thá»](#9-cháº¡y-bá»™-kiá»ƒm-thá»)
10. [API Reference](#10-api-reference)
11. [Xá» lý Sự cố Thường gáº·p](#11-xá»-lÃ½-sá»±-cá»‘-thÆ°á»ng-gáº·p)

---

## 1. Yêu cầu Phần cứng & Phần mềm

### Tối thiểu

| ThÃ nh phần | Yêu cầu |
|:---|:---|
| RAM | 16 GB (đủ chạy Two-Tier HNSW) |
| Storage | 15 GB NVMe SSD trống (cho index SQ8) |
| CPU | x86_64 với AVX2 |
| Python | 3.11 hoặc cao hơn |
| Node.js | 20 hoặc cao hơn |

### Khuyến nghị

| ThÃ nh phần | Khuyến nghị |
|:---|:---|
| RAM | 32 GB+ |
| Storage | 50 GB+ SSD (cho dữ liệu float32 + SQ8 + cache) |
| CPU | Hỗ trợ AVX-512 cho hiệu suất SIMD tốt hơn |

> **Lưu ý:** Standard HNSW trên 16.45M vector cần ~64 GB RAM. Chỉ Two-Tier Quantized HNSW mới chạy được trên máy 16-32 GB.

---

## 2. Tải Dữ liệu (Bắt buộc)

Do giới hạn về dung lượng của GitHub, dữ liệu không được Ä‘Ãnh kèm trong mã nguồn. Bạn cần tải dữ liệu vÃ  đặt đúng vÃ o thư mục `data/`.

👉 **Link tải trọn bộ dữ liệu (Google Drive):**  
[https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

**Cách bố trÃ thư mục dữ liệu sau khi tải:**
```text
HNSW-Combined-Quantization/
├── data/
│   ├── processed/
│   │   ├── search_index_cache.npz          # 5,000 vector đã chuẩn hóa
│   │   ├── search_index_metadata.json      # Metadata 5,000 tÃ i liệu
│   │   ├── pca_3d_projection.json          # Tọa độ PCA 3D
│   │   └── vectors_3d_cache.json           # Cache đồ thị 3D cho Dashboard
│   ├── raw/
│   │   ├── raw_crawled_news.jsonl          # Dữ liệu văn bản thô
│   │   └── RAW_DATASET_MANIFEST.json
```
*(Chi tiết thêm vui lòng xem file `data/README.md`)*

---

## 3. CÃ i đặt Dự án

### Bước 1 — Clone vÃ  môi trường

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# Tạo virtual environment
python -m venv.venv

# KÃch hoạt (Windows)
.venv\Scripts\activate
# KÃch hoạt (Linux/macOS)
source.venv/bin/activate
```

### Bước 2 — CÃ i đặt thư viện Python

```bash
# CÃ i đặt cơ bản
pip install -e.

# CÃ i đặt thêm ML + dev tools
pip install -e ".[ml,dev]"
```

### Bước 3 — CÃ i đặt Node.js cho Dashboard

```bash
cd dashboard
npm install
cd..
```

### Bước 4 — Kiểm tra cÃ i đặt

```bash
python -c "import numpy, sentence_transformers; print('Python OK')"
node -e "console.log('Node OK')"
```

---

## 4. Chạy Dashboard Trực quan

Hãy chắc chắn rằng bạn đã lÃ m bước **2. Tải Dữ liệu** vÃ  đặt chúng vÃ o thư mục `data/processed/`.

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

Mở trình duyệt, truy cáºp: **http://localhost:3000**

---

## 5. Hướng dẫn Sá» dụng Từng Tab

### Tab 1 — Tìm kiếm & Execution Inspector

**Mục Ä‘Ãch:** Nháºp câu truy vấn ngữ nghĩa vÃ  xem kết quả tìm kiếm cùng với biểu đồ thực thi 4 giai đoạn.

**Cách sá» dụng:**

1. Nháºp văn bản vÃ o ô tìm kiếm (vÃ dụ: `hợp đồng lao động tối thiểu`).
2. Chọn thuáºt toán: `Two-Tier Quantized HNSW`, `Standard HNSW` hoặc `Distributed Collaborative Filtering`.
3. Chỉnh Top-K slider (5-20 kết quả).
4. Chọn chip danh mục nếu muốn lọc.
5. Nhấn **Tìm kiếm** hoặc Enter.

**Giải thÃch kết quả hiển thị:**

| Phần | Mô tả |
|:---|:---|
| 4 KPI cards | Elapsed time, Slot time, Bytes shuffled, Bytes spilled |
| S00 — Input | Thời gian chuẩn hóa vÃ  nhúng vector |
| S01 — Aggregate | Thời gian duyệt đồ thị SQ8 qua 200 shards |
| S02 — Re-rank | Thời gian đọc SSD vÃ  tÃnh lại khoảng cách float32 |
| S03 — Output | Tổng kết quả vÃ  thời gian phát sinh response |
| Graph Output | Danh sách kết quả (List view / JSON view) |

**Chuyển đổi dạng xem kết quả:**

- Nhấn `[Dạng Danh Sách]` để xem thẻ card.
- Nhấn `[Dạng JSON]` để xem raw JSON.
- Nhấn `Copy JSON` để sao chép vÃ o clipboard.

**Dynamic SQL:** Phần SQL dưới thanh tìm kiếm tự động cáºp nháºt khi đổi tham số — đây lÃ  SQL mô phỏng logic truy vấn động.

---

### Tab 2 — Không gian Vector 3D (Three.js)

**Mục Ä‘Ãch:** Trực quan hóa không gian vector nhúng 384-D được chiếu xuống 3 chiều qua PCA.

**Cách sá» dụng:**

1. Thực hiện tìm kiếm ở Tab 1 trước.
2. Chuyển sang Tab 2.
3. Các điểm kết quả tìm kiếm được tô mÃ u vÃ ng/đỏ, các điểm nền mÃ u xanh.
4. Di chuột lên điểm bất kỳ để xem tooltip (tiêu đề, danh mục, score, lý do).
5. Nhấn **Xem trên 3D** trên một kết quả để focus vÃ o điểm đó.
6. Panel **HUD Detail** hiển thị đầy đủ thông tin tÃ i liệu được chọn.

**Điều hướng:**
- Kéo chuột để xoay
- Scroll để phóng to/thu nhỏ
- Click phải + kéo để dịch chuyển

---

### Tab 3 — Danh sách Top-K

**Mục Ä‘Ãch:** Xem bảng kết quả tìm kiếm đầy đủ với xếp hạng rõ rÃ ng.

**Nội dung hiển thị:**
- Thứ tự xếp hạng (Rank #1 = độ tương đồng cao nhất)
- Độ tương đồng (Similarity Score, thang 0-1)
- Tiêu đề tÃ i liệu
- Đoạn trÃch dẫn văn bản
- Danh mục (News / Legal)
- Lý do xếp hạng (Reasoning badge)

**Lưu ý:** Kết quả được sắp xếp giảm dần theo `similarity_score`.

---

### Tab 4 — Đánh giá Thuáºt toán

**Mục Ä‘Ãch:** So sánh Two-Tier Quantized HNSW vs Standard HNSW trên các chỉ số QPS, Recall, Latency.

**Cách sá» dụng:**

1. Nhấn **Chạy Đánh giá**.
2. Hệ thống chạy 100 câu truy vấn mẫu trên cả 2 thuáºt toán.
3. Biểu đồ QPS, Latency, Recall hiển thị so sánh trực tiếp.
4. Biểu đồ HNSW Siêu tham số cho phép thay đổi `M`, `ef_construction`, `ef_search` để xem ảnh hưởng.

---

## 6. Chạy Đánh giá Thuáºt toán bằng CLI

NgoÃ i việc dùng Dashboard, bạn có thể chạy bằng dòng lệnh:

```bash
# Chạy đánh giá truy xuất trên 2 thuáºt toán
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

Chỉ thực hiện khi bạn muốn lÃ m lại toÃ n bộ quá trình thu tháºp vÃ  lượng tá» hóa:

```bash
# 1. Thu tháºp dữ liệu báo chÃ & pháp luáºt
python scripts/run_crawler.py --target-records 100000 --batch-size 1000

# 2. Lượng tá» hóa SQ8
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
| `ef_construction` | int | 100 | KÃch thước hÃ ng đợi ứng viên khi xây graph |
| `ef_search` | int | 32 | KÃch thước hÃ ng đợi ứng viên khi truy vấn |
| `tau` | int | 3 | Số bước bão hòa dừng sớm (Adaptive Early-Exit) |
| `eps` | float | 0.0001 | Ngưỡng cải thiện tương đối để dừng sớm |
| `rerank_factor` | int | 3 | Hệ số nhân số lượng ứng viên Tier 2 |

---

## 9. Chạy Bộ Kiểm thá»

### Kiểm thá» Backend Python

```bash
# Chạy toÃ n bộ 91 bÃ i kiểm thá» pytest
pytest tests/ -v
```

### Kiểm thá» Frontend UI

```bash
# Kiểm thá» render vÃ  logic UI (Node.js)
node tests/test_ui_render_harness.js
# Kết quả: 19 passed, 0 failed

# Kiểm thá» adversarial stress
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
| `POST /api/eval/run` | POST | `{ top_k }` | Chạy benchmark 2 thuáºt toán |
| `GET /api/eval/history` | GET | — | Danh sách các báo cáo benchmark đã chạy |
| `GET /api/eval/download/:type/:file` | GET | type=report/query, file=filename | Tải JSON/Markdown report |

### VÃ dụ gọi API tìm kiếm

```bash
curl -X POST http://localhost:3000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "hợp đồng lao động tối thiểu", "algorithm": "two_tier", "top_k": 5}'
```

---

## 11. Xá» lý Sự cố Thường gặp

### Lỗi kết nối `Python service not responding`

**Nguyên nhân:** Python microservice (port 5005) chưa chạy.

**Cách xá» lý:**
```bash
cd dashboard
python scripts/search_service.py
```

---

### Lỗi `Cannot find module` khi chạy Node

**Nguyên nhân:** Bạn chưa cÃ i đặt package cho thư mục dashboard.

**Cách xá» lý:**
```bash
cd dashboard
npm install
```

---

### Lỗi `ModuleNotFoundError` trong Python

**Cách xá» lý:** Đảm bảo bạn đã cÃ i toÃ n bộ môi trường ảo.
```bash
pip install -e ".[ml,dev]"
```

---

### Biểu đồ 3D không hiển thị

**Nguyên nhân:** Trình duyệt không hỗ trợ WebGL hoặc GPU bị vô hiệu hóa.

**Cách xá» lý:**
- Thá» trình duyệt khác (Chrome/Edge phiên bản mới nhất).
- Báºt `Override software rendering list` trong `chrome://flags`.

---

### Out-Of-Memory khi chạy Standard HNSW

**Đây lÃ  điều bình thường** với táºp 16.45M vector. Standard HNSW cần tới ~64 GB RAM. Hãy chuyển sang sá» dụng `Two-Tier Quantized HNSW` để tiết kiệm 75% RAM.

