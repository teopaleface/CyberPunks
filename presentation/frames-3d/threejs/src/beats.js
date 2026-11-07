// The five keyframes + the map motion timeline. Every value here is a pure
// function of (beat, t): no clocks, no randomness.
import * as THREE from 'three';
import { setThreadProgress, placeOnCurve, park } from './routes.js';
import { STREET_Y } from './world.js';

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const easeInOutCubic = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const easeOutCubic = (x) => 1 - Math.pow(1 - x, 3);
const easeInOutSine = (x) => -(Math.cos(Math.PI * x) - 1) / 2;
const seg = (t, a, b) => clamp01((t - a) / (b - a));
const lerp = (a, b, t) => a + (b - a) * t;

// Camera spec: target, distance, elevation (deg), azimuth (deg, 0 = from +z / south,
// 90 = from +x / east), fov (deg, vertical), aperture (lens radius, world units),
// shift: [x, y] frustum shift as a fraction of the half-frame (to place the
// subject without tilting verticals).
export const BEATS = {
  storm: {
    duration: 6,
    camera: { target: [1.6, 1.15, 0.6], dist: 15.5, el: 7.5, az: -38, fov: 30, aperture: 0.07, shift: [-0.42, 0.22] },
    key: { az: -20, el: 58, kelvin: 6900, intensity: 1.35, spread: 24 },
    sky: { kelvin: 7600, intensity: 1.9, zenith: 0.75 },
    env: 0.16,
    exposure: 1.02,
    fit: { center: [1, 1.5, 0], radius: 12 },
    sweep: 24,
  },
  where: {
    duration: 6,
    camera: { target: [-19.6, 0.7, -3.9], dist: 15.2, el: 35, az: 22, fov: 28, aperture: 0.06, shift: [0.0, 0.36] },
    key: { az: -82, el: 15, kelvin: 3600, intensity: 3.2, spread: 3.2 },
    sky: { kelvin: 9000, intensity: 0.85, zenith: 0.5 },
    env: 0.12,
    exposure: 1.0,
    fit: { center: [-19.6, 0.5, -3.9], radius: 9.5 },
    sweep: 30,
  },
  problems: {
    duration: 6,
    camera: { target: [0, 2.2, 40.2], dist: 17.5, el: 12, az: 0, fov: 30, aperture: 0.05, shift: [0, -0.32] },
    key: { az: -42, el: 48, kelvin: 5600, intensity: 2.1, spread: 14 },
    sky: { kelvin: 7000, intensity: 1.3, zenith: 0.6 },
    env: 0.22,
    exposure: 1.0,
    fit: { center: [0, 1.6, 40], radius: 7.5 },
    sweep: 10,
  },
  map: {
    duration: 6,
    camera: { target: [0.2, 0.2, 0.6], dist: 58, el: 58, az: 0, fov: 30, aperture: 0.09, shift: [0, 0.32] },
    key: { az: 78, el: 15, kelvin: 4100, intensity: 3.1, spread: 3.0 },
    sky: { kelvin: 8800, intensity: 0.95, zenith: 0.5 },
    env: 0.12,
    exposure: 1.0,
    fit: { center: [0, 0.5, 0], radius: 30 },
    sweep: 32,
  },
  dawn: {
    duration: 6,
    camera: { target: [-3.8, 0.7, 1.6], dist: 25, el: 15, az: -40, fov: 30, aperture: 0.09, shift: [0, -0.48] },
    key: { az: 96, el: 7.5, kelvin: 3000, intensity: 3.6, spread: 2.6 },
    sky: { kelvin: 9500, intensity: 0.7, zenith: 0.4 },
    env: 0.1,
    exposure: 1.0,
    fit: { center: [-2, 0.5, 0], radius: 28 },
    sweep: 30,
  },
};

// Default time used for each still.
export const STILL_T = { storm: 0, where: 0, problems: 0, map: 6, dawn: 0 };

function camFromSpec(c) {
  return { ...c, target: new THREE.Vector3(...c.target) };
}

