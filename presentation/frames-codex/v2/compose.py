"""Set the headlines over the Codex plates, in code, with a real typeface.

Why: text baked into AI images carries the AI-font look and can't be checked letter
by letter. Here the plates stay text-free and the type is set with Archivo (the
product's own face, OFL), then each frame is screenshotted at 1920x1080 with headless
Chrome.

Run:  python3 presentation/frames-codex/v2/compose.py [frame_id ...]
Out:  presentation/frames-codex/v2/frames/<frame_id>.png and contact_sheet.jpg
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATES = HERE / "plates"
OUT = HERE / "frames"
FONTS = HERE.parents[1] / "video" / "assets" / "fonts"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Direction 1 "First light": documentary photos, warm white type, Apple billboard grammar.
D1 = dict(wdth=100, wght=620, track="-0.03em", ink="#FBF8F2", align="center")
# Direction 2 "Hi-vis": drenched safety colours, wider signage-like cut, left aligned.
D2 = dict(wdth=116, wght=740, track="-0.032em", ink="#0D0D0C", align="left")

FRAMES: dict[str, dict] = {
    "d1_storm": {**D1, "plate": "d1_storm.jpg", "blocks": [
        {"text": "Storm hits Banat.", "size": 136, "top": 150}]},
    "d1_where": {**D1, "plate": "d1_where.jpg", "ink": "#14181E", "blocks": [
        {"text": "Where do crews go first?", "size": 120, "top": 130}]},
    "d1_problems": {**D1, "plate": "d1_problems.jpg", "triptych": [
        "Fallen poles.", "Stolen power.", "Too much sun."], "label_size": 50,
        "label_bottom": 70, "label_inks": ["#FBF8F2", "#14181E", "#FBF8F2"], "blocks": []},
    "d1_dawn": {**D1, "plate": "d1_dawn.jpg", "ink": "#14181E", "blocks": [
        {"text": "Daybreak", "size": 220, "top": 250, "wght": 660, "track": "-0.04em"},
        {"text": "Tomorrow’s crews, planned tonight.", "size": 50, "top": 500,
         "wght": 470, "track": "-0.01em", "opacity": 0.82}]},
    "d2_storm": {**D2, "plate": "d2_storm.jpg", "blocks": [
        {"text": "Storm hits Banat.", "size": 150, "top": 120, "left": 130}]},
    "d2_where": {**D2, "plate": "d2_where.jpg", "ink": "#FFFFFF", "blocks": [
        {"text": "Where do crews go first?", "size": 130, "top": 120, "left": 130}]},
    "d2_problems": {**D2, "plate": "d2_problems.jpg", "triptych": [
        "Fallen poles.", "Stolen power.", "Too much sun."], "label_size": 54,
        "label_bottom": 80, "label_inks": ["#0D0D0C", "#FFFFFF", "#0D0D0C"],
        "blocks": []},
    "d2_dawn": {**D2, "plate": "d2_dawn.jpg", "blocks": [
        {"text": "Daybreak", "size": 250, "top": 150, "left": 120, "track": "-0.045em"},
        {"text": "Tomorrow’s crews, planned tonight.", "size": 56, "top": 440,
         "left": 132, "wght": 520, "track": "-0.012em"}]},
}


def font_face() -> str:
    faces = []
    for sub, rng in (("latin", "U+0000-00FF, U+2010-2027, U+20AC"),
                     ("latin-ext", "U+0100-024F, U+0259, U+1E00-1EFF")):
        src = FONTS / f"Archivo-wdth62_125-wght100_900-{sub}.woff2"
        faces.append(
            "@font-face{font-family:'Archivo';src:url('%s') format('woff2');"
            "font-weight:100 900;font-stretch:62%% 125%%;unicode-range:%s;}"
            % (src.as_uri(), rng))
    return "\n".join(faces)


def block_html(b: dict, f: dict) -> str:
    align = b.get("align", f["align"])
    left = b.get("left")
    pos = (f"left:{left}px;right:120px;text-align:left;" if left is not None and align == "left"
           else "left:0;right:0;text-align:center;")
    style = (
        f"position:absolute;top:{b['top']}px;{pos}"
        f"font-size:{b['size']}px;line-height:1.02;"
        f"font-weight:{b.get('wght', f['wght'])};"
        f"font-variation-settings:'wdth' {b.get('wdth', f['wdth'])};"
        f"letter-spacing:{b.get('track', f['track'])};"
        f"color:{b.get('ink', f['ink'])};opacity:{b.get('opacity', 1)};"
        "text-wrap:balance;"
    )
    return f'<div style="{style}">{b["text"]}</div>'


def triptych_html(f: dict) -> str:
    labels = f.get("triptych") or []
    inks = f.get("label_inks") or [f["ink"]] * len(labels)
    out = []
    for i, (text, ink) in enumerate(zip(labels, inks)):
        style = (
            f"position:absolute;bottom:{f['label_bottom']}px;left:{i * 640}px;width:640px;"
            f"text-align:center;font-size:{f['label_size']}px;line-height:1.05;"
            f"font-weight:{f['wght']};font-variation-settings:'wdth' {f['wdth']};"
            f"letter-spacing:-0.02em;color:{ink};"
        )
        out.append(f'<div style="{style}">{text}</div>')
    return "".join(out)


def page(fid: str, f: dict) -> str:
    plate = (PLATES / f["plate"]).as_uri()
    body = "".join(block_html(b, f) for b in f["blocks"]) + triptych_html(f)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
{font_face()}
html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;background:#000}}
.plate{{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover}}
.stage{{position:absolute;inset:0;font-family:'Archivo',sans-serif;
  font-kerning:normal;-webkit-font-smoothing:antialiased}}
</style></head><body><img class="plate" src="{plate}"><div class="stage">{body}</div>
</body></html>"""


