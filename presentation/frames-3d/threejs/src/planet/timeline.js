// Film timeline for the 3D layer: camera keys, light moods and event times,
// all locked to the POWER beat grid. Pure functions of t (seconds).
export const BEATS = [0.186, 0.975, 1.741, 2.531, 3.297, 4.087, 4.876, 5.642, 6.432, 7.221, 7.987, 8.777,
  9.474, 9.543, 10.309, 11.099, 11.865, 12.655, 13.444, 14.210, 15.0, 15.766, 16.556, 17.345, 18.111, 18.901,
  19.690, 20.457, 21.223, 22.012, 22.779, 23.568, 24.334, 25.124, 25.890, 26.680, 27.446, 28.235, 29.025, 29.791];
export const DROP = 9.474;
export const FPS = 30;
export const DURATION = 30;

export const T = {
  fadeIn: [0.0, 1.2],
  lightsOff: [3.297, 4.087, 4.876, 5.642],
  poleFall: 4.087,
  cloudIn: [2.6, 4.2],
  cloudOut: [8.4, 9.4],
  labels: [6.432, 7.221, 7.987],
  question: 8.777,
  whip: [9.30, 9.62],
  click: 9.543,
  unroll: [9.543, 9.98],
  rollUp: [10.309, 11.099],
  ribbons: [11.099, 15.0],
  pins: [12.655, 13.444, 14.210, 15.0],
  focus: [16.556, 17.6],
  approve: 18.901,
  askPin: [18.95, 19.45],
  turn: [19.2, 20.9],
  sunrise: [20.457, 24.334],
  windowsOn: [21.223, 23.568],
  pullBack: [25.890, 27.6],
};

const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const seg = (t, a, b) => clamp01((t - a) / (b - a));
export const ease = {
  inOutCubic: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outCubic: (x) => 1 - Math.pow(1 - x, 3),
  inCubic: (x) => x * x * x,
  inOutQuart: (x) => (x < 0.5 ? 8 * x ** 4 : 1 - Math.pow(-2 * x + 2, 4) / 2),
  outQuart: (x) => 1 - Math.pow(1 - x, 4),
  inOutSine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
  outBack: (x) => { const c1 = 1.5, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
};

// Camera keys: az/el in degrees (az 0 = camera on +z, 90 = on +x), dist in
// planet radii, target [x,y,z] in planet units, fov (vertical, deg),
// aperture (lens radius), shift [x,y] (fraction of half frame; + moves the
// subject left/down), focus: 'target' or a named anchor.
// Interpolated with monotone cubic Hermite per channel: smooth, no overshoot.
export const CAM_KEYS = [
  { t: 0.0, az: -40, el: 50, dist: 12.5, target: [0, 0.1, 0], fov: 30, ap: 0.02, shift: [0, 0] },
  { t: 1.9, az: -28, el: 51, dist: 9.6, target: [0, 0.12, 0], fov: 30, ap: 0.025, shift: [0, 0] },
  { t: 3.3, az: -10, el: 52, dist: 7.4, target: [0, 0.15, 0], fov: 30, ap: 0.03, shift: [-0.22, 0.0] },
  { t: 6.4, az: 22, el: 52, dist: 6.1, target: [0.05, 0.2, 0], fov: 30, ap: 0.03, shift: [-0.12, -0.04] },
  { t: 9.05, az: 96, el: 55, dist: 5.9, target: [0.05, 0.2, 0], fov: 30, ap: 0.03, shift: [0, 0.14] },
  { t: 9.30, az: 128, el: 68, dist: 6.2, target: [0.0, 0.5, 0], fov: 30, ap: 0.02, shift: [0, 0] },
  { t: 9.62, az: 180, el: 89.5, dist: 7.6, target: [0, 1.0, 0], fov: 30, ap: 0.0, shift: [0.36, 0.02] },
  { t: 10.309, az: 180, el: 89.5, dist: 7.6, target: [0, 1.0, 0], fov: 30, ap: 0.0, shift: [0.36, 0.02] },
  { t: 11.30, az: 196, el: 56, dist: 5.8, target: [0, 0.35, 0], fov: 30, ap: 0.02, shift: [-0.3, -0.06] },
  { t: 16.556, az: 252, el: 52, dist: 5.5, target: [0, 0.3, 0], fov: 30, ap: 0.025, shift: [-0.3, -0.06] },
  { t: 17.6, rel: 'unsure_house', az: 18, el: -36, dist: 1.7, target: 'unsure_house', fov: 30, ap: 0.035, shift: [0.34, 0.06] },
  { t: 20.457, rel: 'unsure_house', az: 30, el: -38, dist: 1.6, target: 'unsure_house', fov: 30, ap: 0.035, shift: [0.34, 0.06] },
  { t: 21.6, az: 300, el: 21, dist: 5.4, target: [0, 0.25, 0], fov: 30, ap: 0.025, shift: [0, 0.6] },
  { t: 25.89, az: 326, el: 23, dist: 5.1, target: [0, 0.25, 0], fov: 30, ap: 0.025, shift: [0, 0.6] },
  { t: 27.6, az: 334, el: 24, dist: 90, target: [0, 0, 0], fov: 30, ap: 0.0, shift: [0, -0.445] },
  { t: 30.0, az: 335, el: 24, dist: 96, target: [0, 0, 0], fov: 30, ap: 0.0, shift: [0, -0.445] },
];

function pchip(xs, ys) {
  const n = xs.length;
  const h = [], d = [], m = new Array(n).fill(0);
  for (let i = 0; i < n - 1; i++) { h.push(xs[i + 1] - xs[i]); d.push((ys[i + 1] - ys[i]) / h[i]); }
  for (let i = 1; i < n - 1; i++) {
    if (d[i - 1] * d[i] <= 0) m[i] = 0;
    else {
      const w1 = 2 * h[i] + h[i - 1], w2 = h[i] + 2 * h[i - 1];
      m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i]);
    }
  }
  return (x) => {
    if (x <= xs[0]) return ys[0];
    if (x >= xs[n - 1]) return ys[n - 1];
    let i = 0;
    while (x > xs[i + 1]) i++;
    const t = (x - xs[i]) / h[i];
    const t2 = t * t, t3 = t2 * t;
    return (2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i] + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1];
  };
}

