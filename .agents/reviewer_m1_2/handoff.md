# Review Report & Handoff — Reviewer 2: Search API & Data Pipeline

## Review Summary

**Verdict**: REQUEST_CHANGES

---

## 1. Observation

### 1.1 Search API Response Schema and Query Routing
1. In `dashboard/scripts/search_service.py` (lines 118-125):
   ```python
   search_k = min(num_vectors, max(top_k * 4, min_rerank_k, 25))
   router_results, shards_probed = G_ROUTER.distributed_search(
       query=query_vec,
       top_k=search_k,
       nprobe=3,
       re_rank_limit=max(min_rerank_k, search_k),
       return_shards=True,
   )
   ```
2. In `dashboard/scripts/search_bridge.py` (lines 168-174):
   ```python
   search_k = min(num_vectors, max(args.top_k * 4, args.min_rerank_k, 25))
   router_results, shards_probed = router.distributed_search(
       query=query_vec,
       top_k=search_k,
       nprobe=3,
       re_rank_limit=max(args.min_rerank_k, search_k),
       return_shards=True,
   )
   ```
3. Top-level dictionary returns `"shards_probed": shards_probed` in both `search_service.py` (line 238) and `search_bridge.py` (line 282).
4. In both files, each entry appended to `results` contains the required schema fields:
   - `shard_id` (int)
   - `node_id` (int)
   - `doc_id` (str)
   - `title` (str)
   - `preview` (str)
   - `category` (str)
   - `distance` (float)
5. In `dashboard/server.js` (line 432), the endpoint returns `res.json({ success: true, data })`, placing `shards_probed` at `data.shards_probed` and individual results at `data.results`.

### 1.2 Data Pipeline Preservation (Requirement R3)
1. Git diff against HEAD for data directories:
   Command: `git diff HEAD -- src/ann_data/ src/crawler/ src/quantizer/ configs/ scripts/`
   Output: Only `src/ann_data/__init__.py` has modifications. All files in `src/crawler/`, `src/quantizer/`, `configs/default_pipeline.json`, and `scripts/` are identical to HEAD.
2. Safe import guard in `src/ann_data/__init__.py` (lines 5-8, 11-14):
   ```python
   try:
       from ann_data.deduplicator import StreamDeduplicator
   except (ImportError, ModuleNotFoundError):
       StreamDeduplicator = None
   ...
   try:
       from ann_data.pipeline import DataPipeline
   except (ImportError, ModuleNotFoundError):
       DataPipeline = None
   ```
3. Ingestion configuration verification:
   Command: `python -c "import sys; sys.path.insert(0, 'src'); from ann_data.config import PipelineConfig; cfg = PipelineConfig.from_json('configs/default_pipeline.json'); assert cfg.embedding_dim == 384; assert cfg.model_name == 'paraphrase-multilingual-MiniLM-L12-v2'"`
   Result: Exited 0 with exact configuration loaded.

### 1.3 Critical Defect Observed: SSD Storage Append Mode Bug (`"ab"`) and Stale Vector Reads
1. In `src/ann_index/two_tier_hnsw.py` (lines 61-65, 205-209):
   ```python
   # LocalShard.__init__
   os.makedirs(storage_dir, exist_ok=True)
   db_path = os.path.join(storage_dir, f"shard_{shard_id}.bin")
   self.io_manager = DirectIOManager(db_path, dim=dim)
   ...
   def _save_to_ssd(self, vector: np.ndarray) -> None:
       """Append raw float32 vector bytes directly to storage file."""
       with open(self.io_manager.filepath, "ab") as f:
           vector.astype(np.float32).tofile(f)
   ```
2. In `dashboard/scripts/search_bridge.py` (lines 153-165):
   ```python
   storage_dir = os.path.join(BASE_DIR, "shards_db")
   num_shards = 5
   router = ShardedIVFHNSW(
       dim=dim,
       num_shards=num_shards,
       capacity_per_shard=max(num_vectors, 1000),
       storage_dir=storage_dir,
   )
   seed_count = min(num_vectors, 1000)
   for i in range(seed_count):
       router.route_and_insert(global_id=i, vector=vectors[i])
   ```
