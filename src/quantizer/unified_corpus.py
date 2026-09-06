"""Quản lý và ghép nối đa kho vector lượng tử hóa int8 theo kiến trúc Zero-Copy Virtual Federation."""

import bisect
import json
import os
import time
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple
import numpy as np
from ann_data.utils import get_logger

logger = get_logger("quantizer.unified_corpus")


class UnifiedQuantizedCorpus:
    """Lớp quản lý truy xuất kho vector hợp nhất từ nhiều kho con mà không cần nhân bản dữ liệu trên đĩa SSD."""

    def __init__(self, combined_dir: str):
        self.combined_dir = os.path.abspath(combined_dir)
        self.map_file = os.path.join(self.combined_dir, "corpus_offset_map.json")
        self.manifest_file = os.path.join(self.combined_dir, "COMBINED_MANIFEST.json")

        if not os.path.exists(self.map_file):
            raise FileNotFoundError(f"Không tìm thấy bản đồ offset: {self.map_file}")

        with open(self.map_file, "r", encoding="utf-8") as f:
            self.map_data = json.load(f)

        self.total_vectors: int = self.map_data["total_vectors"]
        self.dim: int = self.map_data["dimension"]
        self.corpora_info: List[Dict[str, Any]] = self.map_data["corpora"]

        # Danh sách ngưỡng kết thúc của từng kho để tra cứu nhanh bằng bisect
        self._thresholds: List[int] = [c["end_idx"] for c in self.corpora_info]
        self._memmaps: List[np.memmap] = []
        self._meta_paths: List[str] = []

        # Khởi tạo con trỏ memmap đọc (read-only) cho từng kho
        for c in self.corpora_info:
            v_path = c["vector_file"]
            if not os.path.exists(v_path):
                raise FileNotFoundError(f"Tệp vector con không tồn tại: {v_path}")
            count = c["count"]
            mmap = np.memmap(v_path, dtype="int8", mode="r", shape=(count, self.dim))
            self._memmaps.append(mmap)
            self._meta_paths.append(c["metadata_file"])

        logger.info(
            "Đã nạp kho hợp nhất: %d vector, %d chiều, %d kho con",
            self.total_vectors,
            self.dim,
            len(self.corpora_info),
        )

    def __len__(self) -> int:
        return self.total_vectors

    def _locate_corpus(self, global_idx: int) -> Tuple[int, int]:
        """Xác định chỉ số kho con và offset cục bộ dựa trên global_idx."""
        if global_idx < 0 or global_idx >= self.total_vectors:
            raise IndexError(f"Chỉ số {global_idx} nằm ngoài phạm vi [0, {self.total_vectors - 1}]")

        corpus_idx = bisect.bisect_right(self._thresholds, global_idx)
        start_idx = self.corpora_info[corpus_idx]["start_idx"]
        local_idx = global_idx - start_idx
        return corpus_idx, local_idx

    def get_vector(self, global_idx: int) -> np.ndarray:
        """Đọc 1 vector int8 tại chỉ số toàn cục."""
        corpus_idx, local_idx = self._locate_corpus(global_idx)
        return self._memmaps[corpus_idx][local_idx]

    def get_vectors(self, indices: Sequence[int]) -> np.ndarray:
        """Đọc theo lô mảng chỉ số toàn cục."""
        n = len(indices)
        out = np.empty((n, self.dim), dtype=np.int8)
        if n == 0:
            return out

        # Phân nhóm chỉ số theo từng kho con để đọc khối liên tục
        grouped: Dict[int, List[Tuple[int, int]]] = {}
        for out_pos, g_idx in enumerate(indices):
            c_idx, l_idx = self._locate_corpus(int(g_idx))
            if c_idx not in grouped:
                grouped[c_idx] = []
            grouped[c_idx].append((out_pos, l_idx))

        for c_idx, pairs in grouped.items():
            out_positions = [p[0] for p in pairs]
            local_indices = [p[1] for p in pairs]
            out[out_positions] = self._memmaps[c_idx][local_indices]

        return out

    def get_metadata(self, global_idx: int) -> Dict[str, Any]:
        """Đọc bản ghi metadata tại chỉ số toàn cục bằng cách seek vào tệp metadata tương ứng."""
        corpus_idx, local_idx = self._locate_corpus(global_idx)
        meta_path = self._meta_paths[corpus_idx]

        with open(meta_path, "r", encoding="utf-8") as f:
            for cur_line, line in enumerate(f):
                if cur_line == local_idx:
                    data = json.loads(line.strip())
                    data["global_idx"] = global_idx
                    data["corpus_source"] = self.corpora_info[corpus_idx]["name"]
                    return data

        raise ValueError(f"Không tìm thấy dòng metadata {local_idx} trong {meta_path}")

    def get_metadata_batch(self, global_indices: Sequence[int]) -> Dict[int, Dict[str, Any]]:
        """Đọc theo lô metadata cho nhiều chỉ số toàn cục chỉ qua 1 lần quét cho mỗi tệp kho con."""
        results: Dict[int, Dict[str, Any]] = {}
        if not global_indices:
            return results

        # Phân nhóm theo corpus_idx: corpus_idx -> {local_idx: global_idx}
        corpus_groups: Dict[int, Dict[int, int]] = {}
        for g_idx in global_indices:
            c_idx, l_idx = self._locate_corpus(int(g_idx))
            if c_idx not in corpus_groups:
                corpus_groups[c_idx] = {}
            corpus_groups[c_idx][l_idx] = int(g_idx)

        for c_idx, local_map in corpus_groups.items():
            meta_path = self._meta_paths[c_idx]
            max_local = max(local_map.keys())
            needed = set(local_map.keys())
            source_name = self.corpora_info[c_idx]["name"]

            with open(meta_path, "r", encoding="utf-8") as f:
                for cur_line, line in enumerate(f):
                    if cur_line in needed:
                        data = json.loads(line.strip())
                        g_idx = local_map[cur_line]
                        data["global_idx"] = g_idx
                        data["corpus_source"] = source_name
                        results[g_idx] = data
                        needed.remove(cur_line)
                        if not needed or cur_line >= max_local:
                            break

        return results

    def iter_vectors(self, batch_size: int = 10000) -> Generator[np.ndarray, None, None]:
        """Duyệt tuần tự toàn bộ vector hợp nhất theo từng khối (phục vụ dựng đồ thị HNSW)."""
        for mmap in self._memmaps:
            total_in_corpus = mmap.shape[0]
            for start in range(0, total_in_corpus, batch_size):
                end = min(start + batch_size, total_in_corpus)
                yield mmap[start:end]

    def close(self):
        """Đóng các kết nối memmap và giải phóng file handle trên Windows."""
        import gc
        for mmap in self._memmaps:
            if hasattr(mmap, "_mmap") and mmap._mmap is not None:
                try:
                    mmap._mmap.close()
                except Exception:
                    pass
            del mmap
        self._memmaps.clear()
        gc.collect()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_unified_corpus(
    corpus_dirs: List[str],
    output_dir: str,
    corpus_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Tạo cấu trúc kho hợp nhất Zero-Copy từ danh sách các thư mục lượng tử hóa."""
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if corpus_names is None:
        corpus_names = [os.path.basename(d.rstrip("/\\")) for d in corpus_dirs]

    corpora_info = []
    total_vectors = 0
    common_dim = None
    all_params = []

    for idx, c_dir in enumerate(corpus_dirs):
        c_dir = os.path.abspath(c_dir)
        manifest_path = os.path.join(c_dir, "QUANTIZED_MANIFEST.json")
        params_path = os.path.join(c_dir, "quantization_params.json")
        v_path = os.path.join(c_dir, "vectors_int8.dat")
        m_path = os.path.join(c_dir, "metadata.jsonl")

        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Không tìm thấy QUANTIZED_MANIFEST.json tại {c_dir}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            m_data = json.load(f)

        count = m_data["total_vectors"]
        dim = m_data["vector_dimension"]

        if common_dim is None:
            common_dim = dim
        elif common_dim != dim:
            raise ValueError(f"Số chiều không khớp: {dim} vs {common_dim} tại {c_dir}")

        if os.path.exists(params_path):
            with open(params_path, "r", encoding="utf-8") as f:
                all_params.append(json.load(f))

        corpora_info.append({
            "name": corpus_names[idx],
            "dir": c_dir,
            "vector_file": v_path,
            "metadata_file": m_path,
            "start_idx": total_vectors,
            "end_idx": total_vectors + count,
            "count": count,
        })
        total_vectors += count

    offset_map = {
        "dataset_name": "Unified Quantized Vector Corpus",
        "total_vectors": total_vectors,
        "dimension": common_dim,
        "num_corpora": len(corpora_info),
        "corpora": corpora_info,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    map_path = os.path.join(output_dir, "corpus_offset_map.json")
    with open(map_path, "w", encoding="utf-8") as f:
        json.dump(offset_map, f, indent=2, ensure_ascii=False)

    # Tạo combined manifest
    combined_manifest = {
        "dataset_name": "Unified Quantized Vector Corpus (Combined Multi-Source)",
        "total_vectors": total_vectors,
        "vector_dimension": common_dim,
        "quantization_type": "Scalar Quantization 8-bit (SQ8)",
        "data_type": "int8 (1 byte per dimension)",
        "num_sources": len(corpora_info),
        "source_corpora": [c["name"] for c in corpora_info],
        "offset_map_file": "corpus_offset_map.json",
        "raw_float32_size_mb": round((total_vectors * common_dim * 4) / (1024 * 1024), 2),
        "quantized_size_mb": round((total_vectors * common_dim * 1) / (1024 * 1024), 2),
        "ram_saving_percent": 75.0,
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    manifest_path = os.path.join(output_dir, "COMBINED_MANIFEST.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(combined_manifest, f, indent=2, ensure_ascii=False)

    # Lưu tham số lượng tử hóa chung
    if all_params:
        params_out_path = os.path.join(output_dir, "quantization_params.json")
        with open(params_out_path, "w", encoding="utf-8") as f:
            json.dump(all_params[0], f, indent=2, ensure_ascii=False)

    logger.info(
        "Tạo kho hợp nhất thành công tại %s: %d vector (Tiết kiệm 75%% RAM)",
        output_dir,
        total_vectors,
    )
    return offset_map
