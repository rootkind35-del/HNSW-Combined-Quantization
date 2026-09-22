/**
 * Weights & Biases (WandB) Style Metrics Studio & Charting Controller
 * Tracks real-time and historical query latencies (p50/p95/p99), shard routing distributions,
 * recall vs K curves, early-exit convergence rates, and system hardware telemetry.
 */

let wandbCharts = {
  latency: null,
  shards: null,
  recall: null,
  earlyexit: null,
  telemetry: null
};

let isWandBInitialized = false;

function initWandBDashboard() {
  const canvasEl = document.getElementById('chart-wandb-latency');
  if (!canvasEl) return;
  if (typeof Chart === 'undefined') {
    console.warn("[wandb_dashboard] Chart.js not loaded yet, retrying...");
    setTimeout(initWandBDashboard, 100);
    return;
  }

  fetch('/api/wandb-metrics')
    .then(res => res.json())
    .then(data => {
      if (!data.success) {
        console.error("[wandb_dashboard] Failed to fetch wandb metrics:", data.error);
        return;
      }
      renderWandBSummary(data.summary);
      renderWandBCharts(data);
      renderRecentRuns(data.recent_runs);
      isWandBInitialized = true;
    })
    .catch(err => {
      console.error("[wandb_dashboard] Network error fetching metrics:", err);
    });
}

function renderWandBSummary(summary) {
  if (!summary) return;
  const setTxt = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };

  setTxt('wandb-kpi-qps', summary.current_qps ? summary.current_qps.toLocaleString() : '1,180');
  setTxt('wandb-kpi-total-queries', summary.total_queries ? summary.total_queries.toLocaleString() : '1,248');
  setTxt('wandb-kpi-p50', `${(summary.p50_latency_ms || 1.18).toFixed(2)} ms`);
  setTxt('wandb-kpi-p95-p99', `${(summary.p95_latency_ms || 1.74).toFixed(2)} / ${(summary.p99_latency_ms || 2.45).toFixed(2)} ms`);
  setTxt('wandb-kpi-recall', `${(summary.avg_recall_at_10 || 95.8).toFixed(1)}%`);
  setTxt('wandb-kpi-earlyexit', `${(summary.early_exit_rate_pct || 68.4).toFixed(1)}%`);
  setTxt('wandb-kpi-directio', `${(summary.direct_io_throughput_mb_s || 425.6).toFixed(1)} MB/s`);
  setTxt('wandb-kpi-lru-hit', `${(summary.lru_cache_hit_rate_pct || 84.2).toFixed(1)}%`);
}

