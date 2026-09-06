# HƯỚNG DẪN DỮ LIỆU THỰC NGHIỆM (DATASET GUIDE)

Do dung lượng tập dữ liệu 31.33 triệu bản ghi và các tệp nhị phân float32/int8 rất lớn (> 20 GB), toàn bộ dữ liệu nhị phân được lưu trữ bên ngoài Git repository.

👉 **Liên kết tải trọn bộ dữ liệu (Google Drive):**  
[https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

---

## 1. Cấu trúc thư mục dữ liệu

```text
data/
├── README.md                                # Hướng dẫn dữ liệu này
├── raw/                                     # Thư mục dữ liệu thô
│   ├── README.md                            # Hướng dẫn dữ liệu thô
│   └── benchmarks/                          # Dữ liệu chuẩn quốc tế (SIFT10K / SIFT1M)
├── processed/                               # Dữ liệu vector và bộ đệm đã xử lý
│   ├── README.md                            # Hướng dẫn dữ liệu processed
│   ├── search_index_cache.npz               # Bộ đệm 5.000 vector chuẩn hóa phục vụ tìm kiếm
│   ├── search_index_metadata.json           # Siêu dữ liệu bài viết kèm tọa độ 3D
│   ├── pca_3d_projection.json               # Ma trận chiếu PCA/SVD không gian 3 chiều
│   └── vectors_3d_cache.json                # Đồ thị 3D Three.js (3.000 điểm mây & 1.686 nút HNSW)
├── crawl/                                   # 200 Shards dữ liệu Báo chí & Pháp luật (.jsonl)
├── crawl_wiki/                              # 200 Shards dữ liệu Wikipedia tiếng Việt (.jsonl)
├── quantized/                               # Mảng int8 memmap Báo chí (16.45M vector, vectors_int8.dat)
├── quantized_wiki/                          # Mảng int8 memmap Wikipedia (14.87M vector, vectors_int8.dat)
├── quantized_combined/                      # Siêu kho hợp nhất 31.33M vector (corpus_offset_map.json)
└── experiments/                             # Kết quả thực nghiệm và báo cáo đối chuẩn
    ├── baselines_benchmark_results.json     # Kết quả so sánh 4 thuật toán
    └── scale_stress_results.json            # Kết quả đo đạc chịu tải
```

---

## 2. Hướng dẫn thiết lập dữ liệu

### Lựa chọn 1: Tải bộ dữ liệu đã tiền xử lý sẵn (Khuyến nghị)
1. Tải tệp dữ liệu từ liên kết Google Drive ở trên.
2. Đặt các thư mục vào đúng vị trí trong thư mục `data/` của dự án.
3. Khởi chạy giao diện tìm kiếm và visualizer 3D:
   ```bash
   cd dashboard
   npm start
   ```

### Lựa chọn 2: Tự động thu thập và tái tạo dữ liệu từ đầu
```bash
# 1. Thu thập dữ liệu Báo chí & Pháp luật
python scripts/run_crawler.py --target-records 100000 --batch-size 1000

# 2. Thu thập dữ liệu Wikipedia tiếng Việt
python scripts/run_wiki_crawler.py --target-records 100000 --batch-size 1000

# 3. Chạy lượng tử hóa SQ8 (int8)
python scripts/run_quantization.py
python scripts/run_wiki_quantization.py

# 4. Hợp nhất hai kho ngữ liệu
python scripts/merge_quantized_corpora.py

# 5. Khởi tạo bộ đệm tìm kiếm & giảm chiều 3D PCA
python dashboard/scripts/build_search_cache.py
python dashboard/scripts/dimension_reduction_3d.py
```

### Lựa chọn 3: Tải bộ dữ liệu đối chuẩn quốc tế SIFT10K / SIFT1M
```bash
python scripts/download_standard_datasets.py --dataset sift10k
python scripts/download_standard_datasets.py --dataset sift1m
```