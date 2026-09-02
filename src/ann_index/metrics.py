"""Evaluation metrics for Approximate Nearest Neighbor search algorithms."""

from typing import Dict, List, Union
import numpy as np


def compute_recall_at_k(
    ground_truth: np.ndarray,
    predictions: np.ndarray,
    k: int = 10,
) -> float:
    """
    Computes average Recall@K comparing predicted neighbor indices against ground truth.

    Args:
        ground_truth: 2D array of true nearest neighbor indices of shape (num_queries, >= k).
        predictions: 2D array of predicted neighbor indices of shape (num_queries, >= k).
        k: Cutoff rank for evaluation (default: 10).

    Returns:
        float: Average Recall@K value in the range [0.0, 1.0].
    """
    if ground_truth.ndim != 2 or predictions.ndim != 2:
        raise ValueError("Ground truth and predictions must be 2D arrays")

    num_queries = ground_truth.shape[0]
    if num_queries == 0:
        return 0.0

    if predictions.shape[0] != num_queries:
        raise ValueError(
            f"Query count mismatch: ground_truth has {num_queries}, predictions has {predictions.shape[0]}"
        )

    actual_k = min(k, ground_truth.shape[1], predictions.shape[1])
    if actual_k == 0:
        return 0.0

    total_hits = 0
    for i in range(num_queries):
        gt_set = set(ground_truth[i, :actual_k])
        pred_set = set(predictions[i, :actual_k])
        hits = len(gt_set.intersection(pred_set))
        total_hits += hits

    average_recall = total_hits / (num_queries * actual_k)
    return float(average_recall)


def compute_latency_stats(
    durations_seconds: Union[List[float], np.ndarray],
    num_queries: int,
) -> Dict[str, float]:
    """
    Calculates latency distribution percentiles and throughput (QPS).

    Args:
        durations_seconds: Sequence of query runtimes measured in seconds.
        num_queries: Total number of queries executed.

    Returns:
        Dict containing mean_ms, p50_ms, p95_ms, p99_ms, and qps.
    """
    arr = np.asarray(durations_seconds, dtype=np.float64)
    if len(arr) == 0:
        return {
            "mean_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "qps": 0.0,
        }

    ms = arr * 1000.0
    total_time = np.sum(arr)
    qps = float(num_queries / max(total_time, 1e-9))

    return {
        "mean_ms": round(float(np.mean(ms)), 3),
        "p50_ms": round(float(np.percentile(ms, 50)), 3),
        "p95_ms": round(float(np.percentile(ms, 95)), 3),
        "p99_ms": round(float(np.percentile(ms, 99)), 3),
        "qps": round(qps, 2),
    }
