// Studio renderer: progressive accumulation of N raster passes.
// Each pass jitters (a) the key light over a disc (true area-light soft
// shadows with contact hardening), (b) K shadow-casting sky lights over the
// hemisphere (real sky occlusion: deep AO in every corner, not screen-space),
// (c) the sub-pixel position (anti-aliasing) and (d) the lens position over
// the aperture (physical depth of field). The average is tone-mapped with AgX.
// Deterministic: the sample pattern depends only on the sample index.
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { halton, hash1 } from './prng.js';

export function kelvinToRGB(k) {
  // Tanner Helland approximation, normalised so the max channel is 1.
  const t = k / 100;
  let r, g, b;
  if (t <= 66) { r = 255; g = 99.4708025861 * Math.log(t) - 161.1195681661; }
  else { r = 329.698727446 * Math.pow(t - 60, -0.1332047592); g = 288.1221695283 * Math.pow(t - 60, -0.0755148492); }
  if (t >= 66) b = 255; else if (t <= 19) b = 0; else b = 138.5177312231 * Math.log(t - 10) - 305.0447927307;
  const c = [r, g, b].map((v) => Math.min(255, Math.max(0, v)) / 255);
  const m = Math.max(...c);
  return new THREE.Color().setRGB(c[0] / m, c[1] / m, c[2] / m, THREE.SRGBColorSpace);
}

