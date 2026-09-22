# Handoff Report — Reviewer 2 Replacement (Storage Alignment & Search Bridge Verifier)

## 1. Observation

### 1.1 Direct Inspection of Storage Offset and File Mode in `src/ann_index/two_tier_hnsw.py`
- **File**: `src/ann_index/two_tier_hnsw.py`, lines 211–220:
  ```python
  def _save_to_ssd(self, idx: int, vector: np.ndarray) -> None:
      """Write raw float32 vector bytes at exact offset in storage file."""
      if not os.path.exists(self.io_manager.filepath):
          open(self.io_manager.filepath, "wb").close()
      offset = idx * self.vector_bytes
      with open(self.io_manager.filepath, "r+b") as f:
          f.seek(offset)
          vector.astype(np.float32).tofile(f)
      self.io_manager.lru_cache.put(idx, vector.astype(np.float32))
  ```
- **File**: `src/ann_index/two_tier_hnsw.py`, lines 64–71:
  ```python
  # --- Tier 2 (Direct I/O SSD Storage) ---
  os.makedirs(storage_dir, exist_ok=True)
  db_path = os.path.join(storage_dir, f"shard_{shard_id}.bin")
  self.io_manager = DirectIOManager(db_path, dim=dim)
  if clean_storage:
      open(self.io_manager.filepath, "wb").close()
      self.io_manager.lru_cache.clear()
  ```
- **File**: `src/ann_index/two_tier_hnsw.py`, lines 255–258:
  ```python
  self.shards = [
      LocalShard(i, dim, capacity_per_shard, storage_dir, clean_storage=clean_storage)
      for i in range(num_shards)
  ]
  ```
- **File**: `dashboard/scripts/search_bridge.py`, lines 156–162:
  ```python
  router = ShardedIVFHNSW(
      dim=dim,
      num_shards=num_shards,
      capacity_per_shard=max(num_vectors, 1000),
      storage_dir=storage_dir,
      clean_storage=True,
  )
  ```
- **File**: `dashboard/scripts/search_service.py`, lines 67–73:
  ```python
  G_ROUTER = ShardedIVFHNSW(
      dim=dim,
      num_shards=num_shards,
      capacity_per_shard=capacity,
      storage_dir=storage_dir,
      clean_storage=True,
  )
  ```

### 1.2 Storage File Size Stability Across Repeated CLI Invocations
Direct execution of `python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5` three consecutive times produced identical byte sizes across all files in `shards_db/`:
- **Run 1**:
  - `shard_0.bin`: 150,528 bytes (98 vectors * 1,536 bytes)
  - `shard_1.bin`: 0 bytes
  - `shard_2.bin`: 1,536 bytes (1 vector * 1,536 bytes)
  - `shard_3.bin`: 0 bytes
  - `shard_4.bin`: 1,536 bytes (1 vector * 1,536 bytes)
- **Run 2**:
  - Exact same sizes (150528, 0, 1536, 0, 1536 bytes)
- **Run 3**:
  - Exact same sizes (150528, 0, 1536, 0, 1536 bytes)
- **Disk growth observed**: 0 bytes across runs.

### 1.3 Returned Search Results and Mathematical Bounds on Distances
Execution output from `dashboard/scripts/search_bridge.py`:
- `query`: `"tìm kiếm phân tán"`
- `shards_probed`: `[0, 4, 2]`
- `shards_hit`: `[0, 4, 2]`
- `results`:
  - Rank 1: `doc_id`: `synthetic_0`, `shard_id`: 0, `node_id`: 0, `distance`: 0.0, `similarity_score`: 1.0
  - Rank 2: `doc_id`: `synthetic_4`, `shard_id`: 4, `node_id`: 4, `distance`: 1.3763, `similarity_score`: 0.0528
  - Rank 3: `doc_id`: `synthetic_3`, `shard_id`: 0, `node_id`: 3, `distance`: 1.4181, `similarity_score`: 0.0
  - Rank 4: `doc_id`: `synthetic_1`, `shard_id`: 0, `node_id`: 1, `distance`: 1.4358, `similarity_score`: 0.0
  - Rank 5: `doc_id`: `synthetic_2`, `shard_id`: 2, `node_id`: 2, `distance`: 1.4517, `similarity_score`: 0.0
- All distance values are in $[0.0, 1.4517]$, strictly $\le 2.0$.

