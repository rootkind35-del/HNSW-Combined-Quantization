"""Scalar Quantization (SQ8) module for 8-bit vector compression."""

from typing import Optional, Tuple
import numpy as np


class ScalarQuantizer:
    """Compresses 32-bit float vectors into 8-bit integers (reducing RAM by 75%)."""

    def __init__(self, per_channel: bool = True):
        """
        Args:
            per_channel: If True, computes min/max scaling per dimension.
                         If False, computes global min/max across all elements.
        """
        self.per_channel = per_channel
        self.min_vals: Optional[np.ndarray] = None
        self.scale: Optional[np.ndarray] = None
        self.dim: int = 0
        self.is_fitted: bool = False

    def fit(self, vectors: np.ndarray) -> "ScalarQuantizer":
        """Calibrates quantization bounds based on training dataset vectors."""
        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array of shape (N, D)")

        self.dim = vectors.shape[1]
        axis = 0 if self.per_channel else None

        min_val = np.min(vectors, axis=axis, keepdims=True)
        max_val = np.max(vectors, axis=axis, keepdims=True)

        diff = max_val - min_val
        # Avoid division by zero for constant dimensions
        diff = np.where(diff == 0.0, 1.0, diff)

        self.min_vals = min_val.astype(np.float32)
        self.scale = (diff / 255.0).astype(np.float32)
        self.is_fitted = True
        return self

    def quantize(self, vectors: np.ndarray) -> np.ndarray:
        """Converts float32 vectors into uint8 arrays (0 to 255)."""
        if not self.is_fitted:
            raise RuntimeError("Quantizer must be fitted before quantizing data.")

        v = np.ascontiguousarray(vectors, dtype=np.float32)
        normalized = (v - self.min_vals) / self.scale
        quantized = np.clip(np.round(normalized), 0, 255).astype(np.uint8)
        return quantized

    def dequantize(self, quantized_vectors: np.ndarray) -> np.ndarray:
        """Reconstructs approximate float32 vectors from uint8 representation."""
        if not self.is_fitted:
            raise RuntimeError("Quantizer must be fitted before dequantizing data.")

        q = np.ascontiguousarray(quantized_vectors, dtype=np.float32)
        reconstructed = q * self.scale + self.min_vals
        return reconstructed.astype(np.float32)

    def compute_distance(self, q1: np.ndarray, q2: np.ndarray) -> float:
        """
        Computes approximate squared Euclidean distance directly between uint8 vectors
        using 32-bit integer arithmetic.
        """
        diff = q1.astype(np.int32) - q2.astype(np.int32)
        scaled_diff = diff.astype(np.float32) * self.scale.flatten()
        return float(np.sum(scaled_diff ** 2))

    def compute_batch_distances(self, query_uint8: np.ndarray, dataset_uint8: np.ndarray) -> np.ndarray:
        """
        Computes approximate distances between a single query (1D or 1xD) and all dataset vectors (NxD).
        """
        q = query_uint8.flatten().astype(np.int32)
        diff = dataset_uint8.astype(np.int32) - q
        scaled_diff = diff.astype(np.float32) * self.scale.flatten()
        return np.sum(scaled_diff ** 2, axis=1).astype(np.float32)
