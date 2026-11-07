"""Cadrele statice ale variantei 4 (Daybreak, în engleză, stil Apple), pentru aprobarea lui Teo.

Fără animație și fără film: fiecare cadru e o compoziție HyperFrames de 1 s, ca să le randăm cu
`hyperframes snapshot` (fonturile locale se încarcă doar așa). După aprobare, aceleași compoziții devin scenele filmului.

Reguli (Teo, 7 nov.): un singur lucru pe ecran, mult spațiu gol, totul centrat, text mare, cel mult 5 cuvinte;
produsul decupat pe un singur element, într-o fereastră cu colțuri rotunjite și umbră moale; harta desenată din nou
(contur simplu și luminos, 3 trasee în 3 culori, 3-4 opriri și o bulină de pornire, fără etichete mici);
o singură culoare de accent pe cadru, în rest alb, negru și gri.

Rulare (din rădăcina repo-ului):
    python3 presentation/scripts/build_boards_v4.py
    npx -y hyperframes@0.9.19 snapshot presentation/video/boards/v4 --at 0.5,1.5,2.5 --no-end -o /tmp/cp-prez/v4
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
VID = ROOT / "presentation" / "video"
OUT = VID / "boards" / "v4"
COMP = OUT / "compositions"

# Activele de care au nevoie cadrele, copiate din proiectul filmului (copia nu intră în git).
ASSETS = [
    "fonts/Archivo-wdth62_125-wght100_900-latin.woff2",
    "fonts/Archivo-wdth62_125-wght100_900-latin-ext.woff2",
    "fonts/OFL-Archivo.txt",
    "vendor/gsap-3.15.0.min.js",
    "3d/astra/storm_hero.webp",
    "ui/cursor.svg",
]

# ------------------------------------------------------------------ paleta (o singură culoare de accent pe cadru)
INK = "#0B1622"      # cerneala produsului (titluri, butonul principal)
GRAY_TXT = "#7A828C"  # text secundar
GRAY_LINE = "#DCDFE3"  # contururi, margini
GRAY_FILL = "#F3F4F6"  # suprafețe, harta
SUN = "#F2A20C"       # soarele din logo
ROUTES = ["#2364D2", "#A23C9E", "#D99100"]  # cele trei trasee: culorile surselor din consolă

BASE_CSS = """
    #root { position: absolute; inset: 0; overflow: hidden; background: #ffffff; }
    .frame { position: absolute; inset: 0; }
    .h { position: absolute; left: 0; right: 0; text-align: center; white-space: nowrap;
         font-weight: 600; letter-spacing: -0.035em; line-height: 1.04; color: var(--ink); }
"""


def scene(cid: str, css: str, body: str, comment: str) -> str:
    return f"""<template>
  <!-- {comment} -->
  <style>{BASE_CSS}{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="1920" data-height="1080">
    <div id="{cid}-f" class="clip frame" data-start="0" data-duration="1">
{body}
    </div>
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    window.__timelines["{cid}"] = gsap.timeline({{ paused: true }});
  </script>
</template>
"""


# ------------------------------------------------------------------ cadrul 1: hook
kf1 = scene("kf1", """
    #kf1-cloud { position: absolute; left: 740px; top: 150px; width: 440px; height: 440px;
                 background: url(assets/3d/astra/storm_hero.webp) center / contain no-repeat; }
    #kf1-h { top: 640px; font-size: 136px; }
    #kf1-date { position: absolute; left: 0; right: 0; top: 812px; text-align: center;
                font-size: 44px; font-weight: 500; letter-spacing: -0.01em; color: var(--gray-txt); }
    #kf1-ai { position: absolute; left: 0; right: 0; top: 990px; text-align: center; font-size: 28px; font-weight: 500; color: #A3A9B0; }
