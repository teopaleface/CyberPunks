// Planet Daybreak scene: builds the world, the dynamic props and applies
// the film state for any time t (pure function of t).
import * as THREE from 'three';
import { Bucket, G, mat, tubeAlong, sagPoints } from '../geo.js';
import { hash1, mulberry32, valueNoise3 } from '../prng.js';
import { buildPlanet, PPC, ROADS, SMOOTH, DEPOT, R3J, R4J, polyLen, polyAt, smoothPoly, offsetPoly } from './world.js';
import { Painter, BentMesh, planetFrame, place, S, PLANET_R } from './painter.js';
import { T, seg, ease, blendAt, lightAt, makeCameraTrack } from './timeline.js';

const C = (h) => new THREE.Color(h);

function makeMaterials() {
  const glass = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.22, metalness: 0, emissive: C(0xffb25a), emissiveIntensity: 1 });
  glass.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nattribute float lit;\nvarying float vLit;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvLit = lit;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying float vLit;')
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance *= vLit;');
  };
  glass.customProgramCacheKey = () => 'glassLit';
  const sat = (hex) => new THREE.MeshPhysicalMaterial({ color: hex, roughness: 0.34, metalness: 0, sheen: 0.8, sheenRoughness: 0.35, sheenColor: C(hex).lerp(C(0xffffff), 0.4) });
  return {
    paint: new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.84, metalness: 0 }),
    ground: new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.96, metalness: 0 }),
    glass,
    solar: new THREE.MeshPhysicalMaterial({ color: 0x1c2a4a, roughness: 0.25, clearcoat: 0.7, clearcoatRoughness: 0.2 }),
    truckWhite: new THREE.MeshStandardMaterial({ color: 0xf1efe9, roughness: 0.48 }),
    truckOrange: new THREE.MeshStandardMaterial({ color: PPC.orange, roughness: 0.5 }),
    dark: new THREE.MeshStandardMaterial({ color: 0x2a2a2b, roughness: 0.7 }),
    tyre: new THREE.MeshStandardMaterial({ color: 0x1f1f20, roughness: 0.9 }),
    tglass: new THREE.MeshStandardMaterial({ color: 0x1b2128, roughness: 0.18 }),
    lamp: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: C(0xfff0d0), emissiveIntensity: 3.0 }),
    beacon: new THREE.MeshStandardMaterial({ color: PPC.orange, emissive: C(PPC.orange), emissiveIntensity: 0.6 }),
    hivis: new THREE.MeshStandardMaterial({ color: PPC.orange, roughness: 0.75, emissive: C(PPC.orange), emissiveIntensity: 0.08 }),
    reflect: new THREE.MeshStandardMaterial({ color: 0xd9dad5, roughness: 0.4 }),
    trousers: new THREE.MeshStandardMaterial({ color: 0x343a44, roughness: 0.9 }),
    skin: new THREE.MeshStandardMaterial({ color: 0xc89a7a, roughness: 0.8 }),
    hat: new THREE.MeshStandardMaterial({ color: 0xf4f3ee, roughness: 0.45 }),
    concrete: new THREE.MeshStandardMaterial({ color: 0xa7a59f, roughness: 0.9 }),
    wire: new THREE.MeshStandardMaterial({ color: 0x2b2a28, roughness: 0.6, vertexColors: true }),
    felt: new THREE.MeshPhysicalMaterial({ color: 0x8b8d90, roughness: 1, sheen: 1, sheenRoughness: 0.5, sheenColor: C(0xc9cbce) }),
    rain: new THREE.MeshStandardMaterial({ color: 0xdfe8f0, roughness: 0.15, transparent: true, opacity: 0.45, depthWrite: false }),
    ribbon: { orange: sat(PPC.orange), cyan: sat(PPC.cyan), blue: sat(PPC.blue) },
    pin: { orange: new THREE.MeshStandardMaterial({ color: PPC.orange, roughness: 0.3 }), cyan: new THREE.MeshStandardMaterial({ color: PPC.cyan, roughness: 0.3 }), blue: new THREE.MeshStandardMaterial({ color: PPC.blue, roughness: 0.3 }) },
    steel: new THREE.MeshStandardMaterial({ color: 0xcfd1d3, roughness: 0.3, metalness: 1 }),
    sun: new THREE.MeshBasicMaterial({ color: new THREE.Color().setRGB(0.98, 0.2, 0.03) }),
  };
}

