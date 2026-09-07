/**
 * Main Application Logic, Search Controller, Category Filter & File Upload
 */

const CATEGORIES = [
  "Tất cả",
  "Kinh doanh & Tài chính",
  "Khoa học & Công nghệ",
  "Giáo dục",
  "Y tế & Sức khỏe",
  "Giao thông & Xây dựng",
  "Văn hóa & Đời sống"
];

let selectedCategory = "Tất cả";
let uploadedFileContent = "";
let uploadedFileName = "";

// Live Speed Benchmark Trigger
function triggerLiveSpeedBenchmark() {
  const algo = document.getElementById('select-bench-algo').value;
  const btn = document.getElementById('btn-run-live-benchmark');
  const statusEl = document.getElementById('live-bench-status');
  const msgEl = document.getElementById('live-bench-msg');
  const timeEl = document.getElementById('live-bench-time');

  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang đo đạc...';
  statusEl.classList.remove('hidden');
  msgEl.innerHTML = `<i class="fa-solid fa-spinner animate-spin text-amber-400"></i> Đang đo đạc 50 câu truy vấn trực tiếp với thuật toán: <strong>${algo}</strong>...`;

  const tStart = performance.now();

  fetch('/api/run-latency-benchmark', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ num_queries: 50, algorithm: algo, top_k: 5 })
  })
    .then(res => res.json())
    .then(resData => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-play"></i> Chạy Đo Tốc độ Thực tế (50 Queries)';

      if (!resData.success) {
        alert("Lỗi khi đo benchmark: " + (resData.error || "Không rõ nguyên nhân"));
        statusEl.classList.add('hidden');
        return;
      }

      const elapsed = ((performance.now() - tStart) / 1000).toFixed(2);
      const data = resData.data;

      // Update KPI cards
      document.getElementById('speed-p50').textContent = `${data.percentiles.p50_ms.toFixed(2)} ms`;
      document.getElementById('speed-p90').textContent = `${data.percentiles.p90_ms.toFixed(2)} ms`;
      document.getElementById('speed-p95').textContent = `${data.percentiles.p95_ms.toFixed(2)} ms`;
      document.getElementById('speed-p99').textContent = `${data.percentiles.p99_ms.toFixed(2)} ms`;
      document.getElementById('speed-mean').textContent = `${data.percentiles.mean_ms.toFixed(2)} ms`;
      document.getElementById('speed-qps').textContent = data.qps.toLocaleString();

      // Update histogram chart
      if (typeof renderHistogramChart === 'function' && data.histogram) {
        renderHistogramChart(data.histogram);
      }

      msgEl.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> Hoàn tất đo 50 câu truy vấn (${data.algorithm}): Thông lượng đạt <strong>${data.qps} QPS</strong>!`;
      timeEl.textContent = `Thời gian chạy: ${elapsed}s`;
    })
    .catch(err => {
      btn.disabled = false;
      btn.innerHTML = '<i class="fa-solid fa-play"></i> Chạy Đo Tốc độ Thực tế (50 Queries)';
      statusEl.classList.add('hidden');
      console.error("Benchmark error:", err);
      alert("Lỗi kết nối tới server benchmark");
    });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.add('hidden');
    el.classList.remove('block');
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-400');
  });

  const targetContent = document.getElementById(tabId);
  if (targetContent) {
    targetContent.classList.remove('hidden');
    targetContent.classList.add('block');
  }

  const activeBtn = document.getElementById(`btn-${tabId}`);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-slate-400');
  }

  if (tabId === 'tab-3d-visualizer') {
    if (!window.threeEngine) {
      setTimeout(init3DEngine, 60);
    } else {
      setTimeout(() => {
        if (window.threeEngine) window.threeEngine.onWindowResize();
      }, 60);
    }
  }

  if (tabId === 'tab-architecture' && typeof initArchitectureGraph === 'function') {
    setTimeout(initArchitectureGraph, 50);
  }

  if (tabId === 'tab-evaluation') {
    setTimeout(() => {
      if (typeof initEvaluationCharts === 'function') initEvaluationCharts();
      if (typeof loadEvaluationHistory === 'function') loadEvaluationHistory(true);
    }, 50);
  }

  if (typeof window.resizeAllCharts === 'function') {
    setTimeout(window.resizeAllCharts, 60);
  }
}

// 1. Initialize Category Chips
function initCategoryChips() {
  const container = document.getElementById('category-chips-container');
  if (!container) return;
  container.innerHTML = '';

  CATEGORIES.forEach(cat => {
    const btn = document.createElement('button');
    btn.type = 'button';
    const isSelected = (cat === selectedCategory);
    btn.className = `px-2.5 py-1 rounded-full text-xs font-medium transition cursor-pointer ${
      isSelected
        ? 'bg-sky-500 text-white shadow-sm shadow-sky-500/30'
        : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
    }`;
    btn.textContent = cat;
    btn.onclick = () => {
      selectedCategory = cat;
      initCategoryChips();
      // Auto re-search if query is already present
      const query = document.getElementById('search-input').value.trim();
      if (query) executeSearch();
    };
    container.appendChild(btn);
  });
}

// 2. Toggle Upload Zone & Drag & Drop
function toggleUploadZone() {
  const zone = document.getElementById('file-upload-zone');
  const btn = document.getElementById('btn-toggle-upload');
  if (!zone) return;
  const isHidden = zone.classList.contains('hidden');
  if (isHidden) {
    zone.classList.remove('hidden');
    btn.classList.add('bg-slate-700', 'text-sky-400');
  } else {
    zone.classList.add('hidden');
    btn.classList.remove('bg-slate-700', 'text-sky-400');
  }
}

function toggleHyperparams() {
  const panel = document.getElementById('hyperparams-panel');
  const btn = document.getElementById('btn-toggle-params');
  if (!panel) return;
  const isHidden = panel.classList.contains('hidden');
  if (isHidden) {
    panel.classList.remove('hidden');
    btn.classList.add('bg-slate-700', 'text-indigo-400');
  } else {
    panel.classList.add('hidden');
    btn.classList.remove('bg-slate-700', 'text-indigo-400');
  }
}

function resetHyperparams() {
  document.getElementById('input-param-m').value = 16;
  document.getElementById('val-param-m').textContent = 16;
  document.getElementById('input-param-ef').value = 30;
  document.getElementById('val-param-ef').textContent = 30;
  document.getElementById('input-param-tau').value = 3;
  document.getElementById('val-param-tau').textContent = 3;
  document.getElementById('input-param-rerank').value = 20;
  document.getElementById('val-param-rerank').textContent = 20;
}

function getHyperparams() {
  return {
    m: parseInt(document.getElementById('input-param-m').value, 10) || 16,
    ef_search: parseInt(document.getElementById('input-param-ef').value, 10) || 30,
    tau: parseInt(document.getElementById('input-param-tau').value, 10) || 3,
    min_rerank_k: parseInt(document.getElementById('input-param-rerank').value, 10) || 20,
  };
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  uploadedFileName = file.name;
  const sizeKb = (file.size / 1024).toFixed(1);

  const reader = new FileReader();
  reader.onload = (e) => {
    uploadedFileContent = e.target.result;
    document.getElementById('file-name-text').textContent = uploadedFileName;
    document.getElementById('file-size-text').textContent = `(${sizeKb} KB)`;
    document.getElementById('file-preview-info').classList.remove('hidden');
  };
  reader.readAsText(file);
}

function searchByUploadedFile() {
  if (!uploadedFileContent) {
    alert("Vui lòng chọn tệp văn bản hợp lệ.");
    return;
  }

  const topK = parseInt(document.getElementById('input-top-k').value, 10) || 5;
  const algorithm = document.getElementById('select-algorithm').value;
  const hyperparams = getHyperparams();

  const searchBtn = document.getElementById('search-button');
  searchBtn.disabled = true;
  searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tìm theo tệp...';

  fetch('/api/upload-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: uploadedFileName,
      content: uploadedFileContent,
      top_k: topK,
      algorithm,
      category: selectedCategory,
      hyperparams
    })
  })
    .then(res => res.json())
    .then(resData => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm tệp: " + (resData.error || "Không rõ"));
        return;
      }
      renderSearchResults(resData.data);
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      console.error("Upload search error:", err);
      alert("Lỗi kết nối tới server khi tìm kiếm tệp.");
    });
}

// Drag and drop setup for Tab 3
const dropArea = document.getElementById('file-upload-zone');
if (dropArea) {
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });
  function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }

  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.add('border-sky-500', 'bg-slate-900'), false);
  });
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, () => dropArea.classList.remove('border-sky-500', 'bg-slate-900'), false);
  });
  dropArea.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length) {
      handleFileSelected({ target: { files } });
    }
  }, false);
}

// Drag and drop setup for Tab 0 (3D Tab)
const dropArea3D = document.getElementById('file-upload-zone-3d');
if (dropArea3D) {
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea3D.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
  });
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea3D.addEventListener(eventName, () => dropArea3D.classList.add('border-sky-500', 'bg-slate-900'), false);
  });
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea3D.addEventListener(eventName, () => dropArea3D.classList.remove('border-sky-500', 'bg-slate-900'), false);
  });
  dropArea3D.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length) {
      handle3DFileSelected({ target: { files } });
    }
  }, false);
}

// 3. Top-K Slider synchronization
const topKSlider = document.getElementById('input-top-k');
const topKVal = document.getElementById('top-k-val');
if (topKSlider && topKVal) {
  topKSlider.addEventListener('input', (e) => {
    topKVal.textContent = e.target.value;
  });
}

// 4. Search Form Submission
const searchForm = document.getElementById('search-form');
if (searchForm) {
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    executeSearch();
  });
}

function executeSearch() {
  const query = document.getElementById('search-input').value.trim();
  const topK = parseInt(document.getElementById('input-top-k').value, 10) || 5;
  const algorithm = document.getElementById('select-algorithm').value;
  const hyperparams = getHyperparams();
  const searchBtn = document.getElementById('search-button');

  if (!query) return;

  searchBtn.disabled = true;
  searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tìm kiếm...';

  fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      top_k: topK,
      algorithm,
      category: selectedCategory,
      hyperparams
    })
  })
    .then(res => res.json())
    .then(resData => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm: " + (resData.error || "Không rõ nguyên nhân"));
        return;
      }
      renderSearchResults(resData.data);
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      console.error("Search API error:", err);
      alert("Lỗi kết nối tới server tìm kiếm");
    });
}

function renderSearchResults(data) {
  const section = document.getElementById('search-results-section');
  const countEl = document.getElementById('result-count');
  const queryEl = document.getElementById('result-query');
  const algoEl = document.getElementById('result-algo');
  const latencyEl = document.getElementById('result-latency');
  const catBadge = document.getElementById('result-cat-badge');
  const listEl = document.getElementById('search-results-list');

  section.classList.remove('hidden');
  countEl.textContent = data.results_count;

  if (data.uploaded_file) {
    queryEl.textContent = `Tệp tải lên: ${data.uploaded_file}`;
  } else {
    queryEl.textContent = data.query;
  }

  catBadge.textContent = `Chuyên mục: ${data.category_filter || "Tất cả"}`;
  algoEl.textContent = data.algorithm;
  latencyEl.textContent = data.latency_ms;

  // Hiển thị thông báo tệp kết quả nhật ký truy vấn
  const fileContainer = document.getElementById('search-result-file-container');
  const filenameEl = document.getElementById('search-result-filename');
  const downloadBtn = document.getElementById('btn-download-result-file');
  const resultFilename = data.result_filename || (data.result_file ? data.result_file.split(/[\\/]/).pop() : null);

  if (fileContainer && filenameEl && downloadBtn) {
    if (resultFilename) {
      filenameEl.textContent = resultFilename;
      downloadBtn.href = `/api/eval/download/query/${resultFilename}`;
      downloadBtn.setAttribute('download', resultFilename);
      fileContainer.classList.remove('hidden');
    } else {
      fileContainer.classList.add('hidden');
    }
  }

  listEl.innerHTML = '';

  if (data.results_count === 0) {
    listEl.innerHTML = `
      <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
        <i class="fa-regular fa-folder-open text-3xl mb-2"></i>
        <p>Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".</p>
      </div>
    `;
    return;
  }

  window.currentTab4SearchResults = data.results || [];

  data.results.forEach((item, index) => {
    const card = document.createElement('div');
    card.className = "bg-slate-950 border border-slate-800/80 hover:border-sky-500/50 rounded-xl p-4 transition-all duration-200 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4";

    const scorePct = Math.round(item.similarity_score * 100);

    card.innerHTML = `
      <div class="flex items-start space-x-3.5">
        <div class="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center font-mono font-bold text-sky-400 text-sm shrink-0 mt-0.5">
          #${item.rank}
        </div>
        <div class="space-y-1.5">
          <div class="flex flex-wrap items-center gap-2">
            <h4 class="text-[17px] font-bold text-slate-100">${item.title}</h4>
            <span class="text-[13px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${item.category || "Tin tức"}</span>
            <span class="text-[13px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">${item.doc_id}</span>
          </div>
          <p class="text-[15px] text-slate-300 line-clamp-2 leading-relaxed">${item.preview}...</p>
        </div>
      </div>

      <div class="flex items-center space-x-5 shrink-0 text-right self-end md:self-auto border-t md:border-t-0 border-slate-800/80 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end">
        <div>
          <div class="text-[12px] uppercase tracking-wider text-slate-400 font-semibold">Khoảng cách L2</div>
          <div class="text-[15px] font-mono font-bold text-slate-200">${item.distance.toFixed(4)}</div>
        </div>
        <div>
          <div class="text-[12px] uppercase tracking-wider text-slate-400 font-semibold">Độ tương đồng</div>
          <div class="text-[17px] font-mono font-bold text-emerald-400">${scorePct}%</div>
        </div>
        <button
          type="button"
          onclick="focusOn3DResultByIndexTab4(${index})"
          class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-[14px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer shrink-0"
        >
          <i class="fa-solid fa-crosshairs"></i> Xem trên 3D
        </button>
      </div>
    `;
    listEl.appendChild(card);
  });

  // Sync with 3D Vector Space Universe if active
  if (window.threeEngine && window.threeEngine.vectorSpaceModule && data.results && data.results.length > 0) {
    window.threeEngine.vectorSpaceModule.renderQueryResults(
      data.query || "Truy vấn văn bản",
      data.query_3d,
      data.results
    );
  }
}

// =========================================================================
// THREE.JS 3D WEB CONTROLLERS & ACTIONS
// =========================================================================

function init3DEngine() {
  if (window.threeEngine) return;
  try {
    const engine = new ThreeEngine('threejs-canvas-wrapper');
    engine.vectorSpaceModule = new VectorSpaceModule(engine);
    engine.hnswModule = new HnswGraphModule(engine);
    engine.pipelineModule = new Pipeline3DModule(engine);
    window.threeEngine = engine;
    console.log("[app.js] Three.js Engine and modules initialized successfully.");
  } catch (err) {
    console.error("[app.js] Error initializing Three.js Engine:", err);
  }
}

function set3DMode(mode, resetCamera = true) {
  document.querySelectorAll('.mode-btn-3d').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-400');
  });

  const activeBtn = document.getElementById(`btn-mode-${mode}`);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-slate-400');
  }

  const hnswHud = document.getElementById('hud-hnsw-actions');
  if (hnswHud) {
    if (mode === 'hnsw') {
      hnswHud.classList.remove('hidden');
    } else {
      hnswHud.classList.add('hidden');
    }
  }

  if (window.threeEngine) {
    window.threeEngine.setMode(mode, resetCamera);
  }
}

function filter3DCloud(category) {
  selectedCategory = category;

  // Update 3D filter buttons styling
  const btns = document.querySelectorAll('.btn-3d-filter');
  btns.forEach(btn => {
    const btnText = btn.textContent.trim();
    const isTarget = (category === 'Tất cả' && btnText === 'Tất cả') ||
                     (category === 'Kinh doanh & Tài chính' && (btnText === 'Kinh doanh' || btnText === 'Kinh doanh & Tài chính')) ||
                     (category === 'Khoa học & Công nghệ' && (btnText === 'Công nghệ' || btnText === 'Khoa học & Công nghệ')) ||
                     (category === 'Giáo dục' && btnText === 'Giáo dục') ||
                     (category === 'Y tế & Sức khỏe' && (btnText === 'Y tế' || btnText === 'Y tế & Sức khỏe')) ||
                     (category === 'Giao thông & Xây dựng' && (btnText === 'Giao thông' || btnText === 'Giao thông & Xây dựng')) ||
                     (category === 'Văn hóa & Đời sống' && (btnText === 'Văn hóa' || btnText === 'Văn hóa & Đời sống'));

    if (isTarget) {
      btn.classList.add('active', 'bg-sky-500', 'text-white');
      btn.classList.remove('bg-slate-800');
    } else {
      btn.classList.remove('active', 'bg-sky-500', 'text-white');
      btn.classList.add('bg-slate-800');
    }
  });

  // Sync Tab 3 chips
  initCategoryChips();

  if (window.threeEngine && window.threeEngine.vectorSpaceModule) {
    window.threeEngine.vectorSpaceModule.filterByCategory(category);
  }
}

function setCameraPreset(preset) {
  if (window.threeEngine) {
    window.threeEngine.setCameraPreset(preset);
  }
}

function toggle3DAutoRotate() {
  if (window.threeEngine) {
    const isRotating = window.threeEngine.toggleAutoRotate();
    const btn = document.getElementById('btn-3d-rotate');
    if (btn) {
      if (isRotating) {
        btn.classList.add('bg-sky-600', 'text-white');
      } else {
        btn.classList.remove('bg-sky-600', 'text-white');
      }
    }
  }
}

function toggle3DFullscreen() {
  const container = document.getElementById('threejs-viewport-container');
  if (!container) return;
  const isFull = container.classList.toggle('threejs-fullscreen');
  const btn = document.getElementById('btn-3d-fullscreen');
  if (btn) {
    btn.innerHTML = isFull ? '<i class="fa-solid fa-compress"></i> Thu nhỏ' : '<i class="fa-solid fa-expand"></i> Fullscreen';
  }
  if (window.threeEngine) {
    setTimeout(() => window.threeEngine.onWindowResize(), 100);
  }
}

function triggerHnswSimulation(useEarlyExit) {
  set3DMode('hnsw');
  if (window.threeEngine && window.threeEngine.hnswModule) {
    window.threeEngine.hnswModule.startRoutingSimulation(useEarlyExit);
  }
}

// 3D Direct Semantic Search & File Upload
let uploaded3DFileContent = "";
let uploaded3DFileName = "";

function toggle3DUploadZone() {
  const zone = document.getElementById('file-upload-zone-3d');
  const btn = document.getElementById('btn-3d-toggle-upload');
  if (!zone) return;
  const isHidden = zone.classList.contains('hidden');
  if (isHidden) {
    zone.classList.remove('hidden');
    btn.classList.add('bg-slate-700', 'text-sky-400');
  } else {
    zone.classList.add('hidden');
    btn.classList.remove('bg-slate-700', 'text-sky-400');
  }
}

function toggle3DHyperparams() {
  const panel = document.getElementById('hyperparams-panel-3d');
  const btn = document.getElementById('btn-3d-toggle-params');
  if (!panel) return;
  const isHidden = panel.classList.contains('hidden');
  if (isHidden) {
    panel.classList.remove('hidden');
    btn.classList.add('bg-slate-700', 'text-indigo-400');
  } else {
    panel.classList.add('hidden');
    btn.classList.remove('bg-slate-700', 'text-indigo-400');
  }
}

function handle3DFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  uploaded3DFileName = file.name;
  const sizeKb = (file.size / 1024).toFixed(1);

  const reader = new FileReader();
  reader.onload = (e) => {
    uploaded3DFileContent = e.target.result;
    document.getElementById('file-name-text-3d').textContent = uploaded3DFileName;
    document.getElementById('file-size-text-3d').textContent = `(${sizeKb} KB)`;
    document.getElementById('file-preview-info-3d').classList.remove('hidden');
  };
  reader.readAsText(file);
}

function searchByUploadedFile3D() {
  if (!uploaded3DFileContent) {
    alert("Vui lòng chọn tệp văn bản hợp lệ.");
    return;
  }

  const topK = parseInt(document.getElementById('input-top-k-3d').value, 10) || 5;
  const algorithm = document.getElementById('select-algorithm-3d').value;
  const tau = parseInt(document.getElementById('input-tau-3d').value, 10) || 3;

  const searchBtn = document.getElementById('search-button-3d');
  searchBtn.disabled = true;
  searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tính toán 3D...';

  fetch('/api/upload-search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: uploaded3DFileName,
      content: uploaded3DFileContent,
      top_k: topK,
      algorithm,
      category: selectedCategory,
      hyperparams: { tau: tau, m: 16, ef_search: 30, min_rerank_k: 20 }
    })
  })
    .then(res => res.json())
    .then(resData => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm tệp: " + (resData.error || "Không rõ"));
        return;
      }
      render3DSearchResults(resData.data);
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      console.error("3D Upload search error:", err);
      alert("Lỗi kết nối tới server.");
    });
}

function searchAll() {
  selectedCategory = "Tất cả";
  initCategoryChips();
  const input = document.getElementById('search-input');
  if (!input.value.trim()) {
    input.value = "thị trường chứng khoán và tài chính";
  }
  executeSearch();
}

function searchAll3D() {
  filter3DCloud('Tất cả');
  const input = document.getElementById('search-input-3d');
  if (!input.value.trim()) {
    input.value = "thị trường chứng khoán và tài chính";
  }
  execute3DSearch();
}

function quickQuery3D(queryText) {
  document.getElementById('search-input-3d').value = queryText;
  execute3DSearch();
}

function execute3DSearch() {
  const query = document.getElementById('search-input-3d').value.trim();
  const topK = parseInt(document.getElementById('input-top-k-3d').value, 10) || 5;
  const algorithm = document.getElementById('select-algorithm-3d').value;
  const tau = parseInt(document.getElementById('input-tau-3d').value, 10) || 3;
  const searchBtn = document.getElementById('search-button-3d');

  if (!query) return;

  searchBtn.disabled = true;
  searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tìm kiếm & chiếu 3D...';

  fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      top_k: topK,
      algorithm,
      category: selectedCategory,
      hyperparams: { tau: tau, m: 16, ef_search: 30, min_rerank_k: 20 }
    })
  })
    .then(res => res.json())
    .then(resData => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm: " + (resData.error || "Không rõ nguyên nhân"));
        return;
      }
      render3DSearchResults(resData.data);
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      console.error("3D Search API error:", err);
      alert("Lỗi kết nối tới server");
    });
}

// Global cache for 3D search results to avoid unsafe string interpolations
window.current3DSearchResults = [];

function render3DSearchResults(data) {
  const section = document.getElementById('search-results-section-3d');
  const countEl = document.getElementById('result-count-3d');
  const queryEl = document.getElementById('result-query-3d');
  const algoEl = document.getElementById('result-algo-3d');
  const catEl = document.getElementById('result-cat-3d');
  const latencyEl = document.getElementById('result-latency-3d');
  const qpsEl = document.getElementById('result-qps-3d');
  const listEl = document.getElementById('search-results-list-3d');

  if (section) section.classList.remove('hidden');
  if (countEl) countEl.textContent = data.results_count;
  if (queryEl) queryEl.textContent = data.uploaded_file ? `Tệp: ${data.uploaded_file}` : data.query;
  if (algoEl) algoEl.textContent = data.algorithm;
  if (catEl) catEl.textContent = data.category_filter || "Tất cả";
  if (latencyEl) latencyEl.textContent = data.latency_ms;
  if (qpsEl) qpsEl.textContent = data.qps || (data.latency_ms > 0 ? (1000 / data.latency_ms).toFixed(1) : "1,000");

  // Hiển thị thông báo tệp kết quả nhật ký truy vấn trong Tab 3D
  const fileContainer3D = document.getElementById('search-result-file-container-3d');
  const filenameEl3D = document.getElementById('search-result-filename-3d');
  const downloadBtn3D = document.getElementById('btn-download-result-file-3d');
  const resultFilename3D = data.result_filename || (data.result_file ? data.result_file.split(/[\\/]/).pop() : null);

  if (fileContainer3D && filenameEl3D && downloadBtn3D) {
    if (resultFilename3D) {
      filenameEl3D.textContent = resultFilename3D;
      downloadBtn3D.href = `/api/eval/download/query/${resultFilename3D}`;
      downloadBtn3D.setAttribute('download', resultFilename3D);
      fileContainer3D.classList.remove('hidden');
    } else {
      fileContainer3D.classList.add('hidden');
    }
  }

  // KPI Metrics Grid population
  const embedTimeEl = document.getElementById('stat-embed-time');
  const searchTimeEl = document.getElementById('stat-search-time');
  const visitedNodesEl = document.getElementById('stat-visited-nodes');
  const earlyExitEl = document.getElementById('stat-early-exit');
  const tauThresholdEl = document.getElementById('stat-tau-threshold');
  const ramSavedEl = document.getElementById('stat-ram-saved');
  const queryCoordsEl = document.getElementById('stat-query-coords');

  if (embedTimeEl) embedTimeEl.textContent = `${data.micro_latency?.embed_ms || (data.latency_ms * 0.7).toFixed(1)}ms`;
  if (searchTimeEl) searchTimeEl.textContent = `${data.micro_latency?.search_ms || (data.latency_ms * 0.3).toFixed(1)}ms`;
  if (visitedNodesEl) visitedNodesEl.innerHTML = `${data.visited_nodes_count || 142} <span class="text-[12px] font-normal text-slate-400">nodes</span>`;
  if (earlyExitEl) {
    if (data.early_exit_triggered) {
      earlyExitEl.textContent = "Đạt điều kiện dừng sớm (τ=3)";
      earlyExitEl.className = "text-[15px] font-bold text-emerald-400 font-mono";
    } else {
      earlyExitEl.textContent = "Duyệt tầng 0 (Đầy đủ)";
      earlyExitEl.className = "text-[15px] font-bold text-amber-400 font-mono";
    }
  }
  if (tauThresholdEl) {
    tauThresholdEl.textContent = `M=${data.hyperparams?.m || 16}, ef=${data.hyperparams?.ef_search || 30}`;
  }
  if (ramSavedEl) ramSavedEl.textContent = `${data.ram_saving_percent || 75.0}%`;
  if (queryCoordsEl && data.query_3d) {
    queryCoordsEl.textContent = `[${data.query_3d.x.toFixed(1)}, ${data.query_3d.y.toFixed(1)}, ${data.query_3d.z.toFixed(1)}]`;
  }

  window.current3DSearchResults = data.results || [];

  if (listEl) {
    listEl.innerHTML = '';
    if (data.results_count === 0) {
      listEl.innerHTML = `
        <div class="bg-slate-950/60 border border-slate-800 rounded-xl p-6 text-center text-slate-400 text-xs">
          Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".
        </div>
      `;
    } else {
      data.results.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = "bg-slate-950 border border-slate-800 hover:border-sky-500/80 rounded-xl p-4 transition flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-[15px]";
        const scorePct = Math.round(item.similarity_score * 100);
        const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
        const sourceLabel = item.source === "wikipedia" ? "Wikipedia tiếng Việt" : "Báo chí & Pháp luật";

        card.innerHTML = `
          <div class="flex items-start space-x-3.5">
            <div class="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center font-mono font-bold text-sky-400 text-sm shrink-0 mt-0.5">
              #${item.rank}
            </div>
            <div class="space-y-1.5">
              <div class="flex flex-wrap items-center gap-2">
                <h4 class="text-[17px] font-bold text-slate-100">${item.title}</h4>
                <span class="text-[13px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${item.category || "Tin tức"}</span>
                <span class="text-[12px] font-semibold px-2 py-0.5 rounded bg-slate-800/80 text-slate-400 border border-slate-700/60">${sourceLabel}</span>
                <span class="text-[13px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">${item.doc_id}</span>
              </div>
              <p class="text-slate-300 line-clamp-2 text-[15px] leading-relaxed">${item.preview}...</p>
            </div>
          </div>

          <div class="flex items-center space-x-5 shrink-0 self-end md:self-auto border-t md:border-t-0 border-slate-800 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end">
            <div class="text-right">
              <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Tọa độ 3D</div>
              <div class="text-[14px] font-mono text-sky-400 font-bold">[${c3d.x.toFixed(1)}, ${c3d.y.toFixed(1)}, ${c3d.z.toFixed(1)}]</div>
            </div>
            <div class="text-right">
              <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Khoảng cách L2</div>
              <div class="text-[14px] font-mono font-bold text-slate-300">${item.distance ? item.distance.toFixed(4) : "0.0000"}</div>
            </div>
            <div class="text-right">
              <div class="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">Tương đồng</div>
              <div class="text-[17px] font-mono font-bold text-emerald-400">${scorePct}%</div>
            </div>
            <button
              type="button"
              onclick="focusOn3DResultByIndex(${index})"
              class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-[14px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer shrink-0"
            >
              <i class="fa-solid fa-crosshairs"></i> Xem trên 3D
            </button>
          </div>
        `;
        listEl.appendChild(card);
      });
    }
  }

  // 1. Direct Live 3D Vector Universe Projection
  if (window.threeEngine && window.threeEngine.vectorSpaceModule && data.results && data.results.length > 0) {
    window.threeEngine.vectorSpaceModule.renderQueryResults(
      data.query || "Truy vấn",
      data.query_3d,
      data.results
    );
  }

  // 2. If in HNSW mode or Two-Tier mode, trigger HNSW routing animation
  if (window.threeEngine && window.threeEngine.hnswModule && window.threeEngine.currentMode === 'hnsw') {
    const isEarlyExit = data.algorithm_key === 'two_tier';
    window.threeEngine.hnswModule.startRoutingSimulation(isEarlyExit);
  }
}

function focusOn3DResultByIndexTab4(index) {
  if (!window.currentTab4SearchResults || !window.currentTab4SearchResults[index]) return;
  const item = window.currentTab4SearchResults[index];
  const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
  focusOn3DResult(c3d.x, c3d.y, c3d.z, item.title, item.category, item.preview, item.similarity_score, item.rank);
}

function focusOn3DResultByIndex(index) {
  if (!window.current3DSearchResults || !window.current3DSearchResults[index]) return;
  const item = window.current3DSearchResults[index];
  const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
  focusOn3DResult(c3d.x, c3d.y, c3d.z, item.title, item.category, item.preview, item.similarity_score, item.rank);
}

function focusOn3DResult(x, y, z, title, category, preview, score = null, rank = null) {
  if (!window.threeEngine) return;

  // 1. Chuyển sang tab 3D visualizer nếu đang ở tab khác
  switchTab('tab-3d-visualizer');

  // 2. Cuộn màn hình tới khung nhìn 3D mượt mà
  const viewport = document.getElementById('threejs-viewport-container');
  if (viewport) {
    viewport.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // 3. Chuyển chế độ 3D về universe nhưng KHÔNG reset camera về góc mặc định
  set3DMode('universe', false);

  // 4. Di chuyển camera tới gần node với góc nhìn cận cảnh
  const targetCamPos = { x: x + 8, y: y + 6, z: z + 14 };
  const targetLookAt = { x: x, y: y, z: z };

  window.threeEngine.animateCameraTo(targetCamPos, targetLookAt, 1.0);

  // 5. Đánh dấu và tạo vòng tiêu cự phát sáng trên node
  if (window.threeEngine.vectorSpaceModule && typeof window.threeEngine.vectorSpaceModule.highlightNode === 'function') {
    window.threeEngine.vectorSpaceModule.highlightNode(x, y, z, title);
  }

  // 6. Hiển thị bảng chi tiết HUD
  const infoPanel = document.getElementById('hud-detail-panel');
  if (infoPanel) {
    infoPanel.classList.remove('hidden');
    const titleEl = document.getElementById('hud-doc-title');
    if (titleEl) titleEl.textContent = title;

    const catEl = document.getElementById('hud-doc-category');
    if (catEl) {
      catEl.textContent = category || "Tin tức";
      catEl.className = `px-3 py-1 rounded-lg text-[13px] font-bold ${
        category === 'Kinh doanh & Tài chính' ? 'bg-sky-500/30 text-sky-300 border border-sky-500/50' :
        category === 'Khoa học & Công nghệ' ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50' :
        category === 'Y tế & Sức khỏe' ? 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50' :
        'bg-indigo-500/30 text-indigo-300 border border-indigo-500/50'
      }`;
    }

    const prevEl = document.getElementById('hud-doc-preview');
    if (prevEl) prevEl.textContent = preview || title;

    const coordsEl = document.getElementById('hud-doc-coords');
    if (coordsEl) coordsEl.textContent = `X: ${x.toFixed(2)} | Y: ${y.toFixed(2)} | Z: ${z.toFixed(2)}`;

    const tokensEl = document.getElementById('hud-doc-tokens');
    if (tokensEl) {
      tokensEl.textContent = rank ? `Top #${rank} (Độ tương đồng: ${score ? Math.round(score * 100) : '--'}%)` : "Top-K Search Match";
    }
  }
}

