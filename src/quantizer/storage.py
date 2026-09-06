"""Quản lý lưu trữ tệp vector lượng tử hóa int8 Memmap và metadata tra cứu toàn văn."""

import json
import os
import time
from typing import Any, Dict, List, Optional
import numpy as np
from ann_data.utils import get_logger

logger = get_logger("quantizer.storage")


class QuantizedStorage:
    """Lưu trữ và nạp vector lượng tử hóa int8 cùng bảng siêu dữ liệu tra cứu toàn văn."""

    def __init__(
        self,
        output_dir: str = "data/quantized",
        dim: int = 384,
        max_capacity: int = 1000000,
    ):
        self.output_dir = os.path.abspath(output_dir)
        self.dim = dim
        self.max_capacity = max_capacity
        os.makedirs(self.output_dir, exist_ok=True)

        self.vector_file = os.path.join(self.output_dir, "vectors_int8.dat")
        self.metadata_file = os.path.join(self.output_dir, "metadata.jsonl")
        self.params_file = os.path.join(self.output_dir, "quantization_params.json")
        self.manifest_file = os.path.join(self.output_dir, "QUANTIZED_MANIFEST.json")

        self.current_count = 0
        self._mmap: Optional[np.memmap] = None
        self._meta_f = None

    def initialize_storage(self, mode: str = "w+"):
        """Khởi tạo tệp nhị phân Memmap int8 và tệp JSONL metadata."""
        if mode == "w+" or not os.path.exists(self.vector_file):
            with open(self.vector_file, "wb") as f:
                f.truncate(self.max_capacity * self.dim)
            self._mmap = np.memmap(
                self.vector_file,
                dtype="int8",
                mode="r+",
                shape=(self.max_capacity, self.dim),
            )
            self._meta_f = open(self.metadata_file, "w", encoding="utf-8")
            self.current_count = 0
        else:
            # Chế độ đọc/ghi tiếp tục (append/resume)
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    self.current_count = sum(1 for line in f if line.strip())

            file_bytes = os.path.getsize(self.vector_file) if os.path.exists(self.vector_file) else 0
            current_capacity = file_bytes // self.dim if file_bytes > 0 else 0
            if current_capacity < self.current_count + 100000:
                new_cap = max(self.max_capacity, self.current_count + 500000)
                with open(self.vector_file, "a+b") as f:
                    f.truncate(new_cap * self.dim)
                current_capacity = new_cap
            self.max_capacity = current_capacity
            self._mmap = np.memmap(
                self.vector_file,
                dtype="int8",
                mode="r+",
                shape=(self.max_capacity, self.dim),
            )
            self._meta_f = open(self.metadata_file, "a", encoding="utf-8")

        logger.info("Khởi tạo QuantizedStorage: %s (Sức chứa: %d, Chiều: %d)", self.vector_file, self.max_capacity, self.dim)

    def append_batch(
        self,
        int8_vectors: np.ndarray,
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        flush: bool = False,
    ):
        """Ghi một lô vector int8 và metadata tương ứng (nếu có)."""
        if self._mmap is None or self._meta_f is None:
            self.initialize_storage(mode="a" if os.path.exists(self.vector_file) else "w+")

        batch_size = len(int8_vectors)
        start_idx = self.current_count
        end_idx = start_idx + batch_size

        if end_idx > self.max_capacity:
            self._resize_mmap(end_idx)

        # Ghi trực tiếp mảng int8 vào đĩa
        self._mmap[start_idx:end_idx] = int8_vectors
        if flush:
            self._mmap.flush()

        # Ghi siêu dữ liệu tra cứu toàn văn nếu có
        if metadata_list is not None and self._meta_f is not None:
            for i, meta in enumerate(metadata_list):
                meta["vector_idx"] = start_idx + i
                self._meta_f.write(json.dumps(meta, ensure_ascii=False) + "\n")
            if flush:
                self._meta_f.flush()

        self.current_count = end_idx

    def flush_buffers(self):
        """Xả toàn bộ bộ đệm mmap và tệp metadata ra đĩa SSD."""
        if self._mmap is not None:
            self._mmap.flush()
        if self._meta_f is not None:
            self._meta_f.flush()

    def _resize_mmap(self, target_capacity: int):
        """Mở rộng kích thước tệp đệm Memmap khi số lượng vector vượt sức chứa ban đầu."""
        new_capacity = max(target_capacity, self.max_capacity * 2)
        if self._mmap is not None:
            self._mmap.flush()
            del self._mmap
            self._mmap = None

        with open(self.vector_file, "a+b") as f:
            f.truncate(new_capacity * self.dim * 1)

        self.max_capacity = new_capacity
        self._mmap = np.memmap(
            self.vector_file,
            dtype="int8",
            mode="r+",
            shape=(self.max_capacity, self.dim),
        )
        logger.info("Đã tự động mở rộng sức chứa Memmap lên: %d vector", self.max_capacity)

    def save_quantization_params(self, params: Dict[str, Any]):
        """Lưu tham số lượng tử hóa ra tệp JSON."""
        with open(self.params_file, "w", encoding="utf-8") as f:
            json.dump(params, f, indent=2, ensure_ascii=False)
        logger.info("Đã lưu tham số lượng tử hóa: %s", self.params_file)

    def close(self):
        """Đóng các con trỏ tệp, cắt tệp về kích thước thực tế và tạo QUANTIZED_MANIFEST.json."""
        if self._mmap is not None:
            self._mmap.flush()
            del self._mmap
            self._mmap = None

        if self._meta_f is not None:
            self._meta_f.flush()
            self._meta_f.close()
            self._meta_f = None

        # Cắt bớt phần đệm thừa của tệp về đúng kích thước vector thực ghi
        if os.path.exists(self.vector_file) and self.current_count > 0:
            with open(self.vector_file, "a+b") as f:
                f.truncate(self.current_count * self.dim * 1)

        self.update_manifest()

    def update_manifest(self) -> Dict[str, Any]:
        """Tạo tệp kê khai QUANTIZED_MANIFEST.json chi tiết."""
        v_size = os.path.getsize(self.vector_file) if os.path.exists(self.vector_file) else 0
        m_size = os.path.getsize(self.metadata_file) if os.path.exists(self.metadata_file) else 0

        # Dung lượng float32 gốc tương ứng
        orig_bytes = self.current_count * self.dim * 4
        actual_bytes = self.current_count * self.dim * 1

        manifest = {
            "dataset_name": "Quantized Vector Dataset (Two-Tier Index Format)",
            "total_vectors": self.current_count,
            "vector_dimension": self.dim,
            "quantization_type": "Scalar Quantization 8-bit (SQ8)",
            "data_type": "int8 (1 byte per dimension)",
            "vector_file": "vectors_int8.dat",
            "metadata_file": "metadata.jsonl",
            "params_file": "quantization_params.json",
            "raw_float32_size_mb": round(orig_bytes / (1024 * 1024), 2),
            "quantized_size_mb": round(actual_bytes / (1024 * 1024), 2),
            "ram_saving_percent": 75.0,
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info("Đã cập nhật QUANTIZED_MANIFEST.json: %d vector int8 (Giảm 75%% RAM)", self.current_count)
        return manifest

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
