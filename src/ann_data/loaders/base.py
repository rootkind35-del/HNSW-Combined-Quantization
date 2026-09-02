"""Base abstract interface for data loaders and crawlers."""

from abc import ABC, abstractmethod
from typing import Generator, Optional, Tuple


class BaseDataLoader(ABC):
    """Abstract base class for all corpus ingestion loaders and crawlers."""

    @abstractmethod
    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        """
        Yields (doc_id, text) pairs from the underlying data source.

        Args:
            limit: Maximum number of records to yield. None indicates no limit.

        Yields:
            Tuple[str, str]: (doc_id, text)
        """
        pass
