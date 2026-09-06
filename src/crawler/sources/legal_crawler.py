"""Trình thu thập dữ liệu văn bản quy phạm pháp luật và án lệ Việt Nam quy mô lớn."""

import hashlib
import os
import re
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, Generator, List, Optional
from bs4 import BeautifulSoup
from crawler.config import CrawlerConfig
from crawler.extractors.article_parser import ArticleParser
from crawler.extractors.text_cleaner import TextCleaner
from crawler.http_client import HttpClient
from ann_data.utils import get_logger

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logger = get_logger("crawler.legal_crawler")


class LegalCrawler:
    """Thu thập văn bản pháp luật, chính sách, nghị định, thông tư và án lệ Việt Nam."""

    LEGAL_DATASETS = [
        {
            "dataset_name": "hirine/dataset-van-ban-phap-luat-381K-samples",
            "split": "train",
            "text_col": "text",
            "title_col": "title",
            "source_name": "VanBanPhapLuat/381K",
        },
        {
            "dataset_name": "thangvip/combined-vietnamese-legal-text",
            "split": "train",
            "text_col": "text",
            "title_col": None,
            "source_name": "VietnameseLegalCorpus",
        },
    ]

    LEGAL_RSS = [
        ("Thu Vien Phap Luat - Chinh Sach Moi", "https://thuvienphapluat.vn/rss/chinh-sach-phap-luat-moi.rss"),
        ("Thu Vien Phap Luat - Thoi Su Phap Luat", "https://thuvienphapluat.vn/rss/thoi-su-phap-luat.rss"),
        ("Thu Vien Phap Luat - An Le", "https://thuvienphapluat.vn/rss/an-le.rss"),
        ("Luat Viet Nam - Van Ban Moi", "https://luatvietnam.vn/rss/van-ban-moi.rss"),
        ("Luat Viet Nam - Chinh Sach Moi", "https://luatvietnam.vn/rss/chinh-sach-moi.rss"),
    ]

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.http_client = HttpClient(self.config)
        self.parser = ArticleParser()
        self.cleaner = TextCleaner()
        self.seen_hashes = set()

    def stream_legal_datasets(self, limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Nạp luồng các kho văn bản pháp luật mở quy mô lớn (hơn 400.000 văn bản pháp quy)."""
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("Thư viện 'datasets' chưa được cài đặt.")
            return

        yielded = 0
        for ds_info in self.LEGAL_DATASETS:
            d_name = ds_info["dataset_name"]
            split = ds_info["split"]
            t_col = ds_info["text_col"]
            title_col = ds_info["title_col"]
            s_name = ds_info["source_name"]

            logger.info("Đang nạp kho văn bản pháp luật mở: %s", d_name)
            try:
                ds = load_dataset(d_name, split=split, streaming=True)
                for item in ds:
                    raw_text = item.get(t_col, "")
                    if not raw_text or len(raw_text) < 60:
                        continue

                    cleaned = self.cleaner.clean(raw_text)
                    tokens = cleaned.split()
                    if len(tokens) < 25:
                        continue

                    doc_hash = hashlib.sha256(cleaned[:250].encode()).hexdigest()[:16]
                    if doc_hash in self.seen_hashes:
                        continue
                    self.seen_hashes.add(doc_hash)

                    if title_col and item.get(title_col):
                        title = str(item.get(title_col)).strip()[:150]
                    else:
                        lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
                        title = lines[0][:150] if lines else "Văn bản pháp luật"

                    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
                    summary = lines[1][:300] if len(lines) > 1 else lines[0][:300]

                    record = {
                        "doc_id": f"law_{doc_hash}",
                        "url": f"https://huggingface.co/datasets/{d_name}",
                        "source": s_name,
                        "published_at": "",
                        "title": title,
                        "summary": summary,
                        "content_full": cleaned,
                        "token_count": len(tokens),
                        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }

                    yield record
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        logger.info("Đã đạt chỉ tiêu văn bản pháp luật: %d tài liệu", limit)
                        return

            except Exception as e:
                logger.warning("Không thể đọc kho pháp luật %s: %s", d_name, str(e))
                continue

    def stream_live_rss(self, limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Cào các văn bản mới và phân tích pháp luật thời sự từ Thư Viện Pháp Luật và Luật Việt Nam."""
        yielded = 0
        for source_name, feed_url in self.LEGAL_RSS:
            logger.info("Đang quét kênh RSS pháp luật: %s", source_name)
            xml_content = self.http_client.get(feed_url)
            if not xml_content:
                continue

            clean_xml = re.sub(r"&(?!([a-zA-Z0-9#]+;))", "&amp;", xml_content)
            try:
                root = ET.fromstring(clean_xml)
            except Exception:
                try:
                    root = ET.fromstring(xml_content)
                except Exception as e:
                    logger.warning("Lỗi giải mã XML RSS pháp luật: %s", str(e))
                    continue

            for item in root.findall(".//item"):
                title_node = item.find("title")
                link_node = item.find("link")
                desc_node = item.find("description")
                pub_date_node = item.find("pubDate")

                title = title_node.text.strip() if title_node is not None and title_node.text else ""
                link = link_node.text.strip() if link_node is not None and link_node.text else ""
                desc = desc_node.text.strip() if desc_node is not None and desc_node.text else ""
                pub_date = pub_date_node.text.strip() if pub_date_node is not None and pub_date_node.text else ""

                if not link:
                    continue

                doc_hash = hashlib.sha256(link.encode()).hexdigest()[:16]
                if doc_hash in self.seen_hashes:
                    continue
                self.seen_hashes.add(doc_hash)

                html_body = self.http_client.get(link)
                parsed = self.parser.parse(
                    html_content=html_body,
                    fallback_title=title,
                    fallback_desc=desc,
                )

                if parsed["token_count"] < 30:
                    continue

                record = {
                    "doc_id": f"law_{doc_hash}",
                    "url": link,
                    "source": source_name,
                    "published_at": pub_date,
                    "title": parsed["title"],
                    "summary": parsed["summary"],
                    "content_full": parsed["content_full"],
                    "token_count": parsed["token_count"],
                    "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                }

                yield record
                yielded += 1
                if limit is not None and yielded >= limit:
                    return

    def stream(self, limit: Optional[int] = None) -> Generator[Dict[str, Any], None, None]:
        """Phát luồng tổng hợp: Cào tin mới trực tuyến rồi nạp toàn bộ kho văn bản pháp quy."""
        count = 0
        for rec in self.stream_live_rss(limit=limit):
            yield rec
            count += 1
            if limit is not None and count >= limit:
                return

        remaining = limit - count if limit is not None else None
        for rec in self.stream_legal_datasets(limit=remaining):
            yield rec
            count += 1
            if limit is not None and count >= limit:
                return
