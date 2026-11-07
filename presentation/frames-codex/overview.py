"""One sheet with every style side by side (4 beats per row). Run after the v2/v4/v5 compose scripts.

Run:  python3 presentation/frames-codex/overview.py   ->  presentation/frames-codex/styles_overview.jpg
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

R = Path(__file__).resolve().parent
ROWS = [
    ("Hi-vis (Codex, v2, reference)", R / "v2/frames", "d2"),
    ("s1 Miniature world (Codex)", R / "v4/frames", "s1"),
    ("s2 Pictogram poster (Codex)", R / "v4/frames", "s2"),
    ("s3 Cut paper (Codex)", R / "v4/frames", "s3"),
    ("g1 Risograph print (Gemini)", R / "v5/frames", "g1"),
    ("g2 White architectural model (Gemini)", R / "v5/frames", "g2"),
]
BEATS = ["storm", "where", "problems", "dawn"]
w, h, pad, head = 560, 315, 12, 42
img = Image.new("RGB", (4 * w + 5 * pad, len(ROWS) * (h + head) + pad), (20, 20, 20))
d = ImageDraw.Draw(img)
ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
for r, (label, folder, v) in enumerate(ROWS):
    y = r * (h + head) + pad
    d.text((pad, y + 6), label, fill=(235, 235, 235), font=ft)
    for c, beat in enumerate(BEATS):
        p = folder / f"{v}_{beat}.png"
        if p.exists():
            img.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS),
                      (pad + c * (w + pad), y + head))
img.save(R / "styles_overview.jpg", quality=86)
print("ok styles_overview.jpg", img.size)
