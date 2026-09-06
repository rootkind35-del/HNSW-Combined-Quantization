#!/usr/bin/env python
"""Kịch bản xây dựng chỉ mục đồ thị Two-Tier HNSW Tier 1 trên vector int8 và đóng gói tệp nhị phân .graph.bin."""

import argparse
import json
import os
import struct
import sys
import time
from typing import Dict, List, Optional
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.utils import get_logger
from quantizer.unified_corpus import UnifiedQuantizedCorpus

logger = get_logger("scripts.build_ann_graph")

MAGIC_HEADER = b"AGYHNSW1"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Xây dựng đồ thị Small-World Tier 1 trên mảng vector int8 và đóng gói ra tệp nhị phân"
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default="data/quantized_combined",
        help="Thư mục chứa kho vector lượng tử hóa (có thể là kho hợp nhất hoặc kho đơn)",
    )
    parser.add_argument(
        "--output-graph",
        type=str,
        default=None,
        help="Đường dẫn tệp đồ thị nhị phân đầu ra (mặc định đặt tại <corpus-dir>/hnsw_tier1_m{M}.graph.bin)",
    )
    parser.add_argument(
        "-m",
        "--m-links",
        type=int,
        default=32,
        help="Số lượng liên kết tối đa của mỗi nút đỉnh trong đồ thị Small-World",
    )
    parser.add_argument(
        "--ef-construction",
        type=int,
        default=100,
        help="Kích thước hàng đợi ưu tiên trong pha dựng đồ thị",
    )
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=None,
        help="Giới hạn số lượng vector dựng đồ thị (dùng cho các mốc thử nghiệm 100K, 1M, 5M...)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Kích thước lô tính toán tích vô hướng ma trận khối",
    )
    return parser.parse_args()


