# Handoff Report — Explorer 2: Backend API & Data Pipeline

## 1. Observation

### 1.1 Backend Server Architecture and Entry Points
- **Web Server / Gateway**: `dashboard/server.js` (Node.js Express application).
  - Port: reads `process.env.PORT || 3000` (`dashboard/server.js:15`).
  - Middleware: CORS (`dashboard/server.js:18`), JSON body parser with 10MB limit (`dashboard/server.js:19`), static file serving from `dashboard/public` (`dashboard/server.js:20`).
  - Startup Hook: `app.listen(PORT, ...)` (`dashboard/server.js:688-691`) executes `ensureSearchService()`.
  - Process Management: `ensureSearchService()` (`dashboard/server.js:671-686`) sends an HTTP GET request to `http://127.0.0.1:5005/health`. If the connection is refused, it spawns `python dashboard/scripts/search_service.py 5005` via `child_process.spawn`.
- **Search Microservice Daemon**: `dashboard/scripts/search_service.py`.
  - Framework: Python standard library `http.server.HTTPServer` with custom `BaseHTTPRequestHandler` (`dashboard/scripts/search_service.py:12, 202-256`).
  - Port: default 5005 (`dashboard/scripts/search_service.py:271`).
  - Initialization: `initialize_service()` (`dashboard/scripts/search_service.py:45-63`) calls `load_dataset_and_metadata()` and initializes `SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2")`.
- **CLI Fallback**: `dashboard/scripts/search_bridge.py`.
  - In `dashboard/server.js:338-419`, `runSearchBridge()` queries `http://127.0.0.1:5005/search` with a 3000ms timeout.
  - On connection timeout or failure, `runSearchBridge()` invokes `execFile('python', ['dashboard/scripts/search_bridge.py', ...])`.

### 1.2 Search API Endpoints & Request/Response Contracts
- **Primary Search Endpoint**: `POST /api/search` (`dashboard/server.js:422-434`).
  - Request Payload:
    ```json
    {
      "query": "string (required)",
      "top_k": 5,
      "algorithm": "two_tier",
      "category": "Tất cả",
      "hyperparams": {
        "m": 16,
        "ef_search": 30,
        "tau": 3,
        "epsilon": 0.0001,
        "min_rerank_k": 20
      }
    }
    ```
  - Response Schema:
    ```json
    {
      "success": true,
      "data": {
        "query": "text",
        "query_3d": { "x": 0.0, "y": 0.0, "z": 0.0 },
        "algorithm": "Two-Tier Quantized HNSW (M=16, ef=30, τ=3)",
        "algorithm_key": "two_tier",
        "category_filter": "Tất cả",
        "hyperparams": { "m": 16, "ef_search": 30, "tau": 3, "epsilon": 0.0001, "min_rerank_k": 20 },
        "dataset_source": "Siêu kho 31.33M ...",
        "dataset_size": 5000,
        "corpus_total_vectors": 31331931,
        "dimension": 384,
        "latency_ms": 2.37,
        "micro_latency": { "embed_ms": 0.18, "search_ms": 1.82 },
        "qps": 365.0,
        "ram_saving_percent": 75.0,
        "visited_nodes_count": 72,
        "early_exit_triggered": true,
        "top_similarity_pct": 82.5,
        "min_distance": 0.35,
        "results_count": 5,
        "results": [
          {
            "rank": 1,
            "index": 42,
            "doc_id": "doc_42",
            "title": "Title text",
            "preview": "Preview snippet",
            "category": "Kinh doanh & Tài chính",
            "source": "Combined",
            "token_count": 28,
            "distance": 0.35,
            "similarity_score": 0.825,
            "coords_3d": { "x": 0.1, "y": -0.2, "z": 0.05 }
          }
        ]
      }
    }
    ```
- **Upload Search Endpoint**: `POST /api/upload-search` (`dashboard/server.js:437-455`). Slices first 400 characters of uploaded text and delegates to `runSearchBridge()`.
- **Current Execution Gap in Search Bridge/Service**:
  - In `dashboard/scripts/search_service.py:88` and `dashboard/scripts/search_bridge.py:152`:
    `cosine_sims = np.dot(vectors, query_vec)`
    The current search implementations execute a flat matrix dot product against 5,000 cached vectors in RAM, while `visited_nodes_count` and `early_exit_triggered` are simulated with heuristics rather than executing actual graph traversal.

