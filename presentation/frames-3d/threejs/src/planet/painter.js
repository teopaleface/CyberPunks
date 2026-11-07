// Painter: collects flat-world geometry (old units, ground at y = 0) into
// per-material groups, with a per-vertex colour and a per-vertex ANCHOR
// (flat x, z). Bending wraps the flat world onto a sphere of radius R:
//   - rigid objects (houses, trees, poles) share one anchor, so they stay
//     undeformed and stand radially on the surface (a real tiny-planet model);
//   - ground, roads and ribbons use the vertex itself as anchor, so they curve.
// Blend factor f: 1 = planet, 0 = flat map tangent to the planet's top
// (y = R). In between the radius is R / f, so the map unrolls like a sheet.
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

export const PLANET_R = 1.0; // planet radius, planet units
export const S = 1 / 9; // old (flat) units -> planet units

const _m = new THREE.Matrix4();

function clean(g) {
  let out = g.index ? g.toNonIndexed() : g.clone();
  for (const k of Object.keys(out.attributes)) if (k !== 'position' && k !== 'normal') out.deleteAttribute(k);
  if (!out.attributes.normal) out.computeVertexNormals();
  return out;
}

class Group {
  constructor(name) { this.name = name; this.parts = []; }
}

export class Painter {
  constructor(palette) {
    this.palette = palette; // name -> { group, color: THREE.Color }
    this.groups = new Map();
    this.anchor = [0, 0]; // current rigid anchor (flat x, z); null = per-vertex
    this.house = -1;
    this.cur = 'paint';
    this.color = new THREE.Color(1, 1, 1);
    this.jitter = 0;
  }
  // gableVolume() calls tint('wall'|'roof'|...) before each part
  tint(name, override) {
    const p = this.palette[name] || this.palette.paint;
    this.cur = p.group;
    this.color.copy(override || p.color);
    return this;
  }
  setColor(c) { this.color.copy(c); return this; }
  add(geom, matrix) {
    const g = clean(geom);
    if (matrix) g.applyMatrix4(matrix);
    const n = g.attributes.position.count;
    const col = new Float32Array(n * 3), anc = new Float32Array(n * 2), hid = new Float32Array(n);
    const pos = g.attributes.position.array;
    for (let i = 0; i < n; i++) {
      col[i * 3] = this.color.r; col[i * 3 + 1] = this.color.g; col[i * 3 + 2] = this.color.b;
      if (this.anchor) { anc[i * 2] = this.anchor[0]; anc[i * 2 + 1] = this.anchor[1]; }
      else { anc[i * 2] = pos[i * 3]; anc[i * 2 + 1] = pos[i * 3 + 2]; }
      hid[i] = this.house;
    }
    g.setAttribute('color', new THREE.BufferAttribute(col, 3));
    g.setAttribute('anchor', new THREE.BufferAttribute(anc, 2));
    g.setAttribute('house', new THREE.BufferAttribute(hid, 1));
    if (!this.groups.has(this.cur)) this.groups.set(this.cur, new Group(this.cur));
    this.groups.get(this.cur).parts.push(g);
    return this;
  }
  addLocal(geom, local, parent) {
    _m.multiplyMatrices(parent, local);
    return this.add(geom, _m);
  }
  // Build one BentMesh per group.
  build(materials) {
    const out = {};
    for (const [name, grp] of this.groups) {
      const geo = mergeGeometries(grp.parts, false);
      out[name] = new BentMesh(geo, materials[name] || materials.paint);
    }
    return out;
  }
}

// Sphere frame at flat anchor (planet units ax, az) for blend f.
const _up = new THREE.Vector3(0, 1, 0);
export function frameAt(ax, az, f, outP, outQ) {
  const R = PLANET_R;
  if (f < 1e-4) {
    outP.set(ax, R, az);
    outQ.identity();
    return;
  }
  const Rf = R / f;
  const r = Math.hypot(ax, az);
  const th = Math.atan2(az, ax);
  const phi = r / Rf;
  const sp = Math.sin(phi), cp = Math.cos(phi);
  const n = new THREE.Vector3(sp * Math.cos(th), cp, sp * Math.sin(th));
  outP.set(n.x * Rf, R - Rf + n.y * Rf, n.z * Rf);
  if (r < 1e-9) outQ.identity();
  else outQ.setFromAxisAngle(new THREE.Vector3(Math.sin(th), 0, -Math.cos(th)).multiplyScalar(-1), phi);
}

