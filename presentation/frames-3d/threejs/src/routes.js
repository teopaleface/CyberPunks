// Route threads, map pins and truck parking for the "map" beat.
import * as THREE from 'three';
import { STREET_Y, GROUND, YARD_Y, DEPOT, buildTruck } from './world.js';
import { G, Bucket, mat } from './geo.js';

export const THREAD_R = 0.068;
const LANE_Y = STREET_Y + THREAD_R * 0.92;

// Five parked trucks in the depot yard, nose towards the gate (+z).
export const PARKED = [0, 1, 2, 3, 4].map((i) => ({
  x: -22.6 + i * 1.3,
  z: -3.55,
  ry: [0.13, -0.07, 0.04, -0.1, 0.15][i],
}));

// Polyline with per-corner fillet radius -> CurvePath.
function filletPath(pts) {
  const path = new THREE.CurvePath();
  const P = pts.map((p) => new THREE.Vector3(p[0], LANE_Y, p[1]));
  let prev = P[0].clone();
  for (let i = 1; i < P.length - 1; i++) {
    const a = P[i - 1], b = P[i], c = P[i + 1];
    const d1 = b.clone().sub(a), d2 = c.clone().sub(b);
    const r = Math.min(pts[i][2] ?? 0.6, d1.length() * 0.45, d2.length() * 0.45);
    const p1 = b.clone().addScaledVector(d1.normalize(), -r);
    const p2 = b.clone().addScaledVector(d2.normalize(), r);
    if (p1.distanceTo(prev) > 1e-4) path.add(new THREE.LineCurve3(prev, p1));
    path.add(new THREE.QuadraticBezierCurve3(p1, b.clone(), p2));
    prev = p2;
  }
  path.add(new THREE.LineCurve3(prev, P[P.length - 1].clone()));
  return path;
}

const ROUTES = [
  {
    key: 'orange', truck: 3, lane: -0.42,
    via: (t) => [[t.x, t.z], [t.x - 0.03, t.z + 1.0, 0.5], [-18.9, -1.55, 0.5], [-18.9, -0.42, 0.42], [-4.5, -0.42, 0.55], [-4.5, -9.0, 0.6]],
    tail: { axis: 'x', c: -9.0, from: -4.5 },
    pins: [{ street: 'C2', near: -5.2 }, { street: 'N', near: -0.5 }, { street: 'N', near: 5.5 }, { street: 'N', near: 10.5 }],
  },
  {
    key: 'cobalt', truck: 2, lane: 0,
    via: (t) => [[t.x, t.z], [t.x, t.z + 1.0, 0.5], [-19.45, -1.5, 0.5], [-19.45, 0.0, 0.95]],
    tail: { axis: 'x', c: 0.0, from: -19.45 },
    pins: [{ street: 'M', near: -9.0 }, { street: 'M', near: 2.6 }, { street: 'M', near: 10.5 }, { street: 'M', near: 19.0 }],
  },
  {
    key: 'green', truck: 1, lane: 0.42,
    via: (t) => [[t.x, t.z], [t.x + 0.04, t.z + 1.0, 0.5], [-20.0, -1.45, 0.5], [-20.0, 0.42, 1.5], [4.0, 0.42, 0.55], [4.0, 9.0, 0.6]],
    tail: { axis: 'x', c: 9.0, from: 4.0 },
    pins: [{ street: 'C3', near: 4.8 }, { street: 'S', near: -0.8 }, { street: 'S', near: -6.8 }],
  },
];

function houseU(h) {
  return h.alongX ? h.front.x : h.front.z;
}

