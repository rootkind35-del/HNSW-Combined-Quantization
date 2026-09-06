"""Kiểm thử đơn vị cho thư viện crawler (ArticleParser, TextCleaner, ShardWriter)."""

import os
import tempfile
import pytest
from crawler.extractors.article_parser import ArticleParser
from crawler.extractors.text_cleaner import TextCleaner
from crawler.storage.shard_writer import ShardWriter


def test_text_cleaner():
    cleaner = TextCleaner()
    raw = "  Tiêu   đề \u200b bài \ufeff viết \n\n\n đoạn  1  "
    cleaned = cleaner.clean(raw)
    assert "\u200b" not in cleaned
    assert "\ufeff" not in cleaned
    assert "Tiêu đề bài viết" in cleaned
    assert "đoạn 1" in cleaned


def test_article_parser_full_text():
    parser = ArticleParser()
    sample_html = """
    <html>
        <head><title>Tiêu đề trang</title></head>
        <body>
            <header><nav>Menu navigation</nav></header>
            <article class="fck_detail">
                <h1>Tiêu đề bài báo chính thức</h1>
                <p class="description">Đoạn tóm tắt mở đầu bài báo.</p>
                <p>Đoạn thân bài số 1 có nội dung chi tiết về kinh tế và công nghệ.</p>
                <p>Đoạn thân bài số 2 tiếp tục phân tích sâu về các giải pháp.</p>
                <script>var ads = 1;</script>
            </article>
            <footer>Footer bản quyền</footer>
        </body>
    </html>
    """
    result = parser.parse(sample_html)
    assert "Tiêu đề bài báo chính thức" in result["title"]
    assert "Đoạn tóm tắt mở đầu" in result["summary"]
    assert "Đoạn thân bài số 1" in result["content_full"]
    assert "Đoạn thân bài số 2" in result["content_full"]
    assert "Menu navigation" not in result["content_full"]
    assert "Footer bản quyền" not in result["content_full"]
    assert result["token_count"] > 25


def test_shard_writer():
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ShardWriter(output_dir=tmpdir, shard_size=2)
        writer.write({"doc_id": "1", "title": "A", "content_full": "Nội dung 1"})
        writer.write({"doc_id": "2", "title": "B", "content_full": "Nội dung 2"})
        # Đạt shard_size=2, sẽ chuyển shard tiếp theo
        writer.write({"doc_id": "3", "title": "C", "content_full": "Nội dung 3"})
        writer.close()

        manifest = writer.update_manifest()
        assert manifest["total_documents"] == 3
        assert manifest["total_shards"] == 2
        assert os.path.exists(os.path.join(tmpdir, "CRAWL_MANIFEST.json"))


def test_hf_streamer_record_structure(monkeypatch):
    from unittest.mock import MagicMock
    from crawler.sources.hf_streamer import HuggingFaceStreamer

    # Mock datasets.load_dataset
    mock_items = [
        {"text": "Tiêu đề bài báo một.\nĐoạn văn chi tiết về nghiên cứu khoa học và công nghệ xử lý dữ liệu lớn."},
        {"text": "Tiêu đề bài báo hai.\nĐoạn văn thứ hai chứa nhiều thông tin hữu ích về lượng tử hóa vector."},
        {"text": "Quá ngắn"},  # Sẽ bị bỏ qua do < 50 ký tự
    ]

    mock_load = MagicMock(return_value=iter(mock_items))
    import datasets
    monkeypatch.setattr(datasets, "load_dataset", mock_load)

    streamer = HuggingFaceStreamer(sources=[{"dataset_name": "mock/ds", "config_name": None, "text_column": "text"}])
    records = list(streamer.stream(limit=5))

    assert len(records) == 2
    assert records[0]["title"] == "Tiêu đề bài báo một."
    assert "nghiên cứu khoa học" in records[0]["content_full"]
    assert records[0]["token_count"] >= 15
    assert records[0]["doc_id"].startswith("hf_")


