# THƯ MỤC DỮ LIỆU ĐÃ XỬ LÝ (DATA/PROCESSED)

Thư mục này chứa kết quả nhúng vector (embeddings) và metadata sau khi chạy qua pipeline.

## 1\. Tải dữ liệu từ Google Drive

Các tệp vector nhị phân float32 (.dat) dung lượng lớn (15.36 GB) và tệp metadata (.jsonl) được lưu tại:
🔗 **Google Drive:** [https://drive.google.com/drive/folders/1pE2o3gbX\_MHZ14MUASGP8o9RNaIPYzdK?usp=drive\_link](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)

## 2\. Danh sách tệp cần đặt vào thư mục này:

* hf\_10m\_vectors.dat (15.36 GB): Mảng nhị phân float32 10 triệu vector x 384 chiều (np.memmap).
* hf\_10m\_metadata.jsonl: Metadata 10 triệu tài liệu tiếng Việt.
* 

eal\_news\_vectors.dat \&
eal\_news\_metadata.jsonl: Dữ liệu vector mẫu phục vụ chạy demo nhanh.

* pca\_3d\_projection.json \& 
ectors\_3d\_cache.json: Dữ liệu tọa độ 3D phục vụ hiển thị Dashboard.

