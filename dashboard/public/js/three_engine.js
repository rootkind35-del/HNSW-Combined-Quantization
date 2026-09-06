/**
 * Three.js 3D Engine Core & Scene Manager
 * Brightened Lighting, High-Detail Materials, and Crisp 3D Billboard Labels.
 */

class ThreeEngine {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`ThreeEngine: Container #${containerId} not found.`);
      return;
    }

    this.currentMode = 'universe'; // 'universe' | 'hnsw' | 'pipeline' | 'quantization'
    this.activeNodes = [];
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2(-999, -999);
    this.hoveredObject = null;
    this.selectedObject = null;
    this.isAutoRotating = false;

    // Sub-modules
    this.vectorSpaceModule = null;
    this.hnswModule = null;
    this.pipelineModule = null;

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 1000;
    const height = this.container.clientHeight || 760;

    // 1. Scene with deep obsidian void and ultra-clean depth
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x020617); // Deep obsidian space
    this.scene.fog = new THREE.FogExp2(0x020617, 0.001); // Minimal fog preserving crystal-clear node sharpness

    // 2. Camera with wide panoramic field of view
    this.camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 2500);
    this.camera.position.set(0, 45, 100);

    // 3. WebGL Renderer with Calibrated Tone Mapping (High Contrast & Sharpness)
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25; // Balanced exposure eliminating fuzzy washed-out blur

    // Clear previous canvas if any
    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.maxDistance = 400;
    this.controls.minDistance = 5;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.15;

    // 5. Bright Multi-Source Lighting
    this.setupLighting();

    // 6. Glowing Sci-Fi Grid Platform
    this.setupBaseGrid();

    // 7. Event Listeners
    window.addEventListener('resize', () => this.onWindowResize());
    this.renderer.domElement.addEventListener('mousemove', (e) => this.onMouseMove(e));
    this.renderer.domElement.addEventListener('click', (e) => this.onMouseClick(e));

    // 8. Animation Loop
    this.clock = new THREE.Clock();
    this.animate();

    console.log('[ThreeEngine] Enhanced Bright WebGL 3D Engine initialized.');
  }

  setupLighting() {
    // 1. High-intensity ambient light
    const ambientLight = new THREE.AmbientLight(0x93c5fd, 1.1);
    this.scene.add(ambientLight);

    // 2. Main Key Directional Lights
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 1.6);
    dirLight1.position.set(70, 110, 70);
    this.scene.add(dirLight1);

    const dirLight2 = new THREE.DirectionalLight(0x818cf8, 1.0);
    dirLight2.position.set(-70, -30, -70);
    this.scene.add(dirLight2);

    // 3. Multi-color Point Lights for rich volumetric glow
    const centerPointLight = new THREE.PointLight(0x38bdf8, 2.5, 300);
    centerPointLight.position.set(0, 40, 0);
    this.scene.add(centerPointLight);

    const leftPointLight = new THREE.PointLight(0xa855f7, 1.8, 280);
    leftPointLight.position.set(-60, 20, 30);
    this.scene.add(leftPointLight);

    const rightPointLight = new THREE.PointLight(0x10b981, 1.8, 280);
    rightPointLight.position.set(60, 20, -30);
    this.scene.add(rightPointLight);
  }

  setupBaseGrid() {
    this.gridHelper = new THREE.GridHelper(160, 40, 0x38bdf8, 0x1e3a8a);
    this.gridHelper.position.y = -35;
    this.scene.add(this.gridHelper);
  }

  // Utility to generate crisp 3D text billboards
  create3DTextSprite(text, bgColor = 'rgba(15, 23, 42, 0.85)', textColor = '#38bdf8', fontSize = 32) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    // Rounded Box
    ctx.fillStyle = bgColor;
    ctx.roundRect ? ctx.roundRect(10, 10, 492, 108, 20) : ctx.fillRect(10, 10, 492, 108);
    ctx.fill();

    // Border
    ctx.strokeStyle = textColor;
    ctx.lineWidth = 4;
    ctx.roundRect ? ctx.roundRect(10, 10, 492, 108, 20) : ctx.strokeRect(10, 10, 492, 108);
    ctx.stroke();

    // Text
    ctx.font = `bold ${fontSize}px sans-serif`;
    ctx.fillStyle = textColor;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 256, 64);

    const texture = new THREE.CanvasTexture(canvas);
    texture.minFilter = THREE.LinearFilter;
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(22, 5.5, 1);
    return sprite;
  }

  onWindowResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  onMouseMove(event) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(this.mouse, this.camera);

    if (this.currentMode === 'universe' && this.vectorSpaceModule) {
      this.vectorSpaceModule.handleMouseMove(this.raycaster);
    } else if (this.currentMode === 'hnsw' && this.hnswModule) {
      this.hnswModule.handleMouseMove(this.raycaster);
    } else if (this.currentMode === 'pipeline' && this.pipelineModule) {
      this.pipelineModule.handleMouseMove(this.raycaster);
    }
  }

  onMouseClick(event) {
    if (event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }
    this.raycaster.setFromCamera(this.mouse, this.camera);

    if (this.currentMode === 'universe' && this.vectorSpaceModule) {
      this.vectorSpaceModule.handleClick(this.raycaster);
    } else if (this.currentMode === 'hnsw' && this.hnswModule) {
      this.hnswModule.handleClick(this.raycaster);
    } else if (this.currentMode === 'pipeline' && this.pipelineModule) {
      this.pipelineModule.handleClick(this.raycaster);
    }
  }

  setMode(mode, resetCamera = true) {
    this.currentMode = mode;
    console.log(`[ThreeEngine] Switched to 3D mode: ${mode}, resetCamera: ${resetCamera}`);

    if (this.vectorSpaceModule) this.vectorSpaceModule.setVisible(mode === 'universe' || mode === 'quantization');
    if (this.hnswModule) this.hnswModule.setVisible(mode === 'hnsw');
    if (this.pipelineModule) this.pipelineModule.setVisible(mode === 'pipeline');

    if (mode === 'hnsw') {
      this.gridHelper.position.y = -35;
      if (resetCamera) this.setCameraPreset('hnsw');
    } else if (mode === 'pipeline') {
      this.gridHelper.position.y = -10;
      if (resetCamera) this.setCameraPreset('pipeline');
    } else if (mode === 'quantization') {
      this.gridHelper.position.y = -35;
      if (this.vectorSpaceModule) this.vectorSpaceModule.toggleQuantizationGrid(true);
      if (resetCamera) this.setCameraPreset('universe');
    } else {
      this.gridHelper.position.y = -35;
      if (this.vectorSpaceModule) this.vectorSpaceModule.toggleQuantizationGrid(false);
      if (resetCamera) this.setCameraPreset('universe');
    }
  }

  setCameraPreset(preset) {
    const duration = 1.0;
    let targetPos = { x: 0, y: 40, z: 95 };
    let targetLook = { x: 0, y: 0, z: 0 };

    switch (preset) {
      case 'universe':
        targetPos = { x: 0, y: 35, z: 95 };
        targetLook = { x: 0, y: 0, z: 0 };
        break;
      case 'topdown':
        targetPos = { x: 0, y: 130, z: 0.1 };
        targetLook = { x: 0, y: 0, z: 0 };
        break;
      case 'hnsw':
        targetPos = { x: 80, y: 55, z: 90 };
        targetLook = { x: 0, y: 0, z: 0 };
        break;
      case 'pipeline':
        targetPos = { x: -60, y: 50, z: 80 };
        targetLook = { x: 5, y: 5, z: 0 };
        break;
      case 'query':
        if (this.vectorSpaceModule && this.vectorSpaceModule.lastQueryPos) {
          const qp = this.vectorSpaceModule.lastQueryPos;
          targetPos = { x: qp.x + 22, y: qp.y + 18, z: qp.z + 32 };
          targetLook = { x: qp.x, y: qp.y, z: qp.z };
        }
        break;
    }

    this.animateCameraTo(targetPos, targetLook, duration);
  }

  animateCameraTo(pos, lookAt, duration = 1.0) {
    // 1. Dừng tự động xoay nếu đang bật
    if (this.isAutoRotating) {
      this.isAutoRotating = false;
      this.controls.autoRotate = false;
      const autoBtn = document.getElementById('btn-3d-autorotate');
      if (autoBtn) autoBtn.classList.remove('bg-sky-500', 'text-white');
    }

    if (typeof gsap !== 'undefined') {
      // 2. Huỷ các tween trước đó trên camera và controls để chống giật / reset góc nhìn
      gsap.killTweensOf(this.camera.position);
      gsap.killTweensOf(this.controls.target);

      // 3. Tạm ngắt damping trong khi camera đang zoom lướt
      const prevDamping = this.controls.enableDamping;
      this.controls.enableDamping = false;

      gsap.to(this.camera.position, {
        x: pos.x,
        y: pos.y,
        z: pos.z,
        duration: duration,
        ease: 'power2.out',
        overwrite: 'all',
        onUpdate: () => {
          this.camera.lookAt(this.controls.target.x, this.controls.target.y, this.controls.target.z);
        },
        onComplete: () => {
          this.controls.target.set(lookAt.x, lookAt.y, lookAt.z);
          this.camera.lookAt(lookAt.x, lookAt.y, lookAt.z);
          this.controls.update();
          this.controls.enableDamping = prevDamping;
        }
      });

      gsap.to(this.controls.target, {
        x: lookAt.x,
        y: lookAt.y,
        z: lookAt.z,
        duration: duration,
        ease: 'power2.out',
        overwrite: 'all'
      });
    } else {
      this.camera.position.set(pos.x, pos.y, pos.z);
      this.controls.target.set(lookAt.x, lookAt.y, lookAt.z);
      this.camera.lookAt(lookAt.x, lookAt.y, lookAt.z);
      this.controls.update();
    }
  }

  toggleAutoRotate() {
    this.isAutoRotating = !this.isAutoRotating;
    this.controls.autoRotate = this.isAutoRotating;
    this.controls.autoRotateSpeed = 1.4;
    return this.isAutoRotating;
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const delta = this.clock.getDelta();
    this.controls.update();

    if (this.currentMode === 'universe' || this.currentMode === 'quantization') {
      if (this.vectorSpaceModule) this.vectorSpaceModule.update(delta);
    } else if (this.currentMode === 'hnsw') {
      if (this.hnswModule) this.hnswModule.update(delta);
    } else if (this.currentMode === 'pipeline') {
      if (this.pipelineModule) this.pipelineModule.update(delta);
    }

    this.renderer.render(this.scene, this.camera);
  }
}

window.ThreeEngine = ThreeEngine;