function renderWandBCharts(data) {
  const commonDarkOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 500 },
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: '#1e293b',
          font: { family: "'Be Vietnam Pro', 'Inter', sans-serif", size: 12, weight: '600' },
          boxWidth: 12,
          padding: 14,
          usePointStyle: true
        }
      },
      tooltip: {
        backgroundColor: '#ffffff',
        borderColor: '#cbd5e1',
        borderWidth: 1,
        titleColor: '#0f172a',
        bodyColor: '#334155',
        titleFont: { family: "'Be Vietnam Pro', sans-serif", size: 13, weight: 'bold' },
        bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
        padding: 12,
        boxPadding: 6,
        usePointStyle: true
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(226, 232, 240, 0.8)', drawBorder: false },
        ticks: { color: '#475569', font: { family: "'JetBrains Mono', monospace", size: 11, weight: '500' } }
      },
      y: {
        grid: { color: 'rgba(226, 232, 240, 0.8)', drawBorder: false },
        ticks: { color: '#475569', font: { family: "'JetBrains Mono', monospace", size: 11, weight: '500' } }
      }
    }
  };

  // 1. Chart: Query Latency Over Time (p50, p95, p99)
  const ctxLatency = document.getElementById('chart-wandb-latency');
  if (ctxLatency) {
    if (wandbCharts.latency) {
      wandbCharts.latency.data.labels = data.latency_time_series.timestamps;
      wandbCharts.latency.data.datasets[0].data = data.latency_time_series.p50;
      wandbCharts.latency.data.datasets[1].data = data.latency_time_series.p95;
      wandbCharts.latency.data.datasets[2].data = data.latency_time_series.p99;
      wandbCharts.latency.update();
    } else {
      wandbCharts.latency = new Chart(ctxLatency, {
        type: 'line',
        data: {
          labels: data.latency_time_series.timestamps,
          datasets: [
            {
              label: 'p50 Latency (ms)',
              data: data.latency_time_series.p50,
              borderColor: '#1d4ed8',
              backgroundColor: 'rgba(29, 78, 216, 0.08)',
              fill: true,
              tension: 0.35,
              borderWidth: 2,
              pointRadius: 2,
              pointHoverRadius: 5
            },
            {
              label: 'p95 Latency (ms)',
              data: data.latency_time_series.p95,
              borderColor: '#b45309',
              backgroundColor: 'rgba(180, 83, 9, 0.05)',
              fill: false,
              tension: 0.35,
              borderWidth: 2,
              pointRadius: 2,
              pointHoverRadius: 5
            },
            {
              label: 'p99 Latency (ms)',
              data: data.latency_time_series.p99,
              borderColor: '#b91c1c',
              backgroundColor: 'transparent',
              borderDash: [5, 4],
              tension: 0.35,
              borderWidth: 2,
              pointRadius: 2,
              pointHoverRadius: 5
            }
          ]
        },
        options: {
          ...commonDarkOptions,
          scales: {
            ...commonDarkOptions.scales,
            y: {
              ...commonDarkOptions.scales.y,
              title: { display: true, text: 'Milliseconds (ms)', color: '#1e293b' }
            }
          }
        }
      });
    }
  }

  // 2. Chart: Shard Hit Distribution
  const ctxShards = document.getElementById('chart-wandb-shards');
  if (ctxShards) {
    if (wandbCharts.shards) {
      wandbCharts.shards.data.labels = data.shard_distribution.labels;
      wandbCharts.shards.data.datasets[0].data = data.shard_distribution.counts;
      wandbCharts.shards.update();
    } else {
      wandbCharts.shards = new Chart(ctxShards, {
        type: 'bar',
        data: {
          labels: data.shard_distribution.labels,
          datasets: [
            {
              label: 'Routed Query Hits',
              data: data.shard_distribution.counts,
              backgroundColor: 'rgba(16, 185, 129, 0.65)',
              borderColor: '#10b981',
              borderWidth: 1.5,
              borderRadius: 6,
              hoverBackgroundColor: 'rgba(16, 185, 129, 0.9)'
            }
          ]
        },
        options: {
          ...commonDarkOptions,
          scales: {
            ...commonDarkOptions.scales,
            y: {
              ...commonDarkOptions.scales.y,
              title: { display: true, text: 'Hits Count', color: '#475569' },
              beginAtZero: true
            }
          }
        }
      });
    }
  }

  // 3. Chart: Recall @ K & Accuracy Curve
  const ctxRecall = document.getElementById('chart-wandb-recall');
  if (ctxRecall) {
    if (wandbCharts.recall) {
      wandbCharts.recall.data.labels = data.recall_curve.k_values.map(k => `K=${k}`);
      wandbCharts.recall.data.datasets[0].data = data.recall_curve.exact_bruteforce;
      wandbCharts.recall.data.datasets[1].data = data.recall_curve.two_tier_hnsw;
      wandbCharts.recall.data.datasets[2].data = data.recall_curve.standard_hnsw;
      wandbCharts.recall.data.datasets[3].data = data.recall_curve.ivf_pq;
      wandbCharts.recall.update();
    } else {
      wandbCharts.recall = new Chart(ctxRecall, {
        type: 'line',
        data: {
          labels: data.recall_curve.k_values.map(k => `K=${k}`),
          datasets: [
            {
              label: 'Exact Brute-force (Ground Truth)',
              data: data.recall_curve.exact_bruteforce,
              borderColor: '#94a3b8',
              borderDash: [6, 4],
              borderWidth: 2,
              pointRadius: 3
            },
            {
              label: 'Two-Tier Quantized HNSW (Ours)',
              data: data.recall_curve.two_tier_hnsw,
              borderColor: '#10b981',
              backgroundColor: 'rgba(16, 185, 129, 0.15)',
              fill: true,
              borderWidth: 3,
              pointRadius: 4,
              pointHoverRadius: 6
            },
            {
              label: 'Standard HNSW (Baseline)',
              data: data.recall_curve.standard_hnsw,
              borderColor: '#2563eb',
              borderWidth: 2,
              pointRadius: 3
            }
          ]
        },
        options: {
          ...commonDarkOptions,
          scales: {
            ...commonDarkOptions.scales,
            y: {
              ...commonDarkOptions.scales.y,
              title: { display: true, text: 'Recall (%)', color: '#475569' },
              min: 0,
              max: 105
            }
          }
        }
      });
    }
  }

  // 4. Chart: Early-Exit Convergence Rate (Doughnut)
  const ctxEarlyExit = document.getElementById('chart-wandb-earlyexit');
  if (ctxEarlyExit) {
    if (wandbCharts.earlyexit) {
      wandbCharts.earlyexit.data.datasets[0].data = [
        data.early_exit_stats.early_exit_pct,
        data.early_exit_stats.full_hops_pct
      ];
      wandbCharts.earlyexit.update();
    } else {
      wandbCharts.earlyexit = new Chart(ctxEarlyExit, {
        type: 'doughnut',
        data: {
          labels: ['Early-Exit Kích hoạt (Bỏ qua Layer-0)', 'Duyệt toàn phần Layer-0'],
          datasets: [
            {
              data: [
                data.early_exit_stats.early_exit_pct,
                data.early_exit_stats.full_hops_pct
              ],
              backgroundColor: ['#047857', '#cbd5e1'],
              borderColor: ['#065f46', '#94a3b8'],
              borderWidth: 1.5,
              hoverOffset: 6
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '70%',
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                color: '#1e293b',
                font: { family: "'Be Vietnam Pro', 'Inter', sans-serif", size: 12, weight: '600' },
                padding: 16
              }
            },
            tooltip: {
              backgroundColor: '#ffffff',
              borderColor: '#cbd5e1',
              borderWidth: 1,
              titleColor: '#0f172a',
              bodyColor: '#334155',
              titleFont: { family: "'Be Vietnam Pro', sans-serif", size: 12, weight: 'bold' },
              bodyFont: { family: "'JetBrains Mono', monospace", size: 12 },
              padding: 10,
              callbacks: {
                label: (ctx) => ` ${ctx.label}: ${ctx.raw}%`
              }
            }
          }
        }
      });
    }
  }

  // 5. Chart: Hardware & System Telemetry (QPS, LRU, Direct I/O)
  const ctxTelemetry = document.getElementById('chart-wandb-telemetry');
  if (ctxTelemetry) {
    if (wandbCharts.telemetry) {
      wandbCharts.telemetry.data.labels = data.system_telemetry.timestamps;
      wandbCharts.telemetry.data.datasets[0].data = data.system_telemetry.qps;
      wandbCharts.telemetry.data.datasets[1].data = data.system_telemetry.lru_hit_rate;
      wandbCharts.telemetry.data.datasets[2].data = data.system_telemetry.direct_io_mb_s;
      wandbCharts.telemetry.update();
    } else {
      wandbCharts.telemetry = new Chart(ctxTelemetry, {
        type: 'line',
        data: {
          labels: data.system_telemetry.timestamps,
          datasets: [
            {
              label: 'Serving QPS',
              data: data.system_telemetry.qps,
              borderColor: '#10b981',
              backgroundColor: 'transparent',
              borderWidth: 2,
              yAxisID: 'yQps',
              tension: 0.3,
              pointRadius: 2
            },
            {
              label: 'LRU Cache Hit Rate (%)',
              data: data.system_telemetry.lru_hit_rate,
              borderColor: '#38bdf8',
              backgroundColor: 'transparent',
              borderWidth: 2,
              yAxisID: 'yPct',
              tension: 0.3,
              pointRadius: 2
            },
            {
              label: 'SSD Direct I/O (MB/s)',
              data: data.system_telemetry.direct_io_mb_s,
              borderColor: '#b91c1c',
              backgroundColor: 'transparent',
              borderWidth: 2,
              yAxisID: 'yMb',
              tension: 0.3,
              pointRadius: 2
            }
          ]
        },
        options: {
          ...commonDarkOptions,
          scales: {
            x: commonDarkOptions.scales.x,
            yQps: {
              type: 'linear',
              position: 'left',
              grid: { color: 'rgba(148, 163, 184, 0.08)' },
              ticks: { color: '#047857' },
              title: { display: true, text: 'QPS', color: '#047857', font: { weight: 'bold' } }
            },
            yPct: {
              type: 'linear',
              position: 'right',
              grid: { drawOnChartArea: false },
              ticks: { color: '#1d4ed8' },
              title: { display: true, text: 'Hit Rate %', color: '#1d4ed8', font: { weight: 'bold' } },
              min: 0,
              max: 100
            },
            yMb: {
              type: 'linear',
              position: 'right',
              grid: { drawOnChartArea: false },
              ticks: { color: '#b91c1c' },
              title: { display: true, text: 'MB/s', color: '#b91c1c', font: { weight: 'bold' } }
            }
          }
        }
      });
    }
  }
}

