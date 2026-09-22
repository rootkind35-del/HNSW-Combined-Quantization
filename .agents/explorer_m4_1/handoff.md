# Handoff Report: 3D UI Survey and Restoration Plan

**Agent**: `explorer_m4_1`  
**Milestone**: M4  
**Date**: 2026-09-21  

---

## 1. Observation

### 1.1 Complete Inventory of 3D Files and Git History
A search of all commits in git history for `three`, `3d`, `shader`, and `webgl` patterns (`git log --all --name-only`) confirmed that exactly 5 files constitute the 3D subsystem:

1. `dashboard/public/js/three_engine.js` (332 lines, 12,034 bytes)
2. `dashboard/public/js/three_hnsw_graph.js` (387 lines, 14,904 bytes)
3. `dashboard/public/js/three_pipeline_3d.js` (285 lines, 10,206 bytes)
4. `dashboard/public/js/three_vector_space.js` (500 lines, 18,655 bytes)
5. `dashboard/scripts/dimension_reduction_3d.py` (387 lines, 16,887 bytes)

The commit history for these files:
- Added in commit `52c82b12a0e1e1626786e0868b45660bb969df7b` ("feat: complete two-tier quantized HNSW for 10M Vietnamese text vector search").
- Completed in commit `4b61b7646c47be7c061a09626b1eefab786031b4` ("feat: hoan thien he thong two-tier quantized HNSW, crawler, 3D visualizer va cap nhat huong dan README").
- Tracked in `HEAD` (`140139883585bc2fb220a5fbe16cd486e81ea555`). `git diff 4b61b76 HEAD` is empty across all 5 files.
- Deleted on branch `update` in commit `7e745d4b6fd17dc9c1dd0ffd955ff6cea390dfdc` ("điều chỉnh lại logic cụm máy chủ phân tán").
- Deleted in the working directory on branch `main` during Milestone 2 by `worker_m2_clean`.
- Restored to disk from `HEAD` at 23:01 local time. `git diff` for all 5 files against `HEAD` currently returns empty output.

Syntax validation check:
```powershell
node -c dashboard/public/js/three_engine.js
node -c dashboard/public/js/three_hnsw_graph.js
node -c dashboard/public/js/three_pipeline_3d.js
node -c dashboard/public/js/three_vector_space.js
python -m py_compile dashboard/scripts/dimension_reduction_3d.py
```
Output: Exit code 0 for all 5 files.

### 1.2 Git Restoration Command
If any of these files are modified or deleted, the exact restoration command is:
```powershell
git checkout HEAD -- dashboard/public/js/three_engine.js dashboard/public/js/three_hnsw_graph.js dashboard/public/js/three_pipeline_3d.js dashboard/public/js/three_vector_space.js dashboard/scripts/dimension_reduction_3d.py
```

### 1.3 Modified Files When 3D Was Removed

#### `dashboard/server.js`
The following endpoints were removed in git diff:
- `GET /api/vectors-3d` (serves vector cloud data from `data/processed/vectors_3d_cache.json`).
- `GET /api/hnsw-topology-3d` (serves multi-layer topology from `data/processed/vectors_3d_cache.json`).

#### `dashboard/public/css/custom.css`
The following rules were removed:
- `.mode-btn-3d.active` (button styling for 3D mode toggles).
- `#hud-tooltip-3d` (tooltip popup for 3D points).
- `.threejs-fullscreen` (fullscreen layout for the 3D canvas).

#### `dashboard/public/index.html`
- External CDN scripts removed from `<head>`:
  - Three.js: `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`
  - OrbitControls: `https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js`
- Tab navigation button removed: `<button onclick="switchTab('tab-3d-visualizer')" id="btn-tab-3d-visualizer" ...>`
- Section `<section id="tab-3d-visualizer" class="tab-content hidden space-y-6">` (535 lines) removed.
- Script tags removed from before `</body>`:
  - `js/three_engine.js`
  - `js/three_vector_space.js`
  - `js/three_hnsw_graph.js`
  - `js/three_pipeline_3d.js`

#### `dashboard/public/js/app.js`
- `switchTab(tabId)` removed handler for `'tab-3d-visualizer'`.
- Core controller functions removed: `init3DEngine()`, `set3DMode()`, `filter3DCloud()`, `setCameraPreset()`, `toggle3DAutoRotate()`, `toggle3DFullscreen()`, `triggerHnswSimulation()`, `toggle3DUploadZone()`, `toggle3DHyperparams()`, `handle3DFileSelected()`, `searchAll3D()`, `quickQuery3D()`, `execute3DSearch()`, `render3DSearchResults()`, `focusOn3DResultByIndex()`, `focusOn3DResult()`.
- Search synchronization removed from `renderSearchResults(data)`:
  - Call to `window.threeEngine.vectorSpaceModule.renderQueryResults(...)`.
  - Button "Xem trên 3D" on each search result card.
- `DOMContentLoaded` removed `setTimeout(init3DEngine, 80)`.

### 1.4 Prohibited Construct in `dimension_reduction_3d.py`
Inspection of `dashboard/scripts/dimension_reduction_3d.py` revealed:
- Line 121 contains: `mmap = np.memmap(v_path, dtype=dtype, mode="r", shape=(count, dim))`.
- Although this path is inside a fallback branch for non-existent datasets, automated adversarial audit tests scan for `memmap` across the repository. This must be replaced with `np.fromfile`.

