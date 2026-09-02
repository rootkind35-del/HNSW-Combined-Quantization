"""Streaming Data Pipeline orchestrator for large-scale text preprocessing and embedding."""

import time
from typing import Any, Dict, Iterable, Optional, Tuple
from ann_data.cleaner import TextCleaner
from ann_data.config import PipelineConfig
from ann_data.deduplicator import StreamDeduplicator
from ann_data.embedder import BatchEmbedder, BaseEmbedder, SentenceTransformerEmbedder
from ann_data.storage import MemmapStorage
from ann_data.tokenizer import BaseTokenizer, PyViTokenizer
from ann_data.utils import get_logger


class DataPipeline:
    """Orchestrates end-to-end streaming data transformation from raw text to memory-mapped embeddings."""

    def __init__(
        self,
        config: PipelineConfig,
        embedder: Optional[BaseEmbedder] = None,
        tokenizer: Optional[BaseTokenizer] = None,
    ):
        self.config = config
        self.logger = get_logger("DataPipeline")
        
        # Subcomponents
        self.cleaner = TextCleaner(
            normalize_nfc=config.normalize_unicode_nfc,
            strip_html=config.strip_html_tags,
            remove_urls=config.remove_urls,
        )
        self.tokenizer = tokenizer or PyViTokenizer()
        self.deduplicator = StreamDeduplicator(
            threshold=config.minhash_threshold,
            num_perm=config.minhash_num_perm,
            lowercase=config.lowercase_tokens_for_dedup,
        )
        self.storage = MemmapStorage(
            file_path=config.output_memmap_path,
            max_records=config.max_records,
            dim=config.embedding_dim,
            dtype=config.dtype,
            mode="w+",
        )
        selected_embedder = embedder or SentenceTransformerEmbedder(
            model_name=config.model_name,
            dim=config.embedding_dim,
        )
        self.batch_embedder = BatchEmbedder(
            embedder=selected_embedder,
            storage=self.storage,
            batch_size=config.batch_size,
        )

    def process_item(self, doc_id: str, raw_text: str) -> Optional[str]:
        """Runs cleaning, tokenization, and deduplication check on a single sample."""
        cleaned = self.cleaner.clean(raw_text)
        if not cleaned:
            return None

        tokenized = self.tokenizer.tokenize(cleaned)
        if not tokenized:
            return None

        if self.deduplicator.is_duplicate(doc_id, tokenized):
            return None

        return tokenized

    def process_stream(
        self, stream: Iterable[Tuple[str, str]], log_interval: int = 10000
    ) -> Dict[str, Any]:
        """
        Consumes an incoming stream of (doc_id, text) tuples, processes each through the pipeline,
        and saves embeddings to disk.
        """
        start_time = time.perf_counter()
        total_input = 0
        total_valid = 0

        self.logger.info("Starting stream processing...")

        for doc_id, text in stream:
            total_input += 1
            processed_text = self.process_item(doc_id, text)
            
            if processed_text is not None:
                total_valid += 1
                self.batch_embedder.add(processed_text)

            if total_input % log_interval == 0:
                self.logger.info(
                    "Processed %d documents | Valid: %d | Duplicates: %d",
                    total_input,
                    total_valid,
                    self.deduplicator.total_duplicates,
                )

        # Flush remaining vectors
        self.batch_embedder.flush()
        elapsed = time.perf_counter() - start_time

        stats = {
            "total_input": total_input,
            "total_valid_embedded": total_valid,
            "total_duplicates": self.deduplicator.total_duplicates,
            "storage_written_records": self.storage.current_count,
            "output_path": self.config.output_memmap_path,
            "elapsed_seconds": round(elapsed, 4),
            "throughput_docs_per_sec": round(total_input / max(elapsed, 1e-6), 2),
        }
        self.logger.info("Pipeline completed: %s", stats)
        return stats

    def close(self) -> None:
        """Closes all underlying open resources."""
        self.batch_embedder.close()

    def __enter__(self) -> "DataPipeline":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
