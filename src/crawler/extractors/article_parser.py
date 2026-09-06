"""Bộ bóc tách bài báo trích xuất toàn văn 100% nội dung bài viết từ mã HTML."""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from crawler.extractors.text_cleaner import TextCleaner


class ArticleParser:
    """Trích xuất tiêu đề, mô tả tóm tắt và toàn bộ nội dung thân bài báo từ HTML."""

    # Danh sách các class chứa nội dung bài báo phổ biến tại Việt Nam
    CONTENT_SELECTORS = [
        "article",
        ".fck_detail",             # VnExpress
        ".singular-content",        # Dân Trí
        ".article-content",         # VietnamNet
        ".detail-content",          # Tuổi Trẻ
        ".content-detail",          # Thanh Niên
        ".post-content",
        ".entry-content",
        "[itemprop='articleBody']",
        "main",
    ]

    # Các thẻ không chứa nội dung chính cần loại bỏ
    STRIP_TAGS = [
        "script", "style", "nav", "footer", "header", "aside",
        "figure", "form", "iframe", "noscript", "svg", "button"
    ]

    def __init__(self):
        self.cleaner = TextCleaner()

    def parse(self, html_content: str, fallback_title: str = "", fallback_desc: str = "") -> Dict[str, str]:
        """
        Bóc tách toàn văn tài liệu HTML.

        Tham số:
            html_content: Mã nguồn HTML thô.
            fallback_title: Tiêu đề dự phòng nếu không tìm thấy trong HTML.
            fallback_desc: Mô tả dự phòng nếu không tìm thấy trong HTML.

        Trả về:
            Dict chứa 'title', 'summary', 'content_full', 'token_count'.
        """
        if not html_content:
            return {
                "title": self.cleaner.clean(fallback_title),
                "summary": self.cleaner.clean(fallback_desc),
                "content_full": self.cleaner.clean(f"{fallback_title}\n\n{fallback_desc}"),
                "token_count": len(f"{fallback_title} {fallback_desc}".split()),
            }

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Trích xuất tiêu đề bài báo
        title = ""
        title_node = soup.find("h1") or soup.find("title")
        if title_node:
            title = title_node.get_text(strip=True)
        if not title:
            meta_title = soup.find("meta", property="og:title")
            if meta_title and meta_title.get("content"):
                title = meta_title["content"].strip()
        if not title:
            title = fallback_title

        # 2. Trích xuất đoạn mô tả / Sapo (Lead / Summary)
        summary = ""
        meta_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            summary = meta_desc["content"].strip()
        if not summary:
            sapo_node = soup.find(class_=re.compile(r"(sapo|description|lead)", re.I))
            if sapo_node:
                summary = sapo_node.get_text(strip=True)
        if not summary:
            summary = fallback_desc

        # 3. Loại bỏ các thẻ rác
        for tag_name in self.STRIP_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # 4. Tìm vùng chứa thân bài báo
        article_body = None
        for selector in self.CONTENT_SELECTORS:
            article_body = soup.select_one(selector)
            if article_body:
                break

        if not article_body:
            article_body = soup.body or soup

        # 5. Thu thập toàn bộ các đoạn văn bản (paragraphs) không giới hạn độ dài
        paragraphs: List[str] = []
        for p in article_body.find_all("p"):
            p_text = p.get_text(separator=" ", strip=True)
            # Lọc bỏ các đoạn quá ngắn như chú thích ảnh ngắn, quảng cáo
            if len(p_text) > 25 and not re.search(r"^(Ảnh|Video|Nguồn|Theo|Từ khóa):", p_text):
                paragraphs.append(p_text)

        body_text = "\n\n".join(paragraphs)

        # 6. Ghép thành nội dung toàn văn hoàn chỉnh (Full Text)
        parts = []
        if title:
            parts.append(title)
        if summary and summary != title:
            parts.append(summary)
        if body_text:
            parts.append(body_text)

        content_full = self.cleaner.clean("\n\n".join(parts))
        tokens = content_full.split()

        return {
            "title": self.cleaner.clean(title),
            "summary": self.cleaner.clean(summary),
            "content_full": content_full,
            "token_count": len(tokens),
        }