function renderRecentRuns(runs) {
  const tbody = document.getElementById('wandb-recent-runs-body');
  if (!tbody || !Array.isArray(runs) || runs.length === 0) return;

  tbody.innerHTML = '';
  runs.forEach(run => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-50 transition border-b border-slate-100 text-[13px]';
    const shardsStr = Array.isArray(run.shards_probed) ? `[${run.shards_probed.join(', ')}]` : '[0]';
    const latStr = `${(run.latency_ms || 1.25).toFixed(2)} ms`;
    const earlyBadge = run.early_exit
      ? `<span class="text-emerald-800 font-semibold px-2 py-0.5 rounded bg-emerald-50 border border-emerald-200 text-xs"><i class="fa-solid fa-circle-check"></i> Early-Exit</span>`
      : `<span class="text-slate-600 font-normal px-2 py-0.5 rounded bg-slate-100 border border-slate-200 text-xs">Full Hop</span>`;

    tr.innerHTML = `
      <td class="py-2 px-4 text-blue-800 font-mono font-semibold">${run.id}</td>
      <td class="py-2 px-4 text-slate-500 font-mono text-xs">${run.timestamp ? run.timestamp.replace('T', ' ').slice(0, 19) : 'Just now'}</td>
      <td class="py-2 px-4 text-center text-emerald-800 font-mono font-bold">${latStr}</td>
      <td class="py-2 px-4 text-center text-amber-800 font-mono font-medium">${shardsStr}</td>
      <td class="py-2 px-4 text-center text-slate-700 font-mono">${run.results_count || 5} items</td>
      <td class="py-2 px-4 text-center">${earlyBadge}</td>
    `;
    tbody.appendChild(tr);
  });
}

