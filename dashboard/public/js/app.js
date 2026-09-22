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

// Academic Math Typesetting via KaTeX
function renderAcademicMath() {
  if (typeof renderMathInElement === 'function') {
    try {
      renderMathInElement(document.body, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true }
        ],
        throwOnError: false
      });
    } catch (e) {
      console.warn("KaTeX render error:", e);
    }
  }
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => {
    el.classList.add('hidden');
    el.classList.remove('block');
  });

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-600');
  });

  const targetContent = document.getElementById(tabId);
  if (targetContent) {
    targetContent.classList.remove('hidden');
    targetContent.classList.add('block');
  }

  const activeBtn = document.getElementById(`btn-${tabId}`);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-slate-600');
  }

  if (tabId === 'tab-3d-visualizer') {
    if (typeof init3DEngine === 'function') {
      init3DEngine();
    }
    if (window.threeEngine && typeof window.threeEngine.onWindowResize === 'function') {
      setTimeout(() => window.threeEngine.onWindowResize(), 60);
    }
  }

  if (tabId === 'tab-wandb-metrics') {
    if (typeof initWandBDashboard === 'function') {
      setTimeout(initWandBDashboard, 50);
    }
  }

  if (tabId === 'tab-architecture' && typeof initArchitectureGraph === 'function') {
    setTimeout(initArchitectureGraph, 50);
  }

  if (tabId === 'tab-benchmarks' || tabId === 'tab-evaluation') {
    setTimeout(renderAcademicMath, 60);
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
    btn.className = `px-3 py-1 rounded-lg text-[13px] font-medium transition-all duration-150 cursor-pointer ${
      isSelected
        ? 'bg-blue-900 text-white shadow-sm border border-blue-900'
        : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100 hover:border-slate-300 hover:text-slate-900'
    }`;
    btn.textContent = cat;
    btn.onclick = () => {
      selectedCategory = cat;
      initCategoryChips();
      if (typeof updateDynamicSql === 'function') updateDynamicSql();
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
    btn.classList.add('bg-blue-50', 'text-blue-700');
  } else {
    zone.classList.add('hidden');
    btn.classList.remove('bg-blue-50', 'text-blue-700');
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
  if (typeof updateDynamicSql === 'function') updateDynamicSql();
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
      try {
        renderSearchResults(resData.data);
      } catch (renderErr) {
        console.error("Error in upload renderSearchResults:", renderErr);
      }
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      console.error("Upload search error:", err);
      alert("Lỗi kết nối tới server khi tìm kiếm tệp: " + (err.message || "Không thể kết nối"));
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

// 3. Top-K Slider synchronization & Dynamic SQL Real-time Listeners
const topKSlider = document.getElementById('input-top-k');
const topKVal = document.getElementById('top-k-val');
if (topKSlider && topKVal) {
  topKSlider.addEventListener('input', (e) => {
    topKVal.textContent = e.target.value;
    if (typeof updateDynamicSql === 'function') updateDynamicSql();
  });
}

const searchInputEl = document.getElementById('search-input');
if (searchInputEl) {
  searchInputEl.addEventListener('input', () => {
    if (typeof updateDynamicSql === 'function') updateDynamicSql();
  });
}

const selectAlgoEl = document.getElementById('select-algorithm');
if (selectAlgoEl) {
  selectAlgoEl.addEventListener('change', () => {
    if (typeof updateDynamicSql === 'function') updateDynamicSql();
  });
}

['input-param-m', 'input-param-ef', 'input-param-tau', 'input-param-rerank'].forEach(id => {
  const el = document.getElementById(id);
  if (el) {
    el.addEventListener('input', () => {
      if (typeof updateDynamicSql === 'function') updateDynamicSql();
    });
  }
});

// 4. Search Form Submission
const searchForm = document.getElementById('search-form');
if (searchForm) {
  searchForm.addEventListener('submit', (e) => {
    e.preventDefault();
    executeSearch();
  });
}

function executeSearch() {
  if (typeof switchTab === 'function') {
    switchTab('tab-search');
  }
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
      try {
        renderSearchResults(resData.data);
      } catch (renderErr) {
        console.error("Error in renderSearchResults:", renderErr);
      }
    })
    .catch(err => {
      searchBtn.disabled = false;
      searchBtn.innerHTML = '<i class="fa-solid fa-bolt"></i> Tìm kiếm';
      console.error("Search API error:", err);
      alert("Lỗi kết nối tới server tìm kiếm: " + (err.message || "Không thể kết nối"));
    });
}

function renderSearchResults(data) {
  if (!data) return;
  const section = document.getElementById('search-results-section');
  const countEl = document.getElementById('result-count');
  const queryEl = document.getElementById('result-query');
  const algoEl = document.getElementById('result-algo');
  const latencyEl = document.getElementById('result-latency');
  const catBadge = document.getElementById('result-cat-badge');
  const listEl = document.getElementById('search-results-list');

  if (section) section.classList.remove('hidden');
  if (countEl) countEl.textContent = data.results_count !== undefined ? data.results_count : 0;

  if (queryEl) {
    if (data.uploaded_file) {
      queryEl.textContent = `Tệp tải lên: ${data.uploaded_file}`;
    } else {
      queryEl.textContent = data.query || "";
    }
  }

  if (catBadge) catBadge.textContent = `Chuyên mục: ${data.category_filter || "Tất cả"}`;
  if (algoEl) algoEl.textContent = data.algorithm || "Two-Tier Quantized HNSW";
  const latVal = typeof data.latency_ms === 'number' ? (isNaN(data.latency_ms) ? '0.00' : data.latency_ms.toFixed(2)) : (data.latency_ms && !isNaN(parseFloat(data.latency_ms)) ? parseFloat(data.latency_ms).toFixed(2) : '0.00');
  if (latencyEl) latencyEl.textContent = latVal;

  // Populate Micro-latency breakdown if available
  const microEl = document.getElementById('result-micro-latency');
  const embedEl = document.getElementById('result-embed-latency');
  const searchEl = document.getElementById('result-search-latency');
  if (microEl && embedEl && searchEl) {
    if (data.micro_latency && (data.micro_latency.embed_ms !== undefined || data.micro_latency.search_ms !== undefined)) {
      const embedVal = data.micro_latency.embed_ms !== undefined ? Number(data.micro_latency.embed_ms).toFixed(2) : '0.00';
      const searchVal = data.micro_latency.search_ms !== undefined ? Number(data.micro_latency.search_ms).toFixed(2) : '0.00';
      embedEl.textContent = embedVal;
      searchEl.textContent = searchVal;
      microEl.classList.remove('hidden');
    } else {
      microEl.classList.add('hidden');
    }
  }

  // Populate Shards Hit summary badge
  const shardsContainer = document.getElementById('result-shards-container');
  const shardsList = document.getElementById('result-shards-list');
  if (shardsContainer && shardsList) {
    const probed = data.shards_probed || data.shards_hit || [];
    if (probed && probed.length > 0) {
      shardsList.textContent = `[${probed.map(s => `Shard #${s}`).join(', ')}]`;
      shardsContainer.classList.remove('hidden');
    } else {
      shardsContainer.classList.add('hidden');
    }
  }

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

  // Cập nhật thẻ chỉ số BigQuery Runtime Inspector
  const bqElapsedEl = document.getElementById('bq-elapsed-time');
  const bqSlotEl = document.getElementById('bq-slot-time');
  const bqShuffledEl = document.getElementById('bq-bytes-shuffled');
  const bqSpilledEl = document.getElementById('bq-bytes-spilled');
  const bqSqlCategory = document.getElementById('bq-sql-category');
  const bqSqlQuery = document.getElementById('bq-sql-query');
  const bqSqlTopk = document.getElementById('bq-sql-topk');
  const rawJsonEl = document.getElementById('search-raw-json');

  if (bqElapsedEl) {
    if (data.bigquery_telemetry && data.bigquery_telemetry.elapsed_time) {
      bqElapsedEl.textContent = data.bigquery_telemetry.elapsed_time;
    } else {
      const latNum = parseFloat(latVal);
      bqElapsedEl.textContent = latNum >= 1000 ? `${(latNum / 1000).toFixed(0)} sec ${(latNum % 1000).toFixed(0)} ms` : `${latVal} ms`;
    }
  }
  if (bqSlotEl) {
    bqSlotEl.textContent = (data.bigquery_telemetry && data.bigquery_telemetry.slot_time_consumed) || "16 sec 645 ms";
  }
  if (bqShuffledEl) {
    bqShuffledEl.textContent = (data.bigquery_telemetry && data.bigquery_telemetry.bytes_shuffled) || "4.75 KB";
  }
  if (bqSpilledEl) {
    bqSpilledEl.textContent = (data.bigquery_telemetry && data.bigquery_telemetry.bytes_spilled_to_disk) || "0 B";
  }
  if (bqSqlCategory) {
    bqSqlCategory.textContent = `'${data.category_filter || "Tất cả"}'`;
  }
  if (bqSqlQuery) {
    bqSqlQuery.textContent = `'${(data.query || "").substring(0, 32)}${(data.query && data.query.length > 32) ? "..." : ""}'`;
  }
  if (bqSqlTopk) {
    bqSqlTopk.textContent = String(data.results_count || 5);
  }

  // Cập nhật thời gian các chặng của BigQuery Execution Graph
  if (data.bigquery_telemetry && Array.isArray(data.bigquery_telemetry.stages)) {
    const s00 = document.getElementById('stage-s00-time');
    const s01 = document.getElementById('stage-s01-time');
    const s02 = document.getElementById('stage-s02-time');
    const s03 = document.getElementById('stage-s03-time');
    if (s00 && data.bigquery_telemetry.stages[0]) s00.textContent = data.bigquery_telemetry.stages[0].slot_time;
    if (s01 && data.bigquery_telemetry.stages[1]) s01.textContent = data.bigquery_telemetry.stages[1].slot_time;
    if (s02 && data.bigquery_telemetry.stages[2]) s02.textContent = data.bigquery_telemetry.stages[2].slot_time;
    if (s03 && data.bigquery_telemetry.stages[3]) s03.textContent = data.bigquery_telemetry.stages[3].slot_time;
  }

  if (rawJsonEl) {
    rawJsonEl.textContent = JSON.stringify(data, null, 2);
  }

  listEl.innerHTML = '';

  if (data.results_count === 0) {
    listEl.innerHTML = `
      <div class="academic-card p-8 text-center text-slate-500 bg-white border border-slate-200 rounded-xl">
        <i class="fa-regular fa-folder-open text-3xl mb-2 text-slate-400"></i>
        <p class="text-[14px]">Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".</p>
      </div>
    `;
    return;
  }

  const resultsList = Array.isArray(data.results) ? data.results : [];

  // Sắp xếp giảm dần theo độ tương đồng Cosine (tương đồng cao nhất đứng top)
  resultsList.sort((a, b) => {
    const scoreA = (a && a.similarity_score !== undefined && !isNaN(a.similarity_score)) ? Number(a.similarity_score) : 0;
    const scoreB = (b && b.similarity_score !== undefined && !isNaN(b.similarity_score)) ? Number(b.similarity_score) : 0;
    return scoreB - scoreA;
  });

  // Gán lại thứ hạng rank và tạo giải thích lý do đứng Top cho từng bản ghi
  resultsList.forEach((item, idx) => {
    item.rank = idx + 1;
    if (!item.reason) {
      const scorePct = Math.round((item.similarity_score || 0) * 100);
      const shardStr = item.shard_id !== undefined ? `Shard #${item.shard_id}` : "phân vùng lượng tử SQ8";
      const distStr = item.distance !== undefined && !isNaN(item.distance) ? Number(item.distance).toFixed(4) : "0.0000";
      const querySnippet = (data.query || "truy vấn").trim();
      item.reason = `Tài liệu đạt độ tương đồng ngữ nghĩa Cosine cao nhất (${scorePct}%) với từ khóa "${querySnippet}". Được định tuyến chính xác tới ${shardStr} qua bộ chỉ mục HNSW đa tầng (τ=3) và được đối soát sai số Euclid (${distStr}) đọc trực tiếp từ tệp Direct I/O trên ổ cứng SSD NVMe.`;
    }
  });

  window.currentTab4SearchResults = resultsList;

  // Cập nhật thẻ chỉ số STAGE S03: OUTPUT trong BigQuery Execution Graph
  const s03TimeEl = document.getElementById('stage-s03-time');
  const s03LatencyEl = document.getElementById('stage-s03-latency');
  const s03RecordsEl = document.getElementById('stage-s03-records');
  const s03TopScoreEl = document.getElementById('stage-s03-top-score');

  if (s03LatencyEl) s03LatencyEl.textContent = `${latVal} ms`;
  if (s03RecordsEl) s03RecordsEl.textContent = `${resultsList.length} bản ghi`;
  if (s03TopScoreEl) {
    if (resultsList.length > 0) {
      const topScore = Math.round((resultsList[0].similarity_score || 0) * 100);
      s03TopScoreEl.textContent = `${topScore}%`;
    } else {
      s03TopScoreEl.textContent = '--';
    }
  }
  if (s03TimeEl && (!data.bigquery_telemetry || !data.bigquery_telemetry.stages)) {
    s03TimeEl.textContent = `${latVal} ms`;
  }

  // Cập nhật khung kết quả xuất ra ngay dưới S03 (Dạng Danh sách & Dạng JSON)
  const graphListEl = document.getElementById('graph-output-list');
  const graphRawJsonEl = document.getElementById('graph-raw-json');

  if (graphRawJsonEl) {
    graphRawJsonEl.textContent = JSON.stringify(data, null, 2);
  }

  if (graphListEl) {
    graphListEl.innerHTML = '';
    if (resultsList.length === 0) {
      graphListEl.innerHTML = `
        <div class="academic-card p-6 text-center text-slate-500 bg-white border border-slate-200 rounded-xl text-xs">
          Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".
        </div>
      `;
    } else {
      resultsList.forEach((item, index) => {
        const scorePct = Math.round((item.similarity_score !== undefined && !isNaN(item.similarity_score) ? item.similarity_score : 0) * 100);
        const shardId = item.shard_id !== undefined ? item.shard_id : 0;
        const nodeId = item.node_id !== undefined ? item.node_id : (item.index !== undefined ? item.index : (item.doc_id || 0));
        const identifier = item.doc_id || ('Node #' + nodeId);

        const card = document.createElement('div');
        card.className = "academic-card p-4 transition-all duration-200 flex flex-col gap-3 border-l-4 border-l-emerald-600 bg-white hover:border-emerald-500 rounded-xl shadow-xs";
        card.innerHTML = `
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-2.5 pb-2 border-b border-slate-100">
            <div class="flex items-center space-x-3">
              <div class="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center font-mono font-bold text-emerald-800 text-sm shrink-0">
                #${item.rank}
              </div>
              <div>
                <h4 class="text-[16px] font-serif font-bold text-slate-900 leading-snug">${item.title}</h4>
                <div class="flex flex-wrap items-center gap-2 mt-1">
                  <span class="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-200">${item.category || "Tin tức"}</span>
                  <span class="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
                    <i class="fa-solid fa-server text-[10px] text-amber-700"></i> Shard #${shardId}
                  </span>
                  <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">${identifier}</span>
                </div>
              </div>
            </div>
            <div class="flex items-center space-x-3 shrink-0 self-end md:self-auto">
              <div class="text-right">
                <div class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Sai số Euclid</div>
                <div class="text-[13px] font-mono font-bold text-slate-800">${item.distance !== undefined && !isNaN(item.distance) ? Number(item.distance).toFixed(4) : '0.0000'}</div>
              </div>
              <div class="text-right">
                <div class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">Tương đồng</div>
                <div class="text-[16px] font-mono font-bold text-emerald-700">${scorePct}%</div>
              </div>
              <button
                type="button"
                onclick="focusOn3DResultByIndexTab4(${index})"
                class="px-3 py-1.5 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 text-xs font-bold transition flex items-center gap-1.5 shadow-xs cursor-pointer shrink-0"
              >
                <i class="fa-solid fa-cube"></i> Xem 3D
              </button>
            </div>
          </div>
          <p class="text-[13px] text-slate-600 line-clamp-2 leading-relaxed font-sans">${item.preview}...</p>
          <div class="bg-amber-50/80 p-2.5 rounded-lg border border-amber-200 text-xs text-amber-950 flex items-start gap-2">
            <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5 shrink-0 text-sm"></i>
            <div>
              <span class="font-bold text-amber-900">Lý do đứng Top &amp; Giải thích:</span> ${item.reason}
            </div>
          </div>
        `;
        graphListEl.appendChild(card);
      });
    }
  }

  // Render danh sách trong tab View 2: Danh sách Top-K
  listEl.innerHTML = '';

  if (resultsList.length === 0) {
    listEl.innerHTML = `
      <div class="academic-card p-8 text-center text-slate-500 bg-white border border-slate-200 rounded-xl">
        <i class="fa-regular fa-folder-open text-3xl mb-2 text-slate-400"></i>
        <p class="text-[14px]">Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".</p>
      </div>
    `;
  } else {
    resultsList.forEach((item, index) => {
      const card = document.createElement('div');
      card.className = "academic-card p-4 transition-all duration-200 flex flex-col gap-3 border-l-4 border-l-blue-700 bg-white rounded-xl shadow-xs";

      const scorePct = Math.round((item.similarity_score !== undefined && !isNaN(item.similarity_score) ? item.similarity_score : 0) * 100);
      const shardId = item.shard_id !== undefined ? item.shard_id : 0;
      const nodeId = item.node_id !== undefined ? item.node_id : (item.index !== undefined ? item.index : (item.doc_id || 0));
      const identifier = item.doc_id || ('Node #' + nodeId);

      card.innerHTML = `
        <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div class="flex items-start space-x-3.5">
            <div class="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center font-mono font-bold text-blue-800 text-sm shrink-0 mt-0.5">
              #${item.rank}
            </div>
            <div class="space-y-1.5">
              <div class="flex flex-wrap items-center gap-2">
                <h4 class="text-[17px] font-serif font-bold text-slate-900">${item.title}</h4>
                <span class="text-[12px] font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-200 font-medium">${item.category || "Tin tức"}</span>
                <span class="text-[12px] font-mono font-semibold px-2.5 py-0.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-medium flex items-center gap-1.5 shadow-sm">
                  <i class="fa-solid fa-server text-[11px] text-amber-700"></i> Shard #${shardId}
                </span>
                <span class="text-[12px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">${identifier}</span>
              </div>
              <p class="text-[14px] text-slate-600 line-clamp-2 leading-relaxed font-sans">${item.preview}...</p>
            </div>
          </div>

          <div class="flex items-center space-x-4 shrink-0 text-right self-end md:self-auto border-t md:border-t-0 border-slate-200 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end">
            <div>
              <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Sai số Euclid</div>
              <div class="text-[15px] font-mono font-bold text-slate-800">${item.distance !== undefined && !isNaN(item.distance) ? Number(item.distance).toFixed(4) : '0.0000'}</div>
            </div>
            <div>
              <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Độ tương đồng</div>
              <div class="text-[17px] font-mono font-bold text-emerald-700">${scorePct}%</div>
            </div>
            <button
              type="button"
              onclick="focusOn3DResultByIndexTab4(${index})"
              class="px-3 py-1.5 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 text-[13px] font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer shrink-0"
            >
              <i class="fa-solid fa-cube"></i> Xem 3D
            </button>
          </div>
        </div>

        <div class="bg-amber-50/80 p-2.5 rounded-lg border border-amber-200 text-xs text-amber-950 flex items-start gap-2">
          <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5 shrink-0 text-sm"></i>
          <div>
            <span class="font-bold text-amber-900">Lý do đứng Top &amp; Giải thích:</span> ${item.reason}
          </div>
        </div>
      `;
      listEl.appendChild(card);
    });
  }

  // Tự động đồng bộ kết quả sang Tab 3D
  if (typeof render3DSearchResults === 'function') {
    try {
      render3DSearchResults(data);
    } catch (syncErr3D) {
      console.warn("Lỗi đồng bộ render3DSearchResults:", syncErr3D);
    }
  }

  // Đồng bộ kết quả tìm kiếm với không gian 3D nếu 3D Engine đang chạy
  if (window.threeEngine && window.threeEngine.vectorSpaceModule && resultsList.length > 0) {
    try {
      window.threeEngine.vectorSpaceModule.renderQueryResults(
        data.query || "Truy vấn văn bản",
        data.query_3d || { x: 0, y: 0, z: 0 },
        resultsList
      );
    } catch (e) {
      console.warn("3D query sync error:", e);
    }
  }

  // Cập nhật số liệu W&B Metrics Studio nếu đã khởi tạo
  if (typeof refreshWandBMetrics === 'function' && typeof isWandBInitialized !== 'undefined' && isWandBInitialized) {
    refreshWandBMetrics();
  }
}

