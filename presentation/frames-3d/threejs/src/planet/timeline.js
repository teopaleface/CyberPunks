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
  lightsOff: [3.297, 4.087, 4.876],
  poleFall: 4.087,
  cloudIn: [2.5, 3.9],
  cloudOut: [4.95, 5.75],
  labels: [5.642, 6.432, 7.221],
  question: 7.987,
  whip: [9.30, 9.62],
  click: 9.543,
  unroll: [9.264, 9.474],
  rollUp: [11.099, 11.75],
  ribbons: [11.099, 15.0],
  pins: [12.655, 13.444, 14.210, 15.0],
  focus: [16.556, 17.6],
  approve: 18.901,
  askPin: [18.95, 19.25],
  turn: [19.2, 20.9],
  sunrise: [20.457, 24.334],
  windowsOn: [21.223, 23.568],
  pullBack: [25.124, 25.89],
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
  // cold open + night: planet right (centre 1400,560; R ~445 px); slow orbit + push
  { t: 0.0, az: -64, el: 46, dist: 5.1, target: [0, 0, 0], fov: 30, ap: 0.02, shift: [-0.458, 0.037] },
  { t: 2.531, az: -40, el: 48, dist: 4.72, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.458, 0.037] },
  { t: 5.642, az: 0, el: 51, dist: 4.64, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.458, 0.037] },
  { t: 7.987, az: 34, el: 53, dist: 4.6, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.458, 0.037] },
  // stillness before the climax: near stop
  { t: 8.9, az: 44, el: 54, dist: 4.58, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.458, 0.037] },
  { t: 9.264, az: 47, el: 55, dist: 4.56, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.458, 0.037] },
  // the drop: inside the 0.2 s zoom-through exit the camera whips to top-down while the map unrolls
  { t: 9.474, az: 90, el: 89.5, dist: 7.6, target: [0, 1.0, 0], fov: 30, ap: 0.0, shift: [0, 0] },
  { t: 11.099, az: 90, el: 89.5, dist: 7.6, target: [0, 1.0, 0], fov: 30, ap: 0.0, shift: [0, 0] },
  // inverse zoom arrival: the map rolls back up; routes framing (planet centre 1360,775)
  { t: 11.9, az: 150, el: 76, dist: 4.56, target: [0, 0, 0], fov: 30, ap: 0.02, shift: [-0.417, 0.435] },
  { t: 15.0, az: 178, el: 76, dist: 4.56, target: [0, 0, 0], fov: 30, ap: 0.02, shift: [-0.417, 0.435] },
  { t: 16.556, rel: 'unsure_house', az: 0, el: 0, dist: 4.56, target: [0, 0, 0], fov: 30, ap: 0.025, shift: [-0.377, 0.366], solveHouse: true },
  // CUT 16.556 (rack focus): close on the unsure house, same screen spot (1290,760)
  { t: 16.556, cut: true, rel: 'unsure_house', az: 14, el: -34, dist: 1.85, target: 'unsure_house', fov: 30, ap: 0.035, shift: [-0.344, 0.407] },
  { t: 20.457, rel: 'unsure_house', az: 26, el: -37, dist: 1.6, target: 'unsure_house', fov: 30, ap: 0.035, shift: [-0.344, 0.407] },
  // CUT 20.457 (cut-the-curve UP): dawn, huge horizon at the bottom
  { t: 20.457, cut: true, az: 296, el: 14, dist: 2.25, target: [0, 0, 0], fov: 30, ap: 0.02, shift: [0.0625, 2.06] },
  { t: 25.124, az: 318, el: 15, dist: 2.3, target: [0, 0, 0], fov: 30, ap: 0.02, shift: [0.0625, 2.06] },
  // pull into the orange dot above the wordmark (960,402)
  { t: 25.89, az: 326, el: 22, dist: 33.6, target: [0, 0, 0], fov: 30, ap: 0.0, shift: [0, -0.256] },
  { t: 26.4, az: 330, el: 24, dist: 91, target: [0, 0, 0], fov: 30, ap: 0.0, shift: [0, -0.256] },
  { t: 30.0, az: 331, el: 24, dist: 92, target: [0, 0, 0], fov: 30, ap: 0.0, shift: [0, -0.256] },
];

