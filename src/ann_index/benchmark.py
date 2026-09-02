"""Benchmarking framework for comparing ANN algorithms against Ground Truth."""

import time
from typing import Any, Dict, List
import numpy as np
from ann_index.base import BaseIndex
from ann_index.flat import FlatIndex
from ann_index.metrics import compute_latency_stats, compute_recall_at_k
from ann_data.utils import get_logger


class BenchmarkRunner:
    """Orchestrates comprehensive benchmark experiments measuring Build Time, RAM, Recall, Latency, and QPS."""

    def __init__(
        self,
        dataset: np.ndarray,
        queries: np.ndarray,
        metric: str = "l2",
        ground_truth_k: int = 50,
    ):
        self.dataset = np.ascontiguousarray(dataset, dtype=np.float32)
        self.queries = np.ascontiguousarray(queries, dtype=np.float32)
        self.metric = metric
        self.ground_truth_k = ground_truth_k
        self.logger = get_logger("BenchmarkRunner")

        self.num_vectors, self.dim = self.dataset.shape
        self.num_queries = len(self.queries)

        self.logger.info(
            "Initializing BenchmarkRunner: Dataset (%d, %d), Queries (%d, %d)",
            self.num_vectors,
            self.dim,
            self.num_queries,
            self.dim,
        )

        # Build baseline FlatIndex to generate ground truth
        self.flat_index = FlatIndex(metric=self.metric)
        self.flat_index.build(self.dataset)
        self.ground_truth_indices = self.flat_index.generate_ground_truth(
            self.queries, top_k=self.ground_truth_k
        )
        self.logger.info("Ground Truth computed successfully for %d queries", self.num_queries)

    def evaluate_index(
        self,
        index: BaseIndex,
        top_k: int = 10,
        repeat_runs: int = 3,
    ) -> Dict[str, Any]:
        """Runs thorough evaluation on a single index instance."""
        self.logger.info("Evaluating index: %s", index.name)

        # 1. Measure Build Time
        build_start = time.perf_counter()
        index.build(self.dataset)
        build_time_sec = time.perf_counter() - build_start

        # 2. Measure Memory
        ram_bytes = index.get_memory_bytes()
        ram_mb = ram_bytes / (1024 * 1024)

        # 3. Warmup Run
        _, _ = index.search(self.queries[: min(5, self.num_queries)], top_k=top_k)

        # 4. Measure Latency and QPS across repeats
        latencies = []
        last_predictions = None

        for _ in range(repeat_runs):
            for q_idx in range(self.num_queries):
                q_vec = self.queries[q_idx : q_idx + 1]
                t0 = time.perf_counter()
                preds, _ = index.search(q_vec, top_k=top_k)
                latencies.append(time.perf_counter() - t0)

        # Batch query for final recall check
        batch_preds, _ = index.search(self.queries, top_k=top_k)
        last_predictions = batch_preds

        # 5. Compute Metrics
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
        self.logger.info("Evaluation completed for %s: %s", index.name, result)
        return result

    def run_comparison(
        self, indices: List[BaseIndex], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Evaluates multiple algorithms and returns comparative summary table."""
        results = []
        for idx in indices:
            res = self.evaluate_index(idx, top_k=top_k)
            results.append(res)
        return results

    @staticmethod
    def format_markdown_table(results: List[Dict[str, Any]]) -> str:
        """Formats evaluation results into a clean markdown table."""
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
