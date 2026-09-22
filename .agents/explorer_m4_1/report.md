# Investigation Report: Survey of Git History, Deleted 3D Assets, and Restoration Plan

**Target**: Milestone 4 — 3D UI Restoration, Preservation & Backend Integration  
**Author**: `explorer_m4_1`  
**Date**: 2026-09-21  
**Project**: Distributed Sharded IVF-HNSW (`f:\ANN`)

---

## 1. Executive Summary

A survey of git history, commit diffs, and the working tree was conducted to locate all 3D files, identify how and where they were removed, determine exact restoration commands, and establish a concrete step-by-step restoration plan for the Worker.

Key findings:
1. **Scope of 3D Files**: Exactly 5 files constitute the 3D subsystem:
   - `dashboard/public/js/three_engine.js` (332 lines, 12,034 bytes)
   - `dashboard/public/js/three_hnsw_graph.js` (387 lines, 14,904 bytes)
   - `dashboard/public/js/three_pipeline_3d.js` (285 lines, 10,206 bytes)
   - `dashboard/public/js/three_vector_space.js` (500 lines, 18,655 bytes)
   - `dashboard/scripts/dimension_reduction_3d.py` (387 lines, 16,887 bytes)
2. **Git Commit History**:
   - The files were introduced in commit `52c82b1` (2026-09-02) and finalized in commit `4b61b76` (2026-09-06).
   - In git `HEAD` of branch `main` (`140139883585bc2fb220a5fbe16cd486e81ea555`), all 5 files are tracked and preserved verbatim.
   - Deletion occurred on branch `update` in commit `7e745d4` (2026-09-21). In the local working tree on `main`, Milestone 2 deleted them from disk and removed references across `index.html`, `app.js`, `server.js`, and `custom.css`.
   - The 5 files currently exist on disk in `f:\ANN` matching `HEAD` bit-for-bit.
3. **Surrounding File Modifications**:
   - `dashboard/public/index.html`: CDN scripts, navigation tab `tab-3d-visualizer`, viewport container/HUD markup (535 lines), and module script tags were removed.
   - `dashboard/public/css/custom.css`: Three classes (`.mode-btn-3d.active`, `#hud-tooltip-3d`, `.threejs-fullscreen`) were removed.
   - `dashboard/public/js/app.js`: 3D initialization (`init3DEngine`), view switching, interactive controllers, search sync, and the "Xem trên 3D" result button were removed.
   - `dashboard/server.js`: `/api/vectors-3d` and `/api/hnsw-topology-3d` routes were removed.
   - `dashboard/scripts/dimension_reduction_3d.py`: Contains a legacy `np.memmap` reference on line 121 in an unused fallback path that must be sanitized to prevent test audit failure.

---

## 2. Git Commit History Analysis

### 2.1 Commit Timeline of 3D Assets

