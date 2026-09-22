# Branch & Core Architecture Exploration Report

## 1. Observation

### 1.1 Git Repository State, Branches, and Commits
- Current working branch: `main`.
- Untracked files on `main`: `.agents/`, `ORIGINAL_REQUEST.md`, `prompt_draft.md`.
- Active branches detected via `git branch -a`:
  - `main`
  - `update`
  - `remotes/origin/main`
  - `remotes/origin/update`
- Branch commit history:
  - `main` HEAD: `1401398 feat(dashboard): implement Data Product Designer studio with 2D UMAP scatter, HNSW laser trajectory, trade-off radar, and text heatmap`
  - `update` HEAD: `7e745d4 điều chỉnh lại logic cụm máy chủ phân tán`
  - Merge-base between `main` and `update`: `140139883585bc2fb220a5fbe16cd486e81ea555`.
  - The `update` branch is exactly 1 commit ahead of `main`.

### 1.2 Branch File Differences (`git diff --name-status main..update`)
Commit `7e745d4` on branch `update` removed the project structure and replaced it with flat standalone scripts and binary artifacts:
- Deleted files in `update`:
  - Configuration and root files: `.gitignore`, `README.md`, `pyproject.toml`, `configs/default_pipeline.json`, `ann_10m_thesis_report.md`.
  - Source directories: `src/ann_data/` (13 files), `src/ann_index/` (11 files), `src/crawler/` (10 files), `src/quantizer/` (5 files).
  - Test suite: `tests/` (24 files).
  - Benchmark and pipeline scripts: `scripts/` (19 files).
  - Dashboard application: `dashboard/` (25 files including `server.js`, `public/`, `scripts/`).
  - Data folders and documentation: `data/`, `docs/`.
- Added files in `update`:
  - Core algorithms: `two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`.
  - Support scripts: `data_pipeline.py`, `evaluation_metrics.py`.
  - Thesis markdown and assets: `chuong5.pdf`, `chuong5_extracted.md`, `chuong5_utf8.md`, `danh_gia_hieu_nang.md`, `ly_do_lua_chon.md`, `metric_1_ram.png` to `metric_5_io_tail.png`.
  - Binary databases: `vector_db.bin`, `shards_db/shard_0.bin` through `shards_db/shard_9.bin`.
  - Bytecode: `__pycache__/hnsw_quantized.cpython-314.pyc`, `__pycache__/io_manager.cpython-314.pyc`.

### 1.3 Exact Code Implementation in Branch `update`

#### A. `two_tier_hnsw.py` (`update`)
- Path: `two_tier_hnsw.py`
- Imports:
  ```python
  import os
  import numpy as np
  import concurrent.futures
  from io_manager import DirectIOManager
  from hnsw_quantized import quantize_adc, distance_adc
  ```
