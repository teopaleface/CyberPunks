// Daybreak village: a white architectural model of a Banat village, built
// procedurally from one seed. Units: 1 unit = 5 m at full scale
// (the board is 50 x 30 units).
import * as THREE from 'three';
import { mulberry32, hash1, valueNoise3 } from './prng.js';
import { Bucket, G, mat, extrude, rect, tubeAlong, sagPoints } from './geo.js';

export const SEED = 20261107;
export const BOARD = { x0: -25, x1: 25, z0: -15, z1: 15, t: 0.35 };
export const STREET_Y = BOARD.t; // street surface
export const SLAB = 0.03; // parcels are raised 0.03 above the streets
export const GROUND = BOARD.t + SLAB; // ground level for buildings
export const YARD_Y = GROUND + 0.012;

export const COLORS = {
  white: 0xf3f1ec,
  table: 0xe7e3dc,
  orange: 0xff5b1a,
  cobalt: 0x1e4fd8,
  green: 0x1fa35b,
  felt: 0x8e8c88,
  wire: 0x3a3936,
  solar: 0x1c2a4a,
  brass: 0xb8894a,
};

export const STREETS = [
  { id: 'M', x0: -25, x1: 25, z0: -0.8, z1: 0.8 },
  { id: 'N', x0: -14.6, x1: 25, z0: -9.6, z1: -8.4 },
  { id: 'S', x0: -14.6, x1: 14.1, z0: 8.4, z1: 9.6 },
  { id: 'C1', x0: -14.6, x1: -13.4, z0: -15, z1: 15 },
  { id: 'C2', x0: -5.1, x1: -3.9, z0: -15, z1: 8.4 },
  { id: 'C3', x0: 3.4, x1: 4.6, z0: -9.6, z1: 15 },
  { id: 'C4', x0: 12.9, x1: 14.1, z0: -15, z1: 9.6 },
];

export const DEPOT = { x0: -24.2, x1: -15.4, z0: -7.0, z1: -1.15, gate: [-21.0, -17.4] };
const FIELD = { x0: 15.0, x1: 24.4, z0: 4.0, z1: 14.4 };
const ORCHARD = { x0: -24.2, x1: -15.6, z0: -14.4, z1: -8.0 };

// ---------------------------------------------------------------------------
// Materials
// ---------------------------------------------------------------------------
function paperGrain(material, amount = 0.035) {
  // A hint of paper grain: world-space value noise on albedo, stable under
  // camera motion (a function of position only).
  material.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;')
      .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvWPos = (modelMatrix * vec4(transformed,1.0)).xyz;');
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
varying vec3 vWPos;
float h3(vec3 p){ p = fract(p*0.3183099+.1); p*=17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
float vn(vec3 x){ vec3 i=floor(x); vec3 f=fract(x); f=f*f*(3.0-2.0*f);
 return mix(mix(mix(h3(i),h3(i+vec3(1,0,0)),f.x),mix(h3(i+vec3(0,1,0)),h3(i+vec3(1,1,0)),f.x),f.y),
            mix(mix(h3(i+vec3(0,0,1)),h3(i+vec3(1,0,1)),f.x),mix(h3(i+vec3(0,1,1)),h3(i+vec3(1,1,1)),f.x),f.y),f.z); }`,
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
float g = vn(vWPos*38.0)*0.6 + vn(vWPos*110.0)*0.4;
diffuseColor.rgb *= 1.0 - ${amount.toFixed(4)} * g;`,
      );
  };
  material.customProgramCacheKey = () => 'grain' + amount;
  return material;
}

export function makeMaterials() {
  const std = (color, roughness, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness, metalness: 0, ...extra });
  return {
    white: paperGrain(std(COLORS.white, 0.86)),
    resin: std(0xf6f4ef, 0.62), // 3D-printed resin parts (wheels, pins needles)
    table: std(COLORS.table, 0.95),
    orange: std(COLORS.orange, 0.5),
    orangeDark: std(0xd9440e, 0.55),
    glass: std(0x2a2b2d, 0.28),
    wire: std(COLORS.wire, 0.6),
    felt: new THREE.MeshPhysicalMaterial({
      color: COLORS.felt, roughness: 1, metalness: 0, sheen: 1, sheenRoughness: 0.55, sheenColor: new THREE.Color(0xb9b6b0),
    }),
    rain: new THREE.MeshPhysicalMaterial({
      color: 0xffffff, roughness: 0.15, metalness: 0, transparent: true, opacity: 0.38, depthWrite: false,
    }),
    thread: {
      orange: new THREE.MeshPhysicalMaterial({ color: COLORS.orange, roughness: 0.75, sheen: 0.6, sheenRoughness: 0.6, sheenColor: new THREE.Color(0xffb08a) }),
      cobalt: new THREE.MeshPhysicalMaterial({ color: COLORS.cobalt, roughness: 0.75, sheen: 0.6, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x8fa8ff) }),
      green: new THREE.MeshPhysicalMaterial({ color: COLORS.green, roughness: 0.75, sheen: 0.6, sheenRoughness: 0.6, sheenColor: new THREE.Color(0x8fe0b4) }),
    },
    pin: {
      orange: std(COLORS.orange, 0.32),
      cobalt: std(COLORS.cobalt, 0.32),
      green: std(COLORS.green, 0.32),
    },
    solar: new THREE.MeshPhysicalMaterial({ color: COLORS.solar, roughness: 0.22, metalness: 0.1, clearcoat: 0.6, clearcoatRoughness: 0.15 }),
    brass: new THREE.MeshStandardMaterial({ color: COLORS.brass, roughness: 0.22, metalness: 1, envMapIntensity: 3.0 }),
    steel: new THREE.MeshStandardMaterial({ color: 0xc9c9c9, roughness: 0.35, metalness: 1, envMapIntensity: 2.0 }),
  };
}

