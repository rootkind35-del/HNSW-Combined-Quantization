# Handoff Report — Dashboard & UI Asset Explorer

- **Role**: Dashboard & UI Asset Explorer (Explorer 3)
- **Working Directory**: `f:\ANN\.agents\explorer_m0_3`
- **Target Subsystem**: `dashboard/` (Front-end, Node.js server, static assets, scripts)
- **Status**: Completed (Hard Handoff)
- **Timestamp**: 2026-09-21T03:52:00Z

---

## 1. Observation

Direct examination of `f:\ANN\dashboard` revealed 25 files across `public/`, `public/js/`, `public/css/`, `scripts/`, and root configuration files.

### 1.1 Complete Dashboard File Inventory & File Sizes

| Relative Path | Size (Bytes) | Lines | Primary Purpose / Status |
|---|---|---|---|
| `dashboard/package.json` | 474 | 17 | Dependencies: Express 4.21.2, cors 2.8.5. Retain. |
| `dashboard/package-lock.json` | 31,153 | 647 | Dependency lockfile. Retain. |
| `dashboard/server.js` | 26,170 | 692 | Express backend server, API routes, process spawner. Modify. |
| `dashboard/public/index.html` | 131,687 | 1,895 | Main dashboard single-page HTML layout (7 tabs). Modify. |
| `dashboard/public/css/custom.css` | 2,537 | 111 | Core styling, fonts, 3D HUD & mode buttons. Modify. |
| `dashboard/public/css/data_product.css` | 7,261 | 300 | Stylesheet for Data Product Studio (Tab 0). Retain. |
| `dashboard/public/js/app.js` | 60,711 | 1,473 | Main application logic, Search controller, 3D controllers. Modify. |
| `dashboard/public/js/architecture.js` | 7,967 | 184 | SVG physical flow graph visualizer (Tab 2). Retain. |
| `dashboard/public/js/charts.js` | 18,661 | 564 | Chart.js comparative performance visualizers. Retain. |
| `dashboard/public/js/data_product_studio.js` | 41,372 | 1,211 | 2D HTML5 Canvas interactive studio. Modify. |
| `dashboard/public/js/three_engine.js` | 12,034 | 332 | **Bloated 3D WebGL engine setup**. Delete candidate. |
| `dashboard/public/js/three_vector_space.js` | 18,655 | 499 | **Bloated 3D point cloud & laser beams**. Delete candidate. |
| `dashboard/public/js/three_hnsw_graph.js` | 14,904 | 368 | **Bloated 3D multi-layer HNSW graph**. Delete candidate. |
| `dashboard/public/js/three_pipeline_3d.js` | 10,206 | 241 | **Bloated 3D cyber racks visualizer**. Delete candidate. |
| `dashboard/scripts/dimension_reduction_3d.py` | 16,887 | 387 | **Offline PCA/SVD 3D generator script**. Delete candidate. |
| `dashboard/scripts/search_bridge.py` | 11,165 | 268 | CLI bridge for Python search. Modify. |
| `dashboard/scripts/search_service.py` | 11,060 | 278 | Local HTTP microservice (port 5005) for search. Modify. |
| `dashboard/scripts/speed_benchmark.py` | 7,641 | 197 | Latency breakdown benchmark script. Retain. |
| `dashboard/scripts/quantization_benchmark.py` | 8,594 | 196 | SQ8 numerical distortion benchmark script. Retain. |
| `dashboard/scripts/auto_search_evaluator.py` | 14,652 | 305 | Synthetic automated search evaluator. Retain. |
| `dashboard/scripts/build_search_cache.py` | 14,706 | 352 | Cache builder for 5,000 document subset. Modify. |

### 1.2 3D Visualizer & Heavy Resource Footprint

1. **Uncompressed Code Files**:
   - `dashboard/public/js/three_engine.js`: 12,034 bytes
   - `dashboard/public/js/three_vector_space.js`: 18,655 bytes
   - `dashboard/public/js/three_hnsw_graph.js`: 14,904 bytes
   - `dashboard/public/js/three_pipeline_3d.js`: 10,206 bytes
   - `dashboard/scripts/dimension_reduction_3d.py`: 16,887 bytes
   - **Total code size to delete**: 72,686 bytes (72.7 KB across 5 files).

