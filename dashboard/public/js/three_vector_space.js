/**
 * 3D Vector Space & Point Cloud Visualizer
 * High-End Crystalline Graph Nodes (GitNexus Graph Style):
 * - Sharp solid spherical beads with 3D specular highlight sparkle
 * - Zero muddy/fuzzy blur, pure category color vibrancy
 * - Depth-tested crisp outlines & interactive dual-ring target reticle.
 */

class VectorSpaceModule {
  constructor(engine) {
    this.engine = engine;
    this.group = new THREE.Group();
    this.engine.scene.add(this.group);

    this.vectorsData = [];
    this.pointCloud = null;
    this.interactiveSpheres = [];
    this.laserLines = [];
    this.queryBeacon = null;
    this.quantGrid = null;
    this.lastQueryPos = null;
    this.hoverReticle = null;
    this.activeHoverIndex = -1;

    // High-Vibrancy Crisp Palette per category
    this.categoryColors = {
      "Kinh doanh & Tài chính": 0x38bdf8, // Electric Sky Blue
      "Khoa học & Công nghệ": 0xa855f7, // Vivid Purple
      "Giáo dục": 0xfb923c,             // Bright Amber/Orange
      "Y tế & Sức khỏe": 0x10b981,       // Emerald Green
      "Giao thông & Xây dựng": 0xfacc15, // Golden Yellow
      "Văn hóa & Đời sống": 0xf43f5e    // Vibrant Rose/Ruby
    };

    this.initHoverReticle();
    this.initFocusMarker();
    this.loadVectorsData();
  }

