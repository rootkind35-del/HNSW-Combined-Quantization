"""Unit tests for the scalability stress test benchmarking script."""

import json
import os
import unittest
from scripts.run_scale_stress_test import run_scale_experiment


class TestStressBenchmark(unittest.TestCase):

    def setUp(self):
        self.output_dir = "tests/temp_stress_dir"
        os.makedirs(self.output_dir, exist_ok=True)
        self.scales = [20, 40]
        self.dim = 8
        self.num_queries = 4

    def tearDown(self):
        for f in ["scale_stress_results.json", "scale_stress_summary.md"]:
            p = os.path.join(self.output_dir, f)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        if os.path.exists(self.output_dir):
            try:
                os.rmdir(self.output_dir)
            except OSError:
                pass

    def test_run_scale_experiment_execution(self):
        res = run_scale_experiment(
            scales=self.scales,
            dim=self.dim,
            num_queries=self.num_queries,
            output_dir=self.output_dir,
        )

        self.assertEqual(len(res["records"]), len(self.scales))
        self.assertTrue(os.path.exists(res["json_path"]))
        self.assertTrue(os.path.exists(res["md_path"]))

        # Verify JSON content
        with open(res["json_path"], "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(len(data), 2)
            self.assertIn("standard_hnsw", data[0])
            self.assertIn("two_tier_hnsw", data[0])
            self.assertGreater(data[0]["ram_reduction_pct"], 0.0)

        # Verify Markdown structure
        md = res["markdown_report"]
        self.assertIn("Báo cáo Thực nghiệm Quy mô Lớn", md)
        self.assertIn("Standard HNSW", md)
        self.assertIn("Two-Tier HNSW", md)


if __name__ == "__main__":
    unittest.main()
