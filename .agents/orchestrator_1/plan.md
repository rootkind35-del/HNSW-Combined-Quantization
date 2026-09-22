# Master Plan: Vector Search Optimization & Sharded IVF-HNSW Integration

## Objectives
1. Integrate Distributed Sharded IVF-HNSW core logic (`two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`) from branch `update` to `main`.
2. Update the Search API to use the new Router-based execution flow with early-exit and ADC quantization, avoiding deprecated `numpy.memmap`.
3. Clean up bloated/unused resources in `dashboard/` (e.g., heavy CSS/JS, unused 3D engines) and optimize UI to display Shard IDs and execution latency cleanly.
4. Strictly preserve existing dataset structure and data loading configuration.
5. Fully verify API stability, codebase cleanliness, and forensic integrity.

## Milestones

### Milestone 0: Comprehensive Repository & Branch Survey
- Explorer 1 (Branch & Core Files): Analyze git diff between `main` and `update`, locating `two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`, and router structures.
- Explorer 2 (Backend & API Flow): Inspect backend server entry point, API search endpoints, router integration points, memory management, and data loading pipeline.
- Explorer 3 (Dashboard & UI Assets): Audit `dashboard/` directory, identifying redundant 3D engines, legacy scripts, asset sizes, and UI components needing Shard ID / latency display.
- Deliverable: Consolidated `PROJECT.md` with architecture, feature inventory, code layout, and interface contracts.

### Milestone 1: Backend Core & Router Integration (R1, R3)
- Worker: Bring in distributed sharding logic, ADC quantization, and direct I/O manager; adapt search API to use `ShardedIVFHNSW` router; implement early-exit; eliminate deprecated `numpy.memmap`; preserve data loading setup intact.
- Reviewers: 2 independent reviewers checking correctness, interfaces, and data loader preservation.
- Challenger: Functional tests for router loading, search endpoint execution, early-exit, and ADC quantization.
- Auditor: Verify genuine algorithm implementation and absence of hardcoded stubs.

### Milestone 2: Dashboard Clean-up & UI Optimization (R2)
- Worker: Remove bloated 3D engines and legacy JS/CSS from `dashboard/`; optimize remaining UI code; ensure clean presentation of search results with hit Shard IDs and execution latency.
- Reviewers: Verify file deletions, performance improvements, and UI code quality.
- Challenger: Verify assets serve properly without 404s and UI correctly binds to backend payload fields.
- Auditor: Verify genuine UI cleanup without broken interfaces.

### Milestone 3: End-to-End Verification & Final Review
- Independent Judge / Auditor validation against all acceptance criteria:
  - Backend API loads `ShardedIVFHNSW` router and exposes search endpoint without errors.
  - Early-exit and ADC quantization active without `numpy.memmap`.
  - Redundant files completely removed.
  - Performance and code quality verified.
- Delivery of final report to parent.
