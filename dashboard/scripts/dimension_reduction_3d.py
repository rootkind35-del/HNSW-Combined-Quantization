"""
Giảm chiều không gian 3D (PCA/SVD) và tiền tính toán cấu trúc đồ thị phân tầng HNSW cho Web Dashboard Three.js.
Chiếu các vector đặc trưng 384 chiều xuống tọa độ không gian 3 chiều (X, Y, Z)
và sinh cấu trúc đồ thị phân tầng HNSW (Layer 2, Layer 1, Layer 0) kèm các liên kết chuyển tầng.
"""

import json
import os
import sys
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))


def assign_category(text: str) -> str:
    """Phân loại nhóm chủ đề bài viết dựa trên từ khóa tiếng Việt."""

    t = text.lower()
    if any(k in t for k in ["chứng khoán", "tài chính", "ngân hàng", "xuất khẩu", "kinh tế", "doanh nghiệp", "usd", "giá cả", "lãi suất", "cổ phiếu", "tăng trưởng"]):
        return "Kinh doanh & Tài chính"
    elif any(k in t for k in ["công nghệ", "trí tuệ nhân tạo", "vi mạch", "bán dẫn", "robot", "máy tính", "phần mềm", "điện tử", "linh kiện", "mạng n", "thị giác"]):
        return "Khoa học & Công nghệ"
    elif any(k in t for k in ["giáo dục", "đại học", "trường học", "sinh viên", "học sinh", "đào tạo", "giảng viên"]):
        return "Giáo dục"
    elif any(k in t for k in ["y tế", "bệnh viện", "bác sĩ", "dược phẩm", "chữa bệnh", "sức khỏe"]):
        return "Y tế & Sức khỏe"
    elif any(k in t for k in ["giao thông", "cao tốc", "đường bộ", "ngập", "xe cộ", "hạ tầng", "cầu đường", "lúa gạo"]):
        return "Giao thông & Xây dựng"
    return "Văn hóa & Đời sống"