export function makeCameraTrack(resolveTarget, resolveNormal) {
  const xs = CAM_KEYS.map((k) => k.t);
  // keys with rel: az/el are offsets from the anchor's surface normal
  const azs = [], els = [];
  for (const k of CAM_KEYS) {
    if (k.rel) {
      const n = resolveNormal(k.rel);
      azs.push((Math.atan2(n[0], n[2]) * 180) / Math.PI + k.az);
      els.push(Math.min(80, (Math.asin(n[1]) * 180) / Math.PI + k.el));
    } else { azs.push(k.az); els.push(k.el); }
  }
  for (let i = 1; i < azs.length; i++) { while (azs[i] - azs[i - 1] > 180) azs[i] -= 360; while (azs[i] - azs[i - 1] < -180) azs[i] += 360; }
  const tg = CAM_KEYS.map((k) => (typeof k.target === 'string' ? resolveTarget(k.target) : k.target));
  const ch = {
    az: pchip(xs, azs),
    el: pchip(xs, els),
    ld: pchip(xs, CAM_KEYS.map((k) => Math.log(k.dist))),
    tx: pchip(xs, tg.map((v) => v[0])),
    ty: pchip(xs, tg.map((v) => v[1])),
    tz: pchip(xs, tg.map((v) => v[2])),
    fov: pchip(xs, CAM_KEYS.map((k) => k.fov)),
    ap: pchip(xs, CAM_KEYS.map((k) => k.ap)),
    sx: pchip(xs, CAM_KEYS.map((k) => k.shift[0])),
    sy: pchip(xs, CAM_KEYS.map((k) => k.shift[1])),
  };
  return (t) => {
    const az = (ch.az(t) * Math.PI) / 180, el = (ch.el(t) * Math.PI) / 180, dist = Math.exp(ch.ld(t));
    const target = [ch.tx(t), ch.ty(t), ch.tz(t)];
    const pos = [
      target[0] + dist * Math.cos(el) * Math.sin(az),
      target[1] + dist * Math.sin(el),
      target[2] + dist * Math.cos(el) * Math.cos(az),
    ];
    return { pos, target, fov: ch.fov(t), aperture: Math.max(0, ch.ap(t)), shift: [ch.sx(t), ch.sy(t)], dist };
  };
}

// Blend factor planet(1) <-> flat map(0)
export function blendAt(t) {
  if (t < T.unroll[0]) return 1;
  if (t < T.rollUp[0]) return 1 - ease.inOutCubic(seg(t, T.unroll[0], T.unroll[1]));
  return ease.inOutCubic(seg(t, T.rollUp[0], T.rollUp[1]));
}

// Light mood: returns { key, sky, env, sunUp }
export function lightAt(t) {
  const sun = ease.inOutSine(seg(t, T.sunrise[0], T.sunrise[1]));
  const storm = seg(t, 3.0, 4.2) * (1 - seg(t, 8.6, 9.6));
  const nightKey = 2.3 - storm * 0.7;
  return {
    sun,
    moon: { kelvin: 8200, intensity: nightKey * (1 - sun), az: -40, el: 42 },
    sunKey: { kelvin: 2900, intensity: 4.6 * sun },
    sky: { kelvin: 11000 - sun * 3500, intensity: 0.95 + sun * 0.3 - storm * 0.2, zenith: 0.5 },
    env: 0.05 + sun * 0.05,
    exposure: 1.45 - sun * 0.2,
  };
}