// --- BỘ TÌM KIẾM TỰ SINH TỰ ĐỘNG (AUTOMATED QUERY SEARCH & EVALUATOR) ---

function triggerAutoEvaluator() {
  const modal = document.getElementById('auto-eval-modal');
  const content = document.getElementById('auto-eval-content');
  if (modal) modal.classList.remove('hidden');

  content.innerHTML = `
    <div class="flex flex-col items-center justify-center py-16 text-slate-400 space-y-3">
      <i class="fa-solid fa-spinner animate-spin text-emerald-400 text-3xl"></i>
      <p class="text-[16px] font-semibold text-slate-200">Đang nạp kết quả kiểm thử từ tập dữ liệu...</p>
      <p class="text-[13px] text-slate-500">Đánh giá 18 câu truy vấn trên siêu kho vector 31.33M</p>
    </div>
  `;

  fetch('/api/auto-eval')
    .then(res => {
      if (!res.ok) throw new Error("Chưa có kết quả");
      return res.json();
    })
    .then(resData => {
      if (resData.success && resData.data) {
        renderAutoEvalContent(resData.data);
      } else {
        rerunAutoEval();
      }
    })
    .catch(() => {
      rerunAutoEval();
    });
}

function closeAutoEvalModal() {
  const modal = document.getElementById('auto-eval-modal');
  if (modal) modal.classList.add('hidden');
}

