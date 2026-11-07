// Daybreak 2D helpers: read the 3D layer's tracks (screen positions of named
// anchors, per frame) and drive tracked elements from a GSAP timeline.
// The 2D layer only depends on window.DAYBREAK_TRACKS, so the 3D layer can be
// the Three.js previs or a Blender image sequence with the same tracks.
(function () {
  const T = window.DAYBREAK_TRACKS;
  const FPS = T.fps;
  const N = T.f.length;
  function idx(t) {
    const x = Math.max(0, Math.min(N - 1, t * FPS));
    const i = Math.floor(x);
    return [i, Math.min(N - 1, i + 1), x - i];
  }
  function at(name, t) {
    const a = T[name];
    if (!a) return { x: -999, y: -999, v: 0 };
    const [i, j, u] = idx(t);
    return { x: a[i][0] + (a[j][0] - a[i][0]) * u, y: a[i][1] + (a[j][1] - a[i][1]) * u, v: u < 0.5 ? a[i][2] : a[j][2] };
  }
  function planet(t) {
    const p = at('planet', t);
    const [i, j, u] = idx(t);
    return { x: p.x, y: p.y, r: T.planetR[i] + (T.planetR[j] - T.planetR[i]) * u };
  }
  // drive(tl, sceneStart, duration, fn): fn(absoluteTime) on every render
  function drive(tl, start, dur, fn) {
    const proxy = { t: 0 };
    fn(start);
    tl.fromTo(proxy, { t: 0 }, {
      t: dur, duration: dur, ease: 'none', immediateRender: true,
      modifiers: { t: (v) => { fn(start + Math.max(0, Math.min(dur, parseFloat(v)))); return v; } },
    }, 0);
  }
  const BEATS = [0.186, 0.975, 1.741, 2.531, 3.297, 4.087, 4.876, 5.642, 6.432, 7.221, 7.987, 8.777, 9.474, 9.543,
    10.309, 11.099, 11.865, 12.655, 13.444, 14.21, 15.0, 15.766, 16.556, 17.345, 18.111, 18.901, 19.69, 20.457,
    21.223, 22.012, 22.779, 23.568, 24.334, 25.124, 25.89, 26.68, 27.446, 28.235, 29.025, 29.791];
  // split a text element into masked words: <span class="w"><span class="wi">word</span></span>
  function words(el) {
    const txt = el.textContent.trim().split(/\s+/);
    el.innerHTML = txt.map((w) => `<span class="w"><span class="wi">${w}</span></span>`).join(' ');
    return el.querySelectorAll('.wi');
  }
  window.DB = { T, at, planet, drive, BEATS, words, map: T.map };
})();
