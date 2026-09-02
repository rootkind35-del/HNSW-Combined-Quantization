"""Module Lượng tử hóa vô hướng (Scalar Quantization - SQ8) nén vector 32-bit float thành 8-bit uint8."""

from typing import Optional, Tuple
import numpy as np


class ScalarQuantizer:
    """
    Bộ lượng tử hóa vô hướng SQ8:
    Nén các vector số thực float32 (4 bytes/chiều) thành số nguyên không dấu uint8 (1 byte/chiều).
    Giúp giảm 75% mức tiêu thụ bộ nhớ RAM cho việc lưu trữ vector và cho phép tăng tốc độ tính toán khoảng cách.
    """

    def __init__(self, per_channel: bool = True):
        """
        Khởi tạo bộ lượng tử hóa SQ8.

        Tham số:
            per_channel: Nếu True, tính toán min/max và hệ số tỉ lệ riêng biệt cho từng chiều đặc trưng (khuyên dùng).
                         Nếu False, tính toán min/max toàn cục trên toàn bộ mảng dữ liệu.
        """
        self.per_channel = per_channel
        self.min_vals: Optional[np.ndarray] = None
        self.scale: Optional[np.ndarray] = None
        self.dim: int = 0
        self.is_fitted: bool = False

    def fit(self, vectors: np.ndarray) -> "ScalarQuantizer":
        """
        Hiệu chuẩn (calibrate) dải giá trị min và max từ tập vector mẫu để xác định bước lượng tử hóa (step size).

        Tham số:
            vectors: Mảng vector 2 chiều kích thước (N, D).

        Trả về:
            Chính đối tượng ScalarQuantizer sau khi đã hiệu chuẩn.
        """
        if vectors.ndim != 2:
            raise ValueError("Mảng vector đầu vào phải là mảng 2 chiều (N, D)")

        self.dim = vectors.shape[1]
        axis = 0 if self.per_channel else None

        min_val = np.min(vectors, axis=axis, keepdims=True)
        max_val = np.max(vectors, axis=axis, keepdims=True)

        diff = max_val - min_val
        # Tránh lỗi chia cho 0 đối với các chiều có giá trị hằng số không đổi
        diff = np.where(diff == 0.0, 1.0, diff)

        self.min_vals = min_val.astype(np.float32)
        self.scale = (diff / 255.0).astype(np.float32)
        self.is_fitted = True
        return self

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """
        Chuyển đổi vector số thực float32 thành mảng số nguyên uint8 trong khoảng [0, 255].
        Công thức: uint8_val = clip(round((x - min) / scale), 0, 255)

        Tham số:
            vectors: Mảng vector float32 cần lượng tử hóa.

        Trả về:
            Mảng vector kiểu np.uint8 có cùng kích thước.
        """
        if not self.is_fitted:
            raise RuntimeError("Cần gọi phương thức fit() trước khi thực hiện lượng tử hóa dữ liệu.")

        v = np.ascontiguousarray(vectors, dtype=np.float32)
        normalized = (v - self.min_vals) / self.scale
        quantized = np.clip(np.round(normalized), 0, 255).astype(np.uint8)
        return quantized

    def dequantize(self, quantized_vectors: np.ndarray) -> np.ndarray:
        """
        Khôi phục vector xấp xỉ kiểu số thực float32 từ mảng uint8 đã nén.
        Công thức: float_val = uint8_val * scale + min

        Tham số:
            quantized_vectors: Mảng vector kiểu np.uint8.

        Trả về:
            Mảng vector khôi phục xấp xỉ kiểu float32.
        """
        if not self.is_fitted:
            raise RuntimeError("Cần gọi phương thức fit() trước khi giải lượng tử hóa dữ liệu.")

        q = np.ascontiguousarray(quantized_vectors, dtype=np.float32)
        reconstructed = q * self.scale + self.min_vals
        return reconstructed.astype(np.float32)

    def compute_distance(self, q1: np.ndarray, q2: np.ndarray) -> float:
        """
        Tính khoảng cách Euclid bình phương xấp xỉ trực tiếp giữa 2 vector uint8.
        Sử dụng phép trừ số nguyên int32 có bù hệ số tỉ lệ scale.

        Tham số:
            q1, q2: Hai vector uint8 1 chiều có cùng số chiều.

        Trả về:
            float: Khoảng cách L2 bình phương xấp xỉ.
        """
        diff = q1.astype(np.int32) - q2.astype(np.int32)
        scaled_diff = diff.astype(np.float32) * self.scale.flatten()
        return float(np.sum(scaled_diff ** 2))

    def compute_batch_distances(self, query_uint8: np.ndarray, dataset_uint8: np.ndarray) -> np.ndarray:
        """
        Tính toán khoảng cách xấp xỉ hàng loạt giữa 1 vector truy vấn uint8 và toàn bộ tập dữ liệu vector uint8 (N, D).

        Tham số:
            query_uint8: Vector truy vấn dạng uint8 (1 chiều hoặc 1xD).
            dataset_uint8: Mảng tập dữ liệu vector dạng uint8 (N, D).

        Trả về:
            Mảng 1 chiều chứa khoảng cách tới từng vector trong tập dữ liệu.
        """
        q = query_uint8.flatten().astype(np.int32)
        diff = dataset_uint8.astype(np.int32) - q
        scaled_diff = diff.astype(np.float32) * self.scale.flatten()
        return np.sum(scaled_diff ** 2, axis=1).astype(np.float32)

