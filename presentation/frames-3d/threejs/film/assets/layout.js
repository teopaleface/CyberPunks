// Shared layout for the product window (style frame 03) and the flat map inside it.
// Used by compositions/ui.html (draws it) and compositions/objects.html (the 3D
// objects land exactly on the map stops), so both agree to the pixel.
(function () {
  const WIN = { left: 250, top: 300, w: 1420, h: 740, tilt: 9, persp: 2600, header: 86 };
  const MAPBOX = { x: 34, y: 114, w: 900, h: 600 }; // inside the window
  const M = window.DAYBREAK_TRACKS.map;
  // fit the flat village (screen coords of the flat 3D map at t = 10.1) into the map box
  const R = M.radius * 0.86;
  const s = (MAPBOX.h - 40) / (2 * R);
  const toMap = ([x, y]) => [MAPBOX.w / 2 + (x - M.center[0]) * s, MAPBOX.h / 2 + 10 + (y - M.center[1]) * s];
  // window-local point -> screen (CSS: perspective(p) rotateX(tilt), origin 50% 0)
  function winPoint(wx, wy, yOffset = 0) {
    const a = (WIN.tilt * Math.PI) / 180;
    const dx = wx - WIN.w / 2;
    const yr = wy * Math.cos(a), zr = wy * Math.sin(a);
    const k = WIN.persp / (WIN.persp - zr);
    return [WIN.left + WIN.w / 2 + dx * k, WIN.top + yOffset + yr * k, k];
  }
  // map point (map-box coords) -> screen
  const mapToScreen = ([mx, my], yOffset = 0) => winPoint(MAPBOX.x + mx, MAPBOX.y + my, yOffset);
  // stops of each route in map coords; and which stop each problem object lands on
  const stops = M.routes.map((r) => ({ key: r.key, pts: r.pins.map(toMap), path: r.pts.map(toMap) }));
  function nearestStop(key, anchorName) {
    const T = window.DAYBREAK_TRACKS;
    const a = T[anchorName][Math.round(10.1 * T.fps)];
    const am = toMap([a[0], a[1]]);
    const st = stops.find((q) => q.key === key);
    let best = 0, bd = 1e9;
    st.pts.forEach((p, i) => { const d = Math.hypot(p[0] - am[0], p[1] - am[1]); if (d < bd) { bd = d; best = i; } });
    return { key, index: best, map: st.pts[best] };
  }
  const LAND = {
    pole: nearestStop('orange', 'fallen_pole'),
    meter: nearestStop('blue', 'meter'),
    solar: nearestStop('cyan', 'hot_roof'),
  };
  // crew pills tied to the trucks (style frame 04): pill top-left = truck + offset;
  // the icon slot (where the 3D truck sprite lands) is at the pill's left end
  const CHIP = { 1: [40, 56], 2: [56, -116], 3: [-340, 56] };
  function chip(n, t) {
    const T = window.DAYBREAK_TRACKS;
    const a = window.DB.at('truck_' + n, t);
    const [dx, dy] = CHIP[n];
    const x = a.x + dx, y = a.y + dy;
    return { x, y, ix: x + 34, iy: y + 28, ax: a.x, ay: a.y, v: a.v };
  }
  window.DBL = { WIN, MAPBOX, toMap, winPoint, mapToScreen, stops, LAND, scale: s, chip, CHIP };
})();