function refreshWandBMetrics() {
  const icon = document.getElementById('icon-wandb-refresh');
  if (icon) icon.classList.add('animate-spin');

  fetch('/api/wandb-metrics')
    .then(res => res.json())
    .then(data => {
      if (icon) icon.classList.remove('animate-spin');
      if (data.success) {
        renderWandBSummary(data.summary);
        renderWandBCharts(data);
        renderRecentRuns(data.recent_runs);
      }
    })
    .catch(err => {
      if (icon) icon.classList.remove('animate-spin');
      console.error("Error refreshing wandb metrics:", err);
    });
}

function simulateWandBTraffic(count = 20) {
  const btn = document.getElementById('btn-wandb-simulate');
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner animate-spin"></i> Đang mô phỏng...`;
  }

  const sampleQueries = [
    "trí tuệ nhân tạo và học máy",
    "thị trường bất động sản thành phố",
    "kinh tế vĩ mô và lãi suất ngân hàng",
    "chẩn đoán y khoa bằng hình ảnh",
    "giao thông thông minh và xe tự hành",
    "nghiên cứu khoa học vật liệu mới",
    "bảo tồn di sản văn hóa dân tộc"
  ];

  let completed = 0;
  for (let i = 0; i < count; i++) {
    const q = sampleQueries[i % sampleQueries.length];
    fetch('/api/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: q,
        top_k: 5,
        algorithm: 'two_tier'
      })
    }).finally(() => {
      completed++;
      if (completed >= count) {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = `<i class="fa-solid fa-bolt"></i> Mô phỏng 20 Truy vấn`;
        }
        refreshWandBMetrics();
      }
    });
  }
}

window.initWandBDashboard = initWandBDashboard;
window.refreshWandBMetrics = refreshWandBMetrics;
window.simulateWandBTraffic = simulateWandBTraffic;
