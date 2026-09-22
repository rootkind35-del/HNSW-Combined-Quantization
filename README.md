<div align="center">

# HNSW Combined Quantization: Two-Tier Vector Retrieval for Big Data

<p align="center">
  <b>High-throughput, out-of-core approximate nearest neighbor search across 16.45M dense 384-D vectors on commodity hardware.</b>
</p>

<p align="center">
  <a href="#-benchmarks--empirical-results"><img alt="Corpus Scale" src="https://img.shields.io/badge/Scale-16.45M%20Vectors-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-system-architecture"><img alt="RAM Reduction" src="https://img.shields.io/badge/RAM%20Reduction--75%25-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>&nbsp;
  <a href="#-interactive-dashboard"><img alt="Dashboard" src="https://img.shields.io/badge/Live%20Dashboard-Port%203000-0A0A0A?style=for-the-badge&labelColor=F5F5F4" height="34"></a>
</p>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/Node.js-20%2B-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![PyTest Suite](https://img.shields.io/badge/Tests-91%20Passed-brightgreen?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=flat-square)](LICENSE)

<p align="center">
  <a href="README.md"><img alt="English" height="40" src="https://img.shields.io/badge/English-BCDCF7"></a>&nbsp;
  <a href="README_VN.md"><img alt="Tiếng Việt" height="40" src="https://img.shields.io/badge/Tiếng_Việt-CDCFD4"></a>
</p>

[Features](#-key-features) · [Get Started](#-get-started) · [Explore](#-explore-project) · [CLI](#%EF%B8%8F-cli--evaluation-engine) · [Community](#-community)

</div>

---

> 🤝 **We welcome any kinds of contributing!** See our [Contributing Guide](CONTRIBUTING.md) for guidelines, and submit your pull requests on GitHub.

---

### 📦 Releases

> **[2026.09]** [v1.0.0](https://github.com/rootkind35-del/HNSW-Combined-Quantization/releases/tag/v1.0.0) — Major release establishing the full 16.45M Vietnamese News & Legal corpus pipeline, Two-Tier Quantized HNSW index with Adaptive Early-Exit, and Three.js 3D dashboard.

---

## ✨ Key Features

HNSW Combined Quantization resolves the fundamental trade-off between memory footprint, query latency, and retrieval recall for high-dimensional vector search on consumer systems.

- **Two-Tier Memory-Disk Decoupling** — Tier 1 navigates an in-memory scalar-quantized (SQ8 int8) HNSW graph saving 75% RAM, while Tier 2 accesses raw float32 vectors directly from NVMe SSD via zero-copy `numpy.memmap` for exact candidate re-ranking.
- **Adaptive Early-Exit Convergence** — Monitors relative distance delta with saturation counter ($\tau=3$) and tolerance ($\epsilon=10^{-4}$), terminating graph beam search once improvements plateau.
- **Streaming Big Data Pipeline** — Ingests multi-gigabyte text dumps across 400 shards with constant memory usage (< 150 MB RAM) using MinHash LSH deduplication, PyVi compound-word tokenization, and atomic write-ahead checkpointing.
- **Dual Interface & Universal Evaluation Engine** — Exposes an interactive WebGL vector space dashboard alongside an automated evaluation CLI that measures QPS, latency percentiles, and Ground-Truth Recall@K against exact brute-force search.

---

## 🚀 Get Started

The project separates the backend execution API from the interactive frontend visualizer. Index partitions are stored under `data/`, and all evaluation configurations are centrally located in `configs/`.

### Prerequisites

- **Python**: Version 3.11 or higher
- **Node.js**: Version 20 or higher
- **Storage**: At least 15 GB free NVMe SSD disk space for quantized index files

<details open>
<summary><b>Option 1 — Install From Source</b> · Recommended for development</summary>

```bash
git clone git@github.com:rootkind35-del/HNSW-Combined-Quantization.git
cd HNSW-Combined-Quantization

python -m venv .venv
source .venv/bin/activate # Or .venv\Scripts\activate on Windows

pip install -e .
pip install -e ".[ml,dev]"
```

Start the system services:

```bash
# Terminal 1: Python Search Microservice
cd dashboard
python scripts/search_service.py

# Terminal 2: Node.js Dashboard UI
cd dashboard
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

</details>

<details>
<summary><b>Option 2 — Pre-Processed Corpus Setup (Google Drive)</b></summary>

For instant evaluation without crawling 16.45M raw records:

1. Download the pre-processed cache files from Google Drive:
   👉 [Download Corpus Cache](https://drive.google.com/drive/folders/1b2yiq6Ly5cl3VdNW2LuM1EqdaZNdpbPW?usp=sharing)
2. Extract the archive into the `data/processed/` directory.
3. Verify cache integrity:
   ```bash
   python -c "import json; d=json.load(open('data/processed/search_index_metadata.json', encoding='utf-8')); print(f'Loaded {len(d)} clean records')"
   ```

</details>

<details>
<summary><b>Configuration Reference</b> — <code>configs/default_pipeline.json</code></summary>

| Parameter | Type | Default | Description |
|:---|:---|:---|:---|
| `dim` | integer | `384` | Vector dimensionality (Sentence-BERT standard) |
| `max_elements` | integer | `10000000` | Target capacity per index partition |
| `M` | integer | `16` | Maximum outgoing connections per node in HNSW |
| `ef_construction` | integer | `100` | Dynamic candidate list size during graph construction |
| `ef_search` | integer | `32` | Dynamic candidate list size during query traversal |
| `tau` | integer | `3` | Early-exit saturation step count |
| `eps` | float | `0.0001` | Early-exit relative improvement threshold |

</details>

---

## 📖 Explore Project

### 📊 Big Data Specifications

| Dimension | Architectural Specification | Implementation Mechanism |
|:---|:---|:---|
| **Volume** | **16,459,486 dense vectors** (384 dimensions)<br>• Vietnamese News & Legal texts<br>• 24.11 GB raw float32 payload | Compressed to **6.02 GB** on disk using SQ8 int8. Out-of-core memory mapping keeps operational RAM under **8.1 GB**, running comfortably on a standard 16 GB workstation. |
| **Velocity** | **400 processing shards** with streaming ingestion<br>• Query latency $p_{50} = 1.25$ ms<br>• Query throughput up to 1,250 QPS | Batch processing (10,000 vectors/chunk) with automatic disk flushing. Write-ahead checkpointing enables non-blocking resume. |
| **Veracity** | Ground-Truth validated search accuracy<br>• Recall@10 = **95.4%** | Tier 2 exact float32 re-ranking fixes quantization boundary errors, delivering high-accuracy semantic search at production scale. |

### 📈 Benchmarks & Empirical Results

Evaluations conducted on a consumer workstation (Microsoft Windows 11 64-bit, x86_64 AVX2, NVMe SSD).

| Retrieval Algorithm | Storage Paradigm | Memory Footprint | Recall@10 | Mean Latency | Throughput (QPS) | Hardware Viability |
|:---|:---|:---:|:---:|:---:|:---:|:---|
| **Standard HNSW** | In-memory graph + float32 | 64.20 GB | 98.3% | 2.90 ms | 303.7 | OOM on 16GB/32GB PCs |
| **Two-Tier Quantized HNSW** | **SQ8 Graph + SSD Memmap** | **8.10 GB** | **95.4%** | **1.25 ms** | **1,250.0** | **Viable on 16GB PCs** |

### 🖥️ Interactive Dashboard

A full-stack monitoring and exploration web interface built with Express, Three.js, and Tailwind CSS.

```text
Dashboard Tabs:
├── Tab 1: Tim kiem & BigQuery Execution Inspector
│           Real-time semantic search, 4 KPI scorecards (Elapsed/Slot/Bytes),
│           4-stage execution graph (S00→S03), dynamic SQL preview,
│           List/JSON output switcher with Copy JSON
├── Tab 2: Khong gian Vector 3D (Three.js WebGL)
│           3D PCA point cloud, HNSW hop trajectory, hover tooltips,
│           HUD Detail Panel with reasoning badge
├── Tab 3: Danh sach Top-K Tai lieu
│           Ranked result cards sorted desc by similarity score,
│           reasoning badge per result, "View 3D" link
└── Tab 4: Danh gia Thuat toan
            Two-Tier Quantized HNSW vs Standard HNSW comparison charts,
            QPS / Recall / Latency metrics, HNSW hyperparameter tuner
```

---

## ⌨ CLI — Evaluation Engine

The repository provides standalone command-line utilities for query execution, baseline benchmarking, and automated report generation.

<details open>
<summary><b>Universal Retrieval Evaluation Suite</b></summary>

Executes multi-domain queries across Two-Tier Quantized HNSW and Standard HNSW, calculates latency percentiles, QPS, and Recall@K, then outputs formatted Markdown and JSON reports:

```bash
python scripts/run_retrieval_evaluation.py --top-k 5
```

</details>

<details>
<summary><b>Interactive Semantic Search CLI Demo</b></summary>

```bash
# Query the index with mock or live embedding models
python scripts/search_demo.py --use-mock-embedder
```

</details>

<details>
<summary><b>Scalability Stress Test Runner</b></summary>

```bash
# Evaluate performance across increasing vector sizes (N = 1,000 -> 2,500 -> 5,000)
python scripts/run_scale_stress_test.py
```

</details>

---

## 📁 Repository Structure

```text
HNSW-Combined-Quantization/
├── README.md                                # Project overview and quick-start
├── KET_QUA_THUC_HIEN.md                     # Full experimental results report
├── HUONG_DAN_THUC_HIEN.md                   # Step-by-step developer & user guide
├── pyproject.toml                           # Python package configuration and dependencies
├── configs/
│   └── default_pipeline.json                # Pipeline hyperparameters and index limits
├── src/
│   ├── ann_data/                            # Big Data ingestion and storage layer
│   └── ann_index/                           # Core vector indexing algorithms
│       ├── hnsw.py                          # Standard hierarchical graph index
│       ├── quantizer.py                     # Scalar Quantizer (SQ8 uint8/int8)
│       ├── early_exit.py                    # Adaptive Early-Exit convergence controller
│       └── two_tier_hnsw.py                 # Two-Tier Quantized HNSW implementation
├── scripts/                                 # Executable CLI scripts
│   └── run_retrieval_evaluation.py          # Universal retrieval benchmark
├── dashboard/                               # Interactive Web Dashboard
│   ├── server.js                            # Express API backend (port 3000)
│   ├── scripts/search_service.py            # Python search microservice (port 5005)
│   └── public/                              # HTML5, Tailwind CSS, Three.js 3D visualizer
├── docs/                                    # Technical reports and supporting documents
│   └── TECHNICAL_REPORT.md                  # Comprehensive experimental report
└── tests/                                   # Automated verification tests
    ├── test_ui_render_harness.js            # UI render tests (19 cases)
    └── test_adversarial_frontend_stress.js  # Adversarial stress tests (3 cases)
```

---

## 🌐 Community

### 🙏 Acknowledgments

This implementation utilizes concepts and components from:

- **Malkov & Yashunin (2018)**: *Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs*
- **Jégou et al. (2011)**: *Product Quantization for Nearest Neighbor Search* (IEEE TPAMI)
- **HKUDS / DeepTutor**: Structural and visual benchmark layout for open-source technical documentation.
- **PyVi**: Vietnamese tokenization and compound-word segmentation.

<div align="center">

Licensed under the [Apache License 2.0](LICENSE).

<p>
  <img src="https://visitor-badge.laobi.icu/badge?page_id=rootkind35-del.HNSW-Combined-Quantization&style=for-the-badge&color=00d4ff" alt="Views">
</p>

</div>

---

## 📚 Documents

| File | Mô tả |
|:---|:---|
| [KET_QUA_THUC_HIEN.md](KET_QUA_THUC_HIEN.md) | Kết quả thực nghiệm đầy đủ: so sánh thuật toán, latency breakdown, RAM savings, hyperparameter sweep, BigQuery execution telemetry |
| [HUONG_DAN_THUC_HIEN.md](HUONG_DAN_THUC_HIEN.md) | Hướng dẫn cài đặt, chạy dashboard, sử dụng từng tab, API reference, xử lý sự cố |
| [docs/TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md) | Báo cáo kỹ thuật chi tiết: lý thuyết, chứng minh toán học, kết quả thực nghiệm |
| [ann_10m_thesis_report.md](ann_10m_thesis_report.md) | Báo cáo đề tài môn học (tiếng Việt) |
