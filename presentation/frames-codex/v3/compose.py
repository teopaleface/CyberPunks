"""Hi-vis colour variants: set the headlines over the v3 plates and build a comparison sheet.

Reuses the typesetting of ../v2/compose.py (Archivo, headless Chrome, 1920x1080).
Rows of the sheet: v2 "Hi-vis" (reference), h1 one colour, h2 dark to light, h3 two colours.

Run:  python3 presentation/frames-codex/v3/compose.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("v2compose", HERE.parent / "v2" / "compose.py")
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

v2.PLATES = HERE / "plates"
v2.OUT = HERE / "frames"

BLACK, WHITE = "#0D0D0C", "#F6F4EF"
BEATS = ["storm", "where", "problems", "dawn"]
INKS = {  # storm, where, problems labels (3), dawn
    "h1": (BLACK, BLACK, (BLACK, BLACK, BLACK), BLACK),
    "h2": (WHITE, WHITE, (WHITE, WHITE, WHITE), BLACK),
    "h3": (WHITE, BLACK, (BLACK, WHITE, BLACK), WHITE),
}
ROWS = [
    ("v2  Hi-vis (as approved)", None),
    ("h1  One colour (orange only)", "h1"),
    ("h2  Dark to light", "h2"),
    ("h3  Two colours (orange + cobalt)", "h3"),
]


def frames_for(v: str) -> dict[str, dict]:
    storm, where, labels, dawn = INKS[v]
    D2 = v2.D2
    return {
        f"{v}_storm": {**D2, "plate": f"{v}_storm.jpg", "ink": storm, "blocks": [
            {"text": "Storm hits Banat.", "size": 150, "top": 120, "left": 130}]},
        f"{v}_where": {**D2, "plate": f"{v}_where.jpg", "ink": where, "blocks": [
            {"text": "Where do crews go first?", "size": 130, "top": 120, "left": 130}]},
        f"{v}_problems": {**D2, "plate": f"{v}_problems.jpg", "ink": labels[0],
                          "triptych": ["Fallen poles.", "Stolen power.", "Too much sun."],
                          "label_size": 54, "label_bottom": 80, "label_inks": list(labels),
                          "blocks": []},
        f"{v}_dawn": {**D2, "plate": f"{v}_dawn.jpg", "ink": dawn, "blocks": [
            {"text": "Daybreak", "size": 250, "top": 150, "left": 120, "track": "-0.045em"},
            {"text": "Tomorrow’s crews, planned tonight.", "size": 56, "top": 440,
             "left": 132, "wght": 520, "track": "-0.012em"}]},
    }


def sheet() -> None:
    from PIL import Image, ImageDraw, ImageFont
    w, h, pad, head = 640, 360, 14, 46
    img = Image.new("RGB", (4 * w + 5 * pad, len(ROWS) * (h + head) + pad), (20, 20, 20))
    dr = ImageDraw.Draw(img)
    try:
        ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 26)
    except OSError:
        ft = None
    for r, (label, v) in enumerate(ROWS):
        y = r * (h + head) + pad
        dr.text((pad, y + 6), label, fill=(235, 235, 235), font=ft)
        for c, beat in enumerate(BEATS):
            p = (HERE.parent / "v2" / "frames" / f"d2_{beat}.png") if v is None \
                else (v2.OUT / f"{v}_{beat}.png")
            if p.exists():
                im = Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS)
                img.paste(im, (pad + c * (w + pad), y + head))
    img.save(HERE / "contact_sheet.jpg", quality=88)
    print("ok contact_sheet.jpg")


if __name__ == "__main__":
    for v in INKS:
        v2.FRAMES = frames_for(v)
        for fid in v2.FRAMES:
            v2.render(fid)
    sheet()
