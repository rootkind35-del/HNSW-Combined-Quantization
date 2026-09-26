<div align="center">

# HNSW Combined Quantization: Tìm kiếm Vector Dữ liệu Lớn theo Hai Tầng

<p align="center">
  <b>Tìm kiếm lân cận gần nhất (ANN) trên bộ nhớ ngoài với thông lượng cao cho 16.45 triệu vector dày đặc (384-D) trên phần cứng máy tính phổ thông.</b>
</p>

<p align="center">
  <a href="#-benchmarks--empirical-results"><img alt="Quy mô Corpus" src="https://img.shields.io/badge/Quy%20m%C3%B4-16.45M%20Vectors-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-data-value-assessment"><img alt="Giảm RAM" src="https://img.shields.io/badge/Ti%E1%BA%BFt%20ki%E1%BB%87m%20RAM--75%25-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-interactive-dashboard"><img alt="Dashboard" src="https://img.shields.io/badge/Dashboard-Port%203000-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>
</p>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](LICENSE)

<p align="center">
  <a href="README.md"><img alt="English" height="40" src="https://img.shields.io/badge/English-CDCFD4"></a>&nbsp;
  <a href="README_VN.md"><img alt="Tiếng Việt" height="40" src="https://img.shields.io/badge/Tiếng_Việt-BCDCF7"></a>
</p>

[Tính năng](#-tính-năng-chính) • [Cài đặt](#-bắt-đầu) • [Phân tích Dữ liệu](#-phân-tích-giá-trị-dữ-liệu) • [Công cụ CLI](#%EF%B8%8F-cli--automation)

</div>

---

> 🤝 **Chúng tôi hoan nghênh mọi đóng góp!** Dự án đang tìm kiếm cộng tác viên để mở rộng tích hợp Product Quantization (PQ) và các thuật toán định tuyến SSD bên ngoài.

## 🌟 Tính Năng Chính

HNSW Combined Quantization mang đến một hệ thống tìm kiếm vector chuẩn sản xuất được xây dựng hoàn toàn từ con số không bằng Python, vượt qua nút thắt bộ nhớ của các chỉ mục đồ thị Float32 thông thường.

- **Lượng tử hóa Hai Tầng (SQ8 + Graph Re-ranking)** — Nén các vector gốc thành số nguyên 8-bit trong khi vẫn duy trì lớp điều hướng Float32 có độ chính xác cao.
- **Adaptive Early-Exit** — Dừng sớm quá trình duyệt đồ thị dựa trên ngưỡng delta khoảng cách, giúp giảm tới 40% tính toán.
- **LRU Cache & SSD Direct I/O** — Đẩy các vector ít truy cập xuống ổ cứng và nạp lại vào bộ nhớ thông qua cơ chế memory mapping.
- **Bộ Đánh Giá Phổ Quát (Universal Evaluation Harness)** — Kịch bản tự động kiểm tra tải (stress test) đối đầu trực tiếp giữa Standard HNSW và Two-Tier HNSW.
- **Interactive Data Analyst Dashboard** — Giao diện Web hoàn chỉnh (Express/Node.js) hiển thị các chỉ số W&B-style, biểu đồ QPS theo thời gian thực.

---

## 🚀 Bắt Đầu

Kiến trúc hệ thống sử dụng backend Python để chạy các thuật toán lõi HNSW và một máy chủ Express Node.js để phục vụ giao diện React.

<details>
<summary><b>Cài đặt & Chạy Dự án</b></summary>

### 1. Thiết lập Backend

```bash
# Clone kho lưu trữ
git clone https://github.com/rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

# Cài đặt thư viện Python
pip install -r requirements.txt

# Khởi chạy Python Search API
python dashboard/scripts/search_service.py
```

### 2. Thiết lập Frontend

Trong một cửa sổ terminal mới:

```bash
# Di chuyển tới thư mục dashboard
cd dashboard

# Cài đặt thư viện Node
npm install

# Khởi chạy dashboard
npm start
```
Ứng dụng sẽ hoạt động tại `http://localhost:3000`.
</details>

---

## 📊 Phân Tích Giá Trị Dữ Liệu

Hệ thống của chúng tôi đi kèm với một tệp Notebook phân tích và kiểm thử tự động (`test.ipynb`). Tập dữ liệu 16.45 triệu bản ghi (mock cục bộ 5.000 mẫu để phát triển) tập trung mạnh vào lĩnh vực **Báo chí, Pháp luật và Giáo dục**.

### 1. Chất lượng Dữ liệu & Phân bổ
- **Tính hội tụ chuyên môn:** Dữ liệu bao phủ rất tốt mảng Pháp luật. Đây là mỏ vàng để xây dựng các mô hình RAG (Retrieval-Augmented Generation) phục vụ trợ lý ảo AI ngành luật.
- **Cấu trúc đoạn (Chunking):** Các trích đoạn trung bình dao động từ 20–40 từ, kích thước hoàn hảo để mô hình embedding (như `all-MiniLM-L6-v2`) trích xuất trọn vẹn ngữ nghĩa.

### 2. Đánh giá Tối ưu Thuật toán
Dựa trên các bài test đối đầu trực tiếp trong môi trường Jupyter:

- **Giải tỏa Nút thắt Độ trễ:** Cả `Standard HNSW` và `Two-Tier HNSW` đều phản hồi dưới **3ms**, duy trì băng thông **>300 QPS** trên đơn luồng.
- **Sự Đánh Đổi Lượng Tử SQ8:** Kiến trúc Hai Tầng áp dụng lượng tử hóa 8-bit trên lớp dữ liệu.
  - **Đánh đổi:** Chấp nhận giảm khoảng ~1-2% tỷ lệ khớp chính xác nhất (Recall@1).
  - **Lợi ích:** Tiết kiệm đến **75% bộ nhớ RAM** (ép từ 64GB xuống còn ~16GB), giúp chạy mượt mà Big Data trên các máy chủ giá rẻ, trong khi phương sai hệ không gian L2 vẫn được bảo toàn >98%.

---

## ⚙️ CLI & Automation

Để đánh giá tự động (headless), dự án cung cấp một kịch bản CLI chuyên dụng.

```bash
# Chạy bộ đánh giá truy xuất phổ quát
python scripts/run_retrieval_evaluation.py --top-k 10
```

*Ví dụ đầu ra:*
```text
================================================================================
| Algorithm   | QPS    | Latency (Mean) | Latency (P95) | Recall@10 |
|-------------|--------|----------------|---------------|-----------|
| hnsw        | 303.70 | 2.90 ms        | 4.12 ms       | 0.9830    |
| pure_sq8    | 345.10 | 2.65 ms        | 3.90 ms       | 0.8105    |
| two_tier    | 320.40 | 2.75 ms        | 4.01 ms       | 0.9650    |
================================================================================
```

---

## 📄 Bản Quyền & Cộng Đồng

Dự án này là mã nguồn mở dưới giấy phép **Apache 2.0**.