// ---- props built in old units (placed with place()) ------------------------
function buildTruck(M) {
  const w = new Bucket(), o = new Bucket(), d = new Bucket(), ty = new Bucket(), gl = new Bucket(), lp = new Bucket(), bc = new Bucket();
  const I = new THREE.Matrix4();
  for (const z of [0.46, -0.42]) for (const sx of [-1, 1]) {
    ty.addLocal(G.cyl(0.1, 0.1, 0.07, 18), mat(sx * 0.21, 0.1, z, 0, 0, Math.PI / 2), I);
    w.addLocal(G.cyl(0.05, 0.05, 0.075, 12), mat(sx * 0.212, 0.1, z, 0, 0, Math.PI / 2), I);
  }
  d.addLocal(G.rbox(0.36, 0.07, 1.4, 0.01), mat(0, 0.15, 0), I);
  w.addLocal(G.rbox(0.5, 0.38, 0.4, 0.04, 2), mat(0, 0.37, 0.52), I); // cab
  gl.addLocal(G.rbox(0.43, 0.15, 0.012, 0.004), mat(0, 0.47, 0.722), I);
  for (const sx of [-1, 1]) gl.addLocal(G.rbox(0.012, 0.13, 0.2, 0.004), mat(sx * 0.252, 0.47, 0.57), I);
  d.addLocal(G.rbox(0.52, 0.06, 0.05, 0.012), mat(0, 0.19, 0.735), I); // bumper
  lp.addLocal(G.rbox(0.08, 0.04, 0.012, 0.004), mat(-0.17, 0.26, 0.726), I);
  lp.addLocal(G.rbox(0.08, 0.04, 0.012, 0.004), mat(0.17, 0.26, 0.726), I);
  bc.addLocal(G.rbox(0.08, 0.035, 0.05, 0.008), mat(0, 0.58, 0.5), I);
  // utility body
  w.addLocal(G.rbox(0.5, 0.28, 0.9, 0.015), mat(0, 0.33, -0.24), I);
  for (const sx of [-1, 1]) {
    o.addLocal(G.box(0.006, 0.03, 0.9), mat(sx * 0.252, 0.29, -0.24), I); // orange stripe
    o.addLocal(G.box(0.006, 0.03, 0.4), mat(sx * 0.252, 0.29, 0.52), I);
  }
  // boom + bucket (white)
  w.addLocal(G.cyl(0.07, 0.08, 0.08, 16), mat(0, 0.51, -0.58), I);
  w.addLocal(G.rbox(0.07, 0.065, 1.0, 0.01), mat(0, 0.6, -0.1, -0.03, 0, 0), I);
  w.addLocal(G.rbox(0.19, 0.18, 0.18, 0.015), mat(0, 0.6, -0.72), I);
  o.addLocal(G.box(0.195, 0.02, 0.185), mat(0, 0.67, -0.72), I);
  const g = new THREE.Group();
  for (const [b, m] of [[w, M.truckWhite], [o, M.truckOrange], [d, M.dark], [ty, M.tyre], [gl, M.tglass], [lp, M.lamp], [bc, M.beacon]]) g.add(b.mesh(m));
  return g;
}

