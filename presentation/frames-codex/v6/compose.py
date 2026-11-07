"""v6: s1 "Miniature world" and g2 "White model" pushed for wow, each made by two models.

Plates: plates/<style>_<beat>_<model>.jpg, style in {s1, g2}, model in {codex, gemini}.
Type is set with ../v2/compose.py (Archivo, headless Chrome, 1920x1080).
Sheet rows: s1 codex, s1 gemini, g2 codex, g2 gemini; columns: the five beats.

Run:  python3 presentation/frames-codex/v6/compose.py
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

INK = "#141414"
BEATS = ["storm", "where", "problems", "map", "dawn"]
# s1 is playful (wider cut); g2 is calm and Apple-like (normal width, lighter weight).
TYPE = {
    "s1": dict(wdth=116, wght=740, track="-0.032em", ink=INK, align="left"),
    "g2": dict(wdth=100, wght=640, track="-0.03em", ink=INK, align="left"),
}
ROWS = [("s1", "codex"), ("s1", "gemini"), ("g2", "codex"), ("g2", "gemini")]
NAMES = {"s1": "Miniature world", "g2": "White model", "codex": "Codex", "gemini": "Gemini"}


def frames_for(style: str, model: str) -> dict[str, dict]:
    t = TYPE[style]
    k = lambda beat: f"{style}_{beat}_{model}"
    return {
        k("storm"): {**t, "plate": f"{k('storm')}.jpg", "blocks": [
            {"text": "Storm hits<br>Banat.", "size": 150, "top": 110, "left": 130}]},
        k("where"): {**t, "plate": f"{k('where')}.jpg", "blocks": [
            {"text": "Where do crews go first?", "size": 120, "top": 110, "left": 130}]},
        k("problems"): {**t, "plate": f"{k('problems')}.jpg",
                        "triptych": ["Fallen poles.", "Stolen power.", "Too much sun."],
                        "label_size": 54, "label_bottom": 70, "blocks": []},
        k("map"): {**t, "plate": f"{k('map')}.jpg", "blocks": [
            {"text": "Every crew knows where to go.", "size": 112, "top": 90, "left": 130}]},
        k("dawn"): {**t, "plate": f"{k('dawn')}.jpg", "blocks": [
            {"text": "Daybreak", "size": 250, "top": 110, "left": 120, "track": "-0.045em"},
            {"text": "Tomorrow’s crews, planned tonight.", "size": 56, "top": 395,
             "left": 132, "wght": 500, "track": "-0.012em"}]},
    }


# Per-plate fixes where the art reaches into the space meant for the headline.
OVERRIDES: dict[str, dict] = {
    "s1_where_gemini": {"blocks": [{"text": "Where do crews<br>go first?", "size": 92, "top": 50, "left": 130}]},
    "s1_map_gemini": {"blocks": [{"text": "Every crew knows<br>where to go.", "size": 92, "top": 45, "left": 130}]},
    "s1_dawn_gemini": {"blocks": [
        {"text": "Daybreak", "size": 230, "top": 60, "left": 120, "track": "-0.045em"},
        {"text": "Tomorrow\u2019s crews, planned tonight.", "size": 52, "top": 315, "left": 132,
         "wght": 500, "track": "-0.012em"}]},
    "g2_problems_gemini": {"label_bottom": 110},
}


def apply_overrides(frames: dict[str, dict]) -> dict[str, dict]:
    for fid, patch in OVERRIDES.items():
        if fid in frames:
            frames[fid] = {**frames[fid], **patch}
    return frames


def sheet() -> None:
    from PIL import Image, ImageDraw, ImageFont
    w, h, pad, head = 512, 288, 12, 44
    img = Image.new("RGB", (5 * w + 6 * pad, len(ROWS) * (h + head) + pad), (20, 20, 20))
    dr = ImageDraw.Draw(img)
    ft = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 24)
    for r, (style, model) in enumerate(ROWS):
        y = r * (h + head) + pad
        dr.text((pad, y + 8), f"{style}  {NAMES[style]}  ·  {NAMES[model]}", fill=(235, 235, 235), font=ft)
        for c, beat in enumerate(BEATS):
            p = v2.OUT / f"{style}_{beat}_{model}.png"
            if p.exists():
                img.paste(Image.open(p).convert("RGB").resize((w, h), Image.LANCZOS),
                          (pad + c * (w + pad), y + head))
    img.save(HERE / "contact_sheet.jpg", quality=86)
    print("ok contact_sheet.jpg", img.size)


if __name__ == "__main__":
    for style, model in ROWS:
        v2.FRAMES = apply_overrides(frames_for(style, model))
        for fid in v2.FRAMES:
            v2.render(fid)
    sheet()
