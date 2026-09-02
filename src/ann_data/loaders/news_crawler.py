"""Module cào tin tức báo chí tiếng Việt qua RSS và trích xuất nội dung bài viết."""

import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Generator, List, Optional, Tuple
from bs4 import BeautifulSoup
from ann_data.loaders.base import BaseDataLoader
from ann_data.utils import get_logger


class NewsRssCrawler(BaseDataLoader):
    """Trình cào tin tức tiếng Việt thời sự từ các kênh RSS chính thống (VnExpress, Dân Trí) và bóc tách nội dung chi tiết."""

    DEFAULT_FEEDS = [
        "https://vnexpress.net/rss/tin-moi-nhat.rss",
        "https://dantri.com.vn/rss/home.rss",
    ]

    def __init__(self, feed_urls: Optional[List[str]] = None, request_timeout: int = 10):
        """
        Khởi tạo trình cào báo.

        Tham số:
            feed_urls: Danh sách các đường dẫn RSS cần quét.
            request_timeout: Thời gian chờ HTTP tối đa tính bằng giây (mặc định 10s).
        """
        self.feed_urls = feed_urls or self.DEFAULT_FEEDS
        self.request_timeout = request_timeout
        self.logger = get_logger("NewsRssCrawler")
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Tải nội dung phản hồi văn bản thô từ một URL qua phương thức HTTP GET.

        Tham số:
            url: Đường dẫn URL cần truy cập.

        Trả về:
            Chuỗi văn bản nội dung HTML/XML hoặc None nếu xảy ra lỗi kết nối.
        """
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self._user_agent, "Accept": "text/html,application/xhtml+xml,application/xml"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as e:
            self.logger.warning("Không thể tải URL %s: %s", url, str(e))
            return None

    @staticmethod
    def parse_rss_xml(xml_content: str) -> List[Dict[str, str]]:
        """
        Phân tích chuỗi XML của kênh RSS thành danh sách các bản ghi tin tức (tiêu đề, link, mô tả).

        Tham số:
            xml_content: Chuỗi nội dung XML.

        Trả về:
            Danh sách các dictionary chứa thông tin từng bài viết.
        """
        items = []
        if not xml_content:
            return items

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            # Làm sạch tiền tố mã hóa hoặc các ký tự đặc biệt nếu có
            clean_xml = re.sub(r"&(?![a-zA-Z0-9#]+;)", "&amp;", xml_content)
            try:
                root = ET.fromstring(clean_xml)
            except Exception:
                return items

        # Quét toàn bộ các phần tử item trong tài liệu RSS
        for item in root.findall(".//item"):
            title_node = item.find("title")
            link_node = item.find("link")
            desc_node = item.find("description")
            guid_node = item.find("guid")

            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            link = link_node.text.strip() if link_node is not None and link_node.text else ""
            desc = desc_node.text.strip() if desc_node is not None and desc_node.text else ""
            guid = guid_node.text.strip() if guid_node is not None and guid_node.text else link

            # Bóc tách mã HTML trong trường mô tả RSS
            if desc:
                desc = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()

            if title or link:
                items.append({
                    "title": title,
                    "link": link,
                    "description": desc,
                    "guid": guid,
                })
        return items

    @staticmethod
    def extract_article_content(html_content: str) -> str:
        """
        Trích xuất văn bản thân bài báo từ tài liệu HTML thô.

        Tham số:
            html_content: Chuỗi mã nguồn HTML bài báo.

        Trả về:
            Chuỗi văn bản thân bài báo đã được bóc tách và ghép nối từ các đoạn văn.
        """
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Loại bỏ các thẻ không chứa nội dung chính như script, quảng cáo, menu
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "figure"]):
            tag.decompose()

        # Nhắm mục tiêu vào các vùng class chứa nội dung báo chí tiếng Việt phổ biến
        article_candidates = (
            soup.find("article")
            or soup.find(class_=re.compile(r"(fck_detail|singular-content|article-content|detail-content)"))
            or soup.body
        )

        if not article_candidates:
            return ""

        paragraphs = [
            p.get_text(strip=True)
            for p in article_candidates.find_all("p")
            if len(p.get_text(strip=True)) > 20
        ]
        return "\n".join(paragraphs)

    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        """
        Thu thập các kênh tin tức và sinh ra luồng các cặp (doc_id, full_text).

        Tham số:
            limit: Số lượng bài báo tối đa cần cào.

        Sinh ra:
            Tuple[str, str]: (doc_id, full_text)
        """
        yielded_count = 0

        for feed_url in self.feed_urls:
            self.logger.info("Đang nạp kênh RSS: %s", feed_url)
            xml_text = self.fetch_url(feed_url)
            if not xml_text:
                continue

            items = self.parse_rss_xml(xml_text)
            self.logger.info("Phân tích thành công %d bài viết từ %s", len(items), feed_url)

            for item in items:
                link = item.get("link", "")
                title = item.get("title", "")
                description = item.get("description", "")

                doc_id = hashlib.sha1(link.encode("utf-8") if link else title.encode("utf-8")).hexdigest()[:16]

                # Tải chi tiết bài viết nếu có đường dẫn hợp lệ, nếu không lấy tiêu đề + mô tả
                body_text = ""
                if link.startswith("http"):
                    html = self.fetch_url(link)
                    if html:
                        body_text = self.extract_article_content(html)

                full_text = f"{title}\n{description}\n{body_text}".strip()

                if len(full_text) > 10:
                    yield doc_id, full_text
                    yielded_count += 1
                    if limit is not None and yielded_count >= limit:
                        return