// ---------------------------------------------------------------------------
// Gable volume (house, barn, shed). Local frame: the front gable faces +z at
// z = 0, the body runs back to z = -D, x in [-W/2, W/2], ground at y = 0.
// Holes are [s, y, w, h] centres: front/back s = x; sides s = distance back.
// Returns the local footprint [x0, x1, z0, z1].
// ---------------------------------------------------------------------------
export function gableVolume(b, M, o) {
  const { W, D, H, pitch = 0.7, t = 0.035 } = o;
  const tp = Math.tan(pitch);
  const Hr = H + (W / 2) * tp;
  const ov = o.overhang ?? 0.07;
  const roofT = o.roofT ?? 0.04;
  const sideOv = o.sideOv ?? 0.1;

  const tint = (n) => b.tint && b.tint(n);
  tint('wall');
  // body (closed pentagon prism)
  const body = extrude([[-W / 2, 0], [W / 2, 0], [W / 2, H], [0, Hr], [-W / 2, H]], [], D, 0);
  b.addLocal(body, mat(0, 0, -D), M);

  const holesXY = (hs) => (hs || []).map(([s, y, w, h]) => rect(s, y, w, h));
  const Wt = W / 2 + t;
  const pent = [[-Wt, 0], [Wt, 0], [Wt, H], [0, Hr + t * tp], [-Wt, H]];
  // front & back plates (gable ends) with real window recesses
  b.addLocal(extrude(pent, holesXY(o.front), t), mat(0, 0, 0), M);
  b.addLocal(extrude(pent, holesXY(o.back), t), mat(0, 0, -D - t), M);
  // side plates (rotate so shape x -> -z)
  const sideR = extrude([[0, 0], [D, 0], [D, H], [0, H]], holesXY(o.right), t);
  b.addLocal(sideR, mat(W / 2, 0, 0, 0, Math.PI / 2, 0), M);
  const leftHoles = (o.left || []).map(([s, y, w, h]) => rect(-s, y, w, h));
  const sideL = extrude([[-D, 0], [0, 0], [0, H], [-D, H]], leftHoles, t);
  b.addLocal(sideL, mat(-W / 2, 0, 0, 0, -Math.PI / 2, 0), M);
  // glass panes + frames inside every recess (painted look only)
  if (b.tint) {
    const win = (plateM, holes, zb) => {
      for (const [hx, hy, hw, hh] of holes) {
        tint(o.glassTint || 'glass');
        b.addLocal(G.box(hw, hh, 0.006), mat(hx, hy, zb), new THREE.Matrix4().multiplyMatrices(M, plateM));
        tint('frame');
        const PM = new THREE.Matrix4().multiplyMatrices(M, plateM);
        const fz = zb + Math.sign(t / 2 - zb) * 0.006;
        b.addLocal(G.box(0.016, hh, 0.012), mat(hx, hy, fz), PM);
        if (hh > 0.18) b.addLocal(G.box(hw, 0.016, 0.012), mat(hx, hy + hh * 0.12, fz), PM);
        b.addLocal(G.box(hw + 0.03, 0.022, 0.03), mat(hx, hy - hh / 2 - 0.006, t + 0.004), PM); // sill
      }
    };
    win(mat(0, 0, 0), (o.front || []).map(([s1, y, w, h]) => [s1, y, w, h]), 0.004);
    win(mat(0, 0, -D - t), (o.back || []).map(([s1, y, w, h]) => [s1, y, w, h]), t - 0.004);
    win(mat(W / 2, 0, 0, 0, Math.PI / 2, 0), o.right || [], 0.004);
    win(mat(-W / 2, 0, 0, 0, -Math.PI / 2, 0), (o.left || []).map(([s1, y, w, h]) => [-s1, y, w, h]), 0.004);
    tint('wall');
  }

  // roof slabs
  const porch = o.porch || 0;
  const len = D + 2 * t + 2 * ov;
  const ext = roofT * tp * 0.5;
  const slab = (side, extra) => {
    const L = Wt / Math.cos(pitch) + sideOv + extra + ext;
    const d = new THREE.Vector2(side * Math.cos(pitch), -Math.sin(pitch));
    const n = new THREE.Vector2(side * Math.sin(pitch), Math.cos(pitch));
    const c = new THREE.Vector2(0, Hr).addScaledVector(d, L / 2 - ext).addScaledVector(n, roofT / 2);
    b.addLocal(G.rbox(L, roofT, len, 0.006), mat(c.x, c.y, -D / 2, 0, 0, -side * pitch), M);
  };
  tint('roof');
  slab(1, porch ? porch / Math.cos(pitch) : 0);
  slab(-1, 0);
  // ridge cap
  b.addLocal(G.rbox(0.07, 0.035, len + 0.01, 0.006), mat(0, Hr + roofT / Math.cos(pitch) + 0.002, -D / 2), M);
  // socle band
  tint('socle');
  b.addLocal(G.rbox(W + 2 * t + 0.024, 0.07, D + 2 * t + 0.024, 0.006), mat(0, 0.035, -D / 2), M);

  let fp = [-Wt - sideOv * 0.9, Wt + sideOv * 0.9, -D - t - ov, t + ov];
  if (porch) {
    tint('wall');
    // Banat porch (tinda): columns along the right side under the long roof
    const z0 = -(o.porchFrom ?? 0.35), z1 = -(o.porchTo ?? D * 0.8);
    const xc = Wt + porch - 0.06;
    const colH = H - (porch - 0.06) * tp;
    const n = Math.max(2, Math.round((z0 - z1) / 0.42) + 1);
    for (let i = 0; i < n; i++) {
      const z = z0 + ((z1 - z0) * i) / (n - 1);
      b.addLocal(G.rbox(0.045, colH, 0.045, 0.006), mat(xc, colH / 2, z), M);
    }
    b.addLocal(G.rbox(porch + 0.02, 0.05, z0 - z1 + 0.2, 0.006), mat(Wt + porch / 2, 0.025, (z0 + z1) / 2), M);
    fp[1] = Wt + porch + sideOv;
  }
  tint('wall');
  if (o.chimney) {
    const [cz, cs] = o.chimney;
    const y = Hr - 0.18 * tp;
    b.addLocal(G.rbox(0.1, 0.32, 0.1, 0.006), mat(cs * 0.18, y + 0.1, -D * cz), M);
  }
  return fp;
}

// Windows for a house front of width W, eave H.
function frontWindows(W, H, rng) {
  const n = W > 1.72 ? 3 : 2;
  const ww = 0.2, wh = 0.27;
  const y = H * 0.56;
  const gap = W / (n + (n === 3 ? 0.6 : 0.9));
  const out = [];
  for (let i = 0; i < n; i++) out.push([(i - (n - 1) / 2) * gap, y, ww, wh]);
  // attic vents in the gable
  const ridgeY = H + (W / 2) * Math.tan(0.7);
  if (rng.chance(0.7)) {
    out.push([-0.09, (H + ridgeY) / 2 - 0.02, 0.05, 0.12], [0.09, (H + ridgeY) / 2 - 0.02, 0.05, 0.12]);
  } else out.push([0, (H + ridgeY) / 2 - 0.03, 0.12, 0.12]);
  return out;
}

function sideWindows(D, H, from, to, every, rng) {
  const out = [];
  for (let s = from; s < to; s += every) out.push([s, H * 0.56, 0.2, 0.27]);
  return out;
}

// ---------------------------------------------------------------------------
// Trees: faceted, walnut-like rounded crowns.
// ---------------------------------------------------------------------------
const crownVariants = [];
function crownGeom(k) {
  if (crownVariants[k]) return crownVariants[k];
  const g = new THREE.IcosahedronGeometry(1, 1);
  const p = g.attributes.position;
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i);
    const key = Math.round(v.x * 1000) * 7 + Math.round(v.y * 1000) * 131 + Math.round(v.z * 1000) * 1031 + k * 99991;
    const s = 1 + (hash1(key) - 0.5) * 0.22;
    v.multiplyScalar(s);
    v.y *= v.y < 0 ? 0.62 : 0.86;
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.computeVertexNormals();
  crownVariants[k] = g;
  return g;
}

function addTree(b, x, z, r, rng, y0 = GROUND) {
  const trunkH = r * 0.62 + 0.18;
  b.add(G.cyl(0.035 * (0.7 + r * 0.4), 0.05 * (0.7 + r * 0.4), trunkH, 7), mat(x, y0 + trunkH / 2, z));
  b.add(crownGeom(rng.int(0, 5)), mat(x, y0 + trunkH + r * 0.48, z, 0, rng.range(0, Math.PI * 2), 0, r, r, r));
}

// ---------------------------------------------------------------------------
// Truck: orange bucket truck. Local: forward +z, ground y = 0, length ~1.5.
// ---------------------------------------------------------------------------
export function buildTruck(mats) {
  const og = new Bucket(), dk = new Bucket(), gl = new Bucket(), wh = new Bucket();
  const I = new THREE.Matrix4();
  // wheels (white resin) on three axles
  for (const z of [0.47, -0.36, -0.55]) for (const sx of [-1, 1]) {
    wh.addLocal(G.cyl(0.105, 0.105, 0.075, 24), mat(sx * 0.212, 0.105, z, 0, 0, Math.PI / 2), I);
    dk.addLocal(G.cyl(0.05, 0.05, 0.08, 16), mat(sx * 0.215, 0.105, z, 0, 0, Math.PI / 2), I);
  }
  og.addLocal(G.rbox(0.34, 0.06, 1.42, 0.01), mat(0, 0.16, -0.02), I); // chassis
  // cab (cab-over)
  og.addLocal(G.rbox(0.5, 0.4, 0.42, 0.035, 2), mat(0, 0.37, 0.55), I);
  og.addLocal(G.rbox(0.52, 0.055, 0.05, 0.012), mat(0, 0.2, 0.77), I); // bumper
  gl.addLocal(G.rbox(0.42, 0.15, 0.012, 0.004), mat(0, 0.47, 0.762), I); // windscreen
  for (const sx of [-1, 1]) gl.addLocal(G.rbox(0.012, 0.13, 0.2, 0.004), mat(sx * 0.252, 0.47, 0.6), I);
  wh.addLocal(G.rbox(0.07, 0.035, 0.012, 0.004), mat(-0.17, 0.27, 0.763), I); // lamps
  wh.addLocal(G.rbox(0.07, 0.035, 0.012, 0.004), mat(0.17, 0.27, 0.763), I);
  og.addLocal(G.rbox(0.44, 0.03, 0.08, 0.008), mat(0, 0.585, 0.43), I); // roof cap
  // utility body with lockers
  og.addLocal(G.rbox(0.5, 0.29, 0.98, 0.012), mat(0, 0.335, -0.21), I);
  for (const sx of [-1, 1]) for (const z of [0.12, -0.21, -0.54]) {
    og.addLocal(G.rbox(0.008, 0.21, 0.29, 0.003), mat(sx * 0.252, 0.34, z), I);
    dk.addLocal(G.box(0.006, 0.012, 0.06), mat(sx * 0.257, 0.38, z + 0.09), I); // handles
  }
  og.addLocal(G.rbox(0.52, 0.02, 1.0, 0.006), mat(0, 0.485, -0.21), I); // deck rim
  // turret + folded boom + bucket
  og.addLocal(G.cyl(0.075, 0.085, 0.09, 24), mat(0, 0.54, -0.52), I);
  og.addLocal(G.rbox(0.09, 0.08, 0.16, 0.01), mat(0, 0.6, -0.52), I);
  og.addLocal(G.rbox(0.075, 0.07, 1.08, 0.01), mat(-0.05, 0.64, -0.02, -0.02, 0, 0), I);
  og.addLocal(G.rbox(0.06, 0.055, 0.98, 0.01), mat(0.05, 0.64, 0.0, -0.02, 0, 0), I);
  og.addLocal(G.rbox(0.05, 0.08, 0.05, 0.008), mat(0, 0.6, 0.38), I); // boom rest
  og.addLocal(G.rbox(0.2, 0.2, 0.19, 0.016), mat(0, 0.62, -0.78), I); // bucket
  dk.addLocal(G.rbox(0.16, 0.02, 0.15, 0.005), mat(0, 0.721, -0.78), I);
  // outriggers
  for (const sx of [-1, 1]) og.addLocal(G.rbox(0.06, 0.06, 0.08, 0.008), mat(sx * 0.2, 0.15, -0.72), I);

  const grp = new THREE.Group();
  for (const [bk, m] of [[og, mats.orange], [dk, mats.orangeDark], [gl, mats.glass], [wh, mats.resin]]) grp.add(bk.mesh(m));
  return grp;
}

// ---------------------------------------------------------------------------
// Utility pole: concrete, crossarm, 3 insulators. Returns attachment points.
// ---------------------------------------------------------------------------
const POLE_H = 1.85;
function addPole(b, x, z, ry, y0 = GROUND, H = POLE_H) {
  const M = mat(x, y0, z, 0, ry, 0);
  b.addLocal(G.cyl(0.026, 0.036, H, 12), mat(0, H / 2, 0), M);
  b.addLocal(G.rbox(0.56, 0.035, 0.035, 0.005), mat(0, H - 0.12, 0), M);
  b.addLocal(G.rbox(0.02, 0.14, 0.02, 0.004), mat(0.13, H - 0.2, 0, 0, 0, 0.75), M);
  b.addLocal(G.rbox(0.02, 0.14, 0.02, 0.004), mat(-0.13, H - 0.2, 0, 0, 0, -0.75), M);
  const pts = [];
  for (const dx of [-0.24, 0, 0.24]) {
    const h = dx === 0 ? H + 0.02 : H - 0.08;
    b.addLocal(G.cyl(0.012, 0.014, 0.05, 8), mat(dx, h - 0.0, 0), M);
    pts.push(new THREE.Vector3(dx, h + 0.022, 0).applyMatrix4(M));
  }
  return pts;
}

function addWire(b, a, c, sag = 0.1, r = 0.0055) {
  b.add(tubeAlong(sagPoints(a, c, sag, 18), r, 5));
}

// ---------------------------------------------------------------------------
// Footprint collision helper (all footprints are axis-aligned in world).
// ---------------------------------------------------------------------------
class Layout {
  constructor() { this.boxes = []; }
  hit(bx, pad = 0) {
    for (const o of this.boxes) {
      if (bx[0] - pad < o[1] && bx[1] + pad > o[0] && bx[2] - pad < o[3] && bx[3] + pad > o[2]) return true;
    }
    return bx[0] < BOARD.x0 + 0.3 || bx[1] > BOARD.x1 - 0.3 || bx[2] < BOARD.z0 + 0.3 || bx[3] > BOARD.z1 - 0.3;
  }
  add(bx) { this.boxes.push(bx); }
}

function worldBox(local, x, z, ry) {
  const [x0, x1, z0, z1] = local;
  const c = Math.round(Math.cos(ry)), s = Math.round(Math.sin(ry));
  const pts = [[x0, z0], [x1, z0], [x0, z1], [x1, z1]].map(([lx, lz]) => [x + lx * c + lz * s, z - lx * s + lz * c]);
  const xs = pts.map((p) => p[0]), zs = pts.map((p) => p[1]);
  return [Math.min(...xs), Math.max(...xs), Math.min(...zs), Math.max(...zs)];
}

// ---------------------------------------------------------------------------
// Ground: board + raised parcels; streets are the recessed gaps.
// ---------------------------------------------------------------------------
function buildGround() {
  const xs = [...new Set([BOARD.x0, BOARD.x1, ...STREETS.flatMap((s) => [s.x0, s.x1])])].sort((a, b) => a - b);
  const zs = [...new Set([BOARD.z0, BOARD.z1, ...STREETS.flatMap((s) => [s.z0, s.z1])])].sort((a, b) => a - b);
  const isStreet = (i, j) => {
    if (i < 0 || j < 0 || i >= xs.length - 1 || j >= zs.length - 1) return null;
    const cx = (xs[i] + xs[i + 1]) / 2, cz = (zs[j] + zs[j + 1]) / 2;
    return STREETS.find((s) => cx > s.x0 && cx < s.x1 && cz > s.z0 && cz < s.z1) || false;
  };
  const pos = [], nor = [];
  const quad = (a, b, c, d, n) => {
    for (const p of [a, b, c, a, c, d]) { pos.push(...p); nor.push(...n); }
  };
  const frontages = [];
  for (let i = 0; i < xs.length - 1; i++) for (let j = 0; j < zs.length - 1; j++) {
    if (isStreet(i, j)) continue;
    const x0 = xs[i], x1 = xs[i + 1], z0 = zs[j], z1 = zs[j + 1];
    const Y = GROUND, y = STREET_Y;
    quad([x0, Y, z1], [x1, Y, z1], [x1, Y, z0], [x0, Y, z0], [0, 1, 0]);
    const sides = [
      { n: [0, 0, -1], nb: isStreet(i, j - 1), a: [x1, z0], b: [x0, z0] },
      { n: [0, 0, 1], nb: isStreet(i, j + 1), a: [x0, z1], b: [x1, z1] },
      { n: [-1, 0, 0], nb: isStreet(i - 1, j), a: [x0, z0], b: [x0, z1] },
      { n: [1, 0, 0], nb: isStreet(i + 1, j), a: [x1, z1], b: [x1, z0] },
    ];
    for (const s of sides) {
      if (s.nb === false) continue; // neighbour is a parcel: seamless
      quad([s.a[0], y, s.a[1]], [s.b[0], y, s.b[1]], [s.b[0], Y, s.b[1]], [s.a[0], Y, s.a[1]], s.n);
      if (s.nb) frontages.push({ street: s.nb.id, out: new THREE.Vector3(s.n[0], 0, s.n[2]), a: s.a, b: s.b });
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  // merge collinear frontages on the same street
  const key = (f) => `${f.street}|${f.out.x},${f.out.z}|${f.out.x ? f.a[0] : f.a[1]}`;
  const groups = new Map();
  for (const f of frontages) {
    const k = key(f);
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(f);
  }
  const merged = [];
  for (const fs of groups.values()) {
    const alongX = fs[0].out.z !== 0;
    const iv = fs.map((f) => (alongX ? [Math.min(f.a[0], f.b[0]), Math.max(f.a[0], f.b[0])] : [Math.min(f.a[1], f.b[1]), Math.max(f.a[1], f.b[1])])).sort((a, b) => a[0] - b[0]);
    let cur = iv[0].slice();
    const flush = () => merged.push({ street: fs[0].street, out: fs[0].out, alongX, c: alongX ? fs[0].a[1] : fs[0].a[0], lo: cur[0], hi: cur[1] });
    for (let k = 1; k < iv.length; k++) {
      if (Math.abs(iv[k][0] - cur[1]) < 1e-6) cur[1] = iv[k][1];
      else { flush(); cur = iv[k].slice(); }
    }
    flush();
  }
  return { slab: g, frontages: merged };
}

// ---------------------------------------------------------------------------
// The world
// ---------------------------------------------------------------------------
export function buildWorld(mats) {
  const rng = mulberry32(SEED);
  const root = new THREE.Group();
  const village = new THREE.Group();
  root.add(village);
  const white = new Bucket();
  const wires = new Bucket();
  const layout = new Layout();

  // board
  white.add(G.box(BOARD.x1 - BOARD.x0, BOARD.t, BOARD.z1 - BOARD.z0), mat(0, BOARD.t / 2, 0));
  const { slab, frontages } = buildGround();
  white.add(slab);

  for (const s of STREETS) layout.add([s.x0 - 0.05, s.x1 + 0.05, s.z0 - 0.05, s.z1 + 0.05]);
  layout.add([DEPOT.x0 - 0.3, DEPOT.x1 + 0.3, DEPOT.z0 - 0.3, DEPOT.z1 + 0.2]);
  layout.add([FIELD.x0 - 0.2, FIELD.x1 + 0.2, FIELD.z0 - 0.2, FIELD.z1 + 0.2]);
  layout.add([ORCHARD.x0, ORCHARD.x1, ORCHARD.z0, ORCHARD.z1]);
  // keep pole line clear
  layout.add([-25, 25, -1.2, -0.8]);

  // ---- houses along frontages (main road first) --------------------------
  const order = { M: 0, N: 1, S: 2, C1: 3, C2: 3, C3: 3, C4: 3 };
  frontages.sort((a, b) => order[a.street] - order[b.street] || a.lo - b.lo);
  const houses = [];
  const SETBACK = 0.42;
  for (const f of frontages) {
    let s = f.lo + 0.5 + rng.range(0, 0.6);
    while (s < f.hi - 2.2) {
      const plotW = rng.range(2.9, 3.7);
      if (s + plotW > f.hi - 0.3) break;
      const inward = f.out.clone().negate();
      const ry = Math.atan2(f.out.x, f.out.z); // local +z -> towards street
      const along = f.alongX ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 0, 1);
      const edge = (u) => (f.alongX ? new THREE.Vector3(u, 0, f.c) : new THREE.Vector3(f.c, 0, u));
      if (rng.chance(0.9)) {
        const W = rng.range(1.42, 1.9);
        let D = rng.range(2.7, 3.9);
        const H = rng.range(0.56, 0.64);
        const porch = rng.chance(0.75) ? 0.3 : 0;
        const lshape = rng.chance(0.22);
        // house sits towards one side of the plot (alternating parity per frontage)
        const sideOff = 0.25 + W / 2 + 0.12;
        const uC = s + sideOff;
        const front = edge(uC).addScaledVector(inward, SETBACK);
        let placed = null;
        for (let tries = 0; tries < 3 && !placed; tries++) {
          const opts = { W, D, H, porch, porchFrom: 0.35, porchTo: lshape ? D - 1.35 : D * 0.82 };
          let fp = [-W / 2 - 0.2, W / 2 + 0.2 + (porch ? 0.3 : 0), -D - 0.15, 0.15];
          if (lshape) fp[1] = Math.max(fp[1], W / 2 + 1.55);
          const wb = worldBox(fp, front.x, front.z, ry);
          if (!layout.hit(wb, 0.12)) { placed = { opts, wb }; break; }
          D *= 0.82;
        }
        if (placed) {
          const { opts, wb } = placed;
          layout.add(wb);
          const M = mat(front.x, GROUND, front.z, 0, ry, 0);
          const sideWins = sideWindows(opts.D, H, 0.6, opts.D - 0.4, 0.62, rng);
          gableVolume(white, M, {
            ...opts,
            front: frontWindows(W, H, rng),
            left: sideWins,
            right: sideWindows(opts.D, H, 0.7, opts.porchTo, 0.75, rng),
            chimney: rng.chance(0.6) ? [rng.range(0.3, 0.7), rng.chance(0.5) ? 1 : -1] : null,
          });
          if (lshape) {
            const W2 = 1.15, D2 = 1.4;
            const Mw = new THREE.Matrix4().multiplyMatrices(M, mat(W / 2 + 0.035 + D2, 0, -opts.D + W2 / 2 + 0.05, 0, Math.PI / 2, 0));
            gableVolume(white, Mw, { W: W2, D: D2, H: H * 0.95, front: [[0, H * 0.53, 0.2, 0.26]], left: [[0.7, H * 0.53, 0.2, 0.26]] });
          }
          const Hr = H + (W / 2) * Math.tan(0.7);
          houses.push({
            street: f.street, out: f.out.clone(), alongX: f.alongX, u: uC, c: f.c, W, D: opts.D, H, ry,
            front: front.clone(), pinTop: new THREE.Vector3(0, Hr + 0.04, -0.55).applyMatrix4(M),
          });
          // barn across the back of the plot
          if (rng.chance(0.55)) {
            const bw = 1.0, bd = Math.min(plotW * 0.62, 2.1);
            const back = opts.D + rng.range(0.9, 1.4) + bw / 2;
            const c0 = edge(s + plotW / 2).addScaledVector(inward, SETBACK + back);
            const ryB = ry + Math.PI / 2;
            const Mb = mat(c0.x, GROUND, c0.z, 0, ryB, 0);
            const lfp = [-bw / 2 - 0.12, bw / 2 + 0.12, -bd / 2 - 0.12, bd / 2 + 0.12];
            const wbb = worldBox(lfp, c0.x, c0.z, ryB);
            if (!layout.hit(wbb, 0.1)) {
              layout.add(wbb);
              gableVolume(white, new THREE.Matrix4().multiplyMatrices(Mb, mat(0, 0, bd / 2)), {
                W: bw, D: bd, H: 0.5, pitch: 0.66, left: [[bd / 2, 0.22, 0.42, 0.4]],
              });
            }
          }
          // front fence (from plot edge to house, with a gate) and a side fence
          const fenceLine = (u0, u1) => {
            if (u1 - u0 < 0.1) return;
            const a = edge(u0).addScaledVector(inward, 0.12), c = edge(u1).addScaledVector(inward, 0.12);
            addFence(white, a, c);
          };
          const houseLo = uC - W / 2 - 0.05, houseHi = uC + W / 2 + 0.05 + (porch ? 0.3 : 0);
          fenceLine(s, houseLo - 0.0);
          fenceLine(houseHi + 0.55, s + plotW); // gate gap next to the porch
          const sideA = edge(s + plotW).addScaledVector(inward, 0.12);
          const sideB = edge(s + plotW).addScaledVector(inward, 0.12 + rng.range(3.0, 4.6));
          const sb = [Math.min(sideA.x, sideB.x) - 0.05, Math.max(sideA.x, sideB.x) + 0.05, Math.min(sideA.z, sideB.z) - 0.05, Math.max(sideA.z, sideB.z) + 0.05];
          if (!layout.hit(sb, 0.02)) addFence(white, sideA, sideB);
          // garden trees
          const nT = rng.int(1, 2);
          for (let k = 0; k < nT; k++) {
            const r = rng.range(0.42, 0.72);
            const p = edge(s + rng.range(0.6, plotW - 0.6)).addScaledVector(inward, SETBACK + rng.range(1.0, opts.D + 2.5));
            const tb = [p.x - r * 0.8, p.x + r * 0.8, p.z - r * 0.8, p.z + r * 0.8];
            if (!layout.hit(tb, 0.02)) { layout.add(tb); addTree(white, p.x, p.z, r, rng); }
          }
        }
      }
      s += plotW;
    }
  }

  // extra trees filling the back gardens
  for (let k = 0; k < 260; k++) {
    const x = rng.range(-24.5, 24.5), z = rng.range(-14.5, 14.5);
    const r = rng.range(0.4, 0.78);
    const tb = [x - r * 0.85, x + r * 0.85, z - r * 0.85, z + r * 0.85];
    if (!layout.hit(tb, 0.08)) { layout.add(tb); addTree(white, x, z, r, rng); }
  }

  // orchard (rows of small round trees)
  for (let x = ORCHARD.x0 + 0.7; x < ORCHARD.x1 - 0.4; x += 1.25)
    for (let z = ORCHARD.z0 + 0.7; z < ORCHARD.z1 - 0.3; z += 1.25) addTree(white, x + rng.range(-0.05, 0.05), z + rng.range(-0.05, 0.05), 0.38, rng);

  // sunflower field: fine parallel ridges
  {
    const ridge = extrude([[-0.055, 0], [0.055, 0], [0.012, 0.045], [-0.012, 0.045]], [], FIELD.x1 - FIELD.x0, 0.0);
    for (let z = FIELD.z0 + 0.1; z < FIELD.z1; z += 0.2) white.add(ridge, mat(FIELD.x0, GROUND, z, 0, Math.PI / 2, 0));
    // a thin rim around the field
    addFence(white, new THREE.Vector3(FIELD.x0 - 0.12, 0, FIELD.z0 - 0.12), new THREE.Vector3(FIELD.x1 + 0.12, 0, FIELD.z0 - 0.12), 0.05, false);
  }

  // ---- depot -------------------------------------------------------------
  const depot = buildDepot(white, rng);

  // ---- poles and wires along the main road (north side) -------------------
  const poleZ = -1.0;
  const poleXs = [];
  for (let x = -23.4; x < 24.5; x += 3.05) {
    if (STREETS.some((s) => s.id.startsWith('C') && x > s.x0 - 0.35 && x < s.x1 + 0.35)) continue;
    poleXs.push(x);
  }
  const stormIndex = poleXs.reduce((best, x, i) => (Math.abs(x - 0.9) < Math.abs(poleXs[best] - 0.9) ? i : best), 0);
  const polePts = [];
  const intactPole = new Bucket(), intactWires = new Bucket();
  poleXs.forEach((x, i) => {
    const b = i === stormIndex ? intactPole : white;
    polePts.push(addPole(b, x, poleZ, 0));
  });
  for (let i = 0; i < poleXs.length - 1; i++) {
    const b = i === stormIndex || i + 1 === stormIndex ? intactWires : wires;
    for (let k = 0; k < 3; k++) addWire(b, polePts[i][k], polePts[i + 1][k], 0.11);
  }
  // a few service drops from poles to houses near the road
  for (const h of houses) {
    if (h.street !== 'M' || h.out.z > 0) continue;
    const i = poleXs.findIndex((x) => Math.abs(x - h.front.x) < 1.2);
    if (i < 0 || i === stormIndex) continue;
    const a = polePts[i][0];
    const c = h.front.clone().setY(GROUND + h.H * 0.92);
    wires.add(tubeAlong(sagPoints(a, c, 0.06, 10), 0.004, 4));
  }

  village.add(white.mesh(mats.white));
  village.add(wires.mesh(mats.wire));

  // storm-variable pole: intact version and snapped version
  const poleIntact = new THREE.Group();
  poleIntact.add(intactPole.mesh(mats.white), intactWires.mesh(mats.wire));
  village.add(poleIntact);
  const poleSnapped = buildSnappedPole(mats, poleXs, polePts, stormIndex, poleZ);
  village.add(poleSnapped);

  return {
    root, village, houses, depot, poleXs, poleZ, stormIndex, poleIntact, poleSnapped,
  };
}

function addFence(b, a, c, h = 0.11, posts = true) {
  const d = new THREE.Vector3().subVectors(c, a);
  const L = d.length();
  if (L < 0.05) return;
  const ry = Math.atan2(d.x, d.z);
  const mid = new THREE.Vector3().addVectors(a, c).multiplyScalar(0.5);
  b.add(G.box(0.012, 0.016, L), mat(mid.x, GROUND + h, mid.z, 0, ry, 0));
  b.add(G.box(0.008, 0.012, L), mat(mid.x, GROUND + h * 0.45, mid.z, 0, ry, 0));
  if (!posts) return;
  const n = Math.max(1, Math.round(L / 0.42));
  for (let i = 0; i <= n; i++) {
    const p = new THREE.Vector3().lerpVectors(a, c, i / n);
    b.add(G.box(0.022, h + 0.02, 0.022), mat(p.x, GROUND + (h + 0.02) / 2, p.z, 0, ry, 0));
  }
}

function buildDepot(white, rng) {
  const D = DEPOT;
  const cx = (D.x0 + D.x1) / 2, cz = (D.z0 + D.z1) / 2;
  // yard pad
  white.add(G.rbox(D.x1 - D.x0, 0.024, D.z1 - D.z0, 0.006), mat(cx, GROUND, cz));
  // parking bay dividers (hair-thin raised strips)
  for (let i = 0; i <= 5; i++) {
    const x = -23.25 + i * 1.3;
    white.add(G.box(0.02, 0.006, 1.6), mat(x, YARD_Y + 0.003, -3.55));
  }
  // fence with open gate
  const P = (x, z) => new THREE.Vector3(x, 0, z);
  const fenceH = 0.22;
  addFence(white, P(D.x0, D.z1), P(D.gate[0], D.z1), fenceH);
  addFence(white, P(D.gate[1], D.z1), P(D.x1, D.z1), fenceH);
  addFence(white, P(D.x1, D.z1), P(D.x1, D.z0), fenceH);
  addFence(white, P(D.x1, D.z0), P(D.x0, D.z0), fenceH);
  addFence(white, P(D.x0, D.z0), P(D.x0, D.z1), fenceH);
  // gate leaves swung open inward
  const leaf = (hx, sign) => {
    const L = 1.75;
    const a = -sign * 1.25;
    const c = P(hx + sign * Math.cos(a) * L * 0.5 * -1 * -1, D.z1);
    const m = mat(hx, GROUND, D.z1, 0, a, 0);
    white.addLocal(G.box(L, 0.018, 0.014), mat(sign * L / 2, fenceH, 0), m);
    white.addLocal(G.box(L, 0.014, 0.012), mat(sign * L / 2, fenceH * 0.5, 0), m);
    for (let i = 0; i <= 6; i++) white.addLocal(G.box(0.014, fenceH, 0.014), mat(sign * (i / 6) * L, fenceH / 2, 0), m);
    return c;
  };
  leaf(D.gate[0], 1);
  leaf(D.gate[1], -1);
  // gate posts
  for (const x of D.gate) white.add(G.rbox(0.07, 0.34, 0.07, 0.01), mat(x, GROUND + 0.17, D.z1));

  // main shed: long side faces the yard (south) with two roller doors
  const Ms = mat(-21.75 + 1.8, GROUND, -5.65, 0, Math.PI / 2, 0); // front gable faces +x
  const doorY = 0.38, doorH = 0.7, doorW = 0.95;
  gableVolume(white, Ms, {
    W: 2.3, D: 3.6, H: 1.0, pitch: 0.36, roofT: 0.045, sideOv: 0.12,
    left: [[0.95, doorY, doorW, doorH], [2.3, doorY, doorW, doorH], [3.25, 0.62, 0.3, 0.24]],
    front: [[-0.5, 0.62, 0.3, 0.24], [0.5, 0.62, 0.3, 0.24], [0, 0.32, 0.32, 0.6]],
    right: [[0.9, 0.7, 0.4, 0.2], [1.8, 0.7, 0.4, 0.2], [2.7, 0.7, 0.4, 0.2]],
  });
  // roller door slats inside the recesses
  for (const s of [0.95, 2.3]) for (let y = doorY - doorH / 2 + 0.04; y < doorY + doorH / 2 - 0.02; y += 0.055) {
    white.addLocal(G.box(0.006, 0.012, doorW - 0.03), mat(-1.15 - 0.004, y, -s), Ms);
  }
  // office
  const Mo = mat(-16.75, GROUND, -5.0, 0, 0, 0);
  gableVolume(white, Mo, {
    W: 1.4, D: 1.6, H: 0.66, pitch: 0.6,
    front: [[-0.36, 0.36, 0.22, 0.26], [0.32, 0.27, 0.22, 0.46]],
    left: [[0.5, 0.36, 0.22, 0.26], [1.1, 0.36, 0.22, 0.26]],
    right: [[0.8, 0.36, 0.42, 0.26]],
  });
  // canopy over a work bay
  for (const [x, z] of [[-18.1, -6.6], [-18.1, -5.0], [-19.8, -6.6], [-19.8, -5.0]]) white.add(G.rbox(0.05, 0.62, 0.05, 0.006), mat(x, YARD_Y + 0.31, z));
  white.add(G.rbox(2.0, 0.035, 1.9, 0.008), mat(-18.95, YARD_Y + 0.64, -5.8, 0.06, 0, 0));
  // stacked spare poles
  for (let i = 0; i < 6; i++) {
    const row = i < 3 ? 0 : 1, k = i % 3;
    if (row === 1 && k === 2) continue;
    white.add(G.cyl(0.034, 0.034, 2.1, 12), mat(-23.15 + 1.05 + 0, YARD_Y + 0.034 + row * 0.06, -1.75 + 0 * k, 0, 0, Math.PI / 2).premultiply(mat(0, 0, -k * 0.07 - row * 0.035)));
  }
  // cable drums
  const drum = (x, z) => {
    const m = mat(x, YARD_Y, z, 0, 0.4, 0);
    white.addLocal(G.cyl(0.19, 0.19, 0.03, 28), mat(0, 0.19, -0.075, Math.PI / 2, 0, 0), m);
    white.addLocal(G.cyl(0.19, 0.19, 0.03, 28), mat(0, 0.19, 0.075, Math.PI / 2, 0, 0), m);
    white.addLocal(G.cyl(0.11, 0.11, 0.14, 24), mat(0, 0.19, 0, Math.PI / 2, 0, 0), m);
  };
  drum(-15.95, -2.0);
  drum(-16.05, -2.6);
  drum(-16.6, -1.75);
  // trees around the depot
  for (const [x, z, r] of [[-24.6, -5.2, 0.5], [-24.6, -3.0, 0.45], [-15.0, -6.4, 0.55], [-14.95, -4.1, 0.48]]) addTree(white, x, z, r, rng);
  // depot poles
  addPole(white, -23.7, -6.6, 0);
  return { cx, cz };
}

function buildSnappedPole(mats, poleXs, polePts, k, poleZ) {
  const grp = new THREE.Group();
  const w = new Bucket(), wi = new Bucket();
  const x = poleXs[k];
  // stump with a jagged top
  const stump = new THREE.CylinderGeometry(0.03, 0.036, 0.42, 12, 3);
  const p = stump.attributes.position;
  for (let i = 0; i < p.count; i++) {
    if (p.getY(i) > 0.2) p.setY(i, p.getY(i) + (hash1(i * 31 + 7) - 0.5) * 0.09);
  }
  stump.computeVertexNormals();
  w.add(stump, mat(x, GROUND + 0.21, poleZ));
  // fallen upper part lying across the road, its foot near the stump
  const L = 1.5;
  const fallen = new THREE.Group();
  const fb = new Bucket();
  const geo = new THREE.CylinderGeometry(0.026, 0.031, L, 12, 3);
  const q = geo.attributes.position;
  for (let i = 0; i < q.count; i++) if (q.getY(i) < -L / 2 + 0.05) q.setY(i, q.getY(i) - (hash1(i * 17 + 3) - 0.5) * 0.08);
  geo.computeVertexNormals();
  fb.add(geo, mat(0, L / 2, 0));
  fb.add(G.rbox(0.56, 0.035, 0.035, 0.005), mat(0, L - 0.12, 0));
  for (const dx of [-0.24, 0, 0.24]) fb.add(G.cyl(0.012, 0.014, 0.05, 8), mat(dx, (dx === 0 ? L + 0.02 : L - 0.08), 0));
  const fm = fb.mesh(mats.white);
  fallen.add(fm);
  // orient: lying down, pointing across the road (towards +z, angled)
  const base = new THREE.Vector3(x + 0.12, STREET_Y + 0.035, poleZ + 0.25);
  const dir = new THREE.Vector3(0.55, 0, 1).normalize();
  fallen.position.copy(base);
  fallen.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
  // rotate around its own axis a little so the crossarm lies flat-ish
  fallen.rotateY(0.3);
  fallen.updateMatrixWorld(true);
  grp.add(fallen);
  // attachment points of the fallen crossarm in world space
  const ends = [-0.24, 0, 0.24].map((dx) => new THREE.Vector3(dx, dx === 0 ? L + 0.04 : L - 0.06, 0).applyMatrix4(fallen.matrixWorld));
  // wires from neighbours drape down to the ground and the fallen arm
  for (const nb of [k - 1, k + 1]) {
    if (nb < 0 || nb >= polePts.length) continue;
    for (let j = 0; j < 3; j++) {
      const a = polePts[nb][j];
      const e = ends[j].clone();
      const mid = new THREE.Vector3().lerpVectors(a, e, 0.62);
      mid.y = STREET_Y + 0.01 + j * 0.006;
      mid.z += (j - 1) * 0.08 + (nb < k ? 0.35 : 0.2);
      const touch = new THREE.Vector3().lerpVectors(mid, e, 0.5);
      touch.y = STREET_Y + 0.008;
      const pts = [a, new THREE.Vector3().lerpVectors(a, mid, 0.45).setY(a.y * 0.55 + mid.y * 0.45 - 0.12), mid, touch, e];
      wi.add(tubeAlong(pts, 0.0055, 5));
    }
  }
  // loose wire ends curling on the road
  for (let j = 0; j < 2; j++) {
    const s = ends[j * 2].clone();
    const pts = [s];
    for (let i = 1; i < 7; i++) pts.push(new THREE.Vector3(s.x + Math.sin(i * 0.9 + j) * 0.18 + i * 0.05, STREET_Y + 0.008, s.z + i * 0.07 * (j ? 1 : -0.6)));
    wi.add(tubeAlong(pts, 0.005, 5));
  }
  grp.add(w.mesh(mats.white), wi.mesh(mats.wire));
  return grp;
}

// ---------------------------------------------------------------------------
// Storm props: felt cloud on a thin wire, rain rods.
// ---------------------------------------------------------------------------
export function buildStorm(mats, center) {
  const rng = mulberry32(SEED + 11);
  const grp = new THREE.Group();
  const cloud = new Bucket();
  const blobs = [];
  for (let i = 0; i < 34; i++) {
    const a = rng.range(0, Math.PI * 2);
    const rr = Math.sqrt(rng.next());
    const x = Math.cos(a) * rr * 3.3, z = Math.sin(a) * rr * 1.5;
    const r = rng.range(0.75, 1.35) * (1 - rr * 0.35);
    const y = rng.range(-0.15, 0.5) + (1 - rr) * 0.55;
    blobs.push([x, y, z, r]);
  }
  for (const [x, y, z, r] of blobs) {
    const g = new THREE.IcosahedronGeometry(1, 4);
    const p = g.attributes.position;
    const v = new THREE.Vector3();
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p, i);
      const wx = v.x * r + x, wy = v.y * r + y, wz = v.z * r + z;
      const n = valueNoise3(wx * 2.2, wy * 2.2, wz * 2.2, 3) * 0.06 + valueNoise3(wx * 22, wy * 22, wz * 22, 5) * 0.012;
      const flat = v.y < -0.2 ? 0.55 : 1; // slightly flattened underside
      v.set(v.x * r, v.y * r * flat, v.z * r).multiplyScalar(1 + n);
      p.setXYZ(i, v.x + x, v.y + y, v.z + z);
    }
    g.computeVertexNormals();
    cloud.add(g);
  }
  const cloudMesh = cloud.mesh(mats.felt);
  cloudMesh.position.copy(center);
  grp.add(cloudMesh);
  // suspension wire (nearly invisible)
  const wire = new THREE.Mesh(G.cyl(0.006, 0.006, 40, 6), mats.resin);
  wire.position.set(center.x + 0.3, center.y + 20.8, center.z);
  grp.add(wire);
  // rain: fine clear rods hanging under the cloud
  const N = 150;
  const rod = new THREE.CylinderGeometry(0.0065, 0.0065, 1, 6, 1).translate(0, -0.5, 0);
  const inst = new THREE.InstancedMesh(rod, mats.rain, N);
  const m = new THREE.Matrix4();
  for (let i = 0; i < N; i++) {
    const a = rng.range(0, Math.PI * 2);
    const rr = Math.sqrt(rng.next());
    const x = center.x + Math.cos(a) * rr * 3.0, z = center.z + Math.sin(a) * rr * 1.2;
    const top = center.y - 0.35 - rng.range(0, 0.3);
    const bottom = GROUND + rng.range(0.0, 1.6) * (rng.chance(0.4) ? 1 : 0.4);
    m.compose(new THREE.Vector3(x, top, z), new THREE.Quaternion(), new THREE.Vector3(1, top - bottom, 1));
    inst.setMatrixAt(i, m);
  }
  inst.castShadow = false;
  inst.receiveShadow = false;
  grp.add(inst);
  return grp;
}

// ---------------------------------------------------------------------------
// Problems set: three plinths with vignettes.
// ---------------------------------------------------------------------------
export function buildPlinths(mats, origin) {
  const grp = new THREE.Group();
  grp.position.copy(origin);
  const w = new Bucket(), wi = new Bucket(), og = new Bucket(), so = new Bucket(), br = new Bucket(), st = new Bucket(), rs = new Bucket();
  const PW = 3.4, PH = 1.7, gap = 0.55;
  const xs = [-(PW + gap), 0, PW + gap];
  for (const x of xs) w.add(G.rbox(PW, PH, PW, 0.012, 2), mat(x, PH / 2, 0));
  const top = PH;

  // (1) snapped pole with wires down
  {
    const x = xs[0];
    const st0 = new THREE.CylinderGeometry(0.06, 0.07, 0.9, 20, 4);
    const p = st0.attributes.position;
    for (let i = 0; i < p.count; i++) if (p.getY(i) > 0.3) p.setY(i, p.getY(i) + (hash1(i * 13 + 1) - 0.5) * 0.16);
    st0.computeVertexNormals();
    w.add(st0, mat(x - 0.75, top + 0.45, -0.3));
    // fallen part leaning from stump top down to the plinth
    const L = 2.7;
    const fg = new THREE.CylinderGeometry(0.052, 0.06, L, 20, 4);
    const q = fg.attributes.position;
    for (let i = 0; i < q.count; i++) if (q.getY(i) < -L / 2 + 0.1) q.setY(i, q.getY(i) - (hash1(i * 7 + 2) - 0.5) * 0.16);
    fg.computeVertexNormals();
    const fall = new THREE.Group();
    const fb = new Bucket();
    fb.add(fg, mat(0, L / 2, 0));
    fb.add(G.rbox(1.0, 0.07, 0.07, 0.01), mat(0, L - 0.22, 0));
    for (const dx of [-0.42, 0, 0.42]) fb.add(G.cyl(0.022, 0.026, 0.1, 12), mat(dx, dx === 0 ? L + 0.04 : L - 0.14, 0));
    fb.add(G.rbox(0.035, 0.26, 0.035, 0.005), mat(0.23, L - 0.36, 0, 0, 0, 0.75));
    fb.add(G.rbox(0.035, 0.26, 0.035, 0.005), mat(-0.23, L - 0.36, 0, 0, 0, -0.75));
    fall.add(fb.mesh(mats.white));
    fall.position.set(x - 0.62, top + 0.7, -0.22);
    const dir = new THREE.Vector3(0.82, -0.26, 0.3).normalize();
    fall.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
    fall.rotateY(0.9);
    fall.updateMatrix();
    grp.add(fall);
    fall.updateMatrixWorld(true);
    const inv = new THREE.Matrix4().copy(grp.matrixWorld).invert();
    const ends = [-0.42, 0, 0.42].map((dx) => new THREE.Vector3(dx, dx === 0 ? L + 0.09 : L - 0.1, 0).applyMatrix4(fall.matrix));
    // wires: from crossarm ends draping over the plinth and over its edge
    ends.forEach((e, j) => {
      const pts = [e];
      const end = new THREE.Vector3(x - 1.2 + j * 0.55, top + 0.004, 1.0 + j * 0.25);
      pts.push(new THREE.Vector3().lerpVectors(e, end, 0.4).setY(top + 0.25 - j * 0.05));
      pts.push(new THREE.Vector3().lerpVectors(e, end, 0.75).setY(top + 0.02));
      pts.push(end);
      pts.push(new THREE.Vector3(end.x + 0.25 - j * 0.15, top + 0.004, PW / 2 - 0.02));
      pts.push(new THREE.Vector3(end.x + 0.3 - j * 0.12, top - 0.25 - j * 0.12, PW / 2 + 0.012));
      wi.add(tubeAlong(pts, 0.011, 6));
      // loose wire back towards the stump
      const p2 = [e, new THREE.Vector3().lerpVectors(e, new THREE.Vector3(x - 0.9, top, -0.9), 0.5).setY(top + 0.15), new THREE.Vector3(x - 1.1 + j * 0.2, top + 0.004, -0.9 - j * 0.15), new THREE.Vector3(x - 1.4 + j * 0.25, top + 0.004, -1.35)];
      wi.add(tubeAlong(p2, 0.011, 6));
    });
  }

  // (2) house wall with a meter box and an orange horseshoe magnet
  {
    const x = xs[1];
    const M = mat(x, top, 0.35, 0, 0, 0);
    gableVolume(w, M, {
      W: 1.9, D: 1.3, H: 1.35, pitch: 0.75, t: 0.06, roofT: 0.07, overhang: 0.1, sideOv: 0.14,
      front: [[-0.55, 0.85, 0.3, 0.42]],
      left: [[0.65, 0.85, 0.3, 0.42]],
    });
    // fine horizontal siding lines on the front (thin raised strips)
    for (let y = 0.12; y < 1.32; y += 0.07) w.addLocal(G.box(1.96, 0.008, 0.008), mat(0, y, 0.064), M);
    // meter box with a round dial recess
    const mb = extrude(rect(0, 0, 0.42, 0.52), [rect(0, 0.08, 0.2, 0.2)], 0.09, 0.008);
    w.addLocal(mb, mat(0.2, 0.72, 0.06), M);
    w.addLocal(G.cyl(0.07, 0.07, 0.02, 32), mat(0.2, 0.8, 0.075, Math.PI / 2, 0, 0), M);
    w.addLocal(G.rbox(0.08, 0.035, 0.03, 0.006), mat(0.2, 0.56, 0.16), M);
    w.addLocal(G.cyl(0.018, 0.018, 0.7, 12), mat(0.2, 0.3, 0.09), M); // conduit
    // horseshoe magnet stuck on the meter box side
    const mm = new THREE.Matrix4().multiplyMatrices(M, mat(0.56, 0.78, 0.12, 0, 0, Math.PI / 2));
    og.addLocal(new THREE.TorusGeometry(0.12, 0.05, 20, 40, Math.PI), mat(0, 0, 0, 0, 0, 0), mm);
    og.addLocal(G.cyl(0.05, 0.05, 0.12, 20), mat(0.12, -0.06, 0), mm);
    og.addLocal(G.cyl(0.05, 0.05, 0.12, 20), mat(-0.12, -0.06, 0), mm);
    st.addLocal(G.cyl(0.051, 0.051, 0.05, 20), mat(0.12, -0.145, 0), mm);
    st.addLocal(G.cyl(0.051, 0.051, 0.05, 20), mat(-0.12, -0.145, 0), mm);
  }

  // (3) roof with dark-blue solar panels and a brass sun on a rod
  {
    const x = xs[2];
    const pitch = 0.62;
    const M = mat(x - 0.15, top, 0.0, 0, Math.PI / 2, 0);
    const W = 2.1, D = 2.3, H = 0.55;
    gableVolume(w, new THREE.Matrix4().multiplyMatrices(M, mat(0, 0, D / 2)), { W, D, H, pitch, t: 0.05, roofT: 0.06, sideOv: 0.12, front: [[0, 0.32, 0.26, 0.3]] });
    // panels on the slope facing the camera (local -x side of the house -> world +z)
    const Hr = H + (W / 2) * Math.tan(pitch);
    const slopeM = new THREE.Matrix4().multiplyMatrices(M, mat(0, 0, D / 2));
    const s = -1; // left slope
    const roofOff = 0.05 / Math.cos(pitch) + 0.06;
    for (let r = 0; r < 2; r++) for (let c = 0; c < 4; c++) {
      const along = 0.32 + r * 0.56; // distance down-slope from ridge
      const pz = -0.28 - c * 0.5 - 0.12; // along the ridge
      const px = s * Math.cos(pitch) * along;
      const py = Hr - Math.sin(pitch) * along + Math.cos(pitch) * roofOff + 0.02;
      const pm = new THREE.Matrix4().multiplyMatrices(slopeM, mat(px - s * Math.sin(pitch) * 0.02, py, pz, 0, 0, -s * pitch));
      so.addLocal(G.rbox(0.52, 0.03, 0.46, 0.006), mat(0, 0, 0), pm);
      // frame + cell grid
      st.addLocal(G.box(0.53, 0.034, 0.012), mat(0, 0, 0.23), pm);
      st.addLocal(G.box(0.53, 0.034, 0.012), mat(0, 0, -0.23), pm);
      st.addLocal(G.box(0.012, 0.034, 0.47), mat(0.26, 0, 0), pm);
      st.addLocal(G.box(0.012, 0.034, 0.47), mat(-0.26, 0, 0), pm);
      for (let k = 1; k < 4; k++) so.addLocal(G.box(0.5, 0.032, 0.003), mat(0, 0.0, -0.23 + k * 0.115), pm);
      for (let k = 1; k < 4; k++) so.addLocal(G.box(0.003, 0.032, 0.44), mat(-0.26 + k * 0.13, 0.0, 0), pm);
    }
    // brass sun on a thin rod rising from behind the ridge
    br.add(G.cyl(0.016, 0.016, 2.6, 12), mat(x + 0.75, top + 1.3, -0.55));
    br.add(G.sphere(0.24, 48, 32), mat(x + 0.75, top + 2.62, -0.55));
  }
  for (const [b, m] of [[w, mats.white], [wi, mats.wire], [og, mats.orange], [so, mats.solar], [br, mats.brass], [st, mats.steel], [rs, mats.resin]]) grp.add(b.mesh(m));
  return grp;
}

