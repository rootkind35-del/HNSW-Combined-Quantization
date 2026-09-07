"""Kịch bản xây dựng bộ đệm chỉ mục tìm kiếm sạch không chứa dữ liệu Hugging Face.

Trích xuất 2.500 văn bản Báo chí tiếng Việt (news_...) và 2.500 văn bản
Wikipedia tiếng Việt (wiki_...), giải lượng tử hóa SQ8 sang float32,
chuẩn hóa L2, tính toán PCA 3D và ghi đè các tệp bộ đệm tại data/processed/.
"""

import json
import os
import sys
import time
from typing import Dict, List, Tuple
import numpy as np

# Đảm bảo mã hóa UTF-8 trên Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from quantizer.sq8 import ScalarQuantizer8


def assign_category(text: str) -> str:
    """Phân loại chủ đề tài liệu dựa trên từ khóa."""
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


def load_clean_corpus_subset(
    meta_path: str,
    prefix: str,
    source_name: str,
    global_offset: int,
    target_count: int = 2500
) -> Tuple[List[int], List[Dict]]:
    """Duyệt metadata.jsonl, chỉ lấy các bản ghi có doc_id bắt đầu bằng tiền tố xác định."""
    row_indices = []
    metadata_list = []

    with open(meta_path, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f):
            if not line.strip():
                continue
            item = json.loads(line)
            doc_id = item.get("doc_id", "")
            if not doc_id.startswith(prefix):
                continue

            row_indices.append(line_idx)
            title = item.get("title") or f"{source_name} #{len(metadata_list)}"
            text = item.get("text") or item.get("preview") or ""
            cat = assign_category(title + " " + text)

            metadata_list.append({
                "doc_id": doc_id,
                "title": title,
                "preview": text[:180].replace("\n", " ").strip(),
                "category": cat,
                "source": source_name,
                "global_idx": global_offset + line_idx,
                "token_count": item.get("token_count", len(text.split()))
            })

            if len(metadata_list) >= target_count:
                break

    return row_indices, metadata_list


def compute_pca_3d(vectors: np.ndarray, n_components: int = 3):
    """Tính toán phép chiếu PCA 3 chiều bằng SVD và chuẩn hóa về dải [-45, 45]."""
    mean_vec = np.mean(vectors, axis=0)
    centered = vectors - mean_vec

    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    components = Vt[:n_components].T  # Kích thước (384, 3)

    coords = np.dot(centered, components)
    max_range = float(np.max(np.abs(coords)))
    scale_factor = 45.0 / max_range if max_range > 0 else 1.0
    scaled_coords = (coords * scale_factor).astype(np.float32)

    return scaled_coords, mean_vec.astype(np.float32), components.astype(np.float32), float(scale_factor)


