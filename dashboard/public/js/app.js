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

  data.results.forEach(item => {
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

function set3DMode(mode) {
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
    window.threeEngine.setMode(mode);
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
  const latencyEl = document.getElementById('result-latency-3d');
  const listEl = document.getElementById('search-results-list-3d');

  if (section) section.classList.remove('hidden');
  if (countEl) countEl.textContent = data.results_count;
  if (queryEl) queryEl.textContent = data.uploaded_file ? `Tệp: ${data.uploaded_file}` : data.query;
  if (algoEl) algoEl.textContent = data.algorithm;
  if (latencyEl) latencyEl.textContent = data.latency_ms;

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
              <p class="text-slate-300 line-clamp-2 text-[15px] leading-relaxed">${item.preview}...</p>
            </div>
          </div>

          <div class="flex items-center space-x-5 shrink-0 self-end md:self-auto border-t md:border-t-0 border-slate-800 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end">
            <div class="text-right">
              <div class="text-[12px] uppercase tracking-wider text-slate-400 font-semibold">Tọa độ 3D</div>
              <div class="text-[15px] font-mono text-sky-400 font-bold">[${c3d.x.toFixed(1)}, ${c3d.y.toFixed(1)}, ${c3d.z.toFixed(1)}]</div>
            </div>
            <div class="text-right">
              <div class="text-[12px] uppercase tracking-wider text-slate-400 font-semibold">Độ tương đồng</div>
              <div class="text-[17px] font-mono font-bold text-emerald-400">${scorePct}%</div>
            </div>
            <button
              type="button"
              onclick="focusOn3DResultByIndex(${index})"
              class="px-3.5 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-[14px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer"
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

function focusOn3DResultByIndex(index) {
  if (!window.current3DSearchResults || !window.current3DSearchResults[index]) return;
  const item = window.current3DSearchResults[index];
  const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
  focusOn3DResult(c3d.x, c3d.y, c3d.z, item.title, item.category, item.preview);
}

function focusOn3DResult(x, y, z, title, category, preview) {
  if (!window.threeEngine) return;
  set3DMode('universe');
  window.threeEngine.animateCameraTo(
    { x: x + 12, y: y + 10, z: z + 18 },
    { x: x, y: y, z: z },
    0.8
  );

  const infoPanel = document.getElementById('hud-detail-panel');
  if (infoPanel) {
    infoPanel.classList.remove('hidden');
    document.getElementById('hud-doc-title').textContent = title;
    document.getElementById('hud-doc-preview').textContent = preview;
    document.getElementById('hud-doc-coords').textContent = `X: ${x.toFixed(2)} | Y: ${y.toFixed(2)} | Z: ${z.toFixed(2)}`;
    document.getElementById('hud-doc-tokens').textContent = "Top-K Search Match";
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initCategoryChips();
});
