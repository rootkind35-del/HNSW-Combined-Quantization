"""Giao diện trừu tượng cơ sở cho các bộ nạp dữ liệu và trình cào báo (Data Loaders & Crawlers)."""

from abc import ABC, abstractmethod
from typing import Generator, Optional, Tuple


class BaseDataLoader(ABC):
    """Lớp trừu tượng cơ sở định nghĩa hành vi thu thập và nạp dữ liệu ngữ liệu văn bản theo luồng."""

    @abstractmethod
    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        """
        Sinh ra từng cặp (doc_id, text) từ nguồn dữ liệu theo dạng generator tiết kiệm bộ nhớ.

        Tham số:
            limit: Số lượng bản ghi tối đa cần nạp (None nghĩa là nạp toàn bộ không giới hạn).

        Sinh ra:
            Tuple[str, str]: Cặp gồm mã định danh tài liệu (doc_id) và nội dung văn bản (text).
        """
        pass