3. Direct execution of `dashboard/scripts/search_bridge.py`:
   Command: `python dashboard/scripts/search_bridge.py --query "tìm kiếm phân tán" --top-k 5`
   Output snippet:
   ```json
   {"rank": 4, "index": 0, "doc_id": "synthetic_0", "shard_id": 0, "node_id": 0, "distance": 15.0621, "similarity_score": 0.0}
   ```
   Observed distance between unit vectors was 15.0621. Theoretical upper bound for L2 distance between normalized vectors is 2.0.
4. Inspection of `shards_db/shard_0.bin`:
   - File size: 4,065,280 bytes.
   - Vector dimension: 384 (1,536 bytes per vector).
   - Alignment: `4065280 % 1536 = 1024` bytes.
   - 1024 bytes corresponds to 8 vectors of dimension 32 (`8 * 32 * 4 = 1024`), left behind by earlier unit tests.
   - Reading `vector_id = 0` via `DirectIOManager('shards_db/shard_0.bin', dim=384).get_vector(0)` produced an array with L2 norm `15.0663`, matching the bogus distance `15.0621`.
5. Disk growth:
   Every execution of `search_bridge.py` appends 1,000 vectors (~1.5 MB) into `shards_db/shard_*.bin`. The storage files grew from 3.61 MB to 4.06 MB across three query calls.

---

## 2. Logic Chain

1. **Premise 1 (Offset Expectation)**: `DirectIOManager._read_single_vector(vector_id)` computes file seek position as `offset = vector_id * self.vector_bytes`. For candidate node `local_node_id = 0`, it reads bytes from offset 0.
2. **Premise 2 (In-Memory vs On-Disk Desynchronization)**: In `LocalShard.__init__`, the in-memory graph index starts empty with `self.local_count = 0`. However, `_save_to_ssd` opens the file with mode `"ab"`. If `shard_{shard_id}.bin` already contains data from previous sessions or tests, the vector for `local_node_id = 0` is appended at `offset = current_file_size`.
3. **Premise 3 (Stale Data Corruption)**: When `distributed_search` queries candidate `local_node_id = 0`, `DirectIOManager` seeks to byte 0 instead of byte `current_file_size`. It reads stale data written during previous executions.
4. **Premise 4 (Alignment Breakdown)**: Because previous test runs executed with different vector dimensions (`dim = 32`), byte offset 0 in `shards_db/shard_0.bin` contains misaligned floats. Reading 384 floats from byte 0 yields unnormalized garbage numbers with norm 15.06.
5. **Premise 5 (Search Bridge Disk Leak)**: `search_bridge.py` is invoked as a CLI subprocess on demand. On each call, it instantiates `ShardedIVFHNSW` pointing to `shards_db` and seeds 1,000 vectors. Because mode `"ab"` is used without truncation, every query permanently expands the files on disk by ~1.5 MB without improving search capacity.
6. **Conclusion**: The search service integration and CLI bridge suffer from a critical storage bug that invalidates re-ranking distance calculations and causes unbounded disk consumption.

---

## 3. Findings

### [Critical] Finding 1: `LocalShard` Append Mode (`"ab"`) Corrupts Re-Ranking Offsets and Leaks Disk in `search_bridge.py`
- **What**: `LocalShard._save_to_ssd` writes vectors using append mode (`"ab"`). `LocalShard` does not reset or truncate the shard binary file when initialized with `self.local_count = 0`.
- **Where**:
  - `src/ann_index/two_tier_hnsw.py`, lines 61-65 (`LocalShard.__init__`)
  - `src/ann_index/two_tier_hnsw.py`, line 207 (`_save_to_ssd`)
  - `dashboard/scripts/search_bridge.py`, lines 153-165
  - `dashboard/scripts/search_service.py`, lines 62-77
- **Why**:
  1. `DirectIOManager.get_vector(i)` reads from `i * vector_bytes`. When new vectors are appended to existing files, node 0 is written at the file end while read operations pull from byte 0.
  2. Residual test data with `dim = 32` left a 1,024-byte misalignment in `shards_db/shard_0.bin`, producing impossible L2 distances of 15.0621 on unit vectors.
  3. Every CLI invocation of `search_bridge.py` writes 1,000 vectors (~1.5 MB) to `shards_db/`, causing continuous, unbounded file growth.