def test_crawler_pipeline_integration(monkeypatch):
    from unittest.mock import MagicMock
    from crawler import CrawlerConfig, CrawlerPipeline

    mock_items = [
        {"text": f"Tiêu đề tài liệu số {i}.\nNội dung toàn văn chi tiết của tài liệu số {i} với độ dài đủ lớn để được lập chỉ mục."}
        for i in range(5)
    ]

    mock_load = MagicMock(return_value=iter(mock_items))
    import datasets
    monkeypatch.setattr(datasets, "load_dataset", mock_load)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = CrawlerConfig(output_dir=tmpdir, shard_size=2)
        pipeline = CrawlerPipeline(config=config)
        res = pipeline.run_hf_streaming(limit=4)

        assert res["records_added"] == 4
        manifest_path = os.path.join(tmpdir, "CRAWL_MANIFEST.json")
        assert os.path.exists(manifest_path)


def test_legal_crawler_record_structure(monkeypatch):
    from unittest.mock import MagicMock
    from crawler.sources.legal_crawler import LegalCrawler

    mock_legal_items = [
        {
            "title": "Nghị định số 123/2024/NĐ-CP",
            "text": "Nghị định số 123/2024/NĐ-CP quy định chi tiết thi hành một số điều của Luật Đất đai về bồi thường, hỗ trợ, tái định cư khi Nhà nước thu hồi đất.",
        },
        {
            "title": "Thông tư số 05/2024/TT-BTP",
            "text": "Thông tư số 05/2024/TT-BTP của Bộ Tư pháp hướng dẫn về trợ giúp pháp lý cho người yếu thế trong xã hội theo quy định hiện hành.",
        },
    ]

    mock_load = MagicMock(return_value=iter(mock_legal_items))
    import datasets
    monkeypatch.setattr(datasets, "load_dataset", mock_load)

    crawler = LegalCrawler()
    records = list(crawler.stream_legal_datasets(limit=5))

    assert len(records) == 2
    assert records[0]["doc_id"].startswith("law_")
    assert "Nghị định số 123/2024/NĐ-CP" in records[0]["title"]
    assert "Luật Đất đai" in records[0]["content_full"]
    assert records[0]["token_count"] >= 20


def test_crawler_pipeline_full_crawl(monkeypatch):
    from crawler import CrawlerConfig, CrawlerPipeline
    from crawler.sources.rss_crawler import RssNewsCrawler
    from crawler.sources.legal_crawler import LegalCrawler
    from crawler.sources.hf_streamer import HuggingFaceStreamer

    # Mock các nguồn sinh bản ghi
    def mock_rss_stream(self, limit=None):
        for i in range(2):
            yield {"doc_id": f"news_{i}", "title": f"Tin tức {i}", "content_full": f"Nội dung báo chí bài viết {i}"}

    def mock_legal_stream(self, limit=None):
        for i in range(2):
            yield {"doc_id": f"law_{i}", "title": f"Luật {i}", "content_full": f"Nội dung văn bản quy phạm {i}"}

    def mock_hf_stream(self, limit=None):
        for i in range(2):
            yield {"doc_id": f"hf_{i}", "title": f"Bách khoa {i}", "content_full": f"Nội dung bách khoa toàn thư {i}"}

    monkeypatch.setattr(RssNewsCrawler, "stream", mock_rss_stream)
    monkeypatch.setattr(LegalCrawler, "stream", mock_legal_stream)
    monkeypatch.setattr(HuggingFaceStreamer, "stream", mock_hf_stream)

    with tempfile.TemporaryDirectory() as tmpdir:
        config = CrawlerConfig(output_dir=tmpdir, shard_size=2)
        pipeline = CrawlerPipeline(config=config)
        res = pipeline.run_full_crawl(limit=6)

        assert res["records_added"] == 6
        manifest_path = os.path.join(tmpdir, "CRAWL_MANIFEST.json")
        assert os.path.exists(manifest_path)


