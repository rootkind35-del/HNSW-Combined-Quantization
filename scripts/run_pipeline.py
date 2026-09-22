"""Pipeline execution script for Distributed Sharded IVF-HNSW vector search."""

import argparse
import json
import os
import sys
import time
from typing import Dict, Iterable, Tuple
import numpy as np

# Add src/ to sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from ann_data.config import PipelineConfig  # noqa: E402
from ann_data.embedder import (  # noqa: E402
    MockEmbedder,
    SentenceTransformerEmbedder,
)
from ann_data.utils import get_logger  # noqa: E402
from ann_index.two_tier_hnsw import ShardedIVFHNSW  # noqa: E402

logger = get_logger("run_pipeline")


def sample_stream_generator(count: int) -> Iterable[Tuple[str, str]]:
    """Generate sample Vietnamese documents for pipeline ingestion."""
    templates = [
        "Trí tuệ nhân tạo và học máy đang thay đổi vận hành doanh nghiệp.",
        "Nghiên cứu thuật toán láng giềng gần đúng ANN trên tập dữ liệu lớn.",
        "Hà Nội bước vào mùa thu với tiết trời se lạnh và trong lành.",
        "<p>Tin kinh tế: Thị trường chứng khoán ghi nhận phiên tăng điểm.</p>",
        "Tìm kiếm vector ngữ nghĩa kết hợp kỹ thuật nén lượng tử hóa HNSW.",
    ]
    for i in range(count):
        idx = i % len(templates)
        doc_id = f"doc_{i:08d}"
        text = f"{templates[idx]} Bản ghi số {i}."
        yield doc_id, text


def train_ivf_kmeans(
    vectors: np.ndarray,
    k: int,
    max_iters: int = 15,
) -> np.ndarray:
    """Train coarse IVF centroids using vectorized Euclidean K-Means."""
    n, dim = vectors.shape
    if n <= k:
        repeats = (k // n) + 1
        return np.tile(vectors, (repeats, 1))[:k].astype(np.float32)

    np.random.seed(42)
    init_idx = np.random.choice(n, size=k, replace=False)
    centroids = np.copy(vectors[init_idx]).astype(np.float32)

    x_norm_sq = np.sum(vectors ** 2, axis=1, keepdims=True)

    for _ in range(max_iters):
        c_norm_sq = np.sum(centroids ** 2, axis=1, keepdims=True).T
        dists = x_norm_sq - 2.0 * (vectors @ centroids.T) + c_norm_sq
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
    parser = argparse.ArgumentParser(
        description="Run Distributed Sharded IVF-HNSW Pipeline."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="configs/default_pipeline.json",
        help="Path to PipelineConfig JSON",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=1000,
        help="Number of sample records",
    )
    parser.add_argument(
        "--use-mock-embedder",
        action="store_true",
        help="Use MockEmbedder for fast execution",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=5,
        help="Number of IVF shards",
    )
    parser.add_argument(
        "--storage-dir",
        type=str,
        default="shards_db",
        help="Directory for sharded index storage",
    )
    parser.add_argument(
        "--nprobe",
        type=int,
        default=3,
        help="Number of shards to probe in search",
    )
    parser.add_argument(
        "--m-links",
        type=int,
        default=16,
        help="HNSW connectivity M",
    )
    parser.add_argument(
        "--ef-construction",
        type=int,
        default=32,
        help="HNSW ef_construction",
    )
    parser.add_argument(
        "--from-cache",
        action="store_true",
        help="Build index from pre-existing search cache if available",
    )
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
    cache_npz = os.path.join(
        BASE_DIR, "data", "processed", "search_index_cache.npz"
    )
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
                embedder = SentenceTransformerEmbedder(
                    model_name=config.model_name,
                    dim=dim,
                )
                logger.info(
                    "Initialized SentenceTransformerEmbedder: %s",
                    config.model_name,
                )
            except Exception as e:
                logger.warning(
                    "Could not load neural model (%s). Fallback.",
                    str(e),
                )
                embedder = MockEmbedder(dim=dim)

        logger.info("Generating %d sample documents...", args.sample_size)
        stream = list(sample_stream_generator(args.sample_size))
        texts = [text for _, text in stream]

        t0_emb = time.perf_counter()
        batch_size = min(config.batch_size, 256)
        embedded_list = []
        for i in range(0, len(texts), batch_size):
            chunk = texts[i:i + batch_size]
            encoded = embedder.encode(chunk)
            embedded_list.append(encoded)
        if embedded_list:
            vectors = np.vstack(embedded_list).astype(np.float32)
        else:
            vectors = np.empty((0, dim), dtype=np.float32)
        logger.info(
            "Embedded %d vectors in %.2fs",
            len(vectors),
            time.perf_counter() - t0_emb,
        )

    total_vectors = len(vectors)
    logger.info(
        "Total vectors available for indexing: %d (dim=%d)",
        total_vectors,
        dim,
    )

    # 3. IVF K-Means Clustering
    logger.info("Running IVF K-Means (K=%d)...", args.num_shards)
    cluster_sample_size = min(total_vectors, 10000)
    if total_vectors > cluster_sample_size:
        sample_indices = np.random.choice(
            total_vectors,
            size=cluster_sample_size,
            replace=False,
        )
    else:
        sample_indices = np.arange(total_vectors)

    centroids = train_ivf_kmeans(
        vectors[sample_indices],
        k=args.num_shards,
        max_iters=15,
    )
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

    logger.info(
        "Routing and indexing %d vectors across %d shards...",
        total_vectors,
        args.num_shards,
    )
    t0_idx = time.perf_counter()
    shard_counts: Dict[int, int] = {i: 0 for i in range(args.num_shards)}

    log_step = max(1, total_vectors // 5)
    for i in range(total_vectors):
        assigned_shard = router.route_and_insert(
            global_id=i,
            vector=vectors[i],
        )
        shard_counts[assigned_shard] += 1
        if (i + 1) % log_step == 0 or (i + 1) == total_vectors:
            logger.info("  Indexed %d / %d vectors", i + 1, total_vectors)

    idx_time = time.perf_counter() - t0_idx
    logger.info(
        "Indexing completed in %.2fs. Shard distribution: %s",
        idx_time,
        shard_counts,
    )

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
        id_keys = np.array(list(shard.id_map.keys()), dtype=np.int32)
        id_vals = np.array(list(shard.id_map.values()), dtype=np.int64)
        ep = shard.entry_point if shard.entry_point is not None else -1
        np.savez_compressed(
            shard_state_file,
            quantized=shard.quantized[: shard.local_count],
            scales=shard.scales[: shard.local_count],
            offsets=shard.offsets[: shard.local_count],
            id_map=json.dumps(shard.id_map),
            id_map_keys=id_keys,
            id_map_values=id_vals,
            entry_point=ep,
            local_count=shard.local_count,
            graph_json=json.dumps(shard.graph),
        )
    logger.info("Saved index artifacts to %s", storage_path)

    # 6. Verification Self-Test
    if total_vectors > 0:
        test_query = vectors[0]
        results, probed = router.distributed_search(
            query=test_query,
            top_k=5,
            nprobe=args.nprobe,
            return_shards=True,
        )
        logger.info("Pipeline self-test verification:")
        logger.info("  Probed Shards: %s", probed)
        if results:
            logger.info(
                "  Top Result: global_id=%s, shard=%s, dist=%.6f",
                results[0][1],
                results[0][2],
                results[0][0],
            )
        else:
            logger.warning("  No search results returned in self-test.")
    logger.info("Pipeline executed successfully with zero legacy memmap code.")


if __name__ == "__main__":
    main()