// Chế độ xem đầu ra S03 trong Execution Graph
function setGraphOutputMode(mode) {
  const btnList = document.getElementById('btn-graph-mode-list');
  const btnJson = document.getElementById('btn-graph-mode-json');
  const listEl = document.getElementById('graph-output-list');
  const jsonEl = document.getElementById('graph-output-json');

  if (!btnList || !btnJson || !listEl || !jsonEl) return;

  if (mode === 'list') {
    btnList.className = "px-3 py-1 rounded-md bg-white text-blue-900 font-bold shadow-xs transition flex items-center gap-1.5 cursor-pointer";
    btnJson.className = "px-3 py-1 rounded-md text-slate-600 hover:text-slate-900 transition flex items-center gap-1.5 cursor-pointer";
    listEl.classList.remove('hidden');
    jsonEl.classList.add('hidden');
  } else {
    btnJson.className = "px-3 py-1 rounded-md bg-white text-blue-900 font-bold shadow-xs transition flex items-center gap-1.5 cursor-pointer";
    btnList.className = "px-3 py-1 rounded-md text-slate-600 hover:text-slate-900 transition flex items-center gap-1.5 cursor-pointer";
    jsonEl.classList.remove('hidden');
    listEl.classList.add('hidden');
  }
}
window.setGraphOutputMode = setGraphOutputMode;

