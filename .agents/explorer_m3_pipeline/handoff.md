# Investigation Report: Requirement R2 (Pipeline Optimization & Router Integration)

## 1. Observation

### 1.1 Current Structure of `scripts/run_pipeline.py`
The file `scripts/run_pipeline.py` contains 84 lines. Its execution flow consists of:
1. Lines 10-13: Imports modules from `ann_data`:
   ```python
   from ann_data.config import PipelineConfig
   from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
   from ann_data.pipeline import DataPipeline
   from ann_data.utils import get_logger
   ```
2. Lines 16-38: Defines `sample_stream_generator(count: int)` yielding `(doc_id, text)` synthetic pairs.
3. Lines 41-47: Configures CLI arguments:
   - `--config`: JSON configuration path (default: `configs/default_pipeline.json`).
   - `--sample-size`: Number of synthetic records to generate (default: `1000`).
   - `--use-mock-embedder`: Switch to `MockEmbedder` instead of `SentenceTransformerEmbedder`.
   - `--output-memmap`: Override output memmap file path (default: `None`).
4. Lines 58-60: Overrides the storage path:
   ```python
   if args.output_memmap:
       config.output_memmap_path = args.output_memmap
   config.max_records = max(config.max_records, args.sample_size)
   ```
5. Lines 73-75: Executes the streaming pipeline:
   ```python
   with DataPipeline(config=config, embedder=embedder) as pipeline:
       stats = pipeline.process_stream(stream, log_interval=max(1, args.sample_size // 5))
   ```
6. Lines 76-79: Logs processing statistics and exits.

### 1.2 Legacy Code to Eliminate in `scripts/run_pipeline.py`
- Line 46:
  ```python
  parser.add_argument("--output-memmap", type=str, default=None, help="Ghi đè đường dẫn tệp xuất memmap")
  ```
- Lines 58-59:
  ```python
  if args.output_memmap:
      config.output_memmap_path = args.output_memmap
  ```
- Omission of Index Building: `run_pipeline.py` currently has zero logic to build an approximate nearest neighbor (ANN) index. It only writes vectors to disk via `MemmapStorage` (`data/processed/vectors.dat`).

### 1.3 Legacy Monolithic Graph Building elsewhere in the Repository
- `scripts/build_ann_graph.py` builds a single monolithic HNSW graph on flat vector files:
  - Line 203: Reads vectors using `np.memmap(v_file, dtype="int8", mode="r", shape=(total_available, dim))`.
  - Lines 67-100: Serializes a single graph into binary format with magic header `b"AGYHNSW1"`.
- `src/ann_index/two_tier_hnsw.py` contains `TwoTierQuantizedHNSW` (lines 382-550), which builds a monolithic in-memory graph connecting all $N$ vectors into a single adjacency structure (`self.graph`).

### 1.4 Sharded Architecture State (`src/ann_index/two_tier_hnsw.py`)
- `LocalShard` (lines 21-220):
  - Tier 1: Maintains `self.graph: Dict[int, List[int]]`, `self.quantized: np.ndarray (uint8)`, `self.scales: np.ndarray (float16)`, `self.offsets: np.ndarray (float16)`, `self.id_map: Dict[int, int]` (local node index to global ID), and `self.entry_point: Optional[int]`.
  - Tier 2: Directly writes raw float32 vectors to `shard_{shard_id}.bin` via `DirectIOManager` (seek offset `idx * dim * 4`).
  - Method `add_node(global_id, vector, M=16, ef_construction=32)` inserts a vector into the local graph and appends raw float32 bytes to SSD.
