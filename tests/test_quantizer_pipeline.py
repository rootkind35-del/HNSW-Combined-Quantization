"""Kiểm thử đơn vị cho thư viện quantizer (ScalarQuantizer8, TextChunker, QuantizedStorage)."""

import os
import tempfile
import numpy as np
import pytest
from quantizer.chunker import TextChunker
from quantizer.sq8 import ScalarQuantizer8
from quantizer.storage import QuantizedStorage


def test_scalar_quantizer_sq8():
    quantizer = ScalarQuantizer8()
    np.random.seed(42)
    vectors = np.random.randn(50, 64).astype(np.float32)

    quantized = quantizer.quantize(vectors)
    assert quantized.shape == (50, 64)
    assert quantized.dtype == np.int8

    reconstructed = quantizer.dequantize(quantized)
    assert reconstructed.shape == (50, 64)
    assert reconstructed.dtype == np.float32

    metrics = quantizer.compute_reconstruction_error(vectors)
    assert metrics["mse_loss"] < 0.05
    assert metrics["mean_cosine_similarity"] > 0.98
    assert metrics["ram_saving_percent"] == 75.0


def test_text_chunker():
    chunker = TextChunker(chunk_size=10, chunk_overlap=3)
    long_text = " ".join([f"từ_{i}" for i in range(25)])
    chunks = chunker.chunk_document(doc_id="doc_1", title="Tiêu đề", full_text=long_text)

    assert len(chunks) >= 3
    assert chunks[0]["chunk_id"] == "doc_1_c0"
    assert chunks[1]["chunk_id"] == "doc_1_c1"
    # Đoạn 1 và 2 phải có từ gối đầu
    words_c0 = set(chunks[0]["text"].split())
    words_c1 = set(chunks[1]["text"].split())
    assert len(words_c0.intersection(words_c1)) >= 2


def test_quantized_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = QuantizedStorage(output_dir=tmpdir, dim=8, max_capacity=100)
        storage.initialize_storage(mode="w+")

        int8_vecs = np.random.randint(-128, 127, size=(5, 8), dtype=np.int8)
        metadata = [{"doc_id": f"d_{i}", "text": f"Đoạn {i}"} for i in range(5)]

        storage.append_batch(int8_vecs, metadata)
        storage.close()

        manifest = storage.update_manifest()
        assert manifest["total_vectors"] == 5
        assert manifest["vector_dimension"] == 8
        assert os.path.exists(os.path.join(tmpdir, "QUANTIZED_MANIFEST.json"))


def test_quantizer_process_vector_file():
    from quantizer.pipeline import QuantizationPipeline

    with tempfile.TemporaryDirectory() as tmpdir:
        vec_file = os.path.join(tmpdir, "raw_vectors.dat")
        n_vecs = 200
        dim = 16
        raw_data = np.random.randn(n_vecs, dim).astype(np.float32)
        raw_mmap = np.memmap(vec_file, dtype="float32", mode="w+", shape=(n_vecs, dim))
        raw_mmap[:] = raw_data[:]
        raw_mmap.flush()
        del raw_mmap

        out_dir = os.path.join(tmpdir, "quantized_out")
        pipeline = QuantizationPipeline(output_dir=out_dir, dim=dim)
        res = pipeline.process_vector_file(vector_file_path=vec_file, batch_size=50)

        assert res["total_vectors"] == n_vecs
        int8_out = os.path.join(out_dir, "vectors_int8.dat")
        assert os.path.exists(int8_out)
        assert os.path.getsize(int8_out) == n_vecs * dim * 1  # 1 byte per dimension
        assert os.path.exists(os.path.join(out_dir, "QUANTIZED_MANIFEST.json"))
        assert os.path.exists(os.path.join(out_dir, "quantization_params.json"))


def test_quantizer_process_with_shards_and_checkpoint():
    import json
    from quantizer.pipeline import QuantizationPipeline

    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "crawl")
        output_dir = os.path.join(tmpdir, "quantized")
        os.makedirs(input_dir, exist_ok=True)

        # Tạo 2 shard giả lập
        for s_idx in range(2):
            s_file = os.path.join(input_dir, f"shard_{s_idx:05d}.jsonl")
            with open(s_file, "w", encoding="utf-8") as f:
                for i in range(10):
                    rec = {
                        "doc_id": f"s{s_idx}_d{i}",
                        "title": f"Tiêu đề {s_idx}_{i}",
                        "content_full": f"Nội dung bài viết thứ {i} thuộc shard {s_idx} dùng để kiểm tra lượng tử hóa.",
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        pipeline = QuantizationPipeline(
            input_dir=input_dir,
            output_dir=output_dir,
            dim=16,
            batch_size=4,
            use_mock_embedder=True,
        )

        res = pipeline.process(resume=True)
        assert res["total_vectors"] == 20
        assert os.path.exists(os.path.join(output_dir, "vectors_int8.dat"))
        assert os.path.exists(os.path.join(output_dir, "checkpoint.json"))
        assert os.path.exists(os.path.join(output_dir, "QUANTIZED_MANIFEST.json"))

        # Chạy lại với resume: các shard đã xong sẽ được bỏ qua
        res_resume = pipeline.process(resume=True)
        assert res_resume["total_vectors"] == 20


