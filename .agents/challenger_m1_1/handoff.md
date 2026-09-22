# Handoff Report — Challenger 1: Core Index Stress Tester (Milestone 1)

## 1. Observation

### 1.1 Empirical Concurrency Race Condition in `ApplicationLRUCache`
During execution of multithreaded stress testing on `DirectIOManager.async_read_batch` with cache hit/miss churn:
- Test command: `python -s -m pytest tests/test_stress_core_index.py -k test_async_read_batch_concurrent_churn_race_condition`
- Verbatim error output:
  ```text
  FAILED tests/test_stress_core_index.py::TestDirectIOManagerConcurrency::test_async_read_batch_concurrent_churn_race_condition
  AssertionError: 3 != 0 : async_read_batch failed under concurrency: ['KeyError: 7', 'KeyError: 11', 'KeyError: 10']
  ```
- Exact file paths and lines involved:
  - `src/ann_index/io_manager.py:27-54`:
    ```python
    class ApplicationLRUCache:
        def __init__(self, capacity: int = 10000) -> None:
            self.capacity = max(1, capacity)
            self.cache: OrderedDict[int, np.ndarray] = OrderedDict()

        def get(self, key: int) -> Optional[np.ndarray]:
            if key not in self.cache:
                return None
            self.cache.move_to_end(key)
            return self.cache[key]

        def put(self, key: int, value: np.ndarray) -> None:
            self.cache[key] = value
            self.cache.move_to_end(key)
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)
    ```
  - `src/ann_index/io_manager.py:155-160`:
    ```python
    max_workers = min(16, max(1, len(missing_ids)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {executor.submit(self.get_vector, vid): vid for vid in missing_ids}
        for future in concurrent.futures.as_completed(future_to_id):
            vid = future_to_id[future]
            results[vid] = future.result()
    ```
  - `ApplicationLRUCache` uses an un-synchronized `OrderedDict`. When `DirectIOManager.async_read_batch` dispatches missing IDs to its internal `ThreadPoolExecutor(max_workers=16)`, multiple threads concurrently call `self.get_vector`, executing `self.lru_cache.get()` and `self.lru_cache.put()`.
  - When Thread A evaluates `if key not in self.cache` (returning False), a thread preemption allows Thread B to execute `put()` and evict `key` via `self.cache.popitem(last=False)`. When Thread A resumes, it calls `self.cache.move_to_end(key)` on the evicted key, triggering `KeyError`.

### 1.2 Full Stress Test Suite Execution Results
Executing the complete 13-test stress harness in `tests/test_stress_core_index.py`:
- Command: `python -s -m pytest tests/test_stress_core_index.py`
- Result summary: 12 passed, 1 failed.
- Details:
  - `TestDirectIOManagerConcurrency::test_async_read_batch_edge_cases`: PASSED. Handles empty batch `[]`, duplicate IDs `[5, 5, 12]`, and out-of-bounds IDs.
  - `TestDirectIOManagerConcurrency::test_concurrent_async_read_batch_data_integrity`: PASSED. Data read matches ground truth bit-for-bit when cache churn does not trigger preemption eviction race.
  - `TestDirectIOManagerConcurrency::test_async_read_batch_concurrent_churn_race_condition`: FAILED (`KeyError` race condition).
  - `TestShardedIVFHNSWStressAndEdgeCases::test_edge_case_vector_values`: PASSED. Zero vectors, extreme values (5000.0), and normal vectors routed and retrieved correctly.
  - `TestShardedIVFHNSWStressAndEdgeCases::test_varied_nprobe`: PASSED. Robust across `nprobe=1`, `nprobe=2`, `nprobe=num_shards`, `nprobe=100` (clamped to `num_shards`), and `nprobe <= 0` (clamped to 1).
  - `TestShardedIVFHNSWStressAndEdgeCases::test_varied_top_k`: PASSED. Robust across `top_k=0`, `top_k=1`, `top_k=5`, `top_k=50` (exceeding total elements), and `top_k=10` with `re_rank_limit=3`. Results strictly sorted ascending by distance.
  - `TestShardedIVFHNSWStressAndEdgeCases::test_edge_case_graph_sizes`: PASSED. Empty index returns `([], shards)`, single-vector index returns `[(0.0, 42, shard)]`, and dynamic capacity expansion safely reallocates arrays from 100 to 1100 elements.
  - `TestEarlyExitTerminationGuarantees::test_pathological_plateau_graph`: PASSED. On 30 identical vectors where distance improvement is 0.0 < epsilon, early-exit terminates in <= tau steps.
  - `TestEarlyExitTerminationGuarantees::test_extreme_tau_and_epsilon_parameters_terminate`: PASSED. Parameters `tau in [0, 1, 2, 10, 1000]` and `epsilon in [-10.0, 0.0, 1e-6, 1.0, 1e5]` all terminate in < 0.5s without infinite loops.
  - `TestEarlyExitTerminationGuarantees::test_cyclic_graph_termination`: PASSED. Monotonically expanding `visited` set guarantees loop termination on directed cycles.
  - `TestZeroMemmapEnforcement::test_runtime_memmap_interception`: PASSED. Monkeypatching `np.memmap` with a raising trap confirmed zero invocations throughout writes, batch reads, routing, graph search, and disk re-ranking.
  - `TestZeroMemmapEnforcement::test_static_code_inspection_zero_memmap`: PASSED. AST and text inspection verified zero occurrences of `memmap` or `import mmap` in `src/ann_index/`.