def render(fid: str) -> Path | None:
    f = FRAMES[fid]
    if not (PLATES / f["plate"]).exists():
        print(f"skip {fid}: plate missing")
        return None
    OUT.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as tmp:
        tmp.write(page(fid, f))
    dst = OUT / f"{fid}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--virtual-time-budget=4000",
                    "--window-size=1920,1080", f"--screenshot={dst}", Path(tmp.name).as_uri()],
                   check=True, capture_output=True)
    print(f"ok {dst.name}")
    return dst


def sheet(paths: list[Path]) -> None:
    from PIL import Image, ImageDraw
    w, h, pad = 900, 506, 18
    order = ["storm", "where", "problems", "dawn"]
    key = lambda p: order.index(p.stem.split("_", 1)[1])
    d1 = sorted((p for p in paths if p.name.startswith("d1")), key=key)
    d2 = sorted((p for p in paths if p.name.startswith("d2")), key=key)
    rows = max(len(d1), len(d2))
    img = Image.new("RGB", (2 * w + 3 * pad, rows * (h + pad) + pad + 50), (20, 20, 20))
    dr = ImageDraw.Draw(img)
    from PIL import ImageFont
    try:
        ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
    except OSError:
        ft = None
    dr.text((pad, 14), "1  First light (documentary photography)", fill=(235, 235, 235), font=ft)
    dr.text((2 * pad + w, 14), "2  Hi-vis (safety colours, studio photography)", fill=(235, 235, 235), font=ft)
    for col, group in enumerate((d1, d2)):
        for row, p in enumerate(group):
            im = Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS)
            img.paste(im, (pad + col * (w + pad), 50 + pad + row * (h + pad)))
    img.save(HERE / "contact_sheet.jpg", quality=88)
    print("ok contact_sheet.jpg")


if __name__ == "__main__":
    ids = sys.argv[1:] or list(FRAMES)
    done = [p for p in (render(i) for i in ids) if p]
    allframes = sorted(OUT.glob("d*.png")) if OUT.exists() else []
    if allframes:
        sheet(allframes)
