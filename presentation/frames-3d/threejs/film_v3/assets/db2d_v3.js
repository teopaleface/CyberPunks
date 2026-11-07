// Daybreak v3 2D helpers: timing (window.V3), style-frame components (ping, leader,
// click rings, cursor, 3D-object sprite) and the 2.5D plate. No clocks (Teo: useless).
(function () {
  const V = window.V3;
  const FALLBACK = { '--db-orange': '#fa4616', '--db-cyan': '#00a3e0', '--db-blue': '#163fe8', '--db-ink': '#f5f7fa', '--db-navy': '#000f1e' };
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim() || FALLBACK[name] || '';
  // drive(tl, sceneStart, duration, fn): fn(absoluteTime) on every render (GSAP modifiers run on silent seeks too)
  function drive(tl, start, dur, fn) {
    const proxy = { t: 0 };
    fn(start);
    tl.fromTo(proxy, { t: 0 }, {
      t: dur, duration: dur, ease: 'none', immediateRender: true,
      modifiers: { t: (v) => { fn(start + Math.max(0, Math.min(dur, parseFloat(v)))); return v; } },
    }, 0);
  }
  const clamp = (x) => Math.max(0, Math.min(1, x));
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const E = {
    o2: (x) => 1 - (1 - x) * (1 - x), o3: (x) => 1 - Math.pow(1 - x, 3), o4: (x) => 1 - Math.pow(1 - x, 4),
    i2: (x) => x * x, i3: (x) => x * x * x, i4: (x) => x * x * x * x,
    io2: (x) => (x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2), io3: (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
    expo: (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)), sine: (x) => -(Math.cos(Math.PI * x) - 1) / 2,
    back: (x, c1 = 1.6) => { const c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); },
  };
  // seeded randomness (mulberry32): deterministic scatter
  function rng(seed) { let a = seed >>> 0; return () => { a = (a + 0x6d2b79f5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
  const line = (n) => V.lines[n - 1];
  const scene = (id) => V.scenes[id];
  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, attrs, parent) {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  const C = () => ({ navy: css('--db-navy'), ink: css('--db-ink'), orange: css('--db-orange'), cyan: css('--db-cyan'), blue: css('--db-blue') });
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

  // 2.5D plate: an <img> of a plate (or its alpha cutout) inside a full-frame wrapper,
  // moved by a camera: push (scale), pan (x/y in px), roll (deg); depth = parallax factor.
  function plate(parent, name, kind = 'up') {
    const P = (window.V3_PLATES || {})[name] || {};
    const src = kind === 'cut' ? P.cut || P.up : P.up;
    const w = document.createElement('div');
    w.className = 'v3-plate';
    w.style.cssText = 'position:absolute;left:0;top:0;width:1920px;height:1080px;will-change:transform;transform-origin:50% 50%';
    const im = document.createElement('img');
    im.src = src || ''; im.alt = '';
    im.style.cssText = 'position:absolute;left:0;top:0;width:1920px;height:1080px';
    w.appendChild(im); parent.appendChild(w);
    return {
      el: w, img: im,
      // cam: { s (scale), x, y (px), r (deg), ox, oy (origin px) }
      update(c) {
        gsap.set(w, { scaleX: (c.s ?? 1) * (c.sx ?? 1), scaleY: c.s ?? 1, x: c.x ?? 0, y: c.y ?? 0, rotation: c.r ?? 0, rotationX: c.rx ?? 0, transformPerspective: c.rx ? 1800 : 0, transformOrigin: `${c.ox ?? 960}px ${c.oy ?? 540}px`, filter: c.blur > 0.3 ? `blur(${c.blur.toFixed(1)}px)` : 'none', opacity: c.opacity ?? 1 });
      },
      // plate px (0..1920, 0..1080 in the un-transformed frame) -> screen px under the camera c
      map(px, py, c) {
        const s = c.s ?? 1, r = ((c.r ?? 0) * Math.PI) / 180, ox = c.ox ?? 960, oy = c.oy ?? 540;
        const dx = (px - ox) * s * (c.sx ?? 1), dy = (py - oy) * s;
        return [ox + dx * Math.cos(r) - dy * Math.sin(r) + (c.x ?? 0), oy + dx * Math.sin(r) + dy * Math.cos(r) + (c.y ?? 0)];
      },
    };
  }
  // waterfall entry for a list of elements (binary opacity, from below, power4.out; heavier first)
  function arrive(tl, sels, t, opts = {}) {
    let gap = opts.gap ?? 0.05;
    sels.forEach((s, i) => {
      const y = i === 0 ? (opts.y0 ?? 70) : (opts.y ?? 46);
      const d = i === 0 ? 0.2 : 0.15;
      tl.set(s, { opacity: 1 }, t);
      tl.fromTo(s, { y }, { y: 0, duration: d, ease: 'power4.out', immediateRender: false }, t);
      t += gap; gap *= 0.84;
    });
  }
  // waterfall cut exit UP (travel 230 px, 0.34 s power4.in, 0.18 s fade, stagger 0.022), ends on `cut`
  function leaveUp(tl, sels, cut) {
    sels.forEach((s, i) => {
      const start = cut - 0.34 - 0.022 * (sels.length - 1 - i);
      tl.to(s, { y: '-=230', duration: 0.34, ease: 'power4.in' }, start);
      tl.to(s, { opacity: 0, duration: 0.18, ease: 'none' }, start + 0.16);
    });
  }
  // key line: big Archivo lines in the left column; returns the ids (one per display line)
  function keyLines(root, prefix, lines, o = {}) {
    const size = o.size || 150, lh = o.lh || 0.92, left = o.left ?? 120, top = o.top ?? 250, cls = o.cls || 'display';
    return lines.map((txt, i) => {
      const d = document.createElement('div');
      d.id = `${prefix}${i + 1}`; d.className = cls;
      d.style.cssText = `position:absolute;left:${left}px;top:${top + i * size * lh}px;font-size:${size}px;opacity:0;white-space:nowrap;${o.align === 'center' ? 'width:1920px;left:0;text-align:center;' : ''}`;
      d.textContent = txt;
      root.appendChild(d);
      return '#' + d.id;
    });
  }
  // word time (absolute) of the first word matching re in VO line n
  const wordT = (n, re) => ((V.lines[n - 1].words.find((w) => re.test(w.w)) || V.lines[n - 1].words[0]).start);
  window.DB = { V, css, drive, keyLines, wordT, clamp, seg, E, rng, line, scene, el, ping, leader, clickRings, CURSOR_SVG, CURSOR_TIP, sprite, plate, arrive, leaveUp };
})();
