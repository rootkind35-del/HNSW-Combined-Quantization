#!/usr/bin/env python
"""Kịch bản ghép nối hai kho vector lượng tử hóa thành kho hợp nhất quy mô 32,5 triệu vector.

Sử dụng kiến trúc Zero-Copy Virtual Federation để tạo bản đồ định danh toàn cục
mà không sao chép nhân bản các tệp metadata 35 GB gây tràn ổ đĩa SSD.
"""

import argparse
import os
import shutil
import sys
from typing import List
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from ann_data.utils import get_logger
from quantizer.unified_corpus import UnifiedQuantizedCorpus, create_unified_corpus

logger = get_logger("scripts.merge_quantized_corpora")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Ghép nối 2 kho vector lượng tử hóa int8 thành kho hợp nhất 32,5M vector"
    )
    parser.add_argument(
        "--corpus-dirs",
        nargs="+",
        default=["data/quantized", "data/quantized_wiki"],
        help="Danh sách các thư mục chứa vector int8 đã lượng tử hóa",
    )
    parser.add_argument(
        "--names",
        nargs="+",
        default=["news_legal", "wikipedia"],
        help="Tên nhãn định danh của từng kho dữ liệu",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/quantized_combined",
        help="Thư mục đích lưu trữ thông tin kho hợp nhất",
    )
    parser.add_argument(
        "--create-continuous-dat",
        action="store_true",
        help="Gộp tệp nhị phân vectors_int8.dat liên tục nếu dung lượng ổ đĩa SSD cho phép",
    )
    return parser.parse_args()


def check_disk_space(required_bytes: int, target_dir: str) -> bool:
    """Kiểm tra xem dung lượng đĩa còn đủ cho thao tác sao chép không."""
    total, used, free = shutil.disk_usage(os.path.abspath(target_dir))
    free_gb = free / (1024 ** 3)
    req_gb = required_bytes / (1024 ** 3)
    logger.info("Dung lượng đĩa trống: %.2f GB | Yêu cầu: %.2f GB", free_gb, req_gb)
    # Giữ lại ít nhất 5 GB đệm an toàn
    return free > (required_bytes + 5 * 1024 ** 3)


def main():
    args = parse_args()

    # Kiểm tra tồn tại các kho đầu vào
    for c_dir in args.corpus_dirs:
        manifest = os.path.join(c_dir, "QUANTIZED_MANIFEST.json")
        if not os.path.exists(manifest):
            logger.error("Không tìm thấy kho lượng tử hóa tại: %s", c_dir)
            logger.error("Vui lòng đợi tiến trình lượng tử hóa của kho này hoàn tất trước khi ghép nối.")
            sys.exit(1)

    logger.info("=" * 70)
    logger.info("BẮT ĐẦU GHÉP NỐI ĐA KHO VECTOR LƯỢNG TỬ HÓA (ZERO-COPY FEDERATION)")
    logger.info("Các kho đầu vào: %s", args.corpus_dirs)
    logger.info("Thư mục đầu ra: %s", args.output_dir)
    logger.info("=" * 70)

    # 1. Tạo bản đồ ánh xạ offset Zero-Copy
    offset_map = create_unified_corpus(
        corpus_dirs=args.corpus_dirs,
        output_dir=args.output_dir,
        corpus_names=args.names,
    )

    total_vectors = offset_map["total_vectors"]
    dim = offset_map["dimension"]
    logger.info("Tổng số vector trong kho hợp nhất: %d vector (%d chiều)", total_vectors, dim)

    # 2. Tùy chọn gộp tệp vectors_int8.dat liên tục
    if args.create_continuous_dat:
        total_vector_bytes = total_vectors * dim * 1
        if check_disk_space(total_vector_bytes, args.output_dir):
            out_dat = os.path.join(args.output_dir, "vectors_int8.dat")
            logger.info("Đang ghép nối vật lý tệp nhị phân vector ra: %s (%.2f GB)...", out_dat, total_vector_bytes / (1024 ** 3))
            
            with open(out_dat, "wb") as f_out:
                for c_info in offset_map["corpora"]:
                    src_v = c_info["vector_file"]
                    logger.info("  Đang truyền dữ liệu từ: %s (%d vector)...", src_v, c_info["count"])
                    with open(src_v, "rb") as f_in:
                        shutil.copyfileobj(f_in, f_out, length=64 * 1024 * 1024)
            logger.info("Đã hoàn tất ghép nối tệp nhị phân vector liên tục.")
        else:
            logger.warning(
                "Không đủ dung lượng đĩa an toàn (cần %.2f GB + 5 GB đệm). Giữ nguyên cơ chế Zero-Copy Virtual Memmap.",
                total_vector_bytes / (1024 ** 3),
            )

    # 3. Kiểm tra tính toàn vẹn của kho hợp nhất
    corpus = UnifiedQuantizedCorpus(args.output_dir)
    test_idx_first = 0
    test_idx_last = total_vectors - 1
    mid_idx = total_vectors // 2

    vec_first = corpus.get_vector(test_idx_first)
    vec_mid = corpus.get_vector(mid_idx)
    vec_last = corpus.get_vector(test_idx_last)

    assert vec_first.shape == (dim,), "Lỗi kích thước vector đầu"
    assert vec_mid.shape == (dim,), "Lỗi kích thước vector giữa"
    assert vec_last.shape == (dim,), "Lỗi kích thước vector cuối"

    meta_first = corpus.get_metadata(test_idx_first)
    logger.info("Mẫu metadata đầu [ID 0]: Nguồn '%s' | Tiêu đề: '%s'", meta_first.get("corpus_source"), meta_first.get("title", "")[:50])

    corpus.close()

    logger.info("=" * 70)
    logger.info("GHÉP NỐI KHO HOÀN TẤT VÀ XÁC THỰC THÀNH CÔNG: %d VECTOR", total_vectors)
    logger.info("Sẵn sàng cho Giai đoạn 1: Xây dựng đồ thị Two-Tier HNSW!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
