"""Three more styles (miniature, pictogram poster, cut paper): headlines set in code.

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
    "s1": (B, B, (B, B, B), B),
    "s2": (W, B, (B, W, B), B),
    "s3": (B, B, (B, B, B), B),
}
v3.ROWS = [
    ("v2  Hi-vis (reference)", None),
    ("s1  Miniature world", "s1"),
    ("s2  Pictogram poster", "s2"),
    ("s3  Cut paper", "s3"),
]
v3.HERE = HERE  # the sheet is written next to this file

if __name__ == "__main__":
    for v in v3.INKS:
        v2.FRAMES = v3.frames_for(v)
        # the art leans into the top-left corner here: break the headline onto two lines
        v2.FRAMES[f"{v}_storm"]["blocks"][0]["text"] = "Storm hits<br>Banat."
        for fid in v2.FRAMES:
            v2.render(fid)
    v3.sheet()
