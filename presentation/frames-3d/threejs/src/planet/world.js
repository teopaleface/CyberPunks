// Planet Daybreak: the Banat village laid out on a flat disc (old units,
// 1 unit = 5 m, ground at y = 0, north pole of the planet = flat origin),
// then wrapped onto a sphere of radius 1 by the Painter's bend.
import * as THREE from 'three';
import { mulberry32, hash1, valueNoise3 } from '../prng.js';
import { G, mat, extrude, tubeAlong, sagPoints } from '../geo.js';
import { gableVolume } from '../world.js';
import { Painter, S, PLANET_R } from './painter.js';

export const SEED = 20261107;
export const PPC = { navy: 0x000f1e, orange: 0xfa4616, cyan: 0x00a3e0, blue: 0x163fe8, white: 0xf5f7fa };
export const VILLAGE_R = 11.2; // houses inside this flat radius
export const EDGE_R = 12.8; // grass ends, mossy planet side begins
export const POLE_R = Math.PI / S; // flat radius of the south pole

const C = (hex) => new THREE.Color(hex);
export const PALETTE = {
  paint: { group: 'paint', color: C(0xffffff) },
  wall: { group: 'paint', color: C(0xeee8dd) },
  roof: { group: 'paint', color: C(0xb5523a) },
  socle: { group: 'paint', color: C(0x9b8f80) },
  frame: { group: 'paint', color: C(0x3e4231) },
  glass: { group: 'glass', color: C(0x1d2328) },
  wood: { group: 'paint', color: C(0x5a4030) },
  fence: { group: 'paint', color: C(0x6b4c36) },
  concrete: { group: 'paint', color: C(0xa7a59f) },
  wire: { group: 'paint', color: C(0x2b2a28) },
  trunk: { group: 'paint', color: C(0x5b4636) },
  leaf: { group: 'paint', color: C(0x4e6b35) },
  grass: { group: 'ground', color: C(0x6c8a45) },
  dirt: { group: 'ground', color: C(0x9c8565) },
  asphalt: { group: 'ground', color: C(0x5d5a55) },
  gravel: { group: 'ground', color: C(0x9a958c) },
  soil: { group: 'ground', color: C(0x5a4a3a) },
  stalk: { group: 'paint', color: C(0x4f6a2c) },
  petal: { group: 'paint', color: C(0xe8b32a) },
  seed: { group: 'paint', color: C(0x4a3320) },
  solar: { group: 'solar', color: C(0x1c2a4a) },
  metal: { group: 'paint', color: C(0xb9bbbd) },
};

// --------------------------------------------------------------------------
// Roads (flat polylines, old units)
// --------------------------------------------------------------------------
export const R3J = [-3.6, -2.6];
export const R4J = [5.0, 0.9];
export const ROADS = [
  { id: 'R1', kind: 'asphalt', w: 1.5, pts: [[-5.6, -4.5], R3J, [0, 0], R4J, [9.5, 1.4], [13.6, 1.1]] },
  { id: 'R2', kind: 'dirt', w: 1.15, pts: [[0, 0], [0.6, 4.2], [1.2, 8.4], [1.0, 13.4]] },
  { id: 'R3', kind: 'dirt', w: 1.1, pts: [R3J, [-7.4, 0.5], [-10.6, 2.4], [-13.2, 3.3]] },
  { id: 'R4', kind: 'dirt', w: 1.05, pts: [R4J, [6.1, -3.8], [6.8, -8.2], [7.2, -13.0]] },
];
export const DEPOT = { x: -7.45, z: -6.45, yaw: Math.atan2(2.0, 2.1), w: 6.0, d: 4.3 };
export const FIELD = { x: 6.4, z: 7.4, yaw: 0.3, w: 4.4, d: 3.0 };

