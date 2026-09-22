/**
 * Empirical Adversarial Test Harness for Dashboard UI renderSearchResults
 * Tests edge cases: empty results, missing shards, missing micro_latency,
 * zero latency, high latency, shard badges, live CLI payload, and checks for NaN/undefined leaks.
 */

const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');
const { execFileSync } = require('child_process');

// 1. Mock DOM infrastructure
class MockElement {
  constructor(id, tagName = 'div') {
    this.id = id;
    this.tagName = tagName;
    this.textContent = '';
    this.innerHTML = '';
    this.className = '';
    this.children = [];
    this.attributes = {};
    this.href = '';
    this._classes = new Set();
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

  appendChild(child) {
    this.children.push(child);
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
  }

  getAttribute(name) {
    return this.attributes[name];
  }

  get outerHTML() {
    let classes = Array.from(this._classes).join(' ');
    let childrenHTML = this.children.map(c => c.outerHTML).join('');
    return `<${this.tagName} id="${this.id || ''}" class="${classes}">${this.innerHTML}${childrenHTML}</${this.tagName}>`;
  }
}

function createDOM() {
  const elements = {
    'search-results-section': new MockElement('search-results-section'),
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
  };

  const document = {
    getElementById: (id) => elements[id] || null,
    createElement: (tag) => new MockElement(null, tag)
  };

  const window = {
    currentTab4SearchResults: null
  };

  return { elements, document, window };
}

// 2. Load renderSearchResults function from app.js
const appJsPath = path.resolve(__dirname, '../dashboard/public/js/app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

const fnMatch = appJsContent.match(/function renderSearchResults\(data\)\s*\{([\s\S]*?\n\})/);
if (!fnMatch) {
  console.error("FAIL: Could not extract renderSearchResults from app.js");
  process.exit(1);
}

const renderSearchResultsFnSource = 'function renderSearchResults(data) {' + fnMatch[1];

function runRender(data, env) {
  const context = vm.createContext({
    document: env.document,
    window: env.window,
    console: console,
    Math: Math,
    Number: Number
  });
  vm.runInContext(renderSearchResultsFnSource, context);
  const fn = context.renderSearchResults;
  fn(data);
}

function assertNoLeaks(text, contextName) {
  assert(!text.includes('undefined'), `${contextName} leaked 'undefined' in output: ${text}`);
  assert(!text.includes('NaN'), `${contextName} leaked 'NaN' in output: ${text}`);
}

// 3. Test Suites
console.log("==================================================================");
console.log("RUNNING EMPIRICAL ADVERSARIAL TESTS ON renderSearchResults (app.js)");
console.log("==================================================================");

let testsPassed = 0;
let testsFailed = 0;
const findings = [];

function runTestCase(name, testFn) {
  try {
    const env = createDOM();
    testFn(env);
    console.log(`[PASS] ${name}`);
    testsPassed++;
  } catch (err) {
    console.error(`[FAIL] ${name}`);
    console.error(`       Error: ${err.message}`);
    testsFailed++;
    findings.push({ test: name, error: err.message });
  }
}

// Test 1: Standard Full Payload
runTestCase("Test 1: Standard Full Payload", (env) => {
  const data = {
    query: "thị trường tài chính",
    algorithm: "Two-Tier Quantized HNSW",
    category_filter: "Kinh doanh",
    latency_ms: 1.45,
    micro_latency: { embed_ms: 0.20, search_ms: 1.25 },
    shards_probed: [0, 2, 5],
    results_count: 2,
    results: [
      { rank: 1, doc_id: "doc_1", shard_id: 2, node_id: 101, title: "Bài viết A", preview: "Tóm tắt A", category: "Kinh doanh", distance: 0.2814, similarity_score: 0.852 },
      { rank: 2, doc_id: "doc_2", shard_id: 5, node_id: 202, title: "Bài viết B", preview: "Tóm tắt B", category: "Kinh doanh", distance: 0.3541, similarity_score: 0.764 }
    ]
  };

  runRender(data, env);

  const { elements } = env;
  assert.strictEqual(elements['result-count'].textContent, 2);
  assert.strictEqual(elements['result-query'].textContent, "thị trường tài chính");
  assert.strictEqual(elements['result-algo'].textContent, "Two-Tier Quantized HNSW");
  assert.strictEqual(elements['result-latency'].textContent, "1.45");
  assert.strictEqual(elements['result-cat-badge'].textContent, "Chuyên mục: Kinh doanh");

  // Micro latency
  assert(!elements['result-micro-latency'].classList.contains('hidden'));
  assert.strictEqual(elements['result-embed-latency'].textContent, "0.20");
  assert.strictEqual(elements['result-search-latency'].textContent, "1.25");

  // Shards probed
  assert(!elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(elements['result-shards-list'].textContent, "[Shard #0, Shard #2, Shard #5]");

  // Cards
  assert.strictEqual(elements['search-results-list'].children.length, 2);
  const card1 = elements['search-results-list'].children[0].innerHTML;
  assert(card1.includes("Shard #2"), "Card 1 missing Shard #2");
  assert(card1.includes("85%"), "Card 1 missing score 85%");
  assert(card1.includes("0.2814"), "Card 1 missing distance 0.2814");

  assertNoLeaks(elements['search-results-list'].outerHTML, "Standard Payload");
});

// Test 2: Empty results (results_count: 0, results: [])
runTestCase("Test 2: Empty results (results_count: 0)", (env) => {
  const data = {
    query: "từ khóa không tồn tại",
    algorithm: "Two-Tier Quantized HNSW",
    category_filter: "Văn hóa",
    latency_ms: 0.85,
    shards_probed: [1],
    results_count: 0,
    results: []
  };

  runRender(data, env);
  const { elements } = env;
  assert.strictEqual(elements['result-count'].textContent, 0);
  assert(elements['search-results-list'].innerHTML.includes('Không tìm thấy bài viết nào phù hợp'));
  assert(elements['search-results-list'].innerHTML.includes('Văn hóa'));
  assertNoLeaks(elements['search-results-list'].innerHTML, "Empty results");
});

// Test 3: Missing shards_probed (undefined / omitted)
runTestCase("Test 3: Missing shards_probed (omitted)", (env) => {
  const data = {
    query: "test missing shards",
    algorithm: "Standard HNSW Baseline",
    latency_ms: 2.1,
    results_count: 1,
    results: [
      { rank: 1, doc_id: "doc_1", shard_id: 0, title: "Title", preview: "Preview", distance: 0.1, similarity_score: 0.9 }
    ]
  };

  runRender(data, env);
  const { elements } = env;
  assert(elements['result-shards-container'].classList.contains('hidden'));
  assertNoLeaks(elements['search-results-list'].outerHTML, "Missing shards_probed");
});

// Test 4: Missing micro_latency (undefined and null)
runTestCase("Test 4: Missing micro_latency (undefined and null)", (env) => {
  const dataUndefined = {
    query: "test missing micro",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.0,
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  };
  runRender(dataUndefined, env);
  assert(env.elements['result-micro-latency'].classList.contains('hidden'));

  const env2 = createDOM();
  const dataNull = {
    ...dataUndefined,
    micro_latency: null
  };
  runRender(dataNull, env2);
  assert(env2.elements['result-micro-latency'].classList.contains('hidden'));
});

// Test 5: Single Shard Probed (shards_probed: [0])
runTestCase("Test 5: Single Shard Probed ([0])", (env) => {
  const data = {
    query: "single shard test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 0.5,
    shards_probed: [0],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  };
  runRender(data, env);
  const { elements } = env;
  assert(!elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(elements['result-shards-list'].textContent, "[Shard #0]");
  assert(elements['search-results-list'].children[0].innerHTML.includes("Shard #0"));
});

// Test 6: 10 Shards Probed ([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
runTestCase("Test 6: 10 Shards Probed ([0..9])", (env) => {
  const shards = Array.from({ length: 10 }, (_, i) => i);
  const data = {
    query: "ten shards test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 4.8,
    shards_probed: shards,
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 7, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  };
  runRender(data, env);
  const { elements } = env;
  assert(!elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(elements['result-shards-list'].textContent, "[Shard #0, Shard #1, Shard #2, Shard #3, Shard #4, Shard #5, Shard #6, Shard #7, Shard #8, Shard #9]");
  assert(elements['search-results-list'].children[0].innerHTML.includes("Shard #7"));
});

// Test 7: Zero Latency (latency_ms: 0, embed_ms: 0, search_ms: 0)
runTestCase("Test 7: Zero Latency (0.00 ms boundary)", (env) => {
  const data = {
    query: "zero latency",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 0,
    micro_latency: { embed_ms: 0, search_ms: 0 },
    shards_probed: [0],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 0, title: "T", preview: "P", distance: 0, similarity_score: 1.0 }]
  };
  runRender(data, env);
  const { elements } = env;
  assert.strictEqual(elements['result-latency'].textContent, "0.00");
  assert.strictEqual(elements['result-embed-latency'].textContent, "0.00");
  assert.strictEqual(elements['result-search-latency'].textContent, "0.00");
  assertNoLeaks(elements['result-latency'].textContent, "Zero Latency");
  assertNoLeaks(elements['search-results-list'].outerHTML, "Zero Latency Card");
});

// Test 8: Large Latency (latency_ms: 99999.999, embed_ms: 5432.1, search_ms: 4567.89)
runTestCase("Test 8: Large Latency (>1000ms)", (env) => {
  const data = {
    query: "large latency",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 99999.999,
    micro_latency: { embed_ms: 5432.10, search_ms: 4567.89 },
    shards_probed: [2],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 2, title: "T", preview: "P", distance: 1.5, similarity_score: 0.1 }]
  };
  runRender(data, env);
  const { elements } = env;
  assert.strictEqual(elements['result-latency'].textContent, "100000.00");
  assert.strictEqual(elements['result-embed-latency'].textContent, "5432.10");
  assert.strictEqual(elements['result-search-latency'].textContent, "4567.89");
  assertNoLeaks(elements['result-latency'].textContent, "Large Latency");
});

// Test 9a: Result Cards with doc_id fallback
runTestCase("Test 9a: Result Cards with doc_id identifier", (env) => {
  const data = {
    query: "doc_id fallback test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.2,
    shards_probed: [1],
    results_count: 1,
    results: [
      { rank: 1, doc_id: "doc_999", shard_id: 1, title: "Doc Title", preview: "Snippet", distance: 0.25, similarity_score: 0.88 }
    ]
  };
  runRender(data, env);
  const { elements } = env;
  const cardHTML = elements['search-results-list'].children[0].innerHTML;
  assert(cardHTML.includes("doc_999"), "Card should display doc_999");
  assert(cardHTML.includes("Shard #1"), "Card should display Shard #1");
  assertNoLeaks(cardHTML, "doc_id card");
});

// Test 9b: Result Cards with node_id fallback
runTestCase("Test 9b: Result Cards with node_id identifier", (env) => {
  const data = {
    query: "node_id fallback test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.2,
    shards_probed: [3],
    results_count: 1,
    results: [
      { rank: 1, node_id: 42, shard_id: 3, title: "Node Title", preview: "Snippet", distance: 0.25, similarity_score: 0.88 }
    ]
  };
  runRender(data, env);
  const { elements } = env;
  const cardHTML = elements['search-results-list'].children[0].innerHTML;
  assert(cardHTML.includes("Node #42"), "Card should display Node #42");
  assert(cardHTML.includes("Shard #3"), "Card should display Shard #3");
  assertNoLeaks(cardHTML, "node_id card");
});

// Test 9c: Result Cards with index fallback
runTestCase("Test 9c: Result Cards with index identifier", (env) => {
  const data = {
    query: "index fallback test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.2,
    shards_probed: [2],
    results_count: 1,
    results: [
      { rank: 1, index: 123, shard_id: 2, title: "Index Title", preview: "Snippet", distance: 0.25, similarity_score: 0.88 }
    ]
  };
  runRender(data, env);
  const { elements } = env;
  const cardHTML = elements['search-results-list'].children[0].innerHTML;
  assert(cardHTML.includes("Node #123"), "Card should display Node #123");
  assert(cardHTML.includes("Shard #2"), "Card should display Shard #2");
  assertNoLeaks(cardHTML, "index card");
});

// Test 10: Uploaded file search presentation
runTestCase("Test 10: Uploaded file search presentation", (env) => {
  const data = {
    uploaded_file: "research_notes.txt",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.5,
    shards_probed: [0],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  };
  runRender(data, env);
  assert.strictEqual(env.elements['result-query'].textContent, "Tệp tải lên: research_notes.txt");
});

// Test 11: Query evaluation log file download banner
runTestCase("Test 11: Query evaluation log file download banner", (env) => {
  const data = {
    query: "download query test",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.5,
    shards_probed: [0],
    result_filename: "query_20260921_120000.json",
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_1", shard_id: 0, title: "T", preview: "P", distance: 0.1, similarity_score: 0.9 }]
  };
  runRender(data, env);
  const { elements } = env;
  assert(!elements['search-result-file-container'].classList.contains('hidden'));
  assert.strictEqual(elements['search-result-filename'].textContent, "query_20260921_120000.json");
  assert.strictEqual(elements['btn-download-result-file'].getAttribute('download'), "query_20260921_120000.json");
  assert.strictEqual(elements['btn-download-result-file'].href, "/api/eval/download/query/query_20260921_120000.json");
});

// Test 12: Live Integration with search_bridge.py CLI output
runTestCase("Test 12: Live Integration with search_bridge.py CLI", (env) => {
  const stdout = execFileSync('python', ['dashboard/scripts/search_bridge.py', '--query', 'kinh tế Việt Nam', '--top-k', '3'], { encoding: 'utf8' });
  const jsonStart = stdout.indexOf('{');
  assert(jsonStart >= 0, "No JSON found in search_bridge output");
  const livePayload = JSON.parse(stdout.substring(jsonStart));

  runRender(livePayload, env);
  const { elements } = env;

  assert.strictEqual(elements['result-count'].textContent, livePayload.results_count);
  assert(!elements['result-shards-container'].classList.contains('hidden'));
  assert.strictEqual(elements['search-results-list'].children.length, livePayload.results.length);

  for (let i = 0; i < elements['search-results-list'].children.length; i++) {
    const cardHtml = elements['search-results-list'].children[i].innerHTML;
    assertNoLeaks(cardHtml, `Live card #${i+1}`);
  }
});

// Test 13: Search Result Cards include "Xem 3D" focus button
runTestCase("Test 13: Search Result Cards include 'Xem 3D' focus button", (env) => {
  const data = {
    query: "kiem thu 3D",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.25,
    shards_probed: [0, 1],
    results_count: 1,
    results: [{ rank: 1, doc_id: "doc_3d_test", shard_id: 1, title: "Title 3D", preview: "Preview 3D", distance: 0.15, similarity_score: 0.92 }]
  };
  runRender(data, env);
  const cardHtml = env.elements['search-results-list'].children[0].innerHTML;
  assert(cardHtml.includes("Xem 3D"), "Card must include 'Xem 3D' button");
  assert(cardHtml.includes("focusOn3DResultByIndexTab4(0)"), "Card must call focusOn3DResultByIndexTab4");
  assert(cardHtml.includes("Shard #1"), "Card must display Shard #1");
});

// Test 14: 3D Visualizer HTML markup & CDN assets validation
runTestCase("Test 14: 3D Visualizer HTML markup & CDN assets validation", () => {
  const indexPath = path.resolve(__dirname, '../dashboard/public/index.html');
  const indexHtml = fs.readFileSync(indexPath, 'utf8');

  assert(indexHtml.includes('three.min.js'), "index.html missing Three.js CDN");
  assert(indexHtml.includes('OrbitControls.js'), "index.html missing OrbitControls CDN");
  assert(indexHtml.includes('btn-tab-3d-visualizer'), "index.html missing btn-tab-3d-visualizer");
  assert(indexHtml.includes('id="tab-3d-visualizer"'), "index.html missing section #tab-3d-visualizer");
  assert(indexHtml.includes('threejs-viewport-container'), "index.html missing threejs-viewport-container");
  assert(indexHtml.includes('threejs-canvas-wrapper'), "index.html missing threejs-canvas-wrapper");
  assert(indexHtml.includes('js/three_engine.js'), "index.html missing three_engine.js script tag");
  assert(indexHtml.includes('js/three_vector_space.js'), "index.html missing three_vector_space.js script tag");
  assert(indexHtml.includes('js/three_hnsw_graph.js'), "index.html missing three_hnsw_graph.js script tag");
  assert(indexHtml.includes('js/three_pipeline_3d.js'), "index.html missing three_pipeline_3d.js script tag");
});

// Test 15: WandB Metrics Studio HTML markup & panels validation
runTestCase("Test 15: WandB Metrics Studio HTML markup & panels validation", () => {
  const indexPath = path.resolve(__dirname, '../dashboard/public/index.html');
  const indexHtml = fs.readFileSync(indexPath, 'utf8');

  assert(indexHtml.includes('btn-tab-wandb-metrics'), "index.html missing btn-tab-wandb-metrics");
  assert(indexHtml.includes('id="tab-wandb-metrics"'), "index.html missing section #tab-wandb-metrics");
  assert(indexHtml.includes('id="chart-wandb-latency"'), "index.html missing chart-wandb-latency canvas");
  assert(indexHtml.includes('id="chart-wandb-shards"'), "index.html missing chart-wandb-shards canvas");
  assert(indexHtml.includes('id="chart-wandb-recall"'), "index.html missing chart-wandb-recall canvas");
  assert(indexHtml.includes('id="chart-wandb-earlyexit"'), "index.html missing chart-wandb-earlyexit canvas");
  assert(indexHtml.includes('id="chart-wandb-telemetry"'), "index.html missing chart-wandb-telemetry canvas");
  assert(indexHtml.includes('js/wandb_dashboard.js'), "index.html missing wandb_dashboard.js script tag");
});

// Test 16: Backend 3D Fallback Generator & Topology Data
runTestCase("Test 16: Backend 3D Fallback Generator & Topology Data", () => {
  const { getFallback3DData } = require('../dashboard/server.js');
  assert.strictEqual(typeof getFallback3DData, 'function', "getFallback3DData must be a function");
  const fallback = getFallback3DData();
  assert(fallback.count >= 100, `Fallback vectors count too low: ${fallback.count}`);
  assert(fallback.vectors && fallback.vectors.length >= 100, "Fallback missing vectors array");
  assert(fallback.hnsw_topology, "Fallback missing hnsw_topology");
  assert(fallback.hnsw_topology.layers && fallback.hnsw_topology.layers.length === 3, "HNSW topology must have 3 layers");
  assert(fallback.hnsw_topology.intra_edges && fallback.hnsw_topology.intra_edges.length > 0, "HNSW topology must have intra_edges");
  assert(fallback.hnsw_topology.inter_links && fallback.hnsw_topology.inter_links.length > 0, "HNSW topology must have inter_links");
});

// Test 17: Backend WandB Telemetry & Metrics Collection
runTestCase("Test 17: Backend WandB Telemetry & Metrics Collection", () => {
  const { wandbTelemetry } = require('../dashboard/server.js');
  assert(wandbTelemetry, "wandbTelemetry instance must exist");

  wandbTelemetry.recordQuerySearch({
    latency_ms: 1.32,
    shards_probed: [0, 2, 4],
    results: [{ id: 'doc_1' }],
    early_exit: true
  });

  const payload = wandbTelemetry.getMetricsPayload();
  assert.strictEqual(payload.success, true);
  assert(payload.summary.total_queries > 0, "Total queries must be positive");
  assert(payload.summary.p50_latency_ms > 0, "p50 latency must be positive");
  assert(payload.latency_time_series.p50.length > 0, "Latency time-series p50 array must not be empty");
  assert(payload.latency_time_series.p95.length > 0, "Latency time-series p95 array must not be empty");
  assert(payload.latency_time_series.p99.length > 0, "Latency time-series p99 array must not be empty");
  assert(payload.shard_distribution.labels.length >= 8, "Must track at least 8 shards");
  assert(payload.shard_distribution.counts.length >= 8, "Must have counts for at least 8 shards");
  assert(payload.recall_curve.k_values.length > 0, "Recall curve must have k_values");
  assert(payload.early_exit_stats.early_exit_pct > 0, "Early exit rate must be recorded");
  assert(payload.system_telemetry.qps.length > 0, "System telemetry must have QPS");
});

// ADVERSARIAL STRESS TEST: Adversarial Challenge Cases
console.log("\n--- Adversarial Challenge Tests ---");

function runAdversarialCase(name, testFn) {
  try {
    const env = createDOM();
    testFn(env);
    console.log(`[PASS / ROBUST] ${name}`);
  } catch (err) {
    console.log(`[VULNERABILITY DETECTED] ${name}: ${err.message}`);
    findings.push({ adversarialTest: name, error: err.message });
  }
}

runAdversarialCase("Adv-1: Item lacking doc_id, node_id, and index leaks 'undefined'", (env) => {
  const data = {
    query: "adversarial item",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.0,
    shards_probed: [0],
    results_count: 1,
    results: [{ rank: 1, title: "Title Only", preview: "Snippet" }]
  };
  runRender(data, env);
  const cardHTML = env.elements['search-results-list'].children[0].innerHTML;
  if (cardHTML.includes('undefined')) {
    throw new Error("Rendered card leaked 'Node #undefined'");
  }
});

runAdversarialCase("Adv-2: Null results with non-zero results_count throws unhandled TypeError", (env) => {
  const data = {
    query: "null results",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: 1.0,
    shards_probed: [0],
    results_count: 1,
    results: null
  };
  try {
    runRender(data, env);
  } catch (e) {
    throw new Error(`Unhandled exception: ${e.message}`);
  }
});

runAdversarialCase("Adv-3: NaN in latency_ms renders 'NaN' string", (env) => {
  const data = {
    query: "nan latency",
    algorithm: "Two-Tier Quantized HNSW",
    latency_ms: NaN,
    shards_probed: [0],
    results_count: 0,
    results: []
  };
  runRender(data, env);
  const val = env.elements['result-latency'].textContent;
  if (val.includes('NaN')) {
    throw new Error("Rendered latency contains 'NaN'");
  }
});

console.log("==================================================================");
console.log(`CORE TEST SUITE: ${testsPassed} passed, ${testsFailed} failed.`);
console.log(`ADVERSARIAL FINDINGS COUNT: ${findings.length}`);
console.log("==================================================================");

if (testsFailed > 0) {
  process.exit(1);
} else {
  process.exit(0);
}