export class BentMesh {
  constructor(geo, material) {
    this.flatPos = geo.attributes.position.array.slice();
    this.flatNor = geo.attributes.normal.array.slice();
    this.anchor = geo.attributes.anchor.array;
    this.geo = geo;
    this.mesh = new THREE.Mesh(geo, material);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    this.mesh.frustumCulled = false;
    this.f = -1;
  }
  bend(f) {
    if (Math.abs(f - this.f) < 1e-6) return;
    this.f = f;
    const P = this.geo.attributes.position.array, N = this.geo.attributes.normal.array;
    const fp = this.flatPos, fn = this.flatNor, an = this.anchor;
    const n = P.length / 3;
    const R = PLANET_R;
    const flat = f < 1e-4;
    const Rf = flat ? 0 : R / f;
    let lastAx = NaN, lastAz = NaN;
    let px = 0, py = 0, pz = 0;
    let q00 = 1, q01 = 0, q02 = 0, q10 = 0, q11 = 1, q12 = 0, q20 = 0, q21 = 0, q22 = 1;
    for (let i = 0; i < n; i++) {
      const ax = an[i * 2], az = an[i * 2 + 1];
      if (ax !== lastAx || az !== lastAz) {
        lastAx = ax; lastAz = az;
        const AX = ax * S, AZ = az * S;
        if (flat) {
          px = AX; py = R; pz = AZ;
          q00 = 1; q01 = 0; q02 = 0; q10 = 0; q11 = 1; q12 = 0; q20 = 0; q21 = 0; q22 = 1;
        } else {
          const r = Math.hypot(AX, AZ);
          const phi = r / Rf;
          const sp = Math.sin(phi), cp = Math.cos(phi);
          const c = r > 1e-9 ? AX / r : 1, s = r > 1e-9 ? AZ / r : 0; // cos/sin theta
          px = sp * c * Rf; py = R - Rf + cp * Rf; pz = sp * s * Rf;
          // rotation by phi about axis k = (-s, 0, c) ... maps up -> (sp c, cp, sp s)
          const kx = -s, kz = c; // axis = up x radial = (s*?); see derivation below
          // Rodrigues with k = (kx, 0, kz): R = I cos + sin [k]x + (1-cos) k k^T
          const C = cp, Sn = sp, T = 1 - cp;
          // We need R*up = (sp c, cp, sp s). With k = (s, 0, -c): R*up = (k x up) sin + up cos
          // k x up = (s,0,-c) x (0,1,0) = (0*0-(-c)*1, (-c)*0 - s*0, s*1-0*0) = (c, 0, s). Good.
          const Kx = s, Kz = -c;
          q00 = C + Kx * Kx * T; q01 = -Kz * Sn; q02 = Kx * Kz * T;
          q10 = Kz * Sn;         q11 = C;        q12 = -Kx * Sn;
          q20 = Kz * Kx * T;     q21 = Kx * Sn;  q22 = C + Kz * Kz * T;
          void kx; void kz;
        }
      }
      const ox = (fp[i * 3] - ax) * S, oy = fp[i * 3 + 1] * S, oz = (fp[i * 3 + 2] - az) * S;
      P[i * 3] = px + q00 * ox + q01 * oy + q02 * oz;
      P[i * 3 + 1] = py + q10 * ox + q11 * oy + q12 * oz;
      P[i * 3 + 2] = pz + q20 * ox + q21 * oy + q22 * oz;
      const nx = fn[i * 3], ny = fn[i * 3 + 1], nz = fn[i * 3 + 2];
      N[i * 3] = q00 * nx + q01 * ny + q02 * nz;
      N[i * 3 + 1] = q10 * nx + q11 * ny + q12 * nz;
      N[i * 3 + 2] = q20 * nx + q21 * ny + q22 * nz;
    }
    this.geo.attributes.position.needsUpdate = true;
    this.geo.attributes.normal.needsUpdate = true;
    this.geo.computeBoundingSphere();
  }
}

// Same rotation as BentMesh.bend, as a quaternion, for dynamic objects.
export function planetFrame(axOld, azOld, f, yaw = 0, lift = 0) {
  const AX = axOld * S, AZ = azOld * S, R = PLANET_R;
  const p = new THREE.Vector3(), q = new THREE.Quaternion();
  if (f < 1e-4) {
    p.set(AX, R, AZ);
  } else {
    const Rf = R / f;
    const r = Math.hypot(AX, AZ);
    const phi = r / Rf;
    const c = r > 1e-9 ? AX / r : 1, s = r > 1e-9 ? AZ / r : 0;
    p.set(Math.sin(phi) * c * Rf, R - Rf + Math.cos(phi) * Rf, Math.sin(phi) * s * Rf);
    q.setFromAxisAngle(new THREE.Vector3(s, 0, -c), phi);
  }
  const qy = new THREE.Quaternion().setFromAxisAngle(_up, yaw);
  q.multiply(qy);
  const n = new THREE.Vector3(0, 1, 0).applyQuaternion(q);
  p.addScaledVector(n, lift * S);
  return { p, q, n };
}

export function place(obj, axOld, azOld, f, yaw = 0, lift = 0) {
  const { p, q } = planetFrame(axOld, azOld, f, yaw, lift);
  obj.position.copy(p);
  obj.quaternion.copy(q);
  obj.scale.setScalar(S);
}
