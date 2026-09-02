# HƯỚNG DẪN TẢI VÀ CẤU HÌNH BỘ DỮ LIỆU (DATASET DOWNLOAD GUIDE)

Do quy mô tập dữ liệu lớn (> 10 triệu bản ghi, dung lượng vector thô > 15.36 GB), toàn bộ dữ liệu thô và dữ liệu vector đã xử lý được lưu trữ tập trung trên Google Drive thay vì đẩy trực tiếp lên Git Repository.

---

## 1. Đường dẫn tải Dữ liệu (Google Drive Link)

🔗 **Google Drive Folder:**  
[https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

---

## 2. Cấu trúc thư mục dữ liệu sau khi tải về

Sau khi tải các tệp từ link Google Drive ở trên, hãy giải nén và đặt vào đúng cấu trúc thư mục như sau:

\data/
├── README.md                                # File hướng dẫn này
├── raw/                                     # Thư mục dữ liệu thô
│   ├── README.md                            # Mô tả chi tiết dữ liệu thô
│   ├── RAW_DATASET_MANIFEST.json            # Bảng đặc tả manifest các thuộc tính
│   ├── raw_crawled_news.jsonl               # 500K tin tức tự cào từ báo điện tử (VnExpress, Dân Trí)
│   └── raw_vietnamese_corpus_10m.jsonl      # 9.5M văn bản ngữ liệu thô tiếng Việt
├── processed/                               # Thư mục dữ liệu vector đã nhúng
│   ├── README.md                            # Mô tả dữ liệu đã xử lý
│   ├── real_news_metadata.jsonl             # Metadata tin tức tiếng Việt
│   ├── real_news_vectors.dat                # Vector nhúng float32 mẫu (384 chiều)
│   ├── hf_10m_vectors.dat                   # Vector nhị phân memmap 10 triệu bản ghi (15.36 GB)
│   ├── hf_10m_metadata.jsonl                # Metadata 10 triệu bản ghi (JSONL)
│   ├── hf_10m_checkpoint.json               # Checkpoint nạp luồng dữ liệu
│   ├── pca_3d_projection.json               # Dữ liệu chiếu 3D PCA cho Dashboard
│   └── vectors_3d_cache.json                # Cache không gian 3D Three.js
└── experiments/                             # Kết quả thực nghiệm và bảng đối chuẩn
    ├── scale_stress_results.json            # Kết quả đo đạc 3 mốc (100K, 1M, 10M)
    └── scale_stress_summary.md              # Báo cáo tóm tắt thực nghiệm
\
---

## 3. Tự động thu thập hoặc tạo lại dữ liệu bằng mã nguồn

Nếu không tải trực tiếp từ Drive, bạn có thể tự chạy pipeline để thu thập và xử lý lại dữ liệu từ đầu bằng các lệnh sau:

### Bước 1: Cào tin tức thực tế từ Internet
\\ash
python scripts/crawl_real_data.py --limit 500
\
### Bước 2: Tải và khởi tạo dữ liệu thô
\\ash
python scripts/download_and_save_raw_data.py
\
### Bước 3: Chạy Pipeline làm sạch, lọc trùng MinHash và tạo Vector Memmap
\\ash
python scripts/stream_hf_large_scale.py --max-records 10000000 --batch-size 10000
\