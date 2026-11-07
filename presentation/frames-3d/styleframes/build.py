"""Style frames v2 for "Planet Daybreak": the target look of the 2D layer and the space
around the planet. Plates: the concept planets (presentation/frames-codex/v7/concepts),
cut out with cutout.py. Type: Archivo (OFL). Palette: PPC navy, orange, cyan, electric blue.

Run:  python3 presentation/frames-3d/styleframes/build.py   ->  frames/*.png + sheet.jpg
"""
from __future__ import annotations

import math
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
A = HERE / "assets"
CONCEPTS = HERE.parents[1] / "frames-codex" / "v7" / "concepts"
FONTS = HERE.parents[1] / "video" / "assets" / "fonts"
OUT = HERE / "frames"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

NAVY = "#00091B"   # matches the plates; PPC navy family (#000F1E)
INK = "#F5F7FA"
ORANGE, CYAN, BLUE = "#FA4616", "#00A3E0", "#163FE8"
MUTED = "rgba(245,247,250,.56)"


def font_css() -> str:
    out = []
    for sub, rng in (("latin", "U+0000-00FF, U+2010-2027, U+20AC, U+2190-2193"),
                     ("latin-ext", "U+0100-024F, U+1E00-1EFF")):
        src = (FONTS / f"Archivo-wdth62_125-wght100_900-{sub}.woff2").as_uri()
        out.append(f"@font-face{{font-family:'Archivo';src:url('{src}') format('woff2');"
                   f"font-weight:100 900;font-stretch:62% 125%;unicode-range:{rng};}}")
    return "\n".join(out)


BASE_CSS = f"""
{font_css()}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:{NAVY}}}
*{{box-sizing:border-box}}
.stage{{position:absolute;inset:0;font-family:'Archivo',sans-serif;color:{INK};
  -webkit-font-smoothing:antialiased;font-kerning:normal}}
.abs{{position:absolute}}
.display{{font-weight:800;font-variation-settings:'wdth' 112;letter-spacing:-0.035em;line-height:.9}}
.head{{font-weight:760;font-variation-settings:'wdth' 108;letter-spacing:-0.03em;line-height:.95}}
.body{{font-weight:520;font-variation-settings:'wdth' 100;letter-spacing:-0.01em}}
.mono{{font-variant-numeric:tabular-nums;font-weight:640;font-variation-settings:'wdth' 100;letter-spacing:.01em}}
"""


def img(name: str, left: float, top: float, width: float, extra: str = "") -> str:
    src = (A / name).as_uri() if (A / name).exists() else (CONCEPTS / name).as_uri()
    return f'<img class="abs" src="{src}" style="left:{left}px;top:{top}px;width:{width}px;{extra}">'


def pt(cx, cy, r, hour):
    th = math.radians((hour % 12) / 12 * 360)
    return cx + r * math.sin(th), cy - r * math.cos(th)


def arc(cx, cy, r, h1, h2):
    x1, y1 = pt(cx, cy, r, h1)
    x2, y2 = pt(cx, cy, r, h2)
    span = ((h2 - h1) % 12) / 12 * 360
    return f"M{x1:.1f},{y1:.1f} A{r},{r} 0 {1 if span > 180 else 0} 1 {x2:.1f},{y2:.1f}"