""", """      <div id="kf1-cloud"></div>
      <h1 id="kf1-h" class="h">A storm hits Banat.</h1>
      <p id="kf1-date">July 8, 2025</p>
      <p id="kf1-ai">3D object modelled with AI</p>""",
    "Hook: ziua reală (8 iulie 2025, cod roșu de vijelii în Banat; sursa în docs/research/B.md). Accentul cadrului: norul 3D.")

# ------------------------------------------------------------------ cadrul 2: produsul (un singur card, mărit)
# Cardul "Nu sunt sigur" din consolă, desenat din nou în engleză, cu aceeași structură: titlul, încrederea, cele trei butoane.
kf2 = scene("kf2", f"""
    #kf2-h {{ top: 150px; font-size: 112px; }}
    #kf2-win {{ position: absolute; left: 470px; top: 360px; width: 980px; height: 540px; border-radius: 38px; background: #ffffff;
               border: 1px solid #E7E9EC; box-shadow: 0 44px 110px rgba(11,22,34,.13), 0 12px 34px rgba(11,22,34,.07); overflow: hidden; }}
    #kf2-bar {{ position: absolute; left: 34px; top: 30px; display: flex; gap: 12px; }}
    #kf2-bar i {{ width: 16px; height: 16px; border-radius: 50%; background: {GRAY_LINE}; }}
    #kf2-lab {{ position: absolute; left: 72px; top: 104px; font-size: 32px; font-weight: 600; letter-spacing: -0.01em; color: var(--gray-txt); }}
    #kf2-t {{ position: absolute; left: 72px; top: 150px; font-size: 76px; font-weight: 640; letter-spacing: -0.035em; line-height: 1.05; color: var(--ink); white-space: nowrap; }}
    #kf2-conf {{ position: absolute; left: 72px; top: 272px; display: flex; align-items: center; gap: 26px; font-size: 32px; font-weight: 500; color: var(--gray-txt); }}
    #kf2-track {{ width: 400px; height: 14px; border-radius: 7px; background: #ECEEF1; overflow: hidden; }}
    #kf2-fill {{ width: 62%; height: 100%; border-radius: 7px; background: var(--sun); }}
    #kf2-pct {{ color: var(--ink); font-weight: 600; font-variant-numeric: tabular-nums; }}
    #kf2-btns {{ position: absolute; left: 72px; top: 382px; display: flex; gap: 20px; }}
    .kf2-b {{ height: 92px; padding: 0 46px; border-radius: 22px; display: flex; align-items: center; font-size: 38px; font-weight: 600; letter-spacing: -0.015em; }}
    #kf2-ok {{ background: var(--ink); color: #ffffff; }}
    .kf2-sec {{ border: 2px solid {GRAY_LINE}; color: var(--ink); background: #ffffff; }}
    #kf2-cur {{ position: absolute; left: 684px; top: 791px; width: 134px; height: 134px; filter: drop-shadow(0 4px 6px rgba(0,0,0,.3)); }}
""", """      <h1 id="kf2-h" class="h">Not sure? It asks.</h1>
      <div id="kf2-win">
        <div id="kf2-bar"><i></i><i></i><i></i></div>
        <p id="kf2-lab">Not sure</p>
        <p id="kf2-t">Storm damage near Deva</p>
        <div id="kf2-conf"><span>Confidence</span><span id="kf2-track"><span id="kf2-fill" style="display:block"></span></span><span id="kf2-pct">62%</span></div>
        <div id="kf2-btns"><span id="kf2-ok" class="kf2-b">Approve</span><span class="kf2-b kf2-sec">Reject</span><span class="kf2-b kf2-sec">Later</span></div>
      </div>
      <img id="kf2-cur" src="assets/ui/cursor.svg" alt="" />""",
    "Produsul: cardul Nu sunt sigur din consolă (http://localhost:3710/, 8 iulie 2025), desenat din nou în engleză. Accentul: încrederea (soarele).")


# ------------------------------------------------------------------ cadrul 3: harta (ilustrație, nu captură)
def banat_map(box_w: float, box_h: float, cx: float, cy: float):
    """Conturul regiunii Banat (geoBoundaries ROU ADM1, CC BY 4.0) și o funcție lon/lat -> pixeli în cadru."""
    reg = json.loads((VID / "assets/geo/regions.json").read_text())
    meta = json.loads((VID / "assets/img/romania_night_z8.json").read_text())
    z, x0, y0 = meta["z"], meta["x_tiles"][0], meta["y_tiles"][0]

    def to_src(lon: float, lat: float) -> tuple[float, float]:
        n = 2 ** z
        lr = math.radians(lat)
        return ((lon + 180.0) / 360.0 * n - x0) * 256.0, \
               ((1.0 - math.log(math.tan(lr) + 1.0 / math.cos(lr)) / math.pi) / 2.0 * n - y0) * 256.0

    pts = [(float(a), float(b)) for a, b in re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", reg["regions"]["banat"]["path"])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    s = min(box_w / (bx1 - bx0), box_h / (by1 - by0))
    ox, oy = cx - s * (bx0 + bx1) / 2, cy - s * (by0 + by1) / 2

    def tf(x: float, y: float) -> tuple[float, float]:
        return ox + s * x, oy + s * y

    ring = smooth(rdp([tf(x, y) for x, y in pts], 2.2), 2)
    d = "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in ring) + "Z"
    return d, (lambda lon, lat: tf(*to_src(lon, lat)))


def rdp(pts: list, eps: float) -> list:
    """Ramer-Douglas-Peucker: scoate zimții mai mici de eps pixeli."""
    if len(pts) < 3:
        return pts
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy)
    if norm < 1e-6:  # contur închis: primul punct = ultimul, deci măsurăm distanța față de el
        dists = [math.hypot(x - x0, y - y0) for x, y in pts[1:-1]]
    else:
        dists = [abs(dy * (x - x0) - dx * (y - y0)) / norm for x, y in pts[1:-1]]
    i = max(range(len(dists)), key=dists.__getitem__) + 1
    if dists[i - 1] <= eps:
        return [pts[0], pts[-1]]
    return rdp(pts[: i + 1], eps)[:-1] + rdp(pts[i:], eps)


def smooth(ring: list, it: int) -> list:
    """Chaikin pe un contur închis: colțurile devin curbe moi."""
    for _ in range(it):
        out = []
        for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
            out += [(0.75 * ax + 0.25 * bx, 0.75 * ay + 0.25 * by), (0.25 * ax + 0.75 * bx, 0.25 * ay + 0.75 * by)]
        ring = out
    return ring


# Trei echipe, trei trasee, fiecare cu baza (bulina de pornire) și 3-4 opriri. Orașe reale din Banat, fără etichete.
CREWS = [
    [(21.3123, 46.1866), (21.6900, 46.3300), (22.1167, 46.3667), (22.3400, 46.2700)],                      # Arad: Pâncota, Sebiș, Gurahonț
    [(21.2087, 45.7489), (21.6036, 45.6497), (21.9031, 45.6886), (22.2219, 45.4214), (21.8892, 45.3008)],  # Timișoara
    [(22.9000, 45.8667), (23.0100, 45.7300), (23.1000, 45.5100), (23.3733, 45.4125)],                      # Deva: Călan, Pui, Petroșani
]
MAP_D, PROJ = banat_map(1000, 640, 960, 655)


def route_svg() -> str:
    parts = []
    for color, crew in zip(ROUTES, CREWS):
        xy = [PROJ(lon, lat) for lon, lat in crew]
        pl = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
        parts.append(f'<polyline points="{pl}" fill="none" stroke="#ffffff" stroke-width="26" stroke-linecap="round" stroke-linejoin="round" />')
        parts.append(f'<polyline points="{pl}" fill="none" stroke="{color}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round" />')
        for x, y in xy[1:]:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="#ffffff" stroke="{color}" stroke-width="8" />')
        x, y = xy[0]
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="27" fill="#ffffff" filter="url(#kf3-sh)" />')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="19" fill="{color}" />')
    return "\n          ".join(parts)


kf3 = scene("kf3", f"""
    #kf3-h {{ top: 96px; font-size: 120px; }}
    #kf3-map {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; }}
""", f"""      <h1 id="kf3-h" class="h">Planned.</h1>
      <svg id="kf3-map" viewBox="0 0 1920 1080" aria-hidden="true">
        <defs>
          <filter id="kf3-sh" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#0B1622" flood-opacity="0.18" /></filter>
          <filter id="kf3-land" x="-10%" y="-10%" width="120%" height="130%"><feDropShadow dx="0" dy="26" stdDeviation="30" flood-color="#0B1622" flood-opacity="0.08" /></filter>
        </defs>
        <path d="{MAP_D}" fill="{GRAY_FILL}" stroke="{GRAY_LINE}" stroke-width="3" stroke-linejoin="round" filter="url(#kf3-land)" />
          {route_svg()}
      </svg>""",
    "Harta, desenată din nou: conturul regiunii Banat (geoBoundaries, CC BY 4.0), trei echipe, trei trasee. Ilustrativ.")


SCENES = [("kf1", "kf1-hook.html", kf1), ("kf2", "kf2-produs.html", kf2), ("kf3", "kf3-harta.html", kf3)]

FONT_FACE = """
      @font-face { font-family: "Archivo"; font-style: normal; font-weight: 100 900; font-stretch: 62% 125%; font-display: block;
        src: url("assets/fonts/Archivo-wdth62_125-wght100_900-latin-ext.woff2") format("woff2");
        unicode-range: U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C4, U+2113, U+2C60-2C7F, U+A720-A7FF; }
      @font-face { font-family: "Archivo"; font-style: normal; font-weight: 100 900; font-stretch: 62% 125%; font-display: block;
        src: url("assets/fonts/Archivo-wdth62_125-wght100_900-latin.woff2") format("woff2");
        unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD; }"""


def main() -> None:
    COMP.mkdir(parents=True, exist_ok=True)
    for rel in ASSETS:
        dst = OUT / "assets" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(VID / "assets" / rel, dst)
    (OUT / ".gitignore").write_text("# Copii ale activelor din presentation/video/assets (le pune build_boards_v4.py) și fișierele CLI-ului.\nassets/\n.hyperframes/\n")
    (OUT / "meta.json").write_text(json.dumps({"id": "boards-v4", "name": "boards-v4"}, indent=2) + "\n")
    for _, name, html in SCENES:
        (COMP / name).write_text(html)
    hosts = "\n".join(
        f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{name}" data-start="{i}" '
        f'data-duration="1" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>'
        for i, (cid, name, _) in enumerate(SCENES))
    (OUT / "index.html").write_text(f"""<!doctype html>
<html lang="en" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <!-- Varianta 4 (Daybreak): cadre statice pentru aprobare, câte 1 s fiecare. Scrise de presentation/scripts/build_boards_v4.py. -->
    <script src="assets/vendor/gsap-3.15.0.min.js"></script>
    <style>{FONT_FACE}
      :root {{ --ink: {INK}; --gray-txt: {GRAY_TXT}; --sun: {SUN}; --font-display: "Archivo", sans-serif; }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ margin: 0; width: 1920px; height: 1080px; overflow: hidden; background: #ffffff; }}
      #root {{ width: 100%; height: 100%; font-family: var(--font-display); color: var(--ink); -webkit-font-smoothing: antialiased; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="boards" data-start="0" data-duration="{len(SCENES)}" data-width="1920" data-height="1080">
{hosts}
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["boards"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
""")
    print("scrise:", ", ".join(n for _, n, _ in SCENES), "în", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