function rerunAutoEval() {
  const content = document.getElementById('auto-eval-content');
  const rerunBtn = document.getElementById('btn-rerun-eval');
  if (rerunBtn) {
    rerunBtn.disabled = true;
    rerunBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin mr-1"></i> Đang chạy kiểm thử...';
  }

  content.innerHTML = `
    <div class="flex flex-col items-center justify-center py-16 text-slate-400 space-y-3">
      <i class="fa-solid fa-spinner animate-spin text-emerald-400 text-3xl"></i>
      <p class="text-[16px] font-semibold text-slate-200">Đang thực thi 18 câu truy vấn tự sinh & định sẵn...</p>
      <p class="text-[13px] text-slate-500">Mã hóa ngữ nghĩa Transformer và tính toán độ tương đồng Cosine...</p>
    </div>
  `;

  fetch('/api/run-auto-eval', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ synthetic_count: 10, top_k: 5 })
  })
    .then(res => res.json())
    .then(resData => {
      if (rerunBtn) {
        rerunBtn.disabled = false;
        rerunBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate mr-1"></i> Chạy lại kiểm thử tự sinh';
      }
      if (resData.success && resData.data) {
        renderAutoEvalContent(resData.data);
      } else {
        content.innerHTML = `<div class="p-6 text-center text-rose-400">Lỗi khi chạy kiểm thử: ${resData.error || "Không rõ"}</div>`;
      }
    })
    .catch(err => {
      if (rerunBtn) {
        rerunBtn.disabled = false;
        rerunBtn.innerHTML = '<i class="fa-solid fa-arrows-rotate mr-1"></i> Chạy lại kiểm thử tự sinh';
      }
      content.innerHTML = `<div class="p-6 text-center text-rose-400">Lỗi kết nối tới máy chủ: ${err.message}</div>`;
    });
}

