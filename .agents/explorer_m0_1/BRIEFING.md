# BRIEFING — 2026-09-21T03:44:31Z

## Mission
Investigate git repository state and compare core architecture implementations between branches `main` and `update` (two_tier_hnsw.py, hnsw_quantized.py, io_manager.py).

## 🔒 My Identity
- Archetype: explorer
- Roles: Branch & Core Architecture Explorer
- Working directory: f:\ANN\.agents\explorer_m0_1
- Original parent: aaca76c0-f648-44ef-a246-dfe8deb4d9da
- Milestone: M0 Branch & Core Architecture Exploration

## 🔒 Key Constraints
- Read-only investigation — do NOT implement
- Inspect git status, branches, commits (main vs update)
- Analyze two_tier_hnsw.py, hnsw_quantized.py, io_manager.py
- Compare update vs main
- Document exact file paths, signatures, data structures, integration points
- Produce 5-component handoff report in f:\ANN\.agents\explorer_m0_1\handoff.md
- Adhere to Layer A and Layer B writing hygiene rules

## Current Parent
- Conversation ID: aaca76c0-f648-44ef-a246-dfe8deb4d9da
- Updated: not yet

## Investigation State
- **Explored paths**:
  - Git repository structure (`main` and `update` branches, commit `7e745d4`, merge-base `1401398`).
  - `update` branch files: `two_tier_hnsw.py`, `hnsw_quantized.py`, `io_manager.py`, `data_pipeline.py`, `evaluation_metrics.py`, `danh_gia_hieu_nang.md`, `ly_do_lua_chon.md`.
  - `main` branch files: `src/ann_index/two_tier_hnsw.py`, `src/ann_index/quantizer.py`, `src/ann_index/early_exit.py`, `src/ann_index/hnsw.py`, `src/ann_data/storage.py`, `dashboard/scripts/search_service.py`, `dashboard/scripts/search_bridge.py`, `dashboard/server.js`, `dashboard/public/js/`.
- **Key findings**:
  - `update` is 1 commit ahead of `main` (`7e745d4`), where the author replaced the full repository tree with standalone scripts and test binary shards.
  - `two_tier_hnsw.py` (update) implements `LocalShard` and `ShardedIVFHNSW` with multi-shard routing (`nprobe`), ADC distance, adaptive early-exit (`tau`, `epsilon`), and direct I/O re-ranking.
  - `hnsw_quantized.py` (update) implements dynamic per-vector SQ8 with float16 scale/offset and Asymmetric Distance Computation (`distance_adc`).
  - `io_manager.py` (update) implements `DirectIOManager` with file seek/read, parallel batch read via `ThreadPoolExecutor`, and `ApplicationLRUCache` (OrderedDict), removing `numpy.memmap`.
  - `main` branch retains full enterprise directory structure (`src/`, `dashboard/`, `tests/`, `scripts/`, `data/`, `docs/`), but its `two_tier_hnsw.py` is monolithic and uses `numpy.memmap`, while `search_service.py` runs a mock linear dot product rather than the HNSW router.
  - Import coupling in `src/ann_index/__init__.py` pulls in `datasketch` via `ann_data.deduplicator`.
- **Unexplored areas**:
  - Frontend UI modifications for shard display in `dashboard/public/` (to be handled by subsequent UI worker).

## Key Decisions Made
- Analyzed all files across `main` and `update` using read-only non-destructive git inspection (`git show`, `git ls-tree`).
- Cataloged exact class signatures, methods, data structures, and architectural integration points for the merge plan.

## Artifact Index
- f:\ANN\.agents\ORIGINAL_REQUEST.md — Initial user requirements
- f:\ANN\.agents\explorer_m0_1\DISPATCH.md — Dispatch log
- f:\ANN\.agents\explorer_m0_1\progress.md — Liveness and progress heartbeat
- f:\ANN\.agents\explorer_m0_1\BRIEFING.md — Situational awareness
- f:\ANN\.agents\explorer_m0_1\handoff.md — Final investigation handoff report
