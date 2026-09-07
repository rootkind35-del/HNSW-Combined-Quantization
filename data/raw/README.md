# THƯ MỤC DỮ LIỆU THÔ (DATA/RAW)

Thư mục này dùng để chứa toàn bộ dữ liệu thô nguyên bản trước khi qua pipeline làm sạch và lọc trùng.

## 1. Tải dữ liệu từ Google Drive

Do dung lượng lưu trữ lớn, toàn bộ các tệp dữ liệu thô được lưu trữ tập trung tại:
🔗 **Google Drive:** [https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

## 2. Danh mục các phân vùng dữ liệu thô:

- `data/crawl/`: 200 shards dữ liệu Báo chí & Pháp luật (`shard_00000.jsonl` đến `shard_00199.jsonl`), chứa 16.459.486 bản ghi toàn văn kèm tệp kê khai `CRAWL_MANIFEST.json`.
- `data/crawl_wiki/`: 200 shards dữ liệu Wikipedia tiếng Việt (`shard_00000.jsonl` đến `shard_00199.jsonl`), chứa 14.872.445 phân đoạn bách khoa toàn thư kèm tệp kê khai `CRAWL_MANIFEST.json`.
- `data/raw/benchmarks/`: Dữ liệu vector chuẩn quốc tế phục vụ đối chuẩn thuật toán:
  - `siftsmall/`: Tập dữ liệu SIFT10K (`siftsmall_base.fvecs`, `siftsmall_query.fvecs`, `siftsmall_groundtruth.ivecs`).
  - `sift/`: Tập dữ liệu SIFT1M.