def bezel(cx, cy, r, now: float, label: str, sun: bool = False) -> str:
    """The night-shift clock as a ring around the planet: 22:00 -> 06:00 on a 12 h dial."""
    s = [f'<svg class="abs" style="left:0;top:0" width="1920" height="1080" viewBox="0 0 1920 1080">',
         f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="rgba(245,247,250,.16)" stroke-width="1.5"/>',
         f'<path d="{arc(cx, cy, r, 22, 6)}" fill="none" stroke="rgba(245,247,250,.10)" stroke-width="8" stroke-linecap="round"/>']
    for i in range(24):
        h = i / 2
        x1, y1 = pt(cx, cy, r + 10, h)
        x2, y2 = pt(cx, cy, r + (34 if i % 2 == 0 else 22), h)
        s.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="rgba(245,247,250,{0.55 if i % 2 == 0 else 0.25})" stroke-width="2"/>')
    for h, txt in ((22, "22"), (0, "00"), (2, "02"), (4, "04"), (6, "06")):
        if min(abs(h - now), 12 - abs(h - now)) < 0.9:
            continue
        x, y = pt(cx, cy, r + 62, h)
        s.append(f'<text x="{x:.1f}" y="{y + 9:.1f}" text-anchor="middle" fill="rgba(245,247,250,.5)" '
                 f'style="font:640 26px Archivo;font-variant-numeric:tabular-nums">{txt}</text>')
    s.append(f'<path d="{arc(cx, cy, r, 22, now)}" fill="none" stroke="{ORANGE if sun else CYAN}" '
             f'stroke-width="8" stroke-linecap="round"/>')
    mx, my = pt(cx, cy, r, now)
    s.append(f'<circle cx="{mx:.1f}" cy="{my:.1f}" r="15" fill="{ORANGE if sun else INK}"/>')
    lx, ly = pt(cx, cy, r + 112, now)
    s.append(f'<text x="{lx:.1f}" y="{ly + 14:.1f}" text-anchor="middle" fill="{INK}" '
             f'style="font:700 42px Archivo;font-variant-numeric:tabular-nums">{label}</text>')
    s.append("</svg>")
    return "".join(s)


def ping(x, y, color, big=True) -> str:
    rings = [(14, 1, 0, color), (34, 0, .8, color), (58, 0, .38, color)] if big else [(12, 1, 0, color), (28, 0, .7, color)]
    out = ['<svg class="abs" style="left:0;top:0" width="1920" height="1080">']
    for r, fill, op, c in rings:
        if fill:
            out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}" stroke="{NAVY}" stroke-width="4"/>')
        else:
            out.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="3"/>')
    out.append("</svg>")
    return "".join(out)


def leader(points, color) -> str:
    d = " ".join(f"{x},{y}" for x, y in points)
    return (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080"><polyline points="{d}" '
            f'fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"/></svg>')


CURSOR = ('<svg class="abs" style="left:{x}px;top:{y}px" width="78" height="98" viewBox="0 0 26 33">'
          '<path d="M2 2 L2 26 L8.2 20.4 L12.6 30.6 L16.9 28.8 L12.6 18.8 L21 18.8 Z" fill="#0B0B0C" '
          'stroke="#FFFFFF" stroke-width="1.6" stroke-linejoin="round"/></svg>')


def click_rings(x, y, color=INK) -> str:
    return (f'<svg class="abs" style="left:0;top:0" width="1920" height="1080">'
            f'<circle cx="{x}" cy="{y}" r="26" fill="none" stroke="{color}" stroke-opacity=".7" stroke-width="3"/>'
            f'<circle cx="{x}" cy="{y}" r="46" fill="none" stroke="{color}" stroke-opacity=".3" stroke-width="2"/></svg>')


# ---- placements (planet_storm plate: planet centre (1050,485), radius ~445 in plate px)
S1 = 1650 / 1672
P1L, P1T = 364, 81                     # planet centre on canvas = (1400, 560)


def a1(x, y):
    return P1L + x * S1, P1T + y * S1


def f1_storm() -> str:
    return (img("planet_storm_cut.png", P1L, P1T, 1650)
            + bezel(1400, 560, 478, 22, "22:00")
            + '<div class="abs display" style="left:120px;top:250px;font-size:232px">Storm<br>hits<br>Banat.</div>'
            + f'<div class="abs body" style="left:126px;top:910px;font-size:30px;color:{MUTED}">8 July 2025 · red-code storm warning</div>')


