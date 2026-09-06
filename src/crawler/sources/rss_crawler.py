"""Trình cào tin tức báo chí trực tiếp từ các kênh RSS và tải toàn văn 100% nội dung bài viết."""

import hashlib
import re
import time
import xml.etree.ElementTree as ET
from typing import Dict, Generator, List, Optional
from bs4 import BeautifulSoup
from crawler.config import CrawlerConfig
from crawler.extractors.article_parser import ArticleParser
from crawler.http_client import HttpClient
from ann_data.utils import get_logger

logger = get_logger("crawler.rss_crawler")


class RssNewsCrawler:
    """Thu thập tin tức từ RSS và tải trang bài báo gốc để bóc tách toàn văn nội dung."""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.http_client = HttpClient(self.config)
        self.parser = ArticleParser()
        self.seen_urls = set()

    def parse_rss_feed(self, xml_content: str) -> List[Dict[str, str]]:
        """Bóc tách các item trong tài liệu RSS XML."""
        items = []
        if not xml_content:
            return items

        # Chuẩn hóa các ký tự đặc biệt trong XML
        clean_xml = re.sub(r"&(?![a-zA-Z0-9#]+;)", "&amp;", xml_content)
        try:
            root = ET.fromstring(clean_xml)
        except Exception:
            try:
                root = ET.fromstring(xml_content)
            except Exception as e:
                logger.warning("Lỗi phân tích XML: %s", str(e))
                return items

        for item in root.findall(".//item"):
            title_node = item.find("title")
            link_node = item.find("link")
            desc_node = item.find("description")
            pub_date_node = item.find("pubDate")

            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            link = link_node.text.strip() if link_node is not None and link_node.text else ""
            desc = desc_node.text.strip() if desc_node is not None and desc_node.text else ""
            pub_date = pub_date_node.text.strip() if pub_date_node is not None and pub_date_node.text else ""

            # Loại bỏ mã HTML trong trường mô tả RSS
            if desc:
                desc = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()

            if link:
                items.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "published_at": pub_date,
                })
        return items

    def stream(self, limit: Optional[int] = None) -> Generator[Dict[str, str], None, None]:
        """
        Quét danh sách các kênh RSS và sinh luồng các tài liệu toàn văn.

        Tham số:
            limit: Giới hạn số lượng bài viết tối đa cần lấy.

        Sinh ra:
            Dict chứa 'doc_id', 'url', 'source', 'title', 'summary', 'content_full', 'token_count', 'crawled_at'.
        """
        yielded_count = 0

        for source_name, feed_url in self.config.rss_sources:
            logger.info("Đang nạp kênh RSS: %s (%s)", source_name, feed_url)
            xml_content = self.http_client.get(feed_url)
            if not xml_content:
                continue

            rss_items = self.parse_rss_feed(xml_content)
            logger.info("Tìm thấy %d bài viết từ %s", len(rss_items), source_name)

            for item in rss_items:
                link = item["link"]
                if link in self.seen_urls:
                    continue
                self.seen_urls.add(link)

                # Tải toàn bộ mã HTML trang bài báo để trích xuất thân bài
                html_body = self.http_client.get(link)
                parsed = self.parser.parse(
                    html_content=html_body,
                    fallback_title=item["title"],
                    fallback_desc=item["description"],
                )

                # Bỏ qua nếu nội dung quá ngắn (< 30 từ)
                if parsed["token_count"] < 30:
                    continue

                doc_id = f"news_{hashlib.sha256(link.encode()).hexdigest()[:16]}"
                record = {
                    "doc_id": doc_id,
                    "url": link,
                    "source": source_name,
                    "published_at": item.get("published_at", ""),
                    "title": parsed["title"],
                    "summary": parsed["summary"],
                    "content_full": parsed["content_full"],
                    "token_count": parsed["token_count"],
                    "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                yield record
                yielded_count += 1
                if limit is not None and yielded_count >= limit:
                    logger.info("Đã đạt chỉ tiêu cào tin tức: %d bài viết", limit)
                    return
