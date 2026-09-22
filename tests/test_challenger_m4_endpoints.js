/**
 * Empirical Stress Test Harness for Backend Endpoints:
 * - /api/vectors-3d
 * - /api/hnsw-topology-3d
 * - /api/wandb-metrics
 *
 * Tests:
 * 1. Concurrency (100 parallel requests per endpoint)
 * 2. Missing cache fallback (graceful 200 with fallback data)
 * 3. Empty cache file (0 bytes) handling
 * 4. Empty object cache ({}) handling
 * 5. Corrupted JSON cache syntax handling
 * 6. WandB Telemetry stress and malformed input handling
 * 7. Schema completeness and numeric validity checks
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const assert = require('assert');

const ROOT_DIR = path.resolve(__dirname, '..');
const { app, getFallback3DData, wandbTelemetry } = require(path.join(ROOT_DIR, 'dashboard', 'server.js'));

const CACHE_PATH = path.join(ROOT_DIR, 'data', 'processed', 'vectors_3d_cache.json');
const CACHE_BACKUP_PATH = path.join(ROOT_DIR, 'data', 'processed', 'vectors_3d_cache.json.bak_challenger');

let server;
let baseUrl;

function startServer() {
  return new Promise((resolve) => {
    server = app.listen(0, '127.0.0.1', () => {
      const port = server.address().port;
      baseUrl = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
}

function stopServer() {
  return new Promise((resolve) => {
    if (server) {
      server.close(resolve);
    } else {
      resolve();
    }
  });
}

async function request(endpoint) {
  const url = `${baseUrl}${endpoint}`;
  const res = await fetch(url);
  const status = res.status;
  const json = await res.json().catch(() => null);
  return { status, json };
}

async function runConcurrencyTest(endpoint, totalRequests) {
  const promises = [];
  for (let i = 0; i < totalRequests; i++) {
    promises.push(request(endpoint));
  }
  const results = await Promise.all(promises);
  return results;
}

async function runTestSuite() {
  console.log('===============================================================');
  console.log('CHALLENGER M4: EMPIRICAL STRESS TESTS ON BACKEND ENDPOINTS');
  console.log('===============================================================');

  await startServer();

  let hadOriginalCache = false;
  if (fs.existsSync(CACHE_PATH)) {
    hadOriginalCache = true;
    fs.copyFileSync(CACHE_PATH, CACHE_BACKUP_PATH);
  }

  let totalPassed = 0;
  let totalFailed = 0;
  const findings = [];

  function recordPass(testName) {
    console.log(`[PASS] ${testName}`);
    totalPassed++;
  }

  function recordFail(testName, error) {
    console.error(`[FAIL] ${testName}: ${error}`);
    totalFailed++;
    findings.push({ test: testName, error: String(error) });
  }

  try {
    // -------------------------------------------------------------
    // Test 1: Concurrency stress on /api/vectors-3d (100 requests)
    // -------------------------------------------------------------
    try {
      const results = await runConcurrencyTest('/api/vectors-3d', 100);
      assert.strictEqual(results.length, 100, 'Expected 100 responses');
      for (const r of results) {
        assert.strictEqual(r.status, 200, `Expected status 200, got ${r.status}`);
        assert.strictEqual(r.json.success, true, 'Expected success === true');
        assert.ok(Array.isArray(r.json.vectors), 'Expected vectors array');
        assert.ok(r.json.count > 0, 'Expected non-zero vector count');
        assert.ok(r.json.bounds, 'Expected bounds object');
      }
      recordPass('Test 1: 100 concurrent requests to /api/vectors-3d');
    } catch (err) {
      recordFail('Test 1: 100 concurrent requests to /api/vectors-3d', err.message);
    }

    // -------------------------------------------------------------
    // Test 2: Concurrency stress on /api/hnsw-topology-3d (100 requests)
    // -------------------------------------------------------------
    try {
      const results = await runConcurrencyTest('/api/hnsw-topology-3d', 100);
      assert.strictEqual(results.length, 100, 'Expected 100 responses');
      for (const r of results) {
        assert.strictEqual(r.status, 200, `Expected status 200, got ${r.status}`);
        assert.strictEqual(r.json.success, true, 'Expected success === true');
        assert.ok(r.json.topology, 'Expected topology object');
        assert.ok(Array.isArray(r.json.topology.layers), 'Expected topology layers');
        assert.ok(Array.isArray(r.json.topology.intra_edges), 'Expected intra_edges array');
        assert.ok(Array.isArray(r.json.topology.inter_links), 'Expected inter_links array');
      }
      recordPass('Test 2: 100 concurrent requests to /api/hnsw-topology-3d');
    } catch (err) {
      recordFail('Test 2: 100 concurrent requests to /api/hnsw-topology-3d', err.message);
    }

    // -------------------------------------------------------------
    // Test 3: Concurrency stress on /api/wandb-metrics (100 requests)
    // -------------------------------------------------------------
    try {
      const results = await runConcurrencyTest('/api/wandb-metrics', 100);
      assert.strictEqual(results.length, 100, 'Expected 100 responses');
      for (const r of results) {
        assert.strictEqual(r.status, 200, `Expected status 200, got ${r.status}`);
        assert.strictEqual(r.json.success, true, 'Expected success === true');
        assert.ok(r.json.summary, 'Expected summary metrics');
        assert.ok(r.json.latency_time_series, 'Expected latency_time_series');
        assert.ok(r.json.shard_distribution, 'Expected shard_distribution');
        assert.ok(r.json.recall_curve, 'Expected recall_curve');
        assert.ok(r.json.early_exit_stats, 'Expected early_exit_stats');
        assert.ok(r.json.system_telemetry, 'Expected system_telemetry');
        assert.ok(Array.isArray(r.json.recent_runs), 'Expected recent_runs array');
      }
      recordPass('Test 3: 100 concurrent requests to /api/wandb-metrics');
    } catch (err) {
      recordFail('Test 3: 100 concurrent requests to /api/wandb-metrics', err.message);
    }

    // -------------------------------------------------------------
    // Test 4: Missing cache fallback behavior
    // -------------------------------------------------------------
    try {
      if (fs.existsSync(CACHE_PATH)) {
        fs.unlinkSync(CACHE_PATH);
      }
      const resVec = await request('/api/vectors-3d');
      assert.strictEqual(resVec.status, 200);
      assert.strictEqual(resVec.json.success, true);
      assert.strictEqual(resVec.json.count, 240, 'Fallback count should be 240');
      assert.strictEqual(resVec.json.vectors.length, 240);

      const resTop = await request('/api/hnsw-topology-3d');
      assert.strictEqual(resTop.status, 200);
      assert.strictEqual(resTop.json.success, true);
      assert.strictEqual(resTop.json.topology.layers.length, 3, 'Fallback should have 3 layers');
      assert.strictEqual(resTop.json.topology.stats.total_nodes_l0, 120);
      recordPass('Test 4: Missing cache gracefully falls back to dynamic 3D generator (status 200, 240 vectors, 120 L0 topology nodes)');
    } catch (err) {
      recordFail('Test 4: Missing cache fallback', err.message);
    }

    // -------------------------------------------------------------
    // Test 5: Empty cache file (0-byte file)
    // -------------------------------------------------------------
    try {
      fs.writeFileSync(CACHE_PATH, '');
      const resVec = await request('/api/vectors-3d');
      const resTop = await request('/api/hnsw-topology-3d');

      // Server catches JSON.parse error and returns 500 with error message
      assert.strictEqual(resVec.status, 500, 'Expected status 500 for 0-byte invalid JSON');
      assert.strictEqual(resVec.json.success, false);
      assert.ok(resVec.json.error.includes('JSON'), 'Error should describe JSON parsing error');

      assert.strictEqual(resTop.status, 500, 'Expected status 500 for 0-byte invalid JSON');
      assert.strictEqual(resTop.json.success, false);
      recordPass('Test 5: 0-byte cache file safely caught by try/catch with status 500 (no process crash)');
    } catch (err) {
      recordFail('Test 5: 0-byte cache file', err.message);
    }

    // -------------------------------------------------------------
    // Test 6: Corrupted syntax in cache file
    // -------------------------------------------------------------
    try {
      fs.writeFileSync(CACHE_PATH, '{"count": 50, "vectors": [{"x": 1, "y":'); // truncated JSON
      const resVec = await request('/api/vectors-3d');
      const resTop = await request('/api/hnsw-topology-3d');

      assert.strictEqual(resVec.status, 500);
      assert.strictEqual(resVec.json.success, false);
      assert.strictEqual(resTop.status, 500);
      assert.strictEqual(resTop.json.success, false);
      recordPass('Test 6: Truncated corrupted JSON cache safely returns status 500 with error diagnostics');
    } catch (err) {
      recordFail('Test 6: Corrupted syntax cache', err.message);
    }

    // -------------------------------------------------------------
    // Test 7: Empty JSON object cache ({})
    // -------------------------------------------------------------
    try {
      fs.writeFileSync(CACHE_PATH, '{}');
      const resVec = await request('/api/vectors-3d');
      const resTop = await request('/api/hnsw-topology-3d');

      assert.strictEqual(resVec.status, 200);
      assert.strictEqual(resVec.json.success, true);
      assert.strictEqual(resVec.json.count, 0);
      assert.deepStrictEqual(resVec.json.vectors, []);

      assert.strictEqual(resTop.status, 200);
      assert.strictEqual(resTop.json.success, true);
      assert.deepStrictEqual(resTop.json.topology, {});
      recordPass('Test 7: Empty object JSON cache ({}) handled cleanly without throwing error');
    } catch (err) {
      recordFail('Test 7: Empty object JSON cache', err.message);
    }

    // -------------------------------------------------------------
    // Test 8: Valid custom cache file structure
    // -------------------------------------------------------------
    try {
      const validCache = {
        count: 2,
        source: 'Challenger Synthetic Cache',
        bounds: { min: -10, max: 10 },
        vectors: [
          { id: 101, x: 1.0, y: 2.0, z: 3.0, cluster_id: 0, preview: 'Doc 1' },
          { id: 102, x: -1.0, y: -2.0, z: -3.0, cluster_id: 1, preview: 'Doc 2' }
        ],
        hnsw_topology: {
          layers: [{ level: 0, name: 'L0', y: 0, nodes: [{ id: 'n1', x: 0, y: 0, z: 0 }] }],
          intra_edges: [],
          inter_links: [],
          entry_point_id: 'n1',
          stats: { total_nodes_l0: 1, total_edges: 0 }
        }
      };
      fs.writeFileSync(CACHE_PATH, JSON.stringify(validCache));
      const resVec = await request('/api/vectors-3d');
      assert.strictEqual(resVec.status, 200);
      assert.strictEqual(resVec.json.count, 2);
      assert.strictEqual(resVec.json.source, 'Challenger Synthetic Cache');
      assert.strictEqual(resVec.json.vectors.length, 2);

      const resTop = await request('/api/hnsw-topology-3d');
      assert.strictEqual(resTop.status, 200);
      assert.strictEqual(resTop.json.topology.entry_point_id, 'n1');
      recordPass('Test 8: Valid cache file correctly parsed and served');
    } catch (err) {
      recordFail('Test 8: Valid custom cache', err.message);
    }

    // -------------------------------------------------------------
    // Test 9: WandB Telemetry Stress with Adversarial Inputs
    // -------------------------------------------------------------
    try {
      const initialTotal = wandbTelemetry.totalQueries;

      // 1. Extreme numeric latency
      wandbTelemetry.recordQuerySearch({ latency_ms: -100.5, shards_probed: [0, 1] });
      wandbTelemetry.recordQuerySearch({ latency_ms: 1000000.0, shards_probed: [2, 3] });
      wandbTelemetry.recordQuerySearch({ latency_ms: 0.0, shards_probed: [4] });

      // 2. Non-numeric / NaN latency
      wandbTelemetry.recordQuerySearch({ latency_ms: 'invalid_latency', shards_probed: [5] });
      wandbTelemetry.recordQuerySearch({ latency_ms: null, shards_probed: [6] });
      wandbTelemetry.recordQuerySearch({ latency_ms: undefined, shards_probed: [7] });

      // 3. Malformed shards_probed (negative shard IDs, out-of-range, strings, non-arrays)
      wandbTelemetry.recordQuerySearch({ latency_ms: 1.2, shards_probed: [-1, 9999, 'bad_shard', null] });
      wandbTelemetry.recordQuerySearch({ latency_ms: 1.5, shards_probed: null });
      wandbTelemetry.recordQuerySearch({ latency_ms: 1.8, shards_probed: 'not_an_array' });

      // 4. Boundary results array and non-boolean early_exit
      wandbTelemetry.recordQuerySearch({ latency_ms: 2.1, shards_probed: [0], results: null, early_exit: false });
      wandbTelemetry.recordQuerySearch({ latency_ms: 2.2, shards_probed: [1], results: new Array(100).fill({}), early_exit: null });

      assert.strictEqual(wandbTelemetry.totalQueries, initialTotal + 11);

      // Verify payload generation remains robust and non-crashing
      const payload = wandbTelemetry.getMetricsPayload();
      assert.strictEqual(payload.success, true);
      assert.ok(!isNaN(payload.summary.p50_latency_ms), 'p50 must be a valid number');
      assert.ok(!isNaN(payload.summary.p95_latency_ms), 'p95 must be a valid number');
      assert.ok(!isNaN(payload.summary.p99_latency_ms), 'p99 must be a valid number');
      assert.ok(!isNaN(payload.summary.early_exit_rate_pct), 'early_exit_rate_pct must be a valid number');
      assert.strictEqual(payload.shard_distribution.labels.length, 8);
      assert.strictEqual(payload.shard_distribution.counts.length, 8);

      // Verify endpoint also returns valid status 200
      const resMetrics = await request('/api/wandb-metrics');
      assert.strictEqual(resMetrics.status, 200);
      assert.strictEqual(resMetrics.json.success, true);
      assert.strictEqual(resMetrics.json.summary.total_queries, wandbTelemetry.totalQueries);

      recordPass('Test 9: WandB Telemetry survives adversarial inputs (NaN, negative, malformed shards, null results)');
    } catch (err) {
      recordFail('Test 9: WandB Telemetry adversarial inputs', err.message);
    }

    // -------------------------------------------------------------
    // Test 10: Concurrent interleaved reads and writes
    // -------------------------------------------------------------
    try {
      const promises = [];
      for (let i = 0; i < 50; i++) {
        // Interleaved writes
        wandbTelemetry.recordQuerySearch({
          latency_ms: 1.0 + Math.random() * 2.0,
          shards_probed: [i % 8],
          results: [{ doc_id: `doc_${i}` }],
          early_exit: i % 2 === 0
        });
        // Interleaved reads to /api/wandb-metrics
        promises.push(request('/api/wandb-metrics'));
        // Interleaved reads to /api/vectors-3d
        promises.push(request('/api/vectors-3d'));
      }
      const results = await Promise.all(promises);
      for (const r of results) {
        assert.strictEqual(r.status, 200);
        assert.strictEqual(r.json.success, true);
      }
      recordPass('Test 10: Interleaved concurrent telemetry writes and API reads (100 operations)');
    } catch (err) {
      recordFail('Test 10: Interleaved concurrent operations', err.message);
    }

  } finally {
    // Restore cache file state
    if (hadOriginalCache) {
      if (fs.existsSync(CACHE_BACKUP_PATH)) {
        fs.copyFileSync(CACHE_BACKUP_PATH, CACHE_PATH);
        fs.unlinkSync(CACHE_BACKUP_PATH);
      }
    } else {
      if (fs.existsSync(CACHE_PATH)) {
        fs.unlinkSync(CACHE_PATH);
      }
      if (fs.existsSync(CACHE_BACKUP_PATH)) {
        fs.unlinkSync(CACHE_BACKUP_PATH);
      }
    }
    await stopServer();
  }

  console.log('===============================================================');
  console.log(`TOTAL PASSED: ${totalPassed}`);
  console.log(`TOTAL FAILED: ${totalFailed}`);
  if (findings.length > 0) {
    console.log('FINDINGS / ISSUES:');
    findings.forEach(f => console.log(`  - [${f.test}]: ${f.error}`));
  }
  console.log('===============================================================');

  if (totalFailed > 0) {
    process.exit(1);
  }
}

runTestSuite().catch(err => {
  console.error('Fatal test harness error:', err);
  process.exit(1);
});