| Commit Hash | Branch | Author / Date | Description & Impact |
|---|---|---|---|
| `52c82b12a0e1e162` | `main` | Project Team <br> 2026-09-02 | Initial commit implementing Two-Tier Quantized HNSW. Created `three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, and `three_vector_space.js`. |
| `0286b3eec656e916` | `main` | Project Team <br> 2026-09-02 | Added Vietnamese documentation and clean styling to `dimension_reduction_3d.py`. |
| `4b61b7646c47be7c` | `main` | Project Team <br> 2026-09-06 | Finalized 3D visualizer, photon routing simulation, crystalline nodes, and high-contrast glass planes. |
| `140139883585bc2f` (HEAD) | `main` | Project Team <br> 2026-09-07 | Implemented Data Product Designer studio. All 5 3D files remained tracked in the tree without modification (`git diff 4b61b76 HEAD` is empty for all 5 files). |
| `7e745d4b6fd17dc9` | `update` | Project Team <br> 2026-09-21 | Distributed cluster refactor on `update` branch. Deleted all 4 frontend 3D JS files and `dimension_reduction_3d.py`. |
| Working Tree (M2) | `main` | `worker_m2_clean` <br> 2026-09-21 | Removed 3D files from disk and deleted 3D endpoints/markup to meet the original M2 clean-up prompt. |

### 2.2 Forensic Confirmation of Deletion Mechanism

The deletion of 3D components did not originate from a committed change on `main`. Rather:
1. Branch `update` removed them in commit `7e745d4`.
2. The initial task description for Milestone 2 directed the team to delete unused 3D engines (`PROJECT.md` Feature 6: "Delete Bloated 3D Assets").
3. Working tree edits by `worker_m2_clean` stripped the HTML markup, CSS rules, Express routes, and JS controllers.
4. The user updated requirements at 2026-09-21T16:02:19Z mandating that all 3D files be kept, preserved, and functional.

---

## 3. Inventory of 3D Files and Git Restoration Commands

### 3.1 File Specifications

```
f:\ANN/
├── dashboard/
│   ├── public/
│   │   └── js/
│   │       ├── three_engine.js                 (12,034 bytes, 332 lines)
│   │       ├── three_hnsw_graph.js             (14,904 bytes, 387 lines)
│   │       ├── three_pipeline_3d.js            (10,206 bytes, 285 lines)
│   │       └── three_vector_space.js           (18,655 bytes, 500 lines)
│   └── scripts/
│       └── dimension_reduction_3d.py           (16,887 bytes, 387 lines)
```

### 3.2 Exact Git Restoration Command

If any of these files are lost or modified unexpectedly, they can be restored from `HEAD`:

```powershell
git checkout HEAD -- dashboard/public/js/three_engine.js dashboard/public/js/three_hnsw_graph.js dashboard/public/js/three_pipeline_3d.js dashboard/public/js/three_vector_space.js dashboard/scripts/dimension_reduction_3d.py
```

All 5 files currently match git `HEAD` with zero byte variance.

---

## 4. Detailed Component Analysis & Interfaces

### 4.1 `dashboard/public/js/three_engine.js`
- **Role**: Core WebGL engine and scene manager.
- **Key Methods**:
  - `constructor(containerId)`: Binds to element `#threejs-canvas-wrapper`.
  - `init()`: Sets up `THREE.Scene`, `THREE.PerspectiveCamera`, `THREE.WebGLRenderer` with ACESFilmicToneMapping, `THREE.OrbitControls`, lighting, and animation loop.
  - `setMode(mode, resetCamera)`: Switches between `'universe'`, `'hnsw'`, `'pipeline'`, and `'quantization'`.
  - `setCameraPreset(preset)`: Positions camera for `'universe'`, `'topdown'`, `'hnsw'`, `'pipeline'`, `'query'`.
  - `animateCameraTo(pos, lookAt, duration)`: Smooth camera movement via GSAP (with fallback to direct positioning).
  - `toggleAutoRotate()`: Toggles OrbitControls rotation.
- **Global Export**: `window.ThreeEngine = ThreeEngine`.

### 4.2 `dashboard/public/js/three_vector_space.js`
- **Role**: 3D point cloud renderer and interactive search vector projector.
- **Key Methods**:
  - `loadVectorsData()`: Executes `fetch('/api/vectors-3d')`.
  - `buildPointCloud()`: Renders 3D particles with category coloring (6 categories).
  - `renderQueryResults(queryText, query3D, results)`: Projects search query beacon and draws laser lines to top-K result nodes.
  - `highlightNode(x, y, z, label)`: Places dual-ring target reticle on selected node.
  - `filterByCategory(cat)`: Toggles visibility per category.
- **Global Export**: `window.VectorSpaceModule = VectorSpaceModule`.

### 4.3 `dashboard/public/js/three_hnsw_graph.js`
- **Role**: Hierarchical HNSW graph visualizer.
- **Key Methods**:
  - `loadTopology()`: Executes `fetch('/api/hnsw-topology-3d')`.
  - `buildHnswScene()`: Constructs 3 glass planes (`Layer 2`, `Layer 1`, `Layer 0`), intra-layer edges, and inter-layer vertical conduit links.
  - `startRoutingSimulation(isEarlyExit)`: Animates photon packet traveling from entry point at Layer 2 down to candidate nodes at Layer 0.
- **Global Export**: `window.HnswGraphModule = HnswGraphModule`.

### 4.4 `dashboard/public/js/three_pipeline_3d.js`
- **Role**: Isometric hardware server pod and data pipeline visualizer.
- **Structure**: Self-contained static node list (`this.pipelineNodes`), particle stream emitters, and hover HUD. Does not require dedicated backend API.
- **Global Export**: `window.Pipeline3DModule = Pipeline3DModule`.

