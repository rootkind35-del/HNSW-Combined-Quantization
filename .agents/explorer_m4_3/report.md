# Investigation Report: Backend 3D APIs, 3D UI Integration, Pipeline Integrity, and Configuration Preservation

## Executive Summary
This investigation audits the repository state following the critical mandate to retain and integrate the Three.js 3D visualizer modules (`three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`) alongside the new Distributed Sharded IVF-HNSW backend architecture. All four 3D JavaScript files remain preserved in `dashboard/public/js/` and pass `node -c` syntax compilation with zero errors. The required backend endpoints (`/api/vectors-3d`, `/api/hnsw-topology-3d`) and fallback strategies have been specified to ensure continuous operation without runtime exceptions. `scripts/run_pipeline.py` has been verified to use IVF K-Means clustering and `ShardedIVFHNSW` router integration with zero legacy `memmap` or monolithic graph dependencies. The configuration file `configs/default_pipeline.json` is intact with matching SHA-256 hash.

---

## 1. 3D UI Module Status & Backend API Survey

### 1.1 Existing 3D File Inventory
All 3D assets in `dashboard/public/js/` exist and are valid JavaScript:

| File Path | Size | Role | Syntax Status (`node -c`) |
|---|---|---|---|
| `dashboard/public/js/three_engine.js` | 12,034 bytes | Core Three.js WebGL scene manager, OrbitControls, lighting, billboard text | PASSED |
| `dashboard/public/js/three_vector_space.js` | 18,655 bytes | 3D vector point cloud visualizer, SQ8 bounding cube, focus marker, category filtering | PASSED |
| `dashboard/public/js/three_hnsw_graph.js` | 14,904 bytes | Multi-layer HNSW topology (L0, L1, L2), intra-layer edges, inter-layer jump links | PASSED |
| `dashboard/public/js/three_pipeline_3d.js` | 10,206 bytes | Isometric cyber-pipeline architecture pods with animated photon streams | PASSED |
| `dashboard/scripts/dimension_reduction_3d.py` | 16,887 bytes | Offline PCA/SVD 384D -> 3D projection script & HNSW topology generator | SYNTAX VALID |

### 1.2 Required Backend Endpoints (`dashboard/server.js`)
The 3D frontend modules communicate with two primary GET endpoints:

#### Endpoint 1: `GET /api/vectors-3d`
- **Consumer**: `VectorSpaceModule.loadVectorsData()` (`three_vector_space.js:116-128`).
- **Expected Payload Structure**:
  ```json
  {
    "success": true,
    "count": 3000,
    "source": "data/processed/search_index_cache.npz (5,000 vectors)",
    "bounds": { "min": -45.0, "max": 45.0 },
    "vectors": [
      {
        "id": "doc_0",
        "index": 0,
        "x": 12.34,
        "y": -5.67,
        "z": 8.91,
        "title": "Document Title",
        "preview": "Document text snippet...",
        "category": "Kinh doanh & Tài chính",
        "token_count": 150
      }
    ]
  }
  ```
- **Error Behavior**: If this endpoint returns 404 HTML, `fetch().then(res => res.json())` throws a `SyntaxError: Unexpected token '<'` in the browser console. If it returns `{ success: true, count: 0, vectors: [] }`, `buildPointCloud()` executes an early return (`if (count === 0) return;`), rendering an empty space without points.

#### Endpoint 2: `GET /api/hnsw-topology-3d`
- **Consumer**: `HnswGraphModule.loadTopology()` (`three_hnsw_graph.js:27-37`).
- **Expected Payload Structure**:
  ```json
  {
    "success": true,
    "topology": {
      "layers": [
        { "level": 2, "name": "Layer 2: Top Sparse Navigation Tier", "y": 28.0, "nodes": [ ... ] },
        { "level": 1, "name": "Layer 1: Intermediate Routing Tier", "y": 0.0, "nodes": [ ... ] },
        { "level": 0, "name": "Layer 0: Dense Base Graph Tier", "y": -28.0, "nodes": [ ... ] }
      ],
      "intra_edges": [
        { "from": "l0_doc_0", "to": "l0_doc_1", "layer": 0, "type": "intra" }
      ],
      "inter_links": [
        { "from": "l1_doc_0", "to": "l0_doc_0", "type": "inter" }
      ],
      "entry_point_id": "l2_doc_0",
      "stats": {
        "total_nodes_l2": 48,
        "total_nodes_l1": 240,
        "total_nodes_l0": 1200,
        "total_edges": 4500
      }
    }
  }
  ```
