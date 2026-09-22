## 2026-09-21T06:11:37Z
You are worker_m3_pipeline, an implementation worker.
Your Working Directory: f:\ANN\.agents\worker_m3_pipeline
Your Parent: f6bb6527-f227-482e-9dba-02b6816c634b

MANDATORY FIRST STEP:
Read f:\ANN\.agents\ORIGINAL_REQUEST.md, f:\ANN\PROJECT.md, and f:\ANN\.agents\explorer_m3_pipeline\handoff.md before making any changes.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

File Ownership Boundaries:
You EXCLUSIVELY own and are permitted to edit:
- `scripts/run_pipeline.py`
DO NOT modify any files in `dashboard/` (owned by Worker M2).
DO NOT alter `configs/default_pipeline.json`, `data/`, or `src/ann_data/` (strictly preserved under Requirement R3).

Detailed Tasks:
1. Refactor `scripts/run_pipeline.py` following the detailed architecture and code provided in `f:\ANN\.agents\explorer_m3_pipeline\handoff.md §4.2`:
   - Completely eliminate `--output-memmap` argument and any assignment to `config.output_memmap_path`.
   - Implement IVF K-Means clustering (`train_ivf_kmeans`) to compute coarse cluster centroids from sample/ingested vectors.
   - Initialize `ShardedIVFHNSW` router (`from ann_index.two_tier_hnsw import ShardedIVFHNSW`) with `dim`, `num_shards`, `capacity_per_shard`, `storage_dir`, and `clean_storage=True`.
   - Assign trained K-Means centroids to `router.centroids`.
   - Route and insert all vectors using `router.route_and_insert(global_id=i, vector=vectors[i])`.
   - Save artifacts for `search_service.py` to `storage_dir`:
     - `centroids.npy`
     - `router_metadata.json` (dim, num_shards, total_vectors, shard_distribution, created_at)
     - Per-shard state archives: `shard_{sid}_state.npz` (quantized, scales, offsets, id_map, entry_point, local_count, graph_json)
   - Include inline self-test: execute `router.distributed_search(query=test_query, top_k=5, nprobe=args.nprobe, return_shards=True)` and log probed shards and top result distance.
   - Ensure resilient execution: support `--use-mock-embedder` and gracefully handle missing optional packages (like `datasketch` or `sentence_transformers`).
2. Verification:
   - Run `python scripts/run_pipeline.py --help` to confirm valid CLI arguments and absence of `--output-memmap`.
   - Run pipeline with test parameters: `python scripts/run_pipeline.py --sample-size 100 --num-shards 3 --use-mock-embedder --storage-dir tests/temp_pipeline_shards`
   - Check that output artifacts are created in `tests/temp_pipeline_shards`.
   - Clean up `tests/temp_pipeline_shards`.
   - Verify with grep: ensure 0 occurrences of `memmap` or monolithic graph building in `scripts/run_pipeline.py`.
   - Verify unittests: `python -m unittest tests/test_two_tier_hnsw.py tests/test_stress_core_index.py`.
   - Verify R3 preservation: `git diff -- configs/default_pipeline.json src/ann_data/` must be clean.

Deliverables:
Document all changes, CLI outputs, test verification, and file diffs in `f:\ANN\.agents\worker_m3_pipeline\handoff.md`.
Update `progress.md` in your working directory.
When done, send a completion message to parent with path to handoff.md.