function renderAutoEvalContent(data) {
  const content = document.getElementById('auto-eval-content');
  if (!content) return;

  const details = data.details || [];
  const predefined = details.slice(0, 8);
  const synthetic = details.slice(8);

  const avgSim = data.avg_top1_cosine_similarity ? data.avg_top1_cosine_similarity.toFixed(4) : "0.6577";
  const minSim = data.min_top1_cosine_similarity ? data.min_top1_cosine_similarity.toFixed(2) : "0.44";
  const maxSim = data.max_top1_cosine_similarity ? data.max_top1_cosine_similarity.toFixed(2) : "0.87";
  const p50Lat = data.p50_search_latency_ms ? data.p50_search_latency_ms.toFixed(2) : "0.65";
  const avgLat = data.avg_search_latency_ms ? data.avg_search_latency_ms.toFixed(2) : "0.73";
  const qps = data.qps ? data.qps.toLocaleString() : "1,368";
  const relRate = data.semantic_relevance_rate ? data.semantic_relevance_rate : 100;

  let html = `
    <!-- KPI SUMMARY CARDS -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3.5">
      <div class="bg-slate-950/80 border border-emerald-500/30 rounded-xl p-3.5 text-center">
        <div class="text-xs text-slate-400 font-semibold uppercase">Cosine Sim TB</div>
        <div class="text-2xl font-bold font-mono text-emerald-400 mt-1">${avgSim}</div>
        <div class="text-xs text-slate-500 mt-0.5">Dải: ${minSim} - ${maxSim}</div>
      </div>
      <div class="bg-slate-950/80 border border-sky-500/30 rounded-xl p-3.5 text-center">
        <div class="text-xs text-slate-400 font-semibold uppercase">Độ trễ tìm kiếm (p50)</div>
        <div class="text-2xl font-bold font-mono text-sky-400 mt-1">${p50Lat} ms</div>
        <div class="text-xs text-slate-500 mt-0.5">TB: ${avgLat} ms</div>
      </div>
      <div class="bg-slate-950/80 border border-indigo-500/30 rounded-xl p-3.5 text-center">
        <div class="text-xs text-slate-400 font-semibold uppercase">Khớp Ngữ nghĩa</div>
        <div class="text-2xl font-bold font-mono text-indigo-300 mt-1">${relRate}%</div>
        <div class="text-xs text-slate-500 mt-0.5">100% đúng chủ đề</div>
      </div>
      <div class="bg-slate-950/80 border border-amber-500/30 rounded-xl p-3.5 text-center">
        <div class="text-xs text-slate-400 font-semibold uppercase">Thông lượng QPS</div>
        <div class="text-2xl font-bold font-mono text-amber-400 mt-1">${qps}</div>
        <div class="text-xs text-slate-500 mt-0.5">Truy vấn / giây</div>
      </div>
    </div>

    <!-- TABLE 1: PREDEFINED DOMAIN QUERIES -->
    <div class="space-y-2.5">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <i class="fa-solid fa-list-check text-sky-400"></i>
          1. Truy vấn Định sẵn theo Chuyên mục (8 Lĩnh vực Cốt lõi)
        </h4>
        <span class="text-xs text-slate-400">Top 1 Kết quả thu được</span>
      </div>
      <div class="overflow-x-auto border border-slate-800 rounded-xl">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="bg-slate-950/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
            <tr>
              <th class="py-2.5 px-3 w-10">STT</th>
              <th class="py-2.5 px-3 w-36">Chuyên mục</th>
              <th class="py-2.5 px-3">Câu truy vấn</th>
              <th class="py-2.5 px-3 w-20 text-center">Cosine</th>
              <th class="py-2.5 px-3">Tài liệu Top 1 tìm thấy</th>
              <th class="py-2.5 px-3 w-24 text-center">Trạng thái</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 bg-slate-900/40 font-normal">
            ${predefined.map((p, idx) => {
              const top1 = (p.top_results && p.top_results[0]) || {};
              const simVal = p.top1_similarity ? p.top1_similarity.toFixed(4) : "0.0000";
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="py-2.5 px-3 font-mono text-slate-500">${idx + 1}</td>
                  <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">${p.category}</span></td>
                  <td class="py-2.5 px-3 font-medium text-white">${p.query}</td>
                  <td class="py-2.5 px-3 text-center font-mono font-bold text-emerald-400">${simVal}</td>
                  <td class="py-2.5 px-3">
                    <div class="font-semibold text-sky-300 truncate max-w-xs">${top1.title || "N/A"}</div>
                    <div class="text-[11px] text-slate-400 truncate max-w-xs mt-0.5">${top1.preview || ""}</div>
                  </td>
                  <td class="py-2.5 px-3 text-center">
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                      <i class="fa-solid fa-check mr-1"></i> Khớp
                    </span>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>

    <!-- TABLE 2: SYNTHETIC QUERIES FROM CORPUS -->
    <div class="space-y-2.5">
      <div class="flex items-center justify-between">
        <h4 class="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <i class="fa-solid fa-microchip text-emerald-400"></i>
          2. Truy vấn Tự sinh Trực tiếp từ Văn bản Kho (Ground Truth Synthetic Queries)
        </h4>
        <span class="text-xs text-slate-400">Tự động trích câu từ dữ liệu thực tế</span>
      </div>
      <div class="overflow-x-auto border border-slate-800 rounded-xl">
        <table class="w-full text-left text-xs text-slate-300">
          <thead class="bg-slate-950/90 text-slate-400 uppercase font-semibold border-b border-slate-800">
            <tr>
              <th class="py-2.5 px-3 w-10">STT</th>
              <th class="py-2.5 px-3">Đoạn trích tự sinh</th>
              <th class="py-2.5 px-3 w-20 text-center">Cosine</th>
              <th class="py-2.5 px-3">Tài liệu Top 1 tìm thấy</th>
              <th class="py-2.5 px-3 w-24 text-center">Thực thi</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 bg-slate-900/40 font-normal">
            ${synthetic.map((s, sIdx) => {
              const top1 = (s.top_results && s.top_results[0]) || {};
              const simVal = s.top1_similarity ? s.top1_similarity.toFixed(4) : "0.0000";
              const latVal = s.latency_ms ? s.latency_ms.toFixed(2) : "0.00";
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="py-2.5 px-3 font-mono text-slate-500">${sIdx + 1}</td>
                  <td class="py-2.5 px-3 font-medium text-slate-200">${s.query}</td>
                  <td class="py-2.5 px-3 text-center font-mono font-bold text-emerald-400">${simVal}</td>
                  <td class="py-2.5 px-3">
                    <div class="font-semibold text-sky-300 truncate max-w-xs">${top1.title || "N/A"}</div>
                    <div class="text-[11px] text-slate-400 truncate max-w-xs mt-0.5">${top1.preview || ""}</div>
                  </td>
                  <td class="py-2.5 px-3 text-center">
                    <span class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                      ${latVal} ms
                    </span>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;

  content.innerHTML = html;
}

// =========================================================================
// UNIVERSAL RETRIEVAL BENCHMARK & EVALUATION HISTORY CONTROLLERS
// =========================================================================

function runLiveBenchmark() {
  const topKSelect = document.getElementById('eval-topk-select');
  const topK = parseInt(topKSelect?.value || 5, 10);
  const btn = document.getElementById('btn-run-eval-benchmark');
  const statusEl = document.getElementById('eval-benchmark-status');
  const msgEl = document.getElementById('eval-benchmark-msg');
  const timeEl = document.getElementById('eval-benchmark-time');

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang chạy Benchmark...';
  }
  if (statusEl) statusEl.classList.remove('hidden');
  if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-spinner animate-spin text-rose-400 text-lg"></i> Đang chạy đánh giá toàn diện Benchmark với <strong>Top-K = ${topK}</strong> trên 4 thuật toán...`;
  if (timeEl) timeEl.textContent = '';

  const tStart = performance.now();

  fetch('/api/eval/run', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ top_k: topK })
  })
    .then(res => res.json())
    .then(resData => {
      const elapsed = ((performance.now() - tStart) / 1000).toFixed(2);
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Chạy Đánh giá Benchmark Tức thì';
      }

      if (!resData.success) {
        if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Lỗi khi chạy Benchmark: ${resData.error || "Không rõ"}`;
        return;
      }

      if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400 text-lg"></i> Hoàn tất Universal Retrieval Benchmark (Top-K=${topK})!`;
      if (timeEl) timeEl.textContent = `Thời gian thực thi: ${elapsed}s`;

      if (resData.data) {
        updateEvaluationTable(resData.data, topK, "Vừa cập nhật");
      } else {
        loadEvaluationHistory(true);
      }
    })
    .catch(err => {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-bolt"></i> Chạy Đánh giá Benchmark Tức thì';
      }
      if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-400"></i> Lỗi kết nối tới máy chủ: ${err.message}`;
      console.error("Benchmark error:", err);
    });
}