- **Error Behavior**: If this endpoint returns 404 HTML, `res.json()` throws a SyntaxError. If it returns `{ success: true, topology: {} }`, `buildHnswScene()` exits early (`if (!this.topology || !this.topology.layers) return;`), resulting in a blank scene.

---

## 2. Fallback Data Generator Strategy

`data/processed/vectors_3d_cache.json` does not exist on disk in fresh checkouts. To prevent blank canvas views or network errors, `dashboard/server.js` requires an in-memory fallback generator when `vectors_3d_cache.json` is missing:

### 2.1 Proposed In-Memory Generator Specification (`server.js`)
```javascript
function getFallback3DData() {
  const categories = [
    "Khoa học & Công nghệ",
    "Kinh doanh & Tài chính",
    "Y tế & Sức khỏe",
    "Giáo dục",
    "Giao thông & Xây dựng",
    "Văn hóa & Đời sống"
  ];

  // 1. Generate 240 clustered 3D points
  const vectors = [];
  const clusterCenters = [
    { x: -20, y: 10, z: -15 },
    { x: 20, y: -10, z: 15 },
    { x: -15, y: -15, z: 20 },
    { x: 15, y: 15, z: -20 },
    { x: 0, y: 0, z: 0 },
    { x: 25, y: -5, z: -10 }
  ];

  for (let i = 0; i < 240; i++) {
    const cIdx = i % clusterCenters.length;
    const center = clusterCenters[cIdx];
    const x = center.x + (Math.random() - 0.5) * 16;
    const y = center.y + (Math.random() - 0.5) * 16;
    const z = center.z + (Math.random() - 0.5) * 16;
    const cat = categories[cIdx];
    vectors.push({
      id: `doc_sample_${i}`,
      index: i,
      x: parseFloat(x.toFixed(2)),
      y: parseFloat(y.toFixed(2)),
      z: parseFloat(z.toFixed(2)),
      title: `Tài liệu Vector phân tán #${i + 1} (${cat})`,
      preview: `Đoạn trích dẫn thông tin mô phỏng cho điểm vector #${i + 1} thuộc cụm ${cat}.`,
      category: cat,
      token_count: 120 + (i % 80)
    });
  }

  // 2. Generate multi-layer HNSW topology
  const l2_nodes = [];
  const l1_nodes = [];
  const l0_nodes = [];

  vectors.slice(0, 120).forEach((v, idx) => {
    const baseNode = {
      id: `l0_${v.id}`,
      doc_id: v.id,
      orig_index: idx,
      layer: 0,
      x: v.x,
      y: -28.0,
      z: v.z,
      title: v.title,
      category: v.category
    };
    l0_nodes.push(baseNode);

    if (idx % 4 === 0) {
      l1_nodes.push({
        id: `l1_${v.id}`,
        doc_id: v.id,
        orig_index: idx,
        layer: 1,
        x: parseFloat((v.x * 0.85).toFixed(2)),
        y: 0.0,
        z: parseFloat((v.z * 0.85).toFixed(2)),
        title: v.title,
        category: v.category
      });
    }

    if (idx % 16 === 0) {
      l2_nodes.push({
        id: `l2_${v.id}`,
        doc_id: v.id,
        orig_index: idx,
        layer: 2,
        x: parseFloat((v.x * 0.7).toFixed(2)),
        y: 28.0,
        z: parseFloat((v.z * 0.7).toFixed(2)),
        title: v.title,
        category: v.category
      });
    }
  });

  const intra_edges = [];
  const inter_links = [];

  function linkLayer(nodes, maxDegree) {
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < Math.min(i + maxDegree + 1, nodes.length); j++) {
        intra_edges.push({ from: nodes[i].id, to: nodes[j].id, layer: nodes[i].layer, type: "intra" });
      }
    }
  }
  linkLayer(l2_nodes, 2);
  linkLayer(l1_nodes, 3);
  linkLayer(l0_nodes, 3);

  l2_nodes.forEach(n2 => {
    const n1 = l1_nodes.find(x => x.doc_id === n2.doc_id);
    if (n1) inter_links.push({ from: n2.id, to: n1.id, type: "inter" });
  });
  l1_nodes.forEach(n1 => {
    const n0 = l0_nodes.find(x => x.doc_id === n1.doc_id);
    if (n0) inter_links.push({ from: n1.id, to: n0.id, type: "inter" });
  });

  const hnsw_topology = {
    layers: [
      { level: 2, name: "Layer 2: Top Sparse Navigation Tier", y: 28.0, nodes: l2_nodes },
      { level: 1, name: "Layer 1: Intermediate Routing Tier", y: 0.0, nodes: l1_nodes },
      { level: 0, name: "Layer 0: Dense Base Graph Tier", y: -28.0, nodes: l0_nodes }
    ],
    intra_edges,
    inter_links,
    entry_point_id: l2_nodes[0]?.id || "l0_doc_sample_0",
    stats: {
      total_nodes_l2: l2_nodes.length,
      total_nodes_l1: l1_nodes.length,
      total_nodes_l0: l0_nodes.length,
      total_edges: intra_edges.length + inter_links.length
    }
  };

  return { count: vectors.length, source: "In-Memory Dynamic Fallback", bounds: { min: -45.0, max: 45.0 }, vectors, hnsw_topology };
}
```

### 2.2 Endpoint Integration in `server.js`
With this generator in place, `/api/vectors-3d` and `/api/hnsw-topology-3d` first check `data/processed/vectors_3d_cache.json`. If the file is absent, they invoke `getFallback3DData()`. The client receives structured data instantly without disk I/O failure or network error.

---

## 3. Frontend Wiring Requirements (`index.html` & `app.js`)

To make the 3D UI visible and active without interfering with search metrics (Shard IDs hit, probed shards, latency):

### 3.1 CDN Dependencies (`index.html` `<head>`)
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
```