- `ShardedIVFHNSW` (lines 222-380):
  - Constructor takes `(dim, num_shards, capacity_per_shard, storage_dir, clean_storage=False)`.
  - Line 254 initializes centroids randomly:
    ```python
    np.random.seed(42)
    self.centroids = np.random.randn(num_shards, dim).astype(np.float32)
    ```
  - Centroid Routing: `_get_nearest_shards(vector, nprobe)` evaluates Euclidean distance against `self.centroids`.
  - Insertion: `route_and_insert(global_id, vector)` directs the vector to the closest centroid shard (`nprobe=1`) and calls `self.shards[target_shard_id].add_node(global_id, vector)`.
  - Search: `distributed_search(query, top_k, nprobe, re_rank_limit, return_shards=True)` probes `nprobe` candidate shards, performs ADC beam search with adaptive early-exit, reads full-precision float32 vectors asynchronously via `DirectIOManager.async_read_batch`, and re-ranks via exact L2 distance.
  - Absence of Clustering & Persistence:
    - Neither `ShardedIVFHNSW` nor `LocalShard` currently includes K-Means centroid training methods.
    - Neither class provides `save()` or `load()` serialization methods for the Tier 1 in-memory graphs, quantized arrays, or centroids.

### 1.5 Clustering Implementations in the Repository
- `src/ann_index/ivf_pq.py` (lines 48-81) implements vectorized K-Means in `_train_coarse_centroids(vectors: np.ndarray, k: int) -> np.ndarray` with random sample initialization, broadcasted distance calculation, cluster assignment, mean recalculation, and convergence checking (`atol=1e-4`, 15 iterations max).
- `src/ann_index/pq.py` (lines 34-79) implements `_fast_kmeans(data: np.ndarray, k: int) -> np.ndarray`.
- `src/quantizer/` provides scalar quantization (`ScalarQuantizer8`) and text chunking (`TextChunker`), but contains no clustering methods.

### 1.6 Consumer Interface (`dashboard/scripts/search_service.py` & `search_bridge.py`)
- `dashboard/scripts/search_service.py` (lines 61-78) initializes `ShardedIVFHNSW`:
  ```python
  storage_dir = os.path.join(BASE_DIR, "shards_db")
  dim = G_VECTORS.shape[1]
  num_shards = 5
  capacity = max(len(G_VECTORS), 1000)
  G_ROUTER = ShardedIVFHNSW(
      dim=dim,
      num_shards=num_shards,
      capacity_per_shard=capacity,
      storage_dir=storage_dir,
      clean_storage=True,
  )
  seed_count = min(len(G_VECTORS), 1000)
  for i in range(seed_count):
      G_ROUTER.route_and_insert(global_id=i, vector=G_VECTORS[i])
  ```
  Because no index persistence exists, `search_service.py` reconstructs shards in memory at startup by inserting 1,000 vectors one by one with random centroids.

### 1.7 Verification Commands and Baseline Tests
- Command: `python -m unittest tests/test_two_tier_hnsw.py`
  Result: 15 tests run, 0 failures, exit code 0.
- Command: `python -m unittest tests/test_stress_core_index.py`
  Result: 13 tests run, 0 failures, exit code 0.
- Command: `python scripts/run_pipeline.py --help`
  Result: Fails with `ModuleNotFoundError: No module named 'datasketch'` because line 12 imports `DataPipeline` unconditionally while `datasketch` is missing from the active environment. In contrast, `src/ann_data/__init__.py` guards this import with `try...except (ImportError, ModuleNotFoundError)`.

---

## 2. Logic Chain

1. **Elimination of Legacy Code**:
   - Observations in 1.1 and 1.2 show that `scripts/run_pipeline.py` exposes `--output-memmap` and updates `config.output_memmap_path`.
   - The project architecture requires replacing `numpy.memmap` with `DirectIOManager` and sharded storage.
   - Therefore, `--output-memmap` and any assignment to `config.output_memmap_path` must be removed from `scripts/run_pipeline.py`.

2. **Transition from Monolithic to Sharded IVF Indexing**:
   - Observations in 1.1 and 1.3 reveal that `run_pipeline.py` currently builds no index, while historical scripts (`build_ann_graph.py`) built a single monolithic HNSW graph.
   - Requirement R2 mandates configuring `scripts/run_pipeline.py` to use the IVF K-Means clustering logic and `ShardedIVFHNSW`.
   - Therefore, `scripts/run_pipeline.py` must take ingested or cached vectors, execute K-Means clustering to identify shard centroids, and insert all vectors into `ShardedIVFHNSW`.