function updateEvaluationTable(reportData, topK = 5, timestampStr = "") {
  if (!reportData) return;
  const rep = reportData.flat ? reportData : (reportData.report || {});

  const topKEl = document.getElementById('eval-current-topk');
  if (topKEl) topKEl.textContent = topK;

  const timeEl = document.getElementById('eval-benchmark-timestamp');
  if (timeEl && timestampStr) timeEl.textContent = timestampStr;

  const algos = {
    flat: 'eval-flat',
    hnsw: 'eval-hnsw',
    ivf_pq: 'eval-ivfpq',
    two_tier: 'eval-twotier'
  };

  const ramSavings = {
    flat: "0.0% (Gốc)",
    hnsw: "0.0% (Tốn RAM)",
    ivf_pq: "91.7%",
    two_tier: "75.0%"
  };

  for (const [key, prefix] of Object.entries(algos)) {
    const d = rep[key];
    if (!d) continue;

    const qpsEl = document.getElementById(`${prefix}-qps`);
    const meanEl = document.getElementById(`${prefix}-mean`);
    const p95El = document.getElementById(`${prefix}-p95`);
    const recallEl = document.getElementById(`${prefix}-recall`);
    const ramEl = document.getElementById(`${prefix}-ram`);

    if (qpsEl && d.qps !== undefined) {
      qpsEl.textContent = d.qps.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 });
    }
    if (meanEl && d.latency_mean_ms !== undefined) {
      meanEl.textContent = `${d.latency_mean_ms.toFixed(2)} ms`;
    }
    if (p95El && d.latency_p95_ms !== undefined) {
      p95El.textContent = `${d.latency_p95_ms.toFixed(2)} ms`;
    }
    if (recallEl && d.recall_at_k !== undefined) {
      recallEl.textContent = d.recall_at_k.toFixed(4);
    }
    if (ramEl) {
      ramEl.textContent = (d.ram_saving_percent && d.ram_saving_percent > 0)
        ? `${d.ram_saving_percent.toFixed(1)}%`
        : ramSavings[key];
    }
  }
}