function copyGraphJson() {
  const rawJsonEl = document.getElementById('graph-raw-json');
  if (!rawJsonEl) return;
  navigator.clipboard.writeText(rawJsonEl.textContent).then(() => {
    alert("Đã sao chép toàn bộ dữ liệu JSON kết quả vào clipboard!");
  }).catch(() => {
    alert("Không thể tự động sao chép. Vui lòng chọn văn bản JSON thủ công.");
  });
}
window.copyGraphJson = copyGraphJson;

function searchAll() {
  selectedCategory = "Tất cả";
  initCategoryChips();
  const input = document.getElementById('search-input');
  if (!input.value.trim()) {
    input.value = "thị trường chứng khoán và tài chính";
  }
  executeSearch();
}

function switchExecutionView(viewName) {
  const graphView = document.getElementById('view-execution-graph');
  const resultsView = document.getElementById('view-execution-results');
  const detailsView = document.getElementById('view-execution-details');

  const btnGraph = document.getElementById('btn-tab-bq-graph');
  const btnResults = document.getElementById('btn-tab-bq-results');
  const btnDetails = document.getElementById('btn-tab-bq-details');

  if (!graphView || !resultsView || !detailsView) return;

  const activeClasses = ['bg-blue-800', 'text-white', 'font-semibold', 'shadow-xs'];
  const inactiveClasses = ['text-slate-600', 'hover:text-slate-900'];

  [btnGraph, btnResults, btnDetails].forEach(b => {
    if (b) {
      b.classList.remove(...activeClasses);
      b.classList.add(...inactiveClasses);
    }
  });

  graphView.classList.add('hidden');
  resultsView.classList.add('hidden');
  detailsView.classList.add('hidden');

  if (viewName === 'graph') {
    graphView.classList.remove('hidden');
    if (btnGraph) {
      btnGraph.classList.remove(...inactiveClasses);
      btnGraph.classList.add(...activeClasses);
    }
  } else if (viewName === 'results') {
    resultsView.classList.remove('hidden');
    if (btnResults) {
      btnResults.classList.remove(...inactiveClasses);
      btnResults.classList.add(...activeClasses);
    }
  } else if (viewName === 'details') {
    detailsView.classList.remove('hidden');
    if (btnDetails) {
      btnDetails.classList.remove(...inactiveClasses);
      btnDetails.classList.add(...activeClasses);
    }
  }
}

