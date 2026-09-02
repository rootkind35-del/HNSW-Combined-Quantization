"""Vietnamese word segmentation and tokenization module."""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseTokenizer(ABC):
    """Abstract interface for text tokenizers."""

    @abstractmethod
    def tokenize(self, text: str) -> str:
        """Tokenizes or segments input text, returning compound words joined by underscore."""
        pass

    @abstractmethod
    def tokenize_to_list(self, text: str) -> List[str]:
        """Tokenizes text into a list of word tokens."""
        pass


class PyViTokenizer(BaseTokenizer):
    """Vietnamese word segmenter implementation using PyVi."""

    def __init__(self):
        try:
            from pyvi import ViTokenizer
            self._engine = ViTokenizer
        except ImportError:
            self._engine = None

    def tokenize(self, text: Optional[str]) -> str:
        if not text:
            return ""
        if self._engine is not None:
            return self._engine.tokenize(text)
        return text

    def tokenize_to_list(self, text: Optional[str]) -> List[str]:
        segmented = self.tokenize(text)
        if not segmented:
            return []
        return segmented.split()


class WhitespaceTokenizer(BaseTokenizer):
    """Fallback tokenizer splitting purely on whitespace."""

    def tokenize(self, text: Optional[str]) -> str:
        return text or ""

    def tokenize_to_list(self, text: Optional[str]) -> List[str]:
        if not text:
            return []
        return text.split()


_default_tokenizer = PyViTokenizer()


def segment_text(text: Optional[str]) -> str:
    """Convenience function to segment text using the default Vietnamese tokenizer."""
    return _default_tokenizer.tokenize(text)
