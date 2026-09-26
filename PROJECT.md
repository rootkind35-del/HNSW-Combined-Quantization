> **LƯU Ý:** Tài liệu này đã cũ và được thay thế toàn bộ bởi [BAO_CAO_LUAN_VAN_CHIT_TIET.md](BAO_CAO_LUAN_VAN_CHIT_TIET.md). Xin vui lòng tham khảo file báo cáo chính thức để xem kiến trúc Two-Tier HNSW lượng tử hóa SQ8 mới nhất.

# Project: Distributed Sharded IVF-HNSW & Dashboard Optimization

## Architecture
The system transitions from a single-node flat/monolithic search into a high-performance two-tier distributed vector search engine:
1. **Tier 1 (Routing & In-Memory Graph)**:
   - Centroid-based IVF router (`ShardedIVFHNSW`) distributes vectors across $K$ shards using Euclidean clustering and `nprobe` shard selection.
   - Each `LocalShard` maintains an HNSW proximity graph with row-wise SQ8 dynamic quantization (`quantize_adc`) and Asymmetric Distance Computation (`distance_adc`).
   - Adaptive early-exit stops traversal when consecutive candidate evaluations fail to improve the distance by $\epsilon$ within $\tau$ steps.
2. **Tier 2 (Direct I/O SSD Storage & Re-ranking)**:
   - `DirectIOManager` replaces deprecated `numpy.memmap` with raw binary seek/read operations, a multi-threaded `ThreadPoolExecutor(max_workers=16)`, and an application-level `ApplicationLRUCache`.
   - Re-ranks top-$k$ candidates against full-precision float32 vectors fetched directly from disk.
3. **API & Gateway Layer**:
   - Express.js (`dashboard/server.js` on port 3000) acts as the API gateway.
   - Python HTTP microservice (`dashboard/scripts/search_service.py` on port 5005) hosts `ShardedIVFHNSW` in memory and executes `distributed_search()`.
   - CLI bridge (`dashboard/scripts/search_bridge.py`) serves as an automated fallback.
4. **Optimized Dashboard UI**:
   - Clean, high-performance HTML5/Tailwind/Canvas dashboard with all bloated 3D engines and WebGL dependencies removed.
   - Result cards display individual Shard IDs (`Shard #X`), Node IDs, L2 distances, and similarity scores.
   - Global search status displays probed Shards (`[Shard #0, Shard #2, Shard #5]`) and micro-second execution latency.
   - Preserves existing data loading configs and ingestion datasets untouched.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | DirectIOManager & LRUCache | Raw binary seek/read SSD manager with ThreadPoolExecutor and LRU caching, replacing `numpy.memmap` | M1 | Survey (Explorer 1, 2) |
