"""Vector embedding generation and batch persistence module."""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from ann_data.storage import MemmapStorage
from ann_data.utils import get_logger


class BaseEmbedder(ABC):
    """Abstract interface for text embedding models."""

    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encodes a list of text strings into an ndarray of shape (len(texts), dim)."""
        pass

    @property
    @abstractmethod
    def dim(self) -> int:
        """Returns the embedding vector dimension."""
        pass


class MockEmbedder(BaseEmbedder):
    """Deterministic or random embedding generator for testing and I/O validation."""

    def __init__(self, dim: int = 384, seed: Optional[int] = 42):
        self._dim = dim
        self._rng = np.random.RandomState(seed)

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: List[str]) -> np.ndarray:
        count = len(texts)
        if count == 0:
            return np.empty((0, self._dim), dtype=np.float32)
        # Generate normalized float32 vectors
        vectors = self._rng.randn(count, self._dim).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)


class SentenceTransformerEmbedder(BaseEmbedder):
    """Neural embedding model using the sentence-transformers library."""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", dim: int = 384):
        self.model_name = model_name
        self._dim = dim
        self._logger = get_logger("SentenceTransformerEmbedder")
        self._model = None
        self._fallback_mock: Optional[MockEmbedder] = None
        self._init_model()

    def _init_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        except Exception as e:
            self._logger.warning(
                "Could not load sentence_transformers (%s). Activating fallback MockEmbedder.",
                str(e)
            )
            self._fallback_mock = MockEmbedder(dim=self._dim)

    @property
    def dim(self) -> int:
        return self._dim

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self._dim), dtype=np.float32)

        if self._model is not None:
            embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return embeddings.astype(np.float32)
        elif self._fallback_mock is not None:
            return self._fallback_mock.encode(texts)
        else:
            raise RuntimeError("No operational embedding backend available.")


class BatchEmbedder:
    """Coordinates batching and direct writing of embeddings into MemmapStorage."""

    def __init__(self, embedder: BaseEmbedder, storage: MemmapStorage, batch_size: int = 64):
        self.embedder = embedder
        self.storage = storage
        self.batch_size = batch_size
        self.buffer: List[str] = []

    def add(self, text: str) -> Optional[int]:
        """Adds a text sample to buffer. If buffer reaches batch_size, flushes to storage."""
        self.buffer.append(text)
        if len(self.buffer) >= self.batch_size:
            return self.flush()
        return None

    def flush(self) -> int:
        """Encodes all buffered texts and writes directly into storage."""
        if not self.buffer:
            return 0

        vectors = self.embedder.encode(self.buffer)
        num_records = len(vectors)
        self.storage.append_batch(vectors)
        self.buffer.clear()
        return num_records

    def close(self) -> None:
        """Flushes remaining items and closes storage handle."""
        self.flush()
        self.storage.close()

    def __enter__(self) -> "BatchEmbedder":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
