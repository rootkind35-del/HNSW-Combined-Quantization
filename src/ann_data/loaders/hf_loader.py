"""Streaming dataset loader from Hugging Face Hub."""

from typing import Generator, Optional, Tuple
from ann_data.loaders.base import BaseDataLoader
from ann_data.utils import get_logger


class HuggingFaceLoader(BaseDataLoader):
    """Streams records directly from Hugging Face Hub datasets without full local downloads."""

    def __init__(
        self,
        dataset_name: str = "fsnaix/vietnamese-corpus-large",
        config_name: Optional[str] = None,
        split: str = "train",
        text_column: str = "text",
        id_column: Optional[str] = None,
        streaming: bool = True,
    ):
        self.dataset_name = dataset_name
        self.config_name = config_name
        self.split = split
        self.text_column = text_column
        self.id_column = id_column
        self.streaming = streaming
        self.logger = get_logger("HuggingFaceLoader")

    def _load_dataset_stream(self):
        """Attempts to load streaming dataset object."""
        try:
            from datasets import load_dataset
            kwargs = {
                "path": self.dataset_name,
                "split": self.split,
                "streaming": self.streaming,
                "trust_remote_code": False,
            }
            if self.config_name:
                kwargs["name"] = self.config_name
                
            dataset = load_dataset(**kwargs)
            return dataset
        except Exception as e:
            self.logger.warning(
                "Could not initialize Hugging Face stream for '%s' (config: %s): %s",
                self.dataset_name,
                self.config_name,
                str(e),
            )
            return None

    def stream(self, limit: Optional[int] = None) -> Generator[Tuple[str, str], None, None]:
        """Streams (doc_id, text) pairs from Hugging Face dataset."""
        dataset = self._load_dataset_stream()
        if dataset is None:
            self.logger.info("Dataset stream unavailable or network unreachable.")
            return

        yielded = 0
        for idx, item in enumerate(dataset):
            if not isinstance(item, dict):
                continue

            text = item.get(self.text_column, "")
            if not text or not isinstance(text, str):
                continue

            doc_id = (
                str(item.get(self.id_column))
                if self.id_column and self.id_column in item
                else f"hf_{self.split}_{idx:08d}"
            )

            yield doc_id, text
            yielded += 1

            if limit is not None and yielded >= limit:
                break
