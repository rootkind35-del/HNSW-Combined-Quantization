"""Asymmetric Distance Computation (ADC) and dynamic quantization for HNSW.

Implements per-vector row-wise 8-bit scalar quantization with float16 scale
and offset parameters, enabling asymmetric distance evaluation directly on
compressed representations without full dataset decompression.
"""

from typing import Tuple
import numpy as np


def quantize_adc(vectors: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Quantize vectors to uint8 and extract float16 scale and offset anchors for ADC.

    Args:
        vectors: 2D array of float32 vectors with shape (N, dim), or 1D array (dim,).

    Returns:
        Tuple of:
            - quantized_vectors: uint8 array of shape (N, dim)
            - scale: float16 array of shape (N, 1)
            - offset: float16 array of shape (N, 1)
    """
    arr = np.asarray(vectors, dtype=np.float32)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    min_val = np.min(arr, axis=1, keepdims=True)
    max_val = np.max(arr, axis=1, keepdims=True)

    range_val = max_val - min_val
    range_val[range_val == 0] = 1e-8

    scale = (range_val / 255.0).astype(np.float16)
    offset = min_val.astype(np.float16)

    normalized = (arr - min_val) / range_val
    quantized_vectors = np.clip(np.round(normalized * 255.0), 0, 255).astype(np.uint8)

    return quantized_vectors, scale, offset


def distance_adc(
    query_float32: np.ndarray,
    q_vector_uint8: np.ndarray,
    scale: np.float16,
    offset: np.float16,
) -> float:
    """Compute Asymmetric Euclidean (L2) Distance between query and quantized vector.

    Calculates distance directly in float32 without decompressing the entire index:
    approx_vector = (q_vector_uint8 * scale) + offset.

    Args:
        query_float32: Uncompressed query vector of shape (dim,).
        q_vector_uint8: Quantized candidate vector in uint8 of shape (dim,).
        scale: Per-vector scale factor (float16).
        offset: Per-vector offset (float16).

    Returns:
        Approximate L2 Euclidean distance as float.
    """
    q_float = np.asarray(query_float32, dtype=np.float32).flatten()
    s = float(scale)
    o = float(offset)
    approx_vector = (q_vector_uint8.astype(np.float32) * s) + o
    diff = q_float - approx_vector
    return float(np.linalg.norm(diff))


def exact_distance_l2(query: np.ndarray, vector: np.ndarray) -> float:
    """Compute exact Euclidean (L2) distance between two float32 vectors.

    Args:
        query: Query vector.
        vector: Target candidate vector.

    Returns:
        Exact L2 distance as float.
    """
    q = np.asarray(query, dtype=np.float32).flatten()
    v = np.asarray(vector, dtype=np.float32).flatten()
    return float(np.linalg.norm(q - v))
