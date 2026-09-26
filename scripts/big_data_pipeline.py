import os
import argparse
import polars as pl
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
import numpy as np
import json

def run_pipeline(jsonl_shard, vector_bin, q_params, num_samples=50000):
    os.makedirs('assets/figs', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    parquet_path = 'data/processed/shard_00000_optimized.parquet'
    
    print("1. [Polars] Chuyển đổi dữ liệu thô sang Parquet...")
    if not os.path.exists(parquet_path):
        pl_df_raw = pl.read_ndjson(jsonl_shard)
        pl_df_subset = pl_df_raw.select(["doc_id", "title", "token_count", "crawled_at"])
        pl_df_subset.write_parquet(parquet_path)
        print(" -> Đã lưu cache Parquet thành công.")
    else:
        print(" -> Đã tìm thấy Parquet tối ưu, bỏ qua bước build.")
        pl_df_subset = pl.read_parquet(parquet_path)

    print("\n2. [DuckDB] Trích xuất thống kê Database...")
    query = f"""
        SELECT 
            CAST(crawled_at AS DATE) as crawl_date,
            COUNT(*) as doc_count,
            AVG(token_count) as avg_token
        FROM '{parquet_path}'
        GROUP BY crawl_date
        ORDER BY doc_count DESC
        LIMIT 5
    """
    print(duckdb.query(query).df())

    print("\n3. [PCA] Giải nén Vector và vẽ phổ Datashader...")
    dim = 384
    with open(q_params, 'r') as f:
        q_params_data = json.load(f)
    min_vals = np.array(q_params_data['min_vals'], dtype=np.float32)
    scales = np.array(q_params_data['scales'], dtype=np.float32)

    mapped_vectors = np.memmap(vector_bin, dtype=np.uint8, mode='r', shape=(16459486, dim))
    sq8_vectors = mapped_vectors[:num_samples]
    float_vectors = (sq8_vectors.astype(np.float32) * scales) + min_vals
    float_vectors = float_vectors / np.linalg.norm(float_vectors, axis=1, keepdims=True)

    pca = PCA(n_components=2)
    coords = pca.fit_transform(float_vectors)
    
    plt.figure(figsize=(10,6))
    sns.scatterplot(x=coords[:,0], y=coords[:,1], s=5, alpha=0.5, color='indigo')
    plt.title('2D PCA Clusters of Real Vectors')
    plt.savefig('assets/figs/pca_clusters.png', dpi=300)
    plt.close()
    print(" -> Xuất ảnh PCA hoàn tất.")
    print("\n[DONE] Pipeline Big Data đã thực thi xong. Giao diện Database Analytics đã được cập nhật số liệu mới nhất!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chạy luồng xử lý Big Data từ bài học (Polars, DuckDB)")
    parser.add_argument('--jsonl', type=str, default='data/crawl/shard_00000.jsonl')
    parser.add_argument('--vector', type=str, default='data/quantized/vectors_int8.dat')
    parser.add_argument('--qparams', type=str, default='data/quantized/quantization_params.json')
    args = parser.parse_args()
    
    run_pipeline(args.jsonl, args.vector, args.qparams)
