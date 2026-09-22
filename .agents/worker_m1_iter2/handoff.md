# Handoff Report — Worker 1 (Iteration 2: Backend Core & Concurrency Remediation)

## 1. Observation

### 1.1 Concurrency Race Condition in `ApplicationLRUCache`
- Initial test run: `python -s -m pytest tests/test_stress_core_index.py`
- Failure details:
  - `TestDirectIOManagerConcurrency::test_async_read_batch_concurrent_churn_race_condition`:
    `AssertionError: 1 != 0 : async_read_batch failed under concurrency: ['KeyError: 4']`
  - `TestDirectIOManagerConcurrency::test_lru_cache_thread_safety_race_condition`:
    `AssertionError: 2 != 0 : ApplicationLRUCache is not thread-safe: ['KeyError in get: 1', 'KeyError in get: 1']`
- Cause: In `src/ann_index/io_manager.py`, `ApplicationLRUCache.get()` and `put()` modified internal state without synchronization. When `DirectIOManager.async_read_batch()` spawned 16 threads in `ThreadPoolExecutor`, concurrent calls to `get()` and `put()` caused interleaved executions between membership checks and `OrderedDict.move_to_end()` / `popitem()`.

### 1.2 Storage File Offset Desynchronization & Disk Growth
- Initial inspection of `shards_db/`:
  - `shard_0.bin` size: 22,580,224 bytes (~22.5 MB).
  - Contaminated by previous runs appending raw vectors via `"ab"` without truncation or offset control.
- Initial CLI query run: `python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5`
- Output snippet:
  - `doc_id`: `synthetic_0`, `distance`: 15.0621.
  - Normalized float32 vectors yielded distances exceeding 2.0 due to reading misaligned bytes from offset 0 while appended vectors were located at the end of the file.
  - Each CLI execution permanently grew the shard binary files on disk by ~1.5 MB.

---

## 2. Logic Chain

1. **Premise 1 (Cache Synchronization)**: Adding a `threading.Lock()` to `ApplicationLRUCache` around `get()`, `put()`, `clear()`, and `__len__()` ensures atomic cache operations across concurrent reader/writer worker threads.
2. **Premise 2 (Exact Offset Seek)**: In `LocalShard._save_to_ssd(self, idx: int, vector: np.ndarray)`, writing vector bytes via `f.seek(idx * self.vector_bytes)` with mode `"r+b"` guarantees vectors are saved at predictable offsets (`node_id * vector_bytes`) regardless of file state or write order.
3. **Premise 3 (Idempotent Shard Storage)**: Adding `clean_storage: bool = False` to `LocalShard.__init__` and `ShardedIVFHNSW.__init__` allows callers to truncate existing shard storage files (`open(self.io_manager.filepath, "wb").close()`) when initializing a fresh index.
4. **Premise 4 (Elimination of Disk Leaks)**: Passing `clean_storage=True` in `dashboard/scripts/search_bridge.py` and `dashboard/scripts/search_service.py` ensures CLI runs and service restarts reset shard files, avoiding unbounded growth.
5. **Premise 5 (Stale Data Removal)**: Deleting old `.bin` files in `shards_db/` removes contaminated vectors and guarantees subsequent seeks read valid float32 values.

---

## 3. Caveats

- `sentence_transformers` is not installed in the local environment; the system automatically falls back to `MockEmbedder` as designed in `search_bridge.py` and `search_service.py`.
- Shard storage files are created locally in `shards_db/` during search operations.

---

## 4. Conclusion

All remediation tasks have been implemented and verified:
1. `src/ann_index/io_manager.py`: `ApplicationLRUCache` now synchronizes all read, write, clear, and length queries using `self._lock = threading.Lock()`.
2. `src/ann_index/two_tier_hnsw.py`: `LocalShard` and `ShardedIVFHNSW` support `clean_storage: bool = False`. `LocalShard._save_to_ssd` writes each vector at `idx * self.vector_bytes` via `"r+b"`.
3. `shards_db/`: All stale `.bin` files were purged.
4. `dashboard/scripts/search_bridge.py` and `dashboard/scripts/search_service.py`: Initialized with `clean_storage=True`, eliminating disk expansion across repeated queries.
5. All 56 test cases across `test_stress_core_index.py`, `test_two_tier_hnsw.py`, and `test_search_edge_cases.py` pass cleanly.
6. `search_bridge.py` returns valid Euclidean distances <= 2.0 (0.0 to 1.4517) on normalized vectors.

---

## 5. Verification Method

To independently verify the implementation:

### 5.1 Run Stress and Concurrency Tests (13 tests)
```powershell
python -s -m pytest tests/test_stress_core_index.py
```
Expected result: `13 passed`.

### 5.2 Run Two-Tier HNSW Tests (15 tests)
```powershell
python -s -m pytest tests/test_two_tier_hnsw.py
```
Expected result: `15 passed`.

### 5.3 Run Search Edge Cases and API Tests (28 tests)
```powershell
python -s -m pytest tests/test_search_edge_cases.py
```
Expected result: `28 passed`.

### 5.4 Verify All 56 Tests Simultaneously
```powershell
python -s -m pytest tests/test_stress_core_index.py tests/test_two_tier_hnsw.py tests/test_search_edge_cases.py
```
Expected result: `56 passed in ~12s`.

### 5.5 Verify CLI Search Bridge Distance Bounds
```powershell
python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5
```
Expected output: JSON containing 5 results with `distance` values between 0.0 and 2.0.

### 5.6 Invalidation Conditions
- Any `KeyError` raised during concurrent execution of `ApplicationLRUCache`.
- Any Euclidean distance > 2.0 on normalized vectors.
- Any disk accumulation in `shards_db/` across repeated executions of `search_bridge.py`.