def save_graph_binary(
    filepath: str,
    graph: Dict[int, List[int]],
    entry_point: int,
    num_vectors: int,
    dim: int,
    m: int,
    ef_construction: int,
):
    """
    Đóng gói cấu trúc đồ thị ra tệp nhị phân siêu gọn:
    - 8 bytes Magic Header: AGYHNSW1
    - 4 bytes Header JSON Length
    - Header JSON string UTF-8
    - Lần lượt cho từng nút i từ 0 đến N-1:
        - 2 bytes (H) uint16: số lượng láng giềng k
        - k * 4 bytes (I) uint32: danh sách ID láng giềng
    """
    header_meta = {
        "num_vectors": num_vectors,
        "dim": dim,
        "m": m,
        "ef_construction": ef_construction,
        "entry_point": entry_point,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    header_bytes = json.dumps(header_meta, ensure_ascii=False).encode("utf-8")

    with open(filepath, "wb") as f:
        f.write(MAGIC_HEADER)
        f.write(struct.pack("<I", len(header_bytes)))
        f.write(header_bytes)

        for i in range(num_vectors):
            neighbors = graph.get(i, [])
            f.write(struct.pack("<H", len(neighbors)))
            if neighbors:
                f.write(struct.pack(f"<{len(neighbors)}I", *neighbors))

    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    logger.info("Đã tuần tự hóa đồ thị ra tệp nhị phân: %s (%.2f MB)", filepath, file_size_mb)


def load_graph_binary(filepath: str) -> Tuple[Dict[int, List[int]], Dict[str, Any]]:
    """Nạp nhanh đồ thị từ tệp nhị phân trong thời gian dưới 1 giây."""
    with open(filepath, "rb") as f:
        magic = f.read(8)
        if magic != MAGIC_HEADER:
            raise ValueError(f"Tệp không đúng định dạng nhị phân HNSW đồ thị: {magic}")

        header_len = struct.unpack("<I", f.read(4))[0]
        header_meta = json.loads(f.read(header_len).decode("utf-8"))

        num_vectors = header_meta["num_vectors"]
        graph = {}
        for i in range(num_vectors):
            count = struct.unpack("<H", f.read(2))[0]
            if count > 0:
                neighbors = list(struct.unpack(f"<{count}I", f.read(count * 4)))
            else:
                neighbors = []
            graph[i] = neighbors

    return graph, header_meta


def build_small_world_graph(
    vectors_int8: np.ndarray,
    m: int = 32,
    batch_size: int = 5000,
) -> Tuple[Dict[int, List[int]], int]:
    """Xây dựng đồ thị Small-World Tier 1 trên mảng vector int8 bằng tính toán ma trận gom lô."""
    num_vectors, dim = vectors_int8.shape
    k_best = min(m, num_vectors - 1)
    graph: Dict[int, List[int]] = {i: [] for i in range(num_vectors)}
    entry_point = 0

    if k_best <= 0:
        return graph, entry_point

    logger.info("Bắt đầu dựng đồ thị cho %d vector (M=%d, Batch=%d)...", num_vectors, m, batch_size)
    t0 = time.time()

    # Chuyển đổi sang float32 theo từng khối để tính tích vô hướng ma trận BLAS
    # ||q - x||^2 = ||q||^2 + ||x||^2 - 2 * <q, x>
    int8_float = vectors_int8.astype(np.float32)
    sq_norms = np.sum(int8_float ** 2, axis=1, keepdims=True)

    for start_idx in range(0, num_vectors, batch_size):
        end_idx = min(start_idx + batch_size, num_vectors)
        chunk_v = int8_float[start_idx:end_idx]
        chunk_sq = sq_norms[start_idx:end_idx]

        # Tính khoảng cách Euclidean bình phương giữa chunk và toàn bộ tập
        chunk_dists = chunk_sq + sq_norms.T - 2.0 * np.dot(chunk_v, int8_float.T)

        for local_i, global_i in enumerate(range(start_idx, end_idx)):
            chunk_dists[local_i, global_i] = np.inf
            nearest = np.argpartition(chunk_dists[local_i], k_best - 1)[:k_best]
            for nb in nearest:
                nb_int = int(nb)
                if nb_int not in graph[global_i]:
                    graph[global_i].append(nb_int)
                if global_i not in graph[nb_int]:
                    graph[nb_int].append(global_i)

        if (start_idx // batch_size + 1) % 5 == 0 or end_idx == num_vectors:
            elapsed = time.time() - t0
            speed = end_idx / max(elapsed, 0.001)
            logger.info("  Tiến độ: %d / %d vector (%.1f%%) - Tốc độ: %.0f vecs/s", end_idx, num_vectors, (end_idx / num_vectors) * 100, speed)

    return graph, entry_point


def main():
    args = parse_args()

    corpus_dir = os.path.abspath(args.corpus_dir)
    map_file = os.path.join(corpus_dir, "corpus_offset_map.json")
    v_file = os.path.join(corpus_dir, "vectors_int8.dat")

    if os.path.exists(map_file):
        logger.info("Nạp dữ liệu từ kho hợp nhất: %s", corpus_dir)
        corpus = UnifiedQuantizedCorpus(corpus_dir)
        total_available = len(corpus)
        dim = corpus.dim
        n_build = min(args.sample_limit, total_available) if args.sample_limit else total_available
        logger.info("Lấy mẫu: %d / %d vector", n_build, total_available)
        vectors_slice = corpus.get_vectors(list(range(n_build)))
        corpus.close()
    elif os.path.exists(v_file):
        logger.info("Nạp dữ liệu từ tệp đơn: %s", v_file)
        dim = 384
        file_bytes = os.path.getsize(v_file)
        total_available = file_bytes // dim
        n_build = min(args.sample_limit, total_available) if args.sample_limit else total_available
        mmap = np.memmap(v_file, dtype="int8", mode="r", shape=(total_available, dim))
        vectors_slice = mmap[:n_build]
    else:
        logger.error("Không tìm thấy dữ liệu vector tại: %s", corpus_dir)
        sys.exit(1)

    if args.output_graph:
        out_graph_path = os.path.abspath(args.output_graph)
    else:
        out_graph_path = os.path.join(corpus_dir, f"hnsw_tier1_m{args.m_links}.graph.bin")

    os.makedirs(os.path.dirname(out_graph_path), exist_ok=True)

    t0 = time.time()
    graph, entry_point = build_small_world_graph(
        vectors_int8=vectors_slice,
        m=args.m_links,
        batch_size=args.batch_size,
    )
    build_time = time.time() - t0

    save_graph_binary(
        filepath=out_graph_path,
        graph=graph,
        entry_point=entry_point,
        num_vectors=len(vectors_slice),
        dim=dim,
        m=args.m_links,
        ef_construction=args.ef_construction,
    )

    manifest_path = os.path.join(corpus_dir, "GRAPH_MANIFEST.json")
    manifest = {
        "graph_file": os.path.basename(out_graph_path),
        "total_nodes": len(vectors_slice),
        "dimension": dim,
        "m": args.m_links,
        "ef_construction": args.ef_construction,
        "entry_point": entry_point,
        "build_time_seconds": round(build_time, 2),
        "file_size_mb": round(os.path.getsize(out_graph_path) / (1024 * 1024), 2),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info("=" * 70)
    logger.info("XÂY DỰNG ĐỒ THỊ THÀNH CÔNG: %d nút trong %.2f giây", len(vectors_slice), build_time)
    logger.info("Đã lưu tệp nhị phân: %s", out_graph_path)
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
