"""End-to-end Semantic Search Engine combining vector index and text metadata."""

import json
import os
from typing import Any, Dict, List, Optional
import numpy as np
from ann_data.cleaner import TextCleaner
from ann_data.embedder import BaseEmbedder, SentenceTransformerEmbedder
from ann_data.search.exact_search import ExactVectorSearch
from ann_data.tokenizer import BaseTokenizer, PyViTokenizer
from ann_data.utils import get_logger


class SemanticSearchEngine:
    """Orchestrates query preprocessing, embedding inference, vector retrieval, and metadata mapping."""

    def __init__(
        self,
        vector_file: str,
        metadata_file: str,
        embedder: Optional[BaseEmbedder] = None,
        cleaner: Optional[TextCleaner] = None,
        tokenizer: Optional[BaseTokenizer] = None,
        dim: int = 384,
    ):
        self.vector_file = vector_file
        self.metadata_file = metadata_file
        self.dim = dim
        self.logger = get_logger("SemanticSearchEngine")

        self.cleaner = cleaner or TextCleaner()
        self.tokenizer = tokenizer or PyViTokenizer()
        self.embedder = embedder or SentenceTransformerEmbedder(dim=self.dim)

        self.metadata: List[Dict[str, Any]] = []
        self._load_metadata()

        self.index: Optional[ExactVectorSearch] = None
        self._load_vector_index()

    def _load_metadata(self) -> None:
        """Loads metadata records from JSONL file."""
        if not os.path.exists(self.metadata_file):
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file}")

        with open(self.metadata_file, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    self.metadata.append(json.loads(stripped))

        self.logger.info("Loaded %d metadata records from %s", len(self.metadata), self.metadata_file)

    def _load_vector_index(self) -> None:
        """Loads vector binary file as memory-mapped array and builds exact search index."""
        if not os.path.exists(self.vector_file):
            raise FileNotFoundError(f"Vector file not found: {self.vector_file}")

        num_records = len(self.metadata)
        if num_records == 0:
            raise ValueError("No metadata records found to map vectors to.")

        # Read only the active populated slice from disk
        raw_mmap = np.memmap(
            self.vector_file,
            dtype="float32",
            mode="r",
            shape=(num_records, self.dim),
        )
        vectors = np.array(raw_mmap)
        del raw_mmap

        self.index = ExactVectorSearch(vectors=vectors, normalize=True)
        self.logger.info("Initialized vector search index with shape (%d, %d)", num_records, self.dim)

    def search(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes semantic search for a text query.

        Returns:
            List of matching records with rank, similarity score, title, preview, and doc_id.
        """
        if not query_text or not query_text.strip():
            return []

        cleaned_query = self.cleaner.clean(query_text)
        tokenized_query = self.tokenizer.tokenize(cleaned_query)

        # Generate query embedding
        query_vectors = self.embedder.encode([tokenized_query])
        if len(query_vectors) == 0:
            return []

        query_vector = query_vectors[0]
        raw_results = self.index.search(query_vector=query_vector, top_k=top_k)

        enriched_results = []
        for rank, (idx, score) in enumerate(raw_results, start=1):
            meta = self.metadata[idx] if idx < len(self.metadata) else {}
            enriched_results.append({
                "rank": rank,
                "vector_idx": idx,
                "score": round(score, 4),
                "title": meta.get("title", "N/A"),
                "preview": meta.get("preview", ""),
                "doc_id": meta.get("doc_id", ""),
            })

        return enriched_results
