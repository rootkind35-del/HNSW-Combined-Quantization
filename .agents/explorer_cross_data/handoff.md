# Investigation Report: Data Preservation (R3) & End-to-End Acceptance

## 1. Observation

### 1.1 Ingestion Configuration & Data Structures
- **`configs/default_pipeline.json`**:
  - File size: 403 bytes.
  - SHA-256 hash: `678C17BDF5013DFE648CB5ED4BEC91CE5B07209C5D75B1E8295D8CF45014EFDF`.
  - Contents:
    ```json
    {
      "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
      "embedding_dim": 384,
      "batch_size": 2048,
      "max_records": 10000000,
      "output_memmap_path": "data/processed/vectors_10m.dat",
      "dtype": "float32",
      "minhash_threshold": 0.8,
      "minhash_num_perm": 128,
      "strip_html_tags": true,
      "normalize_unicode_nfc": true,
      "remove_urls": true,
      "lowercase_tokens_for_dedup": true
    }
    ```
- **`data/` Directory Structure**:
  - `data/README.md`: Explains external storage of the 31.33M vector corpora (>20 GB) hosted on Google Drive.
  - `data/processed/`: Contains `README.md` and `query_logs/` (directory for JSON query execution traces). Destination for `search_index_cache.npz` and `search_index_metadata.json`.
  - `data/raw/`: Contains `README.md` and `benchmarks/` (destination for `.fvecs` / `.ivecs` benchmarks).
  - `data/experiments/`: Contains `scale_stress_results.json` (2,145 bytes) and `scale_stress_summary.md` (1,910 bytes).
- **`src/ann_data/` Ingestion Components**:
  - `config.py` (lines 9-63): Defines `PipelineConfig` dataclass matching `default_pipeline.json` with helper methods `from_json()`, `save_json()`, `from_dict()`, and `to_dict()`.
  - `pipeline.py` (lines 14-155): Defines `DataPipeline` managing the streaming pipeline: `TextCleaner` -> `PyViTokenizer` -> `StreamDeduplicator` -> `SentenceTransformerEmbedder` / `BatchEmbedder` -> `MemmapStorage`.
  - `storage.py` (lines 14-118): Defines `MemmapStorage` wrapping `numpy.memmap` for append-only streaming writes to binary `.dat` vector files.
  - `loaders/`:
    - `base.py`: Defines `BaseDataLoader` interface with `stream(limit=None) -> Generator[Tuple[str, str], None, None]`.
    - `news_crawler.py`: RSS crawler yielding `(doc_id, text)`.
    - `hf_loader.py`: HuggingFace streaming loader.
    - `benchmark_loader.py`: Parsers for SIFT `.fvecs` and `.ivecs` formats.

### 1.2 Git Status & Milestone 1 Verification
- Command: `git diff configs/ data/`
  - Output: Empty (0 lines changed).
- Command: `git diff src/ann_data/`
  - Output: Exactly one diff in `src/ann_data/__init__.py`:
    ```diff
    diff --git a/src/ann_data/__init__.py b/src/ann_data/__init__.py
    index 0fcaa07..92ed989 100644
    --- a/src/ann_data/__init__.py
    +++ b/src/ann_data/__init__.py
    @@ -2,10 +2,16 @@
     
     from ann_data.cleaner import TextCleaner, clean_text
     from ann_data.config import PipelineConfig
    -from ann_data.deduplicator import StreamDeduplicator
    +try:
    +    from ann_data.deduplicator import StreamDeduplicator
    +except (ImportError, ModuleNotFoundError):
    +    StreamDeduplicator = None
     from ann_data.embedder import BatchEmbedder, BaseEmbedder, MockEmbedder, SentenceTransformerEmbedder
     from ann_data.loaders import BaseDataLoader, HuggingFaceLoader, NewsRssCrawler
    -from ann_data.pipeline import DataPipeline
    +try:
    +    from ann_data.pipeline import DataPipeline
    +except (ImportError, ModuleNotFoundError):
    +    DataPipeline = None
    ```
  - This import guard prevents runtime failures when `datasketch` is omitted in lean execution environments. No internal logic, schemas, or configs were altered.

