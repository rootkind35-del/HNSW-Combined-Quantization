"""Kiểm thử đơn vị cho kiến trúc ghép nối đa kho vector lượng tử hóa (Zero-Copy Virtual Federation)."""

import json
import os
import tempfile
import numpy as np
import pytest
from quantizer.unified_corpus import UnifiedQuantizedCorpus, create_unified_corpus


def _create_dummy_quantized_corpus(tmpdir: str, name: str, count: int, dim: int = 16):
    corpus_dir = os.path.join(tmpdir, name)
    os.makedirs(corpus_dir, exist_ok=True)

    # 1. Tạo vectors_int8.dat
    np.random.seed(42 if name == "corpus_a" else 99)
    vectors = np.random.randint(-128, 127, size=(count, dim), dtype=np.int8)
    v_path = os.path.join(corpus_dir, "vectors_int8.dat")
    with open(v_path, "wb") as f:
        f.write(vectors.tobytes())

    # 2. Tạo metadata.jsonl
    m_path = os.path.join(corpus_dir, "metadata.jsonl")
    with open(m_path, "w", encoding="utf-8") as f:
        for i in range(count):
            record = {
                "vector_idx": i,
                "doc_id": f"{name}_doc_{i}",
                "title": f"Tiêu đề {name} {i}",
                "text": f"Nội dung văn bản thuộc kho {name} bản ghi thứ {i}",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    # 3. Tạo QUANTIZED_MANIFEST.json
    manifest = {
        "dataset_name": f"Dummy {name}",
        "total_vectors": count,
        "vector_dimension": dim,
        "quantization_type": "Scalar Quantization 8-bit (SQ8)",
        "data_type": "int8 (1 byte per dimension)",
    }
    with open(os.path.join(corpus_dir, "QUANTIZED_MANIFEST.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # 4. Tạo quantization_params.json
    params = {
        "dim": dim,
        "scale": [1.0] * dim,
        "zero_point": [0] * dim,
    }
    with open(os.path.join(corpus_dir, "quantization_params.json"), "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2, ensure_ascii=False)

    return corpus_dir, vectors


def test_unified_corpus_creation_and_indexing():
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_a, vecs_a = _create_dummy_quantized_corpus(tmpdir, "corpus_a", count=30, dim=16)
        dir_b, vecs_b = _create_dummy_quantized_corpus(tmpdir, "corpus_b", count=20, dim=16)
        combined_dir = os.path.join(tmpdir, "combined")

        # 1. Tạo kho hợp nhất
        offset_map = create_unified_corpus(
            corpus_dirs=[dir_a, dir_b],
            output_dir=combined_dir,
            corpus_names=["kho_bao_chi", "kho_wiki"],
        )

        assert offset_map["total_vectors"] == 50
        assert offset_map["dimension"] == 16
        assert len(offset_map["corpora"]) == 2

        # 2. Mở qua UnifiedQuantizedCorpus
        unified = UnifiedQuantizedCorpus(combined_dir)
        assert len(unified) == 50
        assert unified.dim == 16

        # 3. Kiểm tra đọc vector đơn lẻ ranh giới
        # Đầu kho A
        v0 = unified.get_vector(0)
        np.testing.assert_array_equal(v0, vecs_a[0])

        # Cuối kho A
        v29 = unified.get_vector(29)
        np.testing.assert_array_equal(v29, vecs_a[29])

        # Đầu kho B (global_idx 30)
        v30 = unified.get_vector(30)
        np.testing.assert_array_equal(v30, vecs_b[0])

        # Cuối kho B (global_idx 49)
        v49 = unified.get_vector(49)
        np.testing.assert_array_equal(v49, vecs_b[19])

        # 4. Kiểm tra đọc vector theo lô (batch gather) chéo qua 2 kho
        batch_indices = [0, 15, 29, 30, 45, 49]
        batch_vecs = unified.get_vectors(batch_indices)
        assert batch_vecs.shape == (6, 16)
        np.testing.assert_array_equal(batch_vecs[0], vecs_a[0])
        np.testing.assert_array_equal(batch_vecs[1], vecs_a[15])
        np.testing.assert_array_equal(batch_vecs[2], vecs_a[29])
        np.testing.assert_array_equal(batch_vecs[3], vecs_b[0])
        np.testing.assert_array_equal(batch_vecs[4], vecs_b[15])
        np.testing.assert_array_equal(batch_vecs[5], vecs_b[19])

        # 5. Kiểm tra đọc metadata chính xác và ghi nhận đúng nguồn
        meta_0 = unified.get_metadata(0)
        assert meta_0["doc_id"] == "corpus_a_doc_0"
        assert meta_0["corpus_source"] == "kho_bao_chi"

        meta_30 = unified.get_metadata(30)
        assert meta_30["doc_id"] == "corpus_b_doc_0"
        assert meta_30["corpus_source"] == "kho_wiki"

        # 5.1 Kiểm tra đọc metadata theo lô (batch)
        batch_meta = unified.get_metadata_batch([0, 29, 30, 49])
        assert len(batch_meta) == 4
        assert batch_meta[0]["doc_id"] == "corpus_a_doc_0"
        assert batch_meta[29]["doc_id"] == "corpus_a_doc_29"
        assert batch_meta[30]["doc_id"] == "corpus_b_doc_0"
        assert batch_meta[49]["doc_id"] == "corpus_b_doc_19"
        assert batch_meta[0]["corpus_source"] == "kho_bao_chi"
        assert batch_meta[49]["corpus_source"] == "kho_wiki"

        # 6. Kiểm tra duyệt tuần tự iter_vectors
        total_iterated = 0
        for chunk in unified.iter_vectors(batch_size=12):
            total_iterated += len(chunk)
        assert total_iterated == 50

        # 7. Kiểm tra ngoại lệ khi vượt ngưỡng
        with pytest.raises(IndexError):
            unified.get_vector(50)

        with pytest.raises(IndexError):
            unified.get_vector(-1)

        unified.close()
