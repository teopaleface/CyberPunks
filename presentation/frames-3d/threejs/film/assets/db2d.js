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
  // read a design token from assets/theme.css
  const FALLBACK = { '--db-orange': '#fa4616', '--db-cyan': '#00a3e0', '--db-blue': '#163fe8', '--db-ink': '#f5f7fa', '--db-navy': '#000f1e',
    '--db-map-ground': '#041a30', '--db-map-ring': 'rgba(0,163,224,0.4)', '--db-map-road': '#1f3d5c', '--db-map-house': '#f5f7fa', '--db-field': '#e8b32a' };
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || FALLBACK[name] || '';
  // ---------------------------------------------------------------------------
  // Components ported 1:1 from presentation/frames-3d/styleframes/build.py
  // (bezel, ping, leader, chip, CURSOR, click_rings). Each returns an object
  // with update(...) so tracked elements follow the 3D anchors every frame.
  // ---------------------------------------------------------------------------
  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const C = () => ({ navy: css('--db-navy'), ink: css('--db-ink'), orange: css('--db-orange'), cyan: css('--db-cyan'), blue: css('--db-blue') });
  // 12 h dial: hour h (22..30 allowed) -> point
  function hpt(cx, cy, r, h) { const th = ((h % 12) / 12) * Math.PI * 2; return [cx + r * Math.sin(th), cy - r * Math.cos(th)]; }
  function arcD(cx, cy, r, h1, h2) {
    const [x1, y1] = hpt(cx, cy, r, h1), [x2, y2] = hpt(cx, cy, r, h2);
    const span = (((h2 - h1) % 12) + 12) % 12 / 12 * 360;
    if (span < 0.05) return `M${x1.toFixed(1)},${y1.toFixed(1)}`;
    return `M${x1.toFixed(1)},${y1.toFixed(1)} A${r.toFixed(1)},${r.toFixed(1)} 0 ${span > 180 ? 1 : 0} 1 ${x2.toFixed(1)},${y2.toFixed(1)}`;
  }
  function clockText(h) {
    let m = Math.round(((h % 1) * 60) / 5) * 5, hh = Math.floor(h);
    if (m === 60) { m = 0; hh += 1; }
    return String(hh % 24).padStart(2, '0') + ':' + String(m).padStart(2, '0');
  }
  // the night-shift clock as a bezel around the planet
  function bezel(svg) {
    const c = C();
    const g = el('g', { class: 'db-bezel' }, svg);
    const ring = el('circle', { fill: 'none', stroke: 'rgba(245,247,250,.16)', 'stroke-width': 1.5 }, g);
    const track = el('path', { fill: 'none', stroke: 'rgba(245,247,250,.10)', 'stroke-width': 8, 'stroke-linecap': 'round' }, g);
    const ticks = [];
    for (let i = 0; i < 24; i++) ticks.push(el('line', { stroke: `rgba(245,247,250,${i % 2 === 0 ? 0.55 : 0.25})`, 'stroke-width': 2 }, g));
    const nums = [[22, '22'], [0, '00'], [2, '02'], [4, '04'], [6, '06']].map(([h, txt]) => {
      const t = el('text', { 'text-anchor': 'middle', fill: 'rgba(245,247,250,.5)', class: 'db-bezel-num' }, g); t.textContent = txt; return { h, t };
    });
    const prog = el('path', { fill: 'none', stroke: c.cyan, 'stroke-width': 8, 'stroke-linecap': 'round' }, g);
    const mark = el('circle', { r: 15, fill: c.ink }, g);
    const lbl = el('text', { 'text-anchor': 'middle', fill: c.ink, class: 'db-bezel-time' }, g);
    const prev = el('text', { 'text-anchor': 'middle', fill: c.ink, class: 'db-bezel-time' }, g);
    return {
      g,
      update(cx, cy, r, now, sun = 0, o = {}) {
        const draw = o.draw ?? 1; // cold-open draw-on, clockwise from 22
        ring.setAttribute('cx', cx); ring.setAttribute('cy', cy); ring.setAttribute('r', r);
        ring.setAttribute('pathLength', 1); ring.setAttribute('stroke-dasharray', `${draw} 1.2`);
        ring.setAttribute('transform', `rotate(210 ${cx} ${cy})`);
        track.style.opacity = draw;
        ticks.forEach((ln, i) => { ln.style.opacity = Math.max(0, Math.min(1, draw * 24 - i * 0.6)); });
        track.setAttribute('d', arcD(cx, cy, r, 22, 6));
        ticks.forEach((ln, i) => {
          const h = i / 2;
          const [x1, y1] = hpt(cx, cy, r + 10, h), [x2, y2] = hpt(cx, cy, r + (i % 2 === 0 ? 34 : 22), h);
          ln.setAttribute('x1', x1.toFixed(1)); ln.setAttribute('y1', y1.toFixed(1)); ln.setAttribute('x2', x2.toFixed(1)); ln.setAttribute('y2', y2.toFixed(1));
        });
        for (const n of nums) {
          const d = Math.abs(((n.h - now) % 12 + 18) % 12 - 6);
          const [x, y] = hpt(cx, cy, r + 62, n.h);
          n.t.setAttribute('x', x.toFixed(1)); n.t.setAttribute('y', (y + 9).toFixed(1));
          n.t.style.opacity = d < 0.9 ? 0 : 1;
        }
        const col = sun > 0.5 ? c.orange : c.cyan;
        prog.setAttribute('d', arcD(cx, cy, r, 22, now)); prog.setAttribute('stroke', col);
        const [mx, my] = hpt(cx, cy, r, now);
        mark.setAttribute('cx', mx.toFixed(1)); mark.setAttribute('cy', my.toFixed(1)); mark.setAttribute('fill', sun > 0.5 ? c.orange : c.ink);
        const [lx, ly] = hpt(cx, cy, r + 112, now);
        // odometer: on a change the old time rolls up and the new one rolls in (0.2 s)
        const roll = o.roll ?? 1;
        lbl.setAttribute('x', lx.toFixed(1)); lbl.setAttribute('y', (ly + 14 + (1 - roll) * 22).toFixed(1)); lbl.textContent = clockText(now);
        lbl.style.opacity = draw * (0.25 + 0.75 * roll);
        prev.setAttribute('x', lx.toFixed(1)); prev.setAttribute('y', (ly + 14 - roll * 22).toFixed(1)); prev.textContent = o.prevLabel || '';
        prev.style.opacity = o.prevLabel ? draw * (1 - roll) : 0;
        prog.style.opacity = draw; mark.style.opacity = draw;
        for (const n of nums) n.t.style.opacity = (n.t.style.opacity === '0' ? 0 : 1) * draw;
      },
    };
  }
  // concentric ping in the source colour
  function ping(svg, color, big = true) {
    const c = C();
    const g = el('g', { class: 'db-ping' }, svg);
    const spec = big ? [[58, 0, 0.38], [34, 0, 0.8], [14, 1, 0]] : [[28, 0, 0.7], [12, 1, 0]];
    const rings = spec.map(([r, fill, op]) => el('circle', fill ? { r, fill: color, stroke: c.navy, 'stroke-width': 4 } : { r, fill: 'none', stroke: color, 'stroke-opacity': op, 'stroke-width': 3 }, g));
    return { g, rings, update(x, y) { g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`); } };
  }
  // elbow leader line
  function leader(svg, color) {
    const p = el('polyline', { fill: 'none', stroke: color, 'stroke-width': 3, 'stroke-linejoin': 'round', 'stroke-linecap': 'round', pathLength: 1, 'stroke-dasharray': '1 1.2', 'stroke-dashoffset': 1.1, class: 'db-leader' }, svg);
    return { el: p, update(points) { p.setAttribute('points', points.map(([x, y]) => x.toFixed(1) + ',' + y.toFixed(1)).join(' ')); } };
  }
  // click rings (two circles, expanded by the timeline on the click)
  function clickRings(svg, color) {
    const g = el('g', { class: 'db-click', opacity: 0 }, svg);
    el('circle', { r: 26, fill: 'none', stroke: color || css('--db-ink'), 'stroke-opacity': 0.7, 'stroke-width': 3 }, g);
    el('circle', { r: 46, fill: 'none', stroke: color || css('--db-ink'), 'stroke-opacity': 0.3, 'stroke-width': 2 }, g);
    return { g, update(x, y) { g.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`); } };
  }
  // the macOS cursor of the style frames (black body, white stroke); tip at (2,2) of 26x33
  const CURSOR_SVG = '<svg viewBox="0 0 26 33" class="db-cursor-svg"><path d="M2 2 L2 26 L8.2 20.4 L12.6 30.6 L16.9 28.8 L12.6 18.8 L21 18.8 Z" fill="#0B0B0C" stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  const CURSOR_TIP = [2 / 26, 2 / 33];
  // night-shift clock time per film second (monotone): 22:00 -> 06:00 at the sunrise beat
  const CLOCK_KEYS = [[0, 22.0], [3.297, 22.3], [5.642, 22.75], [9.474, 23.5], [11.099, 24.5], [14.0, 25.0], [16.556, 26.0], [20.457, 28.6], [22.012, 30.0], [30, 30.0]];
  // night (0.975 -> 8.777): the clock TICKS 5 min on each beat, with a tiny overshoot (back.out 1.6, 0.18 s)
  const TICKS = BEATS.filter((b) => b >= 0.975 && b <= 8.8);
  const backOut = (x, c1 = 1.6) => { const c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
  function clockTick(t) {
    // returns { h, roll (0..1 since the last step), prev (label before the step) }
    let k = -1;
    for (let i = 0; i < TICKS.length; i++) if (t >= TICKS[i]) k = i;
    const base = 22.0;
    if (t > 9.3) return { h: clockHour(t), roll: 1, prev: '' };
    const step = 5 / 60;
    if (k < 0) return { h: base, roll: 1, prev: '' };
    const x = Math.min(1, (t - TICKS[k]) / 0.18);
    const h = base + step * k + step * backOut(x);
    const r = Math.min(1, (t - TICKS[k]) / 0.2);
    return { h, roll: r, prev: r < 1 ? clockText(base + step * k) : '' };
  }
  function clockHour(t) {
    for (let i = 1; i < CLOCK_KEYS.length; i++) {
      const [t0, h0] = CLOCK_KEYS[i - 1], [t1, h1] = CLOCK_KEYS[i];
      if (t <= t1) { const u = Math.max(0, (t - t0) / (t1 - t0)); return h0 + (h1 - h0) * u; }
    }
    return 30;
  }
  // 3D hero object sprite: plays the spin/tumble atlas when the objects team has delivered it
  // (assets/objects/manifest.js), else the hero image with 2D rotation (same API, drops in).
  function sprite(parent, name) {
    const O = (window.DAYBREAK_OBJECTS || {})[name] || {};
    const wrap = document.createElement('div');
    wrap.className = 'db-obj';
    wrap.style.cssText = 'position:absolute;left:0;top:0;width:100px;height:100px;will-change:transform;pointer-events:none';
    const hero = document.createElement('img');
    hero.src = O.hero || ''; hero.alt = '';
    hero.style.cssText = 'position:absolute;inset:0;width:100%;height:100%';
    wrap.appendChild(hero);
    const atl = {};
    for (const mode of ['spin', 'tumble']) {
      if (!O[mode]) continue;
      const vp = document.createElement('div');
      vp.style.cssText = 'position:absolute;inset:0;overflow:hidden;display:none';
      const im = document.createElement('img');
      im.src = O[mode].src; im.alt = '';
      im.style.cssText = 'position:absolute;left:0;top:0;max-width:none';
      vp.appendChild(im); wrap.appendChild(vp);
      atl[mode] = { vp, im, ...O[mode] };
    }
    parent.appendChild(wrap);
    return {
      el: wrap, name, has: (m) => !!atl[m],
      // p: { x, y (centre), size, mode: 'hero'|'spin'|'tumble', u (0..1), rot (deg), blur (px), opacity, flipY (deg) }
      update(p) {
        const size = p.size;
        wrap.style.width = size + 'px'; wrap.style.height = size + 'px';
        let rot = p.rot || 0;
        const A = atl[p.mode];
        for (const k in atl) atl[k].vp.style.display = 'none';
        if (A) {
          const n = A.frames;
          const f = p.mode === 'spin' ? Math.floor(((p.u % 1) + 1) % 1 * n) % n : Math.min(n - 1, Math.max(0, Math.round(p.u * (n - 1))));
          A.vp.style.display = 'block'; hero.style.display = 'none';
          A.im.style.width = A.cols * size + 'px';
          A.im.style.left = -(f % A.cols) * size + 'px'; A.im.style.top = -Math.floor(f / A.cols) * size + 'px';
        } else {
          hero.style.display = 'block';
          if (p.mode === 'tumble') rot += (1 - p.u) * (p.spinDir || 1) * 300;
        }
        const rotY = p.mode === 'spin' && !A ? (p.u % 1) * 360 : (p.flipY || 0);
        gsap.set(wrap, { x: p.x - size / 2, y: p.y - size / 2, rotation: rot, rotationY: rotY, transformPerspective: 900, opacity: p.opacity ?? 1, filter: p.blur > 0.3 ? `blur(${p.blur.toFixed(1)}px)` : 'none' });
      },
      hide() { gsap.set(wrap, { opacity: 0 }); },
    };
  }
  window.DB = { T, at, planet, drive, BEATS, words, css, map: T.map, el, bezel, ping, leader, clickRings, CURSOR_SVG, CURSOR_TIP, clockHour, clockText, clockTick, sprite };
})();
