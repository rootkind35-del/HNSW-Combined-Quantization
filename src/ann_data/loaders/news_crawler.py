"""News RSS crawler and article extractor module."""

import hashlib
import re
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Generator, List, Optional, Tuple
from bs4 import BeautifulSoup
from ann_data.loaders.base import BaseDataLoader
from ann_data.utils import get_logger


class NewsRssCrawler(BaseDataLoader):
    """Crawls latest Vietnamese news articles from RSS feeds and extracts clean body text."""

    DEFAULT_FEEDS = [
        "https://vnexpress.net/rss/tin-moi-nhat.rss",
        "https://dantri.com.vn/rss/home.rss",
    ]

    def __init__(self, feed_urls: Optional[List[str]] = None, request_timeout: int = 10):
        self.feed_urls = feed_urls or self.DEFAULT_FEEDS
        self.request_timeout = request_timeout
        self.logger = get_logger("NewsRssCrawler")
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

    def fetch_url(self, url: str) -> Optional[str]:
        """Fetches raw text content from a URL via HTTP GET."""
        req = urllib.request.Request(
            url,
            headers={"User-Agent": self._user_agent, "Accept": "text/html,application/xhtml+xml,application/xml"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except Exception as e:
            self.logger.warning("Failed to fetch %s: %s", url, str(e))
            return None

    @staticmethod
    def parse_rss_xml(xml_content: str) -> List[Dict[str, str]]:
        """Parses an RSS XML string into a list of item dictionaries."""
        items = []
        if not xml_content:
            return items

        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError:
            # Attempt to clean encoding prefix or bad tokens if any
            clean_xml = re.sub(r"&(?![a-zA-Z0-9#]+;)", "&amp;", xml_content)
            try:
                root = ET.fromstring(clean_xml)
            except Exception:
                return items

        # Search for all item elements under channel or root
        for item in root.findall(".//item"):
            title_node = item.find("title")
            link_node = item.find("link")
            desc_node = item.find("description")
            guid_node = item.find("guid")

            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            link = link_node.text.strip() if link_node is not None and link_node.text else ""
            desc = desc_node.text.strip() if desc_node is not None and desc_node.text else ""
            guid = guid_node.text.strip() if guid_node is not None and guid_node.text else link

            # Description in RSS often contains HTML or CDATA; strip basic tags
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
        """Extracts article text from raw HTML body."""
        if not html_content:
            return ""

        soup = BeautifulSoup(html_content, "html.parser")

        # Strip non-content elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "figure"]):
            tag.decompose()

        # Target standard Vietnamese news content classes and tags
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
        """Crawls feeds and streams (doc_id, text) pairs."""
        yielded_count = 0

        for feed_url in self.feed_urls:
            self.logger.info("Fetching feed: %s", feed_url)
            xml_text = self.fetch_url(feed_url)
            if not xml_text:
                continue

            items = self.parse_rss_xml(xml_text)
            self.logger.info("Parsed %d items from %s", len(items), feed_url)

            for item in items:
                link = item.get("link", "")
                title = item.get("title", "")
                description = item.get("description", "")

                doc_id = hashlib.sha1(link.encode("utf-8") if link else title.encode("utf-8")).hexdigest()[:16]

                # Fetch full article if link available, else fallback to title + description
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
