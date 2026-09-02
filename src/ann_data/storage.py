"""Module quản lý lưu trữ vector nhị phân trên đĩa SSD thông qua ánh xạ bộ nhớ (numpy.memmap)."""

import os
from typing import List, Optional, Tuple
import numpy as np


class MemmapStorage:
    """
    Quản lý lưu trữ mảng vector liên tục trên đĩa thông qua kỹ thuật ánh xạ bộ nhớ (Memory Mapping).
    Cho phép đọc ngẫu nhiên và ghi dữ liệu hàng chục gigabyte (như tập 10 triệu vector float32 ~ 15.36 GB)
    mà không phải nạp toàn bộ vào bộ nhớ RAM, duy trì mức tiêu thụ RAM luôn phẳng và cực thấp (< 150 MB).
    """

    def __init__(
        self,
        file_path: str,
        max_records: int,
        dim: int,
        dtype: str = "float32",
        mode: str = "w+",
    ):
        """
        Khởi tạo đối tượng MemmapStorage.

        Tham số:
            file_path: Đường dẫn tệp nhị phân lưu trữ (ví dụ: data/processed/hf_10m_vectors.dat).
            max_records: Số lượng vector tối đa dự kiến lưu trữ (ví dụ: 10.000.000).
            dim: Số chiều không gian vector (ví dụ: 384).
            dtype: Kiểu dữ liệu số học (mặc định float32 = 4 bytes/chiều).
            mode: Chế độ mở tệp ('w+' để tạo mới hoặc ghi đè, 'r' để chỉ đọc, 'r+' để đọc/ghi).
        """
        self.file_path = file_path
        self.max_records = max_records
        self.dim = dim
        self.dtype = np.dtype(dtype)
        self.mode = mode
        self.current_count = 0
        
        # Đảm bảo thư mục cha chứa tệp tồn tại
        parent_dir = os.path.dirname(os.path.abspath(file_path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        self._mmap: Optional[np.memmap] = None
        self._initialize_storage()

    def _initialize_storage(self) -> None:
        """Khởi tạo mảng ánh xạ bộ nhớ np.memmap trỏ tới tệp nhị phân trên đĩa SSD."""
        self._mmap = np.memmap(
            self.file_path,
            dtype=self.dtype,
            mode=self.mode,
            shape=(self.max_records, self.dim),
        )

    def append_batch(self, vectors: np.ndarray) -> Tuple[int, int]:
        """
        Ghi nối tiếp một lô vector mới vào tệp bộ nhớ đệm memmap.
        
        Tham số:
            vectors: Mảng 2 chiều chứa các vector cần ghi.

        Trả về:
            Tuple[int, int]: (start_index, end_index) khoảng chỉ số vừa được ghi trong tệp.
        """
        if self._mmap is None:
            raise RuntimeError("Bộ lưu trữ Memmap đã bị đóng.")

        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        num_vectors, vector_dim = vectors.shape
        if vector_dim != self.dim:
            raise ValueError(f"Lệch số chiều vector: mong đợi {self.dim}, nhận được {vector_dim}")

        start_idx = self.current_count
        end_idx = start_idx + num_vectors

        if end_idx > self.max_records:
            raise OverflowError(
                f"Vượt quá dung lượng tối đa của tệp: hiện tại {start_idx}, thêm {num_vectors}, tối đa {self.max_records}"
            )

        self._mmap[start_idx:end_idx] = vectors.astype(self.dtype)
        self.current_count = end_idx
        self.flush()
        return start_idx, end_idx

    def read_slice(self, start_idx: int, end_idx: int) -> np.ndarray:
        """
        Đọc một lát cắt vector liên tục từ vị trí start_idx đến end_idx.

        Tham số:
            start_idx: Vị trí bắt đầu.
            end_idx: Vị trí kết thúc.

        Trả về:
            Mảng numpy chứa các vector được trích xuất.
        """
        if self._mmap is None:
            raise RuntimeError("Bộ lưu trữ Memmap đã bị đóng.")
        return np.array(self._mmap[start_idx:end_idx])

    def read_indices(self, indices: List[int]) -> np.ndarray:
        """
        Đọc ngẫu nhiên các vector tại danh sách chỉ số cụ thể (dùng trong pha Tái xếp hạng Tier 2).

        Tham số:
            indices: Danh sách các chỉ số định danh cần đọc.

        Trả về:
            Mảng numpy chứa đúng các vector ứng viên cần truy xuất từ SSD.
        """
        if self._mmap is None:
            raise RuntimeError("Bộ lưu trữ Memmap đã bị đóng.")
        return np.array(self._mmap[indices])

    def flush(self) -> None:
        """Đồng bộ và đẩy toàn bộ dữ liệu đang sửa đổi từ RAM xuống đĩa vật lý."""
        if self._mmap is not None:
            self._mmap.flush()

    def close(self) -> None:
        """Xả toàn bộ dữ liệu và giải phóng con trỏ ánh xạ bộ nhớ."""
        if self._mmap is not None:
            self._mmap.flush()
            del self._mmap
            self._mmap = None

    def __enter__(self) -> "MemmapStorage":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