- Class `LocalShard`:
  - Signature: `__init__(self, shard_id: int, dim: int, max_elements: int, storage_dir: str)`
  - Internal state:
    - `self.shard_id = shard_id`
    - `self.graph = {}` (type: `dict[int, list[int]]`)
    - `self.entry_point = None` (type: `int | None`)
    - `self.quantized = np.zeros((max_elements, dim), dtype=np.uint8)`
    - `self.scales = np.zeros((max_elements, 1), dtype=np.float16)`
    - `self.offsets = np.zeros((max_elements, 1), dtype=np.float16)`
    - `self.local_count = 0`
    - `self.io_manager = DirectIOManager(db_path, dim=dim)` where `db_path = os.path.join(storage_dir, f"shard_{shard_id}.bin")`
  - Method `_calc_distance(self, query: np.ndarray, node_id: int) -> float`:
    - Retrieves `q_vec = self.quantized[node_id]`, `scale = self.scales[node_id][0]`, `offset = self.offsets[node_id][0]`.
    - Returns `distance_adc(query, q_vec, scale, offset)`.
  - Method `_search_local_graph(self, query: np.ndarray, entry_point: int, ef: int, tau: int = 3, epsilon: float = 1e-4) -> list[tuple[float, int]]`:
    - Executes beam search on `self.graph` starting at `entry_point`.
    - Implements adaptive early-exit:
      ```python
      if current_best_dist - n_dist < epsilon:
          fail_count += 1
      else:
          fail_count = 0  
          current_best_dist = n_dist
      if fail_count >= tau:
          break
      ```
    - Caps output list at `ef` candidates and returns `top_results`.
  - Method `add_node(self, global_id: int, vector: np.ndarray, M: int = 16, ef_construction: int = 32) -> None`:
    - Runs `q_vec, scale, offset = quantize_adc(vector.reshape(1, -1))`.
    - Assigns `idx = self.local_count`.
    - Stores `self.quantized[idx] = q_vec[0]`, `self.scales[idx] = scale[0][0]`, `self.offsets[idx] = offset[0][0]`.
    - If `entry_point is None`, sets `entry_point = idx`, calls `_save_to_ssd(vector)`, increments `local_count`, and returns.
    - Otherwise calls `_search_local_graph(query=vector.astype(np.float32), entry_point=self.entry_point, ef=ef_construction)`.
    - Connects reciprocal edges between `idx` and up to `M` nearest neighbors in `self.graph`.
    - Calls `self._save_to_ssd(vector)` and increments `self.local_count`.
  - Method `_save_to_ssd(self, vector: np.ndarray) -> None`:
    - Appends `vector.astype(np.float32).tofile(f)` to `self.io_manager.filepath`.

- Class `ShardedIVFHNSW`:
  - Signature: `__init__(self, dim: int, num_shards: int, capacity_per_shard: int, storage_dir: str)`
  - Internal state:
    - `self.dim = dim`
    - `self.num_shards = num_shards`
    - `self.centroids = np.random.randn(num_shards, dim).astype(np.float32)` (fixed seed 42)
    - `self.shards = [LocalShard(i, dim, capacity_per_shard, storage_dir) for i in range(num_shards)]`
  - Method `_get_nearest_shards(self, vector: np.ndarray, nprobe: int) -> list[int]`:
    - Computes `distances = np.linalg.norm(self.centroids - vector, axis=1)`.
    - Returns `np.argsort(distances)[:nprobe].tolist()`.
  - Method `route_and_insert(self, global_id: int, vector: np.ndarray) -> int`:
    - Identifies target shard: `target_shard_id = self._get_nearest_shards(vector, nprobe=1)[0]`.
    - Inserts node: `self.shards[target_shard_id].add_node(global_id, vector)`.
    - Returns `target_shard_id`.
  - Method `distributed_search(self, query: np.ndarray, top_k: int, nprobe: int = 3, re_rank_limit: int = 50) -> list[tuple[float, int, int]]`:
    - Step 1 (Router): Calls `_get_nearest_shards(query, nprobe=nprobe)` to obtain candidate shard IDs.
    - Step 2 (Tier 1 In-Memory Search): Iterates over target shards, executes `shard._search_local_graph(query, shard.entry_point, ef=re_rank_limit)`. Gathers candidates as `(dist, node_id, sid)` and selects top `re_rank_limit`.
    - Step 3 (Tier 2 SSD Direct I/O): Groups candidates by `sid`. Calls `self.shards[sid].io_manager.async_read_batch(node_ids)` to retrieve original float32 vectors asynchronously.
    - Step 4 (Re-ranking): Calculates exact L2 distance `np.linalg.norm(query - exact_vec)` for each candidate.
    - Returns top `top_k` sorted results as `[(exact_dist, node_id, sid), ...]`.