def f2_problems() -> str:
    pole, meter, roof = a1(1200, 410), a1(1410, 390), a1(780, 570)
    rows = [("Fallen poles.", ORANGE, 250, pole), ("Stolen power.", CYAN, 362, meter), ("Too much sun.", BLUE, 474, roof)]
    html = [img("planet_storm_cut.png", P1L, P1T, 1650), bezel(1400, 560, 478, 22.75, "22:45")]
    for text, color, y, (ax, ay) in rows:
        html.append(f'<div class="abs head" style="left:150px;top:{y}px;font-size:66px">'
                    f'<span style="display:inline-block;width:22px;height:22px;border-radius:6px;background:{color};'
                    f'margin-right:24px;vertical-align:8px"></span>{text}</div>')
        html.append(leader([(640, y + 34), (760, y + 34), (ax, ay)], color))
        html.append(ping(round(ax), round(ay), color))
    html.append('<div class="abs display" style="left:120px;top:700px;font-size:104px">Where do crews<br>go first?</div>')
    return "".join(html)


def ui_map_svg() -> str:
    roads = ["M60,380 C260,370 420,300 560,300 S860,330 900,320",
             "M330,40 C340,200 360,300 380,420 S420,640 430,700",
             "M560,300 C600,420 680,520 820,600",
             "M120,120 C220,160 300,220 350,300",
             "M600,80 C620,160 600,240 560,300"]
    houses = [(110, 250), (170, 450), (240, 560), (450, 140), (520, 200), (700, 200), (760, 420),
              (640, 470), (480, 560), (300, 650), (820, 260), (230, 300), (650, 620), (870, 470), (90, 600)]
    r1 = "M380,330 C470,320 520,305 560,300 S700,280 700,200"
    r2 = "M380,330 C370,420 340,500 300,650"
    r3 = "M380,330 C470,360 560,420 640,470 S760,560 820,600"
    s = ['<svg width="900" height="720" viewBox="0 0 900 720">',
         '<rect width="900" height="720" rx="22" fill="#061426"/>']
    for d in roads:
        s.append(f'<path d="{d}" fill="none" stroke="#17324F" stroke-width="22" stroke-linecap="round"/>')
    for x, y in houses:
        s.append(f'<rect x="{x}" y="{y}" width="46" height="34" rx="8" fill="#1F3D60"/>')
    s.append('<rect x="352" y="306" width="56" height="48" rx="10" fill="#2A4E78" stroke="#F5F7FA" stroke-width="3"/>')
    for d, c, stops in ((r1, ORANGE, [(560, 300), (700, 200), (650, 240)]),
                        (r2, CYAN, [(340, 500), (300, 650)]),
                        (r3, BLUE, [(640, 470), (820, 600), (730, 530)])):
        s.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="12" stroke-linecap="round"/>')
        for x, y in stops:
            s.append(f'<circle cx="{x}" cy="{y}" r="15" fill="{c}" stroke="#F5F7FA" stroke-width="5"/>')
    s.append("</svg>")
    return "".join(s)


def crew_card(name, stops, color, glyph) -> str:
    return (f'<div style="display:flex;align-items:center;gap:22px;background:#10263F;border-radius:18px;'
            f'padding:22px 26px;margin-bottom:18px">'
            f'<svg width="64" height="48" viewBox="0 0 64 48"><path d="{glyph}" fill="none" stroke="{color}" '
            f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
            f'<div><div class="head" style="font-size:38px">{name}</div>'
            f'<div class="body" style="font-size:26px;color:{MUTED};margin-top:6px">{stops}</div></div></div>')


