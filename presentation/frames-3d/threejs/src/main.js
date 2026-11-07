// Entry: builds the world once, exposes a deterministic seek API.
//   index.html?beat=storm|where|problems|map|dawn&t=<seconds>&spp=<samples>
// HyperFrames: listens to `hf-seek` and renders e.detail.time.
import * as THREE from 'three';
import { makeMaterials, buildWorld, buildStorm, buildPlinths, buildSweep, GROUND } from './world.js';
import { buildRoutes, makeTrucks } from './routes.js';
import { BEATS, STILL_T, applyState, cameraPose } from './beats.js';
import { Studio } from './studio.js';

const params = new URLSearchParams(location.search);
const W = +(params.get('w') || 1920), H = +(params.get('h') || 1080);
const canvas = document.getElementById('c');
const studio = new Studio(canvas, W, H, { skyLights: +(params.get('sky') || 2) });
const scene = studio.scene;
scene.userData.bg = 0xe7e3dc;

const mats = makeMaterials();
const world = buildWorld(mats);
scene.add(world.root);
const routes = buildRoutes(world, mats);
for (const r of routes) world.village.add(r.group);
const trucks = makeTrucks(mats, 5);
for (const t of trucks) world.village.add(t);
const storm = buildStorm(mats, new THREE.Vector3(world.poleXs[world.stormIndex] + 0.3, GROUND + 5.2, -0.6));
scene.add(storm);
const plinths = buildPlinths(mats, new THREE.Vector3(0, 0, 40));
scene.add(plinths);
const sweep = buildSweep(mats.table);
scene.add(sweep);

const S = { world, routes, trucks, storm, plinths };

function placeSweep(cam) {
  const dx = cam.position.x - cam.target.x, dz = cam.position.z - cam.target.z;
  const az = Math.atan2(dx, dz);
  sweep.rotation.set(0, az, 0);
  const d = cam.sweep;
  sweep.position.set(cam.target.x - Math.sin(az) * d, 0, cam.target.z - Math.cos(az) * d);
  sweep.updateMatrixWorld(true);
}

function settingsFor(beat, t) {
  const { B, cam, fit } = applyState(S, beat, t);
  const pose = cameraPose(cam);
  const c = { ...pose, fov: cam.fov, aperture: cam.aperture, shift: cam.shift, sweep: B.sweep };
  placeSweep(c);
  scene.updateMatrixWorld(true);
  const o = window.daybreak?.override || {};
  return { cam: c, key: { ...B.key, ...(o.key || {}) }, sky: { ...B.sky, ...(o.sky || {}) }, env: o.env ?? B.env, exposure: o.exposure ?? B.exposure, fit };
}

let currentBeat = BEATS[params.get('beat')] ? params.get('beat') : 'map';
const defaultSpp = +(params.get('spp') || 64);

function renderFrame(beat = currentBeat, t = STILL_T[beat], spp = defaultSpp) {
  currentBeat = beat;
  const t0 = performance.now();
  studio.render(settingsFor(beat, t), spp);
  return performance.now() - t0;
}

window.daybreak = {
  BEATS, STILL_T, canvas, studio, info: () => studio.info(),
  renderFrame,
  seek: (t) => renderFrame(currentBeat, t, defaultSpp),
  setBeat: (b) => { currentBeat = b; },
  png: () => canvas.toDataURL('image/png'),
};

// HyperFrames seek protocol: every frame is a pure function of time.
window.addEventListener('hf-seek', (e) => { renderFrame(currentBeat, e.detail.time, defaultSpp); });

const tParam = params.get('t');
const ms = renderFrame(currentBeat, tParam !== null ? +tParam : STILL_T[currentBeat], defaultSpp);
window.__daybreakReady = true;
document.body.dataset.ready = '1';
console.log(`[daybreak] ${currentBeat} rendered in ${ms.toFixed(0)} ms`, studio.info());