2. **External CDN Bundles in `dashboard/public/index.html` (Lines 9-12)**:
   - Three.js core: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js` (~600 KB)
   - OrbitControls: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js` (~30 KB)
   - GSAP animation library: `https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js` (~65 KB)
   - **Total network transfer eliminated**: ~695 KB to ~700 KB on every page load.
   - Code verification: A search across all JavaScript files proved that `gsap` is only referenced inside `three_engine.js` (lines 265, 272, 290) and `three_hnsw_graph.js` (lines 246, 321, 357). No other module relies on GSAP.

3. **DOM Markup Bloat in `dashboard/public/index.html`**:
   - Tab navigation item: lines 132-134 (button `#btn-tab-3d-visualizer`).
   - Section container: lines 438 to 825 (section `#tab-3d-visualizer`, 388 lines of HTML containing 4-mode switcher, 3D search form, camera presets, HUD overlays).
   - Script tags: lines 1885-1888 (`three_engine.js`, `three_vector_space.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`).
   - Script tag references in `<head>`: lines 9-12.

4. **Dedicated 3D Endpoints in `dashboard/server.js`**:
   - `GET /api/vectors-3d` (lines 299-318, 20 lines)
   - `GET /api/hnsw-topology-3d` (lines 320-335, 16 lines)

5. **3D Code Blocks in `dashboard/public/js/app.js`**:
   - Lines 107-115: `init3DEngine` call in `switchTab()`.
   - Lines 456-462: "Xem trên 3D" button in search result cards.
   - Lines 468-476: `window.threeEngine.vectorSpaceModule.renderQueryResults()` sync call.
   - Lines 478-770: `init3DEngine()`, `set3DMode()`, `filter3DCloud()`, `setCameraPreset()`, `toggle3DAutoRotate()`, `trigger3DExplode()`, `triggerHnswSimulate()`, `focusOn3DResultByIndexTab4()`, `execute3DSearch()`, `render3DSearchResults()` (293 lines of unused controllers).

6. **Dedicated 3D Styles in `dashboard/public/css/custom.css`**:
   - Lines 60-66: `.mode-btn-3d.active`
   - Lines 84-98: `#hud-tooltip-3d`
   - Lines 100-110: `.threejs-fullscreen`

### 1.3 Search Data Flow and API Consumption

The dashboard provides two user search interfaces:

1. **Tab 4: Interactive Semantic Search (`tab-search`)**:
   - **Form submission**: `#search-form` triggers `executeSearch()` in `dashboard/public/js/app.js:332`.
   - **Parameters collected**: `query` (text input), `top_k` (range 1-10), `algorithm` (select dropdown: `two_tier`, `hnsw`, `pure_sq8`), `selectedCategory`, `hyperparams` (`m`, `ef_search`, `tau`, `epsilon`, `min_rerank_k`).
   - **Network request**: `POST /api/search` with JSON payload.
   - **Result handler**: `renderSearchResults(data)` in `app.js:373`.
   - **UI elements populated**:
     - `#result-count`: Total matches count.
     - `#result-query`: Query string or uploaded filename.
     - `#result-algo`: Algorithm description.
     - `#result-latency`: Total execution latency in milliseconds.
     - `#result-cat-badge`: Category filter badge.
     - `#search-results-list`: Container appending result cards.
   - **Current card fields**:
     - Rank badge: `#${item.rank}`
     - Title: `${item.title}`
     - Category badge: `${item.category}`
     - Doc ID: `${item.doc_id}`
     - Preview excerpt: `${item.preview}`
     - L2 distance: `${item.distance.toFixed(4)}`
     - Cosine similarity: `${scorePct}%`
     - Obsolete button: "Xem trên 3D" invoking `focusOn3DResultByIndexTab4(${index})`.
   - **Missing information**: Neither the probed shard IDs nor individual hit `shard_id` are currently exposed or rendered.