const FS_VERT = /* glsl */`
varying vec2 vUv;
void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export class Studio {
  constructor(canvas, width, height, { skyLights = 2, keyMap = 4096, skyMap = 2048 } = {}) {
    this.W = width;
    this.H = height;
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(1);
    renderer.setSize(width, height, false);
    renderer.autoClear = false;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.shadowMap.autoUpdate = true;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    this.renderer = renderer;

    this.scene = new THREE.Scene();
    const pm = new THREE.PMREMGenerator(renderer);
    this.envTex = pm.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environment = this.envTex;
    this.scene.environmentIntensity = 0.15;

    this.near = 0.5; this.far = 600;
    this.camera = new THREE.PerspectiveCamera(30, width / height, this.near, this.far);

    const mkLight = (size) => {
      const l = new THREE.DirectionalLight(0xffffff, 1);
      l.castShadow = true;
      l.shadow.mapSize.set(size, size);
      l.shadow.bias = -0.00015;
      l.shadow.radius = 1.6;
      this.scene.add(l, l.target);
      return l;
    };
    this.key = mkLight(keyMap);
    this.sky = [];
    for (let i = 0; i < skyLights; i++) this.sky.push(mkLight(skyMap));

    const rtOpts = { type: THREE.HalfFloatType, depthBuffer: true, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter };
    this.rtSample = new THREE.WebGLRenderTarget(width, height, rtOpts);
    const gl = renderer.getContext();
    const floatBlend = !!gl.getExtension('EXT_float_blend') && !!gl.getExtension('EXT_color_buffer_float');
    this.rtAccum = new THREE.WebGLRenderTarget(width, height, { type: floatBlend ? THREE.FloatType : THREE.HalfFloatType, depthBuffer: false, minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter });

    const quad = new THREE.PlaneGeometry(2, 2);
    this.addMat = new THREE.ShaderMaterial({
      uniforms: { tSrc: { value: null }, weight: { value: 1 } },
      vertexShader: FS_VERT,
      fragmentShader: /* glsl */`
        uniform sampler2D tSrc; uniform float weight; varying vec2 vUv;
        void main(){ vec3 c = texture2D(tSrc, vUv).rgb; c = min(c, vec3(64.0)); gl_FragColor = vec4(c * weight, 1.0); }`,
      blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.OneFactor, blendDst: THREE.OneFactor,
      depthTest: false, depthWrite: false,
    });
    this.outMat = new THREE.RawShaderMaterial({
      uniforms: { tDiffuse: { value: null }, toneMappingExposure: { value: 1 }, uRes: { value: new THREE.Vector2(width, height) }, uFade: { value: 1 }, uFadeCol: { value: new THREE.Color(0x000f1e) } },
      defines: { AGX_TONE_MAPPING: '', SRGB_TRANSFER: '' },
      vertexShader: /* glsl */`
        precision highp float; attribute vec3 position; attribute vec2 uv; varying vec2 vUv;
        void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`,
      fragmentShader: /* glsl */`
        precision highp float;
        uniform sampler2D tDiffuse; uniform vec2 uRes; uniform float uFade; uniform vec3 uFadeCol;
        #include <tonemapping_pars_fragment>
        #include <colorspace_pars_fragment>
        varying vec2 vUv;
        float ign(vec2 p){ return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
        void main(){
          vec4 c = vec4(texture2D(tDiffuse, vUv).rgb, 1.0);
          c.rgb = AgXToneMapping(c.rgb);
          c = sRGBTransferOETF(c);
          c.rgb = mix(uFadeCol, c.rgb, uFade);
          c.rgb += (ign(gl_FragCoord.xy) - 0.5) / 255.0; // deterministic dither against banding
          gl_FragColor = vec4(c.rgb, 1.0);
        }`,
      depthTest: false, depthWrite: false,
    });
    this.fsScene = new THREE.Scene();
    this.fsCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.fsQuad = new THREE.Mesh(quad, this.addMat);
    this.fsQuad.frustumCulled = false;
    this.fsScene.add(this.fsQuad);
  }

  info() {
    const gl = this.renderer.getContext();
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    return {
      gpu: ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unknown',
      accum: this.rtAccum.texture.type === THREE.FloatType ? 'float32' : 'float16',
      maxTex: gl.getParameter(gl.MAX_TEXTURE_SIZE),
    };
  }

  fitLight(light, dir, center, radius) {
    light.target.position.copy(center);
    light.position.copy(center).addScaledVector(dir, radius * 2.2);
    const cam = light.shadow.camera;
    cam.left = -radius; cam.right = radius; cam.top = radius; cam.bottom = -radius;
    cam.near = 0.1; cam.far = radius * 4.4;
    cam.updateProjectionMatrix();
    const texel = (2 * radius) / light.shadow.mapSize.x;
    light.shadow.normalBias = texel * 1.4;
    light.target.updateMatrixWorld();
    light.updateMatrixWorld();
  }

  // settings: { cam:{position,target,fov,aperture,shift,focus}, key, sky, env, exposure, fit }
  // projection (no jitter) identical to the one used for rendering
  baseProjection(cam) {
    const c = new THREE.PerspectiveCamera(cam.fov, this.W / this.H, this.near, this.far);
    c.position.copy(cam.position); c.up.set(0, 1, 0); c.lookAt(cam.target); c.updateMatrixWorld();
    const top = this.near * Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2), rgt = top * this.W / this.H;
    const sx = (cam.shift?.[0] ?? 0) * rgt, sy = (cam.shift?.[1] ?? 0) * top;
    c.projectionMatrix.makePerspective(-rgt + sx, rgt + sx, top + sy, -top + sy, this.near, this.far);
    c.projectionMatrixInverse.copy(c.projectionMatrix).invert();
    return c;
  }

  render(settings, spp, onSample) {
    const { renderer, scene, camera } = this;
    const S = settings;
    const N = Math.max(1, spp | 0);
    const K = this.sky.length;
    scene.environmentIntensity = S.env;
    scene.environment = S.env > 0 ? this.envTex : null;
    renderer.toneMappingExposure = 1;
    this.outMat.uniforms.toneMappingExposure.value = S.exposure;
    this.outMat.uniforms.uFade.value = S.fade ?? 1;
    camera.near = this.near; camera.far = this.far;

    // camera base frame
    camera.fov = S.cam.fov;
    camera.aspect = this.W / this.H;
    camera.position.copy(S.cam.position);
    camera.up.set(0, 1, 0);
    camera.lookAt(S.cam.target);
    camera.updateMatrixWorld();
    const basePos = camera.position.clone();
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    const focus = S.cam.focus ?? basePos.distanceTo(S.cam.target);

    // lights
    const keyCol = kelvinToRGB(S.key.kelvin);
    const skyCol = kelvinToRGB(S.sky.kelvin);
    const d2r = THREE.MathUtils.degToRad;
    const dirFrom = (azD, elD) => {
      const az = d2r(azD), el = d2r(elD);
      return new THREE.Vector3(Math.cos(el) * Math.sin(az), Math.sin(el), Math.cos(el) * Math.cos(az));
    };
    const keyDir = dirFrom(S.key.az, S.key.el);
    const kT = new THREE.Vector3().crossVectors(keyDir, new THREE.Vector3(0, 1, 0)).normalize();
    if (kT.lengthSq() < 1e-6) kT.set(1, 0, 0);
    const kB = new THREE.Vector3().crossVectors(kT, keyDir).normalize();
    const spread = Math.tan(d2r(S.key.spread));

    // sky directions: stratified uniform hemisphere (Fibonacci), weighted towards zenith
    const M = N * K;
    const golden = Math.PI * (3 - Math.sqrt(5));
    const rot = hash1(1234) * Math.PI * 2;
    const dirs = [];
    let norm = 0;
    for (let j = 0; j < M; j++) {
      const cz = 1 - (j + 0.5) / M;
      const phi = j * golden + rot;
      const sz = Math.sqrt(1 - cz * cz);
      const w = (1 - S.sky.zenith) + S.sky.zenith * cz * 1.5;
      dirs.push({ d: new THREE.Vector3(sz * Math.cos(phi), Math.max(cz, 0.04), sz * Math.sin(phi)).normalize(), w });
      norm += w * cz;
    }
    norm /= M;
    // shuffle deterministically so each pass gets spread-out directions
    const order = dirs.map((_, j) => j).sort((a, b) => hash1(a * 7919 + 13) - hash1(b * 7919 + 13));

    const center = S.fit.center, radius = S.fit.radius;
    const near = camera.near, far = camera.far;
    const top = near * Math.tan(d2r(camera.fov) / 2);
    const rgt = top * camera.aspect;
    const sx0 = (S.cam.shift?.[0] ?? 0) * rgt, sy0 = (S.cam.shift?.[1] ?? 0) * top;

    renderer.setRenderTarget(this.rtAccum);
    renderer.setClearColor(0x000000, 0);
    renderer.clear(true, false, false);
    const sync = new Uint8Array(4);

    for (let i = 0; i < N; i++) {
      if (onSample) {
        const c2 = onSample(i, N);
        if (c2) {
          camera.position.copy(c2.position); camera.lookAt(c2.target); camera.updateMatrixWorld();
          basePos.copy(camera.position);
          right.setFromMatrixColumn(camera.matrixWorld, 0); up.setFromMatrixColumn(camera.matrixWorld, 1);
        }
      }
      // key light over a disc (Halton 2,3 with a fixed rotation offset)
      const u1 = (halton(i + 1, 2) + 0.371) % 1, u2 = (halton(i + 1, 3) + 0.613) % 1;
      const r = Math.sqrt(u1) * spread, a = u2 * Math.PI * 2;
      const kd = keyDir.clone().addScaledVector(kT, Math.cos(a) * r).addScaledVector(kB, Math.sin(a) * r).normalize();
      this.key.color.copy(keyCol);
      this.key.intensity = S.key.intensity;
      this.fitLight(this.key, kd, center, radius);
      for (let k = 0; k < K; k++) {
        const s = dirs[order[i * K + k]];
        const L = this.sky[k];
        L.color.copy(skyCol);
        L.intensity = (S.sky.intensity * s.w) / (norm * K);
        this.fitLight(L, s.d, center, radius);
      }
      // pixel jitter (Halton 5,7) and lens sample (Halton 11,13)
      const jx = halton(i + 1, 5) - 0.5, jy = halton(i + 1, 7) - 0.5;
      const lr = Math.sqrt(halton(i + 1, 11)) * (S.cam.aperture || 0), la = halton(i + 1, 13) * Math.PI * 2;
      const lx = Math.cos(la) * lr, ly = Math.sin(la) * lr;
      camera.position.copy(basePos).addScaledVector(right, lx).addScaledVector(up, ly);
      camera.updateMatrixWorld();
      const sx = sx0 - (lx * near) / focus + (jx * 2 * rgt) / this.W;
      const sy = sy0 - (ly * near) / focus + (jy * 2 * top) / this.H;
      camera.projectionMatrix.makePerspective(-rgt + sx, rgt + sx, top + sy, -top + sy, near, far);
      camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();

      renderer.setRenderTarget(this.rtSample);
      renderer.setClearColor(scene.userData.bg ?? 0xe7e3dc, 1);
      renderer.clear(true, true, false);
      renderer.render(scene, camera);

      this.fsQuad.material = this.addMat;
      this.addMat.uniforms.tSrc.value = this.rtSample.texture;
      this.addMat.uniforms.weight.value = 1 / N;
      renderer.setRenderTarget(this.rtAccum);
      renderer.render(this.fsScene, this.fsCam);
      if ((i & 7) === 7) renderer.readRenderTargetPixels(this.rtSample, 0, 0, 1, 1, new Uint16Array(4)); // keep the GPU queue short
    }
    camera.position.copy(basePos);
    renderer.setRenderTarget(null);
    this.fsQuad.material = this.outMat;
    this.outMat.uniforms.tDiffuse.value = this.rtAccum.texture;
    renderer.render(this.fsScene, this.fsCam);
    const gl = renderer.getContext();
    gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, sync); // block until the frame is done
  }
}
