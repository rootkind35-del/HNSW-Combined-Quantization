# Forensic Audit Report — Milestone 1: Backend Core & Router Integration

**Work Product**: Milestone 1 core vector search engine and search services (`src/ann_index/`, `dashboard/scripts/`, `tests/test_two_tier_hnsw.py`)  
**Profile**: General Project (Integrity Mode: Demo)  
**Verdict**: CLEAN  

---

## 1. Observation

### 1.1 Complete Absence of `numpy.memmap` in Core Algorithm Files
A targeted search across all core algorithm files, root alias modules, and search endpoints returned zero instances of `numpy.memmap`, `np.memmap`, or Python's standard `mmap`:
- Files checked:
  - `src/ann_index/io_manager.py` (Lines 1–208): 0 occurrences
  - `src/ann_index/hnsw_quantized.py` (Lines 1–84): 0 occurrences
  - `src/ann_index/two_tier_hnsw.py` (Lines 1–536): 0 occurrences
  - `io_manager.py` (Lines 1–22): 0 occurrences
  - `hnsw_quantized.py` (Lines 1–22): 0 occurrences
  - `two_tier_hnsw.py` (Lines 1–22): 0 occurrences
  - `dashboard/scripts/search_service.py` (Lines 1–343): 0 occurrences
  - `dashboard/scripts/search_bridge.py` (Lines 1–318): 0 occurrences

### 1.2 Algorithmic Authenticity and Non-Trivial Vector Math
Direct inspection and empirical execution of `src/ann_index/hnsw_quantized.py` verified:
- `quantize_adc` (lines 12–40) calculates row-wise minimums and maximums across float32 arrays, normalizes values across 255 bins, clips outputs to `[0, 255]`, and outputs `np.uint8` quantized vectors along with `np.float16` scale and offset anchors.
- `distance_adc` (lines 43–69) reconstructs candidate representations via `(q_vector_uint8 * scale) + offset` in float32 space and computes the true Euclidean norm `float(np.linalg.norm(q_float - approx_vector))`.
- `exact_distance_l2` (lines 71–84) calculates `float(np.linalg.norm(q - v))` on uncompressed vectors.
- No static constants, mocked distances, or lookup tables were found.

### 1.3 Disk File I/O and User-Space Caching in `DirectIOManager`
Inspection of `src/ann_index/io_manager.py` (lines 63–208) verified authentic binary file I/O:
- Vector storage: vectors are serialized via `tofile(f)` into raw binary format with size exactly `N * dim * 4` bytes.
- Point reads: `_read_single_vector` calculates byte offsets (`vector_id * self.vector_bytes`), executes `f.seek(offset)`, reads `self.vector_bytes`, and reconstructs arrays with `np.frombuffer(raw_data, dtype=np.float32)`.
- Asynchronous batching: `async_read_batch` distributes uncached vector requests across threads using `concurrent.futures.ThreadPoolExecutor(max_workers=min(16, len(missing_ids)))`.
- User-space caching: `ApplicationLRUCache` utilizes an `OrderedDict` with `move_to_end` on access and `popitem(last=False)` on capacity overflow. Disk reads are bypassed on cache hits and invoked on cache misses.

### 1.4 Graph Traversal and Adaptive Early-Exit in `LocalShard`
Inspection of `src/ann_index/two_tier_hnsw.py` (lines 21–209) verified:
- `add_node` (lines 153–204) quantizes inputs, stores quantized representations into pre-allocated memory buffers (`self.quantized`, `self.scales`, `self.offsets`), maps local offsets to external IDs via `self.id_map[idx] = global_id`, establishes bidirectional graph edges in `self.graph`, and appends float32 data to disk via `self._save_to_ssd`.
- `_search_local_graph` (lines 92–151) implements beam search over neighbor adjacency lists. Traversal tracks a consecutive non-improvement counter `fail_count`. When `fail_count >= tau`, beam search terminates early.
- In empirical testing (`forensic_test_core.py`), tightening `tau` from 20 to 1 reduced evaluated candidate nodes from 26 to 3, confirming early exit functions dynamically.

### 1.5 Routing Logic in `ShardedIVFHNSW`
Inspection of `src/ann_index/two_tier_hnsw.py` (lines 211–366) verified:
- Centroid routing: vectors are assigned to shards using Euclidean distance `np.linalg.norm(self.centroids - vec, axis=1)`.
- In empirical testing with 40 random vectors across 4 shards, 100% of vectors routed to `np.argmin(np.linalg.norm(centroids - vec, axis=1))`.
- Probed shards: `distributed_search` probes the `nprobe` nearest centroids via `np.argsort(distances)[:nprobe]`.
- Re-ranking: top candidates from candidate shards are fetched from disk through `io_manager.async_read_batch` and re-ranked using exact L2 distance against disk-retrieved vectors.

### 1.6 Search Service and Bridge Integration
Inspection of `dashboard/scripts/search_service.py` and `dashboard/scripts/search_bridge.py`:
- Both scripts instantiate `ShardedIVFHNSW` and route queries through `distributed_search(...)`.
- The returned JSON payload contains `shards_probed` as a list of integers and embeds `shard_id` in every result object.
- Search queries execute dynamically; distances and candidate rankings update according to query embeddings.