### 3.2 Navigation Bar Tab Button (`index.html`)
The navigation tab bar includes a dedicated button for the 3D engine:
```html
<button onclick="switchTab('tab-3d-visualizer')" id="btn-tab-3d-visualizer" class="tab-btn px-4 py-3.5 text-[13px] sm:text-[18px] font-medium text-slate-400 hover:text-slate-200 transition-all duration-150 flex items-center gap-2">
  <i class="fa-solid fa-cube text-sky-400"></i> Không gian 3D WebGL
</button>
```

### 3.3 3D Viewport Markup (`index.html`)
The container section `#tab-3d-visualizer` contains `#threejs-viewport-container` and `#threejs-canvas-wrapper`, HUD tooltips, and mode buttons (Universe, HNSW, Pipeline).

### 3.4 Script Inclusions (`index.html` footer)
```html
<script src="js/three_engine.js"></script>
<script src="js/three_vector_space.js"></script>
<script src="js/three_hnsw_graph.js"></script>
<script src="js/three_pipeline_3d.js"></script>
<script src="js/architecture.js"></script>
<script src="js/charts.js"></script>
<script src="js/app.js"></script>
```

### 3.5 App Controller Integration (`app.js`)
- `switchTab(tabId)` initializes `ThreeEngine` on first visit to `tab-3d-visualizer` and calls `threeEngine.onWindowResize()`.
- Search query coordination: `search_bridge.py` and `search_service.py` return `query_3d` coordinates (`{x, y, z}`) along with `shards_probed` and `shard_id`.
- When search results are returned:
  * `renderSearchResults(data)` renders shard badges (`#result-shards-container`), execution latency (`#result-latency`), and result cards with Shard IDs (`Shard #X`).
  * If `window.threeEngine` is active, it calls `vectorSpaceModule.renderQueryResults(data.query, data.query_3d, data.results)`.
  * `focusOn3DResult(x, y, z, ...)` allows clicking "Xem trên 3D" from result cards to fly the camera to that node.

---

## 4. Pipeline Refactoring Audit (`scripts/run_pipeline.py`)

Verification of `scripts/run_pipeline.py` against user requirements:

1. **IVF K-Means Clustering**:
   - `train_ivf_kmeans(vectors, k, max_iters=15)` implements vectorized Euclidean distance matrix calculations (`x_norm_sq - 2*(X @ C.T) + c_norm_sq`).
   - Assigns trained centroids to `router.centroids = centroids`.
2. **ShardedIVFHNSW Router Integration**:
   - Imports `from ann_index.two_tier_hnsw import ShardedIVFHNSW`.
   - Initializes router with storage path, dimensions, shard count, and clean storage flag.
   - Iterates through dataset calling `router.route_and_insert(global_id=i, vector=vectors[i])`.
   - Persists per-shard states to `shard_{sid}_state.npz` (`quantized`, `scales`, `offsets`, `id_map`, `entry_point`, `graph_json`).
   - Executes self-test query via `router.distributed_search(...)`.
3. **Absence of Legacy Code**:
   - Legacy `with DataPipeline(config=config, embedder=embedder) as pipeline:` removed.
   - Legacy `--output-memmap` argument removed.
   - Grep search for `memmap` returns zero occurrences in executable code (one log statement affirms zero legacy code).
   - Grep search for `monolithic` returns zero occurrences.
