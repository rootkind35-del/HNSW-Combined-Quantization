/**
 * 3D Isometric Cyber-Pipeline Architecture Visualizer
 * Renders futuristic 3D hardware server pods with glowing energy reactors, live photon streams, and 3D Billboard Labels.
 */

class Pipeline3DModule {
  constructor(engine) {
    this.engine = engine;
    this.group = new THREE.Group();
    this.group.visible = false;
    this.engine.scene.add(this.group);

    this.pods = [];
    this.particleStreams = [];

    this.pipelineNodes = [
      {
        id: "pod_stream",
        name: "1. Hugging Face Stream",
        tier: "Input Layer",
        color: 0x38bdf8,
        pos: { x: -40, y: 0, z: -20 },
        desc: "Nạp luồng dữ liệu thời gian thực không chiếm RAM",
        stats: { speed: "900 docs/s", memory: "0.1 MB buffer" }
      },
      {
        id: "pod_prep",
        name: "2. Cleaner & MinHash Dedup",
        tier: "Data Prep Layer",
        color: 0xc084fc,
        pos: { x: -15, y: 0, z: -20 },
        desc: "Chuẩn hóa NFC tiếng Việt & lọc trùng luồng MinHash 128-perm",
        stats: { tokens: ">50k/s", dedup_ratio: "5.2% trùng lọc bỏ" }
      },
      {
        id: "pod_sq8",
        name: "3. Tier 1: SQ8 Quantizer",
        tier: "Tier 1 (RAM)",
        color: 0x10b981,
        pos: { x: 15, y: 0, z: -20 },
        desc: "Lượng tử hóa vector float32 sang uint8 (Tiết kiệm 75% RAM)",
        stats: { ram_reduction: "75%", dtype: "uint8 [10M, 384]" }
      },
      {
        id: "pod_early_exit",
        name: "4. Adaptive Early-Exit",
        tier: "Tier 1 Routing",
        color: 0x34d399,
        pos: { x: 40, y: 0, z: -20 },
        desc: "Tự động ngắt duyệt sớm khi khoảng cách hội tụ (tau=3)",
        stats: { hops_saved: "35% - 40%", p50_latency: "2.37 ms" }
      },
      {
        id: "pod_memmap",
        name: "5. Tier 2: SSD Memmap",
        tier: "Tier 2 (SSD Disk)",
        color: 0xf59e0b,
        pos: { x: 25, y: 0, z: 20 },
        desc: "Mảng nhị phân float32 nguyên bản trên đĩa SSD (Zero-RAM)",
        stats: { disk_size: "15.36 GB", active_ram: "0 MB" }
      },
      {
        id: "pod_reranker",
        name: "6. Tier 2: Exact Re-Rank",
        tier: "Tier 2 Engine",
        color: 0xfb923c,
        pos: { x: -5, y: 0, z: 20 },
        desc: "Đọc chọn lọc Top-K ứng viên tính lại khoảng cách float32 chính xác",
        stats: { recall: ">94%", rerank_pool: "30 candidates" }
      },
      {
        id: "pod_serving",
        name: "7. Serving Pod (365 QPS)",
        tier: "Serving Layer",
        color: 0xf43f5e,
        pos: { x: -35, y: 0, z: 20 },
        desc: "Trả về kết quả tìm kiếm ngữ nghĩa theo thời gian thực",
        stats: { qps: "365 QPS", unit_tests: "71/71 Passed" }
      }
    ];

    this.conduits = [
      { from: 0, to: 1 },
      { from: 1, to: 2 },
      { from: 2, to: 3 },
      { from: 3, to: 4 },
      { from: 4, to: 5 },
      { from: 5, to: 6 }
    ];

    this.buildPipelineScene();
  }

  buildPipelineScene() {
    // 1. Build Pods
    this.pipelineNodes.forEach((node) => {
      const podGroup = new THREE.Group();
      podGroup.position.set(node.pos.x, node.pos.y, node.pos.z);

      // Base Cyber Platform
      const baseGeo = new THREE.CylinderGeometry(5.5, 6.5, 1.2, 8);
      const baseMat = new THREE.MeshStandardMaterial({
        color: 0x0f172a,
        metalness: 0.8,
        roughness: 0.3
      });
      const baseMesh = new THREE.Mesh(baseGeo, baseMat);
      podGroup.add(baseMesh);

      // Neon Ring on Base
      const ringGeo = new THREE.RingGeometry(5.6, 6.2, 16);
      const ringMat = new THREE.MeshBasicMaterial({ color: node.color, side: THREE.DoubleSide });
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = -Math.PI / 2;
      ringMesh.position.y = 0.65;
      podGroup.add(ringMesh);

      // Glass Pod Chamber
      const chamberGeo = new THREE.BoxGeometry(6, 8, 6);
      const chamberMat = new THREE.MeshPhysicalMaterial({
        color: node.color,
        transparent: true,
        opacity: 0.45,
        roughness: 0.1,
        metalness: 0.2,
        transmission: 0.8
      });
      const chamber = new THREE.Mesh(chamberGeo, chamberMat);
      chamber.position.y = 4.6;
      podGroup.add(chamber);

      // Chamber Edges
      const edgesGeo = new THREE.EdgesGeometry(chamberGeo);
      const edgesMat = new THREE.LineBasicMaterial({ color: node.color, transparent: true, opacity: 0.9 });
      const edges = new THREE.LineSegments(edgesGeo, edgesMat);
      edges.position.y = 4.6;
      podGroup.add(edges);

      // Floating Core Reactor inside Chamber
      const coreGeo = new THREE.OctahedronGeometry(2.2, 0);
      const coreMat = new THREE.MeshStandardMaterial({
        color: node.color,
        emissive: node.color,
        emissiveIntensity: 0.95,
        roughness: 0.2
      });
      const coreMesh = new THREE.Mesh(coreGeo, coreMat);
      coreMesh.position.y = 4.6;
      podGroup.add(coreMesh);

      // 3D Billboard Label Floating Above Pod
      const hexStr = '#' + new THREE.Color(node.color).getHexString();
      const podSprite = this.engine.create3DTextSprite(node.name, 'rgba(10, 18, 36, 0.95)', hexStr, 26);
      podSprite.position.set(0, 10.8, 0);
      podSprite.scale.set(24, 6, 1);
      podGroup.add(podSprite);

      podGroup.userData = { nodeData: node, coreMesh: coreMesh };
      this.group.add(podGroup);
      this.pods.push(podGroup);
    });

    // 2. Build Conduits and Particle Systems
    this.conduits.forEach(c => {
      const p1 = this.pipelineNodes[c.from].pos;
      const p2 = this.pipelineNodes[c.to].pos;

      const midY = 6;
      const curve = new THREE.CatmullRomCurve3([
        new THREE.Vector3(p1.x, 3, p1.z),
        new THREE.Vector3((p1.x + p2.x) / 2, midY, (p1.z + p2.z) / 2),
        new THREE.Vector3(p2.x, 3, p2.z)
      ]);

      // Glowing Conduit Tube
      const tubeGeo = new THREE.TubeGeometry(curve, 32, 0.35, 8, false);
      const tubeMat = new THREE.MeshBasicMaterial({
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.55
      });
      const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
      this.group.add(tubeMesh);

      // Flowing Energy Photons
      const particleCount = 18;
      const pGeo = new THREE.BufferGeometry();
      const pPos = new Float32Array(particleCount * 3);
      for (let i = 0; i < particleCount; i++) {
        const pt = curve.getPoint(i / particleCount);
        pPos[i * 3] = pt.x;
        pPos[i * 3 + 1] = pt.y;
        pPos[i * 3 + 2] = pt.z;
      }
      pGeo.setAttribute('position', new THREE.BufferAttribute(pPos, 3));

      const pMat = new THREE.PointsMaterial({
        color: 0x38bdf8,
        size: 2.2,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending
      });

      const pSystem = new THREE.Points(pGeo, pMat);
      pSystem.userData = { curve: curve, offsets: Array.from({ length: particleCount }, (_, i) => i / particleCount) };
      this.group.add(pSystem);
      this.particleStreams.push(pSystem);
    });
  }

  handleMouseMove(raycaster) {
    const meshes = this.pods.flatMap(p => [p.children[0], p.children[2], p.children[4]]);
    const intersects = raycaster.intersectObjects(meshes);
    const tooltipEl = document.getElementById('hud-tooltip-3d');

    if (intersects.length > 0) {
      const podGroup = intersects[0].object.parent;
      const node = podGroup.userData.nodeData;
      document.body.style.cursor = 'pointer';

      if (tooltipEl) {
        tooltipEl.style.display = 'block';
        tooltipEl.style.left = `${(this.engine.mouse.x + 1) * 0.5 * this.engine.container.clientWidth + 15}px`;
        tooltipEl.style.top = `${(-this.engine.mouse.y + 1) * 0.5 * this.engine.container.clientHeight - 10}px`;
        tooltipEl.innerHTML = `
          <div class="text-[17px] font-bold text-white leading-snug">${node.name}</div>
          <div class="text-[14px] text-sky-400 font-semibold mt-1">${node.tier}</div>
          <div class="text-[13px] text-slate-300 mt-1">${node.desc}</div>
        `;
      }
    } else {
      document.body.style.cursor = 'default';
      if (tooltipEl) tooltipEl.style.display = 'none';
    }
  }

  handleClick(raycaster) {
    const meshes = this.pods.flatMap(p => [p.children[0], p.children[2], p.children[4]]);
    const intersects = raycaster.intersectObjects(meshes);
    if (intersects.length > 0) {
      const podGroup = intersects[0].object.parent;
      const node = podGroup.userData.nodeData;
      const infoPanel = document.getElementById('hud-detail-panel');
      if (infoPanel) {
        infoPanel.classList.remove('hidden');
        document.getElementById('hud-doc-title').textContent = node.name;
        document.getElementById('hud-doc-category').textContent = node.tier;
        document.getElementById('hud-doc-preview').textContent = node.desc;
        document.getElementById('hud-doc-coords').textContent = `Pos: [${node.pos.x}, ${node.pos.y}, ${node.pos.z}]`;
        document.getElementById('hud-doc-tokens').textContent = JSON.stringify(node.stats);
      }
    }
  }

  setVisible(visible) {
    this.group.visible = visible;
  }

  update(delta) {
    this.pods.forEach(p => {
      const core = p.userData.coreMesh;
      if (core) {
        core.rotation.y += delta * 1.5;
        core.rotation.x += delta * 0.8;
      }
    });

    this.particleStreams.forEach(ps => {
      const curve = ps.userData.curve;
      const offsets = ps.userData.offsets;
      const posAttr = ps.geometry.attributes.position;

      for (let i = 0; i < offsets.length; i++) {
        offsets[i] = (offsets[i] + delta * 0.4) % 1.0;
        const pt = curve.getPoint(offsets[i]);
        posAttr.setXYZ(i, pt.x, pt.y, pt.z);
      }
      posAttr.needsUpdate = true;
    });
  }
}

window.Pipeline3DModule = Pipeline3DModule;