### 1.4 Preservation of Requirement R3
`git diff configs/ src/crawler/ src/quantizer/ scripts/ data/` returns empty.
`git diff src/ann_data/` shows only the guarded import in `src/ann_data/__init__.py` for optional `datasketch` dependencies. All data loaders, configs, crawlers, and storage modules are intact.

### 1.5 Automated Test Suite Execution
- `python -s -m pytest tests/test_stress_core_index.py tests/test_two_tier_hnsw.py tests/test_search_edge_cases.py`:
  - 56 passed in 16.52s (0 failures).
- `python -s -m pytest tests/test_adversarial_lru_concurrency.py`:
  - 5 passed in 5.89s (0 failures under 40-thread stress contention).

---

## 2. Logic Chain

1. **Premise 1 (Offset Alignment Fix)**: In Observation 1.1, `LocalShard._save_to_ssd` uses mode `"r+b"` and calls `f.seek(idx * self.vector_bytes)`. Because `idx` increments monotonically ($0, 1, 2, \dots$) in `add_node`, each 384-dimensional float32 vector (1,536 bytes) is written directly into its indexed byte slot without file-pointer drift.
2. **Premise 2 (Truncation on Init)**: In Observation 1.1, `clean_storage=True` explicitly executes `open(self.io_manager.filepath, "wb").close()` and clears `lru_cache` upon initialization. This prevents previous runs from accumulating duplicate vectors or inflating file sizes.
3. **Premise 3 (Zero Disk Leakage)**: In Observation 1.2, three successive executions of `search_bridge.py` maintained identical file sizes (150,528 bytes for shard 0, 1,536 bytes for shard 2 and 4). No 1.5MB per-call expansion occurred.
4. **Premise 4 (Valid Geometric Distances)**: In Observation 1.3, normalized 384-dimensional unit vectors produced Euclidean distances between 0.0 and 1.4517. These satisfy the theoretical Euclidean distance bound for unit vectors ($\sqrt{2(1 - \cos \theta)} \in [0, 2]$).
5. **Premise 5 (Zero Integrity Violations)**: Static inspection and dynamic execution confirm no hardcoded results, no stubbed early-exits, and zero usage of deprecated `numpy.memmap`.
6. **Premise 6 (R3 Compliance)**: In Observation 1.4, git status and diffs show that all ingestion, crawler, quantizer, config, and dataset files remain untouched.

---

## 3. Caveats

- `sentence_transformers` is not pre-installed in the local execution environment. Both `search_bridge.py` and `search_service.py` gracefully activate the deterministic `MockEmbedder` fallback, as intended by system design.
- Multi-process write access to the same shard binary file is not protected by OS-level file locks (`flock`). For the single-node architecture defined in `PROJECT.md`, index building and queries run within a single process.

---

## 4. Conclusion

**Verdict**: **APPROVE**

The SSD storage alignment bug and disk leak have been resolved:
- `LocalShard._save_to_ssd` correctly writes with mode `"r+b"` at exact seek offsets `idx * self.vector_bytes`.
- `clean_storage` handling in `LocalShard` and `ShardedIVFHNSW` guarantees clean state management.
- `search_bridge.py` and `search_service.py` initialize with `clean_storage=True`.
- File sizes in `shards_db/` remain constant across queries.
- Distances are within valid geometric bounds $\le 2.0$.
- Requirement R3 remains 100% satisfied.
- All 61 test cases across the standard and adversarial suites pass cleanly.

---

## 5. Verification Method

To independently reproduce and verify this assessment:

1. **Verify SSD seek alignment and file mode**:
   Inspect lines 211–220 in `src/ann_index/two_tier_hnsw.py`.
2. **Verify disk stability and distance bounds across multiple queries**:
   ```powershell
   python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5
   Get-ChildItem -Path f:\ANN\shards_db | Select-Object Name, Length
   python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5
   Get-ChildItem -Path f:\ANN\shards_db | Select-Object Name, Length
   ```
   Check that `Length` values do not change between runs and all returned `distance` fields in JSON output are $\le 2.0$.
3. **Verify core test suite (56 tests)**:
   ```powershell
   python -s -m pytest tests/test_stress_core_index.py tests/test_two_tier_hnsw.py tests/test_search_edge_cases.py
   ```
4. **Verify adversarial concurrency suite (5 tests)**:
   ```powershell
   python -s -m pytest tests/test_adversarial_lru_concurrency.py
   ```
5. **Verify Requirement R3 compliance**:
   ```powershell
   git diff configs/ src/crawler/ src/quantizer/ scripts/ data/
   ```
   Expected: zero diff lines.
