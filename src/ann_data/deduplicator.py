"""Deduplication module using MinHash and Locality Sensitive Hashing (LSH)."""

from typing import Dict, Generator, Iterable, List, Optional, Tuple
from datasketch import MinHash, MinHashLSH


class StreamDeduplicator:
    """Detects and filters duplicate or highly similar documents in a stream using MinHash LSH."""

    def __init__(
        self,
        threshold: float = 0.8,
        num_perm: int = 128,
        lowercase: bool = True,
        shingle_size: int = 1,
    ):
        self.threshold = threshold
        self.num_perm = num_perm
        self.lowercase = lowercase
        self.shingle_size = shingle_size
        
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.total_seen = 0
        self.total_duplicates = 0

    def _extract_shingles(self, text: str) -> List[str]:
        """Extracts n-gram word shingles from input text."""
        normalized = text.lower() if self.lowercase else text
        tokens = normalized.split()
        if not tokens:
            return []
        if self.shingle_size <= 1:
            return tokens
        
        shingles = []
        for i in range(len(tokens) - self.shingle_size + 1):
            shingles.append(" ".join(tokens[i : i + self.shingle_size]))
        return shingles or tokens

    def compute_minhash(self, text: str) -> MinHash:
        """Computes a MinHash fingerprint for the provided document text."""
        minhash = MinHash(num_perm=self.num_perm)
        shingles = self._extract_shingles(text)
        for s in shingles:
            minhash.update(s.encode("utf-8"))
        return minhash

    def is_duplicate(self, doc_id: str, text: str) -> bool:
        """
        Checks whether document is a near-duplicate.
        If duplicate, returns True.
        If unique, inserts into LSH index and returns False.
        """
        self.total_seen += 1
        
        # Prevent OOM for 10M records by resetting LSH index periodically
        # (local deduplication within chunks of 50,000 documents)
        if self.total_seen % 50000 == 0:
            self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
            
        minhash = self.compute_minhash(text)
        candidates = self.lsh.query(minhash)
        
        if candidates:
            self.total_duplicates += 1
            return True
            
        self.lsh.insert(doc_id, minhash)
        return False

    def filter_stream(
        self, stream: Iterable[Tuple[str, str]]
    ) -> Generator[Tuple[str, str], None, None]:
        """Yields only unique (doc_id, text) pairs from an incoming stream."""
        for doc_id, text in stream:
            if not self.is_duplicate(doc_id, text):
                yield doc_id, text

    @property
    def stats(self) -> Dict[str, int]:
        """Returns processing statistics."""
        return {
            "total_seen": self.total_seen,
            "total_duplicates": self.total_duplicates,
            "unique_kept": self.total_seen - self.total_duplicates,
        }

    def reset(self) -> None:
        """Clears the LSH index and resets statistics."""
        self.lsh = MinHashLSH(threshold=self.threshold, num_perm=self.num_perm)
        self.total_seen = 0
        self.total_duplicates = 0