  initFocusMarker() {
    this.focusMarker = new THREE.Group();
    this.focusMarker.visible = false;

    // Vòng phát sáng trung tâm
    const ring1Geo = new THREE.RingGeometry(2.2, 2.7, 32);
    const ring1Mat = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.95
    });
    this.focusRingInner = new THREE.Mesh(ring1Geo, ring1Mat);
    this.focusMarker.add(this.focusRingInner);

    // Vòng ngoài màu ngọc lục bảo xoay nhịp nhàng
    const ring2Geo = new THREE.RingGeometry(3.6, 4.2, 32);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: 0x10b981,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.85
    });
    this.focusRingOuter = new THREE.Mesh(ring2Geo, ring2Mat);
    this.focusMarker.add(this.focusRingOuter);

    // 4 vạch tiêu cự crosshair
    const crossMat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide });
    const hBar = new THREE.PlaneGeometry(1.6, 0.35);
    const vBar = new THREE.PlaneGeometry(0.35, 1.6);

    const barTop = new THREE.Mesh(vBar, crossMat);
    barTop.position.set(0, 4.8, 0);
    this.focusMarker.add(barTop);

    const barBottom = new THREE.Mesh(vBar, crossMat);
    barBottom.position.set(0, -4.8, 0);
    this.focusMarker.add(barBottom);

    const barLeft = new THREE.Mesh(hBar, crossMat);
    barLeft.position.set(-4.8, 0, 0);
    this.focusMarker.add(barLeft);

    const barRight = new THREE.Mesh(hBar, crossMat);
    barRight.position.set(4.8, 0, 0);
    this.focusMarker.add(barRight);

    this.group.add(this.focusMarker);
  }

  highlightNode(x, y, z, label = "") {
    if (!this.focusMarker) return;
    this.focusMarker.position.set(x, y, z);
    this.focusMarker.visible = true;
    this.focusAnimTimer = 0;
  }

  initHoverReticle() {
    this.hoverReticle = new THREE.Group();
    this.hoverReticle.visible = false;

    // Inner sharp ring
    const ring1Geo = new THREE.RingGeometry(1.8, 2.2, 32);
    const ring1Mat = new THREE.MeshBasicMaterial({ color: 0x38bdf8, side: THREE.DoubleSide, transparent: true, opacity: 0.95 });
    const ring1 = new THREE.Mesh(ring1Geo, ring1Mat);
    this.hoverReticle.add(ring1);

    // Outer dashed/accent ring
    const ring2Geo = new THREE.RingGeometry(2.8, 3.1, 32);
    const ring2Mat = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide, transparent: true, opacity: 0.6 });
    const ring2 = new THREE.Mesh(ring2Geo, ring2Mat);
    this.hoverReticle.add(ring2);

    this.group.add(this.hoverReticle);
  }

  loadVectorsData() {
    fetch('/api/vectors-3d')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.vectors) {
          this.vectorsData = data.vectors;
          this.buildPointCloud();
          this.buildQuantizationGrid();
          console.log(`[VectorSpaceModule] Loaded and rendered ${data.vectors.length} sharp crystalline vector points.`);
        }
      })
      .catch(err => console.error('[VectorSpaceModule] Error loading 3D vectors:', err));
  }

  // Generates a GitNexus-style Crisp 3D Glossy Node Texture
  createCrispNodeTexture() {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Clear background
    ctx.clearRect(0, 0, 128, 128);

    // 1. Subtle Outer Glow Rim (Thin & Controlled)
    const glowGrad = ctx.createRadialGradient(64, 64, 38, 64, 64, 56);
    glowGrad.addColorStop(0, 'rgba(255, 255, 255, 0.4)');
    glowGrad.addColorStop(0.6, 'rgba(255, 255, 255, 0.15)');
    glowGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(64, 64, 56, 0, Math.PI * 2);
    ctx.fill();

    // 2. Solid Core Sphere with 3D Spherical Shading
    const sphereGrad = ctx.createRadialGradient(50, 50, 4, 64, 64, 40);
    sphereGrad.addColorStop(0, 'rgba(255, 255, 255, 1.0)');     // Bright top-left light
    sphereGrad.addColorStop(0.35, 'rgba(240, 240, 240, 0.95)'); // Solid body
    sphereGrad.addColorStop(0.85, 'rgba(190, 190, 190, 0.9)');  // Shaded falloff
    sphereGrad.addColorStop(1, 'rgba(100, 100, 100, 0.85)');    // Darkened Fresnel rim
    ctx.fillStyle = sphereGrad;
    ctx.beginPath();
    ctx.arc(64, 64, 40, 0, Math.PI * 2);
    ctx.fill();

    // 3. Crisp Anti-Aliased Outline Stroke
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(64, 64, 40, 0, Math.PI * 2);
    ctx.stroke();

    // 4. Specular Gloss Sparkle Dot (Top-Left Highlight)
    const specGrad = ctx.createRadialGradient(48, 48, 0, 48, 48, 10);
    specGrad.addColorStop(0, 'rgba(255, 255, 255, 1.0)');
    specGrad.addColorStop(0.5, 'rgba(255, 255, 255, 0.7)');
    specGrad.addColorStop(1, 'rgba(255, 255, 255, 0)');
    ctx.fillStyle = specGrad;
    ctx.beginPath();
    ctx.arc(48, 48, 10, 0, Math.PI * 2);
    ctx.fill();

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    texture.magFilter = THREE.LinearFilter;
    return texture;
  }

  buildPointCloud() {
    const count = this.vectorsData.length;
    if (count === 0) return;

    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      const v = this.vectorsData[i];
      positions[i * 3] = v.x;
      positions[i * 3 + 1] = v.y;
      positions[i * 3 + 2] = v.z;

      const hex = this.categoryColors[v.category] || 0x38bdf8;
      const c = new THREE.Color(hex);
      colors[i * 3] = c.r;
      colors[i * 3 + 1] = c.g;
      colors[i * 3 + 2] = c.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    geometry.computeBoundingSphere();
    geometry.computeBoundingBox();

    const texture = this.createCrispNodeTexture();

    // High-Contrast Crisp Points Material
    const material = new THREE.PointsMaterial({
      size: 3.2,
      vertexColors: true,
      map: texture,
      transparent: true,
      alphaTest: 0.05,
      depthWrite: false,
      blending: THREE.NormalBlending
    });

    this.pointCloud = new THREE.Points(geometry, material);
    this.group.add(this.pointCloud);
  }

  buildQuantizationGrid() {
    this.quantGrid = new THREE.Group();
    this.quantGrid.visible = false;

    // SQ8 Bounding Cube with crisp emerald edges
    const boxGeo = new THREE.BoxGeometry(90, 90, 90);
    const boxEdges = new THREE.EdgesGeometry(boxGeo);
    const boxLine = new THREE.LineSegments(boxEdges, new THREE.LineBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.8 }));
    this.quantGrid.add(boxLine);

    // 3D discrete quantization grid lines
    const gridMat = new THREE.LineBasicMaterial({ color: 0x059669, transparent: true, opacity: 0.3 });
    for (let x = -40; x <= 40; x += 20) {
      for (let y = -40; y <= 40; y += 20) {
        const lineGeo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(x, y, -45),
          new THREE.Vector3(x, y, 45)
        ]);
        this.quantGrid.add(new THREE.Line(lineGeo, gridMat));
      }
    }

    this.group.add(this.quantGrid);
  }

  toggleQuantizationGrid(show) {
    if (this.quantGrid) {
      this.quantGrid.visible = show;
    }
  }

  handleMouseMove(raycaster) {
    if (!this.pointCloud) return;
    raycaster.params.Points = raycaster.params.Points || {};
    raycaster.params.Points.threshold = 2.2;
    const intersects = raycaster.intersectObject(this.pointCloud);
    const tooltipEl = document.getElementById('hud-tooltip-3d');

    if (intersects.length > 0) {
      const idx = intersects[0].index;
      const data = this.vectorsData[idx];
      if (!data) return;

      document.body.style.cursor = 'pointer';

      // Move sharp hover reticle to hovered point
      if (this.hoverReticle) {
        this.hoverReticle.visible = true;
        this.hoverReticle.position.set(data.x, data.y, data.z);
        this.hoverReticle.lookAt(this.engine.camera.position);
      }

      if (tooltipEl) {
        tooltipEl.style.display = 'block';
        tooltipEl.style.left = `${(this.engine.mouse.x + 1) * 0.5 * this.engine.container.clientWidth + 15}px`;
        tooltipEl.style.top = `${(-this.engine.mouse.y + 1) * 0.5 * this.engine.container.clientHeight - 10}px`;
        tooltipEl.innerHTML = `
          <div class="text-[16px] font-bold text-white leading-snug">${data.title.slice(0, 80)}...</div>
          <div class="text-[14px] font-semibold mt-1 flex items-center gap-1.5" style="color: #${new THREE.Color(this.categoryColors[data.category] || 0x38bdf8).getHexString()}">
            <i class="fa-solid fa-tag text-xs"></i> Chuyên mục: ${data.category}
          </div>
          <div class="text-[13px] text-slate-300 font-mono mt-1.5 bg-slate-900/90 px-2.5 py-1 rounded-lg border border-slate-700 inline-block font-bold">
            Tọa độ 3D: [${data.x.toFixed(1)}, ${data.y.toFixed(1)}, ${data.z.toFixed(1)}]
          </div>
        `;
      }
    } else {
      document.body.style.cursor = 'default';
      if (this.hoverReticle) this.hoverReticle.visible = false;
      if (tooltipEl) tooltipEl.style.display = 'none';
    }
  }

  handleClick(raycaster) {
    if (!this.pointCloud) return;
    raycaster.params.Points = raycaster.params.Points || {};
    raycaster.params.Points.threshold = 2.2;
    const intersects = raycaster.intersectObject(this.pointCloud);
    if (intersects.length > 0) {
      const idx = intersects[0].index;
      const data = this.vectorsData[idx];
      if (data) this.inspectVectorPoint(data);
    }
  }

  inspectVectorPoint(data) {
    this.highlightNode(data.x, data.y, data.z, data.title);

    const infoPanel = document.getElementById('hud-detail-panel');
    if (!infoPanel) return;

    infoPanel.classList.remove('hidden');
    document.getElementById('hud-doc-title').textContent = data.title;
    document.getElementById('hud-doc-category').textContent = data.category;
    document.getElementById('hud-doc-category').className = `px-3 py-1 rounded-lg text-[13px] font-bold ${
      data.category === 'Kinh doanh & Tài chính' ? 'bg-sky-500/30 text-sky-300 border border-sky-500/50' :
      data.category === 'Khoa học & Công nghệ' ? 'bg-purple-500/30 text-purple-300 border border-purple-500/50' :
      data.category === 'Y tế & Sức khỏe' ? 'bg-emerald-500/30 text-emerald-300 border border-emerald-500/50' :
      'bg-indigo-500/30 text-indigo-300 border border-indigo-500/50'
    }`;
    document.getElementById('hud-doc-preview').textContent = data.preview || data.title;
    document.getElementById('hud-doc-coords').textContent = `X: ${data.x.toFixed(2)} | Y: ${data.y.toFixed(2)} | Z: ${data.z.toFixed(2)}`;
    document.getElementById('hud-doc-tokens').textContent = `${data.token_count || 280} tokens`;
  }

  renderQueryResults(queryText, query3D, results) {
    this.clearQueryArtifacts();

    if (!query3D) {
      query3D = { x: 0, y: 10, z: 0 };
    }
    this.lastQueryPos = query3D;

    // 1. Create Crisp Query Beacon
    const beaconGroup = new THREE.Group();
    beaconGroup.position.set(query3D.x, query3D.y, query3D.z);

    // Glowing Core Sphere
    const coreGeo = new THREE.SphereGeometry(2.4, 24, 24);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0xf59e0b,
      emissive: 0xd97706,
      emissiveIntensity: 0.8,
      roughness: 0.2,
      metalness: 0.6
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    beaconGroup.add(coreMesh);

    // Inner Glowing Halo Ring
    const innerRingGeo = new THREE.RingGeometry(3.2, 3.8, 32);
    const innerRingMat = new THREE.MeshBasicMaterial({ color: 0xfbbf24, side: THREE.DoubleSide, transparent: true, opacity: 0.9 });
    const innerRing = new THREE.Mesh(innerRingGeo, innerRingMat);
    innerRing.rotation.x = Math.PI / 2;
    beaconGroup.add(innerRing);

    // Outer Rotating Ring
    const outerRingGeo = new THREE.RingGeometry(4.8, 5.3, 32);
    const outerRingMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, side: THREE.DoubleSide, transparent: true, opacity: 0.65 });
    const outerRing = new THREE.Mesh(outerRingGeo, outerRingMat);
    outerRing.rotation.y = Math.PI / 4;
    beaconGroup.add(outerRing);

    // Vertical Light Column
    const beamGeo = new THREE.CylinderGeometry(0.25, 0.25, 50, 16);
    const beamMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b, transparent: true, opacity: 0.7 });
    const beamMesh = new THREE.Mesh(beamGeo, beamMat);
    beamMesh.position.y = 25;
    beaconGroup.add(beamMesh);

    // 3D Billboard Text Label above Beacon
    const labelText = `🎯 QUERY: ${queryText.slice(0, 28)}`;
    const textSprite = this.engine.create3DTextSprite(labelText, 'rgba(245, 158, 11, 0.95)', '#ffffff', 30);
    textSprite.position.y = 7.5;
    beaconGroup.add(textSprite);

    this.queryBeacon = beaconGroup;
    this.group.add(this.queryBeacon);

    // 2. Create Crisp Glowing Laser Rays to Top-K Results
    results.forEach((res, index) => {
      const targetCoords = res.coords_3d || { x: 0, y: 0, z: 0 };

      const points = [
        new THREE.Vector3(query3D.x, query3D.y, query3D.z),
        new THREE.Vector3(targetCoords.x, targetCoords.y, targetCoords.z)
      ];

      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({
        color: index === 0 ? 0x10b981 : 0x38bdf8,
        linewidth: 2.5,
        transparent: true,
        opacity: 0.9
      });

      const laser = new THREE.Line(lineGeo, lineMat);
      this.laserLines.push(laser);
      this.group.add(laser);

      // Target reticle ring
      const reticleGeo = new THREE.RingGeometry(2.0, 2.6, 24);
      const reticleMat = new THREE.MeshBasicMaterial({
        color: index === 0 ? 0x10b981 : 0x38bdf8,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.95
      });
      const reticleMesh = new THREE.Mesh(reticleGeo, reticleMat);
      reticleMesh.position.set(targetCoords.x, targetCoords.y, targetCoords.z);
      reticleMesh.lookAt(query3D.x, query3D.y, query3D.z);
      this.laserLines.push(reticleMesh);
      this.group.add(reticleMesh);

      // Rank billboard tags
      const rankSprite = this.engine.create3DTextSprite(
        `#${res.rank} (${Math.round(res.similarity_score * 100)}%)`,
        index === 0 ? 'rgba(16, 185, 129, 0.95)' : 'rgba(2, 132, 199, 0.95)',
        '#ffffff',
        32
      );
      rankSprite.scale.set(14, 3.5, 1);
      rankSprite.position.set(targetCoords.x, targetCoords.y + 3.2, targetCoords.z);
      this.laserLines.push(rankSprite);
      this.group.add(rankSprite);
    });
  }

  clearQueryArtifacts() {
    if (this.queryBeacon) {
      this.group.remove(this.queryBeacon);
      this.queryBeacon = null;
    }
    this.laserLines.forEach(l => this.group.remove(l));
    this.laserLines = [];
  }

  filterByCategory(category) {
    if (!this.pointCloud || !this.vectorsData) return;
    const colors = this.pointCloud.geometry.attributes.color.array;

    for (let i = 0; i < this.vectorsData.length; i++) {
      const v = this.vectorsData[i];
      const match = category === 'Tất cả' || v.category === category;
      const hex = this.categoryColors[v.category] || 0x38bdf8;
      const c = new THREE.Color(hex);

      if (match) {
        colors[i * 3] = c.r;
        colors[i * 3 + 1] = c.g;
        colors[i * 3 + 2] = c.b;
      } else {
        colors[i * 3] = c.r * 0.12;
        colors[i * 3 + 1] = c.g * 0.12;
        colors[i * 3 + 2] = c.b * 0.12;
      }
    }

    this.pointCloud.geometry.attributes.color.needsUpdate = true;
  }

  setVisible(visible) {
    this.group.visible = visible;
  }

  update(delta) {
    if (this.queryBeacon) {
      const innerRing = this.queryBeacon.children[1];
      const outerRing = this.queryBeacon.children[2];
      if (innerRing) innerRing.rotation.z += delta * 1.8;
      if (outerRing) outerRing.rotation.x += delta * 1.2;
    }

    if (this.hoverReticle && this.hoverReticle.visible) {
      this.hoverReticle.children[1].rotation.z += delta * 2.5;
    }

    if (this.focusMarker && this.focusMarker.visible) {
      this.focusMarker.lookAt(this.engine.camera.position);
      this.focusAnimTimer = (this.focusAnimTimer || 0) + delta;
      if (this.focusRingOuter) {
        this.focusRingOuter.rotation.z += delta * 2.0;
      }
      if (this.focusRingInner) {
        this.focusRingInner.rotation.z -= delta * 1.5;
      }
      const s = 1.0 + Math.sin(this.focusAnimTimer * 5.0) * 0.14;
      this.focusMarker.scale.set(s, s, s);
    }
  }
}

window.VectorSpaceModule = VectorSpaceModule;