| 2 | ADC Quantization | Per-vector SQ8 dynamic quantization with float16 scale/offset and Asymmetric Distance Computation (`distance_adc`) | M1 | Survey (Explorer 1) |
| 3 | Distributed Sharded IVF-HNSW | `LocalShard` (with `id_map` for global doc ID tracking and early-exit) and `ShardedIVFHNSW` router | M1 | Survey (Explorer 1, 2) |
| 4 | Search API Router Flow | Refactor `search_service.py` and `search_bridge.py` to route queries through `ShardedIVFHNSW.distributed_search`, returning `shard_id` and `shards_probed` | M1 | Survey (Explorer 1, 2) |
| 5 | Preserved Data Pipeline & Import Guard | Retain all ingestion code in `src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/`, `scripts/` intact; guard `datasketch` import in `src/ann_data/__init__.py` | M1 | Survey (Explorer 2) |
| 6 | Delete Bloated 3D Assets | Delete `three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, and `dimension_reduction_3d.py` (~73 KB code, ~700 KB CDN) | M2 | Survey (Explorer 1, 3) |
| 7 | Dashboard HTML & CSS Clean-up | Remove 3D CDN tags, 3D tab markup (388 lines), 3D script tags, and unused 3D CSS styles | M2 | Survey (Explorer 3) |
| 8 | Express Server 3D Route Removal | Remove obsolete `/api/vectors-3d` and `/api/hnsw-topology-3d` endpoints in `server.js` | M2 | Survey (Explorer 3) |
| 9 | UI Shard ID & Latency Presentation | Update `app.js` and `data_product_studio.js` to render Shards Hit badge, result card Shard chips, and execution latency | M2 | Survey (Explorer 3) |
| 10 | UI Performance & Mobile Optimization | Throttle canvas events, add touch listeners, and add horizontal scroll for mobile tab navigation | M2 | Survey (Explorer 3) |
| 11 | End-to-End Verification & Forensic Audit | Verify API stability, router execution, zero `numpy.memmap` in core logic, clean codebase, and non-cheating integrity | M3 | Survey (All) |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M0 | Repository & Branch Survey | Comprehensive survey of branches, core algorithms, backend API, and dashboard bloat | none | DONE |
| M1 | Backend Core & Router Integration | Implement `DirectIOManager`, `hnsw_quantized`, `ShardedIVFHNSW` with `id_map`, wire `search_service.py`/`search_bridge.py`, guard imports, preserve data loaders | M0 | DONE |
| M2 | Dashboard Clean-up & UI Optimization | Delete 3D assets, purge 3D routes/markup/CSS, implement Shard ID and latency UI components, optimize UI performance | M1 | IN_PROGRESS |
| M3 | End-to-End Verification & Forensic Audit | Comprehensive adversarial testing, judge verification against acceptance criteria, forensic non-cheating audit | M1, M2 | PLANNED |

## Interface Contracts

### `src/ann_index/io_manager.py`
- `ApplicationLRUCache(capacity: int = 10000)`
  - `get(key: int) -> np.ndarray | None`
  - `put(key: int, value: np.ndarray) -> None`
- `DirectIOManager(filepath: str, dim: int = 384, cache_capacity: int = 10000)`
  - `get_vector(vector_id: int) -> np.ndarray`
  - `async_read_batch(vector_ids: list[int]) -> dict[int, np.ndarray]`

### `src/ann_index/hnsw_quantized.py`
- `quantize_adc(vectors: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]`
  - Output: `(quantized_vectors: uint8, scale: float16, offset: float16)`
- `distance_adc(query_float32: np.ndarray, q_vector_uint8: np.ndarray, scale: np.float16, offset: np.float16) -> float`
  - Output: Asymmetric Euclidean distance as float
- `exact_distance_l2(query: np.ndarray, vector: np.ndarray) -> float`

### `src/ann_index/two_tier_hnsw.py`
- `LocalShard(shard_id: int, dim: int, max_elements: int, storage_dir: str)`
  - `add_node(global_id: int, vector: np.ndarray, M: int = 16, ef_construction: int = 32) -> None`
  - `_search_local_graph(query: np.ndarray, entry_point: int, ef: int, tau: int = 3, epsilon: float = 1e-4) -> list[tuple[float, int]]`
  - `id_map: dict[int, int]` (maps local `node_id` -> `global_id`)
- `ShardedIVFHNSW(dim: int, num_shards: int, capacity_per_shard: int, storage_dir: str)`
  - `route_and_insert(global_id: int, vector: np.ndarray) -> int`
  - `distributed_search(query: np.ndarray, top_k: int, nprobe: int = 3, re_rank_limit: int = 50) -> tuple[list[tuple[float, int, int]], list[int]]`
    - Returns: `(final_results, target_shard_ids)` where each item in `final_results` is `(exact_dist, global_id, shard_id)`

### Search API (`POST /api/search` via `dashboard/server.js` & `dashboard/scripts/search_service.py`)
- Request: `{ "query": str, "top_k": int, "algorithm": str, "category": str, "hyperparams": dict }`
- Response:
  ```json
  {
    "success": true,
    "data": {
      "query": "string",
      "algorithm": "Two-Tier Quantized HNSW",
      "shards_probed": [0, 2, 5],
      "latency_ms": 1.45,
      "micro_latency": { "embed_ms": 0.2, "search_ms": 1.25 },
      "results_count": 5,
      "results": [
        {
          "rank": 1,
          "doc_id": "doc_123",
          "shard_id": 2,
          "node_id": 42,
          "title": "Title",
          "preview": "Snippet...",
          "category": "News",
          "distance": 0.2814,
          "similarity_score": 0.852
        }
      ]
    }
  }
  ```

## Code Layout
```
f:\ANN/
â”œâ”€â”€ configs/
â”‚   â””â”€â”€ default_pipeline.json          # Untouched (R3)
â”œâ”€â”€ data/                              # Untouched (R3)
â”œâ”€â”€ dashboard/
â”‚   â”œâ”€â”€ package.json
â”‚   â”œâ”€â”€ server.js                      # Updated search routes & removed 3D endpoints
â”‚   â”œâ”€â”€ public/
â”‚   â”‚   â”œâ”€â”€ index.html                 # Removed 3D markup, added Shard ID display
â”‚   â”‚   â”œâ”€â”€ css/
â”‚   â”‚   â”‚   â”œâ”€â”€ custom.css             # Removed 3D styles
â”‚   â”‚   â”‚   â””â”€â”€ data_product.css
â”‚   â”‚   â””â”€â”€ js/
â”‚   â”‚       â”œâ”€â”€ app.js                 # Removed 3D controllers, renders Shard ID & latency
â”‚   â”‚       â”œâ”€â”€ data_product_studio.js # Optimized canvas, removed 3D calls
â”‚   â”‚       â”œâ”€â”€ architecture.js
â”‚   â”‚       â””â”€â”€ charts.js              # Visibility-aware polling
â”‚   â””â”€â”€ scripts/
â”‚       â”œâ”€â”€ search_service.py          # Hosts ShardedIVFHNSW router
â”‚       â”œâ”€â”€ search_bridge.py           # CLI fallback with ShardedIVFHNSW router
â”‚       â””â”€â”€ build_search_cache.py
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ ann_data/                      # Untouched ingestion logic (R3), guarded import
â”‚   â”œâ”€â”€ ann_index/
â”‚   â”‚   â”œâ”€â”€ io_manager.py              # NEW: DirectIOManager & ApplicationLRUCache
â”‚   â”‚   â”œâ”€â”€ hnsw_quantized.py          # NEW: quantize_adc & distance_adc
â”‚   â”‚   â””â”€â”€ two_tier_hnsw.py           # NEW: ShardedIVFHNSW & LocalShard with id_map
â”‚   â”œâ”€â”€ crawler/                       # Untouched (R3)
â”‚   â””â”€â”€ quantizer/                     # Untouched (R3)
â””â”€â”€ tests/                             # Unit, integration, and E2E tests
```

