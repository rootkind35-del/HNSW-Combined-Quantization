# THƯ MỤC DỮ LIỆU ĐÃ XỬ LÝ (DATA/PROCESSED)

Thư mục này chứa kết quả nhúng vector, siêu dữ liệu đã làm sạch và bộ đệm phục vụ tìm kiếm ngữ nghĩa, trực quan hóa 3D và đánh giá hiệu năng.

## 1. Tải bộ đệm từ Google Drive

Các tệp bộ đệm tiền xử lý được đóng gói sẵn tại:  
🔗 **Google Drive:** [https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

## 2. Danh mục tệp và cấu trúc thư mục

- `search_index_cache.npz`: Mảng NumPy chứa 5.000 vector mẫu cân bằng (2.500 Báo chí + 2.500 Wikipedia), 384 chiều đã chuẩn hóa $L_2$, kèm ma trận tọa độ 3D và chỉ số toàn cục.
- `search_index_metadata.json`: Siêu dữ liệu 5.000 tài liệu sạch (100% dữ liệu miền thật, không chứa mẫu rác `hf_`), gồm `doc_id`, `title`, `preview`, `category`, `source`, `global_idx`.
- `pca_3d_projection.json`: Tham số ma trận chiếu giảm chiều PCA (mean, components, scale_factor) từ 384 chiều xuống không gian 3 chiều.
- `vectors_3d_cache.json`: Tệp tọa độ điểm mây phục vụ dựng không gian 3D tương tác bằng Three.js trên Web Dashboard.
- `evaluation_results/`: Thư mục lưu trữ tự động các báo cáo đánh giá đối chuẩn đa thuật toán (`benchmark_report_*.json` và `benchmark_summary_*.md`).
- `query_logs/`: Thư mục lưu trữ nhật ký truy vấn đơn lẻ (`query_*.json`) kèm số liệu độ trễ, RAM và kết quả Top-K.

## 3. Lệnh tái tạo bộ đệm sạch từ nguồn lượng tử hóa

```bash
# Trích xuất 5.000 bản ghi sạch (2.500 News + 2.500 Wiki), giải lượng tử hóa SQ8 sang float32 và tính PCA 3D
python scripts/build_clean_search_cache.py
```
