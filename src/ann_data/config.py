"""Quản lý cấu hình tham số cho Pipeline xử lý dữ liệu lớn và nhúng vector."""

from dataclasses import dataclass, field, asdict
import json
import os
from typing import Any, Dict


@dataclass
class PipelineConfig:
    """
    Lớp cấu hình lưu trữ các tham số tiền xử lý văn bản, khử trùng lặp MinHash,
    sinh vector nhúng SentenceTransformer và lưu trữ nhị phân Memmap trên SSD.
    """
    
    # Tham số mô hình Embedding
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384
    batch_size: int = 64
    
    # Tham số lưu trữ đĩa Memmap
    max_records: int = 10_000_000
    output_memmap_path: str = "data/processed/vectors.dat"
    dtype: str = "float32"
    
    # Tham số giải thuật khử trùng MinHash LSH
    minhash_threshold: float = 0.8
    minhash_num_perm: int = 128
    
    # Tùy chọn tiền xử lý văn bản tiếng Việt
    strip_html_tags: bool = True
    normalize_unicode_nfc: bool = True
    remove_urls: bool = True
    lowercase_tokens_for_dedup: bool = True
    
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi cấu hình thành kiểu Dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Khởi tạo đối tượng PipelineConfig từ Dictionary."""
        valid_fields = cls.__dataclass_fields__.keys()
        init_args = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**init_args)

    @classmethod
    def from_json(cls, file_path: str) -> "PipelineConfig":
        """Đọc và nạp cấu hình từ tệp tin JSON."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy tệp cấu hình: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def save_json(self, file_path: str) -> None:
        """Lưu trữ cấu hình hiện tại ra tệp tin định dạng JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

