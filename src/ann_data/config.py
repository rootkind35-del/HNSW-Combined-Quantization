"""Configuration management for data pipeline."""

from dataclasses import dataclass, field, asdict
import json
import os
from typing import Any, Dict


@dataclass
class PipelineConfig:
    """Configuration class storing parameters for text preprocessing, deduplication, and embedding."""
    
    # Model parameters
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    batch_size: int = 64
    
    # Storage parameters
    max_records: int = 10_000_000
    output_memmap_path: str = "data/processed/vectors.dat"
    dtype: str = "float32"
    
    # Deduplication parameters
    minhash_threshold: float = 0.8
    minhash_num_perm: int = 128
    
    # Preprocessing options
    strip_html_tags: bool = True
    normalize_unicode_nfc: bool = True
    remove_urls: bool = True
    lowercase_tokens_for_dedup: bool = True
    
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        valid_fields = cls.__dataclass_fields__.keys()
        init_args = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**init_args)

    @classmethod
    def from_json(cls, file_path: str) -> "PipelineConfig":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Config file not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_json(self, file_path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