function mixCam(a, b, k) {
  // interpolate on a sphere around a moving target: a rising, swinging move
  return {
    target: a.target.clone().lerp(b.target, k),
    dist: Math.exp(lerp(Math.log(a.dist), Math.log(b.dist), k)),
    el: lerp(a.el, b.el, k),
    az: lerp(a.az, b.az, k),
    fov: lerp(a.fov, b.fov, k),
    aperture: lerp(a.aperture, b.aperture, k),
    shift: [lerp(a.shift[0], b.shift[0], k), lerp(a.shift[1], b.shift[1], k)],
  };
}

export function cameraPose(c) {
  const el = THREE.MathUtils.degToRad(c.el), az = THREE.MathUtils.degToRad(c.az);
  const dir = new THREE.Vector3(Math.cos(el) * Math.sin(az), Math.sin(el), Math.cos(el) * Math.cos(az));
  return { position: c.target.clone().addScaledVector(dir, c.dist), target: c.target.clone() };
}

// Map motion timeline (6 s): camera where -> map; threads draw; pins drop;
// trucks leave along their threads.
export const MAP_TIMING = {
  cam: [0.0, 5.4],
  thread: { orange: [0.9, 4.9], cobalt: [0.7, 4.7], green: [1.1, 5.1] },
  truck: [1.6, 6.0],
  truckDist: 3.9,
  pinDrop: 0.42,
};

// Apply the full scene state for (beat, t). Returns render settings.
export function applyState(S, beat, t) {
  const B = BEATS[beat];
  const W = S.world;
  const showVillage = beat !== 'problems';
  W.village.visible = showVillage;
  S.plinths.visible = beat === 'problems';
  S.storm.visible = beat === 'storm';
  W.poleSnapped.visible = beat === 'storm';
  W.poleIntact.visible = beat !== 'storm';
  for (const r of S.routes) r.group.visible = beat === 'map';
  S.trucks.forEach((tk, i) => { tk.visible = showVillage; park(tk, i); });

  let cam = camFromSpec(B.camera);
  let fit = { center: new THREE.Vector3(...B.fit.center), radius: B.fit.radius };

  if (beat === 'storm') {
    S.trucks.forEach((tk, i) => { tk.visible = i === 0; });
    const x = W.poleXs[W.stormIndex];
    S.trucks[0].position.set(x + 1.95, STREET_Y, 0.36);
    S.trucks[0].rotation.set(0, -Math.PI / 2 - 0.06, 0);
  }

  if (beat === 'dawn') {
    // five trucks driving out of the depot in a line along the main road
    const lead = -4.2 + t * 0.9;
    S.trucks.forEach((tk, i) => {
      tk.position.set(lead - i * 2.05, STREET_Y, 0.38);
      tk.rotation.set(0, Math.PI / 2, 0);
    });
  }

  if (beat === 'map') {
    const T = MAP_TIMING;
    const kc = easeInOutCubic(seg(t, T.cam[0], T.cam[1]));
    const from = camFromSpec(BEATS.where.camera);
    cam = mixCam(from, cam, kc);
    // light fit grows with the view
    const f0 = BEATS.where.fit;
    fit = {
      center: new THREE.Vector3(...f0.center).lerp(new THREE.Vector3(...B.fit.center), kc),
      radius: lerp(f0.radius, B.fit.radius, kc),
    };
    for (const r of S.routes) {
      const [a, b] = T.thread[r.key];
      const p = easeInOutSine(seg(t, a, b));
      setThreadProgress(r, p);
      for (const pin of r.pins) {
        const tReach = a + (b - a) * invEaseInOutSine(pin.u);
        const k = seg(t, tReach - 0.05, tReach - 0.05 + T.pinDrop);
        pin.group.visible = k > 0;
        const drop = 1 - easeOutCubic(k);
        pin.group.position.copy(pin.group.userData.base).add(new THREE.Vector3(0, drop * 2.2, 0));
      }
      const tk = S.trucks[r.truck];
      const d = T.truckDist * easeInOutSine(seg(t, T.truck[0], T.truck[1]));
      placeOnCurve(tk, r, d);
    }
  }
  return { B, cam, fit };
}

function invEaseInOutSine(y) {
  // inverse of easeInOutSine on [0,1]
  return Math.acos(1 - 2 * y) / Math.PI;
}
