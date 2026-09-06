"""Kịch bản xây dựng tệp bộ đệm chỉ mục tìm kiếm ngữ nghĩa tốc độ cao (Search Index Cache Builder).
Trích xuất 2.500 văn bản Báo chí-Pháp luật và 2.500 văn bản Wikipedia tiếng Việt,
giải lượng tử hóa SQ8, chuẩn hóa L2 và tính toán trước tọa độ 3D PCA.
"""

import json
import os
import sys
import time
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from quantizer.sq8 import ScalarQuantizer8

def assign_category(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["chứng khoán", "tài chính", "ngân hàng", "xuất khẩu", "kinh tế", "doanh nghiệp", "usd", "giá cả", "lãi suất", "thương mại", "thị trường", "cổ phiếu"]):
        return "Kinh doanh & Tài chính"
    elif any(k in t for k in ["công nghệ", "trí tuệ nhân tạo", "vi mạch", "bán dẫn", "robot", "máy tính", "phần mềm", "lưới điện", "mạng nơ ron", "thuật toán", "kỹ thuật số"]):
        return "Khoa học & Công nghệ"
    elif any(k in t for k in ["giáo dục", "đại học", "trường học", "sinh viên", "học sinh", "đào tạo", "giảng viên", "học bổng", "luận văn", "tiến sĩ", "học viện"]):
        return "Giáo dục"
    elif any(k in t for k in ["y tế", "bệnh viện", "bác sĩ", "dược phẩm", "chữa bệnh", "sức khỏe", "điều trị", "chẩn đoán", "phòng dịch", "thuốc", "y học"]):
        return "Y tế & Sức khỏe"
    elif any(k in t for k in ["giao thông", "cao tốc", "đường bộ", "ngập", "xe cộ", "hạ tầng", "cầu đường", "quy hoạch", "vận tải", "sân bay", "cảng biển"]):
        return "Giao thông & Xây dựng"
    return "Văn hóa & Đời sống"

def main():
    t0 = time.time()
    print("[1] Nạp tham số lượng tử hóa SQ8 của 2 kho...")
    sq8_news = ScalarQuantizer8()
    with open(os.path.join(BASE_DIR, "data", "quantized", "quantization_params.json"), "r", encoding="utf-8") as f:
        sq8_news.load_params(json.load(f))

    sq8_wiki = ScalarQuantizer8()
    with open(os.path.join(BASE_DIR, "data", "quantized_wiki", "quantization_params.json"), "r", encoding="utf-8") as f:
        sq8_wiki.load_params(json.load(f))

    print("[2] Nạp tham số chiếu 3D PCA...")
    pca_file = os.path.join(BASE_DIR, "data", "processed", "pca_3d_projection.json")
    pca_mean = None
    pca_comps = None
    pca_scale = 1.0
    if os.path.exists(pca_file):
        with open(pca_file, "r", encoding="utf-8") as f:
            pca_data = json.load(f)
        pca_mean = np.array(pca_data["mean"], dtype=np.float32)
        pca_comps = np.array(pca_data["components"], dtype=np.float32)
        pca_scale = float(pca_data.get("scale_factor", 1.0))

    print("[3] Nạp vector và metadata từ News & Legal (2.500 bản ghi)...")
    mmap_news = np.memmap(
        os.path.join(BASE_DIR, "data", "quantized", "vectors_int8.dat"),
        dtype=np.int8,
        mode="r",
        shape=(16459486, 384)
    )
    N_SAMPLE = 2500
    vecs_news_deq = sq8_news.dequantize(mmap_news[:N_SAMPLE])

    meta_list = []
    with open(os.path.join(BASE_DIR, "data", "quantized", "metadata.jsonl"), "r", encoding="utf-8") as f:
        for i in range(N_SAMPLE):
            line = f.readline()
            if not line:
                break
            m = json.loads(line)
            title = m.get("title", f"Bản tin pháp luật #{i}")
            text = m.get("text") or m.get("preview") or ""
            cat = assign_category(title + " " + text)
            meta_list.append({
                "doc_id": m.get("doc_id", f"news_{i}"),
                "title": title,
                "preview": text[:180].replace("\n", " "),
                "category": cat,
                "source": "Báo chí & Pháp luật",
                "global_idx": i
            })

    print("[4] Nạp vector và metadata từ Wikipedia tiếng Việt (2.500 bản ghi)...")
    mmap_wiki = np.memmap(
        os.path.join(BASE_DIR, "data", "quantized_wiki", "vectors_int8.dat"),
        dtype=np.int8,
        mode="r",
        shape=(14872445, 384)
    )
    vecs_wiki_deq = sq8_wiki.dequantize(mmap_wiki[:N_SAMPLE])

    with open(os.path.join(BASE_DIR, "data", "quantized_wiki", "metadata.jsonl"), "r", encoding="utf-8") as f:
        for i in range(N_SAMPLE):
            line = f.readline()
            if not line:
                break
            m = json.loads(line)
            title = m.get("title", f"Bài viết Wiki #{i}")
            text = m.get("text") or m.get("preview") or ""
            cat = assign_category(title + " " + text)
            meta_list.append({
                "doc_id": m.get("doc_id", f"wiki_{i}"),
                "title": title,
                "preview": text[:180].replace("\n", " "),
                "category": cat,
                "source": "Wikipedia tiếng Việt",
                "global_idx": 16459486 + i
            })

    print("[5] Ghép nối và chuẩn hóa L2 vector...")
    all_vectors = np.vstack([vecs_news_deq, vecs_wiki_deq])
    norms = np.linalg.norm(all_vectors, axis=1, keepdims=True)
    all_vectors_norm = (all_vectors / np.maximum(norms, 1e-12)).astype(np.float32)

    print("[6] Tính toán tọa độ 3D PCA...")
    coords_3d = np.zeros((len(meta_list), 3), dtype=np.float32)
    if pca_mean is not None and pca_comps is not None:
        centered = all_vectors - pca_mean
        coords_3d = np.dot(centered, pca_comps) * pca_scale
        coords_3d = coords_3d.astype(np.float32)

    for i, meta in enumerate(meta_list):
        meta["x"] = float(round(coords_3d[i, 0], 3))
        meta["y"] = float(round(coords_3d[i, 1], 3))
        meta["z"] = float(round(coords_3d[i, 2], 3))

    print("[7] Lưu trữ bộ đệm chỉ mục ra đĩa...")
    out_npz = os.path.join(BASE_DIR, "data", "processed", "search_index_cache.npz")
    out_meta = os.path.join(BASE_DIR, "data", "processed", "search_index_metadata.json")

    np.savez_compressed(
        out_npz,
        vectors=all_vectors_norm,
        coords_3d=coords_3d,
        global_indices=np.array([m["global_idx"] for m in meta_list], dtype=np.int32)
    )

    with open(out_meta, "w", encoding="utf-8") as f:
        json.dump(meta_list, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - t0
    print(f"[HOÀN TẤT] Đã tạo thành công bộ đệm chỉ mục {len(meta_list):,} bản ghi trong {elapsed:.2f} giây.")
    print(f"  - Tệp vector nhị phân: {out_npz} ({os.path.getsize(out_npz) / 1024 / 1024:.2f} MB)")
    print(f"  - Tệp metadata JSON: {out_meta} ({os.path.getsize(out_meta) / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    main()
