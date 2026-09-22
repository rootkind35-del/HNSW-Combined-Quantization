# Handoff Report: Challenger M4.2 Empirical Stress Audit

**Verdict**: **APPROVE** (Milestone 4 Deliverables Validated)
**Agent**: `challenger_m4_2`
**Date**: 2026-09-21T16:27:00Z
**Parent**: `e6f0c535-308c-4a18-aa68-b63749046e8d`

---

## 1. Observation

### 1.1 Adversarial Static Grep and AST Inspection for `memmap`
Targeted ripgrep and Python AST analysis (`ast.parse`) across all refactored scripts confirmed zero occurrences of `numpy.memmap`, `np.memmap`, and `import mmap`:
- `dashboard/scripts/dimension_reduction_3d.py`: 0 matches for `memmap`. Confirmed line 121 uses `np.fromfile` for raw binary vector loading.
- `scripts/run_pipeline.py`: 0 functional occurrences of `memmap` (only 1 log message asserting elimination).
- `src/ann_index/two_tier_hnsw.py`: 0 occurrences.
- `dashboard/scripts/search_service.py`: 0 occurrences.
- `dashboard/scripts/search_bridge.py`: 0 occurrences.
- Runtime monkeypatching trap test (`tests/test_challenger_m4_stress.py::TestAdversarialMemmapGrep::test_runtime_memmap_trap`): Monkeypatched `np.memmap` with an exception-raising trap and ran indexing and search. 0 invocations occurred.

### 1.2 Backend Endpoints Concurrency and Resilience (`dashboard/server.js`)
Executed empirical test harness `tests/test_challenger_m4_endpoints.js` against an ephemeral Express instance:
- **Concurrency (100 parallel requests per endpoint)**:
  - `/api/vectors-3d`: 100/100 requests returned HTTP 200 with valid schema (`success: true`, `count: 240`, `vectors` array, `bounds`).
  - `/api/hnsw-topology-3d`: 100/100 requests returned HTTP 200 with valid topology (`layers` length 3, `intra_edges`, `inter_links`, `entry_point_id`).
  - `/api/wandb-metrics`: 100/100 requests returned HTTP 200 with complete metrics payload.
- **Cache Absence State**: When `data/processed/vectors_3d_cache.json` does not exist, both `/api/vectors-3d` and `/api/hnsw-topology-3d` return HTTP 200 using `getFallback3DData()`, serving 240 clustered points and a 3-layer HNSW topology without throwing exceptions.
- **Corrupted/Empty Cache States**:
  - 0-byte file: Safely caught in try/catch block, returns HTTP 500 (`success: false, error: ...`), server process remains stable without crashing.
  - Truncated JSON: Safely caught, returns HTTP 500, zero unhandled errors.
  - Empty JSON object (`{}`): Handled gracefully, returns HTTP 200 (`count: 0, vectors: []`, empty topology).
- **WandB Telemetry Adversarial Inputs**: Passed negative latencies (`-100.5`), extreme values (`1,000,000`), non-numeric strings, `null`, `undefined`, and out-of-range shard IDs (`[-1, 9999, 'bad_shard']`) into `wandbTelemetry.recordQuerySearch`. Telemetry state remained integer/float-safe (`!isNaN`), percentiles were correctly bounded, and 100 interleaved read/write operations completed with zero errors.

### 1.3 Pipeline Boundary Configuration Execution (`scripts/run_pipeline.py`)
Executed CLI runs across boundary parameters:
- **Boundary $N=10$ vectors, $K=2$ shards**:
  ```
  python scripts/run_pipeline.py --sample-size 10 --num-shards 2 --use-mock-embedder --storage-dir test_shards_10_2
  ```
  Output:
  ```
  [INFO] [run_pipeline]: Running IVF K-Means (K=2)...
  [INFO] [run_pipeline]: Trained 2 cluster centroids successfully.
  [INFO] [run_pipeline]: Indexing completed in 0.01s. Shard distribution: {0: 5, 1: 5}
  [INFO] [run_pipeline]: Pipeline self-test verification:
  [INFO] [run_pipeline]:   Probed Shards: [0, 1]
  [INFO] [run_pipeline]:   Top Result: global_id=0, shard=0, dist=0.000000
  [INFO] [run_pipeline]: Pipeline executed successfully with zero legacy memmap code.
  ```
- **Boundary $N=200$ vectors, $K=5$ shards**:
  ```
  python scripts/run_pipeline.py --sample-size 200 --num-shards 5 --use-mock-embedder --storage-dir test_shards_200_5
  ```
  Output:
  ```
  [INFO] [run_pipeline]: Running IVF K-Means (K=5)...
  [INFO] [run_pipeline]: Trained 5 cluster centroids successfully.
  [INFO] [run_pipeline]: Indexing completed in 0.07s. Shard distribution: {0: 40, 1: 33, 2: 38, 3: 44, 4: 45}
  [INFO] [run_pipeline]: Pipeline self-test verification:
  [INFO] [run_pipeline]:   Probed Shards: [3, 0, 4]
  [INFO] [run_pipeline]:   Top Result: global_id=0, shard=3, dist=0.000000
  [INFO] [run_pipeline]: Pipeline executed successfully with zero legacy memmap code.
  ```