def load_dataset(max_samples: int = 3000):
    """Nạp mẫu vector và metadata từ bộ đệm chỉ mục thực tế hoặc Kho Hợp nhất 31.33M vector."""
    # 1. Ưu tiên nạp từ search_index_cache.npz để đồng bộ 100% tọa độ 3D với bộ tìm kiếm thực tế
    npz_path = os.path.join(BASE_DIR, "data", "processed", "search_index_cache.npz")
    meta_path = os.path.join(BASE_DIR, "data", "processed", "search_index_metadata.json")

    if os.path.exists(npz_path) and os.path.exists(meta_path):
        try:
            npz_data = np.load(npz_path)
            all_vecs = npz_data["vectors"].astype(np.float32)
            with open(meta_path, "r", encoding="utf-8") as f:
                all_meta = json.load(f)

            n = min(len(all_vecs), max_samples)
            vectors = all_vecs[:n]
            metadata = all_meta[:n]
            return vectors, metadata, f"data/processed/search_index_cache.npz ({len(all_vecs):,} vectors)", all_vecs, all_meta
        except Exception as e:
            print(f"[3D Pipeline] Lỗi nạp từ search_index_cache: {e}")

    # 2. Fallback nạp từ Kho Hợp nhất 31.33M
    combined_dir = os.path.join(BASE_DIR, "data", "quantized_combined")
    map_file = os.path.join(combined_dir, "corpus_offset_map.json")

    if os.path.exists(map_file):
        try:
            from quantizer.unified_corpus import UnifiedQuantizedCorpus
            corpus = UnifiedQuantizedCorpus(combined_dir)
            total = len(corpus)
            half = max_samples // 2
            idx1 = [i * 20 for i in range(half)]
            idx2 = [16459486 + i * 20 for i in range(half)]
            sample_indices = idx1 + idx2

            vecs_int8 = corpus.get_vectors(sample_indices)
            vectors = vecs_int8.astype(np.float32)
            meta_dict = corpus.get_metadata_batch(sample_indices)
            corpus.close()

            metadata = []
            for g_idx in sample_indices:
                m = meta_dict.get(g_idx, {})
                title_text = m.get("title", "") + " " + (m.get("text") or m.get("summary", ""))
                cat = assign_category(title_text)
                metadata.append({
                    "doc_id": m.get("doc_id", f"doc_{g_idx}"),
                    "title": m.get("title", f"Tài liệu {g_idx}"),
                    "preview": (m.get("text") or m.get("summary", ""))[:150],
                    "category": cat,
                    "corpus_source": m.get("corpus_source", "combined"),
                    "token_count": len((m.get("text") or "").split())
                })
            return vectors, metadata, f"data/quantized_combined ({total:,} vectors, 2 nguồn)", None
        except Exception as e:
            print(f"[3D Pipeline] Lỗi nạp từ kho hợp nhất: {e}")

    # 3. Fallback kiểm tra các kho con đơn lẻ
    candidates = [
        ("data/quantized/vectors_int8.dat", "data/quantized/metadata.jsonl", 384, "int8"),
        ("data/quantized_wiki/vectors_int8.dat", "data/quantized_wiki/metadata.jsonl", 384, "int8"),
    ]

    for v_rel, m_rel, dim, dtype in candidates:
        v_path = os.path.join(BASE_DIR, v_rel)
        m_path = os.path.join(BASE_DIR, m_rel)
        if os.path.exists(v_path) and os.path.exists(m_path):
            metadata = []
            with open(m_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            meta_obj = json.loads(line)
                            title_text = meta_obj.get("title", "") + " " + meta_obj.get("text", meta_obj.get("preview", ""))
                            meta_obj["category"] = assign_category(title_text)
                            metadata.append(meta_obj)
                            if len(metadata) >= max_samples:
                                break
                        except Exception:
                            pass
            count = len(metadata)
            if count > 0:
                mmap = np.memmap(v_path, dtype=dtype, mode="r", shape=(count, dim))
                vectors = np.array(mmap, dtype=np.float32)
                del mmap
                return vectors, metadata, v_rel, None

    # Fallback synthetic
    np.random.seed(42)
    dim = 384
    count = 100
    vectors = np.random.randn(count, dim).astype(np.float32)
    metadata = [
        {
            "doc_id": f"synthetic_{i}",
            "title": f"Tài liệu nghiên cứu khoa học hệ thống số {i}",
            "preview": f"Bản tin phân tích thử nghiệm vector số {i}",
            "category": "Khoa học & Công nghệ" if i % 2 == 0 else "Kinh doanh & Tài chính",
            "token_count": 50,
        }
        for i in range(count)
    ]
    return vectors, metadata, "synthetic", None


def compute_pca_3d(vectors: np.ndarray, n_components: int = 3):
    """Computes PCA projection using SVD."""
    mean = np.mean(vectors, axis=0)
    centered = vectors - mean

    # SVD
    U, S, Vt = np.linalg.svd(centered, full_matrices=False)
    components = Vt[:n_components].T  # shape (384, 3)

    coords = np.dot(centered, components)

    # Scale coordinates to fit roughly in [-45, 45] range
    max_range = np.max(np.abs(coords))
    if max_range > 0:
        scale_factor = 45.0 / max_range
    else:
        scale_factor = 1.0

    scaled_coords = coords * scale_factor

    return scaled_coords, mean, components, scale_factor


def generate_hnsw_3d_topology(coords_3d: np.ndarray, metadata: list):
    """
    Tạo cấu trúc đồ thị phân tầng HNSW đa tầng quy mô lớn:
    - Layer 2 (Top Navigation): ~50 nút, kết nối thưa điều hướng nhanh.
    - Layer 1 (Mid Express Routing): ~240 nút, liên kết nhảy cóc tầm trung.
    - Layer 0 (Base Dense Layer): ~1.200 nút, mạng lưới đồ thị dày đặc cơ sở.
    """
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

        # Layer 0 chứa toàn bộ các nút trong mẫu (1.200 nút)
        node_l0 = {
            "id": f"l0_{node_id}",
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

        # Layer 1 lấy ~20% số nút (~240 nút)
        if idx % 5 == 0:
            node_l1 = {
                "id": f"l1_{node_id}",
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

            # Layer 2 lấy ~4% số nút (~48-50 nút)
            if idx % 25 == 0 or len(l2_nodes) < 8:
                node_l2 = {
                    "id": f"l2_{node_id}",
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

    # Xây dựng liên kết cùng tầng (Intra-layer edges)
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

    # Xây dựng liên kết chuyển tầng dọc (Inter-layer links)
    inter_links = []
    for l2_n in l2_nodes:
        for l1_n in l1_nodes:
            if l2_n["doc_id"] == l1_n["doc_id"]:
                inter_links.append({"from": l2_n["id"], "to": l1_n["id"], "type": "inter"})
                break
    for l1_n in l1_nodes:
        for l0_n in l0_nodes:
            if l1_n["doc_id"] == l0_n["doc_id"]:
                inter_links.append({"from": l1_n["id"], "to": l0_n["id"], "type": "inter"})
                break

    # Điểm thâm nhập (Entry point) tại Tầng 2
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


def main():
    print("[3D Pipeline] Nạp dữ liệu vector đặc trưng và metadata...")
    loaded = load_dataset(max_samples=3000)
    all_vecs = None
    all_meta = None
    if len(loaded) == 5:
        vectors, metadata, source_file, all_vecs, all_meta = loaded
    elif len(loaded) == 4:
        vectors, metadata, source_file, _ = loaded
    else:
        vectors, metadata, source_file = loaded[:3]

    print(f"[3D Pipeline] Đã nạp {len(vectors):,} vector từ: {source_file}")

    train_vecs = all_vecs if all_vecs is not None else vectors
    print("[3D Pipeline] Tính toán phép chiếu PCA/SVD không gian 3 chiều chuẩn xác...")
    scaled_coords_all, mean_vec, components, scale_factor = compute_pca_3d(train_vecs, n_components=3)

    # Đồng bộ tọa độ 3D chuẩn hóa vào search_index_cache.npz và search_index_metadata.json
    npz_path = os.path.join(BASE_DIR, "data", "processed", "search_index_cache.npz")
    meta_path = os.path.join(BASE_DIR, "data", "processed", "search_index_metadata.json")
    if all_vecs is not None and os.path.exists(npz_path):
        try:
            npz_data = np.load(npz_path)
            np.savez_compressed(
                npz_path,
                vectors=all_vecs,
                coords_3d=scaled_coords_all,
                global_indices=npz_data["global_indices"]
            )
            print(f"[3D Pipeline] Đã cập nhật tọa độ chuẩn hóa 3D vào {npz_path}")
        except Exception as e:
            print(f"[3D Pipeline] Lỗi ghi lại npz: {e}")

    if all_meta is not None and os.path.exists(meta_path):
        try:
            for i in range(len(all_meta)):
                all_meta[i]["x"] = float(round(scaled_coords_all[i, 0], 3))
                all_meta[i]["y"] = float(round(scaled_coords_all[i, 1], 3))
                all_meta[i]["z"] = float(round(scaled_coords_all[i, 2], 3))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(all_meta, f, ensure_ascii=False, indent=2)
            print(f"[3D Pipeline] Đã cập nhật metadata x,y,z vào {meta_path}")
        except Exception as e:
            print(f"[3D Pipeline] Lỗi ghi lại meta: {e}")

    coords_3d = scaled_coords_all[:len(vectors)]

    # Chuẩn bị 3.000 điểm cho Đám mây Vector 3D
    vector_cloud = []
    for i in range(len(vectors)):
        meta = metadata[i]
        vector_cloud.append({
            "id": meta.get("doc_id", f"doc_{i}"),
            "index": i,
            "x": float(round(coords_3d[i][0], 3)),
            "y": float(round(coords_3d[i][1], 3)),
            "z": float(round(coords_3d[i][2], 3)),
            "title": meta.get("title", f"Tài liệu {i}"),
            "preview": meta.get("preview", meta.get("title", "")[:120]),
            "category": meta.get("category", "Văn hóa & Đời sống"),
            "token_count": meta.get("token_count", 0)
        })

    # Tạo đồ thị HNSW 3D đa tầng quy mô lớn (~1.500 nút, ~4.500 cạnh)
    print("[3D Pipeline] Đang sinh Đồ thị HNSW Đa tầng 3D quy mô lớn...")
    hnsw_topology = generate_hnsw_3d_topology(coords_3d, metadata)

    out_dir = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(out_dir, exist_ok=True)

    cache_path = os.path.join(out_dir, "vectors_3d_cache.json")
    pca_matrix_path = os.path.join(out_dir, "pca_3d_projection.json")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump({
            "count": len(vector_cloud),
            "source": source_file,
            "bounds": {"min": -45.0, "max": 45.0},
            "vectors": vector_cloud,
            "hnsw_topology": hnsw_topology
        }, f, ensure_ascii=False)

    with open(pca_matrix_path, "w", encoding="utf-8") as f:
        json.dump({
            "mean": mean_vec.tolist(),
            "components": components.tolist(),
            "scale_factor": float(scale_factor)
        }, f, ensure_ascii=False)

    print(f"[3D Pipeline] Đã xuất thành công:\n -> {cache_path}\n -> {pca_matrix_path}")
    print(f"[3D Pipeline] Thống kê: {len(vector_cloud):,} vector trong đám mây | HNSW: {hnsw_topology['stats']['total_nodes_l0']} nút L0, {hnsw_topology['stats']['total_nodes_l1']} nút L1, {hnsw_topology['stats']['total_nodes_l2']} nút L2 | Tổng cạnh: {hnsw_topology['stats']['total_edges']:,}")


if __name__ == "__main__":
    main()