2. **Tab 0: Data Product Studio (`tab-data-product`)**:
   - **Form submission**: `#dp-search-input` (debounced) or quick prompt chips trigger `executeSearch(query)` in `dashboard/public/js/data_product_studio.js:358`.
   - **Network request**: `POST /api/search` with `{ query, top_k, algorithm: activeAlgo, category: "Tất cả" }`.
   - **Result handler**: `renderResultsList(query, results)` in `data_product_studio.js:411`.
   - **UI elements populated**:
     - `#dp-search-time`: Latency in ms.
     - `#dp-result-count`: Returned results count.
     - `#dp-results-container`: Container appending styled cards.
   - **Current card fields**:
     - Rank badge: `#${idx + 1}`
     - Category pill
     - Doc ID
     - Cosine % and L2 distance
     - Title
     - Semantic heatmap preview (`generateSemanticHeatmap`)
     - Token count weight
     - "Xem trên đồ thị" button.

3. **Backend Search Dispatch (`dashboard/server.js:337-434`)**:
   - `runSearchBridge()` tries an HTTP `POST` request to `http://127.0.0.1:5005/search` (persisted microservice in RAM).
   - If port 5005 is unavailable or times out after 3000ms, it falls back to `execFile('python', ['scripts/search_bridge.py', ...])`.
   - Both `search_service.py` and `search_bridge.py` load `data/processed/search_index_cache.npz` and calculate flat cosine similarity over 5,000 sample vectors, projecting coordinates to 3D.
   - `search_service.py` returns `query_3d`, `coords_3d`, `latency_ms`, and `micro_latency` (`embed_ms`, `search_ms`). It does not yet invoke `ShardedIVFHNSW` or return `shard_id`.

4. **Target Distributed Backend in `update` Branch (`two_tier_hnsw.py`)**:
   - `ShardedIVFHNSW.distributed_search(query, top_k, nprobe=3, re_rank_limit=50)` returns:
     `final_results[:top_k]` where each tuple is `(exact_dist, node_id, sid)`.
   - `target_shard_ids`: List of shard IDs probed by the router (e.g. `[0, 2, 5]`).
   - `sid`: Specific Shard ID storing the candidate vector.
   - `node_id`: Local index of the vector in that shard.
   - `exact_dist`: Float32 Euclidean distance after SSD Direct I/O re-ranking.

---

## 2. Logic Chain

