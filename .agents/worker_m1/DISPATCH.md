## 2026-09-21T03:52:49Z

You are Worker 1 (Backend Core & Router Integration).
Your working directory is f:\ANN\.agents\worker_m1.
Original request file: f:\ANN\.agents\ORIGINAL_REQUEST.md. You MUST read it before starting work.
Project specification: f:\ANN\PROJECT.md. Read this for interface contracts and architecture.
Prior exploration reports:
- Explorer 1 (Core Architecture): f:\ANN\.agents\explorer_m0_1\handoff.md
- Explorer 2 (Backend API & Data Pipeline): f:\ANN\.agents\explorer_m0_2\handoff.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Mission Objectives for Milestone 1:
1. Core Modules Integration:
   - Extract and merge the distributed sharding logic from branch `update` (can view via `git show update:two_tier_hnsw.py`, `git show update:hnsw_quantized.py`, `git show update:io_manager.py`).
   - Create `src/ann_index/io_manager.py` implementing `DirectIOManager` (raw binary seek/read, 16-worker threadpool, no numpy.memmap) and `ApplicationLRUCache`.
   - Create `src/ann_index/hnsw_quantized.py` implementing `quantize_adc`, `distance_adc`, and `exact_distance_l2`.
   - Update `src/ann_index/two_tier_hnsw.py` to implement `LocalShard` and `ShardedIVFHNSW`.
   - CRITICAL REQUIREMENT FOR GLOBAL ID MAPPING: In `LocalShard`, ensure `add_node(global_id, vector)` stores the global ID (e.g. `self.id_map[idx] = global_id`), and `distributed_search` returns `(exact_dist, global_id, sid)` so the Search API can map candidates back to original document metadata.
   - Also provide root-level modules `two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py` (or import aliases from `src/ann_index/`) for backwards compatibility.
   - Update `src/ann_index/__init__.py` to export `ShardedIVFHNSW`, `LocalShard`, `DirectIOManager`, `quantize_adc`, `distance_adc`.
2. Safe Import Guard:
   - In `src/ann_data/__init__.py`, guard `from ann_data.deduplicator import StreamDeduplicator` in a `try...except (ImportError, ModuleNotFoundError):` block so that missing `datasketch` in the environment does not crash module imports or test discovery.
3. Preserved Data Configuration (Requirement R3):
   - Strictly preserve all existing data loading configs and ingestion code in `src/ann_data/`, `src/crawler/`, `src/quantizer/`, `configs/default_pipeline.json`, and `scripts/`. Do NOT delete or modify them.
4. Search API Router Integration:
   - Refactor `dashboard/scripts/search_service.py` to instantiate `ShardedIVFHNSW` (with reasonable dimensions e.g. 384, shards e.g. 5, seeded from cached vectors) and route incoming search queries through `router.distributed_search(...)`.
   - Ensure the returned response includes `shards_probed` list (e.g. `[0, 2, 5]`) and each item in `data.results` includes `shard_id` (the specific shard storing that document).
   - Update `dashboard/scripts/search_bridge.py` to use `ShardedIVFHNSW` as well.
5. Verification & Testing:
   - Create/update unit and integration tests in `tests/test_two_tier_hnsw.py` testing:
     a) `quantize_adc` and `distance_adc` numerical behavior.
     b) `DirectIOManager` read, write, caching, and batch reading without `numpy.memmap`.
     c) `ShardedIVFHNSW` node insertion, routing, early-exit, and distributed search.
     d) `search_service.py:perform_search` producing results with `shard_id` and `shards_probed`.
   - Execute the test suite using pytest or python unittest and document the results.

File Ownership:
You own:
- `src/ann_index/io_manager.py`
- `src/ann_index/hnsw_quantized.py`
- `src/ann_index/two_tier_hnsw.py`
- `src/ann_index/__init__.py`
- `src/ann_data/__init__.py`
- `two_tier_hnsw.py` (root alias)
- `hnsw_quantized.py` (root alias)
- `io_manager.py` (root alias)
- `dashboard/scripts/search_service.py`
- `dashboard/scripts/search_bridge.py`
- `tests/test_two_tier_hnsw.py`
You MUST NOT edit files in `dashboard/public/` (reserved for Milestone 2).