3. **IVF K-Means Clustering Strategy**:
   - Observations in 1.4 and 1.5 show that `two_tier_hnsw.py` initializes centroids with random Gaussian noise and lacks a K-Means routine, whereas `ivf_pq.py` contains a working vectorized K-Means algorithm (`_train_coarse_centroids`).
   - For `ShardedIVFHNSW` to distribute vectors effectively, centroids must represent the data distribution rather than random noise.
   - Therefore, `ShardedIVFHNSW` should expose a `train_centroids(vectors: np.ndarray, max_iters: int = 15)` method (or accept computed centroids from `run_pipeline.py`), training $K$ centroids using Euclidean K-Means.

4. **Storage Contract and Coordination with `search_service.py`**:
   - Observation in 1.6 shows `search_service.py` initializes `ShardedIVFHNSW` pointing to `storage_dir = "shards_db"`.
   - Currently, Tier 2 writes raw float32 vectors to `shards_db/shard_{id}.bin`. However, Tier 1 graphs, quantized vectors, scale/offset anchors, ID mappings, and centroids are not persisted.
   - If `scripts/run_pipeline.py` persists these artifacts into `shards_db/` (`centroids.npy`, `router_metadata.json`, and per-shard graph/quantized archives `shard_{id}_state.npz`), `search_service.py` can load the pre-built index directly.
   - If artifacts are missing, `search_service.py` retains its current dynamic fallback without disruption.

5. **Preservation of Requirement R3**:
   - Requirement R3 forbids altering existing dataset structures or data ingestion configurations in `src/ann_data/` and `configs/default_pipeline.json`.
   - Observation in 1.7 shows `src/ann_data/__init__.py` already guards optional imports (`StreamDeduplicator`, `DataPipeline`).
   - To preserve R3, `scripts/run_pipeline.py` must retain `--config` pointing to `configs/default_pipeline.json`, preserve `sample_stream_generator`, support `MockEmbedder` and `SentenceTransformerEmbedder`, and gracefully support indexing from cache or stream. All files in `src/ann_data/` and `configs/default_pipeline.json` remain untouched.

---

## 3. Caveats

1. **Missing `datasketch` in Runtime Environment**:
   - The active Python environment lacks `datasketch`. If `scripts/run_pipeline.py` directly executes `from ann_data.pipeline import DataPipeline`, it raises `ModuleNotFoundError`.
   - Mitigation: `scripts/run_pipeline.py` should import `DataPipeline` with a graceful fallback, and allow indexing directly from generated samples, precomputed vectors (`data/processed/search_index_cache.npz`), or direct embedding via `MockEmbedder`/`SentenceTransformerEmbedder`.
2. **Backward Compatibility of `two_tier_hnsw.py`**:
   - Any additions to `ShardedIVFHNSW` (such as `train_centroids`, `save`, or `load`) must not alter existing constructor signatures or parameter defaults, ensuring tests in `tests/test_two_tier_hnsw.py` and `tests/test_stress_core_index.py` pass without modification.
3. **No Direct Code Modifications Performed**:
   - In accordance with explorer role constraints, no changes have been applied to source files during this investigation.

---

## 4. Conclusion & Actionable Design

### 4.1 Interface Contract
The sharded storage layout under `storage_dir` (default: `shards_db/`) must consist of:
```
shards_db/
├── centroids.npy                  # Float32 array of shape (num_shards, dim)
├── router_metadata.json           # JSON containing dim, num_shards, total_vectors, shard_counts
├── shard_0.bin                    # Tier 2: raw float32 vectors (DirectIOManager)
├── shard_0_state.npz              # Tier 1: quantized (uint8), scales (f16), offsets (f16), id_map, entry_point, graph
├── shard_1.bin
├── shard_1_state.npz
└── ...
```

