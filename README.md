<div align="center">

# Two-Tier Quantized HNSW: Billion-Scale Vector Search

<p align="center">
  <a href="README.md"><img alt="English" height="40" src="https://img.shields.io/badge/English-BCDCF7"></a>&nbsp;
  <a href="README_VN.md"><img alt="Tiếng Việt" height="40" src="https://img.shields.io/badge/Tiếng_Việt-CDCFD4"></a>
</p>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

[Features](#-key-features) · [Get Started](#-get-started) · [Explore](#-explore) · [API](#%EF%B8%8F-api)

</div>

---

> 🤝 **We welcome any kinds of contributing!** See our [Contributing Guide](CONTRIBUTING.md) for guidelines and coding standards.

---

## ✨ Key Features

Two-Tier Quantized HNSW is an optimized Approximate Nearest Neighbor (ANN) search architecture designed to break the memory wall of traditional HNSW for billion-scale vector databases.

- **SQ8 Quantization** — Compresses 384-dimensional float32 vectors into 8-bit integers, reducing memory footprint by ~75%.
- **Two-Tier Architecture** — Separates fast graph routing (in RAM) from exact distance verification (on SSD).
- **Adaptive Early-Exit** — Intelligently terminates graph traversal early when convergence is detected, drastically boosting QPS.
- **Direct I/O Storage** — Bypasses OS memory mapping (`mmap`) to read candidate vectors directly from SSD, eliminating Out-Of-Memory (OOM) crashes.

---

## 🚀 Get Started

The project separates the runtime state from the data index. Vector storage is managed under `shards_db/`, while configuration resides in `configs/`.

<details>
<summary><b>Option 1 — Install From Source</b> · Recommended local installation</summary>

Requires **Python 3.11+** and **Node.js 20+** (for the Dashboard).

```bash
git clone https://github.com/USER/HNSW_NEW.git
cd HNSW_NEW

# Backend Setup
python -m venv.venv
source.venv/bin/activate  # On Windows:.\.venv\Scripts\Activate.ps1
pip install -e.

# Launch Search Service
python dashboard/scripts/search_service.py
```

Open a new terminal for the Frontend:

```bash
cd dashboard
npm install
node server.js
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000) in your browser.

</details>

<details>
<summary><b>Configuration Reference</b> — Pipeline configuration under <code>configs/</code></summary>

| File | Purpose |
|:---|:---|
| `default_pipeline.json` | Vector dimensionality, target dataset size (e.g., 10M, 16.45M) |
| `tuning_pareto_results.json` | Hyperparameter search results for Early-Exit ($\tau, \epsilon$) |

</details>

---

## 📖 Explore

<details>
<summary><b>📊 Performance Metrics — Technical Deep Dive</b></summary>

<div align="center">
<img src="assets/figs/perf_latency_qps.png" alt="Latency and QPS Performance" width="600">
</div>

The architecture maintains a flat, logarithmic latency scaling curve. At the 16.45M scale, queries return in just **3.6 ms**. Standard HNSW crashes (OOM) at this scale due to exhausting 25GB of RAM, whereas our SQ8 Direct I/O architecture only consumes **65 MB**.

</details>

---

## ⌨ API

The backend is built for agent-native and programmatic REST API integration.

<details>
<summary><b>Search Service API</b></summary>

```bash
# Query the backend
curl -X POST http://localhost:5005/search \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5, "ef_search": 40}'
```

Returns structured JSON containing `distance`, `shard_id`, and `doc_id`.

</details>

---

## 🌐 Community

### 🔗 Maintainers

Project developed by the HNSW Research Team.

### 🙏 Appreciation

This project builds upon the foundational HNSW algorithm and draws architectural inspiration from modern vector databases like Milvus and Qdrant.

<div align="center">
Licensed under the [MIT License](LICENSE).
</div>