### 1.3 Memory Mechanisms and `numpy.memmap` Usage
- **Main Branch Index (`src/ann_index/two_tier_hnsw.py`)**:
  - Line 52: `self.raw_vectors: Optional[np.ndarray] = None # Dữ liệu Tier 2 trên đĩa SSD (float32, np.memmap)`
  - Line 73: `self.raw_vectors = np.ascontiguousarray(vectors, dtype=np.float32)`
  - Line 204: `cand_raw = self.raw_vectors[candidate_indices]` relies on slicing mapped arrays directly.
  - Other modules utilizing `numpy.memmap`: `src/ann_data/storage.py:50`, `src/quantizer/storage.py:41`, `src/quantizer/unified_corpus.py:43`.
- **Update Branch Distributed Core Logic**:
  - `update:two_tier_hnsw.py`: Implements `LocalShard` and `ShardedIVFHNSW`.
  - `update:hnsw_quantized.py`: Implements `quantize_adc(vectors)` and `distance_adc(query_float32, q_vector_uint8, scale, offset)` without `numpy.memmap`.
  - `update:io_manager.py`: Implements `DirectIOManager` and `ApplicationLRUCache`. It bypasses `numpy.memmap` using binary file seek and read (`f.seek(vector_id * self.vector_bytes)`, `f.read(self.vector_bytes)` in `io_manager.py:38-44`), wrapped with an LRU cache (`ApplicationLRUCache:6-23`) and threaded asynchronous batch reading (`async_read_batch:58-69`).

### 1.4 Data Pipeline and Dataset Configuration (Requirement R3)
- **Files and Directories Responsible for Data Ingestion on `main`**:
  - Configuration: `configs/default_pipeline.json`, `src/ann_data/config.py`, `src/crawler/config.py`.
  - Ingestion Loaders: `src/ann_data/loaders/base.py`, `src/ann_data/loaders/hf_loader.py`, `src/ann_data/loaders/news_crawler.py`, `src/ann_data/loaders/benchmark_loader.py`.
  - Preprocessing & Embedding: `src/ann_data/cleaner.py`, `src/ann_data/tokenizer.py`, `src/ann_data/deduplicator.py`, `src/ann_data/embedder.py`, `src/ann_data/pipeline.py`.
  - Crawler Components: `src/crawler/sources/rss_crawler.py`, `src/crawler/sources/legal_crawler.py`, `src/crawler/sources/hf_streamer.py`, `src/crawler/sources/drive_downloader.py`, `src/crawler/storage/shard_writer.py`.
  - Quantization Pipeline: `src/quantizer/sq8.py`, `src/quantizer/chunker.py`, `src/quantizer/pipeline.py`, `src/quantizer/storage.py`, `src/quantizer/unified_corpus.py`.
  - Execution Scripts: `scripts/run_crawler.py`, `scripts/run_wiki_crawler.py`, `scripts/run_pipeline.py`, `scripts/run_quantization.py`, `scripts/run_wiki_quantization.py`, `scripts/merge_quantized_corpora.py`, `scripts/download_standard_datasets.py`, `scripts/download_and_save_raw_data.py`.
  - Dataset Directory Structure: `data/raw/`, `data/processed/`, `data/experiments/`.
- **Diff Analysis of `update` Branch Commit `7e745d4b6fd17dc9c1dd0ffd955ff6cea390dfdc`**:
  - The author deleted all 165 project files (`src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/`, `scripts/`, `dashboard/`) and replaced them with standalone files in repository root (`two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`, `data_pipeline.py`).
  - Requirement R3 explicitly forbids this deletion. The existing data ingestion pipeline and dataset configuration must be preserved.

