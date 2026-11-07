"""Gemini (via Figma) styles: risograph print and white architectural model: headlines set in code.

Reuses ../v2/compose.py (Archivo, headless Chrome, 1920x1080) and the frame layout of
../v3/compose.py. Sheet rows: v2 Hi-vis (reference), s1, s2, s3.

Run:  python3 presentation/frames-codex/v4/compose.py
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


v3 = _load("v3compose", HERE.parent / "v3" / "compose.py")
v2 = v3.v2
v2.PLATES = HERE / "plates"
v2.OUT = HERE / "frames"

B, W = v3.BLACK, v3.WHITE
# storm, where, problems labels (3), dawn
v3.INKS = {
    "g1": (B, B, (B, B, B), B),
    "g2": (B, B, (B, B, B), B),
}
v3.ROWS = [
    ("v2  Hi-vis (reference)", None),
    ("g1  Risograph print (Gemini)", "g1"),
    ("g2  White architectural model (Gemini)", "g2"),
]
v3.HERE = HERE  # the sheet is written next to this file

if __name__ == "__main__":
    for v in v3.INKS:
        v2.FRAMES = v3.frames_for(v)
        # the art leans into the top-left corner here: break the headline onto two lines
        v2.FRAMES[f"{v}_storm"]["blocks"][0]["text"] = "Storm hits<br>Banat."
        if v == "g1":  # the riso label boxes sit a little higher
            v2.FRAMES["g1_problems"]["label_bottom"] = 110
        if v == "g2":  # keep the subline clear of the model's roofs
            v2.FRAMES["g2_dawn"]["blocks"][0]["top"] = 90
            v2.FRAMES["g2_dawn"]["blocks"][1]["top"] = 370
        for fid in v2.FRAMES:
            v2.render(fid)
    v3.sheet()
