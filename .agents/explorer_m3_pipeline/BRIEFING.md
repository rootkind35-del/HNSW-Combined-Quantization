# BRIEFING — 2026-09-21T06:10:00Z

## Mission
Investigate Requirement R2 (Pipeline Optimization & Router Integration) across scripts/run_pipeline.py, two_tier_hnsw.py, io_manager.py, and search_service.py.

## 🔒 My Identity
- Archetype: explorer
- Roles: investigation, synthesis
- Working directory: f:\ANN\.agents\explorer_m3_pipeline
- Original parent: f6bb6527-f227-482e-9dba-02b6816c634b
- Milestone: M3

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Layer A cleanup: Zero hidden watermarks, clean code writes
- Layer B mitigation: Direct, objective style, avoid AI buzzwords
- Respect file workspace convention (.agents/explorer_m3_pipeline only)
- Send message back to parent when done

## Current Parent
- Conversation ID: f6bb6527-f227-482e-9dba-02b6816c634b
- Updated: 2026-09-21T06:10:00Z

## Investigation State
- **Explored paths**:
  - scripts/run_pipeline.py (84 lines: inspected CLI args, memmap arg, lack of ANN indexing)
  - src/ann_index/two_tier_hnsw.py (550 lines: LocalShard and ShardedIVFHNSW interfaces, random centroid init)
  - src/ann_index/hnsw_quantized.py (quantize_adc, distance_adc, exact_distance_l2)
  - src/ann_index/io_manager.py (DirectIOManager, ApplicationLRUCache)
  - src/ann_index/ivf_pq.py & pq.py (_train_coarse_centroids, _fast_kmeans)
  - src/ann_data/ (config.py, pipeline.py, deduplicator.py, storage.py)
  - dashboard/scripts/search_service.py & search_bridge.py (ShardedIVFHNSW router initialization and search)
  - tests/test_two_tier_hnsw.py & test_stress_core_index.py (15 and 13 tests passing)
- **Key findings**:
  - scripts/run_pipeline.py line 46 has legacy `--output-memmap` argument and lines 58-59 assign `config.output_memmap_path`.
  - run_pipeline.py does not invoke any ANN indexing or clustering; it only executes DataPipeline streaming to disk.
  - ShardedIVFHNSW currently generates random Gaussian centroids (`np.random.randn(num_shards, dim)`) and lacks persistence (`save()`/`load()`) and clustering (`train_centroids()`).
  - Vectorized K-Means clustering is already implemented in `src/ann_index/ivf_pq.py` (`_train_coarse_centroids`).
  - search_service.py dynamically seeds ShardedIVFHNSW in RAM on startup because no offline persistence exists.
  - R3 boundaries: `src/ann_data/` and `configs/default_pipeline.json` must remain untouched.
- **Unexplored areas**: None for this milestone exploration scope.

## Key Decisions Made
- Designed complete refactored `scripts/run_pipeline.py` supporting end-to-end data ingestion, IVF K-Means clustering, ShardedIVFHNSW construction, DirectIOManager storage, and artifact serialization.
- Designed interface contract between `ShardedIVFHNSW`, `run_pipeline.py`, and `search_service.py`.

## Artifact Index
- DISPATCH.md — Dispatch log
- BRIEFING.md — Situational awareness
- progress.md — Progress tracker
- handoff.md — Final investigation report
