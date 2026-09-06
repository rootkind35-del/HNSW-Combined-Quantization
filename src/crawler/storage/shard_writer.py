"""Trình ghi dữ liệu toàn văn phân chia theo Shard JSONL có kiểm soát dung lượng và thống kê manifest."""

import json
import os
import time
from typing import Any, Dict, Optional
from ann_data.utils import get_logger

logger = get_logger("crawler.shard_writer")


class ShardWriter:
    """Quản lý ghi luồng các bản ghi toàn văn vào các tệp shard_XXXXX.jsonl trong data/crawl/."""

    def __init__(self, output_dir: str = "data/crawl", shard_size: int = 50000):
        self.output_dir = os.path.abspath(output_dir)
        self.shard_size = shard_size
        os.makedirs(self.output_dir, exist_ok=True)

        self.current_shard_idx = 0
        self.current_shard_count = 0
        self.total_records = 0
        self._current_file = None

        # Khôi phục trạng thái shard tiếp theo nếu đã có sẵn dữ liệu
        self._init_shard_index()

    def _init_shard_index(self):
        """Xác định chỉ số shard tiếp theo dựa trên các tệp đã tồn tại."""
        existing_shards = [
            f for f in os.listdir(self.output_dir)
            if f.startswith("shard_") and f.endswith(".jsonl")
        ]
        if existing_shards:
            existing_shards.sort()
            last_shard = existing_shards[-1]
            try:
                self.current_shard_idx = int(last_shard.replace("shard_", "").replace(".jsonl", ""))
                # Đếm số dòng của shard cuối
                last_path = os.path.join(self.output_dir, last_shard)
                with open(last_path, "r", encoding="utf-8") as f:
                    self.current_shard_count = sum(1 for line in f if line.strip())
                if self.current_shard_count >= self.shard_size:
                    self.current_shard_idx += 1
                    self.current_shard_count = 0
            except Exception:
                self.current_shard_idx = len(existing_shards)
                self.current_shard_count = 0

    def _get_shard_path(self, idx: int) -> str:
        return os.path.join(self.output_dir, f"shard_{idx:05d}.jsonl")

    def write(self, record: Dict[str, Any]) -> None:
        """
        Ghi một bản ghi toàn văn vào shard hiện tại.

        Tham số:
            record: Dict chứa toàn văn và siêu dữ liệu.
        """
        if self._current_file is None:
            shard_path = self._get_shard_path(self.current_shard_idx)
            self._current_file = open(shard_path, "a", encoding="utf-8")

        # Ghi một dòng JSONL
        json_line = json.dumps(record, ensure_ascii=False)
        self._current_file.write(json_line + "\n")
        self.current_shard_count += 1
        self.total_records += 1

        # Chuyển shard mới nếu đã đạt giới hạn
        if self.current_shard_count >= self.shard_size:
            self._current_file.flush()
            self._current_file.close()
            self._current_file = None
            logger.info("Hoàn tất shard_%05d (%d bản ghi). Chuyển shard tiếp theo.", self.current_shard_idx, self.current_shard_count)
            self.current_shard_idx += 1
            self.current_shard_count = 0

    def flush(self):
        """Xả bộ đệm ghi đĩa."""
        if self._current_file is not None:
            self._current_file.flush()

    def close(self):
        """Đóng tệp và cập nhật CRAWL_MANIFEST.json."""
        if self._current_file is not None:
            self._current_file.flush()
            self._current_file.close()
            self._current_file = None

        self.update_manifest()

    def update_manifest(self) -> Dict[str, Any]:
        """Tạo hoặc cập nhật tệp CRAWL_MANIFEST.json phản ánh đúng 100% dữ liệu đã lưu."""
        shards = [
            f for f in os.listdir(self.output_dir)
            if f.startswith("shard_") and f.endswith(".jsonl")
        ]
        shards.sort()

        total_bytes = 0
        total_docs = 0
        shard_info = []

        for s in shards:
            p = os.path.join(self.output_dir, s)
            size = os.path.getsize(p)
            total_bytes += size
            count = 0
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            total_docs += count
            shard_info.append({
                "shard_name": s,
                "records": count,
                "size_mb": round(size / (1024 * 1024), 2),
            })

        manifest = {
            "dataset_type": "RAW_CRAWLED_FULLTEXT_CORPUS",
            "storage_directory": self.output_dir,
            "total_shards": len(shards),
            "total_documents": total_docs,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "total_size_gb": round(total_bytes / (1024 * 1024 * 1024), 3),
            "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "shards": shard_info,
        }

        manifest_path = os.path.join(self.output_dir, "CRAWL_MANIFEST.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info("Đã cập nhật CRAWL_MANIFEST.json: %d tài liệu toàn văn (%d shards, %.2f MB)", total_docs, len(shards), manifest["total_size_mb"])
        return manifest

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
