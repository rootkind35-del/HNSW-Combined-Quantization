"""Các hàm tiện ích hệ thống cho ghi nhật ký (logging), bấm giờ (timing) và phân khối luồng (streaming)."""

import logging
import sys
import time
from contextlib import contextmanager
from typing import Generator, Iterable, List


def get_logger(name: str = "ann_data", level: int = logging.INFO) -> logging.Logger:
    """
    Tạo hoặc lấy bộ ghi nhật ký (logger) đã được cấu hình định dạng chuẩn và hỗ trợ UTF-8 cho Windows console.

    Tham số:
        name: Tên của logger.
        level: Cấp độ ghi nhật ký (mặc định INFO).

    Trả về:
        logging.Logger: Đối tượng logger sẵn sàng ghi thông điệp.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        # Đảm bảo stdout xử lý mượt mà ký tự tiếng Việt Unicode trên Windows mà không bị lỗi mã hóa cp1252
        if hasattr(sys.stdout, "reconfigure"):
            try:
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


@contextmanager
def timer(name: str, logger: logging.Logger = None):
    """
    Bộ quản lý ngữ cảnh (Context Manager) đo đạc thời gian thực thi của một đoạn mã.

    Tham số:
        name: Tên khối tác vụ đang đo đạc.
        logger: Bộ ghi nhật ký tùy chọn (nếu None sẽ dùng lệnh print chuẩn).
    """
    start_time = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start_time
    msg = f"Tác vụ '{name}' hoàn thành trong {elapsed:.4f} giây"
    if logger:
        logger.info(msg)
    else:
        print(msg)


def chunk_stream(iterable: Iterable[str], chunk_size: int) -> Generator[List[str], None, None]:
    """
    Phân chia một luồng dữ liệu liên tục thành các khối (chunks) có kích thước cố định,
    giúp xử lý luồng lớn mà không nạp toàn bộ dữ liệu vào bộ nhớ RAM.

    Tham số:
        iterable: Luồng dữ liệu nguồn.
        chunk_size: Kích thước của mỗi khối xử lý.

    Sinh ra:
        Từng khối danh sách phần tử kích thước chunk_size.
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk

