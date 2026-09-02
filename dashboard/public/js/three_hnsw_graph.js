/**
 * 3D Hierarchical Navigable Small World (HNSW) Multi-Layer Graph Visualizer
 * Brightened Nodes, High-Contrast Glass Planes, 3D Layer Billboards, Shockwave Text,
 * and Interactive Multi-Hop Photon Routing Simulation.
 */

class HnswGraphModule {
  constructor(engine) {
    this.engine = engine;
    this.group = new THREE.Group();
    this.group.visible = false;
    this.engine.scene.add(this.group);

    this.topology = null;
    this.nodesMap = new Map();
    this.nodeMeshes = [];
    this.routingProbe = null;
    this.routingLaserPath = null;
    this.isSimulating = false;
    this.simulationStep = 0;
    this.simulationPath = [];

    this.loadTopology();
  }

  loadTopology() {
    fetch('/api/hnsw-topology-3d')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.topology) {
          this.topology = data.topology;
          this.buildHnswScene();
          console.log('[HnswGraphModule] HNSW 3D Multi-Layer Graph loaded with high detail.');
        }
      })
      .catch(err => console.error('[HnswGraphModule] Error loading HNSW topology:', err));
  }

  buildHnswScene() {
    if (!this.topology || !this.topology.layers) return;

    // Clear previous elements if re-building
    while (this.group.children.length > 0) {
      this.group.remove(this.group.children[0]);
    }
    this.nodesMap.clear();
    this.nodeMeshes = [];
    this.routingProbe = null;
    this.routingLaserPath = null;

    // 1. Build 3 Layered Glass Planes with 3D Billboard Titles
    this.topology.layers.forEach(layer => {
      this.createGlassPlane(layer.y, layer.name, layer.level);
    });

    // 2. Build Bright Glowing Nodes
    const sphereGeo = new THREE.SphereGeometry(1.6, 20, 20);

    const layerConfig = {
      2: { color: 0xf59e0b, emissive: 0xd97706, label: "TẦNG 2" },
      1: { color: 0xc084fc, emissive: 0x9333ea, label: "TẦNG 1" },
      0: { color: 0x38bdf8, emissive: 0x0284c7, label: "TẦNG 0" }
    };

    this.topology.layers.forEach(layer => {
      const cfg = layerConfig[layer.level] || layerConfig[0];
      const mat = new THREE.MeshStandardMaterial({
        color: cfg.color,
        emissive: cfg.emissive,
        emissiveIntensity: 0.85,
        roughness: 0.15,
        metalness: 0.8
      });

      layer.nodes.forEach(node => {
        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.position.set(node.x, node.y, node.z);
        mesh.userData = { nodeData: node };

        // Make entry point prominent
        if (node.id === this.topology.entry_point_id) {
          mesh.scale.set(1.9, 1.9, 1.9);

          const entryHaloGeo = new THREE.RingGeometry(3.0, 3.8, 24);
          const entryHaloMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, side: THREE.DoubleSide });
          const entryHalo = new THREE.Mesh(entryHaloGeo, entryHaloMat);
          entryHalo.rotation.x = Math.PI / 2;
          mesh.add(entryHalo);

          // Billboard for Entry Point
          const epSprite = this.engine.create3DTextSprite("★ HNSW ENTRY POINT", "rgba(245, 158, 11, 0.95)", "#ffffff", 34);
          epSprite.position.set(0, 4.5, 0);
          epSprite.scale.set(18, 4.5, 1);
          mesh.add(epSprite);
        }

        this.group.add(mesh);
        this.nodeMeshes.push(mesh);
        this.nodesMap.set(node.id, mesh);
      });
    });

    // 3. Build Intra-layer Edges (Bright Glowing Links)
    if (this.topology.intra_edges) {
      this.topology.intra_edges.forEach(edge => {
        const fromMesh = this.nodesMap.get(edge.from);
        const toMesh = this.nodesMap.get(edge.to);
        if (!fromMesh || !toMesh) return;

        const points = [fromMesh.position, toMesh.position];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const lineMat = new THREE.LineBasicMaterial({
          color: edge.layer === 2 ? 0xfbbf24 : edge.layer === 1 ? 0xc084fc : 0x38bdf8,
          transparent: true,
          opacity: edge.layer === 0 ? 0.45 : 0.85
        });
        const line = new THREE.Line(lineGeo, lineMat);
        this.group.add(line);
      });
    }

    // 4. Build Inter-layer Links (Vertical Conduits)
    if (this.topology.inter_links) {
      this.topology.inter_links.forEach(link => {
        const fromMesh = this.nodesMap.get(link.from);
        const toMesh = this.nodesMap.get(link.to);
        if (!fromMesh || !toMesh) return;

        const points = [fromMesh.position, toMesh.position];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
        const lineMat = new THREE.LineDashedMaterial({
          color: 0x34d399,
          dashSize: 2.0,
          gapSize: 1.2,
          transparent: true,
          opacity: 0.9
        });
        const line = new THREE.Line(lineGeo, lineMat);
        line.computeLineDistances();
        this.group.add(line);
      });
    }
  }

  createGlassPlane(yPos, name, level) {
    const planeGeo = new THREE.PlaneGeometry(95, 95);
    const planeMat = new THREE.MeshPhysicalMaterial({
      color: level === 2 ? 0x1e293b : level === 1 ? 0x0f172a : 0x070d1e,
      transparent: true,
      opacity: 0.45,
      roughness: 0.1,
      metalness: 0.2,
      transmission: 0.7,
      ior: 1.5,
      side: THREE.DoubleSide
    });

    const plane = new THREE.Mesh(planeGeo, planeMat);
    plane.rotation.x = -Math.PI / 2;
    plane.position.y = yPos;
    this.group.add(plane);

    // Glowing Plane Border Wire
    const edges = new THREE.EdgesGeometry(planeGeo);
    const borderMat = new THREE.LineBasicMaterial({
      color: level === 2 ? 0xf59e0b : level === 1 ? 0xc084fc : 0x38bdf8,
      transparent: true,
      opacity: 0.9
    });
    const border = new THREE.LineSegments(edges, borderMat);
    border.rotation.x = -Math.PI / 2;
    border.position.y = yPos;
    this.group.add(border);

    // Add 3D Billboard Banner at the corner of each layer
    const labelTitle = level === 2 ? "TẦNG 2: ĐIỀU HƯỚNG TỐC ĐỘ CAO (FAST SKIP LINKS)" :
                       level === 1 ? "TẦNG 1: ĐIỀU HƯỚNG TRUNG GIAN (MID CLUSTERS)" :
                                     "TẦNG 0: ĐỒ THỊ DÀY ĐẶC (DENSE BASE GRAPH)";
    const labelColor = level === 2 ? "#f59e0b" : level === 1 ? "#c084fc" : "#38bdf8";
    const billboard = this.engine.create3DTextSprite(labelTitle, "rgba(10, 18, 36, 0.95)", labelColor, 26);
    billboard.scale.set(38, 7.5, 1);
    billboard.position.set(-25, yPos + 4.5, 45);
    this.group.add(billboard);
  }

  handleMouseMove(raycaster) {
    const intersects = raycaster.intersectObjects(this.nodeMeshes);
    const tooltipEl = document.getElementById('hud-tooltip-3d');

    if (intersects.length > 0) {
      const node = intersects[0].object.userData.nodeData;
      document.body.style.cursor = 'pointer';

      if (tooltipEl) {
        tooltipEl.style.display = 'block';
        tooltipEl.style.left = `${(this.engine.mouse.x + 1) * 0.5 * this.engine.container.clientWidth + 15}px`;
        tooltipEl.style.top = `${(-this.engine.mouse.y + 1) * 0.5 * this.engine.container.clientHeight - 10}px`;
        tooltipEl.innerHTML = `
          <div class="text-[16px] font-bold text-white leading-snug">${node.title.slice(0, 70)}...</div>
          <div class="text-[14px] text-amber-400 font-semibold mt-1 flex items-center gap-1.5">
            <i class="fa-solid fa-layer-group"></i> HNSW Tầng ${node.layer} (${node.layer === 2 ? 'Top Tier' : node.layer === 1 ? 'Mid Tier' : 'Base Tier'})
          </div>
          <div class="text-[13px] text-slate-300 mt-1">Chuyên mục: <strong class="text-sky-300">${node.category}</strong></div>
        `;
      }
    } else {
      document.body.style.cursor = 'default';
      if (tooltipEl) tooltipEl.style.display = 'none';
    }
  }

  handleClick(raycaster) {
    const intersects = raycaster.intersectObjects(this.nodeMeshes);
    if (intersects.length > 0) {
      const node = intersects[0].object.userData.nodeData;
      const infoPanel = document.getElementById('hud-detail-panel');
      if (infoPanel) {
        infoPanel.classList.remove('hidden');
        document.getElementById('hud-doc-title').textContent = `[HNSW Tầng ${node.layer}] ${node.title}`;
        document.getElementById('hud-doc-category').textContent = `Tầng ${node.layer} • ${node.category}`;
        document.getElementById('hud-doc-preview').textContent = `Node ID: ${node.id} | Toạ độ 3D: [${node.x}, ${node.y}, ${node.z}]`;
        document.getElementById('hud-doc-coords').textContent = `Y-Level: ${node.y} | Orig Index: ${node.orig_index}`;
        document.getElementById('hud-doc-tokens').textContent = `Connected in Layer ${node.layer}`;
      }
    }
  }

  startRoutingSimulation(useEarlyExit = true) {
    if (!this.topology || !this.topology.layers) return;

    // Reset previous simulation state cleanly
    if (this.routingProbe && typeof gsap !== 'undefined') {
      gsap.killTweensOf(this.routingProbe.position);
    }
    this.isSimulating = true;

    // Ensure group is visible
    this.setVisible(true);

    const l2Nodes = this.topology.layers.find(l => l.level === 2)?.nodes || [];
    const l1Nodes = this.topology.layers.find(l => l.level === 1)?.nodes || [];
    const l0Nodes = this.topology.layers.find(l => l.level === 0)?.nodes || [];

    if (l2Nodes.length === 0 || l1Nodes.length === 0 || l0Nodes.length === 0) return;

    // Multi-hop path: Layer 2 -> Layer 1 -> Layer 0
    this.simulationPath = [
      l2Nodes[0],
      l2Nodes[Math.min(1, l2Nodes.length - 1)],
      l1Nodes[0],
      l1Nodes[Math.min(2, l1Nodes.length - 1)],
      l0Nodes[0],
      l0Nodes[Math.min(3, l0Nodes.length - 1)]
    ];

    if (useEarlyExit) {
      this.simulationPath = this.simulationPath.slice(0, 4);
    }

    // 1. Create Glowing Routing Photon Probe
    if (!this.routingProbe) {
      const probeGeo = new THREE.SphereGeometry(2.4, 24, 24);
      const probeMat = new THREE.MeshStandardMaterial({
        color: 0x10b981,
        emissive: 0x34d399,
        emissiveIntensity: 1.0,
        roughness: 0.1
      });
      this.routingProbe = new THREE.Mesh(probeGeo, probeMat);

      const haloGeo = new THREE.RingGeometry(3.0, 4.2, 32);
      const haloMat = new THREE.MeshBasicMaterial({ color: 0x34d399, side: THREE.DoubleSide, transparent: true, opacity: 0.95 });
      const halo = new THREE.Mesh(haloGeo, haloMat);
      halo.rotation.x = Math.PI / 2;
      this.routingProbe.add(halo);

      this.group.add(this.routingProbe);
    }

    // 2. Draw Dynamic Laser Trajectory
    if (this.routingLaserPath) {
      this.group.remove(this.routingLaserPath);
    }
    const pathPoints = this.simulationPath.map(n => new THREE.Vector3(n.x, n.y, n.z));
    const pathGeo = new THREE.BufferGeometry().setFromPoints(pathPoints);
    const pathMat = new THREE.LineBasicMaterial({ color: 0x10b981, linewidth: 3, transparent: true, opacity: 0.85 });
    this.routingLaserPath = new THREE.Line(pathGeo, pathMat);
    this.group.add(this.routingLaserPath);

    this.routingProbe.visible = true;
    this.routingProbe.position.set(this.simulationPath[0].x, this.simulationPath[0].y, this.simulationPath[0].z);

    this.stepRoutingAnimation(0, useEarlyExit);
  }

  stepRoutingAnimation(stepIndex, useEarlyExit) {
    if (stepIndex >= this.simulationPath.length) {
      this.isSimulating = false;
      if (useEarlyExit) {
        this.triggerEarlyExitEffect(this.simulationPath[this.simulationPath.length - 1]);
      }
      return;
    }

    const targetNode = this.simulationPath[stepIndex];

    if (typeof gsap !== 'undefined') {
      gsap.to(this.routingProbe.position, {
        x: targetNode.x,
        y: targetNode.y,
        z: targetNode.z,
        duration: 0.7,
        ease: 'power2.inOut',
        onComplete: () => {
          this.stepRoutingAnimation(stepIndex + 1, useEarlyExit);
        }
      });
    } else {
      this.routingProbe.position.set(targetNode.x, targetNode.y, targetNode.z);
      setTimeout(() => this.stepRoutingAnimation(stepIndex + 1, useEarlyExit), 700);
    }
  }

  triggerEarlyExitEffect(node) {
    const shockwaveGeo = new THREE.RingGeometry(1, 2.2, 32);
    const shockwaveMat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 1
    });
    const shockwave = new THREE.Mesh(shockwaveGeo, shockwaveMat);
    shockwave.position.set(node.x, node.y, node.z);
    shockwave.rotation.x = Math.PI / 2;
    this.group.add(shockwave);

    // Add 3D Holographic Label at the shockwave convergence point
    const exitSprite = this.engine.create3DTextSprite("⚡ EARLY-EXIT CONVERGENCE (τ=3)", "rgba(16, 185, 129, 0.95)", "#ffffff", 28);
    exitSprite.scale.set(24, 6, 1);
    exitSprite.position.set(node.x, node.y + 4.5, node.z);
    this.group.add(exitSprite);

    if (typeof gsap !== 'undefined') {
      gsap.to(shockwave.scale, { x: 14, y: 14, z: 1, duration: 1.5, ease: 'power2.out' });
      gsap.to(shockwaveMat, { opacity: 0, duration: 1.5, ease: 'power2.out', onComplete: () => this.group.remove(shockwave) });
      gsap.to(exitSprite.material, { opacity: 0, delay: 2.2, duration: 1.0, onComplete: () => this.group.remove(exitSprite) });
    } else {
      setTimeout(() => {
        this.group.remove(shockwave);
        this.group.remove(exitSprite);
      }, 2500);
    }

    const hudBanner = document.getElementById('hud-early-exit-banner');
    if (hudBanner) {
      hudBanner.classList.remove('hidden');
      setTimeout(() => hudBanner.classList.add('hidden'), 3500);
    }
  }

  setVisible(visible) {
    this.group.visible = visible;
  }

  update(delta) {
    if (this.routingProbe && this.routingProbe.visible) {
      const halo = this.routingProbe.children[0];
      if (halo) halo.rotation.z += delta * 2.0;
    }
  }
}

window.HnswGraphModule = HnswGraphModule;
