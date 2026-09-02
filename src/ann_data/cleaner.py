"""Module làm sạch và chuẩn hóa văn bản tiếng Việt."""

import re
import unicodedata
from typing import Optional
from bs4 import BeautifulSoup


class TextCleaner:
    """
    Bộ làm sạch văn bản tiếng Việt:
    Hỗ trợ chuẩn hóa Unicode dạng dựng sẵn (NFC), bóc tách thẻ HTML/XML,
    loại bỏ đường dẫn URL, lọc ký tự đặc biệt rác và chuẩn hóa khoảng trắng thừa.
    """

    def __init__(
        self,
        normalize_nfc: bool = True,
        strip_html: bool = True,
        remove_urls: bool = True,
        preserve_punctuation: str = r"\.,!?",
    ):
        """
        Khởi tạo bộ làm sạch văn bản.

        Tham số:
            normalize_nfc: Nếu True, chuyển đổi toàn bộ chuỗi ký tự về dạng Unicode NFC chuẩn.
            strip_html: Nếu True, bóc tách toàn bộ mã HTML và chỉ giữ lại nội dung văn bản.
            remove_urls: Nếu True, loại bỏ các đường dẫn web http/https/www.
            preserve_punctuation: Biểu thức chính quy các dấu câu cơ bản cần bảo tồn.
        """
        self.normalize_nfc = normalize_nfc
        self.strip_html = strip_html
        self.remove_urls = remove_urls
        self.preserve_punctuation = preserve_punctuation
        
        # Biên dịch trước các mẫu Regular Expression để đạt thông lượng xử lý cao nhất
        self._url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
        self._char_pattern = re.compile(rf"[^\w\s{self.preserve_punctuation}]")
        self._whitespace_pattern = re.compile(r"\s+")

    def clean_html(self, text: str) -> str:
        """Bóc tách các thẻ HTML/XML và trích xuất nội dung văn bản thuần túy."""
        if not text or ("<" not in text and ">" not in text):
            return text
            
        import warnings
        from bs4 import XMLParsedAsHTMLWarning
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            soup = BeautifulSoup(text, "html.parser")
            
        return soup.get_text(separator=" ")

    def clean_unicode(self, text: str) -> str:
        """Chuẩn hóa văn bản tiếng Việt sang dạng Unicode dựng sẵn NFC (Canonical Decomposition followed by Canonical Composition)."""
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    def clean_urls(self, text: str) -> str:
        """Loại bỏ các liên kết URL và địa chỉ trang web khỏi văn bản."""
        if not text:
            return ""
        return self._url_pattern.sub(" ", text)

    def clean_special_chars(self, text: str) -> str:
        """Loại bỏ các ký tự đặc biệt gây nhiễu nhưng bảo tồn từ ngữ và các dấu câu cơ bản."""
        if not text:
            return ""
        return self._char_pattern.sub(" ", text)

    def normalize_whitespace(self, text: str) -> str:
        """Gộp các khoảng trắng, dấu xuống dòng, và dấu tab liên tiếp thành một dấu cách duy nhất."""
        if not text:
            return ""
        return self._whitespace_pattern.sub(" ", text).strip()

    def clean(self, text: Optional[str]) -> str:
        """
        Thực thi toàn bộ chu trình làm sạch và chuẩn hóa tuần tự trên chuỗi văn bản đầu vào.

        Tham số:
            text: Chuỗi văn bản thô đầu vào.

        Trả về:
            Chuỗi văn bản đã được làm sạch và chuẩn hóa hoàn chỉnh.
        """
        if not text or not isinstance(text, str):
            return ""

        result = text
        if self.strip_html:
            result = self.clean_html(result)

        if self.normalize_nfc:
            result = self.clean_unicode(result)

        if self.remove_urls:
            result = self.clean_urls(result)

        result = self.clean_special_chars(result)
        result = self.normalize_whitespace(result)
        return result


# Thể hiện mặc định phục vụ gọi nhanh dạng tiện ích
_default_cleaner = TextCleaner()


def clean_text(text: Optional[str]) -> str:
    """Hàm tiện ích làm sạch nhanh chuỗi văn bản với các thiết lập chuẩn mặc định."""
    return _default_cleaner.clean(text)

