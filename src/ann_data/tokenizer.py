"""Module tách từ và phân đoạn từ ghép tiếng Việt (Vietnamese Word Segmentation)."""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseTokenizer(ABC):
    """Giao diện trừu tượng cho các bộ tách từ văn bản."""

    @abstractmethod
    def tokenize(self, text: str) -> str:
        """Tách từ và ghép các từ phức bằng dấu gạch dưới (ví dụ: 'thị_trường chứng_khoán')."""
        pass

    @abstractmethod
    def tokenize_to_list(self, text: str) -> List[str]:
        """Tách văn bản thành danh sách các token từ đơn lẻ."""
        pass


class PyViTokenizer(BaseTokenizer):
    """Bộ phân đoạn từ ghép tiếng Việt sử dụng thư viện PyVi (ViTokenizer)."""

    def __init__(self):
        """Khởi tạo bộ tách từ PyVi, tự động xử lý an toàn nếu thư viện chưa được cài đặt."""
        try:
            from pyvi import ViTokenizer
            self._engine = ViTokenizer
        except ImportError:
            self._engine = None

    def tokenize(self, text: Optional[str]) -> str:
        """
        Phân đoạn từ ghép tiếng Việt.

        Tham số:
            text: Chuỗi văn bản tiếng Việt đầu vào.

        Trả về:
            Chuỗi văn bản với các từ ghép được nối bằng dấu gạch dưới.
        """
        if not text:
            return ""
        if self._engine is not None:
            return self._engine.tokenize(text)
        return text

    def tokenize_to_list(self, text: Optional[str]) -> List[str]:
        """
        Tách văn bản tiếng Việt thành mảng các từ/token.

        Tham số:
            text: Chuỗi văn bản đầu vào.

        Trả về:
            Danh sách các token từ.
        """
        segmented = self.tokenize(text)
        if not segmented:
            return []
        return segmented.split()


class WhitespaceTokenizer(BaseTokenizer):
    """Bộ tách từ cơ bản theo khoảng trắng làm cơ chế dự phòng an toàn."""

    def tokenize(self, text: Optional[str]) -> str:
        """Trả về nguyên bản chuỗi văn bản."""
        return text or ""

    def tokenize_to_list(self, text: Optional[str]) -> List[str]:
        """Tách chuỗi thành danh sách từ dựa theo khoảng trắng."""
        if not text:
            return []
        return text.split()


# Thể hiện mặc định phục vụ gọi tiện ích
_default_tokenizer = PyViTokenizer()


def segment_text(text: Optional[str]) -> str:
    """Hàm tiện ích tách từ ghép tiếng Việt nhanh bằng bộ tách từ PyVi mặc định."""
    return _default_tokenizer.tokenize(text)

