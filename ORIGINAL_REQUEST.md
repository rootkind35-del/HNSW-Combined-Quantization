# Original User Request

## Initial Request — 2026-09-21T03:41:12Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Refactor and optimize the existing Vector Search dashboard and backend pipeline on the `main` branch to integrate the new Distributed Sharded IVF-HNSW core logic (from the `update` branch). Clean up all redundant resources, optimize the codebase for performance, and ensure the UI reflects the new distributed architecture while keeping the original data loading configuration intact.

Working directory: f:\ANN
Integrity mode: demo

## Requirements

### R1. HNSW Core Integration
Merge the distributed sharding logic (`two_tier_hnsw.py`), ADC quantization (`hnsw_quantized.py`), and direct I/O memory management (`io_manager.py`) into the main project structure. Ensure the Search API uses the new Router-based execution flow.

### R2. Dashboard Clean-up & UI Optimization
Remove all bloated, unused resources (e.g., heavy CSS/JS, unused 3D engines) from the `dashboard/` directory. Optimize the remaining UI code to cleanly display search results, including the specific Shard IDs hit and the execution latency.

### R3. Preserved Data Configuration
Do not alter the existing dataset structure or data loading configuration. The data ingestion pipeline should remain as-is, ready for the user to load their data later.

## Acceptance Criteria

### Backend & API Stability
- [ ] An independent judge agent verifies that the backend API successfully loads the `ShardedIVFHNSW` router and exposes a search endpoint without throwing runtime errors.
- [ ] The core algorithm files successfully implement early-exit and ADC quantization without relying on the deprecated `numpy.memmap`.

### Codebase Cleanliness
- [ ] An independent judge agent verifies that redundant files (e.g., unused 3D visualizers or legacy scripts in `dashboard/public/js`) have been fully deleted.
- [ ] The dashboard source code is reviewed for performance bottlenecks and passes the judge's code quality rubric.

## Follow-up — 2026-09-21T05:47:25Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Continue the refactoring of the Vector Search project on the `main` branch. Milestone 1 (Backend Core Integration) is successfully completed. The goal now is to execute Milestone 2 (Dashboard Clean-up & UI Optimization) and Milestone 3 (Pipeline Optimization) to fully align the UI and execution scripts with the new Distributed Sharded IVF-HNSW logic.

Working directory: f:\ANN
Integrity mode: demo

## Requirements

### R1. Dashboard Clean-up & UI Optimization
Remove all bloated, unused resources from `dashboard/` (e.g., benchmark scripts not needed for the production API, heavy unused CSS/JS like data_product_studio). Optimize the remaining UI code (like `app.js`, `index.html`) to cleanly display search results, specifically including the Shard IDs hit, shards probed, and the execution latency metrics returned by the new search API.

### R2. Pipeline Optimization
Configure `scripts/run_pipeline.py` to use the new IVF K-Means clustering logic from the updated backend, replacing any old monolithic graph building logic. Ensure it works seamlessly with the new `ShardedIVFHNSW` router.

### R3. Preserved Data Configuration
Do not alter the existing dataset structure or data loading configuration. The data ingestion pipeline should remain as-is, ready for future data loading.

## Acceptance Criteria

### Codebase Cleanliness & UI Functionality
- [ ] An independent judge agent verifies that redundant UI and dashboard script files have been successfully deleted without breaking the core frontend.
- [ ] The dashboard UI is reviewed, and the judge verifies that Shard routing metrics and execution latency are properly wired and displayed on the frontend.

### Pipeline Execution
- [ ] An independent judge agent verifies that `scripts/run_pipeline.py` initializes the `ShardedIVFHNSW` router correctly and contains no legacy `memmap` or monolithic graph logic.

## Follow-up — 2026-09-21T16:00:55Z

# Teamwork Project Prompt — Draft

> Status: Launched
> Goal: Craft prompt → get user approval → delegate to teamwork_preview
> Requested team: [none — teamwork routes from the description]

Finalize and audit the refactored Vector Search dashboard and backend pipeline on the `main` branch. The core integration, UI cleanup, and pipeline optimization (Milestones 1, 2, 3) were previously implemented, but the final independent audit was interrupted. Conduct a strict post-victory audit to ensure all UI routing metrics (Shard IDs, latency) are properly displayed, the pipeline (`run_pipeline.py`) uses the new IVF K-Means logic, and no redundant 3D assets or memmap logic remain. Fix any outstanding issues discovered during the audit.

Working directory: f:\ANN
Integrity mode: demo

## Requirements

### R1. Final Dashboard UI & Asset Audit
Ensure all bloated, unused resources from `dashboard/` (heavy unused CSS/JS, 3D engines) are completely removed. Verify that the UI code (`app.js`, `index.html`) cleanly displays search results, including Shard IDs hit, shards probed, and execution latency.

### R2. Pipeline Refactoring Audit
Verify that `scripts/run_pipeline.py` uses the new IVF K-Means clustering logic from the updated backend, seamlessly integrating with the `ShardedIVFHNSW` router, and contains zero monolithic graph building or `memmap` logic.

### R3. Preserved Data Configuration
Confirm that the existing dataset structure and data loading configurations remain completely intact and unaltered.

## Acceptance Criteria

### Codebase Cleanliness & UI Functionality
- [ ] An independent judge agent strictly verifies that redundant UI/dashboard script files are deleted and the core frontend runs without errors.
- [ ] The dashboard UI is manually or programmatically verified to ensure Shard routing metrics and execution latency are successfully wired and visible.

### Pipeline Execution
- [ ] An independent judge agent executes or reviews `scripts/run_pipeline.py` to confirm it initializes the `ShardedIVFHNSW` router correctly and passes adversarial checks for legacy code.

## Follow-up — 2026-09-21T16:02:19Z

CRITICAL UPDATE FROM USER: The user has requested to KEEP and INTEGRATE the 3D UI files (`three_engine.js`, `three_hnsw_graph.js`, etc.) instead of deleting them. DO NOT delete any 3D UI files. Instead, make sure they are preserved and properly wired to the new backend if necessary. Update your acceptance criteria and audit to expect the 3D UI to be present and functional.

## Follow-up — 2026-09-21T16:08:29Z

CRITICAL UPDATE 2 FROM USER: The user has requested a major new feature for the dashboard. You must build a comprehensive, detailed metrics collection and charting dashboard, similar in style and detail to Weights & Biases (https://wandb.ai/). It should track and plot system metrics, query latency over time, shard hit distribution, recall rates, early exit rates, and other relevant metrics. Use frontend charting libraries (like Chart.js or similar already present) to create these detailed tracking charts. Update your requirements to include this WandB-style metrics dashboard.