#### B. `hnsw_quantized.py` (`update`)
- Path: `hnsw_quantized.py`
- Function `quantize_adc(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]`:
  - Input: `vectors: np.ndarray` (float32, 2D).
  - Normalization:
    ```python
    min_val = np.min(vectors, axis=1, keepdims=True)
    max_val = np.max(vectors, axis=1, keepdims=True)
    range_val = max_val - min_val
    range_val[range_val == 0] = 1e-8
    scale = (range_val / 255.0).astype(np.float16)
    offset = min_val.astype(np.float16)
    normalized = (vectors - min_val) / range_val
    quantized_vectors = np.round(normalized * 255).astype(np.uint8)
    ```
  - Returns `(quantized_vectors, scale, offset)` with uint8 vectors and float16 per-vector scaling anchors.
- Function `distance_adc(query_float32: np.ndarray, q_vector_uint8: np.ndarray, scale: np.float16, offset: np.float16) -> float`:
  - Input: Uncompressed float32 query, uint8 stored vector, float16 scale, float16 offset.
  - Calculation:
    ```python
    approx_vector = (q_vector_uint8.astype(np.float32) * scale) + offset
    distance = np.linalg.norm(query_float32 - approx_vector)
    return float(distance)
    ```
- Function `exact_distance_l2(query: np.ndarray, vector: np.ndarray) -> float`:
  - Returns `float(np.linalg.norm(query - vector))`.

#### C. `io_manager.py` (`update`)
- Path: `io_manager.py`
- Class `ApplicationLRUCache`:
  - Inherits standard `OrderedDict` structure.
  - `__init__(self, capacity: int = 10000)`: Stores capacity, maintains key order.
  - `get(self, key: int) -> np.ndarray | None`: Calls `self.cache.move_to_end(key)` on hit.
  - `put(self, key: int, value: np.ndarray) -> None`: Inserts value, calls `self.cache.move_to_end(key)`, and evicts oldest element via `self.cache.popitem(last=False)` if size exceeds capacity.
- Class `DirectIOManager`:
  - `__init__(self, filepath: str, dim: int = 384, cache_capacity: int = 10000)`:
    - Calculates vector stride: `self.vector_bytes = dim * 4`.
    - Initializes `self.lru_cache = ApplicationLRUCache(capacity=cache_capacity)`.
    - Ensures binary file exists on disk (`open(self.filepath, 'wb').close()`).
  - `_read_single_vector(self, vector_id: int) -> np.ndarray`:
    - Opens `self.filepath` in binary read mode (`rb`).
    - Executes file seek: `f.seek(vector_id * self.vector_bytes)`.
    - Reads exact byte block: `raw_data = f.read(self.vector_bytes)`.
    - Reconstructs array: `np.frombuffer(raw_data, dtype=np.float32).copy()`.
    - Completely omits `numpy.memmap`.
  - `get_vector(self, vector_id: int) -> np.ndarray`:
    - Checks LRU cache hit. If missed, reads from disk via `_read_single_vector` and updates cache.
  - `async_read_batch(self, vector_ids: list[int]) -> dict[int, np.ndarray]`:
    - Executes parallel disk reads using `concurrent.futures.ThreadPoolExecutor(max_workers=16)`.
    - Collects completed futures and returns `{vid: vector, ...}`.

### 1.4 Comparison Against Corresponding Files on Branch `main`