#### Additions to `src/ann_index/two_tier_hnsw.py`:
1. `LocalShard.save_state(self, filepath: str) -> None`:
   Saves `self.quantized[:self.local_count]`, `self.scales[:self.local_count]`, `self.offsets[:self.local_count]`, `self.id_map`, `self.entry_point`, and serialized `self.graph` into a single `.npz` file.
2. `LocalShard.load_state(self, filepath: str) -> None`:
   Restores Tier 1 arrays, sets `self.local_count`, and reconstructs `self.graph` and `self.id_map`.
3. `ShardedIVFHNSW.train_centroids(self, vectors: np.ndarray, max_iters: int = 15) -> np.ndarray`:
   Trains $K$ centroids using vectorized Euclidean K-Means.
4. `ShardedIVFHNSW.save(self, storage_dir: Optional[str] = None) -> None`:
   Writes `centroids.npy`, `router_metadata.json`, and calls `shard.save_state()` for each shard.
5. `ShardedIVFHNSW.load(cls, storage_dir: str) -> ShardedIVFHNSW`:
   Classmethod that re-instantiates the router, loads centroids, initializes `LocalShard` instances with `clean_storage=False`, and calls `shard.load_state()`.

### 4.2 Proposed Refactored Implementation of `scripts/run_pipeline.py`
```python
"""Pipeline execution script for Distributed Sharded IVF-HNSW vector search."""

import argparse
import json
import os
import sys
import time
from typing import Dict, Iterable, List, Optional, Tuple
import numpy as np

# Add src/ to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from ann_data.config import PipelineConfig
from ann_data.embedder import MockEmbedder, SentenceTransformerEmbedder
from ann_data.utils import get_logger
from ann_index.two_tier_hnsw import ShardedIVFHNSW

logger = get_logger("run_pipeline")


def sample_stream_generator(count: int) -> Iterable[Tuple[str, str]]:
    """Generate sample Vietnamese documents for pipeline ingestion."""
    templates = [
        "Trí tuệ nhân tạo và học máy đang thay đổi cách các doanh nghiệp vận hành.",
        "Nghiên cứu thuật toán láng giềng gần đúng Approximate Nearest Neighbor trên tập dữ liệu lớn.",
        "Hà Nội bước vào mùa thu với tiết trời se lạnh và bầu không khí trong lành.",
        "<p>Tin tức kinh tế: Thị trường chứng khoán ghi nhận phiên tăng điểm mạnh mẽ. Xem thêm tại https://example.com</p>",
        "Tìm kiếm vector ngữ nghĩa kết hợp kỹ thuật nén lượng tử hóa HNSW.",
    ]
    for i in range(count):
        idx = i % len(templates)
        doc_id = f"doc_{i:08d}"
        text = f"{templates[idx]} Bản ghi số {i}."
        yield doc_id, text


def train_ivf_kmeans(vectors: np.ndarray, k: int, max_iters: int = 15) -> np.ndarray:
    """Train coarse IVF centroids using vectorized Euclidean K-Means."""
    n, dim = vectors.shape
    if n <= k:
        repeats = (k // n) + 1
        return np.tile(vectors, (repeats, 1))[:k].astype(np.float32)

    np.random.seed(42)
    init_idx = np.random.choice(n, size=k, replace=False)
    centroids = np.copy(vectors[init_idx])

    for _ in range(max_iters):
        diffs = vectors[:, np.newaxis, :] - centroids[np.newaxis, :, :]
        dists = np.sum(diffs ** 2, axis=2)
        labels = np.argmin(dists, axis=1)

        new_centroids = np.zeros_like(centroids)
        for c in range(k):
            mask = (labels == c)
            if np.any(mask):
                new_centroids[c] = np.mean(vectors[mask], axis=0)
            else:
                new_centroids[c] = vectors[np.random.randint(0, n)]

        if np.allclose(centroids, new_centroids, atol=1e-4):
            break
        centroids = new_centroids

    return centroids.astype(np.float32)


def main():
    parser = argparse.ArgumentParser(description="Run Distributed Sharded IVF-HNSW Pipeline.")
    parser.add_argument("--config", type=str, default="configs/default_pipeline.json", help="Path to PipelineConfig JSON")
    parser.add_argument("--sample-size", type=int, default=1000, help="Number of sample records")
    parser.add_argument("--use-mock-embedder", action="store_true", help="Use MockEmbedder for fast execution")
    parser.add_argument("--num-shards", type=int, default=5, help="Number of IVF shards")
    parser.add_argument("--storage-dir", type=str, default="shards_db", help="Directory for sharded index storage")
    parser.add_argument("--nprobe", type=int, default=3, help="Number of shards to probe in search")
    parser.add_argument("--m-links", type=int, default=16, help="HNSW connectivity M")
    parser.add_argument("--ef-construction", type=int, default=32, help="HNSW ef_construction")
    parser.add_argument("--from-cache", action="store_true", help="Build index from pre-existing search cache if available")
    args = parser.parse_args()

    # 1. Load configuration (Preserving R3)
    if os.path.exists(args.config):
        config = PipelineConfig.from_json(args.config)
        logger.info("Loaded configuration from %s", args.config)
    else:
        config = PipelineConfig()
        logger.info("Using default PipelineConfig")

    config.max_records = max(config.max_records, args.sample_size)
    dim = config.embedding_dim

    # 2. Vector Ingestion (From cache or text stream)
    cache_npz = os.path.join(BASE_DIR, "data", "processed", "search_index_cache.npz")
    vectors = None

    if args.from_cache and os.path.exists(cache_npz):
        logger.info("Loading cached vectors from %s", cache_npz)
        data = np.load(cache_npz)
        vectors = data["vectors"].astype(np.float32)
        dim = vectors.shape[1]
    else:
        # Initialize Embedder
        if args.use_mock_embedder:
            embedder = MockEmbedder(dim=dim)
            logger.info("Initialized MockEmbedder (dim=%d)", dim)
        else:
            try:
                embedder = SentenceTransformerEmbedder(model_name=config.model_name, dim=dim)
                logger.info("Initialized SentenceTransformerEmbedder: %s", config.model_name)
            except Exception as e:
                logger.warning("Could not load neural model (%s). Falling back to MockEmbedder.", str(e))
                embedder = MockEmbedder(dim=dim)

        logger.info("Generating %d sample documents...", args.sample_size)
        stream = list(sample_stream_generator(args.sample_size))
        texts = [text for _, text in stream]

        t0_emb = time.perf_counter()
        batch_size = min(config.batch_size, 256)
        embedded_list = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i : i + batch_size]
            encoded = embedder.encode(chunk)
            embedded_list.append(encoded)
        vectors = np.vstack(embedded_list).astype(np.float32)
        logger.info("Embedded %d vectors in %.2fs", len(vectors), time.perf_counter() - t0_emb)

    total_vectors = len(vectors)
    logger.info("Total vectors available for indexing: %d (dim=%d)", total_vectors, dim)

    # 3. IVF K-Means Clustering
    logger.info("Performing IVF K-Means clustering (K=%d)...", args.num_shards)
    cluster_sample_size = min(total_vectors, 10000)
    sample_indices = np.random.choice(total_vectors, size=cluster_sample_size, replace=False) if total_vectors > cluster_sample_size else np.arange(total_vectors)
    centroids = train_ivf_kmeans(vectors[sample_indices], k=args.num_shards, max_iters=15)
    logger.info("Trained %d cluster centroids successfully.", len(centroids))

    # 4. Construct ShardedIVFHNSW Router & Populate Shards
    storage_path = os.path.abspath(args.storage_dir)
    logger.info("Initializing ShardedIVFHNSW Router at %s", storage_path)
    router = ShardedIVFHNSW(
        dim=dim,
        num_shards=args.num_shards,
        capacity_per_shard=max(total_vectors, 1000),
        storage_dir=storage_path,
        clean_storage=True,
    )
    router.centroids = centroids

    logger.info("Routing and indexing %d vectors across %d shards...", total_vectors, args.num_shards)
    t0_idx = time.perf_counter()
    shard_counts: Dict[int, int] = {i: 0 for i in range(args.num_shards)}

    for i in range(total_vectors):
        assigned_shard = router.route_and_insert(global_id=i, vector=vectors[i])
        shard_counts[assigned_shard] += 1
        if (i + 1) % max(1, total_vectors // 5) == 0 or (i + 1) == total_vectors:
            logger.info("  Indexed %d / %d vectors", i + 1, total_vectors)

    idx_time = time.perf_counter() - t0_idx
    logger.info("Indexing completed in %.2fs. Shard distribution: %s", idx_time, shard_counts)

    # 5. Save Artifacts for search_service.py
    os.makedirs(storage_path, exist_ok=True)
    centroids_file = os.path.join(storage_path, "centroids.npy")
    np.save(centroids_file, router.centroids)

    meta_file = os.path.join(storage_path, "router_metadata.json")
    meta_payload = {
        "dim": dim,
        "num_shards": args.num_shards,
        "total_vectors": total_vectors,
        "shard_distribution": shard_counts,
        "storage_dir": storage_path,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    # Save per-shard state
    for sid, shard in enumerate(router.shards):
        shard_state_file = os.path.join(storage_path, f"shard_{sid}_state.npz")
        np.savez_compressed(
            shard_state_file,
            quantized=shard.quantized[: shard.local_count],
            scales=shard.scales[: shard.local_count],
            offsets=shard.offsets[: shard.local_count],
            id_map_keys=np.array(list(shard.id_map.keys()), dtype=np.int32),
            id_map_values=np.array(list(shard.id_map.values()), dtype=np.int64),
            entry_point=shard.entry_point if shard.entry_point is not None else -1,
            local_count=shard.local_count,
            graph_json=json.dumps(shard.graph),
        )
    logger.info("Saved index artifacts to %s", storage_path)

    # 6. Verification Self-Test
    test_query = vectors[0]
    results, probed = router.distributed_search(query=test_query, top_k=5, nprobe=args.nprobe, return_shards=True)
    logger.info("Pipeline self-test verification:")
    logger.info("  Probed Shards: %s", probed)
    logger.info("  Top Result: global_id=%s, shard=%s, dist=%.6f", results[0][1], results[0][2], results[0][0])
    logger.info("Pipeline executed successfully with zero legacy memmap code.")


if __name__ == "__main__":
    main()
```