export function buildRoutes(world, mats) {
  const used = new Set();
  const routes = [];
  for (const R of ROUTES) {
    const tk = PARKED[R.truck];
    const fwd = new THREE.Vector3(Math.sin(tk.ry), 0, Math.cos(tk.ry));
    const tpos = { x: tk.x, z: tk.z };
    const pts = R.via(tpos);
    pts[1] = [tk.x + fwd.x * 1.0, tk.z + fwd.z * 1.0, 0.5];
    // choose pin houses
    const pinHouses = R.pins.map((p) => {
      let best = null, bd = 1e9;
      for (const h of world.houses) {
        if (h.street !== p.street || used.has(h)) continue;
        const d = Math.abs(houseU(h) - p.near);
        if (d < bd) { bd = d; best = h; }
      }
      used.add(best);
      return best;
    });
    // extend the tail to just past the last house
    const last = pinHouses[pinHouses.length - 1];
    const lu = houseU(last);
    if (R.tail) {
      const dir = Math.sign(lu - R.tail.from) || 1;
      const endU = lu + dir * 0.9;
      pts.push(R.tail.axis === 'x' ? [endU, R.tail.c] : [R.tail.c, endU]);
    }
    const curve = filletPath(pts);
    const L = curve.getLength();
    const segs = Math.ceil(L / 0.035);
    const radial = 12;
    const tube = new THREE.TubeGeometry(curve, segs, THREAD_R, radial, false);
    const mesh = new THREE.Mesh(tube, mats.thread[R.key]);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    const capS = new THREE.Mesh(G.sphere(THREAD_R, 20, 14), mats.thread[R.key]);
    const capE = new THREE.Mesh(G.sphere(THREAD_R, 20, 14), mats.thread[R.key]);
    for (const c of [capS, capE]) { c.castShadow = true; c.receiveShadow = true; }
    // pins: needle into the roof ridge, coloured round head
    const samples = 800;
    const table = [];
    for (let i = 0; i <= samples; i++) table.push(curve.getPointAt(i / samples));
    const pins = pinHouses.map((h) => {
      const target = h.front;
      let bi = 0, bd = 1e9;
      table.forEach((p, i) => {
        const d = (p.x - target.x) ** 2 + (p.z - target.z) ** 2;
        if (d < bd) { bd = d; bi = i; }
      });
      const g = new THREE.Group();
      const needleH = 0.78;
      const needle = new THREE.Mesh(G.cyl(0.014, 0.008, needleH, 10), mats.steel);
      needle.position.y = needleH / 2;
      const head = new THREE.Mesh(G.sphere(0.165, 40, 28), mats.pin[R.key]);
      head.position.y = needleH + 0.12;
      for (const m of [needle, head]) { m.castShadow = true; m.receiveShadow = true; }
      g.add(needle, head);
      g.userData.base = h.pinTop.clone().add(new THREE.Vector3(0, -0.08, 0));
      g.position.copy(g.userData.base);
      return { group: g, u: bi / samples, house: h };
    });
    const grp = new THREE.Group();
    grp.add(mesh, capS, capE, ...pins.map((p) => p.group));
    routes.push({ key: R.key, truck: R.truck, curve, L, tube, mesh, capS, capE, pins, group: grp, segs, radial });
  }
  return routes;
}

// Thread drawn to fraction p (0..1).
export function setThreadProgress(r, p) {
  p = Math.min(1, Math.max(0, p));
  const n = Math.floor(p * r.segs);
  r.tube.setDrawRange(0, n * r.radial * 6);
  r.mesh.visible = n > 0;
  r.capS.visible = n > 0;
  r.capE.visible = n > 0;
  r.capS.position.copy(r.curve.getPointAt(0));
  r.capE.position.copy(r.curve.getPointAt(Math.max(0.0001, n / r.segs)));
}

// Place a truck group at arc length d along a route curve.
export function placeOnCurve(truck, r, d) {
  const u = Math.min(1, Math.max(0, d / r.L));
  const p = r.curve.getPointAt(u);
  const tg = r.curve.getTangentAt(u);
  const inYard = p.z < DEPOT.z1 + 0.05;
  const y = inYard ? YARD_Y : STREET_Y;
  truck.position.set(p.x, y, p.z);
  truck.rotation.set(0, Math.atan2(tg.x, tg.z), 0);
}

export function makeTrucks(mats, n = 5) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const t = buildTruck(mats);
    t.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
    out.push(t);
  }
  return out;
}

export function park(truck, i) {
  const p = PARKED[i];
  truck.position.set(p.x, YARD_Y, p.z);
  truck.rotation.set(0, p.ry, 0);
}