// polyline helpers -----------------------------------------------------------
export function polyLen(pts) {
  let L = 0;
  for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  return L;
}
export function polyAt(pts, s) {
  for (let i = 1; i < pts.length; i++) {
    const [ax, az] = pts[i - 1], [bx, bz] = pts[i];
    const l = Math.hypot(bx - ax, bz - az);
    if (s <= l || i === pts.length - 1) {
      const u = Math.min(1, Math.max(0, s / l));
      const dx = (bx - ax) / l, dz = (bz - az) / l;
      return { x: ax + (bx - ax) * u, z: az + (bz - az) * u, dx, dz };
    }
    s -= l;
  }
}
// distance from point to polyline
export function polyDist(pts, x, z) {
  let best = 1e9;
  for (let i = 1; i < pts.length; i++) {
    const [ax, az] = pts[i - 1], [bx, bz] = pts[i];
    const vx = bx - ax, vz = bz - az;
    const u = Math.max(0, Math.min(1, ((x - ax) * vx + (z - az) * vz) / (vx * vx + vz * vz)));
    best = Math.min(best, Math.hypot(x - ax - vx * u, z - az - vz * u));
  }
  return best;
}
// rounded (Chaikin) smoothing for gentle hand-laid curves
export function smoothPoly(pts, iters = 3) {
  let p = pts;
  for (let k = 0; k < iters; k++) {
    const o = [p[0]];
    for (let i = 0; i < p.length - 1; i++) {
      const [ax, az] = p[i], [bx, bz] = p[i + 1];
      o.push([ax * 0.75 + bx * 0.25, az * 0.75 + bz * 0.25], [ax * 0.25 + bx * 0.75, az * 0.25 + bz * 0.75]);
    }
    o.push(p[p.length - 1]);
    p = o;
  }
  return p;
}
export function offsetPoly(pts, d) {
  return pts.map((p, i) => {
    const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
    const dx = b[0] - a[0], dz = b[1] - a[1];
    const l = Math.hypot(dx, dz) || 1;
    return [p[0] - (dz / l) * d, p[1] + (dx / l) * d];
  });
}

const OBBs = [];
function obbHit(x, z) {
  for (const o of OBBs) {
    const dx = x - o.x, dz = z - o.z;
    const lx = dx * Math.cos(o.yaw) - dz * Math.sin(o.yaw);
    const lz = dx * Math.sin(o.yaw) + dz * Math.cos(o.yaw);
    if (Math.abs(lx) < o.hw && Math.abs(lz) < o.hd) return true;
  }
  return false;
}
function addObb(x, z, yaw, hw, hd) { OBBs.push({ x, z, yaw, hw, hd }); }
function roadClear(x, z, pad) {
  return ROADS.every((r) => polyDist(SMOOTH[r.id], x, z) > r.w / 2 + pad);
}
const SMOOTH = Object.fromEntries(ROADS.map((r) => [r.id, smoothPoly(r.pts, 3)]));
export { SMOOTH };

// world point of a local (lx, lz) offset in an object's frame
function toWorld(x, z, yaw, lx, lz) {
  return [x + lx * Math.cos(yaw) + lz * Math.sin(yaw), z - lx * Math.sin(yaw) + lz * Math.cos(yaw)];
}

