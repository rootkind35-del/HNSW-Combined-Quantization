"""Kiểm thử đơn vị cho pipeline thu thập Wikipedia và lượng tử hóa độc lập."""

import os
import tempfile
import pytest
from crawler.extractors.text_cleaner import TextCleaner
from scripts.run_wiki_crawler import clean_wikitext, is_boilerplate_header


def test_clean_wikitext():
    raw_wiki = "{{Hộp thông tin}}\nĐây là [[tiếng Việt|tiếng mẹ đẻ]] của người Việt.<ref>Nguồn chú thích</ref> [http://example.com liên kết]"
    cleaned = clean_wikitext(raw_wiki)
    assert "{{Hộp thông tin}}" not in cleaned
    assert "<ref>" not in cleaned
    assert "tiếng mẹ đẻ" in cleaned
    assert "người Việt" in cleaned


def test_is_boilerplate_header():
    assert is_boilerplate_header("Tham khảo") is True
    assert is_boilerplate_header("Liên kết ngoài") is True
    assert is_boilerplate_header("Lịch sử phát triển") is False
    assert is_boilerplate_header("Địa lý và khí hậu") is False


def test_wiki_quantization_pipeline_run():
    from quantizer.pipeline import QuantizationPipeline
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        input_dir = os.path.join(tmpdir, "crawl_wiki")
        output_dir = os.path.join(tmpdir, "quantized_wiki")
        os.makedirs(input_dir, exist_ok=True)

        shard_file = os.path.join(input_dir, "shard_00000.jsonl")
        with open(shard_file, "w", encoding="utf-8") as f:
            for i in range(15):
                rec = {
                    "doc_id": f"wiki_{i:04d}",
                    "title": f"Bài viết Wikipedia {i}",
                    "url": f"https://vi.wikipedia.org/wiki/Bai_{i}",
                    "content_full": f"Nội dung toàn văn bách khoa toàn thư của mục {i} kiểm thử trên hệ thống lượng tử hóa.",
                    "source": "wikipedia_vi",
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
        assert res["total_vectors"] == 15
        assert os.path.exists(os.path.join(output_dir, "vectors_int8.dat"))
        assert os.path.exists(os.path.join(output_dir, "metadata.jsonl"))
        assert os.path.exists(os.path.join(output_dir, "checkpoint.json"))