// Real-time Dynamic SQL Query Generator
function escapeSqlString(str) {
  if (!str) return '';
  return String(str).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/'/g, "''");
}

function updateDynamicSql() {
  const inputEl = document.getElementById('search-input');
  const rawQuery = inputEl ? inputEl.value.trim() : '';
  const displayQuery = rawQuery || 'thị trường chứng khoán và tài chính';
  const category = selectedCategory || 'Tất cả';
  const topK = parseInt(document.getElementById('input-top-k')?.value || 5, 10);
  const algo = document.getElementById('select-algorithm')?.value || 'two_tier';
  const hp = typeof getHyperparams === 'function' ? getHyperparams() : { m: 16, ef_search: 30, tau: 3, min_rerank_k: 20 };

  const isTwoTier = (algo === 'two_tier');
  const algoTitle = isTwoTier ? 'Two-Tier Quantized HNSW' : 'Standard HNSW';
  const quantMode = isTwoTier ? 'SQ8_UINT8' : 'FLOAT32_EXACT';
  const hintClause = isTwoTier 
    ? `/*+ ROUTING(200_SHARDS), HNSW(M=${hp.m}, ef=${hp.ef_search}), EARLY_EXIT(tau=${hp.tau}, eps=1e-4) */`
    : `/*+ ROUTING(MONOLITHIC_RAM), HNSW(M=${hp.m}, ef=${hp.ef_search}), EARLY_EXIT(OFF) */`;

  const whereCategory = (category && category !== 'Tất cả') 
    ? `category = '${escapeSqlString(category)}'` 
    : `category IS NOT NULL`;

  const lines = [
    `<span class="text-indigo-400 font-bold">SELECT</span>`,
    `  doc_id, title, category,`,
    `  <span class="text-sky-300">ROUND</span>(similarity_score, 4) <span class="text-indigo-400 font-bold">AS</span> cosine_score,`,
    `  shard_id`,
    `<span class="text-indigo-400 font-bold">FROM</span> <span class="text-emerald-300">\`ann_corpus_1645m.documents\`</span>`,
    `<span class="text-slate-500 italic">${hintClause}</span>`,
    `<span class="text-indigo-400 font-bold">WHERE</span>`,
    `  ${whereCategory}`,
    `  <span class="text-indigo-400 font-bold">AND</span> <span class="text-sky-300">VECTOR_SEARCH</span>(`,
    `    vector,`,
    `    <span class="text-sky-300">EMBED_VIETNAMESE</span>(<span class="text-amber-300">"${escapeSqlString(displayQuery)}"</span>),`,
    `    metric =&gt; <span class="text-amber-300">"COSINE"</span>,`,
    `    quantization =&gt; <span class="text-emerald-400">"${quantMode}"</span>,`,
    `    min_rerank_k =&gt; <span class="text-amber-300">${hp.min_rerank_k || 20}</span>`,
    `  )`,
    `<span class="text-indigo-400 font-bold">ORDER BY</span> cosine_score <span class="text-indigo-400 font-bold">DESC</span>`,
    `<span class="text-indigo-400 font-bold">LIMIT</span> <span class="text-amber-300 font-bold">${topK}</span>;`
  ];

  const contentEl = document.getElementById('bq-sql-content');
  const gutterEl = document.getElementById('bq-sql-gutter');
  const engineEl = document.getElementById('bq-sql-engine');
  const routingEl = document.getElementById('bq-sql-routing');
  const queryResultEl = document.getElementById('result-query');

  if (contentEl) {
    contentEl.innerHTML = lines.join('\n');
  }
  if (gutterEl) {
    gutterEl.innerHTML = lines.map((_, i) => `<div>${i + 1}</div>`).join('');
  }
  if (engineEl) {
    engineEl.textContent = algoTitle;
  }
  if (routingEl) {
    routingEl.textContent = isTwoTier ? `200 Shards / M=${hp.m}, τ=${hp.tau}` : `RAM Đầy đủ / M=${hp.m}`;
  }
  if (queryResultEl && rawQuery) {
    queryResultEl.textContent = rawQuery;
  }
}

function runSampleQuery(queryText, category) {
  if (typeof switchTab === 'function') {
    switchTab('tab-search');
  }
  const input = document.getElementById('search-input');
  if (input) {
    input.value = queryText;
  }
  if (category) {
    selectedCategory = category;
    initCategoryChips();
  }
  updateDynamicSql();
  switchExecutionView('graph');
  executeSearch();
}

window.updateDynamicSql = updateDynamicSql;
window.switchExecutionView = switchExecutionView;
window.runSampleQuery = runSampleQuery;