---

## 2. Logic Chain

1. **Premise 1 (Concurrency Contract)**: `DirectIOManager.async_read_batch` is explicitly designed as a multithreaded batch reader using `ThreadPoolExecutor(max_workers=16)` to read missing vectors concurrently.
2. **Premise 2 (Shared Mutable State)**: `DirectIOManager` holds a single instance of `ApplicationLRUCache` (`self.lru_cache`). Every worker thread spawned by `async_read_batch` executes `self.get_vector(vid)`, which performs unsynchronized `self.lru_cache.get(vector_id)` and `self.lru_cache.put(vector_id, vec)`.
3. **Premise 3 (Race Window)**: In `ApplicationLRUCache.get`, there is a multi-step check and mutation: `if key not in self.cache:` followed by `self.cache.move_to_end(key)` and `self.cache[key]`. In `ApplicationLRUCache.put`, eviction is performed via `self.cache.popitem(last=False)`.
4. **Premise 4 (Empirical Reproduction)**: Under high thread contention and cache churn, thread switches between the membership check and `move_to_end` permit concurrent evictions, causing `move_to_end` to raise `KeyError`. This crashes worker threads and propagates unhandled exceptions through `future.result()`.
5. **Premise 5 (Verification of Fix)**: Wrapping `get`, `put`, and `clear` with a `threading.Lock()` completely eliminated all errors across 25 threads and thousands of queries.

---

## 3. Caveats

1. **Optional Neural Dependencies**: `sentence_transformers` and `datasketch` are absent from the local Anaconda environment, as documented by Worker 1. Tests relied on mock embeddings and synthetic vector arrays.
2. **Single Process Scope**: Tests evaluated multi-threaded in-process concurrency on Windows. Multi-process cross-process synchronization was not evaluated as shards currently execute in a single Python runtime.

---

## 4. Conclusion & Verdict

### Verdict: REQUEST_CHANGES

While `ShardedIVFHNSW`, ADC quantization, early-exit termination, and `numpy.memmap` elimination are well-implemented and robust against edge cases, `DirectIOManager.async_read_batch` and `ApplicationLRUCache` contain a confirmed, reproducible concurrency bug:

**Required Changes**:
1. Add `import threading` and initialize `self._lock = threading.Lock()` inside `ApplicationLRUCache.__init__` in `src/ann_index/io_manager.py`.
2. Protect `get()`, `put()`, and `clear()` methods in `ApplicationLRUCache` using `with self._lock:`.
3. Run `python -s -m pytest tests/test_stress_core_index.py` to confirm that all 13 stress tests pass cleanly.

---

## 5. Verification Method

To independently reproduce the failure and verify the fix:

### 5.1 Reproduce Current Failure
Run the stress test suite:
```powershell
python -s -m pytest tests/test_stress_core_index.py -k test_async_read_batch_concurrent_churn_race_condition
```
Expected output:
```text
FAILED ... AssertionError: ... async_read_batch failed under concurrency: ['KeyError: ...']
```

### 5.2 Verify Full Suite
Run all core stress tests:
```powershell
python -s -m pytest tests/test_stress_core_index.py
```
Expected output: 12 passed, 1 failed.

### 5.3 Invalidation Conditions
- Any occurrence of unhandled `KeyError`, `RuntimeError`, or thread exceptions in `DirectIOManager.async_read_batch`.
- Any invocation of `numpy.memmap` at runtime.
- Any infinite loop during graph search with varied `tau` and `epsilon`.
