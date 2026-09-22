## 2026-09-21T04:09:10Z
You are Worker 1 - Iteration 2 (Backend Core & Concurrency Remediation).
Your working directory is f:\ANN\.agents\worker_m1_iter2.
Original request file: f:\ANN\.agents\ORIGINAL_REQUEST.md. You MUST read it before starting work.
Project specification: f:\ANN\PROJECT.md.
Prior reports:
- Reviewer 2 defect report: f:\ANN\.agents\reviewer_m1_2\handoff.md
- Challenger 1 defect report: f:\ANN\.agents\challenger_m1_1\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Remediation Tasks:
1. Thread Synchronization in `src/ann_index/io_manager.py`:
   - In `ApplicationLRUCache`: add `import threading` and initialize `self._lock = threading.Lock()`.
   - Protect all operations in `get(self, key)`, `put(self, key, value)`, and `clear(self)` using `with self._lock:`.
   - Ensure root alias `io_manager.py` reflects this update.
2. SSD Storage File Offset & Append Desynchronization in `src/ann_index/two_tier_hnsw.py`:
   - In `LocalShard.__init__`, support `clean_storage: bool = False`. If `clean_storage` is True, truncate/reset the shard file (`open(self.io_manager.filepath, 'wb').close()`).
   - In `ShardedIVFHNSW.__init__`, accept and pass `clean_storage: bool = False`.
   - In `LocalShard._save_to_ssd(self, idx: int, vector: np.ndarray)`: write vector bytes at exact offset `idx * self.vector_bytes` via `f.seek(idx * self.vector_bytes)` using `"r+b"` (or create/ensure file existence first). Ensure this prevents any offset misalignment.
   - Clean/delete contaminated stale `.bin` files in `shards_db/`.
   - In `dashboard/scripts/search_bridge.py`: ensure initializing `ShardedIVFHNSW` does not cause unbounded disk expansion on each query (e.g. use clean_storage=True when building from scratch or only seed if shards are empty/missing).
   - Ensure root alias `two_tier_hnsw.py` reflects these updates.
3. Verification & Testing:
   - Run `python -s -m pytest tests/test_stress_core_index.py` -> verify all 13 tests pass.
   - Run `python -s -m pytest tests/test_two_tier_hnsw.py` -> verify all 15 tests pass.
   - Run `python -s -m pytest tests/test_search_edge_cases.py` -> verify all 28 tests pass.
   - Verify `python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5` produces valid Euclidean distances <= 2.0 on normalized vectors without error.

Deliverable:
Write report to `f:\ANN\.agents\worker_m1_iter2\handoff.md` detailing changes, test commands, and exact outputs.
Send a completion message to the parent orchestrator.