---

## 2. Logic Chain

1. **Existence and Integrity of 3D Assets**:
   - Observation 1.1 confirms that all 5 required 3D files are present on disk, valid in syntax, and identical to commit `HEAD` (`1401398`).
   - Observation 1.2 provides an exact git restoration command in case of accidental modification.
2. **Identification of Wiring Deficits**:
   - Observation 1.3 details every point of disconnection between the frontend, backend, and 3D visualizer.
   - The files were disconnected during Milestone 2 cleanup, but the core 3D files themselves were never modified.
3. **Integration Strategy**:
   - To restore full 3D functionality without regressing Milestone 2 additions:
     - In `dashboard/server.js`: Re-add `/api/vectors-3d` and `/api/hnsw-topology-3d`. Both endpoints read `vectors_3d_cache.json` and return fallback structures if the cache is absent.
     - In `dashboard/public/css/custom.css`: Re-add the 3 3D CSS classes.
     - In `dashboard/public/index.html`: Re-add CDN scripts, `tab-3d-visualizer` tab button, `<section id="tab-3d-visualizer">`, and script tags, while leaving the Shards Probed and latency elements in `tab-search` untouched.
     - In `dashboard/public/js/app.js`: Re-add 3D controllers and cross-wiring while keeping Shard chip formatting and latency display intact in `renderSearchResults()`.
4. **Audit and Compliance**:
   - Observation 1.4 notes `np.memmap` in `dimension_reduction_3d.py`. Replacing this line with `np.fromfile` ensures 100% compliance with Acceptance Criterion 2 (zero `numpy.memmap`).

---

## 3. Caveats

1. **Active WebGL Context in Headless Tests**: In headless testing environments, WebGL contexts cannot initialize. `init3DEngine()` includes a try-catch block and checks container existence, allowing unit tests and `test_ui_render_harness.js` to execute safely.
2. **Data Cache Availability**: `data/processed/vectors_3d_cache.json` does not exist on disk by default. The server endpoints and `three_vector_space.js` handle fallback data gracefully, but generating a sample cache via `dimension_reduction_3d.py` provides immediate visual validation when the UI loads.
3. **Branch Divergence**: Commit `7e745d4` on branch `update` has deleted these files. Future merges from `update` must avoid overwriting the restored files on `main`.

---

## 4. Conclusion

1. All 5 3D UI files (`three_engine.js`, `three_hnsw_graph.js`, `three_pipeline_3d.js`, `three_vector_space.js`, and `dimension_reduction_3d.py`) are located, intact, and pass syntax compilation.
2. The exact restoration commands, modified dependent files, and required wiring edits have been mapped.
3. The Worker can execute restoration using the step-by-step plan detailed in `report.md`:
   - Step 1: Sanitize line 121 in `dimension_reduction_3d.py` (`np.memmap` -> `np.fromfile`).
   - Step 2: Restore routes in `dashboard/server.js`.
   - Step 3: Restore styles in `dashboard/public/css/custom.css`.
   - Step 4: Restore markup and CDNs in `dashboard/public/index.html`.
   - Step 5: Restore controllers and cross-wiring in `dashboard/public/js/app.js`.
   - Step 6: Verify via test suite and headless harness.

---

## 5. Verification Method

### 5.1 Verification Commands for Downstream Worker & Reviewer

1. **Verify 3D File Existence & Integrity**:
   ```powershell
   @(
     "dashboard/public/js/three_engine.js",
     "dashboard/public/js/three_hnsw_graph.js",
     "dashboard/public/js/three_pipeline_3d.js",
     "dashboard/public/js/three_vector_space.js",
     "dashboard/scripts/dimension_reduction_3d.py"
   ) | ForEach-Object { "$_ : $(Test-Path $_)" }
   ```
   Expected output: `True` for all 5 files.

2. **Verify Zero `numpy.memmap` in 3D Scripts & Core Index**:
   ```powershell
   Select-String -Path dashboard/scripts/dimension_reduction_3d.py -Pattern "memmap"
   Select-String -Path src/ann_index/*.py -Pattern "memmap"
   ```
   Expected output: 0 matches.

3. **Verify JavaScript Syntax**:
   ```powershell
   node -c dashboard/server.js
   node -c dashboard/public/js/app.js
   node -c dashboard/public/js/three_engine.js
   node -c dashboard/public/js/three_hnsw_graph.js
   node -c dashboard/public/js/three_pipeline_3d.js
   node -c dashboard/public/js/three_vector_space.js
   ```
   Expected output: Exit code 0 for all commands.

4. **Verify UI Render Harness & Search Metrics**:
   ```powershell
   node tests/test_ui_render_harness.js
   ```
   Expected output: PASS on all test cases including Shards Probed, latency, and shard chips.

5. **Verify Backend Tests**:
   ```powershell
   python -m pytest tests/test_two_tier_hnsw.py tests/test_search_edge_cases.py
   ```
   Expected output: All 43 tests pass.

### 5.2 Invalidation Conditions
- Any deletion of the 5 3D files.
- Loss of Shards Probed (`#result-shards-container`) or execution latency display in `tab-search`.
- Persistence of `numpy.memmap` in `dimension_reduction_3d.py`.
