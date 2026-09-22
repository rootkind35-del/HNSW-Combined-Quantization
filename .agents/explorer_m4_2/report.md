# Technical Analysis: 3D UI Architecture, Historical Wiring, and Clean Integration Guide

## 1. Executive Summary

This investigation surveys the frontend codebase in `dashboard/public/` and `dashboard/scripts/` to determine the historical architecture of the 3D WebGL visualizers (`three_engine.js`, `three_vector_space.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, and `dimension_reduction_3d.py`) and formulate a concrete plan to preserve, restore, and integrate them with the new Distributed Sharded IVF-HNSW backend.

The user mandate explicitly supersedes earlier cleanup instructions that sought to remove 3D assets:
> "The user has requested to KEEP and INTEGRATE the 3D UI files (`three_engine.js`, `three_hnsw_graph.js`, etc.) instead of deleting them. DO NOT delete any 3D UI files. Instead, make sure they are preserved and properly wired to the new backend if necessary. Update your acceptance criteria and audit to expect the 3D UI to be present and functional."

All core 3D files remain on disk in `dashboard/public/js/` and `dashboard/scripts/`. The previous commit (`1401398`) had them wired through Three.js r128, OrbitControls, and GSAP. Reintegration requires restoring the CDN links, navigation tab, HTML markup section, CSS classes, Express endpoints (`/api/vectors-3d` and `/api/hnsw-topology-3d`), and `app.js` controller functions, while keeping all search routing metrics (`shards_probed`, execution latency, micro-latency, shard IDs, node IDs) intact.

---

## 2. Inventory of 3D Assets and Current Status

| File Path | Status on Disk | Functionality & Scope |
|---|---|---|
| `dashboard/public/js/three_engine.js` | Present (332 lines) | Core 3D engine manager: scene, camera, renderer, OrbitControls, ambient & directional lighting, base grid, billboard text generator, window resize, mouse raycaster, mode switching, GSAP camera tweening. |
| `dashboard/public/js/three_vector_space.js` | Present (500 lines) | 3D point cloud: per-category color coding, glossy node textures, SQ8 3D bounding box / quantization grid, hover reticle & tooltip, query beacon, laser line projections to Top-K nearest neighbors. |
| `dashboard/public/js/three_hnsw_graph.js` | Present (387 lines) | Hierarchical HNSW graph: 3 layered physical glass planes (Layer 2 at y=28, Layer 1 at y=0, Layer 0 at y=-28), entry point halo, intra-layer edges, inter-layer dashed links, animated photon routing simulation, early-exit banner. |
| `dashboard/public/js/three_pipeline_3d.js` | Present (285 lines) | Futuristic cyber-pipeline architecture: 7 hardware server pods with glowing energy reactors, particle conduits, live photon streams, and billboard annotations. |
| `dashboard/scripts/dimension_reduction_3d.py` | Present (387 lines) | Offline dimensionality reduction: PCA/SVD projection of 384-D vectors to 3D space, generates 3-tier HNSW topology (~1,200 nodes in Layer 0, ~240 in Layer 1, ~50 in Layer 2), outputs `vectors_3d_cache.json`. |
| `dashboard/scripts/build_search_cache.py` | Present (352 lines) | Index cache builder: extracts vectors, computes PCA projection, generates `search_index_cache.npz`, `search_index_metadata.json`, and `vectors_3d_cache.json`. |
| `dashboard/public/index.html` | Modified in working copy | CDN script tags, 3D tab button, 3D viewport markup, and script tags were removed. Search routing metrics in `tab-search` were added. |
| `dashboard/public/js/app.js` | Modified in working copy | 3D event controllers removed; search routing metrics rendering (`shards_probed`, `micro_latency`, card shard badges) added. |
| `dashboard/public/css/custom.css` | Modified in working copy | 34 lines of 3D styling (`.mode-btn-3d.active`, `#hud-tooltip-3d`, `.threejs-fullscreen`) removed. |
| `dashboard/server.js` | Modified in working copy | Express endpoints `/api/vectors-3d` and `/api/hnsw-topology-3d` removed. Search route updated to router execution flow. |

---

## 3. Historical 3D Wiring Architecture

Investigation of git commit `1401398` reveals how the 3D subsystems interacted:

### 3.1 External CDN Dependencies
In `<head>` of `index.html`:
```html
<!-- Three.js CDN & OrbitControls -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
```
- `three.min.js`: Three.js revision 128 providing scene graph, shaders, materials, and renderer.
- `OrbitControls.js`: Camera rotation, pan, and zoom interactions.
- `gsap.min.js`: Camera interpolation (`gsap.to`) for smooth focal transitions when clicking nodes or switching camera presets.

### 3.2 Script Execution Order
At the closing `</body>` tag of `index.html`:
```html
<script src="js/three_engine.js"></script>
<script src="js/three_vector_space.js"></script>
<script src="js/three_hnsw_graph.js"></script>
<script src="js/three_pipeline_3d.js"></script>
<script src="js/architecture.js"></script>
<script src="js/charts.js"></script>
<script src="js/app.js"></script>
```
Script order is strict:
1. `three_engine.js` creates `window.ThreeEngine`.
2. `three_vector_space.js` creates `window.VectorSpaceModule`.
3. `three_hnsw_graph.js` creates `window.HnswGraphModule`.
4. `three_pipeline_3d.js` creates `window.Pipeline3DModule`.
5. `app.js` runs `init3DEngine()` to instantiate and attach all modules to `window.threeEngine`.

### 3.3 Backend API Endpoints
`dashboard/server.js` exposed two dedicated read endpoints:
- `GET /api/vectors-3d`: Reads `data/processed/vectors_3d_cache.json` and returns:
  ```json
  {
    "success": true,
    "count": 5000,
    "source": "data/processed/search_index_cache.npz",
    "bounds": { "min": -45.0, "max": 45.0 },
    "vectors": [
      {
        "id": "doc_0",
        "index": 0,
        "x": 12.34, "y": -5.67, "z": 8.90,
        "title": "Document title",
        "preview": "Document snippet...",
        "category": "Kinh doanh & Tài chính",
        "token_count": 280
      }
    ]
  }
  ```
- `GET /api/hnsw-topology-3d`: Reads `data/processed/vectors_3d_cache.json` and returns:
  ```json
  {
    "success": true,
    "topology": {
      "layers": [
        { "level": 2, "name": "Layer 2", "y": 28.0, "nodes": [...] },
        { "level": 1, "name": "Layer 1", "y": 0.0, "nodes": [...] },
        { "level": 0, "name": "Layer 0", "y": -28.0, "nodes": [...] }
      ],
      "entry_point_id": "l2_node_0",
      "intra_edges": [ { "from": "l0_node_0", "to": "l0_node_5", "layer": 0 } ],
      "inter_links": [ { "from": "l2_node_0", "to": "l1_node_0" } ],
      "stats": { "total_nodes_l0": 1200, "total_nodes_l1": 240, "total_nodes_l2": 50, "total_edges": 4500 }
    }
  }
  ```

### 3.4 Runtime Search Integration Flow
When a user submits a query:
1. `POST /api/search` executes through `search_service.py` (or `search_bridge.py` fallback).
2. The search service routes vectors via `ShardedIVFHNSW.distributed_search()`.
3. The response contains both routing metrics (`shards_probed`, `latency_ms`, `micro_latency`) and candidate results with projected coordinates (`coords_3d`: `{x, y, z}`).
4. `render3DSearchResults(data)` in `app.js`:
   - Updates 3D KPI cards (latency, visited nodes, early-exit status, query coordinates).
   - Renders candidate cards in `#search-results-list-3d`.
   - Calls `window.threeEngine.vectorSpaceModule.renderQueryResults(query, query_3d, results)`, which spawns the dynamic query beacon and projects laser lines to the top-K nodes in 3D space.
   - If in `hnsw` mode, triggers `window.threeEngine.hnswModule.startRoutingSimulation(useEarlyExit)`.

---

## 4. Search Routing Metrics Preservation Verification

The working copy contains essential improvements in `dashboard/public/index.html` and `dashboard/public/js/app.js` for Milestone 2:
1. **Global Shards Probed Badge**:
   Container `#result-shards-container` displaying `[Shard #0, Shard #2, Shard #5]` via `#result-shards-list`.
2. **Micro-Latency Breakdown**:
   Container `#result-micro-latency` displaying `#result-embed-latency` and `#result-search-latency` alongside `#result-latency`.
3. **Per-Card Shard and Node Badges**:
   Individual result cards render:
   - `<span class="..."><i class="fa-solid fa-server"></i> Shard #${shardId}</span>`
   - `<span class="...">${item.doc_id || 'Node #' + nodeId}</span>`
   - Exact Euclidean distance (`item.distance`)
   - Similarity score percentage (`item.similarity_score`)

### Protection Plan
The 3D reintegration must preserve these elements without regressions. Furthermore, the 3D result cards in `#search-results-list-3d` will also be enriched with the `Shard #${shardId}` badge, providing consistent metadata across both 2D and 3D views.

In `renderSearchResults()` (Tab 3 search results), each card will include a "Xem trên 3D" button calling `focusOn3DResultByIndexTab4(index)`. When clicked, the dashboard smoothly switches to `tab-3d-visualizer`, aligns the camera with the node in 3D, and displays the HUD metadata card.

---

## 5. Potential Errors and Defensive Countermeasures

| Potential Failure Point | Root Cause | Defensive Countermeasure |
|---|---|---|
| `TypeError: Cannot read properties of undefined (reading 'clientWidth')` | `ThreeEngine` initialized while container `#threejs-canvas-wrapper` is hidden inside inactive tab. | Provide fallback dimensions (`clientWidth || 1000`, `clientHeight || 760`) in `ThreeEngine.init()`. Trigger `onWindowResize()` inside `switchTab('tab-3d-visualizer')`. |
| `ReferenceError: THREE is not defined` | External CDN unreachable or blocked in offline/airgapped environments. | Wrap `init3DEngine()` with `if (typeof THREE === 'undefined') { console.warn('Three.js CDN unavailable'); return; }`. Guard every module instantiation. |
| `TypeError: Cannot read properties of null (reading 'forEach')` | `/api/search` returns `results: null` or malformed payload. | Guard result loops with `(data.results || []).forEach(...)` in both `renderSearchResults` and `render3DSearchResults`. |
| `HTTP 500 / Empty 3D Scene` | `data/processed/vectors_3d_cache.json` does not exist on disk in fresh checkout. | Provide an inline synthetic fallback in `server.js` returning 100 structured vector points across categories and a 3-layer topology so the 3D scene renders immediately. |
| Leaked `Node #undefined` or `NaN ms` | Missing properties on candidate objects or malformed latency values. | Fallback chains: `item.doc_id || (item.node_id !== undefined ? 'Node #' + item.node_id : (item.index !== undefined ? 'Node #' + item.index : 'Node #0'))`. Format latency with `Number.isFinite(val) ? val.toFixed(2) : '0.00'`. |

---

## 6. Implementation Guide for Worker

The Worker should apply the following precise file modifications:

### 6.1 `dashboard/public/index.html`
1. In `<head>` (after line 8):
   ```html
   <!-- Three.js CDN & OrbitControls -->
   <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
   <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
   <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
   ```
2. In `<nav>`: Insert the 3D tab button:
   ```html
   <button onclick="switchTab('tab-3d-visualizer')" id="btn-tab-3d-visualizer" class="tab-btn px-4 py-3.5 text-[13px] sm:text-[18px] font-medium text-slate-400 hover:text-slate-200 transition-all duration-150 flex items-center gap-2">
     <i class="fa-solid fa-cube text-sky-400"></i> Cơ cấu Kiến trúc 3D (Three.js WebGL Engine)
   </button>
   ```
3. In `<main>`: Restore `<section id="tab-3d-visualizer" class="tab-content hidden space-y-6">` before `tab-speed` (exact markup from HEAD commit `1401398`).
4. At bottom of `index.html` (before `architecture.js`):
   ```html
   <script src="js/three_engine.js"></script>
   <script src="js/three_vector_space.js"></script>
   <script src="js/three_hnsw_graph.js"></script>
   <script src="js/three_pipeline_3d.js"></script>
   ```

### 6.2 `dashboard/public/css/custom.css`
Append the required 3D classes:
```css
.mode-btn-3d.active {
  background: linear-gradient(135deg, #0284c7, #4f46e5);
  color: #ffffff;
  border-color: #38bdf8;
  box-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
  font-weight: 700;
}

#hud-tooltip-3d {
  position: absolute;
  display: none;
  pointer-events: none;
  z-index: 50;
  background: rgba(10, 18, 36, 0.95);
  backdrop-filter: blur(10px);
  border: 1.5px solid rgba(56, 189, 248, 0.7);
  border-radius: 0.85rem;
  padding: 0.85rem 1.15rem;
  max-width: 380px;
  box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.7), 0 0 25px rgba(56, 189, 248, 0.4);
  transition: opacity 0.15s ease;
  font-size: 15px;
}

.threejs-fullscreen {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  border-radius: 0 !important;
  margin: 0 !important;
}
```

### 6.3 `dashboard/server.js`
Restore the 3D API routes with fallback data generation:
```javascript
// 3b. API: 3D Vector Embedding Space Cloud (PCA/SVD Projected)
app.get('/api/vectors-3d', (req, res) => {
  try {
    const cachePath = path.join(ROOT_DIR, 'data', 'processed', 'vectors_3d_cache.json');
    if (fs.existsSync(cachePath)) {
      const data = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      return res.json({
        success: true,
        count: data.count,
        source: data.source,
        bounds: data.bounds,
        vectors: data.vectors
      });
    }
    // Graceful sample fallback if cache not yet built
    const categories = ["Kinh doanh & Tài chính", "Khoa học & Công nghệ", "Giáo dục", "Y tế & Sức khỏe", "Giao thông & Xây dựng", "Văn hóa & Đời sống"];
    const fallbackVectors = [];
    for (let i = 0; i < 120; i++) {
      const cat = categories[i % categories.length];
      const angle = (i / 120) * Math.PI * 4;
      const r = 15 + (i % 25);
      fallbackVectors.push({
        id: `doc_${i}`,
        index: i,
        x: Math.round((Math.cos(angle) * r + (Math.random() - 0.5) * 8) * 100) / 100,
        y: Math.round(((i % 30) - 15 + (Math.random() - 0.5) * 6) * 100) / 100,
        z: Math.round((Math.sin(angle) * r + (Math.random() - 0.5) * 8) * 100) / 100,
        title: `Tài liệu Vector Mẫu #${i} - ${cat}`,
        preview: `Trích đoạn nội dung tài liệu vector phân tích đa chiều trong hệ thống HNSW Sharded #${i % 5}...`,
        category: cat,
        token_count: 220 + (i * 3) % 150
      });
    }
    res.json({ success: true, count: fallbackVectors.length, source: "synthetic_fallback", bounds: { min: -45, max: 45 }, vectors: fallbackVectors });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// 3c. API: 3D HNSW Multi-Layer Topology Graph