function buildWorker(M, pose = {}) {
  const tr = new Bucket(), hv = new Bucket(), rf = new Bucket(), sk = new Bucket(), ht = new Bucket(), lp = new Bucket();
  const I = new THREE.Matrix4();
  const lean = pose.lean || 0;
  // legs
  for (const sx of [-1, 1]) tr.addLocal(G.rbox(0.045, 0.17, 0.05, 0.015), mat(sx * 0.03, 0.085, (pose.walk || 0) * sx * 0.02, (pose.walk || 0) * sx * 0.3, 0, 0), I);
  const Mt = mat(0, 0.17, 0, lean, 0, 0);
  hv.addLocal(G.rbox(0.11, 0.13, 0.065, 0.02), mat(0, 0.07, 0), Mt);
  rf.addLocal(G.box(0.112, 0.012, 0.067), mat(0, 0.04, 0), Mt);
  rf.addLocal(G.box(0.112, 0.012, 0.067), mat(0, 0.09, 0), Mt);
  // arms
  const arm = (sx, a, b) => {
    const Ma = new THREE.Matrix4().multiplyMatrices(Mt, mat(sx * 0.068, 0.125, 0, a, 0, sx * b));
    hv.addLocal(G.rbox(0.035, 0.12, 0.035, 0.012), mat(0, -0.055, 0), Ma);
    sk.addLocal(G.sphere(0.018, 8, 6), mat(0, -0.12, 0), Ma);
    return Ma;
  };
  const aL = arm(-1, pose.armL ?? 0.15, pose.spreadL ?? 0.12);
  arm(1, pose.armR ?? -0.1, pose.spreadR ?? 0.12);
  if (pose.torch) lp.addLocal(G.cyl(0.012, 0.016, 0.06, 8), mat(0, -0.14, 0.02, Math.PI / 2, 0, 0), aL);
  const Mh = new THREE.Matrix4().multiplyMatrices(Mt, mat(0, 0.165, 0, pose.look || 0, 0, 0));
  sk.addLocal(G.sphere(0.03, 12, 10), mat(0, 0.02, 0), Mh);
  ht.addLocal(new THREE.SphereGeometry(0.036, 14, 8, 0, Math.PI * 2, 0, Math.PI / 2), mat(0, 0.035, 0), Mh);
  ht.addLocal(G.cyl(0.044, 0.044, 0.006, 14), mat(0, 0.034, 0.004), Mh);
  const g = new THREE.Group();
  for (const [b, m] of [[tr, M.trousers], [hv, M.hivis], [rf, M.reflect], [sk, M.skin], [ht, M.hat], [lp, M.lamp]]) g.add(b.mesh(m));
  g.traverse((o) => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

function buildPin(mat3) {
  const g = new THREE.Group();
  const needle = new THREE.Mesh(G.cyl(0.012, 0.006, 0.62, 8), mat3.steel);
  needle.position.y = 0.31;
  const head = new THREE.Mesh(G.sphere(0.13, 28, 18), mat3.head);
  head.position.y = 0.66;
  for (const m of [needle, head]) { m.castShadow = true; m.receiveShadow = true; }
  g.add(needle, head);
  return g;
}

// ---------------------------------------------------------------------------
export function buildScene(scene) {
  const M = makeMaterials();
  const W = buildPlanet();
  const bent = W.painter.build({ paint: M.paint, ground: M.ground, glass: M.glass, solar: M.solar });
  const bentList = Object.values(bent);
  for (const b of bentList) scene.add(b.mesh);
  bent.ground.mesh.castShadow = true;
  // per-vertex window light attribute
  const gg = bent.glass.geo;
  const lit = new Float32Array(gg.attributes.position.count);
  gg.setAttribute('lit', new THREE.BufferAttribute(lit, 1));
  const houseAttr = gg.attributes.house.array;

  // wires: static (bent per vertex), storm-intact, storm-fallen
  const mkWires = (list, drooped) => {
    const P = new Painter({ wire: { group: 'wire', color: C(0x2b2a28) } });
    P.anchor = null;
    P.tint('wire');
    for (const w of list) for (let k = 0; k < 3; k++) {
      const a = W.poleTops[w.a][k], b = W.poleTops[w.b][k];
      if (drooped) {
        const keep = w.a === W.stormPole ? b : a;
        const fp = W.poles[W.stormPole];
        const end = new THREE.Vector3(fp.x + (k - 1) * 0.25 + 0.6, 0.06, fp.z + 0.7 + k * 0.1);
        const mid = keep.clone().lerp(end, 0.55); mid.y = 0.15;
        P.add(tubeAlong([keep, keep.clone().lerp(mid, 0.5).setY(keep.y * 0.5), mid, end], 0.012, 5));
      } else P.add(tubeAlong(sagPoints(a, b, 0.14, 14), 0.011, 5));
    }
    return P.build({ wire: M.wire }).wire;
  };
  const wiresStatic = mkWires(W.wires.filter((w) => !w.storm), false);
  const wiresStorm = mkWires(W.wires.filter((w) => w.storm), false);
  const wiresDown = mkWires(W.wires.filter((w) => w.storm), true);
  for (const b of [wiresStatic, wiresStorm, wiresDown]) scene.add(b.mesh);
  bentList.push(wiresStatic, wiresStorm, wiresDown);

  // the storm pole (dynamic: falls on the beat)
  const pole = new THREE.Group();
  {
    const b = new Bucket();
    b.add(G.cyl(0.03, 0.042, 1.9, 10), mat(0, 0.95, 0));
    b.add(G.rbox(0.56, 0.04, 0.04, 0.006), mat(0, 1.78, 0));
    const inner = b.mesh(M.concrete);
    pole.add(inner);
    const stump = new THREE.Mesh(G.cyl(0.04, 0.043, 0.28, 10), M.concrete);
    stump.position.y = 0.14;
    stump.castShadow = true;
    pole.userData.stump = stump;
    scene.add(pole);
    const sh = new THREE.Group();
    sh.add(stump);
    scene.add(sh);
    pole.userData.stumpGroup = sh;
  }

  // trucks, workers, pins
  const trucks = [0, 1, 2, 3, 4].map(() => { const t = buildTruck(M); scene.add(t); return t; });
  const depotWorkers = [
    buildWorker(M, { armL: -0.9, armR: -0.7, lean: 0.1 }), buildWorker(M, { armR: -1.2, look: 0.1 }), buildWorker(M, { armL: 0.2, armR: -0.5 }),
  ];
  const poleWorkers = [
    buildWorker(M, { look: -0.5, armL: -1.1, torch: true }), buildWorker(M, { look: -0.45, armR: -0.4 }), buildWorker(M, { look: -0.3, walk: 0.6 }),
  ];
  for (const w of [...depotWorkers, ...poleWorkers]) scene.add(w);

  // parked trucks in the yard
  const park = [0, 1, 2, 3, 4].map((i) => {
    const lx = -2.1 + i * 1.05, lz = 0.25 + (i % 2) * 0.12;
    const yawL = [0.1, -0.06, 0.04, -0.09, 0.12][i];
    const x = DEPOT.x + lx * Math.cos(DEPOT.yaw) + lz * Math.sin(DEPOT.yaw);
    const z = DEPOT.z - lx * Math.sin(DEPOT.yaw) + lz * Math.cos(DEPOT.yaw);
    return { x, z, yaw: DEPOT.yaw + yawL };
  });

  // ---- ribbons (three routes from the depot) ------------------------------
  const r1 = SMOOTH.R1;
  const idxJ = r1.reduce((b, p, i) => (Math.hypot(p[0], p[1]) < Math.hypot(r1[b][0], r1[b][1]) ? i : b), 0);
  const trunk = r1.slice(0, idxJ + 1);
  const r3j = r1.reduce((b, p, i) => (Math.hypot(p[0] - R3J[0], p[1] - R3J[1]) < Math.hypot(r1[b][0] - R3J[0], r1[b][1] - R3J[1]) ? i : b), 0);
  const housesOn = (road, sMin = 0) => W.houses.filter((h) => h.road === road && h.s > sMin).sort((a, b) => a.s - b.s);
  const gate = [DEPOT.x + 2.4 * Math.sin(DEPOT.yaw), DEPOT.z + 2.4 * Math.cos(DEPOT.yaw)];
  const routeDefs = [
    { key: 'orange', truck: 3, path: (st) => [...st, ...offsetPoly(trunk, -0.42), ...r1.slice(idxJ + 1)], road: 'R1', sMin: polyLen(trunk) + 0.5, n: 4 },
    { key: 'cyan', truck: 2, path: (st) => [...st, ...offsetPoly(trunk, 0), ...SMOOTH.R2.slice(1)], road: 'R2', sMin: 0, n: 4 },
    { key: 'blue', truck: 1, path: (st) => [...st, ...offsetPoly(r1.slice(0, r3j + 1), 0.42), ...SMOOTH.R3.slice(1)], road: 'R3', sMin: 0, n: 3 },
  ];
  const routes = routeDefs.map((R) => {
    const pk = park[R.truck];
    const fwd = [Math.sin(pk.yaw), Math.cos(pk.yaw)];
    const st = [[pk.x, pk.z], [pk.x + fwd[0] * 0.9, pk.z + fwd[1] * 0.9], [gate[0] + (R.truck - 2) * 0.25, gate[1]]];
    let pts = smoothPoly(R.path(st), 2);
    // pick pin houses along this road, and cut the path just past the last
    const hs = housesOn(R.road, R.sMin).filter((h) => !(R.key === 'blue' && false)).slice(0, R.n);
    const dense = [];
    const L0 = polyLen(pts);
    for (let s = 0; s <= L0; s += 0.08) dense.push(polyAt(pts, s));
    const near = (h) => dense.reduce((b, p, i) => (Math.hypot(p.x - h.x, p.z - h.z) < Math.hypot(dense[b].x - h.x, dense[b].z - h.z) ? i : b), 0);
    const pinIdx = hs.map(near);
    const endIdx = Math.min(dense.length - 1, Math.max(...pinIdx) + 8);
    const path = dense.slice(0, endIdx + 1);
    const L = (path.length - 1) * 0.08;
    // ribbon strip (flat), anchored per vertex
    const P = new Painter({ r: { group: 'r', color: C(0xffffff) } });
    P.anchor = null; P.tint('r');
    const w = 0.34, y = 0.07 + R.truck * 0.004;
    const pos = [];
    for (let i = 0; i < path.length - 1; i++) {
      const a = path[i], b = path[i + 1];
      const ax0 = a.x - a.dz * w / 2, az0 = a.z + a.dx * w / 2, ax1 = a.x + a.dz * w / 2, az1 = a.z - a.dx * w / 2;
      const bx0 = b.x - b.dz * w / 2, bz0 = b.z + b.dx * w / 2, bx1 = b.x + b.dz * w / 2, bz1 = b.z - b.dx * w / 2;
      pos.push(ax0, y, az0, bx0, y, bz0, bx1, y, bz1, ax0, y, az0, bx1, y, bz1, ax1, y, az1);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.computeVertexNormals();
    P.add(g);
    const bm = P.build({ r: M.ribbon[R.key] }).r;
    bm.mesh.castShadow = false;
    scene.add(bm.mesh);
    bentList.push(bm);
    const pins = hs.map((h, k) => {
      const pin = buildPin({ steel: M.steel, head: M.pin[R.key] });
      scene.add(pin);
      return { pin, house: h, u: pinIdx[k] / (path.length - 1), k };
    });
    return { key: R.key, truck: R.truck, path, L, mesh: bm, segs: path.length - 1, pins };
  });

  // detour for the "unsure" house: from the R1/R4 junction along R4
  const unsure = W.houses.find((h) => h.id === W.anchors.unsure_house?.house);
  const detour = (() => {
    const r4 = SMOOTH.R4;
    const pts = [];
    const L = polyLen(r4);
    const target = unsure ? r4.reduce((b, p, i) => (Math.hypot(p[0] - unsure.x, p[1] - unsure.z) < Math.hypot(r4[b][0] - unsure.x, r4[b][1] - unsure.z) ? i : b), 0) : 10;
    for (let s = 0; s <= L; s += 0.08) { const p = polyAt(r4, s); pts.push(p); if (Math.hypot(p.x - r4[target][0], p.z - r4[target][1]) < 0.1) break; }
    return pts;
  })();
  const askPin = buildPin({ steel: M.steel, head: M.pin.cyan });
  scene.add(askPin);

  // ---- storm cloud + rain ----------------------------------------------------
  const cloud = new THREE.Group();
  {
    const rng = mulberry32(77);
    const b = new Bucket();
    for (let i = 0; i < 140; i++) {
      const a = rng.range(0, 6.28), rr = Math.sqrt(rng.next());
      const x = Math.cos(a) * rr * 0.78, z = Math.sin(a) * rr * 0.38;
      const r = rng.range(0.07, 0.17) * (1 - rr * 0.35);
      const g = new THREE.IcosahedronGeometry(1, 4);
      const p = g.attributes.position;
      const v = new THREE.Vector3();
      for (let k = 0; k < p.count; k++) {
        v.fromBufferAttribute(p, k);
        const n = valueNoise3(v.x * 3 + i, v.y * 3, v.z * 3, i) * 0.25 + valueNoise3(v.x * 16, v.y * 16, v.z * 16 + i, 3) * 0.09 + valueNoise3(v.x * 45, v.y * 45, v.z * 45 + i, 5) * 0.035;
        v.multiplyScalar(1 + n);
        if (v.y < -0.3) v.y = -0.3 + (v.y + 0.3) * 0.4;
        p.setXYZ(k, v.x, v.y, v.z);
      }
      g.computeVertexNormals();
      b.add(g, mat(x, rng.range(-0.03, 0.16) * (1 - rr) + (1 - rr) * 0.14, z, rng.range(0, 3), rng.range(0, 3), 0, r, r * 0.9, r));
    }
    cloud.add(b.mesh(M.felt));
    const rain = new Bucket();
    for (let i = 0; i < 70; i++) {
      const a = rng.range(0, 6.28), rr = Math.sqrt(rng.next());
      const x = Math.cos(a) * rr * 0.62, z = Math.sin(a) * rr * 0.28;
      const len = rng.range(0.25, 0.75);
      rain.add(G.cyl(0.0018, 0.0018, len, 4), mat(x, -0.08 - len / 2, z));
      rain.add(G.sphere(0.006, 6, 4), mat(x, -0.08 - len, z));
    }
    cloud.add(rain.mesh(M.rain, { cast: false }));
    const wire = new THREE.Mesh(G.cyl(0.0015, 0.0015, 12, 4), M.rain);
    wire.position.y = 6.1;
    cloud.add(wire);
    scene.add(cloud);
  }

  // ---- the sun ---------------------------------------------------------------
  const sun = new THREE.Mesh(G.sphere(0.32, 48, 32), M.sun);
  sun.castShadow = false;
  scene.add(sun);

  const anchorsFlat = W.anchors;
  const resolveTarget = (name) => {
    const a = anchorsFlat[name];
    const { p, n } = planetFrame(a.x, a.z, 1, 0, 0.35);
    return [p.x, p.y, p.z];
  };
  const resolveNormal = (name) => {
    const a = anchorsFlat[name];
    const { n } = planetFrame(a.x, a.z, 1, 0, 0);
    return [n.x, n.y, n.z];
  };
  const solveHouseAz = (k) => {
    const n = resolveNormal(k.rel);
    return { az: (Math.atan2(n[0], n[2]) * 180) / Math.PI + (k.az || 0) + 4, el: Math.min(78, (Math.asin(n[1]) * 180) / Math.PI + (k.el || 0) + 2) };
  };
  const camTrack = makeCameraTrack(resolveTarget, resolveNormal, solveHouseAz);

  // window light groups: order houses by azimuth for the storm and the dawn sweep
  const order = W.houses.map((h) => h.id).sort((a, b) => {
    const ha = W.houses[a], hb = W.houses[b];
    return Math.atan2(ha.z, ha.x) - Math.atan2(hb.z, hb.x);
  });
  const rank = new Map(order.map((id, i) => [id, i / order.length]));

  return { M, W, bentList, trucks, park, routes, detour, askPin, pole, cloud, sun, depotWorkers, poleWorkers, wires: { wiresStatic, wiresStorm, wiresDown }, camTrack, rank, lit, houseAttr, unsure };
}

// ---------------------------------------------------------------------------
// Ribbon head arc-length (old units) at time t: lands on pin k at pin beat k.
export function ribbonProgress(route, t) {
  const [t0, t1] = T.ribbons;
  if (t <= t0) return 0;
  const keys = [[t0, 0]];
  route.pins.forEach((p, k) => keys.push([T.pins[k], p.u]));
  keys.push([T.pins[route.pins.length - 1] + 0.5, 1]);
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const x = seg(t, keys[i - 1][0], keys[i][0]);
      const e = 0.5 * x + 0.5 * ease.inOutSine(x);
      return keys[i - 1][1] + (keys[i][1] - keys[i - 1][1]) * e;
    }
  }
  return 1;
}

export function applyAt(SC, t) {
  const f = blendAt(t);
  for (const b of SC.bentList) b.bend(f);

  // window lights
  const offAt = (id) => {
    const r = SC.rank.get(id) ?? 0;
    return T.lightsOff[Math.min(T.lightsOff.length - 1, Math.floor(r * T.lightsOff.length))];
  };
  const onAt = (id) => T.windowsOn[0] + (SC.rank.get(id) ?? 0) * (T.windowsOn[1] - T.windowsOn[0]);
  const L = SC.lit, H = SC.houseAttr;
  let last = -2, val = 0;
  for (let i = 0; i < L.length; i++) {
    const id = H[i];
    if (id !== last) {
      last = id;
      if (id < 0) val = 0;
      else {
        const off = t >= offAt(id) && t < onAt(id);
        const flick = hash1(id * 13) < 0.12 ? 0 : 1; // a few homes stay dark all night
        val = off ? 0 : flick * (4.0 - 2.6 * seg(t, 22.5, 25.0));
      }
    }
    L[i] = val;
  }
  SC.M.glass.userData.dirty = true;
  const litAttr = SC.bentList.find((b) => b.geo.attributes.lit)?.geo.attributes.lit;
  if (litAttr) litAttr.needsUpdate = true;

  // storm pole fall
  const fp = SC.W.poles[SC.W.stormPole];
  const kFall = seg(t, T.poleFall, T.poleFall + 0.38);
  const fall = kFall < 1 ? ease.inCubic(kFall) * 1.52 : 1.52 - Math.sin(seg(t, T.poleFall + 0.38, T.poleFall + 0.6) * Math.PI) * 0.06;
  const roadDir = fp.yaw - Math.PI / 2;
  place(SC.pole, fp.x, fp.z, f, roadDir + 0.9, 0.28);
  SC.pole.rotateX(fall);
  place(SC.pole.userData.stumpGroup, fp.x, fp.z, f, 0, 0);
  SC.pole.userData.stumpGroup.visible = t >= T.poleFall;
  if (t < T.poleFall) { place(SC.pole, fp.x, fp.z, f, roadDir + 0.9, 0); }
  SC.wires.wiresStorm.mesh.visible = t < T.poleFall + 0.3;
  SC.wires.wiresDown.mesh.visible = t >= T.poleFall + 0.3;

  // cloud (above the storm pole), slides in and out
  {
    const kIn = ease.outCubic(seg(t, T.cloudIn[0], T.cloudIn[1]));
    const kOut = ease.inCubic(seg(t, T.cloudOut[0], T.cloudOut[1]));
    SC.cloud.visible = kIn > 0 && kOut < 1;
    const { p, q, n } = planetFrame(fp.x - 0.5, fp.z + 0.6, f, 0, 0);
    const side = new THREE.Vector3(1, 0, -0.4).normalize();
    SC.cloud.position.copy(p).addScaledVector(n, 0.62).add(new THREE.Vector3(0, 0.42, 0)).addScaledVector(side, (1 - kIn) * 2.2 - kOut * 2.6); // passes over and leaves on the far side (no ping-pong)
    SC.cloud.quaternion.identity(); // hangs plumb: the wire stays vertical, rain falls straight down
    SC.cloud.scale.setScalar(0.5);
  }

  // trucks
  SC.trucks.forEach((tk, i) => { const pk = SC.park[i]; place(tk, pk.x, pk.z, f, pk.yaw, 0.045); tk.visible = true; });
  for (const r of SC.routes) {
    const p = ribbonProgress(r, t);
    const n = Math.floor(p * r.segs);
    r.mesh.geo.setDrawRange(0, n * 6);
    r.mesh.mesh.visible = n > 0;
    const head = p * r.L;
    // truck follows behind the head
    const lagT = t - 0.45;
    const ph = ribbonProgress(r, lagT) * r.L;
    let s = Math.max(0, ph - 1.2);
    // orange truck stops at the R4 junction and then takes the detour
    const tk = SC.trucks[r.truck];
    const atS = (ss) => r.path[Math.min(r.path.length - 1, Math.max(0, Math.round(ss / 0.08)))];
    if (r.key === 'orange') {
      const jIdx = r.path.reduce((b, q, i) => (Math.hypot(q.x - R4J[0], q.z - R4J[1]) < Math.hypot(r.path[b].x - R4J[0], r.path[b].z - R4J[1]) ? i : b), 0);
      const sJ = jIdx * 0.08;
      s = Math.min(s, sJ);
      const kT = ease.inOutCubic(seg(t, T.turn[0], T.turn[1]));
      if (kT > 0) {
        const d = SC.detour;
        const q = d[Math.min(d.length - 1, Math.round(kT * (d.length - 1) * 0.8))];
        place(tk, q.x, q.z, f, Math.atan2(q.dx, q.dz), 0.035);
        continue;
      }
    }
    const q = atS(s);
    const inYard = s < 1.6;
    place(tk, q.x, q.z, f, Math.atan2(q.dx, q.dz), inYard ? 0.045 : 0.035);
    void head;
    for (const pin of r.pins) {
      const tk2 = T.pins[pin.k];
      const k = seg(t, tk2 - 0.28, tk2 + 0.1);
      pin.pin.visible = k > 0;
      const h = pin.house;
      // falls, hits the roof on the beat, small bounce (back.out 1.5 feel)
      const fall = k < 0.72 ? 1 - ease.inCubic(k / 0.72) : -Math.sin(((k - 0.72) / 0.28) * Math.PI) * 0.06;
      place(pin.pin, h.x, h.z, f, 0, h.ridge * 0.92 + fall * 2.6);
    }
  }
  // ask pin
  {
    // the 2D card collapses into the cyan pin; the 3D pin takes over when it hits the house (19.25)
    SC.askPin.visible = t >= T.askPin[1] && !!SC.unsure;
    const kb = seg(t, T.askPin[1], T.askPin[1] + 0.2);
    if (SC.unsure) place(SC.askPin, SC.unsure.x, SC.unsure.z, f, 0, SC.unsure.ridge * 0.92 - Math.sin(kb * Math.PI) * 0.12);
  }

  // workers: by the trucks in the depot, and at the fallen pole after it falls
  SC.depotWorkers.forEach((w, i) => {
    const pk = SC.park[[1, 2, 3][i]];
    place(w, pk.x + Math.cos(pk.yaw) * 0.42 * (i - 1) + 0.3, pk.z - Math.sin(pk.yaw) * 0.42 + 0.35, f, pk.yaw + Math.PI + i * 0.8, 0.045);
  });
  SC.poleWorkers.forEach((w, i) => {
    w.visible = t > T.poleFall + 0.5 && t < 20.5;
    const a = [0.2, 0.9, -0.5][i];
    place(w, fp.x + 0.9 + Math.cos(a) * 0.4, fp.z + 0.55 + Math.sin(a) * 0.4, f, -2.2 + i * 0.7, 0.035);
  });
  return { f };
}

// Light setup for t (key may be the moon or the sun)
export function lightsFor(SC, t, cam) {
  const Lm = lightAt(t);
  // sun: rises behind the planet, opposite the camera, slightly to the right
  const cx = cam.pos[0], cz = cam.pos[2];
  const ca = Math.atan2(cx, cz);
  const sa = ca + Math.PI - 0.62;
  const rise = Lm.sun;
  const sunPos = new THREE.Vector3(Math.sin(sa) * 7.5, -0.9 + rise * 2.3, Math.cos(sa) * 7.5);
  SC.sun.position.copy(sunPos);
  SC.sun.visible = false; // the sun disc is drawn in the 2D layer (tracked); only its light is 3D
  let key;
  if (rise > 0.02) {
    const d = sunPos.clone().normalize();
    // blend from the moon direction to the sun direction
    const el = Math.asin(Math.max(-0.2, d.y)) * 180 / Math.PI;
    const az = Math.atan2(d.x, d.z) * 180 / Math.PI;
    key = { az, el: Math.max(4, el), kelvin: 2900, intensity: Lm.sunKey.intensity + Lm.moon.intensity, spread: 2.5 };
  } else key = { ...Lm.moon, spread: 4 };
  return { key, sky: Lm.sky, env: Lm.env, exposure: Lm.exposure };
}

// Anchors in world space (planet units) for t
export function anchorWorld(SC, t, f) {
  const out = {};
  for (const [name, a] of Object.entries(SC.W.anchors)) {
    const { p, n } = planetFrame(a.x, a.z, f, 0, a.h);
    out[name] = { p, n };
  }
  SC.routes.forEach((r, i) => {
    const tk = SC.trucks[r.truck];
    const n = new THREE.Vector3(0, 1, 0).applyQuaternion(tk.quaternion);
    out[`truck_${i + 1}`] = { p: tk.position.clone().addScaledVector(n, 0.75 * S), n };
  });
  out.planet = { p: new THREE.Vector3(0, 0, 0), n: new THREE.Vector3(0, 1, 0) };
  (SC.darkPick || []).forEach((id, k) => { const h = SC.W.houses[id]; const { p, n } = planetFrame(h.x, h.z, f, 0, h.ridge * 0.6); out[`dark_${k}`] = { p, n }; });
  out.sun = { p: SC.sun.position.clone(), n: SC.sun.position.clone().normalize(), always: true };
  SC.routes.forEach((r) => r.pins.forEach((pin, k) => {
    const h = pin.house;
    const { p, n } = planetFrame(h.x, h.z, f, 0, h.ridge * 0.92 + 0.66);
    out[`pin_${r.key}_${k}`] = { p, n };
  }));
  return out;
}