### 1.3 Inspection of `search_service.py` and `search_bridge.py`
- **Initialization of `ShardedIVFHNSW`**:
  - `dashboard/scripts/search_service.py` (lines 61-78):
    ```python
    storage_dir = os.path.join(BASE_DIR, "shards_db")
    dim = G_VECTORS.shape[1]
    num_shards = 5
    capacity = max(len(G_VECTORS), 1000)
    G_ROUTER = ShardedIVFHNSW(
        dim=dim,
        num_shards=num_shards,
        capacity_per_shard=capacity,
        storage_dir=storage_dir,
        clean_storage=True,
    )
    seed_count = min(len(G_VECTORS), 1000)
    for i in range(seed_count):
        G_ROUTER.route_and_insert(global_id=i, vector=G_VECTORS[i])
    ```
  - `dashboard/scripts/search_bridge.py` (lines 153-166): Uses identical logic to instantiate `ShardedIVFHNSW` with 5 shards and seed up to 1,000 vectors from the loaded dataset.
  - Shard binaries are written to `shards_db/shard_{0..4}.bin` using Direct IO seek/write in `LocalShard._save_to_ssd()`.
- **Sample Data and Fallbacks**:
  - Both scripts call `load_dataset_and_metadata()` in `search_bridge.py` (lines 39-86).
  - Priority 1: Reads `data/processed/search_index_cache.npz` and `data/processed/search_index_metadata.json`.
  - Priority 2: If files do not exist, triggers `dashboard/scripts/build_search_cache.py`.
  - Priority 3 (Synthetic Fallback): When source corpora are absent, generates 100 synthetic vectors (`dim=384`, seed=42, L2-normalized) with synthetic metadata entries (`doc_id="synthetic_i"`).
  - Sentence Transformer Fallback: If `sentence_transformers` is not installed, `SentenceTransformerEmbedder` invokes `MockEmbedder(dim=384)` with deterministic MD5 hashing (`tests/test_two_tier_hnsw.py` lines logged: `[WARNING] [SentenceTransformerEmbedder]: Không thể nạp sentence_transformers... Tự động kích hoạt cơ chế dự phòng MockEmbedder`).
- **Search Response Formatting**:
  - `perform_search()` in `search_service.py` calls:
    `router_results, shards_probed = G_ROUTER.distributed_search(query=query_vec, top_k=search_k, nprobe=3, re_rank_limit=max(min_rerank_k, search_k), return_shards=True)`
  - Each item in `router_results` is a 3-tuple `(exact_dist, global_id, shard_id)`.
  - JSON payload returned:
    - Root fields: `query`, `query_3d`, `algorithm`, `algorithm_key`, `category_filter`, `shards_probed`, `shards_hit`, `hyperparams`, `dataset_source`, `dataset_size`, `latency_ms`, `micro_latency`, `qps`, `results_count`, `results`.
    - Candidate items in `results`: `rank`, `index`, `doc_id`, `shard_id`, `node_id`, `title`, `preview`, `category`, `source`, `distance`, `similarity_score`, `coords_3d`.
  - `dashboard/server.js` (lines 385-412): Handles `POST /api/search`, passes parameters to Python, ensures `shards_probed` exists and every candidate item has `shard_id`, returning `{ success: true, data }`.
  - `dashboard/public/js/app.js` (lines 388-398, 448-450): Reads `data.shards_probed` into `#result-shards-list` (rendered as `[Shard #0, Shard #2, Shard #4]`) and renders a `Shard #${item.shard_id}` chip on each result card.

---

## 2. Logic Chain

1. **R3 Data Ingestion Integrity**:
   - Observation: `git diff configs/ data/` is empty; `git diff src/ann_data/` contains only an import guard.
   - Inference: Milestone 1 preserved the entire ingestion configuration. The data loading interfaces and schema remain intact.
2. **Boundary Preservation During Milestone 2 & Milestone 3**:
   - Observation: `configs/default_pipeline.json` defines constants used across multiple scripts (`scripts/run_pipeline.py`, `src/ann_data/pipeline.py`).
   - Inference: Modifying `default_pipeline.json` risks breaking ingestion reproducibility. Milestone 2 (UI clean-up) has no reason to touch `configs/`, `data/`, or `src/ann_data/`. Milestone 3 (`scripts/run_pipeline.py` optimization) only needs to connect the output of pipeline vector generation to `ShardedIVFHNSW.route_and_insert()`.
3. **Search Service Architecture**:
   - Observation: `search_service.py` and `search_bridge.py` construct an in-memory `ShardedIVFHNSW` router instance and index vectors on startup.
   - Inference: The backend already operates on the distributed sharding router. The UI and API contracts match this model.

---

## 3. Caveats

1. **Large External Corpora**: The full 31.33M dataset requires >20 GB of disk space and is hosted externally on Google Drive. Acceptance tests must verify that automated fallbacks (synthetic cache generation and MockEmbedder) function when external data is not downloaded.
2. **`datasketch` Dependency**: `StreamDeduplicator` requires `datasketch`. If testing full `DataPipeline.process_stream` with deduplication enabled, `datasketch` must be installed; otherwise, unit tests relying on deduplication will fail.

