# Independent Review Report — Milestone 1 (Backend Core Algorithms)

## 1. Observation

### 1.1 Direct Source Code Inspections

1. **`src/ann_index/io_manager.py`**:
   - `ApplicationLRUCache`: Implemented using `collections.OrderedDict`. Implements `get(key)` (updating recency via `move_to_end`) and `put(key, value)` (evicting oldest via `popitem(last=False)` when exceeding capacity).
   - `DirectIOManager`:
     - Points seeks executed directly via `f.seek(offset)` where `offset = vector_id * self.vector_bytes` and binary reads via `f.read(self.vector_bytes)`.
     - Buffer decoding executed via `np.frombuffer(raw_data, dtype=np.float32).copy()`.
     - Multithreaded asynchronous retrieval implemented via `ThreadPoolExecutor(max_workers=min(16, max(1, len(missing_ids))))`.
     - Vector IDs are deduplicated before disk retrieval via `list(dict.fromkeys(vector_ids))`.
     - Appends executed via `tofile(f)` and indexed by `pos // self.vector_bytes`.
     - Zero references to `numpy.memmap` or `np.memmap`.

2. **`src/ann_index/hnsw_quantized.py`**:
   - `quantize_adc`: Evaluates row-wise minimum and maximum across dimension columns (`axis=1, keepdims=True`). Computes `range_val = max_val - min_val` with zero-guard `range_val[range_val == 0] = 1e-8`. Generates `scale = (range_val / 255.0).astype(np.float16)` and `offset = min_val.astype(np.float16)`. Produces uint8 quantized vector matrix via `np.clip(np.round(normalized * 255.0), 0, 255).astype(np.uint8)`.
   - `distance_adc`: Takes float32 uncompressed query and uint8 quantized candidate vector with float16 `scale` and `offset`. Evaluates `approx_vector = (q_vector_uint8.astype(np.float32) * float(scale)) + float(offset)` and returns Euclidean distance `float(np.linalg.norm(q_float - approx_vector))`.
   - `exact_distance_l2`: Computes exact L2 distance `float(np.linalg.norm(q - v))` on full-precision float32 vectors.

3. **`src/ann_index/two_tier_hnsw.py`**:
   - `LocalShard`:
     - Maintains in-memory graph `self.graph: Dict[int, List[int]]`.
     - Preallocates `quantized` (uint8), `scales` (float16), and `offsets` (float16) arrays with dynamic resizing via `_ensure_capacity()`.
     - Manages global document identifier mapping via `self.id_map[idx] = global_id`.
     - Direct I/O storage configured per shard at `os.path.join(storage_dir, f"shard_{shard_id}.bin")`.
     - In-memory beam search `_search_local_graph` incorporates early-exit stopping when `fail_count >= tau` consecutive candidates fail to improve distance by at least `epsilon`.
   - `ShardedIVFHNSW`:
     - Partitions space across $K$ shards using centroid proximity in `_get_nearest_shards`.
     - `route_and_insert(global_id, vector)` routes vector to closest centroid and records in local shard.
     - `distributed_search`: Probes closest `nprobe` shards, searches in-memory graphs with ADC and early-exit, collects candidate pool, retrieves exact float32 vectors asynchronously from SSD via `io_manager.async_read_batch`, re-ranks via `exact_distance_l2`, and returns `(final_results, target_shard_ids)`. Each result tuple is `(exact_dist, global_id, shard_id)`.
     - Retains `TwoTierQuantizedHNSW` for backward compatibility.

4. **Backward Compatibility & Import Guards**:
   - Root aliases `io_manager.py`, `hnsw_quantized.py`, and `two_tier_hnsw.py` correctly re-export classes and functions from `src/ann_index/`.
   - `src/ann_data/__init__.py` guards optional `datasketch` dependency with `try...except (ImportError, ModuleNotFoundError)`.
   - Zero changes made to `configs/default_pipeline.json` or `data/` directory.

### 1.2 Independent Verification Outputs

