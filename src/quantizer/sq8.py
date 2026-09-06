"""Lượng tử hóa vô hướng 8-bit (Scalar Quantization SQ8) cho vector đặc trưng."""

from typing import Dict, Optional, Tuple
import numpy as np


class ScalarQuantizer8:
    """Lượng tử hóa vector float32 sang int8 và giải lượng tử hóa (dequantization)."""

    def __init__(self):
        self.min_vals: Optional[np.ndarray] = None
        self.max_vals: Optional[np.ndarray] = None
        self.scales: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def fit(self, vectors: np.ndarray) -> "ScalarQuantizer8":
        """
        Huấn luyện các tham số thang đo min/max trên tập vector đại diện.

        Tham số:
            vectors: Mảng vector float32 (N, D).
        """
        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        # Tính min và max trên từng chiều không gian để giảm thiểu sai số
        self.min_vals = np.min(vectors, axis=0)
        self.max_vals = np.max(vectors, axis=0)
        
        diff = self.max_vals - self.min_vals
        # Tránh chia cho 0
        diff[diff < 1e-8] = 1.0
        self.scales = diff / 255.0
        self.is_fitted = True
        return self

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """
        Nén vector từ float32 (4 bytes) sang int8 (1 byte).

        Tham số:
            vectors: Mảng vector float32 (N, D).

        Trả về:
            Mảng vector int8 (N, D) có giá trị trong khoảng [-128, 127].
        """
        if not self.is_fitted:
            self.fit(vectors)

        vectors = np.ascontiguousarray(vectors, dtype=np.float32)
        # Chuẩn hóa về dải [0, 255]
        normalized = np.clip((vectors - self.min_vals) / self.scales, 0, 255)
        # Dịch về dải [-128, 127] của signed int8
        int8_vecs = np.round(normalized - 128.0).astype(np.int8)
        return int8_vecs

    def dequantize(self, quantized_vectors: np.ndarray) -> np.ndarray:
        """
        Giải nén khôi phục vector xấp xỉ từ int8 sang float32.

        Tham số:
            quantized_vectors: Mảng vector int8 (N, D).

        Trả về:
            Mảng vector float32 xấp xỉ (N, D).
        """
        if not self.is_fitted:
            raise ValueError("Bộ lượng tử hóa chưa được huấn luyện tham số fit().")

        q = np.ascontiguousarray(quantized_vectors, dtype=np.float32)
        # Dịch ngược từ [-128, 127] về [0, 255] rồi nhân tỉ lệ scale
        reconstructed = (q + 128.0) * self.scales + self.min_vals
        return reconstructed.astype(np.float32)

    def compute_reconstruction_error(self, original_vectors: np.ndarray) -> Dict[str, float]:
        """Đo lường sai số bình phương trung bình (MSE) và tỷ lệ nén."""
        quantized = self.quantize(original_vectors)
        reconstructed = self.dequantize(quantized)
        mse = float(np.mean((original_vectors - reconstructed) ** 2))
        cosine_sim = float(np.mean(
            np.sum(original_vectors * reconstructed, axis=1) /
            (np.linalg.norm(original_vectors, axis=1) * np.linalg.norm(reconstructed, axis=1) + 1e-12)
        ))

        return {
            "mse_loss": round(mse, 6),
            "mean_cosine_similarity": round(cosine_sim, 5),
            "compression_ratio": 4.0,  # 32-bit float / 8-bit int = 4x
            "ram_saving_percent": 75.0,
        }

    def export_params(self) -> Dict[str, list]:
        """Xuất các tham số cấu hình ra dict để lưu JSON."""
        return {
            "min_vals": self.min_vals.tolist() if self.min_vals is not None else [],
            "max_vals": self.max_vals.tolist() if self.max_vals is not None else [],
            "scales": self.scales.tolist() if self.scales is not None else [],
        }

    def load_params(self, params: Dict[str, list]) -> "ScalarQuantizer8":
        """Nạp tham số cấu hình từ dict."""
        self.min_vals = np.array(params["min_vals"], dtype=np.float32)
        self.max_vals = np.array(params["max_vals"], dtype=np.float32)
        self.scales = np.array(params["scales"], dtype=np.float32)
        self.is_fitted = True
        return self