def f3_meet() -> str:
    win = (f'<div class="abs" style="left:250px;top:300px;width:1420px;height:740px;border-radius:30px;'
           f'background:#0B1C31;box-shadow:0 50px 120px rgba(0,0,0,.55);transform:perspective(2600px) rotateX(9deg);'
           f'transform-origin:50% 0;overflow:hidden">'
           f'<div style="height:86px;display:flex;align-items:center;justify-content:space-between;padding:0 34px;'
           f'border-bottom:1px solid rgba(245,247,250,.08)">'
           f'<div class="head" style="font-size:34px">Daybreak<span class="body" style="font-size:24px;color:{MUTED};'
           f'margin-left:26px;letter-spacing:0">Tomorrow’s plan · Banat</span></div>'
           f'<div class="head" style="font-size:28px;background:{ORANGE};color:#fff;border-radius:16px;padding:16px 30px">'
           f'Plan tomorrow</div></div>'
           f'<div style="display:flex;gap:30px;padding:28px 34px">'
           f'<div style="width:900px;height:600px;overflow:hidden;border-radius:22px"><div style="transform:translate(-10px,-70px)">{ui_map_svg()}</div></div>'
           f'<div style="flex:1">'
           f'<div class="body" style="font-size:26px;color:{MUTED};margin:6px 0 20px">3 crews ready</div>'
           + crew_card("Crew 1", "3 stops", ORANGE, "M4,40 C20,36 30,20 60,8")
           + crew_card("Crew 2", "2 stops", CYAN, "M8,6 C10,20 14,32 20,44")
           + crew_card("Crew 3", "3 stops", BLUE, "M4,8 C24,16 40,28 60,42")
           + '</div></div></div>')
    return (f'<div class="abs display" style="left:250px;top:70px;font-size:190px">Daybreak</div>'
            f'<div class="abs body" style="left:1250px;top:112px;font-size:44px;line-height:1.15;color:{INK}">'
            f'Tomorrow’s crews,<br>planned in one click.</div>'
            + win + click_rings(1572, 352) + CURSOR.format(x=1560, y=344))


# ---- planet_routes plate: lower half off-canvas, so the cut edge never shows
S4 = 1650 / 1672
P4L, P4T = 528, 183


def a4(x, y):
    return P4L + x * S4, P4T + y * S4


def chip(x, y, text, color, dx=40, dy=-90) -> str:
    bx, by = x + dx, y + dy
    return (leader([(x, y), (bx, by + 30)], color) + ping(round(x), round(y), color, big=False)
            + f'<div class="abs head" style="left:{bx}px;top:{by}px;font-size:30px;background:{color};color:#fff;'
              f'border-radius:999px;padding:12px 24px;white-space:nowrap">{text}</div>')


def f4_routes() -> str:
    t1, t2, t3 = a4(788, 750), a4(648, 460), a4(1018, 510)
    return (img("planet_routes_cut.png", P4L, P4T, 1650)
            + bezel(1360, 775, 486, 1.0, "01:00")
            + '<div class="abs display" style="left:120px;top:110px;font-size:150px">Every crew<br>knows where<br>to go.</div>'
            + chip(*t1, "Crew 1 · 3 stops", ORANGE, 60, -40)
            + chip(*t2, "Crew 2 · 2 stops", CYAN, -330, -120)
            + chip(*t3, "Crew 3 · 3 stops", BLUE, 70, -130))


def f5_ask() -> str:
    # closer on the planet: the routes plate scaled up around the right-hand houses
    W = 2700
    s = W / 1672
    hx, hy = 1290, 760                       # where the "unsure" house lands on canvas
    L, T = hx - 1188 * s, hy - 500 * s
    cx, cy = 1240, hy - 560                  # card top-left, above the house
    card = (f'<div class="abs" style="left:{cx}px;top:{cy}px;width:600px;border-radius:30px;background:#0E2238;'
            f'box-shadow:0 40px 100px rgba(0,0,0,.55);padding:38px 42px">'
            f'<div class="body" style="font-size:28px;color:{CYAN};display:flex;align-items:center;gap:14px">'
            f'<span style="width:16px;height:16px;border-radius:50%;background:{CYAN};display:inline-block"></span>Not sure</div>'
            f'<div class="head" style="font-size:50px;margin:16px 0 30px">Send a crew to<br>check this meter?</div>'
            f'<div style="display:flex;gap:18px">'
            f'<div class="head" style="font-size:32px;background:{CYAN};color:#001B2E;border-radius:18px;padding:20px 40px">Approve</div>'
            f'<div class="head" style="font-size:32px;border:2px solid rgba(245,247,250,.3);border-radius:18px;padding:18px 40px">Skip</div>'
            f'</div></div>')
    bx, by = cx + 42 + 95, cy + 38 + 28 + 16 + 120 + 30 + 36     # centre of the Approve button
    return (img("planet_routes_cut.png", L, T, W)
            + f'<div class="abs" style="inset:0;background:linear-gradient(90deg,{NAVY} 0%,{NAVY} 36%,{NAVY}00 56%)"></div>'
            + '<div class="abs display" style="left:120px;top:300px;font-size:170px">Not sure?<br>It asks<br>you.</div>'
            + leader([(hx, hy), (hx, cy + 318)], CYAN) + ping(hx, hy, CYAN)
            + card + click_rings(bx, by, INK) + CURSOR.format(x=bx - 12, y=by - 8))