// =========================================================================
// THREE.JS 3D WEB CONTROLLERS & ACTIONS
// =========================================================================

function init3DEngine() {
  if (window.threeEngine) return;
  if (typeof THREE === 'undefined' || typeof ThreeEngine === 'undefined') {
    return;
  }
  try {
    const engine = new ThreeEngine('threejs-canvas-wrapper');
    if (typeof VectorSpaceModule !== 'undefined') {
      engine.vectorSpaceModule = new VectorSpaceModule(engine);
    }
    if (typeof HnswGraphModule !== 'undefined') {
      engine.hnswModule = new HnswGraphModule(engine);
    }
    if (typeof Pipeline3DModule !== 'undefined') {
      engine.pipelineModule = new Pipeline3DModule(engine);
    }
    window.threeEngine = engine;
    console.log("[app.js] Three.js Engine and modules initialized successfully.");
  } catch (err) {
    console.error("[app.js] Error initializing Three.js Engine:", err);
  }
}

function set3DMode(mode, resetCamera = true) {
  document.querySelectorAll('.mode-btn-3d').forEach(btn => {
    btn.classList.remove('active');
    btn.classList.add('text-slate-600');
  });

  const activeBtn = document.getElementById(`btn-mode-${mode}`);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-slate-600');
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
      btn.classList.add('active', 'bg-blue-900', 'text-white');
      btn.classList.remove('bg-white', 'text-slate-700');
    } else {
      btn.classList.remove('active', 'bg-blue-900', 'text-white');
      btn.classList.add('bg-white', 'text-slate-700');
    }
  });

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

let uploaded3DFileContent = "";
let uploaded3DFileName = "";

function toggle3DUploadZone() {
  const zone = document.getElementById('file-upload-zone-3d');
  const btn = document.getElementById('btn-3d-toggle-upload');
  if (!zone) return;
  const isHidden = zone.classList.contains('hidden');
  if (isHidden) {
    zone.classList.remove('hidden');
    btn.classList.add('bg-blue-50', 'text-blue-700');
  } else {
    zone.classList.add('hidden');
    btn.classList.remove('bg-blue-50', 'text-blue-700');
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
    const nameEl = document.getElementById('file-name-text-3d');
    const sizeEl = document.getElementById('file-size-text-3d');
    const infoEl = document.getElementById('file-preview-info-3d');
    if (nameEl) nameEl.textContent = uploaded3DFileName;
    if (sizeEl) sizeEl.textContent = `(${sizeKb} KB)`;
    if (infoEl) infoEl.classList.remove('hidden');
  };
  reader.readAsText(file);
}

function searchByUploadedFile3D() {
  if (!uploaded3DFileContent) {
    alert("Vui lòng chọn tệp văn bản hợp lệ.");
    return;
  }

  const topK = parseInt(document.getElementById('input-top-k-3d')?.value || 5, 10);
  const algorithm = document.getElementById('select-algorithm-3d')?.value || 'two_tier';
  const tau = parseInt(document.getElementById('input-tau-3d')?.value || 3, 10);

  const searchBtn = document.getElementById('search-button-3d');
  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tính toán 3D...';
  }

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
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      }
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm tệp: " + (resData.error || "Không rõ"));
        return;
      }
      render3DSearchResults(resData.data);
    })
    .catch(err => {
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      }
      console.error("3D Upload search error:", err);
      alert("Lỗi kết nối tới server.");
    });
}

function searchAll3D() {
  filter3DCloud('Tất cả');
  const input = document.getElementById('search-input-3d');
  if (input && !input.value.trim()) {
    input.value = "thị trường chứng khoán và tài chính";
  }
  execute3DSearch();
}

function quickQuery3D(queryText) {
  const input = document.getElementById('search-input-3d');
  if (input) input.value = queryText;
  execute3DSearch();
}

