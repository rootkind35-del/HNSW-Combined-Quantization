"""Unit tests for NewsRssCrawler module."""

import unittest
from unittest.mock import patch
from ann_data.loaders.news_crawler import NewsRssCrawler


class TestNewsRssCrawler(unittest.TestCase):

    def setUp(self):
        self.crawler = NewsRssCrawler(feed_urls=["https://test.vn/rss/tin-moi.rss"])
        self.sample_rss = """<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
            <channel>
                <title>Báo Điện Tử Mẫu</title>
                <item>
                    <title>Bài viết số 1: Trí tuệ nhân tạo</title>
                    <link>https://test.vn/bai-viet-1</link>
                    <description><![CDATA[Tóm tắt bài viết số 1 về nghiên cứu trí tuệ nhân tạo.]]></description>
                    <guid>https://test.vn/bai-viet-1</guid>
                </item>
                <item>
                    <title>Bài viết số 2: Khoa học máy tính</title>
                    <link>https://test.vn/bai-viet-2</link>
                    <description>Tóm tắt bài viết số 2 về cấu trúc dữ liệu và giải thuật.</description>
                    <guid>https://test.vn/bai-viet-2</guid>
                </item>
            </channel>
        </rss>
        """
        self.sample_article_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <header><nav>Menu thanh điều hướng không lấy</nav></header>
            <article class="article-content">
                <p class="Normal">Đoạn văn thứ nhất nói về thuật toán HNSW trên không gian nhiều chiều.</p>
                <p class="Normal">Đoạn văn thứ hai trình bày về kỹ thuật lượng tử hóa vector và bộ nhớ đệm.</p>
            </article>
            <footer>Chân trang không lấy</footer>
        </body>
        </html>
        """

    def test_parse_rss_xml(self):
        items = NewsRssCrawler.parse_rss_xml(self.sample_rss)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "Bài viết số 1: Trí tuệ nhân tạo")
        self.assertEqual(items[0]["link"], "https://test.vn/bai-viet-1")
        self.assertIn("nghiên cứu trí tuệ nhân tạo", items[0]["description"])
        self.assertEqual(items[1]["title"], "Bài viết số 2: Khoa học máy tính")

    def test_parse_empty_or_malformed_xml(self):
        self.assertEqual(NewsRssCrawler.parse_rss_xml(""), [])
        self.assertEqual(NewsRssCrawler.parse_rss_xml("<<<invalid xml>>>"), [])

    def test_extract_article_content(self):
        content = NewsRssCrawler.extract_article_content(self.sample_article_html)
        self.assertNotIn("Menu thanh điều hướng", content)
        self.assertNotIn("Chân trang", content)
        self.assertIn("thuật toán HNSW", content)
        self.assertIn("lượng tử hóa vector", content)

    @patch.object(NewsRssCrawler, "fetch_url")
    def test_stream_with_mock_network(self, mock_fetch):
        # First call fetches feed XML, subsequent calls fetch article HTML
        mock_fetch.side_effect = [
            self.sample_rss,
            self.sample_article_html,
            self.sample_article_html,
        ]

        stream_items = list(self.crawler.stream(limit=1))
        self.assertEqual(len(stream_items), 1)
        doc_id, text = stream_items[0]
        self.assertTrue(len(doc_id) > 0)
        self.assertIn("Trí tuệ nhân tạo", text)
        self.assertIn("thuật toán HNSW", text)


if __name__ == "__main__":
    unittest.main()
