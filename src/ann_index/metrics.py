"""Các chỉ số đo lường và đánh giá hiệu năng thuật toán tìm kiếm láng giềng gần đúng (ANN)."""

from typing import Dict, List, Union
import numpy as np


def compute_recall_at_k(
    ground_truth: np.ndarray,
    predictions: np.ndarray,
    k: int = 10,
) -> float:
    """
    Tính toán độ chính xác thu hồi trung bình Recall@K:
    So sánh tập chỉ số láng giềng dự đoán của thuật toán ANN với tập mốc chuẩn tuyệt đối (Ground Truth).
    Recall@K = |Predictions_K ∩ GroundTruth_K| / K

    Tham số:
        ground_truth: Mảng 2 chiều chứa chỉ số láng giềng chính xác tuyệt đối (num_queries, >= k).
        predictions: Mảng 2 chiều chứa chỉ số láng giềng dự đoán từ thuật toán ANN (num_queries, >= k).
        k: Ngưỡng xếp hạng đánh giá (mặc định k = 10).

    Trả về:
        float: Giá trị Recall@K trung bình trong khoảng [0.0, 1.0].
    """
    if ground_truth.ndim != 2 or predictions.ndim != 2:
        raise ValueError("Ground truth và predictions bắt buộc phải là mảng 2 chiều")

    num_queries = ground_truth.shape[0]
    if num_queries == 0:
        return 0.0

    if predictions.shape[0] != num_queries:
        raise ValueError(
            f"Lệch số lượng câu truy vấn: ground_truth có {num_queries}, predictions có {predictions.shape[0]}"
        )

    actual_k = min(k, ground_truth.shape[1], predictions.shape[1])
    if actual_k == 0:
        return 0.0

    total_hits = 0
    for i in range(num_queries):
        gt_set = set(ground_truth[i, :actual_k])
        pred_set = set(predictions[i, :actual_k])
        # Đếm số phần tử dự đoán trùng khớp với mốc chuẩn
        hits = len(gt_set.intersection(pred_set))
        total_hits += hits

    average_recall = total_hits / (num_queries * actual_k)
    return float(average_recall)


def compute_latency_stats(
    durations_seconds: Union[List[float], np.ndarray],
    num_queries: int,
) -> Dict[str, float]:
    """
    Tính toán phân phối độ trễ (latency percentiles) và thông lượng xử lý truy vấn (QPS - Queries Per Second).

    Tham số:
        durations_seconds: Danh sách hoặc mảng thời gian thực thi của từng truy vấn (tính bằng giây).
        num_queries: Tổng số câu truy vấn đã thực hiện.

    Trả về:
        Dict chứa các chỉ số:
            - mean_ms: Độ trễ trung bình (mili-giây).
            - p50_ms: Độ trễ trung vị phân vị 50 (mili-giây).
            - p95_ms: Độ trễ phân vị 95 (mili-giây).
            - p99_ms: Độ trễ phân vị 99 (mili-giây).
            - qps: Số lượng truy vấn phục vụ được trong 1 giây.
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