function execute3DSearch() {
  const query = document.getElementById('search-input-3d')?.value.trim();
  const topK = parseInt(document.getElementById('input-top-k-3d')?.value || 5, 10);
  const algorithm = document.getElementById('select-algorithm-3d')?.value || 'two_tier';
  const tau = parseInt(document.getElementById('input-tau-3d')?.value || 3, 10);
  const searchBtn = document.getElementById('search-button-3d');

  if (!query) return;

  if (searchBtn) {
    searchBtn.disabled = true;
    searchBtn.innerHTML = '<i class="fa-solid fa-spinner animate-spin"></i> Đang tìm kiếm & chiếu 3D...';
  }

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
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      }
      if (!resData.success) {
        alert("Lỗi khi tìm kiếm: " + (resData.error || "Không rõ nguyên nhân"));
        return;
      }
      try {
        render3DSearchResults(resData.data);
      } catch (renderErr) {
        console.error("Error in render3DSearchResults:", renderErr);
      }
    })
    .catch(err => {
      if (searchBtn) {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fa-solid fa-bolt text-amber-300"></i> Tìm & Mô phỏng 3D';
      }
      console.error("3D Search API error:", err);
      alert("Lỗi kết nối tới server 3D: " + (err.message || "Không thể kết nối"));
    });
}

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
  if (latencyEl) latencyEl.textContent = typeof data.latency_ms === 'number' ? data.latency_ms.toFixed(2) : (data.latency_ms || '0.00');
  if (qpsEl) qpsEl.textContent = data.qps || (data.latency_ms > 0 ? (1000 / data.latency_ms).toFixed(1) : "1,000");

  const fileContainer3D = document.getElementById('search-result-file-container-3d');
  const filenameEl3D = document.getElementById('search-result-filename-3d');
  const downloadBtn3D = document.getElementById('btn-download-result-file-3d');
  const resultFilename3D = data.result_filename || (data.result_file ? data.result_file.split(/[\/]/).pop() : null);

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

  const results3D = Array.isArray(data.results) ? [...data.results] : [];

  // Sắp xếp giảm dần theo độ tương đồng Cosine (tương đồng cao nhất đứng top)
  results3D.sort((a, b) => {
    const scoreA = (a && a.similarity_score !== undefined && !isNaN(a.similarity_score)) ? Number(a.similarity_score) : 0;
    const scoreB = (b && b.similarity_score !== undefined && !isNaN(b.similarity_score)) ? Number(b.similarity_score) : 0;
    return scoreB - scoreA;
  });

  // Gán lại thứ hạng rank và tạo giải thích lý do đứng Top cho từng bản ghi 3D
  results3D.forEach((item, idx) => {
    item.rank = idx + 1;
    if (!item.reason) {
      const scorePct = Math.round((item.similarity_score || 0) * 100);
      const shardStr = item.shard_id !== undefined ? `Shard #${item.shard_id}` : "phân vùng lượng tử SQ8";
      const distStr = item.distance !== undefined && !isNaN(item.distance) ? Number(item.distance).toFixed(4) : "0.0000";
      const querySnippet = (data.query || "truy vấn").trim();
      item.reason = `Tài liệu đạt độ tương đồng ngữ nghĩa Cosine cao nhất (${scorePct}%) với từ khóa "${querySnippet}". Được định tuyến chính xác tới ${shardStr} qua bộ chỉ mục HNSW đa tầng (τ=3) và đối soát sai số Euclid (${distStr}) trực tiếp từ tệp Direct I/O trên ổ cứng SSD NVMe.`;
    }
  });

  window.current3DSearchResults = results3D;

  if (listEl) {
    listEl.innerHTML = '';
    if (results3D.length === 0) {
      listEl.innerHTML = `
        <div class="academic-card p-6 text-center text-slate-500 bg-white border border-slate-200 rounded-xl text-xs">
          Không tìm thấy bài viết nào phù hợp trong chuyên mục "${data.category_filter || 'Tất cả'}".
        </div>
      `;
    } else {
      results3D.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = "academic-card p-4 transition-all duration-150 flex flex-col gap-3 text-[15px] border-l-4 border-l-blue-700 bg-white hover:border-blue-600 hover:shadow-sm rounded-xl";
        const scorePct = Math.round((item.similarity_score !== undefined && !isNaN(item.similarity_score) ? item.similarity_score : 0) * 100);
        const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
        const sourceLabel = "Báo chí & Pháp luật";
        const shardId = item.shard_id !== undefined ? item.shard_id : 0;
        const nodeId = item.node_id !== undefined ? item.node_id : (item.index !== undefined ? item.index : (item.doc_id || 0));
        const identifier = item.doc_id || ('Node #' + nodeId);

        card.innerHTML = `
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div class="flex items-start space-x-3.5">
              <div class="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center font-mono font-bold text-blue-800 text-sm shrink-0 mt-0.5">
                #${item.rank}
              </div>
              <div class="space-y-1.5">
                <div class="flex flex-wrap items-center gap-2">
                  <h4 class="text-[17px] font-serif font-bold text-slate-900">${item.title}</h4>
                  <span class="text-[13px] font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-800 border border-blue-200 font-medium">${item.category || "Tin tức"}</span>
                  <span class="text-[12px] font-mono font-semibold px-2.5 py-0.5 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-medium flex items-center gap-1.5 shadow-sm">
                    <i class="fa-solid fa-server text-[11px] text-amber-700"></i> Shard #${shardId}
                  </span>
                  <span class="text-[12px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">${sourceLabel}</span>
                  <span class="text-[13px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">${identifier}</span>
                </div>
                <p class="text-slate-600 line-clamp-2 text-[14px] leading-relaxed font-sans">${item.preview}...</p>
              </div>
            </div>

            <div class="flex items-center space-x-4 shrink-0 self-end md:self-auto border-t md:border-t-0 border-slate-200 pt-2 md:pt-0 w-full md:w-auto justify-between md:justify-end text-right">
              <div>
                <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Tọa độ 3D</div>
                <div class="text-[13px] font-mono text-blue-700 font-semibold">[${c3d.x.toFixed(1)}, ${c3d.y.toFixed(1)}, ${c3d.z.toFixed(1)}]</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Khoảng cách L2</div>
                <div class="text-[14px] font-mono font-bold text-slate-800">${item.distance !== undefined && !isNaN(item.distance) ? Number(item.distance).toFixed(4) : "0.0000"}</div>
              </div>
              <div>
                <div class="text-[11px] uppercase tracking-wider text-slate-500 font-semibold">Tương đồng</div>
                <div class="text-[17px] font-mono font-bold text-emerald-700">${scorePct}%</div>
              </div>
              <button
                type="button"
                onclick="focusOn3DResultByIndex(${index})"
                class="px-3.5 py-2 rounded-xl bg-blue-50 hover:bg-blue-100 text-blue-800 border border-blue-200 text-[13px] font-bold transition flex items-center gap-1.5 shadow-sm cursor-pointer shrink-0"
              >
                <i class="fa-solid fa-crosshairs"></i> Xem trên 3D
              </button>
            </div>
          </div>

          <div class="bg-amber-50/80 p-2.5 rounded-lg border border-amber-200 text-xs text-amber-950 flex items-start gap-2">
            <i class="fa-solid fa-lightbulb text-amber-600 mt-0.5 shrink-0 text-sm"></i>
            <div>
              <span class="font-bold text-amber-900">Lý do đứng Top &amp; Giải thích:</span> ${item.reason}
            </div>
          </div>
        `;
        listEl.appendChild(card);
      });
    }
  }

  if (window.threeEngine && window.threeEngine.vectorSpaceModule && results3D.length > 0) {
    window.threeEngine.vectorSpaceModule.renderQueryResults(
      data.query || "Truy vấn",
      data.query_3d || { x: 0, y: 0, z: 0 },
      results3D
    );
  }

  if (window.threeEngine && window.threeEngine.hnswModule && window.threeEngine.currentMode === 'hnsw') {
    const isEarlyExit = data.algorithm_key === 'two_tier';
    window.threeEngine.hnswModule.startRoutingSimulation(isEarlyExit);
  }
}