def f6_dawn() -> str:
    W = 2000
    s = W / 1672
    L, T = -40, 1080 - 941 * s + 60
    return (f'<div class="abs" style="left:1060px;top:{T + 470 * s - 420}px;width:840px;height:840px;border-radius:50%;'
            f'background:{ORANGE}"></div>'
            + img("planet_dawn_cut.png", L, T, W)
            + '<div class="abs display" style="left:120px;top:90px;font-size:330px;letter-spacing:-0.05em">+49%</div>'
            + '<div class="abs head" style="left:132px;top:400px;font-size:76px">Same crews.<br>More value.</div>'
            + f'<div class="abs body" style="left:134px;top:590px;font-size:28px;color:{MUTED}">30-day simulation</div>'
            + f'<div class="abs mono" style="right:120px;top:96px;font-size:44px;display:flex;align-items:center;gap:16px">'
              f'<span style="width:22px;height:22px;border-radius:50%;background:{ORANGE};display:inline-block"></span>06:00</div>')


def f7_end() -> str:
    return (f'<div class="abs" style="left:938px;top:380px;width:44px;height:44px;border-radius:50%;background:{ORANGE}"></div>'
            + '<div class="abs display" style="left:0;right:0;top:450px;text-align:center;font-size:250px">Daybreak</div>'
            + '<div class="abs head" style="left:0;right:0;top:720px;text-align:center;font-size:56px">For Rețele Electrice dispatchers</div>'
            + f'<div class="abs body" style="left:0;right:0;top:980px;text-align:center;font-size:26px;color:{MUTED};'
              f'letter-spacing:.12em">CYBERPUNKS · SMARTHACK 2026</div>')


FRAMES = {"01_storm": f1_storm, "02_problems": f2_problems, "03_meet": f3_meet, "04_routes": f4_routes,
          "05_ask": f5_ask, "06_dawn": f6_dawn, "07_end": f7_end}


def render(name: str, body: str) -> Path:
    from PIL import Image
    OUT.mkdir(exist_ok=True)
    html = f'<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}</style></head><body><div class="stage">{body}</div></body></html>'
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp:
        tmp.write(html)
    dst = OUT / f"{name}.png"
    for _ in range(5):
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                        "--virtual-time-budget=8000", "--run-all-compositor-stages-before-draw",
                        "--window-size=1920,1080", f"--screenshot={dst}", Path(tmp.name).as_uri()],
                       check=True, capture_output=True)
        im = Image.open(dst).convert("RGB")
        if im.getpixel((960, 1077)) != (0, 0, 0) or im.getpixel((10, 1077)) != (0, 0, 0):
            break
    print("ok", dst.name)
    return dst


def sheet(paths):
    from PIL import Image
    w, h, pad = 900, 506, 14
    cols, rows = 2, (len(paths) + 1) // 2
    img_ = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * (h + pad) + pad), (10, 10, 12))
    for i, p in enumerate(paths):
        img_.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS), (pad + (i % cols) * (w + pad), pad + (i // cols) * (h + pad)))
    img_.save(HERE / "sheet.jpg", quality=88)
    print("ok sheet.jpg")


if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FRAMES)
    for n in names:
        render(n, FRAMES[n]())
    sheet(sorted(OUT.glob("*.png")))
