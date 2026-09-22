"""Adversarial edge case and schema validation tests for Search API and CLI bridge.

Tests cover empty queries, special characters, unicode strings, long text,
high top_k, non-existent categories, CLI argument handling, shards_probed integrity,
candidate schema completeness, and HTTP error handling.
"""

import json
import os
import subprocess
import sys
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")
SCRIPTS_DIR = os.path.join(REPO_ROOT, "dashboard", "scripts")
for path in [SRC_DIR, SCRIPTS_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

from search_service import SearchHandler, perform_search


class TestSearchServiceEdgeCases(unittest.TestCase):
    """Empirical adversarial edge case tests for search_service.py perform_search."""

    def test_empty_and_whitespace_query(self):
        """Empty or whitespace-only queries must complete without unhandled exceptions."""
        for query in ["", "   ", "\t\n\r"]:
            resp = perform_search(query, top_k=3)
            self.assertIsInstance(resp, dict)
            self.assertIn("shards_probed", resp)
            self.assertIsInstance(resp["shards_probed"], list)
            self.assertIn("results", resp)
            self.assertIsInstance(resp["results"], list)

    def test_special_characters_and_injections(self):
        """Adversarial queries containing SQL injection, XSS, and shell metacharacters."""
        adversarial_queries = [
            "' OR '1'='1'; --",
            "<script>alert('XSS')</script>",
            '<div class="test" onclick="exploit()">click</div>',
            "%s %x %n ${PATH} $(whoami)",
            "| ls -la ; cat /etc/passwd & calc.exe",
            "!@#$%^&*()_+-=[]{}|;':\",.<>/?`~",
            "SELECT * FROM metadata WHERE id = 1;",
            "../../../secret/config.json",
            "\\x00\\xff\\xfe",
            "None",
            "NULL",
            "undefined",
        ]
        for query in adversarial_queries:
            resp = perform_search(query, top_k=3)
            self.assertIsInstance(resp, dict, f"Failed dictionary return on: {query}")
            self.assertIn("shards_probed", resp)
            self.assertIsInstance(resp["shards_probed"], list)
            self.assertGreater(len(resp["shards_probed"]), 0)
            self.assertIn("results", resp)
            self.assertIsInstance(resp["results"], list)

    def test_unicode_and_multilingual_strings(self):
        """Complex unicode scripts, Vietnamese tone marks, RTL languages, and emojis."""
        unicode_queries = [
            "Tìm kiếm tài liệu tiếng Việt đầy đủ thanh điệu: sắc, huyền, hỏi, ngã, nặng, đ, Đ, ư, ơ, ê, â",
            "Hệ thống định tuyến đồ thị HNSW đa phân mảnh SQ8",
            "人工知能による多言語ベクトル類似度検索",
            "자연어 처리 기반의 고차원 벡터 인덱싱",
            "البحث الدلالي المتجهي متعدد اللغات",
            "חיפוש וקטורי מתקדם במסד נתונים",
            "🔍 🚀 📊 🤖 💡 🔥 ⚡ 🇻🇳 💻 🌐",
            "Zażółć gęślą jaźń (Polish diacritics)",
            "Grüße aus München (German umlauts)",
        ]
        for query in unicode_queries:
            resp = perform_search(query, top_k=3)
            self.assertIsInstance(resp, dict)
            self.assertIn("shards_probed", resp)
            self.assertIsInstance(resp["shards_probed"], list)
            self.assertGreater(len(resp["shards_probed"]), 0)
            self.assertIn("results", resp)
            self.assertGreater(len(resp["results"]), 0)

    def test_long_text_queries(self):
        """Very long query strings up to 50,000 characters must not crash or OOM."""
        lengths = [1000, 10000, 50000]
        for length in lengths:
            long_query = "công nghệ tìm kiếm vector thông minh " * (length // 35 + 1)
            long_query = long_query[:length]
            resp = perform_search(long_query, top_k=2)
            self.assertIsInstance(resp, dict)
            self.assertIn("shards_probed", resp)
            self.assertIsInstance(resp["shards_probed"], list)
            self.assertIn("results", resp)
            self.assertGreater(len(resp["results"]), 0)

    def test_top_k_variations_and_high_limits(self):
        """Diverse top_k values including single-item, dataset bounds, and excessive limits."""
        for k in [1, 5, 50, 100, 500, 5000]:
            resp = perform_search("kiểm tra top_k", top_k=k)
            results = resp["results"]
            self.assertIsInstance(results, list)
            self.assertLessEqual(len(results), k)
            self.assertLessEqual(len(results), resp["dataset_size"])
            if k >= 1:
                self.assertGreater(len(results), 0)

    def test_non_existent_categories(self):
        """Non-existent categories must return empty result lists without index errors."""
        fake_categories = [
            "DanhMucKhongTonTai_9999",
            "NonExistentCategoryXYZ",
            "EmptyCategory_Random123",
            "   ",
        ]
        for cat in fake_categories:
            resp = perform_search("văn bản pháp luật", top_k=5, category=cat)
            self.assertIsInstance(resp, dict)
            self.assertIn("results", resp)
            self.assertEqual(len(resp["results"]), 0)
            self.assertEqual(resp["results_count"], 0)
            self.assertEqual(resp["top_similarity_pct"], 0.0)
            self.assertEqual(resp["min_distance"], 0.0)
            self.assertIsInstance(resp["shards_probed"], list)
            self.assertGreater(len(resp["shards_probed"]), 0)

    def test_all_algorithm_keys(self):
        """All supported algorithm keys and fallback behavior for unlisted keys."""
        algorithms = ["two_tier", "hnsw", "ivf_pq", "flat", "pure_sq8", "custom_unknown_algo"]
        for algo in algorithms:
            resp = perform_search("truy vấn thuật toán", top_k=3, algorithm=algo)
            self.assertIsInstance(resp, dict)
            self.assertIn("algorithm", resp)
            self.assertIsInstance(resp["algorithm"], str)
            self.assertGreater(len(resp["algorithm"]), 0)
            self.assertIn("results", resp)

    def test_shards_probed_integrity(self):
        """shards_probed must always be a non-empty list of native integers within valid range."""
        test_queries = [
            "trí tuệ nhân tạo",
            "kinh tế vĩ mô",
            "xử lý ngôn ngữ tự nhiên",
            "1234567890",
            "special #@! query",
        ]
        for q in test_queries:
            resp = perform_search(q, top_k=3)
            probed = resp["shards_probed"]
            self.assertIsInstance(probed, list, "shards_probed must be a list")
            self.assertGreater(len(probed), 0, "shards_probed must not be empty")
            for shard_id in probed:
                self.assertIsInstance(shard_id, int, f"shard_id {shard_id} must be int")
                self.assertGreaterEqual(shard_id, 0, f"shard_id {shard_id} must be >= 0")
                self.assertLess(shard_id, 5, f"shard_id {shard_id} must be < num_shards (5)")

    def test_candidate_results_schema_completeness(self):
        """Every candidate in results must contain shard_id, node_id, doc_id, title, distance."""
        resp = perform_search("phân tích dữ liệu lớn", top_k=10)
        results = resp["results"]
        self.assertGreater(len(results), 0)

        for rank_idx, item in enumerate(results, start=1):
            self.assertIn("shard_id", item, f"Missing shard_id in item: {item}")
            self.assertIsInstance(item["shard_id"], int)
            self.assertGreaterEqual(item["shard_id"], 0)

            self.assertIn("node_id", item, f"Missing node_id in item: {item}")
            self.assertIsInstance(item["node_id"], int)

            self.assertIn("doc_id", item, f"Missing doc_id in item: {item}")
            self.assertIsInstance(item["doc_id"], str)
            self.assertGreater(len(item["doc_id"]), 0)

            self.assertIn("title", item, f"Missing title in item: {item}")
            self.assertIsInstance(item["title"], str)

            self.assertIn("distance", item, f"Missing distance in item: {item}")
            self.assertIsInstance(item["distance"], (float, int))

            self.assertIn("similarity_score", item)
            self.assertIsInstance(item["similarity_score"], (float, int))
            self.assertGreaterEqual(item["similarity_score"], 0.0)
            self.assertLessEqual(item["similarity_score"], 1.0)

            self.assertIn("category", item)
            self.assertIn("preview", item)
            self.assertEqual(item["rank"], rank_idx)

    def test_full_json_serializability(self):
        """Full perform_search response must be serializable to JSON without TypeError."""
        resp = perform_search("kiểm tra tính tuần tự hóa JSON", top_k=5)
        try:
            serialized = json.dumps(resp, ensure_ascii=False)
            self.assertIsInstance(serialized, str)
            deserialized = json.loads(serialized)
            self.assertEqual(deserialized["query"], "kiểm tra tính tuần tự hóa JSON")
        except TypeError as e:
            self.fail(f"perform_search output failed JSON serialization: {e}")


class TestSearchBridgeCLI(unittest.TestCase):
    """Adversarial CLI tests for search_bridge.py invocation."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess:
        cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "search_bridge.py")] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            cwd=REPO_ROOT,
        )

    def _extract_json(self, stdout: str) -> dict:
        lines = stdout.strip().split("\n")
        json_lines = [l for l in lines if l.startswith("{")]
        self.assertGreater(len(json_lines), 0, f"No JSON found in CLI stdout: {stdout}")
        return json.loads(json_lines[0])

    def test_cli_standard_invocation(self):
        """Standard CLI invocation returns code 0 and valid JSON output."""
        res = self._run_cli(["--query", "tìm kiếm tiêu chuẩn", "--top-k", "3"])
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = self._extract_json(res.stdout)

        self.assertEqual(data["query"], "tìm kiếm tiêu chuẩn")
        self.assertIn("shards_probed", data)
        self.assertIsInstance(data["shards_probed"], list)
        self.assertGreater(len(data["shards_probed"]), 0)
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 3)

        for item in data["results"]:
            for field in ["shard_id", "node_id", "doc_id", "title", "distance"]:
                self.assertIn(field, item)

    def test_cli_missing_required_query_flag(self):
        """CLI invocation without --query must exit with non-zero error code."""
        res = self._run_cli(["--top-k", "5"])
        self.assertNotEqual(res.returncode, 0)
        combined_output = res.stdout + res.stderr
        self.assertTrue("required" in combined_output or "error" in combined_output)

    def test_cli_invalid_algorithm_choice(self):
        """CLI invocation with unapproved algorithm must exit with non-zero code."""
        res = self._run_cli(["--query", "test", "--algorithm", "invalid_algo_name"])
        self.assertNotEqual(res.returncode, 0)

    def test_cli_all_valid_algorithms(self):
        """CLI execution across all supported algorithm choices."""
        for algo in ["two_tier", "hnsw", "ivf_pq", "flat", "pure_sq8"]:
            res = self._run_cli(["--query", "thuật toán", "--algorithm", algo, "--top-k", "2"])
            self.assertEqual(res.returncode, 0, f"Failed on algorithm {algo}: {res.stderr}")
            data = self._extract_json(res.stdout)
            self.assertEqual(data["algorithm_key"], algo)
            self.assertIn("shards_probed", data)
            self.assertGreater(len(data["results"]), 0)

    def test_cli_special_characters_and_quotes(self):
        """CLI execution with tricky quotation and special characters."""
        special_query = "công nghệ 'AI' & \"machine learning\" <2026>"
        res = self._run_cli(["--query", special_query, "--top-k", "2"])
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = self._extract_json(res.stdout)
        self.assertEqual(data["query"], special_query)
        self.assertEqual(len(data["results"]), 2)

    def test_cli_high_top_k(self):
        """CLI execution with top_k exceeding dataset size gracefully caps."""
        res = self._run_cli(["--query", "khoa học", "--top-k", "500"])
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = self._extract_json(res.stdout)
        self.assertLessEqual(len(data["results"]), data["dataset_size"])
        self.assertGreater(len(data["results"]), 0)

    def test_cli_non_existent_category(self):
        """CLI execution with non-existent category returns empty results without crashing."""
        res = self._run_cli(["--query", "khoa học", "--category", "NonExistentCat99"])
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = self._extract_json(res.stdout)
        self.assertEqual(len(data["results"]), 0)
        self.assertIsInstance(data["shards_probed"], list)

    def test_cli_custom_hyperparameters(self):
        """CLI accepts and records custom hyperparameters."""
        args = [
            "--query", "siêu tham số",
            "--m-param", "8",
            "--ef-search", "25",
            "--tau", "2",
            "--epsilon", "0.0005",
            "--min-rerank-k", "15",
            "--top-k", "2",
        ]
        res = self._run_cli(args)
        self.assertEqual(res.returncode, 0, f"CLI stderr: {res.stderr}")
        data = self._extract_json(res.stdout)
        hp = data["hyperparams"]
        self.assertEqual(hp["m"], 8)
        self.assertEqual(hp["ef_search"], 25)
        self.assertEqual(hp["tau"], 2)
        self.assertEqual(hp["epsilon"], 0.0005)
        self.assertEqual(hp["min_rerank_k"], 15)

    def test_cli_query_log_file_created(self):
        """CLI execution records log file in data/processed/query_logs/."""
        res = self._run_cli(["--query", "ghi log truy vấn", "--top-k", "1"])
        self.assertEqual(res.returncode, 0)
        data = self._extract_json(res.stdout)
        self.assertIn("result_file", data)
        log_path = data["result_file"]
        self.assertTrue(os.path.exists(log_path), f"Log file missing: {log_path}")
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = json.load(f)
        self.assertEqual(log_content["query"], "ghi log truy vấn")


class TestSearchServiceHTTPServer(unittest.TestCase):
    """End-to-end HTTP integration tests for SearchHandler server."""

    @classmethod
    def setUpClass(cls):
        # Bind to port 0 for automatic available port selection
        cls.server = HTTPServer(("127.0.0.1", 0), SearchHandler)
        cls.port = cls.server.server_port
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _post(self, path: str, payload: dict | bytes, content_type: str = "application/json"):
        url = f"http://127.0.0.1:{self.port}{path}"
        if isinstance(payload, dict):
            data = json.dumps(payload).encode("utf-8")
        else:
            data = payload
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": f"{content_type}; charset=utf-8",
                "Connection": "close",
            },
            method="POST",
        )
        return urllib.request.urlopen(req)

    def _get(self, path: str):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, headers={"Connection": "close"}, method="GET")
        return urllib.request.urlopen(req)

    def test_http_health_endpoint(self):
        """GET /health must return HTTP 200 with healthy status."""
        resp = self._get("/health")
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body["status"], "healthy")
        self.assertIn("dimension", body)

    def test_http_search_valid_query(self):
        """POST /search with valid payload returns HTTP 200 and schema-compliant JSON."""
        resp = self._post("/search", {"query": "trí tuệ nhân tạo", "top_k": 3})
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(body["query"], "trí tuệ nhân tạo")
        self.assertIn("shards_probed", body)
        self.assertIsInstance(body["shards_probed"], list)
        self.assertIn("results", body)
        self.assertEqual(len(body["results"]), 3)
        for item in body["results"]:
            for field in ["shard_id", "node_id", "doc_id", "title", "distance"]:
                self.assertIn(field, item)

    def test_http_search_empty_query_error(self):
        """POST /search with empty query must return clean HTTP 400 JSON without stack trace."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/search", {"query": ""})
        self.assertEqual(ctx.exception.code, 400)
        err_body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_body, {"error": "Empty query"})

    def test_http_search_whitespace_query_error(self):
        """POST /search with whitespace-only query must return clean HTTP 400 JSON."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/search", {"query": "   \t\n  "})
        self.assertEqual(ctx.exception.code, 400)
        err_body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_body, {"error": "Empty query"})

    def test_http_search_missing_query_field_error(self):
        """POST /search missing 'query' property must return clean HTTP 400 JSON."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/search", {"top_k": 5})
        self.assertEqual(ctx.exception.code, 400)
        err_body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertEqual(err_body, {"error": "Empty query"})

    def test_http_search_malformed_json_error(self):
        """POST /search with invalid JSON body must return clean HTTP 500 JSON without crashing."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/search", b"THIS_IS_NOT_VALID_JSON{{{")
        self.assertEqual(ctx.exception.code, 500)
        err_body = json.loads(ctx.exception.read().decode("utf-8"))
        self.assertIn("error", err_body)
        self.assertIsInstance(err_body["error"], str)

    def test_http_unknown_endpoint_get_404(self):
        """GET to unregistered route returns 404."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/non_existent_route")
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.read()
        ctx.exception.close()

    def test_http_unknown_endpoint_post_404(self):
        """POST to unregistered route returns 404."""
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post("/non_existent_route", {"test": 123})
        self.assertEqual(ctx.exception.code, 404)
        ctx.exception.read()
        ctx.exception.close()

    def test_http_server_resilience_after_errors(self):
        """Server remains healthy and responsive after multiple erroneous requests."""
        for _ in range(3):
            try:
                self._post("/search", b"bad_json")
            except urllib.error.HTTPError as e:
                e.read()
            try:
                self._post("/search", {"query": ""})
            except urllib.error.HTTPError as e:
                e.read()

        resp = self._post("/search", {"query": "phục hồi sau lỗi", "top_k": 2})
        self.assertEqual(resp.status, 200)
        body = json.loads(resp.read().decode("utf-8"))
        self.assertEqual(len(body["results"]), 2)


if __name__ == "__main__":
    unittest.main()
