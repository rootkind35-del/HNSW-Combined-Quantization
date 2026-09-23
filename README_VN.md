<div align="center">

# HNSW Combined Quantization: Tìm kiếm Vector Dữ liệu Lớn theo Hai Tầng

<p align="center">
  <b>Tìm kiếm lân cận gần nhất (ANN) trên bộ nhớ ngoài với thông lượng cao cho 16.45 triệu vector dày đặc (384-D) trên phần cứng máy tính phổ thông.</b>
</p>

<p align="center">
  <a href="#-benchmarks--empirical-results"><img alt="Quy mô Corpus" src="https://img.shields.io/badge/Quy%20m%C3%B4-16.45M%20Vectors-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-system-architecture"><img alt="Giảm RAM" src="https://img.shields.io/badge/Ti%E1%BA%BFt%20ki%E1%BB%87m%20RAM--75%25-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-interactive-dashboard"><img alt="Dashboard" src="https://img.shields.io/badge/Dashboard-Port%203000-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>
</p>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![PyTest Suite](https://img.shields.io/badge/Tests-91%20Passed-brightgreen?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](LICENSE)

<p align="center">
  <a href="README.md"><img alt="English" height="40" src="https://img.shields.io/badge/English-CDCFD4"></a>&nbsp;
  <a href="README_VN.md"><img alt="Tiếng Việt" height="40" src="https://img.shields.io/badge/Tiếng_Việt-BCDCF7"></a>
</p>

[Tính năng](#-tính-năng-chính) · [Cài đặt](#-bắt-đầu) · [Khám phá](#-khám-phá-dự-án) · [Đánh giá](#%EF%B8%8F-cli--công-cụ-đánh-giá) · [Cộng đồng](#-cộng-đồng)

</div>

---

> 🤝 **Chúng tôi hoan nghênh mọi đóng góp!** Xem [Hướng dẫn Đóng góp](CONTRIBUTING.md) và gửi Pull Request của bạn trên GitHub.

---

### 📦 Phát hành

> **[2026.09]** [v1.0.0](https://github.com/rootkind35-del/HNSW-Combined-Quantization/releases/tag/v1.0.0) — Phiên bản chính thức hoàn thiện luồng xử lý 16.45M ngữ liệu Báo chí & Pháp luật, chỉ mục Two-Tier Quantized HNSW với Adaptive Early-Exit, và bảng điều khiển 3D Three.js.

---

## ✨ Tính năng Chính

HNSW Combined Quantization giải quyết điểm nghẽn cốt lõi giữa giới hạn bộ nhớ RAM, độ trễ truy vấn và độ chính xác (recall) trong tìm kiếm vector không gian chiều cao trên các máy tính phổ thông.

- **Kiến trúc Tách biệt Bộ nhớ-Ổ đĩa (Two-Tier)** — Tầng 1 duyệt đồ thị HNSW nén vô hướng (SQ8 int8) trên RAM giúp tiết kiệm 75% bộ nhớ, trong khi Tầng 2 truy cập trực tiếp các vector float32 nguyên bản từ ổ cứng NVMe SSD qua cơ chế zero-copy `numpy.memmap` để tái xếp hạng chính xác.
- **Hội tụ Dừng sớm Thích ứng (Adaptive Early-Exit)** — Theo dõi delta khoảng cách tương đối với bộ đếm bão hòa ($\tau=3$) và dung sai ($\epsilon=10^{-4}$), ngắt tìm kiếm đồ thị ngay khi chất lượng kết quả không còn cải thiện.
- **Luồng Xử lý Dữ liệu Lớn Streaming** — Tiêu hóa hàng chục gigabyte văn bản qua 400 phân vùng với mức RAM cố định (< 150 MB) nhờ dùng MinHash LSH lọc trùng, PyVi tách từ ghép, và cơ chế lưu tự động (checkpointing).
- **Giao diện Kép & Công cụ Đánh giá** — Cung cấp bảng điều khiển không gian vector 3D WebGL trực quan, song song với công cụ CLI tự động đo lường QPS, phần trăm độ trễ, và Recall@K so với tìm kiếm vét cạn (brute-force exact search).

---

## 🚀 Bắt đầu

Dự án tách biệt API thực thi backend khỏi giao diện hiển thị frontend. Dữ liệu được lưu trong `data/`, và mọi cấu hình đánh giá nằm trong `configs/`.

### Yêu cầu hệ thống

- **Python**: Phiên bản 3.11 trở lên
- **Node.js**: Phiên bản 20 trở lên
- **Lưu trữ**: Ít nhất 15 GB SSD NVMe trống cho tệp chỉ mục lượng tử hóa

<details open>
<summary><b>Lựa chọn 1 — Cài đặt từ Mã nguồn (Từ Source)</b> · Khuyên dùng</summary>

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

python -m venv .venv
source .venv/bin/activate # Hoặc .venv\Scripts\activate trên Windows

pip install -e .
pip install -e ".[ml,dev]"
```

Khởi động các dịch vụ:

```bash
# Terminal 1: Python Search Microservice
cd dashboard
python scripts/search_service.py

# Terminal 2: Node.js Dashboard UI
cd dashboard
npm install
npm start
```

Mở [http://localhost:3000](http://localhost:3000) trên trình duyệt.

</details>

<details>
<summary><b>Lựa chọn 2 — Tải Dữ liệu Tiền xử lý (Google Drive)</b></summary>

Để bỏ qua bước thu thập 16.45 triệu bản ghi:

1. Tải các tệp dữ liệu đã được nén từ Google Drive:
   👉 [Tải Dữ liệu Dựng sẵn](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)
2. Giải nén vào thư mục `data/processed/`.
3. Kiểm tra tính toàn vẹn của dữ liệu:
   ```bash
   python -c "import json; d=json.load(open('data/processed/search_index_metadata.json', encoding='utf-8')); print(f'Đã tải {len(d)} bản ghi')"
   ```

</details>

<details>
<summary><b>Tham chiếu Cấu hình</b> — <code>configs/default_pipeline.json</code></summary>

| Tham số | Kiểu | Mặc định | Mô tả |
|:---|:---|:---|:---|
| `dim` | integer | `384` | Số chiều vector (chuẩn Sentence-BERT) |
| `max_elements` | integer | `10000000` | Sức chứa tối đa mỗi index |
| `M` | integer | `16` | Liên kết tối đa mỗi node trong HNSW |
| `ef_construction` | integer | `100` | Kích thước hàng đợi khi xây dựng đồ thị |
| `ef_search` | integer | `32` | Kích thước hàng đợi khi duyệt truy vấn |
| `tau` | integer | `3` | Số bước bão hòa dừng sớm |
| `eps` | float | `0.0001` | Ngưỡng cải thiện tương đối để dừng sớm |

</details>

---

## 📖 Khám phá Dự án

### 📊 Đặc điểm Dữ liệu Lớn

| Khía cạnh | Chỉ số Thiết kế | Cơ chế Thực hiện |
|:---|:---|:---|
| **Volume (Khối lượng)** | **16,459,486 vector dày đặc** (384-D)<br>• Văn bản Báo chí & Pháp luật<br>• 24.11 GB raw float32 | Lượng tử hóa SQ8 int8 giảm còn **6.02 GB**. Map vào SSD giúp RAM hoạt động luôn dưới **8.1 GB**, chạy mượt trên PC 16 GB. |
| **Velocity (Tốc độ)** | **400 phân vùng** xử lý streaming<br>• Độ trễ truy vấn $p_{50} = 1.25$ ms<br>• Thông lượng 1,250 QPS | Xử lý hàng loạt (10K vector/lô) với checkpointing nguyên tử, tự động ghi lên ổ cứng. |
| **Veracity (Chính xác)** | Độ chuẩn xác tìm kiếm cao<br>• Recall@10 = **95.4%** | Tái xếp hạng bằng vector float32 (Tier 2) bù lấp mọi sai số của lượng tử hóa Tầng 1. |

### 📈 Kết quả Đánh giá (Benchmarks)

Thực nghiệm đo trên máy trạm thông thường (Microsoft Windows 11 64-bit, x86_64 AVX2, NVMe SSD).

| Thuật toán | Cơ chế Lưu trữ | Sử dụng RAM | Recall@10 | Độ trễ Trung bình | Thông lượng (QPS) | Khả năng Khả thi |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **Standard HNSW** | Đồ thị RAM + float32 | 64.20 GB | 98.3% | 2.90 ms | 303.7 | OOM (Tràn RAM) trên máy 16GB/32GB |
| **Two-Tier Quantized HNSW** | **Đồ thị SQ8 + SSD Memmap** | **8.10 GB** | **95.4%** | **1.25 ms** | **1,250.0** | **Chạy tốt trên máy 16GB** |
| **Distributed CF** | **Sharded Dot-Product (MIPS)** | **Tùy biến** | **Tương đương** | **Phân tán** | **Cao** | **Mở rộng dễ dàng qua Shards** |

### 🖥️ Bảng Điều khiển Trực quan (Dashboard)

Giao diện web Full-stack phát triển bằng Express, Three.js và Tailwind CSS.

```text
Các Tab của Dashboard:
├── Tab 1: Tìm kiếm & BigQuery Execution Inspector
│           Tìm kiếm thời gian thực, 4 thẻ KPI (Elapsed/Slot/Bytes),
│           Biểu đồ thực thi 4 giai đoạn, Dynamic SQL,
│           Xem dạng Danh sách/JSON.
├── Tab 2: Không gian Vector 3D (Three.js WebGL)
│           Đám mây điểm PCA 3D, quỹ đạo bước nhảy HNSW,
│           Bảng thông tin HUD kèm lý do xếp hạng.
├── Tab 3: Danh sách Tài liệu Top-K
│           Bảng kết quả sắp xếp theo độ tương đồng,
│           Lý do tương đồng cho từng kết quả.
└── Tab 4: Đánh giá Thuật toán
            Biểu đồ so sánh Two-Tier Quantized HNSW vs Standard HNSW,
            Điều chỉnh Siêu tham số HNSW trực tiếp.
```

---

## ⌨ CLI — Công cụ Đánh giá

Kho lưu trữ cung cấp các tiện ích dòng lệnh để chạy truy vấn, benchmark và sinh báo cáo tự động.

<details open>
<summary><b>Công cụ Đánh giá Truy xuất Tự động</b></summary>

Chạy các câu truy vấn mẫu qua 2 thuật toán, tính toán phần trăm độ trễ, QPS, và Recall@K, xuất báo cáo ra JSON/Markdown:

```bash
python scripts/run_retrieval_evaluation.py --top-k 5
```

</details>

<details>
<summary><b>Tìm kiếm Ngữ nghĩa qua CLI</b></summary>

```bash
# Truy vấn index bằng mô hình nhúng
python scripts/search_demo.py --use-mock-embedder
```

</details>

<details>
<summary><b>Kiểm tra Chịu tải theo Quy mô (Stress Test)</b></summary>

```bash
# Đánh giá hiệu năng với N thay đổi (1,000 -> 2,500 -> 5,000)
python scripts/run_scale_stress_test.py
```

</details>

---

## 📁 Cấu trúc Mã nguồn

```text
HNSW-Combined-Quantization/
├── README.md                                # Tổng quan dự án (Tiếng Anh)
├── README_VN.md                             # Tổng quan dự án (Tiếng Việt)
├── KET_QUA_THUC_HIEN.md                     # Báo cáo thực nghiệm đầy đủ
├── HUONG_DAN_THUC_HIEN.md                   # Hướng dẫn cài đặt & sử dụng
├── configs/
│   └── default_pipeline.json                # Siêu tham số đường ống
├── src/
│   ├── ann_data/                            # Lớp tiếp nhận & lưu trữ Dữ liệu lớn
│   └── ann_index/                           # Lõi thuật toán đánh chỉ mục
│       ├── hnsw.py                          # Đồ thị HNSW tiêu chuẩn
│       ├── quantizer.py                     # Lượng tử hóa vô hướng (SQ8 int8)
│       ├── early_exit.py                    # Trình điều khiển Dừng sớm Thích ứng
│       └── two_tier_hnsw.py                 # Thuật toán Two-Tier Quantized HNSW
├── scripts/                                 # Các tập lệnh CLI
│   └── run_retrieval_evaluation.py          # Đánh giá truy xuất (Benchmark)
├── dashboard/                               # Bảng điều khiển Web tương tác
│   ├── server.js                            # Express API backend (cổng 3000)
│   ├── scripts/search_service.py            # Python search microservice (cổng 5005)
│   └── public/                              # HTML5, Tailwind CSS, Three.js 3D
├── docs/                                    # Tài liệu kỹ thuật
│   └── TECHNICAL_REPORT.md                  # Báo cáo phương pháp & kỹ thuật
└── tests/                                   # Kịch bản kiểm thử (Tests)
```

---

## 🌐 Cộng đồng

### 🙏 Lời Cảm ơn

Bản triển khai này sử dụng các khái niệm và thành phần từ:

- **Malkov & Yashunin (2018)**: *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs*
- **Jégou et al. (2011)**: *Product Quantization for Nearest Neighbor Search* (IEEE TPAMI)
- **HKUDS / DeepTutor**: Benchmark cấu trúc và bố cục trực quan cho tài liệu kỹ thuật mã nguồn mở.
- **PyVi**: Thư viện tách từ vựng tiếng Việt.

<div align="center">

Cấp phép theo giấy phép [Apache License 2.0](LICENSE).

<p>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=rootkind35-del.HNSW-Combined-Quantization&style=for-the-badge&color=00d4ff" alt="Views">
</p>

</div>

---

## 📚 Tài liệu đính kèm

| Tệp tin | Mô tả |
|:---|:---|
| [KET_QUA_THUC_HIEN.md](KET_QUA_THUC_HIEN.md) | Kết quả thực nghiệm đầy đủ: so sánh thuật toán, phân tích độ trễ, tiết kiệm RAM, dò siêu tham số. |
| [HUONG_DAN_THUC_HIEN.md](HUONG_DAN_THUC_HIEN.md) | Hướng dẫn cài đặt, khởi chạy dashboard, tải dữ liệu, chạy API. |
| [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) | Báo cáo kỹ thuật chi tiết bằng tiếng Việt. |
| [ann_10m_thesis_report.md](ann_10m_thesis_report.md) | Báo cáo đề tài môn học. |
