"""Client HTTP mạnh mẽ với cơ chế thử lại (exponential retry) và luân chuyển User-Agent."""

import random
import time
import urllib.error
import urllib.request
from typing import Optional
from crawler.config import CrawlerConfig
from ann_data.utils import get_logger

logger = get_logger("crawler.http_client")


class HttpClient:
    """Trình gửi yêu cầu HTTP hỗ trợ backoff, xoay User-Agent và bảo vệ chống chặn IP."""

    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self._ua_index = 0

    def _get_next_user_agent(self) -> str:
        """Lấy User-Agent tiếp theo trong danh sách xoay vòng."""
        ua = self.config.user_agents[self._ua_index % len(self.config.user_agents)]
        self._ua_index += 1
        return ua

    def get(self, url: str) -> Optional[str]:
        """
        Thực hiện HTTP GET với cơ chế thử lại lũy thừa.

        Tham số:
            url: Đường dẫn URL cần tải.

        Trả về:
            Chuỗi văn bản HTML/XML hoặc None nếu thất bại sau max_retries.
        """
        retries = 0
        backoff = self.config.backoff_factor

        while retries < self.config.max_retries:
            headers = {
                "User-Agent": self._get_next_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                "Connection": "keep-alive",
            }

            req = urllib.request.Request(url, headers=headers)
            try:
                if self.config.rate_limit_delay > 0:
                    time.sleep(self.config.rate_limit_delay + random.uniform(0.05, 0.15))

                with urllib.request.urlopen(req, timeout=self.config.request_timeout) as resp:
                    raw_bytes = resp.read()
                    charset = resp.headers.get_content_charset() or "utf-8"
                    return raw_bytes.decode(charset, errors="replace")

            except urllib.error.HTTPError as e:
                # Nếu gặp lỗi 404 thì không thử lại
                if e.code == 404:
                    logger.warning("URL không tồn tại (404): %s", url)
                    return None
                logger.warning("Lỗi HTTP %d khi tải %s (Lần thử %d/%d): %s", e.code, url, retries + 1, self.config.max_retries, e.reason)
            except Exception as e:
                logger.warning("Lỗi kết nối %s (Lần thử %d/%d): %s", url, retries + 1, self.config.max_retries, str(e))

            retries += 1
            time.sleep(backoff)
            backoff *= 1.5

        logger.error("Không thể tải URL sau %d lần thử: %s", self.config.max_retries, url)
        return None