// --------------------------------------------------------------------------
export function buildPlanet() {
  OBBs.length = 0;
  const rng = mulberry32(SEED);
  const P = new Painter(PALETTE);
  const houses = [];
  const anchors = {};

  // reserve depot, field and roads
  addObb(DEPOT.x, DEPOT.z, DEPOT.yaw, DEPOT.w / 2 + 0.5, DEPOT.d / 2 + 0.5);
  addObb(FIELD.x, FIELD.z, FIELD.yaw, FIELD.w / 2 + 0.3, FIELD.d / 2 + 0.3);

  // ---------------- ground: polar grid disc out to the south pole ---------
  {
    P.anchor = null;
    const rings = 150, segs = 300;
    const pos = [], col = [];
    const grass = C(0x7f9f4c), dry = C(0xb3a862), moss = C(0x5a6d36), soil = C(0x6a5440), deep = C(0x4a3b2e);
    const ringR = (i) => {
      const u = i / rings;
      return POLE_R * (u < 0.55 ? (u / 0.55) * 0.55 : u); // even spacing (kept simple)
    };
    const vtx = (i, j) => {
      const r = ringR(i), a = (j / segs) * Math.PI * 2;
      const x = r * Math.cos(a), z = r * Math.sin(a);
      // organic bumps on the planet's side and underside
      const side = THREE.MathUtils.smoothstep(r, EDGE_R - 1, EDGE_R + 3);
      const nz = valueNoise3(x * 0.35, 0, z * 0.35, 9) * 0.5 + valueNoise3(x * 1.3, 1, z * 1.3, 4) * 0.25;
      const y = side * nz * 0.9 + (r > EDGE_R ? nz * 0.15 : 0);
      // colour: grass with dry patches -> moss -> soil
      const g = grass.clone().lerp(dry, Math.max(0, valueNoise3(x * 0.4, 3, z * 0.4, 2)) * 0.55);
      g.offsetHSL(0, 0, (hash1(i * 7919 + j * 104729) - 0.5) * 0.03);
      const k1 = THREE.MathUtils.smoothstep(r, EDGE_R - 1.5, EDGE_R + 1.5);
      const k2 = THREE.MathUtils.smoothstep(r, EDGE_R + 2, EDGE_R + 7);
      const k3 = THREE.MathUtils.smoothstep(r, EDGE_R + 8, POLE_R);
      const c = g.lerp(moss, k1).lerp(soil, k2 * (0.6 + 0.4 * Math.max(0, nz))).lerp(deep, k3);
      return { p: [x, y, z], c };
    };
    const grid = [];
    for (let i = 0; i <= rings; i++) { grid.push([]); for (let j = 0; j <= segs; j++) grid[i].push(vtx(i, j)); }
    const push = (v) => { pos.push(...v.p); col.push(v.c.r, v.c.g, v.c.b); };
    for (let i = 0; i < rings; i++) for (let j = 0; j < segs; j++) {
      const a = grid[i][j], b = grid[i][j + 1], c = grid[i + 1][j + 1], d = grid[i + 1][j];
      push(a); push(c); push(b); push(a); push(d); push(c);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    // keep per-vertex colours by adding manually
    P.tint('grass');
    const before = P.groups.get('ground')?.parts.length || 0;
    P.add(g);
    const part = P.groups.get('ground').parts[before];
    part.attributes.color.array.set(col);
  }

  // ---------------- roads, yard ------------------------------------------
  const strip = (pts, w, y, kind, seed) => {
    const sm = pts.length > 8 ? pts : smoothPoly(pts, 3);
    const dense = [];
    const L = polyLen(sm);
    for (let s = 0; s <= L; s += 0.12) dense.push(polyAt(sm, s));
    const pos = [], col = [];
    const base = C(PALETTE[kind].color.getHex());
    const across = 4;
    const ring = dense.map((p, i) => {
      const row = [];
      for (let k = 0; k <= across; k++) {
        const u = k / across - 0.5;
        const x = p.x - p.dz * u * w, z = p.z + p.dx * u * w;
        const n = valueNoise3(x * 1.7, seed, z * 1.7, 7);
        const c = base.clone().offsetHSL(0, 0, n * 0.05 + (hash1(i * 31 + k + seed * 1000) - 0.5) * 0.025);
        if (kind === 'dirt') c.lerp(C(0x7d8a4a), Math.max(0, Math.abs(u) * 2 - 0.75) * 0.9 * (0.5 + n)); // grassy verges
        row.push({ p: [x, y + (kind === 'dirt' ? Math.abs(n) * 0.01 : 0), z], c });
      }
      return row;
    });
    const push = (v) => { pos.push(...v.p); col.push(v.c.r, v.c.g, v.c.b); };
    for (let i = 0; i < ring.length - 1; i++) for (let k = 0; k < across; k++) {
      const a = ring[i][k], b = ring[i][k + 1], c = ring[i + 1][k + 1], d = ring[i + 1][k];
      push(a); push(b); push(c); push(a); push(c); push(d);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    P.anchor = null;
    P.tint(kind);
    const before = P.groups.get('ground')?.parts.length || 0;
    P.add(g);
    P.groups.get('ground').parts[before].attributes.color.array.set(col);
  };
  ROADS.forEach((r, i) => strip(SMOOTH[r.id], r.w, 0.035 + i * 0.002, r.kind, i + 1));
  // depot yard (gravel), as a short wide strip
  {
    const [ax, az] = toWorld(DEPOT.x, DEPOT.z, DEPOT.yaw, 0, -DEPOT.d / 2);
    const [bx, bz] = toWorld(DEPOT.x, DEPOT.z, DEPOT.yaw, 0, DEPOT.d / 2 + 0.3);
    const pts = [];
    for (let k = 0; k <= 12; k++) pts.push([ax + (bx - ax) * (k / 12), az + (bz - az) * (k / 12)]);
    strip(pts, DEPOT.w, 0.045, 'gravel', 9);
  }

  // ---------------- houses along the roads --------------------------------
  const roadOrder = ['R1', 'R2', 'R3', 'R4'];
  let hid = 0;
  for (const id of roadOrder) {
    const road = ROADS.find((r) => r.id === id);
    const sm = SMOOTH[id];
    const L = polyLen(sm);
    for (const side of [-1, 1]) {
      let s = 1.2 + rng.range(0, 0.8);
      while (s < L - 1.0) {
        const p = polyAt(sm, s);
        const nx = -p.dz * side, nz = p.dx * side; // towards the house side
        const W = rng.range(1.4, 1.8), D = rng.range(2.3, 3.0), H = rng.range(0.56, 0.64);
        const setback = road.w / 2 + rng.range(0.4, 0.7);
        const hx = p.x + nx * setback, hz = p.z + nz * setback;
        const yaw = Math.atan2(-nx, -nz) + rng.range(-0.06, 0.06);
        const porch = rng.chance(0.7) ? 0.3 : 0;
        // footprint check (house body extends along +n)
        let ok = Math.hypot(hx, hz) < VILLAGE_R;
        const pts = [];
        for (let a = -1; a <= 1; a += 0.5) for (let b = 0; b <= 1; b += 0.25) {
          pts.push(toWorld(hx, hz, yaw, a * (W / 2 + 0.25 + (a > 0 ? porch : 0)), -b * (D + 0.25) + 0.15));
        }
        for (const [x, z] of pts) {
          if (!ok) break;
          if (obbHit(x, z) || !roadClear(x, z, 0.25) || Math.hypot(x, z) > VILLAGE_R + 0.8) ok = false;
        }
        if (ok) {
          const [cx, cz] = toWorld(hx, hz, yaw, porch / 2, -D / 2);
          addObb(cx, cz, yaw, W / 2 + 0.25 + porch / 2, D / 2 + 0.25);
          P.anchor = [hx, hz];
          P.house = hid;
          const M = mat(hx, 0, hz, 0, yaw, 0);
          const wall = C(0xeee8dd).offsetHSL(rng.range(-0.01, 0.02), rng.range(-0.05, 0.05), rng.range(-0.03, 0.01));
          const roof = C(0xb5523a).offsetHSL(rng.range(-0.015, 0.02), rng.range(-0.08, 0.05), rng.range(-0.06, 0.04));
          PALETTE.wall.color.copy(wall);
          PALETTE.roof.color.copy(roof);
          const n = W > 1.7 ? 3 : 2;
          const gap = W / (n + 0.8);
          const front = [];
          for (let k = 0; k < n; k++) front.push([(k - (n - 1) / 2) * gap, H * 0.55, 0.2, 0.27]);
          const left = [], right = [];
          for (let q = 0.7; q < D - 0.4; q += 0.7) left.push([q, H * 0.55, 0.2, 0.27]);
          for (let q = 0.8; q < D * 0.75; q += 0.8) right.push([q, H * 0.55, 0.2, 0.27]);
          gableVolume(P, M, { W, D, H, porch, porchTo: D * 0.8, front, left, right, chimney: rng.chance(0.65) ? [rng.range(0.3, 0.7), rng.chance(0.5) ? 1 : -1] : null });
          PALETTE.wall.color.set(0xeee8dd);
          PALETTE.roof.color.set(0xb5523a);
          // fence along the front of the yard, beside the house (wooden pickets)
          const fl = rng.range(1.6, 2.6);
          const fs = side * (porch ? 1 : 1);
          void fs;
          P.tint('fence');
          const f0 = toWorld(hx, hz, yaw, W / 2 + porch + 0.5, 0.1), f1 = toWorld(hx, hz, yaw, W / 2 + porch + 0.5 + fl, 0.1);
          if (roadClear(f1[0], f1[1], 0.1) && !obbHit(f1[0], f1[1])) picketFence(P, f0, f1, rng);
          houses.push({ id: hid, x: hx, z: hz, yaw, W, D, H, road: id, side, s, porch, ridge: H + (W / 2) * Math.tan(0.7) });
          hid++;
          s += W + rng.range(1.1, 1.9);
        } else s += 0.45;
      }
    }
  }
  P.house = -1;

  // ---------------- depot: shed with open bays, fence, office -------------
  {
    const { x, z, yaw, w, d } = DEPOT;
    P.anchor = [x, z];
    const M = mat(x, 0, z, 0, yaw, 0);
    // three-bay shed at the back of the yard, open to the front
    P.tint('wall');
    const shW = 5.0, shD = 1.7, shH = 0.95;
    const back = -d / 2 + 0.25;
    P.addLocal(G.rbox(shW, shH, 0.12, 0.01), mat(0, shH / 2, back), M);
    for (const sx of [-shW / 2, -shW / 6, shW / 6, shW / 2]) P.addLocal(G.rbox(0.12, shH, shD, 0.01), mat(sx, shH / 2, back + shD / 2), M);
    P.tint('roof', C(0x9e4e3a));
    P.addLocal(G.rbox(shW + 0.4, 0.06, shD + 0.5, 0.01), mat(0, shH + 0.12, back + shD / 2, -0.12, 0, 0), M);
    P.tint('wood');
    P.addLocal(G.rbox(shW, 0.05, 0.05, 0.005), mat(0, shH - 0.03, back + shD), M);
    // office hut
    P.tint('wall');
    gableVolume(P, new THREE.Matrix4().multiplyMatrices(M, mat(w / 2 - 0.7, 0, -d / 2 + 2.6, 0, -Math.PI / 2, 0)), {
      W: 1.2, D: 1.3, H: 0.62, front: [[0, 0.33, 0.2, 0.26]], left: [[0.65, 0.33, 0.22, 0.26]],
    });
    // fence around the yard with a gate at the front
    P.tint('fence');
    const c = (lx, lz) => toWorld(x, z, yaw, lx, lz);
    picketFence(P, c(-w / 2, -d / 2), c(-w / 2, d / 2), rng);
    picketFence(P, c(w / 2, -d / 2), c(w / 2, d / 2), rng);
    picketFence(P, c(-w / 2, d / 2), c(-1.2, d / 2), rng);
    picketFence(P, c(1.2, d / 2), c(w / 2, d / 2), rng);
    // cable drums and a pole stack
    P.tint('wood');
    for (const [lx, lz] of [[-2.4, 1.2], [-2.0, 1.5]]) {
      P.addLocal(G.cyl(0.2, 0.2, 0.16, 20), mat(lx, 0.2, lz, Math.PI / 2, 0, 0), M);
    }
    P.tint('concrete');
    for (let k = 0; k < 4; k++) P.addLocal(G.cyl(0.035, 0.035, 1.8, 10), mat(2.0, 0.04 + (k > 2 ? 0.065 : 0), 1.4 + (k % 3) * 0.075, 0, 0, Math.PI / 2), M);
    anchors.depot = { x, z, h: 0.4 };
  }

  // ---------------- sunflower field ---------------------------------------
  {
    const { x, z, yaw, w, d } = FIELD;
    let k = 0;
    for (let lz = -d / 2 + 0.2; lz < d / 2; lz += 0.3) {
      for (let lx = -w / 2 + 0.15; lx < w / 2; lx += 0.2) {
        const jx = lx + (hash1(k * 3 + 1) - 0.5) * 0.08, jz = lz + (hash1(k * 3 + 2) - 0.5) * 0.06;
        const [px, pz] = toWorld(x, z, yaw, jx, jz);
        P.anchor = [px, pz];
        const h = 0.34 + hash1(k * 7) * 0.1;
        const M = mat(px, 0, pz, 0, yaw + 0.3 + (hash1(k) - 0.5) * 0.6, 0);
        P.tint('stalk');
        P.addLocal(G.cyl(0.008, 0.011, h, 5), mat(0, h / 2, 0), M);
        P.addLocal(G.box(0.1, 0.006, 0.04), mat(0.03, h * 0.5, 0, 0, 0, 0.4), M);
        P.tint('petal', C(0xe8b32a).offsetHSL((hash1(k * 11) - 0.5) * 0.02, 0, (hash1(k * 13) - 0.5) * 0.06));
        P.addLocal(G.cyl(0.06, 0.06, 0.012, 10), mat(0, h, 0.012, 1.25, 0, 0), M);
        P.tint('seed');
        P.addLocal(G.cyl(0.032, 0.032, 0.016, 10), mat(0, h + 0.004, 0.018, 1.25, 0, 0), M);
        k++;
      }
    }
    P.tint('fence');
    const c = (lx, lz) => toWorld(x, z, yaw, lx, lz);
    picketFence(P, c(-w / 2 - 0.1, -d / 2 - 0.1), c(w / 2 + 0.1, -d / 2 - 0.1), rng, 0.14);
    picketFence(P, c(-w / 2 - 0.1, -d / 2 - 0.1), c(-w / 2 - 0.1, d / 2 + 0.1), rng, 0.14);
  }

  // ---------------- poles + wires along R1 and R2 -------------------------
  const poles = [];
  {
    const addLine = (id, from, to, step, side) => {
      const sm = SMOOTH[id];
      const road = ROADS.find((r) => r.id === id);
      const pts = [];
      for (let s = from; s < Math.min(to, polyLen(sm)); s += step) {
        const p = polyAt(sm, s);
        const off = road.w / 2 + 0.22;
        const x = p.x - p.dz * off * side, z = p.z + p.dx * off * side;
        if (obbHit(x, z)) continue;
        pts.push({ x, z, yaw: Math.atan2(p.dx, p.dz) + Math.PI / 2, road: id, s });
      }
      return pts;
    };
    poles.push(...addLine('R1', 1.2, 30, 2.9, 1));
    poles.push(...addLine('R2', 2.0, 30, 2.8, -1));
  }
  // the pole that snaps in the storm: first R1 pole east of the junction past x = 6
  const stormPole = poles.findIndex((p) => p.road === 'R1' && p.x > 6.5);
  const poleTops = [];
  poles.forEach((p, i) => {
    P.anchor = [p.x, p.z];
    const M = mat(p.x, 0, p.z, 0, p.yaw, 0);
    const H = 1.9;
    const tops = [-0.24, 0, 0.24].map((dx) => new THREE.Vector3(dx, dx === 0 ? H + 0.02 : H - 0.08, 0).applyMatrix4(M));
    poleTops.push(tops);
    if (i === stormPole) return;
    P.tint('concrete');
    P.addLocal(G.cyl(0.03, 0.042, H, 8), mat(0, H / 2, 0), M);
    P.addLocal(G.rbox(0.56, 0.04, 0.04, 0.006), mat(0, H - 0.12, 0), M);
    P.tint('metal');
    for (const dx of [-0.24, 0, 0.24]) P.addLocal(G.cyl(0.013, 0.015, 0.05, 6), mat(dx, dx === 0 ? H - 0.0 : H - 0.1, 0), M);
  });
  // wires between consecutive poles on the same road (skip ones touching the storm pole)
  const wires = [];
  for (let i = 0; i < poles.length - 1; i++) {
    if (poles[i].road !== poles[i + 1].road) continue;
    wires.push({ a: i, b: i + 1, storm: i === stormPole || i + 1 === stormPole });
  }
  anchors.fallen_pole = { x: poles[stormPole].x, z: poles[stormPole].z, h: 0.3 };

  // ---------------- trees: walnut clumps -----------------------------------
  const trees = [];
  const tryTree = (x, z, r) => {
    if (Math.hypot(x, z) > EDGE_R + 1.2) return false;
    if (!roadClear(x, z, r * 0.7 + 0.1) || obbHit(x, z)) return false;
    for (const t of trees) if (Math.hypot(t.x - x, t.z - z) < (t.r + r) * 0.8) return false;
    trees.push({ x, z, r });
    addTree(P, x, z, r, rng);
    addObb(x, z, 0, r * 0.6, r * 0.6);
    return true;
  };
  tryTree(-1.6, 2.3, 1.15);
  tryTree(2.3, -2.1, 1.05);
  for (let k = 0; k < 900 && trees.length < 46; k++) {
    const a = rng.range(0, Math.PI * 2), rr = Math.sqrt(rng.next()) * (EDGE_R + 0.8);
    tryTree(Math.cos(a) * rr, Math.sin(a) * rr, rng.range(0.45, 0.95));
  }

  // ---------------- grass tufts and bushes ---------------------------------
  {
    const tuft = tuftGeom();
    for (let k = 0; k < 2600; k++) {
      const a = rng.range(0, Math.PI * 2), rr = Math.sqrt(rng.next()) * (EDGE_R + 2.5);
      const x = Math.cos(a) * rr, z = Math.sin(a) * rr;
      if (!roadClear(x, z, 0.05) || obbHit(x, z)) continue;
      P.anchor = [x, z];
      const g = C(0x6c8a45).lerp(C(0xa8a058), rng.next() * 0.6).offsetHSL(0, 0, rng.range(-0.06, 0.04));
      P.tint('leaf', g);
      const sc = rng.range(0.6, 1.4);
      P.add(tuft, mat(x, 0.0, z, 0, rng.range(0, 6.28), 0, sc, sc * rng.range(0.8, 1.3), sc));
    }
  }

  // ---------------- special houses (anchors) -------------------------------
  const pick = (road, near) => houses.filter((h) => h.road === road).sort((a, b) => Math.abs(a.s - near) - Math.abs(b.s - near))[0];
  const meterHouse = pick('R3', 5.0);
  const hotHouse = pick('R2', 6.5);
  const unsureHouse = pick('R4', 6.5);
  for (const [key, h] of [['meter', meterHouse], ['hot_roof', hotHouse], ['unsure_house', unsureHouse]]) {
    if (h) anchors[key] = { x: h.x, z: h.z, h: key === 'hot_roof' ? h.ridge : 0.4, house: h.id };
  }
  // meter box on the meter house front + solar panels on the hot roof
  if (meterHouse) {
    const h = meterHouse;
    P.anchor = [h.x, h.z];
    const M = mat(h.x, 0, h.z, 0, h.yaw, 0);
    P.tint('metal', C(0xd8d6cf));
    P.addLocal(G.rbox(0.16, 0.2, 0.06, 0.008), mat(h.W / 2 - 0.2, 0.38, 0.065), M);
    P.tint('frame', C(0x2b2e30));
    P.addLocal(G.cyl(0.035, 0.035, 0.012, 14), mat(h.W / 2 - 0.2, 0.41, 0.1, Math.PI / 2, 0, 0), M);
  }
  if (hotHouse) {
    const h = hotHouse;
    P.anchor = [h.x, h.z];
    const pitch = 0.7;
    const M = mat(h.x, 0, h.z, 0, h.yaw, 0);
    const Hr = h.H + (h.W / 2) * Math.tan(pitch);
    for (const side of [-1]) for (let r = 0; r < 2; r++) for (let c = 0; c < 4; c++) {
      const along = 0.22 + r * 0.33;
      const px = side * Math.cos(pitch) * along, py = Hr - Math.sin(pitch) * along + 0.07;
      const pz = -0.35 - c * (h.D - 0.7) / 4;
      const pm = new THREE.Matrix4().multiplyMatrices(M, mat(px, py, pz, 0, 0, -side * pitch));
      P.tint('solar');
      P.addLocal(G.rbox(0.3, 0.02, (h.D - 0.9) / 4.3, 0.004), mat(0, 0, 0), pm);
    }
  }

  return { painter: P, houses, anchors, poles, poleTops, wires, stormPole, trees };
}

function picketFence(P, a, b, rng, h = 0.16) {
  const dx = b[0] - a[0], dz = b[1] - a[1];
  const L = Math.hypot(dx, dz);
  if (L < 0.1) return;
  const yaw = Math.atan2(dx, dz);
  const midx = (a[0] + b[0]) / 2, midz = (a[1] + b[1]) / 2;
  const prev = P.anchor;
  P.anchor = [midx, midz];
  P.add(G.box(0.014, 0.018, L), mat(midx, h * 0.8, midz, 0, yaw, 0));
  P.add(G.box(0.012, 0.016, L), mat(midx, h * 0.35, midz, 0, yaw, 0));
  const n = Math.max(2, Math.round(L / 0.09));
  for (let i = 0; i <= n; i++) {
    const u = i / n;
    const hh = h * (0.92 + hash1(i * 17 + Math.round(midx * 100)) * 0.16);
    P.add(G.box(0.03, hh, 0.012), mat(a[0] + dx * u, hh / 2, a[1] + dz * u, 0, yaw + Math.PI / 2, (hash1(i * 5) - 0.5) * 0.08));
  }
  P.anchor = prev;
}

// clumped walnut crown: several lumpy balls in two greens
const lumps = [];
function lumpGeom(k) {
  if (lumps[k]) return lumps[k];
  const g = new THREE.IcosahedronGeometry(1, 2);
  const p = g.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const n = valueNoise3(v.x * 2.8 + k, v.y * 2.8, v.z * 2.8, k) * 0.16 + valueNoise3(v.x * 9, v.y * 9 + k, v.z * 9, k + 3) * 0.06;
    v.multiplyScalar(1 + n);
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  lumps[k] = g;
  return g;
}
function addTree(P, x, z, r, rng) {
  P.anchor = [x, z];
  const th = r * 0.75 + 0.2;
  P.tint('trunk');
  P.add(G.cyl(0.05 * (0.6 + r), 0.08 * (0.6 + r), th, 7), mat(x, th / 2, z, rng.range(-0.06, 0.06), 0, rng.range(-0.06, 0.06)));
  // two branches
  for (let b = 0; b < 2; b++) {
    const a = rng.range(0, 6.28);
    P.add(G.cyl(0.025 * (0.6 + r), 0.04 * (0.6 + r), r * 0.7, 5), mat(x + Math.cos(a) * r * 0.15, th + r * 0.2, z + Math.sin(a) * r * 0.15, Math.sin(a) * 0.6, 0, -Math.cos(a) * 0.6));
  }
  const n = 5 + rng.int(0, 3);
  const g1 = C(0x4e6b35), g2 = C(0x6c8a45);
  for (let i = 0; i < n; i++) {
    const a = rng.range(0, Math.PI * 2), rr = rng.range(0.15, 0.55) * r;
    const lr = r * rng.range(0.42, 0.62);
    const col = g1.clone().lerp(g2, rng.next()).offsetHSL(rng.range(-0.01, 0.01), 0, rng.range(-0.05, 0.03));
    P.tint('leaf', col);
    P.add(lumpGeom(rng.int(0, 5)), mat(x + Math.cos(a) * rr, th + r * 0.55 + rng.range(-0.15, 0.35) * r, z + Math.sin(a) * rr, rng.range(0, 3), rng.range(0, 3), 0, lr, lr * 0.85, lr));
  }
  P.tint('leaf', g2.clone().offsetHSL(0, 0, 0.02));
  P.add(lumpGeom(0), mat(x, th + r * 0.95, z, 0, 0, 0, r * 0.45, r * 0.4, r * 0.45));
}

let _tuft = null;
function tuftGeom() {
  if (_tuft) return _tuft;
  const parts = [];
  for (let i = 0; i < 7; i++) {
    const a = (i / 7) * Math.PI * 2;
    const h = 0.09 + (i % 3) * 0.025;
    const g = new THREE.ConeGeometry(0.012, h, 3, 1);
    g.translate(0, h / 2, 0);
    g.rotateZ(0.35);
    g.rotateY(a);
    parts.push(g.toNonIndexed());
  }
  const pos = [];
  for (const p of parts) pos.push(...p.attributes.position.array);
  _tuft = new THREE.BufferGeometry();
  _tuft.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  _tuft.computeVertexNormals();
  return _tuft;
}

export { PLANET_R, S };
