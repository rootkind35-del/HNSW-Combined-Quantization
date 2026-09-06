"""Bộ nạp và xử lý các tập dữ liệu đối chuẩn chuẩn mực (SIFT10K, SIFT1M) định dạng fvecs / ivecs."""

import os
import tarfile
import urllib.request
from typing import Dict, Optional, Tuple
import numpy as np
from ann_data.utils import get_logger

logger = get_logger("benchmark_loader")


def read_fvecs(file_path: str, max_vectors: int = -1) -> np.ndarray:
    """
    Đọc tệp vector float32 định dạng .fvecs (Inria Texmex).
    Cấu trúc mỗi vector: 4 byte int32 (số chiều d) theo sau bởi d * 4 byte float32.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp: {file_path}")

    # Đọc chiều d từ 4 byte đầu tiên
    dim = int(np.fromfile(file_path, dtype=np.int32, count=1)[0])
    record_size = dim + 1
    file_size_bytes = os.path.getsize(file_path)
    total_vectors = file_size_bytes // (record_size * 4)

    if max_vectors > 0:
        total_vectors = min(total_vectors, max_vectors)

    raw_data = np.fromfile(file_path, dtype=np.float32, count=total_vectors * record_size)
    reshaped = raw_data.reshape((total_vectors, record_size))
    # Bỏ cột đầu tiên chứa giá trị dim
    vectors = reshaped[:, 1:].copy()
    return vectors.astype(np.float32)


def read_ivecs(file_path: str, max_vectors: int = -1) -> np.ndarray:
    """
    Đọc tệp chỉ số nguyên int32 định dạng .ivecs (Ground Truth Inria Texmex).
    Cấu trúc mỗi vector: 4 byte int32 (số chiều k) theo sau bởi k * 4 byte int32.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy tệp: {file_path}")

    k = int(np.fromfile(file_path, dtype=np.int32, count=1)[0])
    record_size = k + 1
    file_size_bytes = os.path.getsize(file_path)
    total_vectors = file_size_bytes // (record_size * 4)

    if max_vectors > 0:
        total_vectors = min(total_vectors, max_vectors)

    raw_data = np.fromfile(file_path, dtype=np.int32, count=total_vectors * record_size)
    reshaped = raw_data.reshape((total_vectors, record_size))
    indices = reshaped[:, 1:].copy()
    return indices.astype(np.int64)


class BenchmarkDatasetLoader:
    """Trình quản lý và nạp tập dữ liệu đối chuẩn SIFT."""

    DATASET_URLS = {
        "sift10k": "ftp://ftp.irisa.fr/local/texmex/corpus/siftsmall.tar.gz",
        "sift1m": "ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz",
    }

    # Mirror HTTP phòng trường hợp FTP bị chặn
    HTTP_MIRRORS = {
        "sift10k": "https://raw.githubusercontent.com/erikbern/ann-benchmarks/master/data/siftsmall.tar.gz",
    }

    def __init__(self, base_dir: str = "data/raw/benchmarks"):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def download_and_extract(self, dataset_name: str = "sift10k") -> str:
        """Tải và giải nén bộ dữ liệu nếu chưa tồn tại trên đĩa."""
        dataset_name = dataset_name.lower()
        sub_dir = "siftsmall" if dataset_name == "sift10k" else "sift"
        target_dir = os.path.join(self.base_dir, sub_dir)

        base_file = os.path.join(target_dir, f"{sub_dir}_base.fvecs")
        if os.path.exists(base_file):
            logger.info("Bộ dữ liệu %s đã tồn tại tại: %s", dataset_name, target_dir)
            return target_dir

        tar_filename = f"{sub_dir}.tar.gz"
        archive_path = os.path.join(self.base_dir, tar_filename)

        urls = [
            f"ftp://ftp.irisa.fr/local/texmex/corpus/{tar_filename}",
            f"http://corpus-texmex.irisa.fr/{tar_filename}",
        ]

        downloaded = False
        for url in urls:
            logger.info("Đang tải %s từ: %s", dataset_name, url)
            try:
                urllib.request.urlretrieve(url, archive_path)
                downloaded = True
                logger.info("Tải thành công tệp lưu trữ: %s", archive_path)
                break
            except Exception as e:
                logger.warning("Không thể tải từ %s: %s", url, str(e))

        if not downloaded:
            raise RuntimeError(f"Không thể tải bộ dữ liệu {dataset_name} từ tất cả các nguồn.")

        logger.info("Đang giải nén %s ...", archive_path)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=self.base_dir)

        if os.path.exists(archive_path):
            os.remove(archive_path)

        logger.info("Giải nén hoàn tất tại: %s", target_dir)
        return target_dir

    def load_dataset(
        self, dataset_name: str = "sift10k", max_base: int = -1
    ) -> Dict[str, np.ndarray]:
        """
        Nạp toàn bộ tập dữ liệu (base, query, groundtruth).

        Trả về:
            Dict chứa:
                'base': mảng (N, D) float32
                'query': mảng (Q, D) float32
                'groundtruth': mảng (Q, K) int64
        """
        sub_dir = "siftsmall" if dataset_name.lower() == "sift10k" else "sift"
        target_dir = os.path.join(self.base_dir, sub_dir)
        base_file = os.path.join(target_dir, f"{sub_dir}_base.fvecs")

        if not os.path.exists(base_file):
            target_dir = self.download_and_extract(dataset_name)

        base_path = os.path.join(target_dir, f"{sub_dir}_base.fvecs")
        query_path = os.path.join(target_dir, f"{sub_dir}_query.fvecs")
        gt_path = os.path.join(target_dir, f"{sub_dir}_groundtruth.ivecs")

        logger.info("Đang nạp dữ liệu %s ...", dataset_name)
        base_vectors = read_fvecs(base_path, max_vectors=max_base)
        query_vectors = read_fvecs(query_path)
        ground_truth = read_ivecs(gt_path)

        logger.info(
            "Nạp thành công %s: Base %s, Query %s, GroundTruth %s",
            dataset_name,
            base_vectors.shape,
            query_vectors.shape,
            ground_truth.shape,
        )

        return {
            "base": base_vectors,
            "query": query_vectors,
            "groundtruth": ground_truth,
        }