### 1.5 Environment and Dependency State
- Execution command `python -m unittest tests/test_cleaner.py` and `python -s -m pytest` fail with:
  `ModuleNotFoundError: No module named 'datasketch'`
  Root cause: `src/ann_data/__init__.py:5` executes `from ann_data.deduplicator import StreamDeduplicator`, which unconditionally executes `from datasketch import MinHash, MinHashLSH` in `src/ann_data/deduplicator.py:4`. Because `datasketch` is not installed in the active environment, importing `ann_data` breaks modules that import `ann_data.utils`.
- Node.js dependencies: `dashboard/node_modules` is not yet installed in `f:\ANN\dashboard`. `dashboard/package.json` contains `express: ^4.21.2` and `cors: ^2.8.5`.

---

## 2. Logic Chain

1. **Backend Integration Logic**:
   - The user requires the Search API on `main` to transition from the current flat search to the distributed `ShardedIVFHNSW` router-based execution flow.
   - `two_tier_hnsw.py`, `hnsw_quantized.py`, and `io_manager.py` on the `update` branch implement this exact logic:
     - `ShardedIVFHNSW` clusters nodes into $K$ shards using centroids.
     - Query execution determines the closest $nprobe$ centroids (`_get_nearest_shards`), queries local shard graphs (`_search_local_graph`) using early-exit and ADC distance (`distance_adc`), fetches raw vectors from SSD via `DirectIOManager.async_read_batch`, and re-ranks top candidates.
   - Therefore, merging these three modules into `src/ann_index/` (and exposing them at standard import paths) provides the exact algorithm needed by the Search API.

2. **Index Initialization & ID Mapping Logic**:
   - In `update:two_tier_hnsw.py:67`, `LocalShard.add_node(global_id: int, vector: np.ndarray)` accepts `global_id`, but stores only local index `idx = self.local_count`.
   - When `distributed_search` returns `(exact_dist, node_id, sid)`, `node_id` is local to `sid`.
   - Without mapping `(sid, node_id) -> global_id`, the search API cannot look up document metadata (`title`, `preview`, `category`).
   - Therefore, `LocalShard` must maintain an internal mapping table (`self.id_map[idx] = global_id`), and `distributed_search` must propagate `global_id` to the result tuple.

3. **Search API Contract Preservation & UI Support Logic**:
   - Requirement R2 specifies that the UI must display the specific Shard IDs hit and execution latency.
   - In `distributed_search`, the selected shards are returned in `target_shard_ids`, and each candidate tuple includes `sid`.
   - Modifying the output of `perform_search` in `search_service.py` and `search_bridge.py` to inject `"shard_id": sid` into each item of `results` and `"shards_hit": target_shard_ids` into the response object satisfies Requirement R2 while maintaining full backwards compatibility with existing UI fields.

4. **Preserving Data Configuration (Requirement R3) Logic**:
   - The `update` branch committed a destructive purge of `src/ann_data`, `src/crawler`, and `configs/`.
   - Requirement R3 explicitly states: *"Do not alter the existing dataset structure or data loading configuration. The data ingestion pipeline should remain as-is, ready for the user to load their data later."*
   - Therefore, all files in `src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/default_pipeline.json`, and `scripts/` must be retained on `main`.

5. **Elimination of `numpy.memmap` in Core Algorithm Logic**:
   - Acceptance criteria require eliminating `numpy.memmap` from core algorithm files.
   - `update:io_manager.py` (`DirectIOManager`) replaces `numpy.memmap` with random file reads (`f.seek` and `f.read`) plus `ApplicationLRUCache`.
   - Replacing the memmap access in `src/ann_index/two_tier_hnsw.py` with `DirectIOManager` fulfills this criterion.

---

## 3. Caveats

1. **Pure Python Index Build Speed**:
   - In `two_tier_hnsw.py`, building HNSW graphs sequentially in pure Python via `add_node` takes measurable time if indexing thousands of vectors synchronously on cold start.
   - The service should either initialize with pre-seeded shards (e.g. from `shards_db/` if present) or index a moderate initial dataset slice (e.g. 500-1000 items) and cache shard structures to disk to keep startup latency under 1 second.
