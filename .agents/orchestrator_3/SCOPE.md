# Scope: Milestone 4 — 3D UI Restoration, WandB-Style Metrics Dashboard & Pipeline Verification

## Architecture & System Overview
This milestone executes two critical user updates and preserves system integrity:
1. **3D UI Restoration & Full Integration**:
   - Preserves all 5 3D files:
     - `dashboard/public/js/three_engine.js`
     - `dashboard/public/js/three_hnsw_graph.js`
     - `dashboard/public/js/three_pipeline_3d.js`
     - `dashboard/public/js/three_vector_space.js`
     - `dashboard/scripts/dimension_reduction_3d.py`
   - Re-integrates Three.js / OrbitControls / GSAP CDN links in `dashboard/public/index.html`.
   - Restores 3D navigation button `btn-tab-3d-visualizer` and section `<section id="tab-3d-visualizer">`.
   - Restores CSS classes in `dashboard/public/css/custom.css`.
   - Restores API endpoints in `dashboard/server.js`: `/api/vectors-3d` and `/api/hnsw-topology-3d` with an in-memory dynamic fallback generator (240 clustered points and 3-tier HNSW hierarchy) so the 3D scene renders without external dependencies.
   - Restores 3D controller functions in `dashboard/public/js/app.js` (`init3DEngine`, mode switching, camera presets, rotation, HNSW simulation, search sync).
   - In `dashboard/scripts/dimension_reduction_3d.py`, replaces unused `np.memmap` on line 121 with `np.fromfile`.
   - Links search results to 3D via "Xem 3D" buttons on each result card and projects query beacons and laser lines.

2. **WandB-Style Metrics & Charting Dashboard**:
   - Build a comprehensive, detailed metrics collection and charting dashboard, inspired by Weights & Biases (https://wandb.ai/).
   - Add a dedicated navigation tab: "W&B Metrics Studio" (`tab-wandb-metrics` / `btn-tab-wandb-metrics`).
   - WandB-style UI design: dark-mode card grid, run tags, summary KPI stat cards, metric panels with Chart.js:
     1. **Query Latency Over Time**: Multi-line time series chart tracking p50, p95, and p99 latency (ms) per query run.
     2. **Shard Hit Distribution**: Real-time bar chart showing frequency and distribution of hits across shard IDs (Shard #0, #1, #2, etc.).
     3. **Recall @ K & Accuracy Tracking**: Line/area chart comparing exact brute-force vs two-tier quantized HNSW recall over varying top-k and nprobe settings.
     4. **Early Exit Rate & Convergence**: Doughnut / line chart tracking percentage of queries achieving early-exit vs max-hop exploration.
     5. **System Telemetry & Hardware Throughput**: Multi-metric chart for QPS (queries per second), LRU cache hit rate (%), and SSD Direct I/O read throughput (MB/s).
   - Backend endpoint `/api/wandb-metrics` in `dashboard/server.js`:
     - Collects and aggregates real query search telemetry (queries, latency, shards probed, early exit flags).
     - Provides historical runs and rolling metrics buffer.
   - Frontend controller in `dashboard/public/js/wandb_dashboard.js` (or integrated in `charts.js`/`app.js`):
     - Renders responsive Chart.js widgets with dark theme styling (WandB aesthetics).
     - Auto-updates on search queries and supports manual refresh / run simulation.

3. **Search Routing Metrics & UI Cleanliness**:
   - Keep search routing metrics (`shards_probed`, total latency, micro-latency `embed_ms` and `search_ms`, card `Shard #${shardId}` badges, Node IDs) visible and functional in the Search tab (`tab-search`).
   - Zero syntax errors (`node -c` passes on all JavaScript files).

4. **Pipeline Ingestion & Clustering Integrity**:
   - Verify `scripts/run_pipeline.py` maintains vectorized Euclidean IVF K-Means clustering (`train_ivf_kmeans`) and `ShardedIVFHNSW` router integration.
   - Zero `numpy.memmap` or monolithic graph building.

5. **Preserved Data Configurations (Requirement R3)**:
   - Preserve `configs/default_pipeline.json` verbatim (SHA-256: `678C17BDF5013DFE648CB5ED4BEC91CE5B07209C5D75B1E8295D8CF45014EFDF`).
   - Keep `src/ann_data/` and datasets in `data/` untouched.

---

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | 3D File Preservation | Ensure all 5 3D files are present on disk with zero `numpy.memmap` | M4 | Update 1 |
| 2 | Express 3D Endpoints | `/api/vectors-3d` and `/api/hnsw-topology-3d` with fallback data generator | M4 | Update 1 |
| 3 | Frontend 3D Markup & CSS | Three.js CDNs, tab button, section markup, and custom CSS restored in `index.html` & `custom.css` | M4 | Update 1 |
| 4 | Frontend 3D JS Controller Wiring | `init3DEngine()`, mode switcher, camera presets, search sync, and card "Xem 3D" buttons in `app.js` | M4 | Update 1 |
| 5 | WandB Metrics Dashboard UI | WandB-style dashboard tab, KPI cards, and Chart.js panels (latency over time, shard hits, recall, early-exit, system throughput) | M4 | Update 2 |
| 6 | WandB Backend Telemetry API | `/api/wandb-metrics` endpoint in `server.js` storing and serving live query telemetry | M4 | Update 2 |
| 7 | Search Routing Metrics Preservation | Retain `#result-shards-container`, `#result-latency`, `#result-micro-latency`, and result card shard badges | M4 | Original R1/R2 |
| 8 | Pipeline IVF K-Means & Router | Confirm `scripts/run_pipeline.py` initializes `ShardedIVFHNSW` router with zero memmap | M4 | Original R2 |
| 9 | Preserved Configuration (R3) | Maintain `configs/default_pipeline.json` with matching SHA-256 | M4 | Original R3 |
| 10 | Verification Suite | Pass pytest suite (77+ tests), UI render test harness (14+ tests), syntax checks (`node -c`), and pipeline smoke test | M4 | Acceptance Criteria |

---

## File Ownership for Worker
The Worker exclusively owns and may edit:
- `dashboard/server.js` (Add 3D endpoints, `/api/wandb-metrics` telemetry endpoint)
- `dashboard/public/index.html` (Restore 3D tab & markup, add WandB Metrics Studio tab & charts)
- `dashboard/public/css/custom.css` (Add 3D styles & WandB styling tokens)
- `dashboard/public/js/app.js` (Restore 3D controllers, wire search to 3D and WandB metrics)
- `dashboard/public/js/charts.js` or `dashboard/public/js/wandb_dashboard.js` (Implement WandB charting suite)
- `dashboard/scripts/dimension_reduction_3d.py` (Replace `np.memmap` on line 121 with `np.fromfile`)
- `tests/test_ui_render_harness.js` (Add tests for 3D and WandB metrics UI rendering)

Protected Files (DO NOT MODIFY):
- `configs/default_pipeline.json`
- `src/ann_data/*`
- `data/*`