def generate_hnsw_3d_topology(coords_3d: np.ndarray, metadata: List[Dict]) -> Dict:
    """Tạo cấu trúc đồ thị phân tầng HNSW 3 tầng (Layer 2, Layer 1, Layer 0)."""
    n = min(len(coords_3d), 1200)
    sample_indices = np.linspace(0, len(coords_3d) - 1, n, dtype=int)

    layer_heights = {2: 28.0, 1: 0.0, 0: -28.0}

    l2_nodes = []
    l1_nodes = []
    l0_nodes = []

    for idx in sample_indices:
        x, y, z = float(coords_3d[idx][0]), float(coords_3d[idx][1]), float(coords_3d[idx][2])
        meta = metadata[idx]
        node_id = meta.get("doc_id", f"node_{idx}")
        title = meta.get("title", f"Document {idx}")
        category = meta.get("category", "Văn hóa & Đời sống")

        node_l0 = {
            "id": f"l0_{node_id}_{idx}",
            "doc_id": node_id,
            "orig_index": int(idx),
            "layer": 0,
            "x": round(x, 2),
            "y": layer_heights[0],
            "z": round(z, 2),
            "title": title,
            "category": category
        }
        l0_nodes.append(node_l0)

        if idx % 5 == 0:
            node_l1 = {
                "id": f"l1_{node_id}_{idx}",
                "doc_id": node_id,
                "orig_index": int(idx),
                "layer": 1,
                "x": round(x * 0.85, 2),
                "y": layer_heights[1],
                "z": round(z * 0.85, 2),
                "title": title,
                "category": category
            }
            l1_nodes.append(node_l1)

            if idx % 25 == 0 or len(l2_nodes) < 8:
                node_l2 = {
                    "id": f"l2_{node_id}_{idx}",
                    "doc_id": node_id,
                    "orig_index": int(idx),
                    "layer": 2,
                    "x": round(x * 0.7, 2),
                    "y": layer_heights[2],
                    "z": round(z * 0.7, 2),
                    "title": title,
                    "category": category
                }
                l2_nodes.append(node_l2)

    edges = []

    def connect_layer(nodes_list, max_neighbors=4):
        n_nodes = len(nodes_list)
        if n_nodes < 2:
            return
        pts = np.array([[n["x"], n["z"]] for n in nodes_list])
        for i in range(n_nodes):
            dists = np.sum((pts - pts[i]) ** 2, axis=1)
            nearest = np.argsort(dists)[1 : min(max_neighbors + 1, n_nodes)]
            for j in nearest:
                edges.append({
                    "from": nodes_list[i]["id"],
                    "to": nodes_list[j]["id"],
                    "layer": nodes_list[i]["layer"],
                    "type": "intra"
                })

    connect_layer(l2_nodes, max_neighbors=3)
    connect_layer(l1_nodes, max_neighbors=4)
    connect_layer(l0_nodes, max_neighbors=4)

    inter_links = []
    for l2_n in l2_nodes:
        for l1_n in l1_nodes:
            if l2_n["orig_index"] == l1_n["orig_index"]:
                inter_links.append({"from": l2_n["id"], "to": l1_n["id"], "type": "inter"})
                break
    for l1_n in l1_nodes:
        for l0_n in l0_nodes:
            if l1_n["orig_index"] == l0_n["orig_index"]:
                inter_links.append({"from": l1_n["id"], "to": l0_n["id"], "type": "inter"})
                break

    entry_point_id = l2_nodes[0]["id"] if l2_nodes else (l1_nodes[0]["id"] if l1_nodes else l0_nodes[0]["id"])

    return {
        "layers": [
            {"level": 2, "name": "Layer 2: Top Sparse Navigation Tier", "y": layer_heights[2], "nodes": l2_nodes},
            {"level": 1, "name": "Layer 1: Intermediate Routing Tier", "y": layer_heights[1], "nodes": l1_nodes},
            {"level": 0, "name": "Layer 0: Dense Base Graph Tier", "y": layer_heights[0], "nodes": l0_nodes},
        ],
        "intra_edges": edges,
        "inter_links": inter_links,
        "entry_point_id": entry_point_id,
        "stats": {
            "total_nodes_l2": len(l2_nodes),
            "total_nodes_l1": len(l1_nodes),
            "total_nodes_l0": len(l0_nodes),
            "total_edges": len(edges) + len(inter_links)
        }
    }


