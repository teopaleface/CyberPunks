"""Scrie scena 5 (agentul pe hartă) ca schiță: București-Ilfov, lucrări SINTETICE, trasee ilustrative.

Schița ține locul capturii reale din consola dispecerului (se înlocuiește după ora 01:00).
Rulare (din rădăcina repo-ului): uv run --with shapely python presentation/scripts/build_s5_scene.py
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import re

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRES = ROOT / "presentation"
GEO = json.loads((PRES / "video/assets/geo/regions.json").read_text())
OUT = PRES / "video/compositions/s5-agent.html"
W, H = 1920, 1080
SEED = 20261108


def path_to_polys(d: str) -> list[Polygon]:
    polys = []
    for ring in re.findall(r"M([^Z]+)Z", d):
        pts = [tuple(map(float, p.split(","))) for p in ring.split("L")]
        if len(pts) >= 3:
            polys.append(Polygon(pts))
    return polys


def main() -> None:
    buc = unary_union(path_to_polys(GEO["counties"]["BUCURESTI"]))
    ilf = unary_union(path_to_polys(GEO["counties"]["ILFOV"]))
    area = unary_union([buc, ilf])
    minx, miny, maxx, maxy = area.bounds
    # Cadru 16:9 în jurul zonei, cu margine; jos lăsăm loc pentru cele patru cuvinte.
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2 + 4
    vb_h = (maxy - miny) * 1.32
    vb_w = vb_h * W / H
    vb = (cx - vb_w / 2, cy - vb_h / 2, vb_w, vb_h)
    k = W / vb_w  # pixeli de ecran pe unitate de imagine z8

    def scr(x: float, y: float) -> tuple[float, float]:
        return (x - vb[0]) * k, (y - vb[1]) * k

    def svg_path(geom) -> str:
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        out = []
        for p in polys:
            pts = [scr(x, y) for x, y in p.exterior.coords]
            out.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
        return "".join(out)

    rng = random.Random(SEED)
    pts = []
    while len(pts) < 46:
        # mai dese în București
        if len(pts) < 26:
            x = rng.uniform(*buc.bounds[0::2])
            y = rng.uniform(*buc.bounds[1::2])
            geom = buc
        else:
            x = rng.uniform(minx, maxx)
            y = rng.uniform(miny, maxy)
            geom = ilf
        if geom.contains(Point(x, y)):
            sx, sy = scr(x, y)
            if all(math.hypot(sx - p[0], sy - p[1]) > 34 for p in pts):
                kind = "C" if rng.random() < 0.3 else "A"
                score = round(rng.betavariate(2.2, 2.4), 2)
                pts.append((sx, sy, kind, score))

    depots = {d: scr(*GEO["points"][d]) for d in ("D-BUC-V", "D-BUC-E")}
    order = sorted(range(len(pts)), key=lambda i: -pts[i][3])
    assigned = order[:14]
    # Încredere mică: trei lucrări trimise la om, alese departe una de alta, ca etichetele să nu se suprapună.
    review: set[int] = set()
    for i in order[14:]:
        if all(math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]) > 190 for j in review):
            review.add(i)
        if len(review) == 3:
            break
    # Patru trasee: împărțim lucrările alocate după depoul cel mai apropiat, apoi vecinul cel mai apropiat.
    groups: dict[str, list[int]] = {"D-BUC-V": [], "D-BUC-E": []}
    for i in assigned:
        d = min(depots, key=lambda dd: math.hypot(pts[i][0] - depots[dd][0], pts[i][1] - depots[dd][1]))
        groups[d].append(i)
    routes = []
    for d, items in groups.items():
        items = sorted(items, key=lambda i: math.atan2(pts[i][1] - depots[d][1], pts[i][0] - depots[d][0]))
        half = max(1, len(items) // 2)
        for chunk in (items[:half], items[half:]):
            if not chunk:
                continue
            seq, cur, left = [], depots[d], list(chunk)
            while left:
                nxt = min(left, key=lambda i: math.hypot(pts[i][0] - cur[0], pts[i][1] - cur[1]))
                seq.append(nxt)
                cur = pts[nxt][:2]
                left.remove(nxt)
            routes.append((d, seq))

    circles, rings, labels, route_paths, stops = [], [], [], [], []
    for i, (x, y, kind, score) in enumerate(pts):
        r = 7 if kind == "A" else 6
        shape = (
            f'<circle id="s5-p{i}" class="s5-pt s5-a" cx="{x:.1f}" cy="{y:.1f}" r="{r}"/>'
            if kind == "A"
            else f'<rect id="s5-p{i}" class="s5-pt s5-c" x="{x - r:.1f}" y="{y - r:.1f}" width="{2 * r}" height="{2 * r}" rx="2"/>'
        )
        circles.append(shape)
        if i in review:
            rings.append(f'<circle id="s5-q{i}" class="s5-review" cx="{x:.1f}" cy="{y:.1f}" r="17"/>')
            labels.append(f'<text id="s5-ql{i}" class="s5-review-label" x="{x + 26:.1f}" y="{y + 9:.1f}">la om</text>')
    for ri, (d, seq) in enumerate(routes):
        dx, dy = depots[d]
        coords = [(dx, dy)] + [pts[i][:2] for i in seq]
        dpath = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        route_paths.append(f'<path id="s5-r{ri}" class="s5-route" pathLength="1" d="{dpath}"/>')
        for si, i in enumerate(seq):
            stops.append((ri, si, len(seq), i))
    depot_svg = "".join(
        f'<rect class="s5-depot" x="{x - 11:.1f}" y="{y - 11:.1f}" width="22" height="22" rx="4"/>' for x, y in depots.values()
    )
    stop_svg = "".join(
        f'<circle id="s5-s{ri}-{si}" class="s5-stop" cx="{pts[i][0]:.1f}" cy="{pts[i][1]:.1f}" r="15"/>'
        for ri, si, n, i in stops
    )
    focus = next(i for i in assigned if pts[i][2] == "A")
    fx, fy = pts[focus][0], pts[focus][1]
    data = {
        "focus": [round(fx, 1), round(fy, 1)],
        "points": [[round(p[0], 1), round(p[1], 1), p[2], p[3]] for p in pts],
        "assigned": assigned,
        "review": sorted(review),
        "routes": [[ri, len(seq)] for ri, (d, seq) in enumerate(routes)],
    }
    html = TEMPLATE.format(
        area=svg_path(area),
        buc=svg_path(buc),
        points="".join(circles),
        rings="".join(rings),
        labels="".join(labels),
        routes="".join(route_paths),
        stops=stop_svg,
        depots=depot_svg,
        post=f'<rect id="s5-post" class="s5-post" x="{fx + 26:.1f}" y="{fy - 34:.1f}" width="20" height="20" rx="3"/>'
        f'<path id="s5-post-link" class="s5-post-link" d="M{fx + 8:.1f},{fy - 6:.1f}L{fx + 26:.1f},{fy - 20:.1f}"/>',
        data=json.dumps(data),
    )
    OUT.write_text(html)
    print(OUT, "points", len(pts), "routes", [len(s) for _, s in routes])


TEMPLATE = """<template>
  <!-- Generat de presentation/scripts/build_s5_scene.py. Schiță cu date SINTETICE; se înlocuiește cu captura din consolă. -->
  <style>
    #root {{
      position: absolute;
      inset: 0;
      overflow: hidden;
      background: var(--ground);
    }}
    #s5-scene {{
      position: absolute;
      inset: 0;
    }}
    #s5-cam {{
      position: absolute;
      inset: 0;
      transform-origin: 0 0;
    }}
    .s5-post {{ fill: var(--ground); stroke: var(--ink); stroke-width: 2.5; }}
    .s5-post-link {{ stroke: var(--ink); stroke-width: 1.5; stroke-dasharray: 3 3; }}
    /* Bilanțul postului: energia ieșită din post față de suma contoarelor clienților (schiță, valori ilustrative fără cifre). */
    #s5-bil {{
      position: absolute;
      left: 1040px;
      top: 330px;
      width: 560px;
      padding: 28px 32px 30px;
      border-radius: 14px;
      background: rgba(11, 22, 34, 0.92);
      box-shadow: inset 0 0 0 1.5px rgba(245, 244, 240, 0.22);
    }}
    #s5-bil-title {{ font-size: 46px; font-weight: 600; letter-spacing: -0.025em; color: var(--ink); }}
    .s5-bil-row {{ display: flex; align-items: center; gap: 18px; margin-top: 22px; }}
    .s5-bil-name {{ width: 200px; flex: none; font-size: 28px; font-weight: 450; color: var(--ink-2); }}
    .s5-bil-bar {{ height: 26px; border-radius: 3px; transform-origin: 0 50%; }}
    #s5-bil-out {{ width: 280px; background: var(--ink); }}
    #s5-bil-sum {{ width: 196px; background: rgba(245, 244, 240, 0.4); }}
    #s5-bil-gap {{ width: 84px; height: 26px; border-radius: 3px; box-shadow: inset 0 0 0 2px var(--ink); background: repeating-linear-gradient(135deg, rgba(245,244,240,0.35) 0 6px, transparent 6px 12px); transform-origin: 0 50%; }}
    #s5-map {{
      position: absolute;
      left: 0;
      top: 0;
      width: 1920px;
      height: 1080px;
    }}
    .s5-area {{ fill: rgba(242, 239, 232, 0.035); stroke: rgba(242, 239, 232, 0.28); stroke-width: 1.5; }}
    .s5-buc {{ fill: rgba(242, 239, 232, 0.04); stroke: rgba(242, 239, 232, 0.2); stroke-width: 1.2; }}
    .s5-a {{ fill: var(--src-a); }}
    .s5-c {{ fill: var(--src-c); }}
    .s5-review {{ fill: none; stroke: var(--ink); stroke-width: 2; stroke-dasharray: 5 5; }}
    .s5-review-label {{ fill: var(--ink); font-family: var(--font-display); font-size: 28px; font-weight: 500; }}
    .s5-route {{ fill: none; stroke: var(--ink); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }}
    .s5-stop {{ fill: none; stroke: var(--ink); stroke-width: 3.5; }}
    .s5-depot {{ fill: var(--ground); stroke: var(--ink); stroke-width: 3; }}
    #s5-steps {{
      position: absolute;
      left: 0;
      right: 0;
      bottom: 92px;
      display: flex;
      justify-content: center;
      gap: 88px;
      font-size: 46px;
      font-weight: 550;
      letter-spacing: -0.02em;
    }}
    .s5-step {{ color: var(--ink); opacity: 0.3; }}
    #s5-head {{
      position: absolute;
      left: 120px;
      top: 84px;
      font-size: 64px;
      font-weight: 600;
      letter-spacing: -0.03em;
      color: var(--ink);
    }}
    #s5-note {{
      position: absolute;
      left: 120px;
      bottom: 36px;
      font-size: 24px;
      font-weight: 450;
      color: var(--ink-3);
    }}
  </style>
  <div id="root" data-composition-id="s5" data-width="1920" data-height="1080">
    <div id="s5-scene" class="clip" data-start="0" data-duration="6.25" data-layout-allow-overflow>
      <div id="s5-cam">
        <svg id="s5-map" viewBox="0 0 1920 1080" data-layout-ignore>
          <path class="s5-area" d="{area}"/>
          <path class="s5-buc" d="{buc}"/>
          <g id="s5-routes">{routes}</g>
          <g id="s5-points">{points}</g>
          <g id="s5-rings">{rings}</g>
          <g id="s5-labels">{labels}</g>
          <g id="s5-stops">{stops}</g>
          <g id="s5-depots">{depots}</g>
          <g id="s5-postg">{post}</g>
        </svg>
      </div>
      <div id="s5-steps">
        <span id="s5-st1" class="s5-step">Perceive</span>
        <span id="s5-st2" class="s5-step">Estimate</span>
        <span id="s5-st3" class="s5-step">Decide</span>
        <span id="s5-st4" class="s5-step">Act</span>
      </div>
      <h2 id="s5-head">Aceleași echipe, un singur plan.</h2>
      <div id="s5-bil">
        <div id="s5-bil-title">Bilanțul confirmă.</div>
        <div class="s5-bil-row"><span class="s5-bil-name">ieșit din post</span><div id="s5-bil-out" class="s5-bil-bar"></div></div>
        <div class="s5-bil-row"><span class="s5-bil-name">facturat</span><div id="s5-bil-sum" class="s5-bil-bar"></div><div id="s5-bil-gap"></div></div>
      </div>
      <p id="s5-note" data-layout-ignore>Schiță cu date sintetice. Se înlocuiește cu captura reală din consola dispecerului.</p>
    </div>
  </div>
  <script>
    (function () {{
      const D = {data};
      const tl = gsap.timeline({{ paused: true }});
      const F = D.focus, S = 1.85;
      const at = (s) => ({{ x: 960 * (1 - s), y: 540 * (1 - s), scale: s }});
      tl.fromTo("#s5-cam", at(1.0), {{ ...at(1.035), duration: 2.45, ease: "power1.inOut" }}, 0);
      // Decide: camera intră pe contorul cel mai sigur și pe postul lui.
      tl.to("#s5-cam", {{ x: 760 - S * F[0], y: 520 - S * F[1], scale: S, duration: 0.45, ease: "power3.inOut" }}, 2.5);
      tl.fromTo("#s5-bil", {{ opacity: 0, x: 24, filter: "blur(8px)" }}, {{ opacity: 1, x: 0, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, 2.8);
      tl.fromTo("#s5-bil-out", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.4, ease: "power3.out" }}, 2.9);
      tl.fromTo("#s5-bil-sum", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.4, ease: "power3.out" }}, 2.98);
      tl.fromTo("#s5-bil-gap", {{ opacity: 0, scaleX: 0 }}, {{ opacity: 1, scaleX: 1, duration: 0.3, ease: "power3.out" }}, 3.3);
      tl.fromTo(["#s5-post", "#s5-post-link"], {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, 2.7);
      tl.to("#s5-bil", {{ opacity: 0, filter: "blur(8px)", duration: 0.2, ease: "power3.in" }}, 3.62);
      // Act: înapoi la toată harta, traseele se desenează.
      tl.to("#s5-cam", {{ ...at(1.05), duration: 0.45, ease: "power3.inOut" }}, 3.7);
      tl.to("#s5-cam", {{ ...at(1.08), duration: 2.1, ease: "power1.inOut" }}, 4.15);
      tl.fromTo("#s5-map", {{ opacity: 0, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.35, ease: "expo.out" }}, 0);
      const step = (id, at) => {{
        tl.fromTo(id, {{ opacity: 0.3 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, at);
      }};
      // Perceive (0 s): lucrările apar din datele celor trei modele.
      step("#s5-st1", 0.0);
      tl.fromTo(".s5-pt", {{ opacity: 0, scale: 0, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "expo.out", stagger: 0.012 }}, 0.1);
      // Estimate (1,25 s): fiecare punct primește mărimea scorului.
      step("#s5-st2", 1.25);
      D.points.forEach((p, i) => {{
        tl.to("#s5-p" + i, {{ scale: 0.55 + p[3] * 1.3, duration: 0.5, ease: "expo.out" }}, 1.3 + i * 0.004);
      }});
      // Decide (2,5 s): ce e sigur primește echipă, ce nu e sigur merge la om, restul se amână.
      step("#s5-st3", 2.5);
      const keep = new Set(D.assigned.concat(D.review));
      D.points.forEach((p, i) => {{
        if (!keep.has(i)) tl.to("#s5-p" + i, {{ opacity: 0.22, duration: 0.4, ease: "power2.out" }}, 2.55);
      }});
      tl.fromTo(".s5-review", {{ opacity: 0, scale: 0.4, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "expo.out", stagger: 0.06 }}, 2.6);
      tl.fromTo(".s5-review-label", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.35, ease: "power2.out", stagger: 0.06 }}, 2.75);
      // Act (3,75 s): traseele echipelor se desenează din bazele operative.
      step("#s5-st4", 3.75);
      tl.fromTo(".s5-depot", {{ opacity: 0, scale: 0.5, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.4, ease: "expo.out" }}, 3.75);
      D.routes.forEach(([ri, n]) => {{
        tl.fromTo("#s5-r" + ri, {{ strokeDasharray: "1 1", strokeDashoffset: 1 }}, {{ strokeDashoffset: 0, duration: 1.5, ease: "power2.inOut" }}, 3.85 + ri * 0.08);
        for (let si = 0; si < n; si++) {{
          tl.fromTo("#s5-s" + ri + "-" + si, {{ opacity: 0, scale: 0.3, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.3, ease: "expo.out" }}, 3.95 + ri * 0.08 + (1.4 * (si + 1)) / n);
        }}
      }});
      tl.fromTo("#s5-head", {{ opacity: 0, filter: "blur(10px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: 0.45, ease: "expo.out" }}, 0.15);
      tl.to("#s5-head", {{ opacity: 0, filter: "blur(8px)", duration: 0.25, ease: "power3.in" }}, 2.45);
      tl.to(["#s5-cam", "#s5-steps", "#s5-note"], {{ opacity: 0, filter: "blur(8px)", duration: 0.22, ease: "power3.in" }}, 6.03);
      window.__timelines["s5"] = tl;
    }})();
  </script>
</template>
"""

if __name__ == "__main__":
    main()