- **Suggestion**:
  1. In `LocalShard.__init__`, if initializing a fresh local shard with `self.local_count = 0`, clear or truncate the backing file (`with open(db_path, "wb") as f: pass`) or provide an explicit `clean: bool = True` argument.
  2. When writing in `_save_to_ssd`, seek to the specific vector index offset: `offset = self.local_count * self.io_manager.vector_bytes` or use `io_manager.write_vector`.
  3. Remove or regenerate contaminated `.bin` files in `shards_db/`.
  4. In `search_bridge.py`, ensure temporary index creation does not accumulate disk data across runs.

---

## 4. Verified Claims

| Claim | Method | Result |
|---|---|---|
| Search API routes through `ShardedIVFHNSW.distributed_search` | Inspected call sites in `search_service.py` and `search_bridge.py` | PASS |
| Search API returns `shards_probed` at top level | Inspected return dictionaries and verified with Python test call | PASS |
| Result items contain `shard_id`, `node_id`, `doc_id`, `title`, `preview`, `category`, `distance` | Inspected items and validated all 7 keys on real query output | PASS |
| Standalone `search_service.py` responds to `/health` and `/search` | Launched HTTP daemon on port 5005 and verified HTTP 200 responses | PASS |
| Requirement R3 data directories preserved | Git diff check on `src/crawler/`, `src/quantizer/`, `configs/`, `scripts/` | PASS |
| Safe import guard in `src/ann_data/__init__.py` | Imported `ann_data` without `datasketch` installed | PASS |
| Pipeline configuration loads from `configs/default_pipeline.json` | Loaded via `PipelineConfig.from_json()` | PASS |

---

## 5. Adversarial Stress Tests

### Stress Test 1: Repeated CLI Search Calls (Disk Growth)
- **Scenario**: Invoke `search_bridge.py` repeatedly to simulate incoming user traffic.
- **Expected**: Index storage files remain constant in size or bounded to dataset size.
- **Observed**: `shards_db/shard_0.bin` grew from 3,613,696 bytes to 4,065,280 bytes across runs.
- **Status**: FAIL (Unbounded disk leak).

### Stress Test 2: Unit Vector L2 Distance Re-Ranking
- **Scenario**: Execute search on normalized synthetic vectors.
- **Expected**: Re-ranked L2 distances satisfy $0.0 \le \text{dist} \le 2.0$.
- **Observed**: Candidate results exhibited distances up to 16.2548 due to reading stale 32-dim test vectors from byte offset 0.
- **Status**: FAIL (Broken re-ranking distance).

### Stress Test 3: Clean Directory Router Execution
- **Scenario**: Execute `ShardedIVFHNSW` in an isolated clean temporary directory with 50 normalized vectors.
- **Expected**: Search returns nearest neighbor with distance < 0.2.
- **Observed**: Clean run returned distance = 0.1921.
- **Status**: PASS (Proves algorithmic logic is sound when backing storage is not contaminated).

---

## 6. Caveats

1. `sentence-transformers` and `datasketch` are absent from the conda environment. `MockEmbedder` and import guards function as intended.
2. Dashboard UI rendering in `dashboard/public/` was not reviewed, as it belongs to Milestone 2.

---

## 7. Conclusion

The data pipeline preservation (Requirement R3), safe import guards, and Search API response schema are implemented as specified. However, the Two-Tier SSD storage mechanism in `LocalShard` has an append-mode bug that desynchronizes node indices from disk offsets. This causes stale vector re-ranking (distances exceeding 15.0 on unit vectors) and unbounded disk growth during CLI search bridge executions.

Changes are requested for Worker 1 to address Finding 1 before Milestone 1 can be approved.

---

## 8. Verification Method

To verify the required fixes:
1. Ensure `shards_db/` is clean of misaligned data.
2. Run `python dashboard/scripts/search_bridge.py --query "kiểm tra" --top-k 5`.
3. Check `distance` values for all returned items: all must be $\le 2.0$.
4. Check file size of `shards_db/shard_0.bin` across repeated executions: it must not grow indefinitely.
