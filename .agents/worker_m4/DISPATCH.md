# Dispatch: worker_m4

**Working Directory**: f:\ANN\.agents\worker_m4
**Project Root**: f:\ANN
**Authoritative User Request**: f:\ANN\.agents\ORIGINAL_REQUEST.md
**Scope Document**: f:\ANN\.agents\orchestrator_3\SCOPE.md
**Explorer Reports**:
- `f:\ANN\.agents\explorer_m4_1\report.md`
- `f:\ANN\.agents\explorer_m4_2\report.md`
- `f:\ANN\.agents\explorer_m4_3\report.md`

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Permitted File Ownership
You exclusively own and may edit:
- `dashboard/server.js`
- `dashboard/public/index.html`
- `dashboard/public/css/custom.css`
- `dashboard/public/js/app.js`
- `dashboard/public/js/charts.js` (or `dashboard/public/js/wandb_dashboard.js`)
- `dashboard/public/js/three_pipeline_3d.js`
- `dashboard/scripts/dimension_reduction_3d.py`
- `tests/test_ui_render_harness.js`

PROTECTED FILES (DO NOT MODIFY):
- `configs/default_pipeline.json`
- `src/ann_data/*`
- `data/*`

## Tasks:
1. **3D UI Preservation & Integration**:
   - Verify that all 5 3D files (`three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, `dimension_reduction_3d.py`) are preserved on disk.
   - In `dashboard/scripts/dimension_reduction_3d.py`, replace `np.memmap` on line 121 with `np.fromfile`.
   - In `dashboard/public/js/three_pipeline_3d.js`, update node 5 title to "Tier 2: Direct I/O SSD Manager".
   - In `dashboard/server.js`, restore `/api/vectors-3d` and `/api/hnsw-topology-3d` with an in-memory synthetic fallback generator so the 3D scene renders immediately.
   - In `dashboard/public/css/custom.css`, add the 3D CSS classes (`.mode-btn-3d.active`, `#hud-tooltip-3d`, `.threejs-fullscreen`).
   - In `dashboard/public/index.html`, restore Three.js and OrbitControls CDN script tags in `<head>`, add `btn-tab-3d-visualizer` to `<nav>`, restore `<section id="tab-3d-visualizer">`, and add 3D script tags before `</body>`.
   - In `dashboard/public/js/app.js`, restore 3D controllers (`init3DEngine`, mode switching, rotation, camera presets, HNSW simulation, search sync), add "Xem 3D" button to search result cards, and update `switchTab` to initialize/resize 3D scene.

2. **WandB-Style Metrics & Charting Dashboard**:
   - Design and build a comprehensive Weights & Biases (WandB)-style metrics dashboard.
   - In `dashboard/public/index.html`, add a tab button `btn-tab-wandb-metrics` ("W&B Metrics Studio") in the top nav and add `<section id="tab-wandb-metrics">`.
   - Add WandB-style dark theme cards with summary metrics and Chart.js canvas elements:
     - Query Latency Over Time (p50, p95, p99 multi-line time series)
     - Shard Hit Distribution (bar/histogram chart across shards)
     - Recall @ K & Accuracy Curve (line chart)
     - Early-Exit Convergence Rate (percentage doughnut / line chart)
     - System Telemetry (QPS, LRU cache hit rate, Direct I/O throughput)
   - In `dashboard/server.js`, implement `/api/wandb-metrics` returning live and aggregated telemetry data.
   - In `dashboard/public/js/wandb_dashboard.js` (or `charts.js`), implement the charting controllers with Chart.js, rendering high-contrast dark theme charts matching WandB aesthetics.

3. **Preserve Search Routing Metrics**:
   - Ensure `#result-shards-container`, `#result-latency`, `#result-micro-latency`, and individual card shard badges (`Shard #${shardId}`) remain intact and fully functional.

4. **Verification & Testing**:
   - Run `node -c` on all modified JavaScript files.
   - Update and run `node tests/test_ui_render_harness.js` to assert that 3D elements and WandB dashboard elements render properly.
   - Run the Python test suite: `python -m pytest tests/test_two_tier_hnsw.py tests/test_stress_core_index.py tests/test_search_edge_cases.py tests/test_adversarial_lru_concurrency.py tests/test_storage.py tests/test_cleaner.py tests/test_quantizer_pipeline.py -q`.
   - Run pipeline smoke test: `python scripts/run_pipeline.py --sample-size 50 --num-shards 3 --use-mock-embedder --storage-dir tests/temp_verify_shards`.
   - Check `git diff -- configs/default_pipeline.json` to confirm 0 changes.
   - Check `Select-String -Path dashboard/scripts/dimension_reduction_3d.py -Pattern "memmap"` to confirm 0 memmap occurrences.

Write your report to `f:\ANN\.agents\worker_m4\report.md` and deliver `f:\ANN\.agents\worker_m4\handoff.md`.
