// Planet Daybreak previs entry.
//   planet.html?t=<seconds>&spp=<samples>
// API: window.planet.renderFrame(t, spp, { mblur }) ; window.planet.tracks(t) ; window.planet.png()
// World convention (also used by camera_path.json): planet centre at the
// origin, +Y up, planet radius 1.0, village centred on the north pole (+Y).
import * as THREE from 'three';
import { Studio } from '../studio.js';
import { buildScene, applyAt, lightsFor, anchorWorld } from './scene.js';
import { SMOOTH, ROADS, DEPOT, FIELD, VILLAGE_R } from './world.js';
import { planetFrame } from './painter.js';
import { T, seg, ease, blendAt, FPS, DURATION } from './timeline.js';

const params = new URLSearchParams(location.search);
const W = +(params.get('w') || 1920), H = +(params.get('h') || 1080);
const canvas = document.getElementById('c');
const studio = new Studio(canvas, W, H, { skyLights: 2, keyMap: 4096, skyMap: 2048 });
studio.near = 0.03; studio.far = 400;
const scene = studio.scene;
scene.userData.bg = 0x000f1e;

const SC = buildScene(scene);
// cool rim light from behind the planet (relative to the camera): separates it from the void
const rim = new THREE.DirectionalLight(0xa9c8ff, 1.6);
rim.castShadow = false;
scene.add(rim, rim.target);

function camAt(t) {
  const c = SC.camTrack(t);
  return {
    position: new THREE.Vector3(...c.pos), target: new THREE.Vector3(...c.target), fov: c.fov,
    aperture: c.aperture, shift: c.shift, pos: c.pos, dist: c.dist,
  };
}

function settingsAt(t) {
  const { f } = applyAt(SC, t);
  const cam = camAt(t);
  const L = lightsFor(SC, t, cam);
  const fade = ease.outCubic(seg(t, T.fadeIn[0], T.fadeIn[1]));
  const back = cam.position.clone().setY(0).normalize().multiplyScalar(-6);
  rim.position.set(back.x, 3.2, back.z); rim.target.position.set(0, 0, 0);
  rim.intensity = 1.6 * (1 - 0.5 * L.key.intensity / 6);
  scene.updateMatrixWorld(true);
  const fitR = 1.85 + (1 - f) * 1.6;
  return { cam, key: L.key, sky: L.sky, env: L.env, exposure: L.exposure, fade, fit: { center: new THREE.Vector3(0, 0.25 + (1 - f) * 0.75, 0), radius: fitR }, f };
}

function renderFrame(t, spp = 32, opts = {}) {
  const t0 = performance.now();
  const S = settingsAt(t);
  const shutter = opts.mblur ? (opts.shutter ?? 0.5) / FPS : 0;
  const onSample = shutter > 0 ? (i, N) => {
    const dt = ((i + 0.5) / N - 0.5) * shutter;
    const c = camAt(t + dt);
    return { position: c.position, target: c.target };
  } : null;
  studio.render(S, spp, onSample);
  return performance.now() - t0;
}

function tracks(t) {
  const { f } = applyAt(SC, t);
  scene.updateMatrixWorld(true);
  const cam = camAt(t);
  const pc = studio.baseProjection(cam);
  const A = anchorWorld(SC, t, f);
  const out = {};
  const camPos = cam.position;
  for (const [k, a] of Object.entries(A)) {
    const v = a.p.clone().project(pc);
    const facing = k === 'planet' || a.always ? 1 : a.n.dot(camPos.clone().sub(a.p).normalize());
    out[k] = {
      world: [+a.p.x.toFixed(5), +a.p.y.toFixed(5), +a.p.z.toFixed(5)],
      px: [+(((v.x + 1) / 2) * W).toFixed(1), +(((1 - v.y) / 2) * H).toFixed(1)],
      visible: facing > 0.05 && v.z < 1,
    };
  }
  // projected planet radius in pixels (for the ring text)
  const d = camPos.length();
  const ang = Math.asin(Math.min(1, 1 / d));
  const fy = (H / 2) / Math.tan(THREE.MathUtils.degToRad(cam.fov) / 2);
  out.planet.radiusPx = +(Math.tan(ang) * fy).toFixed(1);
  const L = lightsFor(SC, t, cam);
  return {
    t: +t.toFixed(4), f: +f.toFixed(5),
    camera: { position: cam.pos.map((x) => +x.toFixed(5)), target: cam.target.toArray().map((x) => +x.toFixed(5)), fov: +cam.fov.toFixed(3), shift: cam.shift.map((x) => +x.toFixed(4)), aperture: +cam.aperture.toFixed(4) },
    sun: { position: SC.sun.position.toArray().map((x) => +x.toFixed(4)), visible: SC.sun.visible },
    key: L.key,
    anchors: out,
  };
}

// Screen-space drawing of the flat map (f = 0) at time t, for the 2D PPC map.
function mapLayout(t) {
  applyAt(SC, t);
  const cam = camAt(t);
  const pc = studio.baseProjection(cam);
  const pr = (x, z, h = 0) => {
    const { p } = planetFrame(x, z, 0, 0, h);
    const v = p.project(pc);
    return [+(((v.x + 1) / 2) * W).toFixed(1), +(((1 - v.y) / 2) * H).toFixed(1)];
  };
  const quad = (x, z, yaw, hw, d0, d1) => [[-hw, d0], [hw, d0], [hw, d1], [-hw, d1]].map(([lx, lz]) => pr(x + lx * Math.cos(yaw) + lz * Math.sin(yaw), z - lx * Math.sin(yaw) + lz * Math.cos(yaw)));
  const c = pr(0, 0), e = pr(VILLAGE_R + 2.2, 0);
  return {
    t, center: c, radius: +Math.hypot(e[0] - c[0], e[1] - c[1]).toFixed(1),
    roads: ROADS.map((r) => ({ id: r.id, kind: r.kind, w: r.w, pts: SMOOTH[r.id].filter((_, i) => i % 2 === 0).map(([x, z]) => pr(x, z)) })),
    houses: SC.W.houses.map((h) => ({ id: h.id, quad: quad(h.x, h.z, h.yaw, h.W / 2 + 0.03, 0.05, -h.D - 0.03), roof: pr(h.x, h.z) })),
    depot: quad(DEPOT.x, DEPOT.z, DEPOT.yaw, DEPOT.w / 2, DEPOT.d / 2, -DEPOT.d / 2),
    field: quad(FIELD.x, FIELD.z, FIELD.yaw, FIELD.w / 2, FIELD.d / 2, -FIELD.d / 2),
    routes: SC.routes.map((r) => ({ key: r.key, pts: r.path.filter((_, i) => i % 4 === 0).map((p) => pr(p.x, p.z)) })),
    pxPerUnit: +Math.hypot(e[0] - c[0], e[1] - c[1]).toFixed(2) / (VILLAGE_R + 2.2),
  };
}

window.planet = {
  mapLayout,
  renderFrame, tracks, T, FPS, DURATION, studio,
  png: (type = 'image/png', q) => canvas.toDataURL(type, q),
  houses: SC.W.houses.length,
};
// HyperFrames seek protocol (live mode): every frame is a pure function of t.
window.addEventListener('hf-seek', (e) => renderFrame(e.detail.time, +(params.get('spp') || 16)));

const t = +(params.get('t') || 1.5);
const ms = renderFrame(t, +(params.get('spp') || 16));
window.__planetReady = true;
console.log(`[planet] t=${t} ${ms.toFixed(0)} ms, houses=${SC.W.houses.length}`, studio.info());