// Rack-focus spike around the 16.556 cut: 0 -> 1 (power2.in) -> 0 (power2.out, longer)
export function rackSpike(t) {
  const a = 16.556 - 0.3, c = 16.556, b = 16.556 + 0.42;
  if (t <= a || t >= b) return 0;
  if (t < c) { const x = (t - a) / (c - a); return x * x; }
  const x = (t - c) / (b - c); return 1 - (1 - (1 - x) * (1 - x));
}
// vertical image offset (fraction of half frame, + = content down) for the UP cut at 20.457
export function upCutShift(t) {
  const c = 20.457;
  if (t > c - 0.34 && t < c) { const x = (t - (c - 0.34)) / 0.34; return -0.24 * x * x * x; }
  if (t >= c && t < c + 0.42) { const x = (t - c) / 0.42; return 0.24 * Math.pow(1 - x, 4); }
  return 0;
}

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

export function makeCameraTrack(resolveTarget, resolveNormal, solveHouseAz) {
  // split keys into segments at hard cuts
  const segs = [];
  let cur = [];
  for (const k of CAM_KEYS) {
    if (k.cut && cur.length) { segs.push(cur); cur = []; }
    cur.push(k);
  }
  segs.push(cur);
  const tracks = segs.map((keys) => {
    const xs = keys.map((k) => k.t);
    const tg = keys.map((k) => (typeof k.target === 'string' ? resolveTarget(k.target) : k.target));
    const azs = [], els = [];
    for (const k of keys) {
      if (k.solveHouse) { const s = solveHouseAz(k); azs.push(s.az); els.push(s.el); }
      else if (k.rel) {
        const n = resolveNormal(k.rel);
        azs.push((Math.atan2(n[0], n[2]) * 180) / Math.PI + k.az);
        els.push(Math.min(80, (Math.asin(n[1]) * 180) / Math.PI + k.el));
      } else { azs.push(k.az); els.push(k.el); }
    }
    for (let i = 1; i < azs.length; i++) { while (azs[i] - azs[i - 1] > 180) azs[i] -= 360; while (azs[i] - azs[i - 1] < -180) azs[i] += 360; }
    const one = xs.length === 1;
    const P = (ys) => (one ? () => ys[0] : pchip(xs, ys));
    return {
      t0: xs[0], t1: xs[xs.length - 1],
      az: P(azs), el: P(els), ld: P(keys.map((k) => Math.log(k.dist))),
      tx: P(tg.map((v) => v[0])), ty: P(tg.map((v) => v[1])), tz: P(tg.map((v) => v[2])),
      fov: P(keys.map((k) => k.fov)), ap: P(keys.map((k) => k.ap)),
      sx: P(keys.map((k) => k.shift[0])), sy: P(keys.map((k) => k.shift[1])),
    };
  });
  return (t) => {
    let ch = tracks[0];
    for (const tr of tracks) if (t >= tr.t0) ch = tr;
    const az = (ch.az(t) * Math.PI) / 180, el = (ch.el(t) * Math.PI) / 180, dist = Math.exp(ch.ld(t));
    const target = [ch.tx(t), ch.ty(t), ch.tz(t)];
    const pos = [target[0] + dist * Math.cos(el) * Math.sin(az), target[1] + dist * Math.sin(el), target[2] + dist * Math.cos(el) * Math.cos(az)];
    const sp = rackSpike(t);
    return { pos, target, fov: ch.fov(t) * (1 + 0.06 * sp), aperture: Math.max(0, ch.ap(t)) + 0.05 * sp, focusMul: 1 - 0.42 * sp,
      shift: [ch.sx(t), ch.sy(t) + upCutShift(t)], dist };
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
  const storm = seg(t, 3.0, 4.0) * (1 - seg(t, 5.0, 6.0));
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
