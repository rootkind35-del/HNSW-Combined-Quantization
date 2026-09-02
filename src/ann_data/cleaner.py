"""Text cleaning and normalization module."""

import re
import unicodedata
from typing import Optional
from bs4 import BeautifulSoup


class TextCleaner:
    """Text cleaner supporting Unicode NFC normalization, HTML removal, and character cleanup."""

    def __init__(
        self,
        normalize_nfc: bool = True,
        strip_html: bool = True,
        remove_urls: bool = True,
        preserve_punctuation: str = r"\.,!?",
    ):
        self.normalize_nfc = normalize_nfc
        self.strip_html = strip_html
        self.remove_urls = remove_urls
        self.preserve_punctuation = preserve_punctuation
        
        # Precompile regex patterns for high throughput
        self._url_pattern = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
        self._char_pattern = re.compile(rf"[^\w\s{self.preserve_punctuation}]")
        self._whitespace_pattern = re.compile(r"\s+")

    def clean_html(self, text: str) -> str:
        """Strips HTML tags while retaining inner text separated by whitespace."""
        if not text or ("<" not in text and ">" not in text):
            return text
            
        import warnings
        from bs4 import XMLParsedAsHTMLWarning
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
            soup = BeautifulSoup(text, "html.parser")
            
        return soup.get_text(separator=" ")

    def clean_unicode(self, text: str) -> str:
        """Converts text to standard Unicode NFC form."""
        if not text:
            return ""
        return unicodedata.normalize("NFC", text)

    def clean_urls(self, text: str) -> str:
        """Removes web links and URLs."""
        if not text:
            return ""
        return self._url_pattern.sub(" ", text)

    def clean_special_chars(self, text: str) -> str:
        """Removes unsupported special characters while preserving words and basic punctuation."""
        if not text:
            return ""
        return self._char_pattern.sub(" ", text)

    def normalize_whitespace(self, text: str) -> str:
        """Collapses consecutive spaces, newlines, and tabs into a single space."""
        if not text:
            return ""
        return self._whitespace_pattern.sub(" ", text).strip()

    def clean(self, text: Optional[str]) -> str:
        """Executes the full cleaning sequence on input text."""
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


# Standalone utility function for quick access
_default_cleaner = TextCleaner()


def clean_text(text: Optional[str]) -> str:
    """Convenience function using default cleaning settings."""
    return _default_cleaner.clean(text)