### 4.5 `dashboard/scripts/dimension_reduction_3d.py`
- **Role**: Computes PCA/SVD projection from 384 dimensions to 3D and generates HNSW multi-layer topology.
- **Outputs**:
  - `data/processed/vectors_3d_cache.json` (Vector cloud + HNSW 3-layer topology).
  - `data/processed/pca_3d_projection.json` (Mean vector, components, scale factor).
- **Forensic Note**: Line 121 contains `mmap = np.memmap(...)` in an unused candidate fallback. The project has an acceptance criterion forbidding `numpy.memmap`. This line must be replaced with `np.fromfile` to prevent adversarial test failures.

---

## 5. Scope of Other Modified Files

### 5.1 `dashboard/server.js`
- **Lines to Re-add**:
  ```javascript
  // 3b. API: 3D Vector Embedding Space Cloud (PCA/SVD Projected)
  app.get('/api/vectors-3d', (req, res) => {
    try {
      const cachePath = path.join(ROOT_DIR, 'data', 'processed', 'vectors_3d_cache.json');
      if (fs.existsSync(cachePath)) {
        const data = JSON.parse(fs.readFileSync(cachePath, 'utf8'));
        return res.json({
          success: true,
          count: data.count || (data.vectors ? data.vectors.length : 0),
          source: data.source || 'Siêu kho 31.33M Vector',
          bounds: data.bounds || { min: -45, max: 45 },
          vectors: data.vectors || []
        });
      }
      res.json({
        success: true,
        count: 0,
        source: 'Chưa sinh bộ đệm 3D',
        bounds: { min: -45, max: 45 },
        vectors: []
      });
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
      res.json({ success: true, topology: {} });
    } catch (err) {
      res.status(500).json({ success: false, error: err.message });
    }
  });
  ```

### 5.2 `dashboard/public/css/custom.css`
- **Rules to Re-add**:
  ```css
  .mode-btn-3d.active {
    background: linear-gradient(135deg, #0284c7, #4f46e5);
    color: #ffffff;
    border-color: #38bdf8;
    box-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
    font-weight: 700;
  }

  /* 3D HUD Tooltip */
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

  /* 3D Viewport Fullscreen Class */
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

### 5.3 `dashboard/public/index.html`
- **CDN Scripts in `<head>`**:
  ```html
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
  ```
- **Navigation Button in `<nav>`**:
  ```html
  <button onclick="switchTab('tab-3d-visualizer')" id="btn-tab-3d-visualizer" class="tab-btn px-4 py-3.5 text-[13px] sm:text-[18px] font-medium text-slate-400 hover:text-slate-200 transition-all duration-150 flex items-center gap-2">
    <i class="fa-solid fa-cube text-sky-400"></i> Cơ cấu Kiến trúc 3D (Three.js WebGL Engine)
  </button>
  ```
- **Markup Section `<section id="tab-3d-visualizer">`**:
  Restored from `HEAD:dashboard/public/index.html` lines 438 to 971.
- **Script Tags before `</body>`**:
  ```html
  <script src="js/three_engine.js"></script>
  <script src="js/three_vector_space.js"></script>
  <script src="js/three_hnsw_graph.js"></script>
  <script src="js/three_pipeline_3d.js"></script>
  ```
- **Preservation Requirement**: Ensure `tab-search` retains all Milestone 2 elements (`#result-shards-container`, `#result-shards-list`, `#result-latency`, `#result-micro-latency`, shard chips).

### 5.4 `dashboard/public/js/app.js`
- **Functions to Re-add**:
  - `init3DEngine()`: Instantiates `ThreeEngine`, mounts `VectorSpaceModule`, `HnswGraphModule`, `Pipeline3DModule`.
  - `set3DMode(mode, resetCamera)`: Switches mode and HUD visibility.
  - `filter3DCloud(category)`: Filters points by category and syncs active UI chips.
  - `setCameraPreset(preset)`: Invokes `threeEngine.setCameraPreset()`.
  - `toggle3DAutoRotate()`: Toggles rotation and button highlight.
  - `toggle3DFullscreen()`: Toggles `.threejs-fullscreen` on `#threejs-viewport-container`.
  - `triggerHnswSimulation(useEarlyExit)`: Starts routing animation.
  - `toggle3DUploadZone()`, `toggle3DHyperparams()`, `handle3DFileSelected(event)`.
  - `searchAll3D()`, `quickQuery3D(queryText)`, `execute3DSearch()`, `render3DSearchResults(data)`.
  - `focusOn3DResultByIndex(index)`, `focusOn3DResultByIndexTab4(index)`, `focusOn3DResult(x, y, z, ...)`.