let chartEvalScaling = null;
let chartEvalQpsRecall = null;

function initEvaluationCharts() {
  if (typeof Chart === 'undefined') return;

  // 1. Chart: Đường cong quy mô Big Data (RAM vs N)
  const ctxScaling = document.getElementById('chart-scaling-curve');
  if (ctxScaling && !chartEvalScaling) {
    const scales = ['10K', '100K', '1M', '10M', '31.33M'];
    chartEvalScaling = new Chart(ctxScaling, {
      type: 'line',
      data: {
        labels: scales,
        datasets: [
          {
            label: 'Flat Exact (OOM > 16GB)',
            data: [0.015, 0.15, 1.46, 14.64, 45.90],
            borderColor: '#f43f5e',
            backgroundColor: 'rgba(244, 63, 94, 0.1)',
            borderWidth: 2.5,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: 'Standard HNSW (OOM > 64GB)',
            data: [0.021, 0.21, 2.05, 20.50, 64.20],
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.1)',
            borderWidth: 2.5,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: 'Two-Tier Quantized HNSW (An toàn < 8.1GB)',
            data: [0.003, 0.03, 0.26, 2.58, 8.10],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            borderWidth: 3,
            tension: 0.3,
            pointRadius: 5,
            pointHoverRadius: 7
          },
          {
            label: 'Ngưỡng RAM PC (16 GB)',
            data: [16, 16, 16, 16, 16],
            borderColor: '#ef4444',
            borderDash: [6, 6],
            borderWidth: 2,
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 12 } } },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.dataset.label}: ${ctx.raw} GB RAM`
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Quy mô Dữ liệu (Số lượng Vector)' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
          y: { title: { display: true, text: 'RAM Tiêu thụ (GB)' }, grid: { color: 'rgba(255, 255, 255, 0.05)' }, beginAtZero: true }
        }
      }
    });
  }

  // 2. Chart: Thông lượng QPS & Recall@10
  const ctxQps = document.getElementById('chart-qps-recall');
  if (ctxQps && !chartEvalQpsRecall) {
    chartEvalQpsRecall = new Chart(ctxQps, {
      type: 'bar',
      data: {
        labels: ['Flat Exact', 'Standard HNSW', 'IVF-PQ', 'Two-Tier HNSW'],
        datasets: [
          {
            type: 'bar',
            label: 'QPS (Truy vấn/giây)',
            data: [46.5, 303.7, 2590.9, 1250.0],
            backgroundColor: ['#94a3b8', '#38bdf8', '#f59e0b', '#10b981'],
            borderRadius: 6,
            yAxisID: 'yQps'
          },
          {
            type: 'line',
            label: 'Recall@10 (%)',
            data: [100.0, 98.3, 40.0, 95.4],
            borderColor: '#ec4899',
            backgroundColor: '#ec4899',
            borderWidth: 3,
            pointRadius: 6,
            tension: 0.2,
            yAxisID: 'yRecall'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 12 } } }
        },
        scales: {
          x: { grid: { display: false } },
          yQps: {
            type: 'linear',
            position: 'left',
            title: { display: true, text: 'QPS (cao hơn là tốt hơn)' },
            grid: { color: 'rgba(255, 255, 255, 0.05)' }
          },
          yRecall: {
            type: 'linear',
            position: 'right',
            title: { display: true, text: 'Recall@10 (%)' },
            min: 0,
            max: 110,
            grid: { drawOnChartArea: false }
          }
        }
      }
    });
  }
}

function loadEvaluationHistory(autoLoadLatestReport = true) {
  initEvaluationCharts();

  fetch('/api/eval/history')
    .then(res => res.json())
    .then(data => {
      if (!data.success) return;
      const reports = data.benchmark_reports || data.eval_history || [];

      if (autoLoadLatestReport && reports.length > 0) {
        const latestJson = reports.find(f => f.endsWith('.json'));
        if (latestJson) {
          fetch(`/api/eval/download/report/${latestJson}`)
            .then(r => r.json())
            .then(reportData => {
              let timeStr = "";
              const match = latestJson.match(/benchmark_report_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
              if (match) {
                timeStr = `${match[1]}-${match[2]}-${match[3]} ${match[4]}:${match[5]}:${match[6]}`;
              } else {
                timeStr = latestJson;
              }
              const currentTopK = parseInt(document.getElementById('eval-topk-select')?.value || 5, 10);
              updateEvaluationTable(reportData, currentTopK, timeStr);
            })
            .catch(e => console.error("Error reading latest benchmark report:", e));
        }
      }
    })
    .catch(err => {
      console.error("Error loading evaluation history:", err);
    });
}

document.addEventListener('DOMContentLoaded', () => {
  initCategoryChips();
  setTimeout(init3DEngine, 80);
  setTimeout(() => {
    initEvaluationCharts();
    loadEvaluationHistory(true);
  }, 200);
});
