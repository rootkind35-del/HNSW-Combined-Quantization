"""Bộ làm sạch văn bản và chuẩn hóa Unicode NFC."""

import re
import unicodedata


class TextCleaner:
    """Chuẩn hóa văn bản tiếng Việt và loại bỏ các ký tự rác."""

    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Chuẩn hóa Unicode theo định dạng dựng sẵn NFC."""
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    @staticmethod
    def clean(text: str) -> str:
        """Làm sạch ký tự điều khiển, khoảng trắng thừa và ký tự ẩn."""
        if not text:
            return ""

        text = TextCleaner.normalize_unicode(text)

        # Xóa các ký tự điều khiển và ký tự vô hình
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200d\ufeff]", "", text)

        # Chuẩn hóa khoảng trắng và dòng trống
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        cleaned_text = "\n".join(line for line in lines if line)
        return cleaned_text