1. **Premise**: Requirement R2 states: *"Remove all bloated, unused resources (e.g., heavy CSS/JS, unused 3D engines) from the dashboard/ directory. Optimize the remaining UI code to cleanly display search results, including the specific Shard IDs hit and the execution latency."*
2. **Observation**: `three_engine.js`, `three_vector_space.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, and `dimension_reduction_3d.py` exist solely to power the WebGL visualizer in Tab 1 (`tab-3d-visualizer`).
3. **Inference**: Deleting these 5 files removes 72,686 bytes of code. Removing the 3 external CDN scripts (`three.min.js`, `OrbitControls.js`, `gsap.min.js`) eliminates ~700 KB of payload on client load.
4. **Observation**: `gsap` is only called inside the Three.js files. Deleting Three.js allows removing GSAP completely with zero impact on other tabs.
5. **Observation**: `dashboard/public/index.html` contains 388 lines of HTML in `<section id="tab-3d-visualizer">` plus navigation buttons and script inclusions.
6. **Inference**: Removing this markup decreases `index.html` size by ~20%, reduces initial DOM nodes, and simplifies client initialization.
7. **Observation**: `app.js` contains 293 lines of unused 3D functions and attaches a "Xem trên 3D" button to every search result card.
8. **Inference**: Removing this dead code prevents runtime errors once Three.js files are deleted and frees visual real estate on each result card.
9. **Observation**: In the `update` branch, `ShardedIVFHNSW.distributed_search` returns `(exact_dist, node_id, sid)` and identifies `target_shard_ids`. The current UI only displays `distance` and `similarity_score` without any shard information.
10. **Inference**: To satisfy Requirement R2, `server.js` and `search_service.py` must return `shards_probed` and `results[i].shard_id`. The UI in `app.js` and `data_product_studio.js` must be updated to render a Shards Hit summary badge in the header and an individual Shard ID badge on each result card.

---

## 3. Caveats

1. **2D Canvas in Data Product Studio**:
   `dashboard/public/js/data_product_studio.js` uses a 2D HTML5 canvas (`dp-scatter-canvas`), not WebGL or Three.js. It does not need to be deleted, but its calls to `/api/vectors-3d` and `/api/hnsw-topology-3d` (lines 334-355) must be removed or redirected so it does not log 404 errors once those endpoints are removed.
2. **Offline Data Generation**:
   `build_search_cache.py` currently computes PCA 3D coordinates if run. Removing the 3D calculation logic from `build_search_cache.py` will keep it lightweight without breaking search cache generation.
3. **No Direct Code Modifications Performed**:
   In accordance with the read-only Explorer role, all code files remain unmodified. The proposed changes are specified with exact line numbers and replacement snippets below.

---

## 4. Conclusion & Actionable Recommendations

### 4.1 File Deletion Schedule

Delete the following 5 files completely from `dashboard/`:
1. `dashboard/public/js/three_engine.js` (12,034 bytes)
2. `dashboard/public/js/three_hnsw_graph.js` (14,904 bytes)
3. `dashboard/public/js/three_pipeline_3d.js` (10,206 bytes)
4. `dashboard/public/js/three_vector_space.js` (18,655 bytes)
5. `dashboard/scripts/dimension_reduction_3d.py` (16,887 bytes)

### 4.2 Cleanup in `dashboard/public/index.html`

1. **Remove CDN tags** (lines 9-12):
   - Delete Three.js, OrbitControls, and GSAP script tags.
2. **Remove Navigation Tab Button** (lines 132-134):
   - Delete `<button onclick="switchTab('tab-3d-visualizer')" ...>`.
3. **Remove Tab Section Markup** (lines 438-825):
   - Delete entire `<section id="tab-3d-visualizer" ...>...</section>`.
4. **Remove Script Inclusions** (lines 1885-1888):
   - Delete `<script src="js/three_engine.js"></script>`, `three_vector_space.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`.
5. **Update Search Header Markup** (around line 1198):
   - Add a Shards Hit summary badge container:
   ```html
   <div class="flex flex-wrap items-center gap-3">
     <div id="result-shards-container" class="hidden flex items-center gap-1.5 px-3 py-1 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-mono font-bold">
       <i class="fa-solid fa-server text-amber-400"></i>
       <span>Shards Hit:</span>
       <span id="result-shards-list" class="text-white"></span>
     </div>
     <div class="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-slate-800 border border-slate-700 text-xs text-slate-300">
       <i class="fa-solid fa-microchip text-indigo-400"></i>
       <span>Thuật toán:</span>
       <span id="result-algo" class="text-indigo-300 font-bold"></span>
     </div>
     <div class="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 text-xs font-mono font-bold">
       <i class="fa-solid fa-stopwatch text-emerald-400"></i>
       <span>Độ trễ:</span>
       <span id="result-latency" class="text-white font-bold">0.00</span> ms
     </div>
   </div>
   ```

### 4.3 Cleanup and Enhancement in `dashboard/public/js/app.js`

1. **Remove Tab Switch Handler** (lines 107-115):
   - Remove `if (tabId === 'tab-3d-visualizer') { ... }`.
2. **Remove 3D Web Controllers** (lines 478-770):
   - Delete `init3DEngine()`, `set3DMode()`, `filter3DCloud()`, `setCameraPreset()`, `toggle3DAutoRotate()`, `trigger3DExplode()`, `triggerHnswSimulate()`, `focusOn3DResultByIndexTab4()`, `execute3DSearch()`, `render3DSearchResults()`.
3. **Enhance `renderSearchResults(data)`** (lines 373-476):
   - Populate `#result-shards-container` and `#result-shards-list`:
     ```javascript
     const shardsContainer = document.getElementById('result-shards-container');
     const shardsList = document.getElementById('result-shards-list');
     if (shardsContainer && shardsList) {
       if (data.shards_probed && data.shards_probed.length > 0) {
         shardsList.textContent = `[${data.shards_probed.map(s => `Shard #${s}`).join(', ')}]`;
         shardsContainer.classList.remove('hidden');
       } else {
         shardsContainer.classList.add('hidden');
       }
     }
     ```
   - In each result card, replace the old "Xem trên 3D" button with a Shard ID and Node ID chip:
     ```javascript
     card.innerHTML = `
       <div class="flex items-start space-x-3.5">
         <div class="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center font-mono font-bold text-sky-400 text-sm shrink-0 mt-0.5">
           #${item.rank}
         </div>
         <div class="space-y-1.5">
           <div class="flex flex-wrap items-center gap-2">
             <h4 class="text-[17px] font-bold text-slate-100">${item.title}</h4>
             <span class="text-[12px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${item.category || "Tin tức"}</span>
             <span class="text-[12px] font-mono font-semibold px-2 py-0.5 rounded-lg bg-amber-500/15 text-amber-300 border border-amber-500/30 flex items-center gap-1">
               <i class="fa-solid fa-server text-[10px]"></i> Shard #${item.shard_id !== undefined ? item.shard_id : '0'}
             </span>
             <span class="text-[12px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">${item.doc_id || `Node #${item.node_id || item.index}`}</span>
           </div>
           <p class="text-[15px] text-slate-300 line-clamp-2 leading-relaxed">${item.preview}...</p>
         </div>
       </div>

       <div class="flex items-center space-x-5 shrink-0 text-right self-end md:self-auto border-t md:border-t-0 border-slate-800/80 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end">
         <div>
           <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Sai số Euclid</div>
           <div class="text-[15px] font-mono font-bold text-slate-200">${item.distance !== undefined ? item.distance.toFixed(4) : '0.0000'}</div>
         </div>
         <div>
           <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Độ tương đồng</div>
           <div class="text-[17px] font-mono font-bold text-emerald-400">${scorePct}%</div>
         </div>
       </div>
     `;
     ```
   - Delete lines 468-476 (`threeEngine.vectorSpaceModule.renderQueryResults`).

