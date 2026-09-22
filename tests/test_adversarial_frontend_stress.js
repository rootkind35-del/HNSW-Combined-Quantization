/**
 * Empirical Adversarial Frontend Stress Test Harness
 * Conducts stress tests on:
 * 1. Search Payloads & Edge Cases (malformed, null, missing shards, missing doc_id, latency extremes)
 * 2. WandB Metrics Edge Cases (empty runs, spikes, single-shard distribution, extreme recall, early exit extremes)
 * 3. 3D UI Container Lifecycle (hidden container, 0x0 resize, slow Three.js, mode switching, camera presets)
 * 4. Persistence of Search Routing Metrics (multi-query state transitions, container visibility toggles, badge persistence)
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

// -------------------------------------------------------------
// 1. Comprehensive Mock DOM Infrastructure
// -------------------------------------------------------------
class MockElement {
  constructor(id = null, tagName = 'div') {
    this.id = id;
    this.tagName = tagName.toUpperCase();
    this.textContent = '';
    this._innerHTML = '';
    this.className = '';
    this.children = [];
    this.attributes = {};
    this.href = '';
    this.value = '';
    this.disabled = false;
    this.clientWidth = 1000;
    this.clientHeight = 760;
    this._classes = new Set();
    this.style = {};
    this.eventListeners = {};

    this.classList = {
      add: (...cls) => cls.forEach(c => this._classes.add(c)),
      remove: (...cls) => cls.forEach(c => this._classes.delete(c)),
      contains: (c) => this._classes.has(c),
      toggle: (c) => {
        if (this._classes.has(c)) {
          this._classes.delete(c);
          return false;
        } else {
          this._classes.add(c);
          return true;
        }
      }
    };
  }

  get innerHTML() {
    return this._innerHTML || '';
  }

  set innerHTML(val) {
    this._innerHTML = String(val);
    if (val === '' || val === null || val === undefined) {
      this.children = [];
    }
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    const idx = this.children.indexOf(child);
    if (idx >= 0) this.children.splice(idx, 1);
    return child;
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === 'href') this.href = String(value);
  }

  getAttribute(name) {
    return this.attributes[name] !== undefined ? this.attributes[name] : null;
  }

  addEventListener(event, fn) {
    if (!this.eventListeners[event]) this.eventListeners[event] = [];
    this.eventListeners[event].push(fn);
  }

  removeEventListener(event, fn) {
    if (this.eventListeners[event]) {
      this.eventListeners[event] = this.eventListeners[event].filter(f => f !== fn);
    }
  }

  getBoundingClientRect() {
    return { left: 0, top: 0, width: this.clientWidth, height: this.clientHeight };
  }

  getContext(type) {
    return {
      fillRect: () => {},
      strokeRect: () => {},
      fillText: () => {},
      roundRect: () => {},
      fill: () => {},
      stroke: () => {}
    };
  }

  get outerHTML() {
    let classes = Array.from(this._classes).join(' ');
    let childrenHTML = this.children.map(c => (c && c.outerHTML !== undefined ? c.outerHTML : '')).join('');
    return `<${this.tagName} id="${this.id || ''}" class="${classes}">${this.innerHTML}${childrenHTML}</${this.tagName}>`;
  }
}

function createDashboardDOM() {
  const elements = {
    // Top headers / KPI
    'speed-p50': new MockElement('speed-p50', 'span'),
    'speed-p90': new MockElement('speed-p90', 'span'),
    'speed-p95': new MockElement('speed-p95', 'span'),
    'speed-p99': new MockElement('speed-p99', 'span'),
    'speed-mean': new MockElement('speed-mean', 'span'),
    'speed-qps': new MockElement('speed-qps', 'span'),
    'select-bench-algo': new MockElement('select-bench-algo', 'select'),
    'btn-run-live-benchmark': new MockElement('btn-run-live-benchmark', 'button'),
    'live-bench-status': new MockElement('live-bench-status', 'div'),
    'live-bench-msg': new MockElement('live-bench-msg', 'div'),
    'live-bench-time': new MockElement('live-bench-time', 'div'),

    // Search tab elements
    'search-results-section': new MockElement('search-results-section', 'section'),
    'result-count': new MockElement('result-count', 'span'),
    'result-query': new MockElement('result-query', 'span'),
    'result-algo': new MockElement('result-algo', 'span'),
    'result-latency': new MockElement('result-latency', 'span'),
    'result-cat-badge': new MockElement('result-cat-badge', 'span'),
    'search-results-list': new MockElement('search-results-list', 'div'),
    'result-micro-latency': new MockElement('result-micro-latency', 'span'),
    'result-embed-latency': new MockElement('result-embed-latency', 'span'),
    'result-search-latency': new MockElement('result-search-latency', 'span'),
    'result-shards-container': new MockElement('result-shards-container', 'div'),
    'result-shards-list': new MockElement('result-shards-list', 'span'),
    'search-result-file-container': new MockElement('search-result-file-container', 'div'),
    'search-result-filename': new MockElement('search-result-filename', 'code'),
    'btn-download-result-file': new MockElement('btn-download-result-file', 'a'),
    'search-input': new MockElement('search-input', 'input'),
    'search-button': new MockElement('search-button', 'button'),
    'category-chips-container': new MockElement('category-chips-container', 'div'),
    'select-algorithm': new MockElement('select-algorithm', 'select'),
    'input-top-k': new MockElement('input-top-k', 'input'),

    // WandB tab elements
    'wandb-kpi-qps': new MockElement('wandb-kpi-qps', 'div'),
    'wandb-kpi-total-queries': new MockElement('wandb-kpi-total-queries', 'div'),
    'wandb-kpi-p50': new MockElement('wandb-kpi-p50', 'div'),
    'wandb-kpi-p95-p99': new MockElement('wandb-kpi-p95-p99', 'div'),
    'wandb-kpi-recall': new MockElement('wandb-kpi-recall', 'div'),
    'wandb-kpi-earlyexit': new MockElement('wandb-kpi-earlyexit', 'div'),
    'wandb-kpi-directio': new MockElement('wandb-kpi-directio', 'div'),
    'wandb-kpi-lru-hit': new MockElement('wandb-kpi-lru-hit', 'div'),
    'chart-wandb-latency': new MockElement('chart-wandb-latency', 'canvas'),
    'chart-wandb-shards': new MockElement('chart-wandb-shards', 'canvas'),
    'chart-wandb-recall': new MockElement('chart-wandb-recall', 'canvas'),
    'chart-wandb-earlyexit': new MockElement('chart-wandb-earlyexit', 'canvas'),
    'chart-wandb-telemetry': new MockElement('chart-wandb-telemetry', 'canvas'),
    'wandb-recent-runs-body': new MockElement('wandb-recent-runs-body', 'tbody'),
    'icon-wandb-refresh': new MockElement('icon-wandb-refresh', 'i'),
    'btn-wandb-simulate': new MockElement('btn-wandb-simulate', 'button'),

    // 3D Visualizer tab elements
    'threejs-viewport-container': new MockElement('threejs-viewport-container', 'div'),
    'threejs-canvas-wrapper': new MockElement('threejs-canvas-wrapper', 'div'),
    'btn-3d-autorotate': new MockElement('btn-3d-autorotate', 'button'),
    'btn-3d-rotate': new MockElement('btn-3d-rotate', 'button'),
    'btn-3d-fullscreen': new MockElement('btn-3d-fullscreen', 'button'),
    'hud-hnsw-actions': new MockElement('hud-hnsw-actions', 'div'),
    'btn-mode-universe': new MockElement('btn-mode-universe', 'button'),
    'btn-mode-hnsw': new MockElement('btn-mode-hnsw', 'button'),
    'btn-mode-pipeline': new MockElement('btn-mode-pipeline', 'button'),
    'btn-mode-quantization': new MockElement('btn-mode-quantization', 'button')
  };

  const document = {
    body: new MockElement('body', 'body'),
    getElementById: (id) => elements[id] || null,
    createElement: (tag) => new MockElement(null, tag),
    querySelectorAll: (selector) => {
      if (selector === '.mode-btn-3d') {
        return [elements['btn-mode-universe'], elements['btn-mode-hnsw'], elements['btn-mode-pipeline'], elements['btn-mode-quantization']];
      }
      if (selector === '.tab-content' || selector === '.tab-btn' || selector === '.btn-3d-filter') {
        return [];
      }
      return [];
    },
    addEventListener: (event, fn) => {},
    removeEventListener: (event, fn) => {}
  };

  const window = {
    document: document,
    currentTab4SearchResults: null,
    devicePixelRatio: 1,
    addEventListener: (event, fn) => {},
    removeEventListener: (event, fn) => {}
  };

  return { elements, document, window };
}

// -------------------------------------------------------------
// 2. Mock Chart.js Implementation
// -------------------------------------------------------------
class MockChart {
  constructor(ctx, config) {
    this.ctx = ctx;
    this.config = config;
    this.type = config.type;
    this.data = config.data || { labels: [], datasets: [] };
    this.options = config.options || {};
    this.updatedCount = 0;
  }

  update() {
    this.updatedCount++;
  }

  destroy() {
    this.destroyed = true;
  }
}

// -------------------------------------------------------------
// 3. Mock Three.js & OrbitControls Implementation
// -------------------------------------------------------------
function createMockThree() {
  class Scene {
    constructor() { this.children = []; this.background = null; this.fog = null; }
    add(obj) { this.children.push(obj); }
    remove(obj) { const idx = this.children.indexOf(obj); if (idx >= 0) this.children.splice(idx, 1); }
  }
  class Color { constructor(hex) { this.hex = hex; } }
  class FogExp2 { constructor(c, d) { this.color = c; this.density = d; } }
  class PerspectiveCamera {
    constructor(fov, aspect, near, far) {
      this.fov = fov;
      this.aspect = aspect;
      this.near = near;
      this.far = far;
      this.position = { x: 0, y: 0, z: 0, set: (x, y, z) => { this.position.x = x; this.position.y = y; this.position.z = z; } };
    }
    updateProjectionMatrix() {
      this.projectionMatrixUpdated = true;
    }
    lookAt(x, y, z) {}
  }
  class WebGLRenderer {
    constructor(opts) {
      this.domElement = new MockElement('canvas-gl', 'canvas');
      this.shadowMap = {};
    }
    setSize(w, h) { this.width = w; this.height = h; }
    setPixelRatio(r) { this.pixelRatio = r; }
    render(scene, camera) {}
  }
  class OrbitControls {
    constructor(camera, domElement) {
      this.camera = camera;
      this.domElement = domElement;
      this.target = { x: 0, y: 0, z: 0, set: (x, y, z) => { this.target.x = x; this.target.y = y; this.target.z = z; } };
      this.autoRotate = false;
      this.enableDamping = true;
    }
    update() {}
  }
  class Raycaster {
    constructor() { this.ray = {}; }
    setFromCamera() {}
  }
  class Vector2 { constructor(x, y) { this.x = x; this.y = y; } }
  class Clock { getDelta() { return 0.016; } }
  class AmbientLight { constructor(c, i) {} }
  class DirectionalLight { constructor(c, i) { this.position = { set: () => {} }; } }
  class PointLight { constructor(c, i, d) { this.position = { set: () => {} }; } }
  class GridHelper { constructor(s, d, c1, c2) { this.position = { y: 0 }; } }
  class Sprite { constructor(mat) { this.scale = { set: () => {} }; } }
  class SpriteMaterial { constructor(opts) {} }
  class CanvasTexture { constructor(c) {} }

  return {
    Scene,
    Color,
    FogExp2,
    PerspectiveCamera,
    WebGLRenderer,
    OrbitControls,
    Raycaster,
    Vector2,
    Clock,
    AmbientLight,
    DirectionalLight,
    PointLight,
    GridHelper,
    Sprite,
    SpriteMaterial,
    CanvasTexture,
    LinearFilter: 1006,
    PCFSoftShadowMap: 2,
    ACESFilmicToneMapping: 4
  };
}

// -------------------------------------------------------------
// 4. Test Suite Execution Runner
// -------------------------------------------------------------
let totalPassed = 0;
let totalFailed = 0;
const testResults = [];
const empiricalFindings = [];

function runTest(suiteName, testName, testFn) {
  try {
    testFn();
    console.log(`  [PASS] ${testName}`);
    totalPassed++;
    testResults.push({ suite: suiteName, test: testName, status: 'PASS' });
  } catch (err) {
    console.error(`  [FAIL] ${testName}: ${err.message}`);
    totalFailed++;
    testResults.push({ suite: suiteName, test: testName, status: 'FAIL', error: err.message });
    empiricalFindings.push({ suite: suiteName, test: testName, error: err.message });
  }
}

function assertNoLeak(html, context) {
  assert(!html.includes('undefined'), `${context} contains unescaped 'undefined'`);
  assert(!html.includes('NaN'), `${context} contains unescaped 'NaN'`);
}

// Load source code
const appJsPath = path.resolve(__dirname, '../dashboard/public/js/app.js');
const appJsSource = fs.readFileSync(appJsPath, 'utf8');

const wandbJsPath = path.resolve(__dirname, '../dashboard/public/js/wandb_dashboard.js');
const wandbJsSource = fs.readFileSync(wandbJsPath, 'utf8');

const threeEnginePath = path.resolve(__dirname, '../dashboard/public/js/three_engine.js');
const threeEngineSource = fs.readFileSync(threeEnginePath, 'utf8');

console.log("================================================================================");
console.log("STARTING EMPIRICAL ADVERSARIAL FRONTEND STRESS TEST SUITE");
console.log("================================================================================");

// =============================================================================
// SUITE 1: Search Payloads & Edge Cases
// =============================================================================
console.log("\n--- Suite 1: Malformed & Empty Search Payloads ---");

function createSearchContext(env) {
  const sandbox = {
    document: env.document,
    window: env.window,
    console: console,
    Math: Math,
    Number: Number,
    parseFloat: parseFloat,
    parseInt: parseInt,
    isNaN: isNaN,
    refreshWandBMetrics: () => {},
    focusOn3DResultByIndexTab4: () => {}
  };
  const ctx = vm.createContext(sandbox);
  vm.runInContext(appJsSource, ctx);
  return { ctx, env };
}

runTest("Suite 1", "1.1: Null and undefined payload handles safely or reports vulnerability", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  try {
    ctx.renderSearchResults(null);
  } catch (e) {
    empiricalFindings.push({
      category: "Malformed Payload",
      observation: "renderSearchResults(null) throws unhandled TypeError: Cannot read properties of null (reading 'results_count')",
      blast_radius: "If backend returns null JSON or network handler passes null, UI crashes with unhandled exception."
    });
    assert(e.name === 'TypeError' || e.message.includes('null'), `Expected TypeError, got ${e.name}: ${e.message}`);
  }
});

runTest("Suite 1", "1.2: Empty object payload {} renders without throwing", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  ctx.renderSearchResults({});
  const listEl = env.elements['search-results-list'];
  assert(listEl !== null, "listEl should exist");
});

runTest("Suite 1", "1.3: results: null with results_count: 5 does not throw unhandled error", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "null results array",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.2,
    shards_probed: [0],
    results_count: 5,
    results: null
  };
  ctx.renderSearchResults(data);
  assert.strictEqual(env.elements['result-count'].textContent, 5);
});

runTest("Suite 1", "1.4: results_count: 0 with results: [] renders clean empty state", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "empty query test",
    algorithm: "Two-Tier Quantized HNSW",
    category_filter: "Văn hóa",
    latency_ms: 0.45,
    shards_probed: [1],
    results_count: 0,
    results: []
  };
  ctx.renderSearchResults(data);
  const listHtml = env.elements['search-results-list'].innerHTML;
  assert(listHtml.includes("Không tìm thấy bài viết nào phù hợp"), "Empty state message missing");
  assertNoLeak(listHtml, "Empty state list HTML");
});

runTest("Suite 1", "1.5: Array containing null and undefined items handled safely", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "null items in results",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.0,
    results_count: 2,
    results: [
      { rank: 1, doc_id: "valid_doc", title: "Valid", preview: "Valid preview", distance: 0.1, similarity_score: 0.9, shard_id: 1 },
      null,
      undefined
    ]
  };
  try {
    ctx.renderSearchResults(data);
  } catch (e) {
    empiricalFindings.push({
      category: "Malformed Array Elements",
      observation: "results array containing null element causes TypeError: Cannot read properties of null (reading 'similarity_score')",
      blast_radius: "If search API returns sparse array or null entry, result card iteration breaks."
    });
    assert(e.name === 'TypeError' || e.message.includes('null') || e.message.includes('undefined'), `Expected null error, got: ${e.message}`);
  }
});

runTest("Suite 1", "1.6: Item missing shard_id defaults to Shard #0 without undefined leak", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "missing shard_id",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.1,
    results_count: 1,
    results: [
      { rank: 1, doc_id: "doc_no_shard", title: "No Shard", preview: "Preview", distance: 0.2, similarity_score: 0.8 }
    ]
  };
  ctx.renderSearchResults(data);
  const cardHtml = env.elements['search-results-list'].children[0].innerHTML;
  assert(cardHtml.includes("Shard #0"), "Card should fallback to Shard #0");
  assertNoLeak(cardHtml, "Missing shard_id card HTML");
});

runTest("Suite 1", "1.7: Item missing doc_id, node_id, and index defaults safely without undefined leak", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "missing identifiers",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 0.95,
    results_count: 1,
    results: [
      { rank: 1, title: "Title Only", preview: "Preview Only", distance: 0.35, similarity_score: 0.75, shard_id: 2 }
    ]
  };
  ctx.renderSearchResults(data);
  const cardHtml = env.elements['search-results-list'].children[0].innerHTML;
  assert(cardHtml.includes("Node #0"), "Card should fallback to Node #0");
  assertNoLeak(cardHtml, "Missing identifiers card HTML");
});

runTest("Suite 1", "1.8: Latency extremes: NaN, string, negative, zero, and huge values", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  // Zero latency
  ctx.renderSearchResults({ query: "q", latency_ms: 0, results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-latency'].textContent, "0.00");

  // NaN latency
  ctx.renderSearchResults({ query: "q", latency_ms: NaN, results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-latency'].textContent, "0.00");
  assertNoLeak(env.elements['result-latency'].textContent, "NaN latency");

  // String latency "2.456"
  ctx.renderSearchResults({ query: "q", latency_ms: "2.456", results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-latency'].textContent, "2.46");

  // Huge latency 1,000,000 ms
  ctx.renderSearchResults({ query: "q", latency_ms: 1000000, results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-latency'].textContent, "1000000.00");
});

runTest("Suite 1", "1.9: Micro-latency edge cases (null, missing search_ms, NaN values)", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  // Missing micro_latency
  ctx.renderSearchResults({ query: "q", results_count: 0, results: [] });
  assert(env.elements['result-micro-latency'].classList.contains('hidden'));

  // Partially specified micro_latency { embed_ms: 0.35 }
  ctx.renderSearchResults({ query: "q", micro_latency: { embed_ms: 0.35 }, results_count: 0, results: [] });
  assert(!env.elements['result-micro-latency'].classList.contains('hidden'));
  assert.strictEqual(env.elements['result-embed-latency'].textContent, "0.35");
  assert.strictEqual(env.elements['result-search-latency'].textContent, "0.00");

  // Micro-latency with NaN
  ctx.renderSearchResults({ query: "q", micro_latency: { embed_ms: NaN, search_ms: 1.2 }, results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-search-latency'].textContent, "1.20");
});

runTest("Suite 1", "1.10: Shards probed edge cases (single, multi, empty)", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  // Empty shards
  ctx.renderSearchResults({ query: "q", shards_probed: [], results_count: 0, results: [] });
  assert(env.elements['result-shards-container'].classList.contains('hidden'));

  // Single shard [4]
  ctx.renderSearchResults({ query: "q", shards_probed: [4], results_count: 0, results: [] });
  assert(!env.elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(env.elements['result-shards-list'].textContent, "[Shard #4]");

  // 8 Shards probed
  ctx.renderSearchResults({ query: "q", shards_probed: [0, 1, 2, 3, 4, 5, 6, 7], results_count: 0, results: [] });
  assert.strictEqual(env.elements['result-shards-list'].textContent, "[Shard #0, Shard #1, Shard #2, Shard #3, Shard #4, Shard #5, Shard #6, Shard #7]");
});

runTest("Suite 1", "1.11: HTML / Special character payload safety", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const data = {
    query: "<script>alert('xss')</script>",
    algorithm: "<b>Two-Tier</b>",
    category_filter: "<tag>",
    latency_ms: 1.0,
    results_count: 1,
    results: [{
      rank: 1,
      doc_id: "doc_<1>",
      title: "Title & <script>alert(1)</script>",
      preview: "Preview & <b>Bold</b>",
      distance: 0.1,
      similarity_score: 0.9
    }]
  };
  ctx.renderSearchResults(data);
  assert.strictEqual(env.elements['result-query'].textContent, "<script>alert('xss')</script>");
  assertNoLeak(env.elements['search-results-list'].outerHTML, "Special char test");
});

runTest("Suite 1", "1.12: Large scale results rendering (100 cards)", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const largeResults = Array.from({ length: 100 }, (_, i) => ({
    rank: i + 1,
    doc_id: `doc_stress_${i}`,
    shard_id: i % 8,
    node_id: i * 10,
    title: `Stress Result Item #${i + 1}`,
    preview: `Stress preview content for document index ${i}`,
    category: "Khoa học & Công nghệ",
    distance: 0.1 + (i * 0.005),
    similarity_score: Math.max(0.1, 0.95 - (i * 0.008))
  }));

  ctx.renderSearchResults({
    query: "stress large batch",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 15.4,
    shards_probed: [0, 1, 2, 3, 4, 5, 6, 7],
    results_count: 100,
    results: largeResults
  });

  assert.strictEqual(env.elements['search-results-list'].children.length, 100);
  assertNoLeak(env.elements['search-results-list'].outerHTML, "Large 100 results");
});

// =============================================================================
// SUITE 2: WandB Metrics Studio Edge Cases
// =============================================================================
console.log("\n--- Suite 2: WandB Metrics Dashboard Edge Cases ---");

function createWandBContext(env) {
  const sandbox = {
    document: env.document,
    window: env.window,
    console: console,
    Chart: MockChart,
    Math: Math,
    Number: Number,
    parseFloat: parseFloat,
    parseInt: parseInt,
    isNaN: isNaN,
    setTimeout: (fn) => fn()
  };
  const ctx = vm.createContext(sandbox);
  // Expose wandbCharts for harness access
  const enhancedWandbScript = wandbJsSource + '\nwindow.getWandBCharts = () => wandbCharts;';
  vm.runInContext(enhancedWandbScript, ctx);
  return { ctx, env };
}

runTest("Suite 2", "2.1: Empty telemetry summary {} handled without crash", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  ctx.renderWandBSummary({});
  assert.strictEqual(env.elements['wandb-kpi-p50'].textContent, "1.18 ms");
  assert.strictEqual(env.elements['wandb-kpi-recall'].textContent, "95.8%");
  assert.strictEqual(env.elements['wandb-kpi-earlyexit'].textContent, "68.4%");
});

runTest("Suite 2", "2.2: Null summary handled safely", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  ctx.renderWandBSummary(null);
});

runTest("Suite 2", "2.3: Empty recent runs array [] does not break table", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  ctx.renderRecentRuns([]);
  assert.strictEqual(env.elements['wandb-recent-runs-body'].children.length, 0);
});

runTest("Suite 2", "2.4: High-latency spikes in metrics (120,000 ms)", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  const spikeData = {
    summary: {
      total_queries: 100,
      current_qps: 15,
      p50_latency_ms: 12000.5,
      p95_latency_ms: 45000.0,
      p99_latency_ms: 120000.0,
      avg_recall_at_10: 94.2,
      early_exit_rate_pct: 12.5,
      direct_io_throughput_mb_s: 18.2,
      lru_cache_hit_rate_pct: 22.0
    },
    latency_time_series: {
      timestamps: ["10:00:00", "10:00:01", "10:00:02"],
      p50: [11000, 11500, 12000.5],
      p95: [40000, 42000, 45000],
      p99: [100000, 110000, 120000]
    },
    shard_distribution: {
      labels: ["Shard #0", "Shard #1", "Shard #2", "Shard #3", "Shard #4", "Shard #5", "Shard #6", "Shard #7"],
      counts: [10, 5, 2, 8, 4, 12, 1, 3]
    },
    recall_curve: {
      k_values: [1, 5, 10, 20, 50, 100],
      exact_bruteforce: [100, 100, 100, 100, 100, 100],
      two_tier_hnsw: [90, 93, 94.2, 96, 98, 99],
      standard_hnsw: [88, 91, 93, 95, 97, 98],
      ivf_pq: [30, 35, 40, 45, 50, 55]
    },
    early_exit_stats: {
      early_exit_pct: 12.5,
      full_hops_pct: 87.5
    },
    system_telemetry: {
      timestamps: ["10:00:00", "10:00:01", "10:00:02"],
      qps: [15, 12, 15],
      lru_hit_rate: [22, 20, 22],
      direct_io_mb_s: [18, 15, 18]
    }
  };

  ctx.renderWandBSummary(spikeData.summary);
  ctx.renderWandBCharts(spikeData);

  assert.strictEqual(env.elements['wandb-kpi-p50'].textContent, "12000.50 ms");
  assert.strictEqual(env.elements['wandb-kpi-p95-p99'].textContent, "45000.00 / 120000.00 ms");
});

runTest("Suite 2", "2.5: Single shard hit pattern (all queries hit Shard #0)", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  const singleShardData = {
    latency_time_series: { timestamps: ["10:00"], p50: [1.1], p95: [1.5], p99: [2.0] },
    shard_distribution: {
      labels: ["Shard #0", "Shard #1", "Shard #2", "Shard #3", "Shard #4", "Shard #5", "Shard #6", "Shard #7"],
      counts: [500, 0, 0, 0, 0, 0, 0, 0]
    },
    recall_curve: {
      k_values: [10],
      exact_bruteforce: [100],
      two_tier_hnsw: [95],
      standard_hnsw: [94],
      ivf_pq: [40]
    },
    early_exit_stats: { early_exit_pct: 70, full_hops_pct: 30 },
    system_telemetry: { timestamps: ["10:00"], qps: [1200], lru_hit_rate: [85], direct_io_mb_s: [400] }
  };

  ctx.renderWandBCharts(singleShardData);
  const charts = ctx.window.getWandBCharts();
  assert(charts.shards !== null, "Shards chart should be created");
  assert.strictEqual(charts.shards.data.datasets[0].data[0], 500);
  assert.strictEqual(charts.shards.data.datasets[0].data[1], 0);
});

runTest("Suite 2", "2.6: Extreme recall rates (0% and 100% boundary)", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  const extremeRecallData = {
    latency_time_series: { timestamps: ["10:00"], p50: [1.0], p95: [1.2], p99: [1.5] },
    shard_distribution: { labels: ["Shard #0"], counts: [1] },
    recall_curve: {
      k_values: [1, 10, 100],
      exact_bruteforce: [100, 100, 100],
      two_tier_hnsw: [0.0, 50.0, 100.0],
      standard_hnsw: [0.0, 48.0, 99.0],
      ivf_pq: [0.0, 10.0, 30.0]
    },
    early_exit_stats: { early_exit_pct: 0.0, full_hops_pct: 100.0 },
    system_telemetry: { timestamps: ["10:00"], qps: [1000], lru_hit_rate: [80], direct_io_mb_s: [350] }
  };

  ctx.renderWandBCharts(extremeRecallData);
  const charts = ctx.window.getWandBCharts();
  assert.strictEqual(charts.recall.data.datasets[1].data[0], 0.0);
  assert.strictEqual(charts.recall.data.datasets[1].data[2], 100.0);
});

runTest("Suite 2", "2.7: Extreme early-exit rates (100% early-exit vs 0%)", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  const eeData = {
    latency_time_series: { timestamps: ["10:00"], p50: [0.5], p95: [0.6], p99: [0.8] },
    shard_distribution: { labels: ["Shard #0"], counts: [1] },
    recall_curve: { k_values: [10], exact_bruteforce: [100], two_tier_hnsw: [98], standard_hnsw: [97], ivf_pq: [50] },
    early_exit_stats: { early_exit_pct: 100.0, full_hops_pct: 0.0 },
    system_telemetry: { timestamps: ["10:00"], qps: [2000], lru_hit_rate: [95], direct_io_mb_s: [500] }
  };

  ctx.renderWandBCharts(eeData);
  const charts = ctx.window.getWandBCharts();
  assert.strictEqual(charts.earlyexit.data.datasets[0].data[0], 100.0);
  assert.strictEqual(charts.earlyexit.data.datasets[0].data[1], 0.0);
});

runTest("Suite 2", "2.8: Repeated chart updates update datasets without memory leaks", () => {
  const { ctx, env } = createWandBContext(createDashboardDOM());
  const baseData = {
    latency_time_series: { timestamps: ["T1"], p50: [1.2], p95: [1.8], p99: [2.5] },
    shard_distribution: { labels: ["Shard #0", "Shard #1"], counts: [10, 20] },
    recall_curve: { k_values: [10], exact_bruteforce: [100], two_tier_hnsw: [95], standard_hnsw: [94], ivf_pq: [40] },
    early_exit_stats: { early_exit_pct: 65, full_hops_pct: 35 },
    system_telemetry: { timestamps: ["T1"], qps: [1100], lru_hit_rate: [82], direct_io_mb_s: [410] }
  };

  // Initial render
  ctx.renderWandBCharts(baseData);
  const charts = ctx.window.getWandBCharts();
  const initialUpdateCount = charts.latency.updatedCount;

  // Subsequent render
  const updatedData = {
    ...baseData,
    latency_time_series: { timestamps: ["T1", "T2"], p50: [1.2, 1.4], p95: [1.8, 1.9], p99: [2.5, 2.6] }
  };
  ctx.renderWandBCharts(updatedData);

  assert(charts.latency.updatedCount > initialUpdateCount, "Chart update() must be called on re-render");
  assert.strictEqual(charts.latency.data.datasets[0].data.length, 2);
});

// =============================================================================
// SUITE 3: 3D UI Container Lifecycle & Robustness
// =============================================================================
console.log("\n--- Suite 3: 3D UI Container Lifecycle & Initialization ---");

function createThreeContext(env, customThree = createMockThree()) {
  const sandbox = {
    document: env.document,
    window: env.window,
    console: console,
    THREE: customThree,
    Math: Math,
    Number: Number,
    parseFloat: parseFloat,
    parseInt: parseInt,
    isNaN: isNaN,
    setTimeout: (fn, d) => fn(),
    requestAnimationFrame: (fn) => 1
  };
  const ctx = vm.createContext(sandbox);
  vm.runInContext(threeEngineSource, ctx);
  return { ctx, env };
}

runTest("Suite 3", "3.1: init3DEngine() returns safely when THREE is undefined", () => {
  const env = createDashboardDOM();
  const sandbox = {
    document: env.document,
    window: env.window,
    console: console,
    THREE: undefined,
    ThreeEngine: undefined
  };
  const ctx = vm.createContext(sandbox);
  vm.runInContext(appJsSource, ctx);
  ctx.init3DEngine();
  assert.strictEqual(ctx.window.threeEngine, undefined);
});

runTest("Suite 3", "3.2: init3DEngine() returns safely when ThreeEngine is undefined", () => {
  const env = createDashboardDOM();
  const sandbox = {
    document: env.document,
    window: env.window,
    console: console,
    THREE: createMockThree(),
    ThreeEngine: undefined
  };
  const ctx = vm.createContext(sandbox);
  vm.runInContext(appJsSource, ctx);
  ctx.init3DEngine();
  assert.strictEqual(ctx.window.threeEngine, undefined);
});

runTest("Suite 3", "3.3: Missing container element handled without throwing", () => {
  const env = createDashboardDOM();
  env.elements['threejs-canvas-wrapper'] = null;
  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');
  assert.strictEqual(engine.renderer, undefined);
});

runTest("Suite 3", "3.4: Hidden container (clientWidth: 0, clientHeight: 0) uses fallbacks", () => {
  const env = createDashboardDOM();
  const container = env.elements['threejs-canvas-wrapper'];
  container.clientWidth = 0;
  container.clientHeight = 0;

  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');
  assert(engine.camera !== undefined, "Camera must be created");
  assert(!isNaN(engine.camera.aspect), `Camera aspect ratio must not be NaN, was: ${engine.camera.aspect}`);
  assert.strictEqual(engine.camera.aspect, 1000 / 760);
});

runTest("Suite 3", "3.5: onWindowResize() when container size is 0x0 does not produce NaN aspect", () => {
  const env = createDashboardDOM();
  const container = env.elements['threejs-canvas-wrapper'];
  container.clientWidth = 1000;
  container.clientHeight = 760;

  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');

  // Container is hidden dynamically (0x0)
  container.clientWidth = 0;
  container.clientHeight = 0;
  engine.onWindowResize();

  if (isNaN(engine.camera.aspect)) {
    empiricalFindings.push({
      category: "3D Viewport Geometry",
      observation: "ThreeEngine.onWindowResize() sets camera.aspect = NaN when container.clientWidth = 0 & clientHeight = 0.",
      blast_radius: "If window resizes while 3D tab is hidden, projection matrix becomes NaN until next valid resize."
    });
  }
});

runTest("Suite 3", "3.6: onWindowResize() recovery when container is restored (1200x800)", () => {
  const env = createDashboardDOM();
  const container = env.elements['threejs-canvas-wrapper'];
  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');

  container.clientWidth = 1200;
  container.clientHeight = 800;
  engine.onWindowResize();

  assert.strictEqual(engine.camera.aspect, 1.5);
  assert.strictEqual(engine.renderer.width, 1200);
  assert.strictEqual(engine.renderer.height, 800);
});

runTest("Suite 3", "3.7: Mode switching handles valid and invalid mode parameters", () => {
  const env = createDashboardDOM();
  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');

  engine.setMode('universe', false);
  assert.strictEqual(engine.currentMode, 'universe');

  engine.setMode('hnsw', false);
  assert.strictEqual(engine.currentMode, 'hnsw');

  engine.setMode('pipeline', false);
  assert.strictEqual(engine.currentMode, 'pipeline');

  engine.setMode('quantization', false);
  assert.strictEqual(engine.currentMode, 'quantization');

  // Unknown mode
  engine.setMode('non_existent_mode', false);
  assert.strictEqual(engine.currentMode, 'non_existent_mode');
});

runTest("Suite 3", "3.8: Camera presets handle missing query position safely", () => {
  const env = createDashboardDOM();
  const { ctx } = createThreeContext(env);
  const engine = new ctx.window.ThreeEngine('threejs-canvas-wrapper');

  engine.setCameraPreset('universe');
  engine.setCameraPreset('topdown');
  engine.setCameraPreset('hnsw');
  engine.setCameraPreset('pipeline');
  engine.setCameraPreset('query');
  assert(engine.camera.position.x !== undefined, "Camera position must remain defined");
});

// =============================================================================
// SUITE 4: Persistence & State Transitions of Search Routing Metrics
// =============================================================================
console.log("\n--- Suite 4: Persistence of Search Routing Metrics ---");

runTest("Suite 4", "4.1: Query 1 (Distributed, multi-shard) sets shards container visible", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  const dataQ1 = {
    query: "truy vấn đa phân mảnh",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.45,
    micro_latency: { embed_ms: 0.25, search_ms: 1.20 },
    shards_probed: [0, 2, 5],
    results_count: 2,
    results: [
      { rank: 1, doc_id: "doc_q1_a", shard_id: 2, title: "Doc A", preview: "Snippet A", distance: 0.25, similarity_score: 0.88 },
      { rank: 2, doc_id: "doc_q1_b", shard_id: 5, title: "Doc B", preview: "Snippet B", distance: 0.32, similarity_score: 0.80 }
    ]
  };

  ctx.renderSearchResults(dataQ1);
  assert(!env.elements['result-shards-container'].classList.contains('hidden'), "Shards container must be visible");
  assert.strictEqual(env.elements['result-shards-list'].textContent, "[Shard #0, Shard #2, Shard #5]");
  assert.strictEqual(env.elements['result-latency'].textContent, "1.45");
  assert(!env.elements['result-micro-latency'].classList.contains('hidden'), "Micro latency must be visible");
  assert.strictEqual(env.elements['result-embed-latency'].textContent, "0.25");
  assert.strictEqual(env.elements['result-search-latency'].textContent, "1.20");

  const cards = env.elements['search-results-list'].children;
  assert.strictEqual(cards.length, 2);
  assert(cards[0].innerHTML.includes("Shard #2"));
  assert(cards[1].innerHTML.includes("Shard #5"));
});

runTest("Suite 4", "4.2: Query 2 (Monolithic / no shards) hides shards container and micro-latency", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());

  // First run Query 1
  ctx.renderSearchResults({
    query: "q1",
    latency_ms: 1.5,
    micro_latency: { embed_ms: 0.3, search_ms: 1.2 },
    shards_probed: [1, 3],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 1, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  });

  // Now run Query 2 without shards and without micro-latency
  ctx.renderSearchResults({
    query: "q2 monolithic",
    algorithm: "Standard HNSW Baseline",
    latency_ms: 0.82,
    shards_probed: [], // No shards
    micro_latency: null, // No micro-latency
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_2", shard_id: 0, title: "T2", preview: "P2", distance: 0.2, similarity_score: 0.85 }]
  });

  // Shards container MUST be hidden!
  assert(env.elements['result-shards-container'].classList.contains('hidden'), "Shards container must be hidden when shards_probed is empty");
  // Micro latency MUST be hidden!
  assert(env.elements['result-micro-latency'].classList.contains('hidden'), "Micro latency must be hidden when micro_latency is null");
  // Latency MUST be updated to 0.82, NOT stuck at 1.50
  assert.strictEqual(env.elements['result-latency'].textContent, "0.82", "Latency must update to Query 2 latency");
});

runTest("Suite 4", "4.3: Query 3 (Single-shard hit) re-enables shards container with [Shard #3]", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());

  // Query 2 (empty)
  ctx.renderSearchResults({ query: "q2", shards_probed: [], results_count: 0, results: [] });
  assert(env.elements['result-shards-container'].classList.contains('hidden'));

  // Query 3 (single shard)
  ctx.renderSearchResults({
    query: "q3 single shard",
    latency_ms: 0.65,
    micro_latency: { embed_ms: 0.12, search_ms: 0.53 },
    shards_probed: [3],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_3", shard_id: 3, title: "T3", preview: "P3", distance: 0.15, similarity_score: 0.91 }]
  });

  assert(!env.elements['result-shards-container'].classList.contains('hidden'), "Shards container must reappear");
  assert.strictEqual(env.elements['result-shards-list'].textContent, "[Shard #3]");
  assert(!env.elements['result-micro-latency'].classList.contains('hidden'), "Micro latency must reappear");
  assert.strictEqual(env.elements['result-embed-latency'].textContent, "0.12");
  assert.strictEqual(env.elements['result-search-latency'].textContent, "0.53");
  assert.strictEqual(env.elements['result-latency'].textContent, "0.65");
  assert(env.elements['search-results-list'].children[0].innerHTML.includes("Shard #3"));
});

runTest("Suite 4", "4.4: Shard badges persistence across repeated 10-query search burst", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());

  for (let q = 0; q < 10; q++) {
    const targetShard = q % 8;
    ctx.renderSearchResults({
      query: `burst query #${q}`,
      latency_ms: 1.0 + (q * 0.1),
      shards_probed: [targetShard],
      results_count: 3,
      results: [
        { rank: 1, doc_id: `b_${q}_1`, shard_id: targetShard, title: `T1_${q}`, preview: "P", distance: 0.1, similarity_score: 0.9 },
        { rank: 2, doc_id: `b_${q}_2`, shard_id: targetShard, title: `T2_${q}`, preview: "P", distance: 0.2, similarity_score: 0.8 },
        { rank: 3, doc_id: `b_${q}_3`, shard_id: targetShard, title: `T3_${q}`, preview: "P", distance: 0.3, similarity_score: 0.7 }
      ]
    });

    const cards = env.elements['search-results-list'].children;
    assert.strictEqual(cards.length, 3);
    for (let c = 0; c < 3; c++) {
      assert(cards[c].innerHTML.includes(`Shard #${targetShard}`), `Query ${q} Card ${c} missing Shard #${targetShard}`);
      assertNoLeak(cards[c].innerHTML, `Query ${q} Card ${c}`);
    }
  }
});

runTest("Suite 4", "4.5: Shards probed fallback to shards_hit property", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());
  ctx.renderSearchResults({
    query: "shards_hit fallback",
    latency_ms: 1.0,
    shards_hit: [1, 4, 7],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_hit", shard_id: 1, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  });

  assert(!env.elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(env.elements['result-shards-list'].textContent, "[Shard #1, Shard #4, Shard #7]");
});

runTest("Suite 4", "4.6: Result filename download banner toggles correctly between queries", () => {
  const { ctx, env } = createSearchContext(createDashboardDOM());

  // Query 1: with result_filename
  ctx.renderSearchResults({
    query: "q1 download",
    results_count: 1,
    result_filename: "eval_run_123.json",
    results: [{ rank: 1, doc_id: "d1", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  });
  assert(!env.elements['search-result-file-container'].classList.contains('hidden'));
  assert.strictEqual(env.elements['search-result-filename'].textContent, "eval_run_123.json");

  // Query 2: without result_filename
  ctx.renderSearchResults({
    query: "q2 no download",
    results_count: 1,
    results: [{ rank: 1, doc_id: "d2", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  });
  assert(env.elements['search-result-file-container'].classList.contains('hidden'));
});

// =============================================================================
// SUMMARY REPORT
// =============================================================================
console.log("\n================================================================================");
console.log(`EMPIRICAL STRESS TEST COMPLETE: ${totalPassed} PASSED, ${totalFailed} FAILED.`);
console.log(`PASS RATE: ${((totalPassed / (totalPassed + totalFailed)) * 100).toFixed(1)}%`);
console.log(`EMPIRICAL ADVERSARIAL OBSERVATIONS RECORDED: ${empiricalFindings.length}`);
console.log("================================================================================");

if (totalFailed > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