1. **Target Unit Test Suite (`pytest tests/test_two_tier_hnsw.py`)**:
   ```text
   ============================= test session starts =============================
   platform win32 -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0 -- F:\anaconda3\python.exe
   rootdir: F:\ANN
   configfile: pyproject.toml
   collected 15 items

   tests/test_two_tier_hnsw.py::TestTwoTierQuantizedHNSW::test_benchmark_runner_integration PASSED [  6%]
   tests/test_two_tier_hnsw.py::TestTwoTierQuantizedHNSW::test_build_and_search_shapes PASSED [ 13%]
   tests/test_two_tier_hnsw.py::TestTwoTierQuantizedHNSW::test_high_recall_with_reranking PASSED [ 20%]
   tests/test_two_tier_hnsw.py::TestTwoTierQuantizedHNSW::test_ram_footprint_reduction PASSED [ 26%]
   tests/test_two_tier_hnsw.py::TestHNSWQuantizedADC::test_distance_adc_approximation_accuracy PASSED [ 33%]
   tests/test_two_tier_hnsw.py::TestHNSWQuantizedADC::test_quantize_adc_numerical_properties PASSED [ 40%]
   tests/test_two_tier_hnsw.py::TestDirectIOManager::test_async_read_batch_multithreaded PASSED [ 46%]
   tests/test_two_tier_hnsw.py::TestDirectIOManager::test_lru_cache_operations PASSED [ 53%]
   tests/test_two_tier_hnsw.py::TestDirectIOManager::test_no_numpy_memmap_in_implementation PASSED [ 60%]
   tests/test_two_tier_hnsw.py::TestDirectIOManager::test_write_and_read_single_vector PASSED [ 66%]
   tests/test_two_tier_hnsw.py::TestShardedIVFHNSW::test_distributed_search_returns_global_id_and_shard_id PASSED [ 73%]
   tests/test_two_tier_hnsw.py::TestShardedIVFHNSW::test_early_exit_in_local_shard PASSED [ 80%]
   tests/test_two_tier_hnsw.py::TestShardedIVFHNSW::test_route_and_insert_with_id_mapping PASSED [ 86%]
   tests/test_two_tier_hnsw.py::TestSearchServiceIntegration::test_perform_search_category_filter PASSED [ 93%]
   tests/test_two_tier_hnsw.py::TestSearchServiceIntegration::test_perform_search_contract_and_shard_fields PASSED [100%]

   ============================= 15 passed in 0.69s ==============================
   ```

2. **Index Regression Suite (`43 test cases across 9 files`)**:
   Ran: `python -s -m pytest tests/test_two_tier_hnsw.py tests/test_hnsw_index.py tests/test_flat_index.py tests/test_early_exit.py tests/test_metrics.py tests/test_ivf_pq.py tests/test_pq.py tests/test_quantizer.py tests/test_quantizer_pipeline.py`
   Output: `43 passed in 1.63s`. Zero regressions in existing index components.

3. **Multi-Threaded Stress Test (`tests/test_stress_core_index.py`)**:
   Executed 50 concurrent threads with overlapping `async_read_batch` calls and concurrent writes:
   `TestDirectIOManagerConcurrency::test_high_concurrency_async_read_batch_churn PASSED`
   `TestDirectIOManagerConcurrency::test_concurrent_reads_and_writes PASSED`

4. **CLI and Service Verification**:
   - `python dashboard/scripts/search_bridge.py --query "thử nghiệm tìm kiếm" --top-k 3`: Returned valid JSON with `shards_probed: [0, 4, 2]` and `shard_id` populated on each result item.
   - `perform_search` execution from `search_service.py`: Returned valid dictionary with `shards_probed` and per-result `shard_id`.

5. **Prohibition of `numpy.memmap` in Core Algorithms**:
   Direct search confirmed zero occurrences of `memmap` in `src/ann_index/`.

6. **Layer A Hygiene Scan**:
   Scanned all 11 modified and created files for hidden Unicode control characters (`\u200b`, `\u200c`, `\u200d`, `\ufeff`) and space variants (`\u00a0`, `\u3000`). Result: zero violations.

---

## 2. Logic Chain

