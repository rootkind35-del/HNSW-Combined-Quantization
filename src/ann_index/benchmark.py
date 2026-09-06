"""Khung thử nghiệm đối chuẩn (Benchmarking Framework) đánh giá các thuật toán ANN so với Ground Truth."""

import time
from typing import Any, Dict, List, Optional
import numpy as np
from ann_index.base import BaseIndex
from ann_index.flat import FlatIndex
from ann_index.metrics import compute_latency_stats, compute_recall_at_k
from ann_data.utils import get_logger


class BenchmarkRunner:
    """
    Trình điều phối thực nghiệm đối chuẩn toàn diện:
    Đo đạc 5 chỉ số cốt lõi: Thời gian dựng chỉ mục (Build Time), Dung lượng RAM, Độ chính xác Recall@K,
    Phân phối độ trễ (Latency p50, p95, p99), và Thông lượng truy vấn (QPS).
    """

    def __init__(
        self,
        dataset: np.ndarray,
        queries: np.ndarray,
        metric: str = "l2",
        ground_truth_k: int = 50,
        ground_truth_indices: Optional[np.ndarray] = None,
    ):
        """
        Khởi tạo bộ chạy thực nghiệm đối chuẩn.

        Tham số:
            dataset: Mảng vector dữ liệu float32 (N, D).
            queries: Mảng vector truy vấn float32 (num_queries, D).
            metric: Độ đo khoảng cách ('l2' hoặc 'cosine').
            ground_truth_k: Số lượng láng giềng mốc chuẩn cần tính trước bằng FlatIndex.
            ground_truth_indices: Mốc chuẩn tính sẵn (nếu có, ví dụ từ tập dữ liệu SIFT).
        """
        self.dataset = np.ascontiguousarray(dataset, dtype=np.float32)
        self.queries = np.ascontiguousarray(queries, dtype=np.float32)
        self.metric = metric
        self.ground_truth_k = ground_truth_k
        self.logger = get_logger("BenchmarkRunner")

        self.num_vectors, self.dim = self.dataset.shape
        self.num_queries = len(self.queries)

        self.logger.info(
            "Khởi tạo BenchmarkRunner: Tập dữ liệu (%d, %d), Tập truy vấn (%d, %d)",
            self.num_vectors,
            self.dim,
            self.num_queries,
            self.dim,
        )

        if ground_truth_indices is not None:
            self.ground_truth_indices = ground_truth_indices
            self.flat_index = None
            self.logger.info("Sử dụng mốc chuẩn Ground Truth có sẵn (%s)", ground_truth_indices.shape)
        else:
            # Xây dựng mốc chuẩn Ground Truth bằng thuật toán vét cạn chính xác FlatIndex
            self.flat_index = FlatIndex(metric=self.metric)
            self.flat_index.build(self.dataset)
            self.ground_truth_indices = self.flat_index.generate_ground_truth(
                self.queries, top_k=self.ground_truth_k
            )
            self.logger.info("Đã sinh xong mốc chuẩn Ground Truth cho %d câu truy vấn", self.num_queries)

    def evaluate_index(
        self,
        index: BaseIndex,
        top_k: int = 10,
        repeat_runs: int = 3,
    ) -> Dict[str, Any]:
        """
        Đo lường chi tiết hiệu năng của một thể hiện chỉ mục thuật toán.

        Tham số:
            index: Thể hiện của thuật toán cần kiểm thử (kế thừa từ BaseIndex).
            top_k: Số lượng kết quả láng giềng đánh giá.
            repeat_runs: Số lượt chạy lặp lại để lấy trung bình thống kê độ trễ ổn định.

        Trả về:
            Dict chứa toàn bộ các chỉ số đo lường thực nghiệm.
        """
        self.logger.info("Bắt đầu đánh giá chỉ mục: %s", index.name)

        # 1. Đo thời gian xây dựng chỉ mục (Build Time)
        build_start = time.perf_counter()
        index.build(self.dataset)
        build_time_sec = time.perf_counter() - build_start

        # 2. Đo dung lượng bộ nhớ RAM tiêu thụ
        ram_bytes = index.get_memory_bytes()
        ram_mb = ram_bytes / (1024 * 1024)

        # 3. Lượt chạy khởi động bộ đệm (Warmup Run)
        _, _ = index.search(self.queries[: min(5, self.num_queries)], top_k=top_k)

        # 4. Đo đạc độ trễ từng câu truy vấn và thông lượng qua nhiều lượt lặp
        latencies = []
        last_predictions = None

        for _ in range(repeat_runs):
            for q_idx in range(self.num_queries):
                q_vec = self.queries[q_idx : q_idx + 1]
                t0 = time.perf_counter()
                preds, _ = index.search(q_vec, top_k=top_k)
                latencies.append(time.perf_counter() - t0)

        # Truy vấn lô để tính Recall@K chính xác
        batch_preds, _ = index.search(self.queries, top_k=top_k)
        last_predictions = batch_preds

        # 5. Tổng hợp các chỉ số thống kê
        latency_metrics = compute_latency_stats(latencies, num_queries=len(latencies))
        recall = compute_recall_at_k(self.ground_truth_indices, last_predictions, k=top_k)

        result = {
            "algorithm": index.name,
            "build_time_sec": round(build_time_sec, 3),
            "ram_mb": round(ram_mb, 2),
            "recall_at_10": round(recall * 100.0, 2),
            "latency_p50_ms": latency_metrics["p50_ms"],
            "latency_p95_ms": latency_metrics["p95_ms"],
            "latency_p99_ms": latency_metrics["p99_ms"],
            "qps": latency_metrics["qps"],
        }
        self.logger.info("Hoàn tất đánh giá cho %s: %s", index.name, result)
        return result

    def run_comparison(
        self, indices: List[BaseIndex], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Chạy kiểm thử so sánh lần lượt toàn bộ danh sách các thuật toán cấu hình.

        Tham số:
            indices: Danh sách các chỉ mục thuật toán cần đối chuẩn.
            top_k: Số lượng láng giềng đánh giá.

        Trả về:
            Danh sách kết quả đo lường của từng thuật toán.
        """
        results = []
        for idx in indices:
            res = self.evaluate_index(idx, top_k=top_k)
            results.append(res)
        return results

    @staticmethod
    def format_markdown_table(results: List[Dict[str, Any]]) -> str:
        """Định dạng bảng kết quả so sánh đối chuẩn thành định dạng Markdown tiêu chuẩn."""
        headers = [
            "Thuật toán / Cấu hình",
            "Build Time (s)",
            "RAM (MB)",
            "Recall@10 (%)",
            "Latency p50 (ms)",
            "Latency p95 (ms)",
            "QPS",
        ]
        lines = [
            "| " + " | ".join(headers) + " |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
        for r in results:
            row = [
                r["algorithm"],
                f"{r['build_time_sec']} s",
                f"{r['ram_mb']} MB",
                f"{r['recall_at_10']}%",
                f"{r['latency_p50_ms']} ms",
                f"{r['latency_p95_ms']} ms",
                f"{r['qps']}",
            ]
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