---

## 5. Verification Method

To independently verify the refactoring design:

1. **Verify No Legacy Memmap or Monolithic Graph References**:
   Run grep search over `scripts/run_pipeline.py`:
   ```powershell
   grep -n "memmap" scripts/run_pipeline.py
   grep -n "AGYHNSW1" scripts/run_pipeline.py
   ```
   Expected: 0 matches.

2. **Verify Interface and CLI Execution**:
   Run the refactored pipeline with `MockEmbedder` and synthetic samples:
   ```powershell
   python scripts/run_pipeline.py --sample-size 200 --num-shards 4 --use-mock-embedder --storage-dir tests/temp_shards_db
   ```
   Expected:
   - Exits with returncode 0.
   - Outputs `centroids.npy`, `router_metadata.json`, `shard_0.bin`, `shard_0_state.npz`, etc.
   - Self-verification search succeeds with top result having distance $\approx 0$.

3. **Verify Core Index Unit and Stress Tests**:
   Run unittest suite:
   ```powershell
   python -m unittest tests/test_two_tier_hnsw.py tests/test_stress_core_index.py
   ```
   Expected: 28 tests pass (15 in `test_two_tier_hnsw.py` and 13 in `test_stress_core_index.py`).

4. **Verify Preservation of Requirement R3**:
   Inspect `git diff -- configs/default_pipeline.json src/ann_data/` to confirm zero changes made to ingestion configs or loaders.