- **Integration Points**:
  - `switchTab(tabId)`: Add branch for `'tab-3d-visualizer'` calling `init3DEngine()` and `onWindowResize()`.
  - `renderSearchResults(data)`:
    - Keep existing Shards Probed, Shard chips, latency metrics intact.
    - Re-add sync with 3D:
      ```javascript
      if (window.threeEngine && window.threeEngine.vectorSpaceModule && data.results && data.results.length > 0) {
        window.threeEngine.vectorSpaceModule.renderQueryResults(
          data.query || "Truy vấn văn bản",
          data.query_3d,
          data.results
        );
      }
      ```
    - Re-add "Xem trên 3D" button to each search result card:
      ```javascript
      <button type="button" onclick="focusOn3DResultByIndex(${index})" class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-[14px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer shrink-0">
        <i class="fa-solid fa-crosshairs"></i> Xem trên 3D
      </button>
      ```
  - `DOMContentLoaded`: Add `setTimeout(init3DEngine, 80);`.

---

## 6. Step-by-Step Restoration Plan for the Worker

### Phase 1: Sanitize and Seed 3D Data
1. Inspect `dashboard/scripts/dimension_reduction_3d.py`:
   - Replace `np.memmap` on line 121 with `np.fromfile` to guarantee zero `memmap` across the entire codebase.
2. Ensure `data/processed/vectors_3d_cache.json` exists or is generated with sample vectors and 3-layer topology so the 3D visualizer renders immediately.

### Phase 2: Restore Express Server Endpoints
1. In `dashboard/server.js`, re-insert `/api/vectors-3d` and `/api/hnsw-topology-3d`.
2. Run `node -c dashboard/server.js` to verify syntax.

### Phase 3: Restore Styles and HTML
1. In `dashboard/public/css/custom.css`, append `.mode-btn-3d.active`, `#hud-tooltip-3d`, and `.threejs-fullscreen`.
2. In `dashboard/public/index.html`:
   - Add Three.js and OrbitControls CDNs to `<head>`.
   - Add `btn-tab-3d-visualizer` to `<nav>`.
   - Insert `<section id="tab-3d-visualizer">` block from `HEAD`.
   - Add 3D script tags before `</body>`.
   - Verify that `#result-shards-container` and `#result-micro-latency` in `tab-search` remain intact.

### Phase 4: Restore JavaScript Controllers & Cross-Wiring
1. In `dashboard/public/js/app.js`:
   - Add `init3DEngine()` and all 3D controller functions.
   - Update `switchTab` to handle `'tab-3d-visualizer'`.
   - In `renderSearchResults`, keep shard chips and latency while adding 3D query projection sync and "Xem trên 3D" buttons.
   - In `DOMContentLoaded`, add `setTimeout(init3DEngine, 80)`.
2. Run `node -c dashboard/public/js/app.js` to verify syntax.

### Phase 5: Verification Suite
1. Run `node tests/test_ui_render_harness.js` to confirm no regressions in UI rendering.
2. Run `python -m pytest tests/test_two_tier_hnsw.py tests/test_search_edge_cases.py` to confirm backend test suite passes.
3. Verify zero occurrences of `numpy.memmap` or `mmap` across `dashboard/scripts/` and `src/ann_index/`.
4. Validate that all 5 3D files exist on disk with valid syntax.

---

## 7. Conclusion

All 5 core 3D files (`three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, `dimension_reduction_3d.py`) are tracked in git `HEAD` and currently exist on disk in valid working condition. The required work is purely additive integration: wiring routes back into `server.js`, adding styles into `custom.css`, re-inserting markup into `index.html`, and restoring controller hooks in `app.js` while maintaining the distributed shard routing metrics developed in Milestone 2.
