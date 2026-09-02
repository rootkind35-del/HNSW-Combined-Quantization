"""Lớp cơ sở trừu tượng (Abstract Base Class) cho các cấu trúc chỉ mục tìm kiếm vector láng giềng gần đúng (ANN)."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class BaseIndex(ABC):
    """Giao diện trừu tượng định nghĩa các phương thức bắt buộc cho mọi thuật toán chỉ mục k-NN / ANN."""

    @abstractmethod
    def build(self, vectors: np.ndarray) -> None:
        """
        Xây dựng hoặc nạp cấu trúc chỉ mục tìm kiếm từ tập vector dữ liệu đầu vào.

        Tham số:
            vectors: Mảng numpy 2 chiều kiểu số thực, kích thước (N, D),
                     trong đó N là số lượng vector và D là số chiều không gian nhúng.
        """
        pass

    @abstractmethod
    def search(self, query_vectors: np.ndarray, top_k: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Thực hiện tìm kiếm Top-K láng giềng gần nhất cho một lô (batch) vector truy vấn.

        Tham số:
            query_vectors: Mảng numpy 2 chiều kích thước (num_queries, D) chứa các vector truy vấn.
            top_k: Số lượng phần tử láng giềng gần nhất cần truy xuất cho mỗi truy vấn (mặc định là 10).

        Trả về:
            Tuple gồm 2 mảng numpy:
                - indices: Mảng số nguyên kích thước (num_queries, top_k) chứa chỉ số định danh của các vector kết quả.
                - distances: Mảng số thực kích thước (num_queries, top_k) chứa khoảng cách tương ứng tới truy vấn.
        """
        pass

    @abstractmethod
    def get_memory_bytes(self) -> int:
        """
        Tính toán và trả về dung lượng bộ nhớ RAM (tính bằng byte) mà cấu trúc chỉ mục đang chiếm dụng.
        
        Trả về:
            int: Dung lượng RAM xấp xỉ tính bằng byte.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Trả về tên định danh của thuật toán kèm các siêu tham số cấu hình chính."""
        pass

