# Master Plan — Orchestrator 2 (Milestone 2 & Milestone 3)

## Objective
Execute Milestone 2 (Dashboard Clean-up & UI Optimization) and Milestone 3 (Pipeline Optimization), followed by comprehensive verification and forensic auditing to align the project with Distributed Sharded IVF-HNSW.

---

## Phase 1: Technical Exploration & Assessment
- **Task 1.1: M2 Technical Exploration (Explorer)**
  - Inspect `dashboard/` directory to catalog all bloated/redundant files:
    - 3D engine files (`three_*.js`, `dimension_reduction_3d.py`)
    - Unused benchmark scripts not needed for production API
    - Unused CSS/JS such as `data_product_studio`
  - Inspect `dashboard/public/index.html`, `dashboard/public/js/app.js`, `dashboard/server.js`, and `custom.css`
  - Map UI components to receive and display: Shard IDs hit, shards probed, and execution latency metrics from `/api/search`.
- **Task 1.2: M3 Technical Exploration (Explorer)**
  - Inspect `scripts/run_pipeline.py` to identify legacy monolithic graph building, old indexing calls, and `numpy.memmap` usage.
  - Review `src/ann_index/two_tier_hnsw.py` and clustering modules to determine exact IVF K-Means clustering integration with `ShardedIVFHNSW`.
  - Confirm preservation boundaries (R3): ensure data ingestion pipeline and dataset structures remain intact.

---

## Phase 2: Milestone 2 — Dashboard Clean-up & UI Optimization
- **Task 2.1: Worker Execution (Worker M2)**
  - Delete redundant assets in `dashboard/` (3D engines, benchmark scripts not needed for production, `data_product_studio` JS/CSS).
  - Clean `index.html`: remove obsolete script tags/links, add UI badges/containers for Shards Probed, Shard IDs Hit, and Latency.
  - Clean `server.js`: ensure obsolete 3D endpoints are removed and `/api/search` cleanly serves router response data.
  - Update `app.js`: cleanly parse and display Shard IDs hit per result, shards probed list, and execution latency.
  - Optimize UI performance (throttling, error states, clean layout).
- **Task 2.2: Review & Verification Gate (Reviewer M2 & Challenger M2)**
  - Verify deleted files are completely removed.
  - Verify frontend renders without console errors or broken resource links.
  - Verify Shard routing metrics and latency are properly wired and displayed.

---

## Phase 3: Milestone 3 — Pipeline Optimization
- **Task 3.1: Worker Execution (Worker M3)**
  - Refactor `scripts/run_pipeline.py` to use IVF K-Means clustering logic.
  - Seamlessly initialize and populate `ShardedIVFHNSW` router.
  - Purge all legacy `numpy.memmap` imports and monolithic graph construction logic.
  - Strictly preserve dataset structures and data ingestion pipeline (R3).
- **Task 3.2: Review & Verification Gate (Reviewer M3 & Challenger M3)**
  - Verify `scripts/run_pipeline.py` imports and runs `ShardedIVFHNSW`.
  - Verify zero occurrences of legacy `memmap` or monolithic graph code.
  - Verify data loading compatibility and pipeline execution.

---

## Phase 4: Final Gate & Forensic Integrity Audit
- **Task 4.1: Forensic Integrity Audit (Auditor)**
  - Audit codebase against integrity standards (no hardcoded metrics, no dummy mocks, no fake assertions).
  - Confirm binary veto compliance.
- **Task 4.2: Gate Decision & Synthesis**
  - Record verdicts in `GATE_STATUS.md`.
  - Compile final results.
- **Task 4.3: User & Parent Reporting**
  - Synthesize outcomes, produce handoff, and deliver structured report.