4. **Smoke Execution Result**:
   - Command: `python scripts/run_pipeline.py --sample-size 50 --use-mock-embedder --num-shards 3 --storage-dir test_smoke_shards`
   - Output: 50 vectors indexed across 3 shards in 0.02 seconds, distributed search self-test probed `[1, 0, 2]`, exit code 0.

---

## 5. Preserved Configuration Audit (`configs/default_pipeline.json`)

Requirement R3 states that existing dataset structure and data loading configurations must remain unaltered.

### 5.1 Integrity Verification
- Path: `configs/default_pipeline.json`
- Git Status: Clean (`nothing to commit, working tree clean`)
- SHA-256 Hash: `678C17BDF5013DFE648CB5ED4BEC91CE5B07209C5D75B1E8295D8CF45014EFDF`
- File Structure:
  ```json
  {
    "model_name": "paraphrase-multilingual-MiniLM-L12-v2",
    "embedding_dim": 384,
    "batch_size": 2048,
    "max_records": 10000000,
    "output_memmap_path": "data/processed/vectors_10m.dat",
    "dtype": "float32",
    "minhash_threshold": 0.8,
    "minhash_num_perm": 128,
    "strip_html_tags": true,
    "normalize_unicode_nfc": true,
    "remove_urls": true,
    "lowercase_tokens_for_dedup": true
  }
  ```
All 12 parameter keys remain preserved.

---

## 6. Verification Test Command Suite

The complete verification test battery includes unit, integration, syntax, and adversarial checks:

### 6.1 Core Algorithm & Sharding Pytest Suite
```bash
python -s -m pytest tests/test_two_tier_hnsw.py tests/test_stress_core_index.py tests/test_search_edge_cases.py tests/test_adversarial_lru_concurrency.py tests/test_storage.py tests/test_cleaner.py tests/test_quantizer_pipeline.py -q
```
- **Verified Status**: 77 passed in 23.33 seconds (exit code 0).
- **Note on `python -s`**: The `-s` flag isolates execution from user-level Python packages (preventing conflicts with global `langsmith` plugins on Python 3.14).

### 6.2 Extended Pytest Ingestion Suite
```bash
python -s -m pytest --ignore=tests/test_deduplicator.py --ignore=tests/test_large_scale_stream.py --ignore=tests/test_loader_integration.py --ignore=tests/test_pipeline.py --ignore=tests/test_crawler_pipeline.py --ignore=tests/test_tokenizer.py -q
```
- **Verified Status**: 130+ tests passed. (Ignored tests depend on optional external modules `datasketch` and `datasets` or `pyvi`).

### 6.3 JavaScript Syntax Audit
```bash
node -c dashboard/server.js dashboard/public/js/app.js dashboard/public/js/charts.js dashboard/public/js/architecture.js dashboard/public/js/three_engine.js dashboard/public/js/three_hnsw_graph.js dashboard/public/js/three_pipeline_3d.js dashboard/public/js/three_vector_space.js
```
- **Verified Status**: 8 files verified with 0 syntax errors.

### 6.4 UI Render Adversarial Test Harness
```bash
node tests/test_ui_render_harness.js
```
- **Verified Status**: 14 core tests passed, verifying that Shard IDs hit, probed shards array, and micro-second latency correctly populate DOM elements without NaN leaks.

### 6.5 Pipeline End-to-End Smoke Test
```bash
python scripts/run_pipeline.py --sample-size 50 --use-mock-embedder --num-shards 3 --storage-dir test_smoke_shards
```
- **Verified Status**: Executes in 0.02 seconds with complete shard artifact generation and self-test distributed search.

### 6.6 CLI Search Bridge Smoke Test
```bash
python dashboard/scripts/search_bridge.py --query "tri tue nhan tao" --top-k 3 --algorithm two_tier
```
- **Verified Status**: Emits valid JSON containing `shards_probed`, individual result `shard_id`, and `query_3d` coordinates.

---

## 7. Actionable Recommendations for Implementation
1. **Preserve and Restore 3D UI in `dashboard/server.js`**: Implement the fallback data generator so `/api/vectors-3d` and `/api/hnsw-topology-3d` return complete visual structures even when `vectors_3d_cache.json` is missing.
2. **Re-integrate 3D Markup & CDN in `dashboard/public/index.html`**: Retain Three.js script tags, the 3D visualizer navigation tab button, and the 3D viewport canvas wrapper.
3. **Wire 3D Event Handlers in `dashboard/public/js/app.js`**: Ensure `switchTab('tab-3d-visualizer')` initializes the 3D engine, and `renderSearchResults` passes `query_3d` to `vectorSpaceModule.renderQueryResults` without disturbing Shard ID badges or latency displays.