2. **Missing Optional Dependencies in Environment**:
   - `datasketch` and `sentence_transformers` are not installed in `F:\anaconda3`.
   - `src/ann_data/__init__.py` must guard imports of `StreamDeduplicator` so importing `ann_data` or `ann_index` does not crash during automated testing or evaluation.
3. **Node.js Dependencies**:
   - `dashboard/node_modules` does not exist in the working copy. `npm install` inside `dashboard/` is required if running `node server.js` directly, though Python search tests can be verified independently via unit tests and Python HTTP requests.

---

## 4. Conclusion

1. **Backend Server & Dispatch Architecture**:
   - The system uses a two-tier backend: an Express.js gateway (`dashboard/server.js` on port 3000) that routes search queries to a resident Python HTTP microservice (`dashboard/scripts/search_service.py` on port 5005), falling back to CLI execution (`dashboard/scripts/search_bridge.py`).
2. **Core Algorithm Migration Target**:
   - The core logic from `update` (`hnsw_quantized.py`, `io_manager.py`, `two_tier_hnsw.py`) must be merged into `src/ann_index/` (and mirrored at root/import aliases).
   - In `two_tier_hnsw.py`, `LocalShard` must be augmented to store `self.id_map` for `global_id` tracking.
   - `ShardedIVFHNSW.distributed_search` must return `(exact_dist, global_id, sid)` to link candidates with dataset metadata.
3. **Search API Dispatch Updates**:
   - Both `dashboard/scripts/search_service.py` and `dashboard/scripts/search_bridge.py` must replace the flat `np.dot` calculation with `ShardedIVFHNSW.distributed_search`.
   - The response payload must maintain existing fields while populating `shard_id` in each result record and `shards_hit` in top-level metadata.
4. **Preserved Assets (Requirement R3)**:
   - All modules in `src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/default_pipeline.json`, and ingestion scripts in `scripts/` must remain untouched in structure and behavior.
   - `src/ann_data/__init__.py` and `src/ann_data/deduplicator.py` require a safe import guard for `datasketch` to prevent collection failures.

---

## 5. Verification Method

### 5.1 Verifying ShardedIVFHNSW and Core Algorithm
Run the core algorithm test without relying on `numpy.memmap`:
```powershell
$env:PYTHONPATH = "src"
python -c "from ann_index.two_tier_hnsw import ShardedIVFHNSW; import numpy as np; router = ShardedIVFHNSW(dim=64, num_shards=3, capacity_per_shard=100, storage_dir='shards_db'); router.route_and_insert(global_id=1, vector=np.random.randn(64).astype(np.float32)); res = router.distributed_search(np.random.randn(64).astype(np.float32), top_k=1, nprobe=2); print('Router search success:', res)"
```
Expected output: successful execution returning list of `(distance, id, shard_id)` without runtime errors.

### 5.2 Verifying Python Search Service & Sharded Execution
Test the search service handler directly:
```powershell
python -c "import sys; sys.path.insert(0, 'src'); sys.path.insert(0, 'dashboard/scripts'); from search_service import perform_search; res = perform_search('tìm kiếm văn bản', top_k=3); print('Results count:', len(res['results'])); print('Shard IDs:', [r.get('shard_id') for r in res['results']])"
```
Expected output: `results` contains valid matches, each result record contains a valid `shard_id`, and no `numpy.memmap` deprecation or crash occurs.

### 5.3 Verifying Data Loading Configuration Integrity (Requirement R3)
Verify that data ingestion configs and pipeline loaders remain loadable and unchanged:
```powershell
python -c "from ann_data.config import PipelineConfig; cfg = PipelineConfig.from_json('configs/default_pipeline.json'); print('Pipeline config loaded:', cfg.model_name, cfg.embedding_dim)"
```
Expected output: `Pipeline config loaded: paraphrase-multilingual-MiniLM-L12-v2 384`.

### 5.4 Invalidation Conditions
- Any occurrence of `numpy.memmap` inside `LocalShard` or `ShardedIVFHNSW`.
- Missing `shard_id` in search result items.
- Modifying or deleting files in `src/ann_data/`, `src/crawler/`, `src/quantizer/`, or `configs/default_pipeline.json`.
- Search endpoint throwing unhandled 500 errors when queried.