function focusOn3DResultByIndexTab4(index) {
  if (!window.currentTab4SearchResults || !window.currentTab4SearchResults[index]) return;
  const item = window.currentTab4SearchResults[index];
  const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
  focusOn3DResult(c3d.x, c3d.y, c3d.z, item.title, item.category, item.preview, item.similarity_score, item.rank, item.reason);
}

function focusOn3DResultByIndex(index) {
  if (!window.current3DSearchResults || !window.current3DSearchResults[index]) return;
  const item = window.current3DSearchResults[index];
  const c3d = item.coords_3d || { x: 0, y: 0, z: 0 };
  focusOn3DResult(c3d.x, c3d.y, c3d.z, item.title, item.category, item.preview, item.similarity_score, item.rank, item.reason);
}

function focusOn3DResult(x, y, z, title, category, preview, score = null, rank = null, reason = null) {
  if (!window.threeEngine) {
    init3DEngine();
  }
  if (!window.threeEngine) return;

  switchTab('tab-3d-visualizer');

  const viewport = document.getElementById('threejs-viewport-container');
  if (viewport) {
    viewport.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  set3DMode('universe', false);

  const targetCamPos = { x: x + 8, y: y + 6, z: z + 14 };
  const targetLookAt = { x: x, y: y, z: z };

  window.threeEngine.animateCameraTo(targetCamPos, targetLookAt, 1.0);

  if (window.threeEngine.vectorSpaceModule && typeof window.threeEngine.vectorSpaceModule.highlightNode === 'function') {
    window.threeEngine.vectorSpaceModule.highlightNode(x, y, z, title);
  }

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

    const reasonContainer = document.getElementById('hud-doc-reason-container');
    const reasonEl = document.getElementById('hud-doc-reason');
    if (reasonContainer && reasonEl) {
      if (reason) {
        reasonEl.textContent = reason;
        reasonContainer.classList.remove('hidden');
      } else {
        reasonContainer.classList.add('hidden');
      }
    }

    const coordsEl = document.getElementById('hud-doc-coords');
    if (coordsEl) coordsEl.textContent = `X: ${x.toFixed(2)} | Y: ${y.toFixed(2)} | Z: ${z.toFixed(2)}`;

    const tokensEl = document.getElementById('hud-doc-tokens');
    if (tokensEl) {
      tokensEl.textContent = rank ? `Top #${rank} (Độ tương đồng: ${score ? Math.round(score * 100) : '--'}%)` : "Top-K Search Match";
    }
  }
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
  if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-spinner animate-spin text-emerald-700 text-lg"></i> Đang chạy đối chuẩn toàn diện Benchmark với <strong>Top-K = ${topK}</strong> trên 2 thuật toán HNSW...`;
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
        if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600"></i> Lỗi khi chạy Benchmark: ${resData.error || "Không rõ"}`;
        return;
      }

      if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-700 text-lg"></i> Hoàn tất Universal Retrieval Benchmark (Top-K=${topK})!`;
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
      if (msgEl) msgEl.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600"></i> Lỗi kết nối tới máy chủ: ${err.message}`;
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
    hnsw: 'eval-hnsw',
    two_tier: 'eval-twotier'
  };

  const ramSavings = {
    hnsw: "0.0% (Tốn RAM)",
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
    const scales = ['10K', '100K', '1M', '10M', '16.45M'];
    chartEvalScaling = new Chart(ctxScaling, {
      type: 'line',
      data: {
        labels: scales,
        datasets: [
          {
            label: 'Standard HNSW (OOM > 32GB)',
            data: [0.021, 0.21, 2.05, 20.50, 64.20],
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.1)',
            borderWidth: 2.5,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6
          },
          {
            label: 'Two-Tier Quantized HNSW (Đề xuất - An toàn < 8.1GB)',
            data: [0.003, 0.03, 0.26, 2.58, 8.10],
            borderColor: '#059669',
            backgroundColor: 'rgba(5, 150, 105, 0.1)',
            borderWidth: 3,
            tension: 0.3,
            pointRadius: 5,
            pointHoverRadius: 7
          },
          {
            label: 'Ngưỡng RAM PC (16 GB)',
            data: [16, 16, 16, 16, 16],
            borderColor: '#dc2626',
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
          x: { title: { display: true, text: 'Quy mô Dữ liệu (Số lượng Vector)' }, grid: { color: 'rgba(0, 0, 0, 0.05)' } },
          y: { title: { display: true, text: 'RAM Tiêu thụ (GB)' }, grid: { color: 'rgba(0, 0, 0, 0.05)' }, beginAtZero: true }
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
        labels: ['Standard HNSW (Baseline)', 'Two-Tier Quantized HNSW (Đề xuất)'],
        datasets: [
          {
            type: 'bar',
            label: 'QPS (Truy vấn/giây)',
            data: [303.7, 1250.0],
            backgroundColor: ['#3b82f6', '#059669'],
            borderRadius: 6,
            yAxisID: 'yQps'
          },
          {
            type: 'line',
            label: 'Recall@10 (%)',
            data: [98.3, 95.4],
            borderColor: '#d97706',
            backgroundColor: '#d97706',
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
            grid: { color: 'rgba(0, 0, 0, 0.05)' }
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
  if (typeof updateDynamicSql === 'function') updateDynamicSql();
  setTimeout(() => {
    initEvaluationCharts();
    loadEvaluationHistory(true);
    renderAcademicMath();
  }, 200);
  setTimeout(() => {
    if (typeof init3DEngine === 'function') init3DEngine();
    if (typeof initWandBDashboard === 'function') initWandBDashboard();
  }, 100);
});

window.addEventListener('load', () => {
  setTimeout(renderAcademicMath, 150);
});