app.get('/api/hnsw-topology-3d', (req, res) => {
  try {
    const cachePath = path.join(ROOT_DIR, 'data', 'processed', 'vectors_3d_cache.json');
    if (fs.existsSync(cachePath)) {
      const data = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
      return res.json({
        success: true,
        topology: data.hnsw_topology || {}
      });
    }
    // Synthetic 3-tier fallback topology
    const l2Nodes = [], l1Nodes = [], l0Nodes = [];
    const intraEdges = [], interLinks = [];
    for (let i = 0; i < 40; i++) {
      const x = (Math.random() - 0.5) * 60;
      const z = (Math.random() - 0.5) * 60;
      const id0 = `l0_n${i}`;
      l0Nodes.push({ id: id0, doc_id: `doc_${i}`, x: Math.round(x * 10) / 10, y: -28.0, z: Math.round(z * 10) / 10, title: `Node L0 #${i}`, category: "Khoa học & Công nghệ" });
      if (i % 3 === 0) {
        const id1 = `l1_n${i}`;
        l1Nodes.push({ id: id1, doc_id: `doc_${i}`, x: Math.round(x * 0.8 * 10) / 10, y: 0.0, z: Math.round(z * 0.8 * 10) / 10, title: `Node L1 #${i}`, category: "Khoa học & Công nghệ" });
        interLinks.push({ from: id1, to: id0 });
      }
      if (i % 10 === 0) {
        const id2 = `l2_n${i}`;
        l2Nodes.push({ id: id2, doc_id: `doc_${i}`, x: Math.round(x * 0.6 * 10) / 10, y: 28.0, z: Math.round(z * 0.6 * 10) / 10, title: `Node L2 #${i}`, category: "Khoa học & Công nghệ" });
        interLinks.push({ from: id2, to: `l1_n${i}` });
      }
    }
    for (let i = 0; i < l0Nodes.length - 1; i++) {
      intraEdges.push({ from: l0Nodes[i].id, to: l0Nodes[i + 1].id, layer: 0 });
    }
    for (let i = 0; i < l1Nodes.length - 1; i++) {
      intraEdges.push({ from: l1Nodes[i].id, to: l1Nodes[i + 1].id, layer: 1 });
    }
    for (let i = 0; i < l2Nodes.length - 1; i++) {
      intraEdges.push({ from: l2Nodes[i].id, to: l2Nodes[i + 1].id, layer: 2 });
    }
    res.json({
      success: true,
      topology: {
        layers: [
          { level: 2, name: "Layer 2", y: 28.0, nodes: l2Nodes },
          { level: 1, name: "Layer 1", y: 0.0, nodes: l1Nodes },
          { level: 0, name: "Layer 0", y: -28.0, nodes: l0Nodes }
        ],
        entry_point_id: l2Nodes.length > 0 ? l2Nodes[0].id : "l2_n0",
        intra_edges: intraEdges,
        inter_links: interLinks,
        stats: { total_nodes_l0: l0Nodes.length, total_nodes_l1: l1Nodes.length, total_nodes_l2: l2Nodes.length, total_edges: intraEdges.length }
      }
    });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});
```

### 6.4 `dashboard/public/js/app.js`
1. Re-add all 3D controller functions (`init3DEngine`, `set3DMode`, `filter3DCloud`, `setCameraPreset`, `toggle3DAutoRotate`, `toggle3DFullscreen`, `triggerHnswSimulation`, `toggle3DUploadZone`, `toggle3DHyperparams`, `handle3DFileSelected`, `searchByUploadedFile3D`, `searchAll3D`, `quickQuery3D`, `execute3DSearch`, `render3DSearchResults`, `focusOn3DResult`, `focusOn3DResultByIndex`, `focusOn3DResultByIndexTab4`).
2. Defensively guard `init3DEngine()` against missing `THREE` library.
3. In `switchTab(tabId)`, restore resize and initialization for `tab-3d-visualizer`.
4. In `DOMContentLoaded`, call `setTimeout(init3DEngine, 80)`.
5. In `renderSearchResults()`, add the "Xem trên 3D" button to each card:
   ```javascript
   <button type="button" onclick="focusOn3DResultByIndexTab4(${index})" class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-[13px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer shrink-0">
     <i class="fa-solid fa-cube"></i> Xem 3D
   </button>
   ```
6. In `render3DSearchResults()`, render Shard ID chips alongside coordinates and L2 distance.
7. Fix the 3 adversarial vulnerabilities in `renderSearchResults`:
   - Safely handle missing `doc_id`, `node_id`, and `index` with fallback `Node #0`.
   - Guard against `null` results array (`data.results || []`).
   - Format `latency_ms` safely when NaN.

### 6.5 `dashboard/public/js/three_pipeline_3d.js`
Update node 5 from "Tier 2: SSD Memmap" to "Tier 2: Direct I/O SSD Manager" with description "Đọc trực tiếp nhị phân Direct I/O kết hợp bộ nhớ đệm đa luồng ThreadPoolExecutor" to align with Feature 1 of `PROJECT.md`.

---

## 7. Verification Strategy for Acceptance Criteria

1. **Static Analysis & Syntax Check**:
   Run `node -c dashboard/public/js/app.js` and `node -c dashboard/server.js` to ensure zero syntax errors.
2. **Empirical Adversarial Test Harness**:
   Execute `node tests/test_ui_render_harness.js`. All 14 tests must pass with 0 regressions.
3. **HTTP Endpoint Verification**:
   Send requests to `/api/vectors-3d` and `/api/hnsw-topology-3d` via Node HTTP script to verify valid JSON structures.
4. **Search Routing Metrics Integrity**:
   Verify that `POST /api/search` returns `shards_probed`, `latency_ms`, and `micro_latency`, and that `renderSearchResults` renders them in DOM elements `#result-shards-container`, `#result-latency`, `#result-micro-latency`, and individual card chips.