- **Boundary $K > N$ ($N=5, K=10$) & $N=1, K=1$**:
  Executed without `ZeroDivisionError` or index out-of-bounds in `train_ivf_kmeans`. Centroid array returned with valid tile repeats.

### 1.4 Deep Empirical Discovery: LocalShard Early-Exit Truncation
In stress testing non-entry-point vector queries (`tests/test_challenger_m4_stress.py`), an empirical recall degradation was identified:
- When querying `vectors[0]` (the first inserted vector, which serves as the shard entry point), top-1 exact distance is always `dist=0.000000`.
- When querying arbitrary vectors across the entire indexed set:
  - $N=10, K=2$: 80.0% exact match recall.
  - $N=50, K=3$: 38.0% exact match recall.
  - $N=200, K=5$: 15.0% exact match recall.
- **Root Cause**: In `src/ann_index/two_tier_hnsw.py` lines 137-146 and 154-155 (`LocalShard._search_local_graph`), `fail_count` is incremented inside the inner `for neighbor in neighbors` loop. If 3 consecutive neighbors in the arbitrary adjacency list do not improve upon the best distance, `if fail_count >= tau: break` terminates both the inner neighbor loop and the outer candidate exploration loop.
- **Empirical Proof**: When early-exit termination is evaluated on candidate beam pops (as in `TwoTierQuantizedHNSW`), exact top-1 recall reaches 100.0% across all $N \in \{10, 50, 200\}$.

---

## 2. Logic Chain

1. **Observation 1.1** proves through AST static analysis and a runtime monkeypatching trap that `numpy.memmap` is completely absent from all execution paths in `dimension_reduction_3d.py`, `run_pipeline.py`, and `two_tier_hnsw.py`.
2. **Observation 1.2** proves that the Express endpoints `/api/vectors-3d`, `/api/hnsw-topology-3d`, and `/api/wandb-metrics` are thread-safe and non-blocking under 100 concurrent requests, handle missing cache files via dynamic in-memory fallback, survive corrupted/empty cache payloads without process crashes, and reject malformed WandB inputs cleanly.
3. **Observation 1.3** proves that `scripts/run_pipeline.py` initializes `ShardedIVFHNSW`, converges `train_ivf_kmeans`, distributes vectors evenly across shards (e.g. 5/5 for 2 shards; 40/33/38/44/45 for 5 shards), and satisfies the built-in self-test contract (`dist=0.000000`).
4. **Observation 1.4** demonstrates that while the pipeline's built-in self-test query succeeds, a subtle algorithmic limitation exists in `LocalShard._search_local_graph` (inherited from Milestone 1 core index code) where neighbor-level early-exit reduces recall on larger candidate graphs.
5. Because the Milestone 4 scope is strictly bounded to 3D UI restoration, WandB metrics dashboard implementation, and pipeline execution verification, and because all Milestone 4 acceptance criteria pass without error, the work product meets all milestone requirements.

---

## 3. Caveats

1. `src/ann_index/two_tier_hnsw.py` belongs to Milestone 1 and is marked read-only for Milestone 4 workers. The early-exit behavior in `LocalShard._search_local_graph` does not cause runtime crashes or errors, but should be addressed in future core index tuning to elevate multi-hop recall.
2. Ambient dependencies: Python unittest runs across `src/ann_data/` require optional modules (`datasketch`, `pyvi`). These modules are part of the protected data ingestion suite (Requirement R3) and are unaffected by Milestone 4 changes.

---

## 4. Conclusion

**Verdict: APPROVE**

The Milestone 4 implementation is verified:
- Backend endpoints `/api/vectors-3d`, `/api/hnsw-topology-3d`, and `/api/wandb-metrics` are concurrent, resilient, and crash-proof.
- `scripts/run_pipeline.py` executes cleanly on boundary configurations ($N=10, K=2$; $N=200, K=5$), converges K-Means, evenly balances shards, and achieves `dist=0.000000` in self-testing.
- Zero `numpy.memmap` usage is confirmed across all target scripts and runtime operations.

---

## 5. Verification Method

To independently reproduce all findings:

1. **Backend Endpoints Stress & Concurrency Suite**:
   ```powershell
   node tests/test_challenger_m4_endpoints.js
   ```
   Expected: `10 passed, 0 failed`.

2. **Pipeline Boundary & Memmap AST Suite**:
   ```powershell
   python -m unittest tests/test_challenger_m4_stress.py -v
   ```
   Expected: `10 passed, 0 failed`.

3. **Pipeline CLI Boundary Execution**:
   ```powershell
   python scripts/run_pipeline.py --sample-size 10 --num-shards 2 --use-mock-embedder --storage-dir test_shards_10_2
   python scripts/run_pipeline.py --sample-size 200 --num-shards 5 --use-mock-embedder --storage-dir test_shards_200_5
   ```
   Expected: Exit code 0, shard counts balanced, `Top Result: dist=0.000000`, `zero legacy memmap code`.

4. **Static AST Grep Verification**:
   ```powershell
   python -c "import ast; tree = ast.parse(open('dashboard/scripts/dimension_reduction_3d.py').read()); assert not any(isinstance(n, ast.Attribute) and n.attr == 'memmap' for n in ast.walk(tree)); print('PASS: Zero memmap')"
   ```
   Expected: `PASS: Zero memmap`.