// ---------------------------------------------------------------------------
// Studio sweep (seamless table + backdrop). Rotated per beat to sit behind
// the subject. Profile: floor -> quarter circle -> wall.
// ---------------------------------------------------------------------------
export function buildSweep(material) {
  const R = 22, wall = 140, floor = 260, width = 520;
  const prof = [];
  prof.push([-floor, 0]);
  prof.push([0, 0]);
  for (let i = 1; i <= 32; i++) {
    const a = (i / 32) * Math.PI / 2;
    prof.push([Math.sin(a) * R, R - Math.cos(a) * R]);
  }
  prof.push([R, R + wall]);
  const pos = [], nor = [];
  for (let i = 0; i < prof.length - 1; i++) {
    const [u0, y0] = prof[i], [u1, y1] = prof[i + 1];
    const tx = u1 - u0, ty = y1 - y0;
    const l = Math.hypot(tx, ty);
    const n = [0, tx / l, -ty / l]; // normal pointing up / towards -u
    // in local: u -> -z (wall stands at -z), x across
    const a = [-width / 2, y0, -u0], b = [width / 2, y0, -u0], c = [width / 2, y1, -u1], d = [-width / 2, y1, -u1];
    const nn = [0, n[1], -n[2]];
    for (const p of [a, b, c, a, c, d]) { pos.push(...p); nor.push(...nn); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  const m = new THREE.Mesh(g, material);
  m.receiveShadow = true;
  m.castShadow = false;
  const holder = new THREE.Group();
  holder.add(m);
  return holder;
}
