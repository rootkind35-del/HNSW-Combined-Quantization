/**
 * Architecture Flow Graph Visualizer
 * Renders an interactive, animated SVG representing the physical data and algorithmic flow.
 * Uses robust HTML foreignObject cards to guarantee text NEVER overflows outside node frames.
 */

let currentArchitectureData = null;
let selectedNodeId = "node_early_exit";

function initArchitectureGraph() {
  fetch('/api/architecture')
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        currentArchitectureData = data.architecture;
        renderSvgGraph(currentArchitectureData);
        // Default inspection to early-exit node
        inspectNode(selectedNodeId);
      }
    })
    .catch(err => console.error("Could not load architecture graph:", err));
}

function renderSvgGraph(arch) {
  const svg = document.getElementById('architecture-svg');
  if (!svg) return;
  svg.innerHTML = '';

  svg.setAttribute('viewBox', `0 0 940 615`);

  // Define SVG Marker for Arrows
  const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
  defs.innerHTML = `
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#64748b" />
    </marker>
    <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#38bdf8" />
    </marker>
  `;
  svg.appendChild(defs);

  // Enlarged node dimensions (W: 275, H: 88) ensuring text never escapes
  const nodePositions = {
    "node_hf_stream":    { x: 25,  y: 25,  w: 275, h: 88, color: "#38bdf8", icon: "fa-satellite-dish" },
    "node_cleaner":      { x: 330, y: 25,  w: 275, h: 88, color: "#c084fc", icon: "fa-filter" },
    "node_tokenizer":    { x: 635, y: 25,  w: 275, h: 88, color: "#c084fc", icon: "fa-spell-check" },
    "node_dedup":        { x: 635, y: 150, w: 275, h: 88, color: "#c084fc", icon: "fa-clone" },
    "node_sq8":          { x: 330, y: 150, w: 275, h: 88, color: "#10b981", icon: "fa-compress" },
    "node_early_exit":   { x: 25,  y: 275, w: 275, h: 88, color: "#34d399", icon: "fa-stopwatch-20" },
    "node_beam_search":  { x: 330, y: 275, w: 275, h: 88, color: "#10b981", icon: "fa-network-wired" },
    "node_memmap":       { x: 635, y: 275, w: 275, h: 88, color: "#f59e0b", icon: "fa-hard-drive" },
    "node_reranker":     { x: 480, y: 405, w: 285, h: 88, color: "#fb923c", icon: "fa-arrow-down-1-9" },
    "node_serving":      { x: 480, y: 515, w: 285, h: 76, color: "#f43f5e", icon: "fa-check-double" }
  };

  // Group for connections (lines and animated dashes)
  const gEdges = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  gEdges.setAttribute('id', 'graph-edges');

  arch.connections.forEach(conn => {
    const fromP = nodePositions[conn.from];
    const toP = nodePositions[conn.to];
    if (!fromP || !toP) return;

    const x1 = fromP.x + fromP.w / 2;
    const y1 = fromP.y + fromP.h / 2;
    const x2 = toP.x + toP.w / 2;
    const y2 = toP.y + toP.h / 2;

    // Calculate boundary intersection
    let startX = x1, startY = y1, endX = x2, endY = y2;
    if (Math.abs(x2 - x1) > Math.abs(y2 - y1)) {
      startX = x2 > x1 ? fromP.x + fromP.w : fromP.x;
      endX = x2 > x1 ? toP.x : toP.x + toP.w;
    } else {
      startY = y2 > y1 ? fromP.y + fromP.h : fromP.y;
      endY = y2 > y1 ? toP.y : toP.y + toP.h;
    }

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const midY = (startY + endY) / 2;
    const d = `M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`;

    path.setAttribute('d', d);
    path.setAttribute('fill', 'none');
    path.setAttribute('stroke', '#38bdf8');
    path.setAttribute('stroke-width', '2.5');
    path.setAttribute('stroke-opacity', '0.85');
    path.setAttribute('class', 'flow-edge');
    path.setAttribute('marker-end', 'url(#arrow-active)');
    gEdges.appendChild(path);
  });
  svg.appendChild(gEdges);

  // Group for Nodes
  const gNodes = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  gNodes.setAttribute('id', 'graph-nodes');

  arch.layers.forEach(layer => {
    layer.nodes.forEach(node => {
      const pos = nodePositions[node.id];
      if (!pos) return;

      const isSelected = (node.id === selectedNodeId);

      const fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
      fo.setAttribute('x', pos.x);
      fo.setAttribute('y', pos.y);
      fo.setAttribute('width', pos.w);
      fo.setAttribute('height', pos.h);
      fo.setAttribute('class', 'cursor-pointer select-none');

      fo.innerHTML = `
        <div xmlns="http://www.w3.org/1999/xhtml" class="w-full h-full rounded-2xl p-3.5 flex flex-col justify-between transition-all duration-200 border-2 ${
          isSelected ? 'bg-slate-800/95 ring-2 ring-sky-400 shadow-xl' : 'bg-slate-900/95 hover:bg-slate-850 shadow-md'
        }" style="border-color: ${isSelected ? '#38bdf8' : pos.color}; box-shadow: 0 8px 20px rgba(0,0,0,0.55);">
          <div class="flex items-center justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <i class="fa-solid ${pos.icon} text-[15px] shrink-0" style="color: ${pos.color}"></i>
              <h4 class="font-bold text-[14px] text-white truncate leading-tight">${node.label}</h4>
            </div>
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0 ${isSelected ? 'animate-ping' : ''}"></span>
          </div>
          <p class="text-[12px] text-slate-300 line-clamp-2 leading-snug mt-1">${node.sublabel}</p>
        </div>
      `;

      fo.onclick = () => inspectNode(node.id);
      gNodes.appendChild(fo);
    });
  });

  svg.appendChild(gNodes);
}

function inspectNode(nodeId) {
  selectedNodeId = nodeId;
  if (!currentArchitectureData) return;

  let foundNode = null;
  for (const layer of currentArchitectureData.layers) {
    for (const n of layer.nodes) {
      if (n.id === nodeId) {
        foundNode = n;
        break;
      }
    }
    if (foundNode) break;
  }
  if (!foundNode) return;

  document.getElementById('inspect-title').textContent = foundNode.label;
  document.getElementById('inspect-sublabel').textContent = foundNode.sublabel;
  document.getElementById('inspect-status').textContent = foundNode.status.toUpperCase();

  const paramsContainer = document.getElementById('inspect-params');
  paramsContainer.innerHTML = '';
  Object.entries(foundNode.params || {}).forEach(([k, v]) => {
    const item = document.createElement('div');
    item.className = "flex justify-between";
    item.innerHTML = `<span class="text-slate-400">${k}:</span> <span class="text-slate-100 font-semibold">${v}</span>`;
    paramsContainer.appendChild(item);
  });

  const metricsContainer = document.getElementById('inspect-metrics');
  metricsContainer.innerHTML = '';
  Object.entries(foundNode.metrics || {}).forEach(([k, v]) => {
    const item = document.createElement('div');
    item.className = "flex justify-between";
    item.innerHTML = `<span class="text-slate-400 capitalize">${k.replace(/_/g, ' ')}:</span> <span class="text-emerald-400 font-semibold">${v}</span>`;
    metricsContainer.appendChild(item);
  });

  // Re-render SVG to update selected border highlight
  renderSvgGraph(currentArchitectureData);
}

document.addEventListener('DOMContentLoaded', initArchitectureGraph);