def build_cache():
    start_time = time.time()
    n_sample = 2500

    news_meta_file = os.path.join(BASE_DIR, "data", "quantized", "metadata.jsonl")
    news_dat_file = os.path.join(BASE_DIR, "data", "quantized", "vectors_int8.dat")
    news_param_file = os.path.join(BASE_DIR, "data", "quantized", "quantization_params.json")

    wiki_meta_file = os.path.join(BASE_DIR, "data", "quantized_wiki", "metadata.jsonl")
    wiki_dat_file = os.path.join(BASE_DIR, "data", "quantized_wiki", "vectors_int8.dat")
    wiki_param_file = os.path.join(BASE_DIR, "data", "quantized_wiki", "quantization_params.json")

    out_dir = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)

    print("[1/7] Đọc và lọc dữ liệu Báo chí tiếng Việt (chỉ lấy news_)...")
    news_rows, news_metadata = load_clean_corpus_subset(
        meta_path=news_meta_file,
        prefix="news_",
        source_name="Báo chí & Pháp luật",
        global_offset=0,
        target_count=n_sample
    )
    print(f"      -> Thu thập {len(news_metadata)} bản ghi news (dòng {news_rows[0]} đến {news_rows[-1]}).")

    print("[2/7] Đọc và lọc dữ liệu Wikipedia tiếng Việt (chỉ lấy wiki_)...")
    wiki_rows, wiki_metadata = load_clean_corpus_subset(
        meta_path=wiki_meta_file,
        prefix="wiki_",
        source_name="Wikipedia tiếng Việt",
        global_offset=16459486,
        target_count=n_sample
    )
    print(f"      -> Thu thập {len(wiki_metadata)} bản ghi wiki (dòng {wiki_rows[0]} đến {wiki_rows[-1]}).")

    print("[3/7] Nạp vector int8 từ đĩa và giải lượng tử hóa SQ8 sang float32...")
    mmap_news = np.memmap(news_dat_file, dtype=np.int8, mode="r", shape=(16459486, 384))
    raw_news_int8 = np.array(mmap_news[news_rows], dtype=np.int8)
    del mmap_news

    sq8_news = ScalarQuantizer8()
    with open(news_param_file, "r", encoding="utf-8") as f:
        sq8_news.load_params(json.load(f))
    vecs_news_float = sq8_news.dequantize(raw_news_int8)

    mmap_wiki = np.memmap(wiki_dat_file, dtype=np.int8, mode="r", shape=(14872445, 384))
    raw_wiki_int8 = np.array(mmap_wiki[wiki_rows], dtype=np.int8)
    del mmap_wiki

    sq8_wiki = ScalarQuantizer8()
    with open(wiki_param_file, "r", encoding="utf-8") as f:
        sq8_wiki.load_params(json.load(f))
    vecs_wiki_float = sq8_wiki.dequantize(raw_wiki_int8)

    print("[4/7] Ghép nối và chuẩn hóa L2 vector...")
    all_vectors = np.vstack([vecs_news_float, vecs_wiki_float]).astype(np.float32)
    norms = np.linalg.norm(all_vectors, axis=1, keepdims=True)
    all_vectors_norm = (all_vectors / np.maximum(norms, 1e-12)).astype(np.float32)

    all_metadata = news_metadata + wiki_metadata
    assert len(all_metadata) == 5000, f"Tổng số bản ghi không khớp 5000: {len(all_metadata)}"
    assert all(not m["doc_id"].startswith("hf_") for m in all_metadata), "Phát hiện bản ghi hf_!"

    print("[5/7] Tính toán phép chiếu PCA 3D và lưu tham số mô hình...")
    coords_3d, mean_vec, components, scale_factor = compute_pca_3d(all_vectors_norm, n_components=3)

    pca_file = os.path.join(out_dir, "pca_3d_projection.json")
    with open(pca_file, "w", encoding="utf-8") as f:
        json.dump({
            "mean": mean_vec.tolist(),
            "components": components.tolist(),
            "scale_factor": float(scale_factor)
        }, f, ensure_ascii=False)
    print(f"      -> Lưu tham số PCA: {pca_file}")

    print("[6/7] Cập nhật tọa độ 3D vào metadata và ghi search_index_cache.npz...")
    cleaned_metadata = []
    for i, m in enumerate(all_metadata):
        cleaned_m = {
            "doc_id": m["doc_id"],
            "title": m["title"],
            "preview": m["preview"],
            "category": m["category"],
            "source": m["source"],
            "global_idx": m["global_idx"],
            "x": float(round(coords_3d[i, 0], 3)),
            "y": float(round(coords_3d[i, 1], 3)),
            "z": float(round(coords_3d[i, 2], 3))
        }
        cleaned_metadata.append(cleaned_m)

    meta_file = os.path.join(out_dir, "search_index_metadata.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(cleaned_metadata, f, ensure_ascii=False, indent=2)
    print(f"      -> Lưu metadata ({len(cleaned_metadata)} bản ghi): {meta_file}")

    npz_file = os.path.join(out_dir, "search_index_cache.npz")
    global_indices = np.array([m["global_idx"] for m in cleaned_metadata], dtype=np.int32)
    np.savez_compressed(
        npz_file,
        vectors=all_vectors_norm,
        coords_3d=coords_3d,
        global_indices=global_indices
    )
    print(f"      -> Lưu search_index_cache.npz: {npz_file}")

    print("[7/7] Sinh cấu trúc đồ thị HNSW 3D và lưu vectors_3d_cache.json...")
    vector_cloud = []
    for i, m in enumerate(cleaned_metadata):
        vector_cloud.append({
            "id": m["doc_id"],
            "index": i,
            "x": m["x"],
            "y": m["y"],
            "z": m["z"],
            "title": m["title"],
            "preview": m["preview"],
            "category": m["category"],
            "token_count": all_metadata[i].get("token_count", 0)
        })

    hnsw_topology = generate_hnsw_3d_topology(coords_3d, cleaned_metadata)

    v3d_file = os.path.join(out_dir, "vectors_3d_cache.json")
    with open(v3d_file, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(vector_cloud),
            "source": "data/processed/search_index_cache.npz (5,000 vectors)",
            "bounds": {"min": -45.0, "max": 45.0},
            "vectors": vector_cloud,
            "hnsw_topology": hnsw_topology
        }, f, ensure_ascii=False)
    print(f"      -> Lưu vectors_3d_cache.json: {v3d_file}")

    elapsed = time.time() - start_time
    print(f"Xử lý thành công trong {elapsed:.2f} giây.")


if __name__ == "__main__":
    build_cache()
