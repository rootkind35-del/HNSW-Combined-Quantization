"""Trình nạp luồng ngữ liệu văn bản tiếng Việt quy mô lớn từ Hugging Face."""

import hashlib
import os
import time
from typing import Dict, Generator, List, Optional
from crawler.extractors.text_cleaner import TextCleaner
from ann_data.utils import get_logger

# Ngăn cảnh báo symlink trên hệ điều hành Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logger = get_logger("crawler.hf_streamer")


class HuggingFaceStreamer:
    """Nạp luồng các kho dữ liệu văn bản tiếng Việt quy mô hàng triệu bản ghi từ Hugging Face."""

    DEFAULT_SOURCES = [
        {"dataset_name": "wikimedia/wikipedia", "config_name": "20231101.vi", "text_column": "text"},
        {"dataset_name": "CohereLabs/xP3x", "config_name": "vie_Latn", "text_column": "inputs"},
        {"dataset_name": "facebook/xnli", "config_name": "vi", "text_column": "premise"},
        {"dataset_name": "allenai/c4", "config_name": "vi", "text_column": "text"},
    ]

    def __init__(self, sources: Optional[List[Dict[str, Optional[str]]]] = None):
        self.sources = sources or self.DEFAULT_SOURCES
        self.cleaner = TextCleaner()

    def stream(self, limit: Optional[int] = None) -> Generator[Dict[str, str], None, None]:
        """
        Quét luồng các kho ngữ liệu Hugging Face và sinh ra các bản ghi toàn văn.

        Tham số:
            limit: Giới hạn số lượng tài liệu cần lấy.

        Sinh ra:
            Dict chứa 'doc_id', 'source', 'title', 'content_full', 'token_count', 'crawled_at'.
        """
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("Thư viện 'datasets' chưa được cài đặt. Hãy chạy: pip install datasets")
            return

        yielded_count = 0

        for source in self.sources:
            d_name = source["dataset_name"]
            c_name = source["config_name"]
            text_col = source["text_column"]

            logger.info("Đang kết nối luồng Hugging Face: %s (cấu hình: %s)", d_name, c_name)
            try:
                ds = load_dataset(d_name, c_name, split="train", streaming=True)
                for item in ds:
                    raw_text = item.get(text_col, "")
                    if not raw_text or len(raw_text) < 50:
                        continue

                    cleaned = self.cleaner.clean(raw_text)
                    tokens = cleaned.split()
                    if len(tokens) < 20:
                        continue

                    lines = [l.strip() for l in cleaned.splitlines() if l.strip()]
                    title = lines[0][:120] if lines else "Tài liệu không tên"
                    doc_id = f"hf_{hashlib.sha256(cleaned[:200].encode()).hexdigest()[:16]}"

                    record = {
                        "doc_id": doc_id,
                        "url": f"https://huggingface.co/datasets/{d_name}",
                        "source": f"HuggingFace/{d_name}",
                        "published_at": "",
                        "title": title,
                        "summary": lines[1][:300] if len(lines) > 1 else lines[0][:300],
                        "content_full": cleaned,
                        "token_count": len(tokens),
                        "crawled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    }

                    yield record
                    yielded_count += 1
                    if limit is not None and yielded_count >= limit:
                        logger.info("Đã đạt chỉ tiêu nạp ngữ liệu: %d bản ghi", limit)
                        return

            except Exception as e:
                logger.warning("Không thể đọc luồng từ %s: %s", d_name, str(e))
                continue
