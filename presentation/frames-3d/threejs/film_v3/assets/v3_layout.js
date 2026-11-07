// Daybreak v3: anchor points on each plate, in the plate's own 1920x1080 space.
// Measured on the delivered plates (re-measure when a plate changes: render/v3_plates.py
// prints which plates are placeholders). Scenes map these through their camera.
window.V3L = {
  // measured on the FINAL plates (plates_v3/up, 19:28), in plate px (1920x1080 space)
  planet: {
    p01_storm: { c: [1273, 563], r: 506 },
    p02_dark: { c: [1273, 563], r: 506 },
    p04_wide: { c: [1265, 575], r: 500 },
    p11_dawn: { c: [1100, 1900], r: 1000 },
    p12_day: { c: [1260, 540], r: 540 },
  },
  // horizontal placement of each plate (px) so the left column stays free for type
  offset: { p01_storm: 0, p02_dark: 160, p04_wide: 0 },
  // vertical lift of the horizon plates (px)
  lift: { p11_dawn: 0, p12_day: 0 },
  // scene 12/13 framing of the day planet: pushed right and a touch smaller so the left column holds the type
  frame12: { x: 200, s: 0.9 },
  // the cotton cloud crosses in the FOREGROUND (the plate has its own cloud), big and soft
  cloud: { from: [2350, 980], to: [-560, 820], size: 760, blur: 3 },
  // three houses that go dark on "Houses" / "go" / "dark" (lit windows on p02)
  dark: [[870, 746], [1040, 470], [1776, 392]],
  magnet: [1480, 600],
  solar: [1390, 410],
  depot: [1270, 262],
  // a 16:9 region of the flat half of p06 (the camera pushes into it; it becomes the app map)
  flat: { x0: 720, y0: 380, x1: 1440, y1: 785 },
  map: {
    depot: [930, 250],
    spots: [[400, 330], [380, 580], [460, 840], [1540, 380], [1480, 710], [1240, 630], [1220, 910], [740, 1040], [1640, 660], [1240, 120], [380, 120], [980, 520]],
    urgent: [5, 4, 0, 6],
    house: [1480, 710],
    objects: { meter: 4, cloud: 5, solar: 3 },
    routes: [
      [[930, 250], [700, 260], [560, 300], [470, 330], [400, 330]],
      [[930, 250], [700, 260], [560, 300], [600, 500], [470, 580], [380, 580]],
      [[930, 250], [700, 260], [560, 300], [600, 500], [680, 700], [560, 840], [460, 840]],
      [[930, 250], [700, 260], [560, 300], [600, 500], [680, 700], [760, 840], [745, 960], [740, 1040]],
      [[930, 250], [1200, 260], [1290, 300], [1450, 380], [1540, 380]],
      [[930, 250], [1200, 260], [1290, 300], [1320, 500], [1480, 600], [1480, 710]],
      [[930, 250], [1200, 260], [1290, 300], [1320, 500], [1240, 630]],
      [[930, 250], [700, 260], [560, 300], [600, 500], [680, 700], [760, 840], [980, 780], [1100, 860], [1220, 910]],
      [[930, 250], [1200, 260], [1290, 300], [1320, 500], [1560, 560], [1640, 660]],
      [[930, 250], [1200, 260], [1260, 180], [1240, 120]],
      [[930, 250], [700, 250], [530, 180], [380, 120]],
    ],
  },
  house: [730, 645],
  houseScreen: [1290, 760],
  sun: { c: [1460, 860], r: 420 },
};

// the app map camera (scene 7): full frame at the seam, then FLIP into the window slot.
// Shared so scene 10 can place the house exactly where scene 7 left its marker (seam F carrier).
(function () {
  const SLOT = { x: 120 + 24, y: 190 + 96, w: 1100, h: 740 };
  const fitS = Math.min(SLOT.w / 1920, SLOT.h / 1080) * 1.12;
  function mapCam(t) {
    const S = window.V3.scenes.s07, E = window.DB.E, seg = window.DB.seg;
    const k = E.io3(seg(t, S.start + 0.05, S.start + 0.75));
    const push = 1 + 0.04 * E.sine(seg(t, S.start + 0.75, S.end));
    const s = (1 + (fitS - 1) * k) * push;
    const cx = 960 + (SLOT.x + SLOT.w / 2 - 960) * k, cy = 540 + (SLOT.y + SLOT.h / 2 - 540) * k;
    return { s, x: cx - 960, y: cy - 540, ox: 960, oy: 540, k };
  }
  function mapPoint(p, t) {
    const c = mapCam(t), dx = (p[0] - 960) * c.s, dy = (p[1] - 540) * c.s;
    return [960 + dx + c.x, 540 + dy + c.y];
  }
  Object.assign(window.V3L, { SLOT, mapCam, mapPoint });
})();