| Feature / Component | Branch `main` | Branch `update` |
|---|---|---|
| Architecture style | Monolithic single-node index (`src/ann_index/two_tier_hnsw.py: TwoTierQuantizedHNSW`) | Distributed sharded index (`two_tier_hnsw.py: ShardedIVFHNSW` + `LocalShard`) |
| Partitioning & Routing | No partitioning; single graph for all vectors | Centroid-based IVF Router with `nprobe` parameter (`_get_nearest_shards`) |
| Quantization method | Dataset-wide column-wise `ScalarQuantizer(per_channel=True)` (`src/ann_index/quantizer.py`) | Dynamic row-wise SQ8 per vector with `float16` scale and offset (`hnsw_quantized.py: quantize_adc`) |
| Distance computation | Symmetric distance between two uint8 vectors with scale offset | Asymmetric Distance Computation (ADC): float32 query against uint8 vector (`distance_adc`) |
| Early-exit implementation | `AdaptiveEarlyExitController` in `src/ann_index/early_exit.py` using `collections.deque` and sliding window | Inlined in `LocalShard._search_local_graph` using `fail_count`, `tau`, `epsilon` |
| Tier 2 SSD Storage | `numpy.memmap` (`src/ann_data/storage.py`, `src/quantizer/storage.py`, `src/ann_index/two_tier_hnsw.py`) | `DirectIOManager` with raw binary seek/read + `ThreadPoolExecutor` + `ApplicationLRUCache` (`io_manager.py`) |
| Search API integration | Linear dot product on preloaded `G_VECTORS` (`dashboard/scripts/search_service.py:88`) | Standalone CLI test script; not yet wired into `search_service.py` |
| Dashboard UI footprint | Bloated with 3D engines (`three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, `dimension_reduction_3d.py`) | Dashboard directory was completely deleted in `update` commit `7e745d4` |
| Dependency constraints | Pyproject dependencies require `datasketch` for `StreamDeduplicator`, which is pulled in by `ann_index.__init__` | Self-contained, standard library (`concurrent.futures`, `os`, `collections`) + `numpy` |

---

## 2. Logic Chain

1. **Premise 1 (Git History)**: Observation 1.1 reveals that `update` has only one unique commit (`7e745d4`) above `main` (`1401398`). A standard git merge or checkout of `update` would delete `src/`, `dashboard/`, `tests/`, and `configs/`. Therefore, the distributed algorithms must be transplanted into the existing `main` project structure rather than doing a naive branch merge.
2. **Premise 2 (Algorithm Evolution)**: Observation 1.3 shows that `two_tier_hnsw.py` on `update` introduces two key architectural abstractions (`ShardedIVFHNSW` and `LocalShard`) that replace monolithic graph construction with cluster-routed search.
3. **Premise 3 (Quantization & ADC)**: Observation 1.3.B shows `quantize_adc` and `distance_adc`. In contrast to `main`'s `ScalarQuantizer` (which requires pre-fitting all data and quantizing the query), ADC keeps the query vector in float32 and evaluates distances on dynamically reconstructed vectors ($Query \times (Vector_{uint8} \times Scale + Offset)$), yielding higher recall without full dataset decompression.
4. **Premise 4 (Elimination of `numpy.memmap`)**: Observation 1.3.C confirms that `DirectIOManager` replaces `numpy.memmap` by seeking directly into `.bin` files and batching reads over 16 worker threads, coupled with an application-level LRU cache. This directly addresses the requirement in `ORIGINAL_REQUEST.md` to remove reliance on `numpy.memmap`.
5. **Premise 5 (Search Service Gap)**: Observation 1.4 confirms that `dashboard/scripts/search_service.py` on `main` does not execute `TwoTierQuantizedHNSW` or `ShardedIVFHNSW`. It computes `np.dot(G_VECTORS, query_vec)` directly. To satisfy acceptance criterion R1, `search_service.py` must initialize `ShardedIVFHNSW` and route search requests through `router.distributed_search(...)`.
6. **Premise 6 (Dashboard Cleanup)**: Observation 1.4 confirms that `dashboard/public/js/` contains four unused 3D engine files (`three_*.js`) and `dashboard/scripts/dimension_reduction_3d.py`. Removing them satisfies requirement R2 without disrupting 2D search presentation.
7. **Premise 7 (Global ID Tracking in Shards)**: Observation 1.3.A reveals that `LocalShard.add_node(global_id, vector)` does not store `global_id`. During `distributed_search`, it returns `(exact_dist, node_id, sid)`. Because `node_id` is the local shard index (`0..local_count-1`), the search service will not be able to retrieve the correct original document metadata unless `LocalShard` maintains a mapping from `node_id` to `global_id`. Adding an internal array `self.global_ids = np.zeros(max_elements, dtype=np.int64)` is necessary for metadata retrieval.

---

## 3. Caveats

1. **Pre-existing Dataset Formats**: In `data/quantized_combined/` and `data/processed/`, existing data files are formatted as `.dat` and `.npz`. The `ShardedIVFHNSW` implementation on `update` expects `.bin` shards in `shards_db/` or builds them dynamically via `route_and_insert`. The data loading bridge must adapt the existing dataset without altering its format (satisfying R3).
2. **Import Coupling in `src/ann_index/__init__.py`**: Importing `ann_index` currently triggers `src/ann_index/benchmark.py`, which pulls `src/ann_data/deduplicator.py` and fails if `datasketch` is missing from the environment. Lazy imports or decoupling in `__init__.py` should be applied during integration to prevent test and import failures.
3. **Centroid Initialization**: In `two_tier_hnsw.py` on `update`, centroids are initialized via `np.random.randn`. For production accuracy, centroids can either be seeded from a sample k-means fit or initialized deterministically.

---

## 4. Conclusion

The core architectural components on branch `update` (`two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`) are concise, functional, and self-contained. They successfully implement:
1. Distributed sharding logic via `ShardedIVFHNSW` and `LocalShard`.
2. Asymmetric Distance Computation (ADC) and in-graph adaptive early-exit (`tau`, `epsilon`).
3. Direct file I/O with multithreaded batch reads and LRU caching, completely replacing `numpy.memmap`.

To merge these capabilities into `main` cleanly:
1. **Core Index Placement**: Place `DirectIOManager` and `ApplicationLRUCache` into `src/ann_index/io_manager.py` (or `src/ann_data/io_manager.py`). Integrate `quantize_adc` and `distance_adc` into `src/ann_index/quantizer.py` (or `src/ann_index/hnsw_quantized.py`). Integrate `LocalShard` and `ShardedIVFHNSW` into `src/ann_index/two_tier_hnsw.py` while adding `global_id` tracking.
2. **Search API Wiring**: Refactor `dashboard/scripts/search_service.py` and `dashboard/scripts/search_bridge.py` to instantiate `ShardedIVFHNSW`, feed vectors from the existing cache/corpus, execute queries through `distributed_search`, and return the hit shard IDs (`sid`), distances, and execution latencies.
3. **Dashboard Asset Pruning**: Delete `three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, and `dimension_reduction_3d.py`. Clean up HTML/JS references in `dashboard/public/index.html` and `dashboard/public/js/app.js` to focus on displaying the hit Shard IDs and distributed latency metrics.
4. **Test Suite Alignment**: Add dedicated unit and integration tests for `ShardedIVFHNSW`, `DirectIOManager`, and `quantize_adc`/`distance_adc` in `tests/test_two_tier_hnsw.py`.

---

## 5. Verification Method

### 5.1 Verification Commands
1. Inspect git status and commit difference:
   ```bash
   git status
   git log --oneline main..update
   ```
2. Verify update branch core files directly via git tree:
   ```bash
   git show update:two_tier_hnsw.py
   git show update:hnsw_quantized.py
   git show update:io_manager.py
   ```
3. Test isolated execution of update's core files:
   ```bash
   python -c "import sys; sys.path.insert(0, '.'); from hnsw_quantized import quantize_adc, distance_adc; print('ADC OK')"
   ```
4. Verify tests on main once integrated:
   ```bash
   python -c "import os; os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'; import pytest; pytest.main(['tests/test_two_tier_hnsw.py'])"
   ```

### 5.2 Invalidation Conditions
- If `two_tier_hnsw.py` fails to route queries to specific shard IDs.
- If any reference to `numpy.memmap` remains in the active execution path of `two_tier_hnsw.py` or `io_manager.py`.
- If `search_service.py` continues falling back to linear dot product rather than using `ShardedIVFHNSW.distributed_search`.
