# BRIEFING — 2026-09-21T03:49:15Z

## Mission
Investigate backend server architecture, search API endpoints, index loading/memmap usage, dataset structure and ingestion config, and determine exact changes needed to switch Search API to ShardedIVFHNSW router-based flow while preserving data loading configuration.

## 🔒 My Identity
- Archetype: explorer
- Roles: Backend API & Data Pipeline Explorer
- Working directory: f:\ANN\.agents\explorer_m0_2
- Original parent: aaca76c0-f648-44ef-a246-dfe8deb4d9da
- Milestone: M0 Exploration

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Zero Hidden Watermarks (Layer A Cleanup)
- Eliminate AI Writing Style Tells (Layer B Mitigation)
- Write only to own folder (f:\ANN\.agents\explorer_m0_2)
- Preserve existing dataset structure and data loading configuration (Requirement R3)

## Current Parent
- Conversation ID: aaca76c0-f648-44ef-a246-dfe8deb4d9da
- Updated: not yet

## Investigation State
- **Explored paths**:
  - `dashboard/server.js`: Node.js Express server on port 3000, lifecycle and routing
  - `dashboard/scripts/search_service.py`: Resident Python HTTP server on port 5005
  - `dashboard/scripts/search_bridge.py`: CLI search fallback and cache loading logic
  - `src/ann_index/two_tier_hnsw.py`: Existing monolithic TwoTierQuantizedHNSW on main using memmap
  - `update` branch files: `two_tier_hnsw.py` (ShardedIVFHNSW, LocalShard), `hnsw_quantized.py` (ADC quantization), `io_manager.py` (DirectIOManager, ApplicationLRUCache)
  - `configs/default_pipeline.json`, `src/ann_data/`, `src/crawler/`, `src/quantizer/`: Ingestion configurations to preserve per R3
  - Environment dependencies: Missing `datasketch` and `sentence_transformers` in conda base causing eager import failure in `src/ann_data/__init__.py`
- **Key findings**:
  - Web server uses Express (`server.js`), spawns Python HTTP daemon `search_service.py` on port 5005 via `ensureSearchService()`, falls back to CLI `search_bridge.py`.
  - Current search performs flat `np.dot` in memory; need to switch to `ShardedIVFHNSW.distributed_search`.
  - `LocalShard` on `update` branch lacks `global_id` mapping (ignores `global_id` in `add_node`), requiring `id_map` fix during merge.
  - Search API response schema needs `shard_id` in each result item and `shards_hit` at top-level.
  - Core algorithm on `update` eliminates `numpy.memmap` by using `DirectIOManager` with LRU cache and binary file seek.
  - Requirement R3 is preserved by retaining all of `src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/`, and `scripts/`.
- **Unexplored areas**: None within the exploration scope.

## Key Decisions Made
- Identified exact entry points and dispatch call chains.
- Outlined precise data contracts for ShardedIVFHNSW integration.
- Documented import safety fixes needed for optional dependencies.

## Artifact Index
- `f:\ANN\.agents\explorer_m0_2\DISPATCH.md` — Task dispatch log
- `f:\ANN\.agents\explorer_m0_2\BRIEFING.md` — Situational awareness
- `f:\ANN\.agents\explorer_m0_2\progress.md` — Heartbeat & progress tracker
- `f:\ANN\.agents\explorer_m0_2\handoff.md` — Comprehensive 5-section handoff report