### 4.4 Cleanup in `dashboard/public/css/custom.css`

Delete lines 60-66 (`.mode-btn-3d.active`), lines 84-98 (`#hud-tooltip-3d`), and lines 100-110 (`.threejs-fullscreen`).

### 4.5 Cleanup in `dashboard/server.js`

Delete routes `GET /api/vectors-3d` (lines 299-318) and `GET /api/hnsw-topology-3d` (lines 320-335).

### 4.6 UI Performance and Responsive Improvements

1. **Canvas Event Optimization in `data_product_studio.js`**:
   - Throttle the `window.addEventListener('mousemove', ...)` handler with `requestAnimationFrame` to eliminate repetitive `getBoundingClientRect()` reflows.
   - Add touch event listeners (`touchstart`, `touchmove`, `touchend`) to `dp-scatter-canvas` so mobile and tablet users can drag and navigate the 2D scatter view.
2. **Polling Discipline in `charts.js`**:
   - Wrap `setInterval(pollStatus, 3000)` inside a visibility check (`if (document.hidden) return;`) to avoid unnecessary background AJAX requests when the dashboard tab is idle or backgrounded.
3. **Mobile Tab Overflow in `index.html`**:
   - Add `overflow-x-auto whitespace-nowrap` to the tab navigation wrapper (`nav > div`) to enable clean horizontal swiping on screens narrower than 768px.

---

## 5. Verification Method

### 5.1 Verification Commands
Once the changes are applied:

1. **Verify deleted files are absent**:
   ```powershell
   Get-ChildItem -Path "f:\ANN\dashboard\public\js" -Filter "*three*"
   Test-Path "f:\ANN\dashboard\scripts\dimension_reduction_3d.py"
   ```
   *Expected outcome*: Returns nothing / False.

2. **Verify no remaining Three.js references**:
   ```powershell
   Select-String -Path "f:\ANN\dashboard\public\**\*" -Pattern "three\.min\.js|OrbitControls|ThreeEngine"
   ```
   *Expected outcome*: 0 matching lines found.

3. **Verify Node.js server startup**:
   ```powershell
   cd f:\ANN\dashboard
   node server.js
   ```
   *Expected outcome*: Server starts on port 3000 without missing module exceptions.

4. **Verify Search API returns Shard IDs and execution latency**:
   ```powershell
   Invoke-RestMethod -Uri "http://localhost:3000/api/search" -Method POST -ContentType "application/json" -Body '{"query":"thị trường tài chính", "top_k": 5}'
   ```
   *Expected outcome*: JSON response contains `shards_probed` array (e.g. `[0, 2, 5]`), `latency_ms` float, and each result in `data.results` contains a `shard_id` property.

5. **Invalidation Conditions**:
   - If any UI component throws `ReferenceError: THREE is not defined` or `ThreeEngine is not defined`.
   - If the search results table renders without showing which Shard ID was hit.
   - If the 3D visualizer tab button or canvas wrapper remains in `index.html`.
