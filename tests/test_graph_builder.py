"""Kiểm thử đơn vị cho bộ xây dựng và tuần tự hóa đồ thị HNSW nhị phân (.graph.bin)."""

import os
import tempfile
import numpy as np
import pytest
from scripts.build_ann_graph import (
    build_small_world_graph,
    load_graph_binary,
    save_graph_binary,
)


def test_build_and_serialize_graph_binary():
    with tempfile.TemporaryDirectory() as tmpdir:
        num_vecs = 60
        dim = 16
        m = 8

        np.random.seed(42)
        vectors_int8 = np.random.randint(-128, 127, size=(num_vecs, dim), dtype=np.int8)

        # 1. Dựng đồ thị
        graph, entry_point = build_small_world_graph(vectors_int8, m=m, batch_size=20)
        assert len(graph) == num_vecs
        assert entry_point == 0
        for node, nbs in graph.items():
            assert len(nbs) >= 1
            assert node not in nbs  # Không tự nối với chính mình

        # 2. Lưu ra file nhị phân
        bin_path = os.path.join(tmpdir, "test_graph.bin")
        save_graph_binary(
            filepath=bin_path,
            graph=graph,
            entry_point=entry_point,
            num_vectors=num_vecs,
            dim=dim,
            m=m,
            ef_construction=50,
        )
        assert os.path.exists(bin_path)
        assert os.path.getsize(bin_path) > 0

        # 3. Nạp lại và kiểm tra tính toàn vẹn
        loaded_graph, meta = load_graph_binary(bin_path)
        assert meta["num_vectors"] == num_vecs
        assert meta["dim"] == dim
        assert meta["m"] == m
        assert meta["entry_point"] == entry_point
        assert len(loaded_graph) == num_vecs

        for node in range(num_vecs):
            assert loaded_graph[node] == graph[node]