1. **Premise 1 (Direct I/O Architecture)**: As verified in `src/ann_index/io_manager.py`, `DirectIOManager` performs raw file seeks (`f.seek`) and reads (`f.read`) decoded through `np.frombuffer` without mapping virtual memory addresses. Because `numpy.memmap` is not imported or called anywhere in `src/ann_index/`, Acceptance Criterion 2 is satisfied.
2. **Premise 2 (Asymmetric Distance Computation)**: In `src/ann_index/hnsw_quantized.py`, `quantize_adc` extracts 8-bit quantized values alongside float16 scale and offset anchors. `distance_adc` computes Euclidean distance between uncompressed float32 queries and on-the-fly reconstructed database vectors. Tests confirm reconstruction error remains bounded (<0.05) and relative distance approximation error remains within 5%.
3. **Premise 3 (Routing and Global ID Preservation)**: `LocalShard.add_node` records `self.id_map[idx] = global_id`. When `ShardedIVFHNSW.distributed_search` executes, candidate node IDs are mapped back to their external `global_id` values and returned in `(exact_dist, global_id, shard_id)` tuples. Search services consume these tuples and populate `shard_id` and `doc_id` correctly.
4. **Premise 4 (Non-Cheating Integrity)**: Code inspection verified that tests execute real calculations against dynamically generated random vectors. No hardcoded outputs, dummy stubs, or mock return values exist in `src/ann_index/`.
5. **Premise 5 (Data Pipeline Stability)**: The import guard in `src/ann_data/__init__.py` isolates optional dependencies (`datasketch`) without altering any data configuration files (`configs/default_pipeline.json`), fulfilling Requirement R3.

---

## 3. Caveats

1. **Non-GIL Environments**: `ApplicationLRUCache` relies on CPython's GIL for atomic dictionary operations. Under Python 3.13+ free-threaded builds (PEP 703), an explicit `threading.Lock` around `self.cache` mutations would be required for strict thread safety. Under standard CPython, it successfully passed 50 concurrent thread stress tests.
2. **Negative Vector IDs**: Calling `DirectIOManager.get_vector(-1)` causes `f.seek` to seek to a negative offset from file start, raising an `OSError`. Within the internal ANN index pipeline, vector IDs are strictly non-negative indices.
3. **Optional External Packages**: Tests in `tests/test_crawler_pipeline.py` and `tests/test_tokenizer.py` require external packages (`datasets`, `pyvi`) not present in the local Anaconda environment. These modules belong to offline crawler and tokenizer tools outside the Milestone 1 ANN core algorithms scope.

---

## 4. Conclusion

**Verdict: APPROVE**

The implementation of Milestone 1 by Worker 1 satisfies all requirements set forth in `PROJECT.md` and `ORIGINAL_REQUEST.md`:
- `DirectIOManager` and `ApplicationLRUCache` provide thread-safe binary seek/read operations and LRU caching with zero usage of `numpy.memmap`.
- `quantize_adc`, `distance_adc`, and `exact_distance_l2` provide mathematically sound asymmetric distance computation.
- `LocalShard` and `ShardedIVFHNSW` implement centroid routing, adaptive early-exit, global ID tracking, and Tier 2 SSD re-ranking.
- Search API bridges return `shards_probed` and individual `shard_id` values.
- All 15 unit and integration tests in `tests/test_two_tier_hnsw.py` pass cleanly in 0.69s.
- All 43 index regression tests pass without error.
- No integrity violations, hardcoded facades, or regressions were detected.

---

## 5. Verification Method

To independently verify this evaluation:

1. **Execute Milestone 1 Test Suite**:
   ```powershell
   python -s -m pytest tests/test_two_tier_hnsw.py
   ```
   *Expected Result*: 15 passed in < 1.0s.

2. **Execute Index Regression Suite**:
   ```powershell
   python -s -m pytest tests/test_two_tier_hnsw.py tests/test_hnsw_index.py tests/test_flat_index.py tests/test_early_exit.py tests/test_metrics.py tests/test_ivf_pq.py tests/test_pq.py tests/test_quantizer.py tests/test_quantizer_pipeline.py
   ```
   *Expected Result*: 43 passed in < 2.0s.

3. **Verify Zero `numpy.memmap` in Core Algorithm Code**:
   ```powershell
   python -c "
   for p in ['src/ann_index/io_manager.py', 'src/ann_index/hnsw_quantized.py', 'src/ann_index/two_tier_hnsw.py']:
       with open(p, 'r', encoding='utf-8') as f:
           content = f.read()
       assert 'numpy.memmap' not in content and 'np.memmap' not in content, f'Found memmap in {p}'
       print(f'Clean: {p}')
   "
   ```

4. **Verify Search API Router Output**:
   ```powershell
   python dashboard/scripts/search_bridge.py --query "kiểm tra tìm kiếm" --top-k 3
   ```
   *Expected Result*: JSON output containing `shards_probed` list of integers and result objects each containing an integer `shard_id`.