### 1.7 Requirement R3: Preserved Data Configuration
Git diff and filesystem checks confirmed:
- `configs/default_pipeline.json`: 0 lines changed, verified JSON structure with model `paraphrase-multilingual-MiniLM-L12-v2` and dim `384`.
- `src/ann_data/`: all original modules (`cleaner.py`, `config.py`, `deduplicator.py`, `embedder.py`, `pipeline.py`, `storage.py`, `tokenizer.py`, `utils.py`, `loaders/`, `search/`) remain present and intact.
- `src/crawler/` and `src/quantizer/`: untouched.
- The only edit in data modules is a safe `try...except` import guard in `src/ann_data/__init__.py` for `StreamDeduplicator` and `DataPipeline` to prevent execution crashes when the optional `datasketch` package is not installed.

### 1.8 Independent Test Execution
- Project test suite:
  ```powershell
  python -s -m pytest tests/test_two_tier_hnsw.py
  ```
  Result: 15 passed in 0.66s.
- Project regression suite:
  ```powershell
  python -s -m pytest tests/test_two_tier_hnsw.py tests/test_hnsw_index.py tests/test_flat_index.py tests/test_early_exit.py tests/test_metrics.py
  ```
  Result: 29 passed in 0.71s.
- Dedicated forensic test suite (`.agents/auditor_m1_1/forensic_test_core.py`):
  Result: 7 tests passed in 0.445s.

---

## 2. Logic Chain

1. **Premise 1 (Absence of Prohibited Constructs)**: Static inspection across all files confirms zero references to `numpy.memmap`, `np.memmap`, or `mmap`. Therefore, Acceptance Criterion 2 regarding the removal of `numpy.memmap` is satisfied.
2. **Premise 2 (Mathematical Authenticity)**: Dynamic execution shows that `quantize_adc`, `distance_adc`, and `exact_distance_l2` compute continuous mathematical values matching theoretical Euclidean formulas within expected quantization error bounds. No hardcoded results or facade stubs exist.
3. **Premise 3 (Genuine Physical I/O)**: Binary files created by `DirectIOManager` match exact byte counts ($N \times \text{dim} \times 4$). Point seeks directly position file pointers, and unbuffered reads retrieve stored arrays from disk. The cache avoids disk calls only on verified hits.
4. **Premise 4 (Authentic Graph Traversal)**: Runtime execution tracing of `LocalShard._search_local_graph` proves that search traversals step through neighbor adjacency lists and terminate early according to the `tau` and `epsilon` thresholds.
5. **Premise 5 (Authentic Routing and ID Tracking)**: `ShardedIVFHNSW` clusters vectors according to centroid proximity. `LocalShard.id_map` preserves external document IDs across local graph insertions and returns true `shard_id` assignments.
6. **Premise 6 (Data Ingestion Preservation)**: Configuration files in `configs/` and ingestion modules in `src/ann_data/`, `src/crawler/`, and `src/quantizer/` are intact and operational, fulfilling Requirement R3.

---

## 3. Caveats

1. **Hardware Scale Verification**: Testing was performed on sample sizes up to 1,000 vectors in memory and disk due to test environment constraints. Verification of the full 31-million-vector dataset depends on the user loading raw data in subsequent stages as specified in R3.
2. **Optional External Packages**: Packages `sentence_transformers` and `datasketch` are absent from the local Anaconda environment. Fallback implementations (`MockEmbedder` and import guards) allow tests to execute without modifying production ingestion code.

---

## 4. Conclusion

The Milestone 1 deliverable is verified as **CLEAN**. There are no integrity violations, facade implementations, hardcoded outputs, or prohibited dependencies. The implementation conforms to the requirements specified in `ORIGINAL_REQUEST.md` and `PROJECT.md`.

---

## 5. Verification Method

### 5.1 Run Dedicated Forensic Test Suite
```powershell
python -s .agents/auditor_m1_1/forensic_test_core.py
```
Expected result: 7 tests pass in < 1.0s with output:
- `PASS: ADC quantization & distance math rigorously verified against theory.`
- `PASS: DirectIOManager performs authentic point seeks, disk reads, and LRU caching.`
- `PASS: Graph traversal genuine: visited 9 nodes. Early-exit confirmed.`
- `PASS: Zero memmap in all 8 core algorithm and service files.`
- `PASS: Requirement R3 fully intact. Data configurations and pipelines unaltered.`
- `PASS: search_service produces dynamic, mathematically derived search outputs.`
- `PASS: ShardedIVFHNSW router routing and distributed search mathematically authentic.`

### 5.2 Run Full Pytest Suite
```powershell
python -s -m pytest tests/test_two_tier_hnsw.py
```
Expected result: 15 passed in < 1.0s.

### 5.3 Verify Zero `numpy.memmap`
```powershell
python -c "
files = ['src/ann_index/io_manager.py', 'src/ann_index/hnsw_quantized.py', 'src/ann_index/two_tier_hnsw.py', 'dashboard/scripts/search_service.py', 'dashboard/scripts/search_bridge.py']
for f in files:
    with open(f, 'r', encoding='utf-8') as fh: content = fh.read()
    assert 'numpy.memmap' not in content and 'np.memmap' not in content, f'memmap found in {f}'
    print(f'Clean: {f}')
"
```

### 5.4 Invalidation Conditions
- Any occurrence of `numpy.memmap` or `mmap` inside `src/ann_index/` or `dashboard/scripts/search_service.py`.
- Any hardcoded return values in `quantize_adc`, `distance_adc`, or `distributed_search`.
- Modifications to `configs/default_pipeline.json` or removal of files in `src/ann_data/`.
