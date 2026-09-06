"""Kiểm thử đơn vị cho BenchmarkDatasetLoader và các hàm đọc fvecs / ivecs."""

import os
import tempfile
import numpy as np
import pytest
from ann_data.loaders.benchmark_loader import (
    BenchmarkDatasetLoader,
    read_fvecs,
    read_ivecs,
)


def test_read_fvecs_synthetic():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.fvecs")
        dim = 8
        num_vecs = 10
        vectors = np.random.randn(num_vecs, dim).astype(np.float32)

        with open(file_path, "wb") as f:
            for vec in vectors:
                np.int32(dim).tofile(f)
                vec.tofile(f)

        loaded = read_fvecs(file_path)
        assert loaded.shape == (num_vecs, dim)
        np.testing.assert_allclose(loaded, vectors, rtol=1e-5)

        # Kiểm tra giới hạn max_vectors
        loaded_sub = read_fvecs(file_path, max_vectors=4)
        assert loaded_sub.shape == (4, dim)


def test_read_ivecs_synthetic():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.ivecs")
        k = 5
        num_queries = 6
        indices = np.random.randint(0, 100, size=(num_queries, k), dtype=np.int32)

        with open(file_path, "wb") as f:
            for row in indices:
                np.int32(k).tofile(f)
                row.tofile(f)

        loaded = read_ivecs(file_path)
        assert loaded.shape == (num_queries, k)
        np.testing.assert_array_equal(loaded, indices)


def test_benchmark_loader_local():
    loader = BenchmarkDatasetLoader(base_dir="data/raw/benchmarks")
    # Tập sift10k đã tải ở bước trước
    if os.path.exists("data/raw/benchmarks/siftsmall/siftsmall_base.fvecs"):
        data = loader.load_dataset("sift10k", max_base=100)
        assert data["base"].shape == (100, 128)
        assert data["query"].shape[1] == 128
        assert data["groundtruth"].shape[1] == 100