---

## 4. Conclusion

- **Requirement R3 Status**: Fully compliant. No changes were made to dataset layouts or ingestion configurations in Milestone 1, except for an import guard in `src/ann_data/__init__.py`.
- **Router Integration Status**: `search_service.py` and `search_bridge.py` initialize `ShardedIVFHNSW` with 5 shards and direct SSD backing in `shards_db/`. Response schemas contain `shards_probed` and `shard_id`.
- **Preservation Rules for M2 & M3**:
  1. `configs/default_pipeline.json` must remain byte-identical (SHA-256: `678C17BDF5013DFE648CB5ED4BEC91CE5B07209C5D75B1E8295D8CF45014EFDF`).
  2. `src/ann_data/` files must remain unmodified.
  3. `scripts/run_pipeline.py` in M3 must retain argument `--config configs/default_pipeline.json` and ingest data via `PipelineConfig`.

---

## 5. Verification Method

### 5.1 Milestone 2 (Dashboard Clean-up & UI Optimization) Acceptance Criteria

| ID | Criterion | Verification Command / Check |
|---|---|---|
| **M2-AC1** | 3D Assets Purged | Verify deleted files do not exist: `three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, `dimension_reduction_3d.py`. |
| **M2-AC2** | Redundant UI Assets Removed | Verify unused 3D markup, `data_product_studio.js`, and `data_product.css` are removed or cleanly decoupled. Check `dashboard/public/index.html` contains no broken `<script>` or `<link>` tags. |
| **M2-AC3** | Express Server Clean-up | `dashboard/server.js` removes obsolete endpoints (`/api/vectors-3d`, `/api/hnsw-topology-3d`). Returns 404 for removed endpoints. |
| **M2-AC4** | UI Shard & Latency Rendering | In `dashboard/public/js/app.js` and `index.html`, verify `#result-shards-container` renders probed shards and each result card renders `Shard #X` badge and latency in ms. |
| **M2-AC5** | API Stability | Run `python -c "import sys; sys.path.insert(0, 'src'); import unittest; suite = unittest.defaultTestLoader.discover('tests', pattern='test_search_edge_cases.py'); res = unittest.TextTestRunner().run(suite); sys.exit(0 if res.wasSuccessful() else 1)"`. All 28 tests must pass. |

### 5.2 Milestone 3 (Pipeline Optimization) Acceptance Criteria

| ID | Criterion | Verification Command / Check |
|---|---|---|
| **M3-AC1** | Router-based Pipeline | `scripts/run_pipeline.py` imports and initializes `ShardedIVFHNSW`. Inserts generated or loaded vectors via `route_and_insert()`. |
| **M3-AC2** | Zero Monolithic Graph / Zero Memmap in Core Indexing | Grep check confirms zero occurrences of `np.memmap` used for index graph structures or distance calculations in `scripts/run_pipeline.py`. |
| **M3-AC3** | Ingestion Compatibility (R3) | `scripts/run_pipeline.py` accepts `--config configs/default_pipeline.json`. `configs/default_pipeline.json` hash matches `678C17BDF5013DFE648CB5ED4BEC91CE5B07209C5D75B1E8295D8CF45014EFDF`. |
| **M3-AC4** | Pipeline Execution Test | Run `python scripts/run_pipeline.py --sample-size 50 --use-mock-embedder` exits 0 and populates shards in `shards_db/`. |

### 5.3 Final Verification Gate & Forensic Audit Criteria

| ID | Criterion | Check Description |
|---|---|---|
| **GATE-1** | Real Algorithmic Execution | Verify `distributed_search` performs real calculation; verify candidates have valid Euclidean distances and `shard_id in shards_probed`. |
| **GATE-2** | No Stubs or Mock Bypasses | Ensure production paths do not bypass index routing with hardcoded result arrays. |
| **GATE-3** | Unit Test Suite Green | Execute `test_two_tier_hnsw.py`, `test_search_edge_cases.py`, and `test_stress_core_index.py`. 100% pass rate. |
| **GATE-4** | R3 Hash Invariance | Verify `configs/default_pipeline.json` hash matches expected SHA-256. |

### Invalidation Conditions
- Any modification to `configs/default_pipeline.json` invalidates R3 compliance.
- Any change to `src/ann_data/` class contracts invalidates backward compatibility.
- Any failure in `test_search_edge_cases.py` or `test_two_tier_hnsw.py` blocks gate passage.
