"""Descarcă imaginea reală a României noaptea (NASA Black Marble 2016, VIIRS) și o lipește într-un PNG.

Sursa: NASA Earth Observatory / GIBS, stratul VIIRS_Black_Marble (date publice NASA, fără cheie).
Rulare (din rădăcina repo-ului): uv run python presentation/scripts/fetch_night_lights.py
"""

from __future__ import annotations

import io
import math
import pathlib
import urllib.request

from PIL import Image

Z = 8  # nivelul maxim al stratului (aprox. 500 m pe pixel la ecuator)
LON_MIN, LON_MAX = 19.5, 30.5
LAT_MIN, LAT_MAX = 43.0, 48.8
URL = (
    "https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_Black_Marble/default/2016-01-01/"
    "GoogleMapsCompatible_Level8/{z}/{y}/{x}.png"
)
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "video" / "assets" / "img" / "romania_night_z8.jpg"


def tile_xy(lon: float, lat: float, z: int) -> tuple[float, float]:
    n = 2**z
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return x, y


def main() -> None:
    x0, y0 = tile_xy(LON_MIN, LAT_MAX, Z)
    x1, y1 = tile_xy(LON_MAX, LAT_MIN, Z)
    xs = range(int(x0), int(x1) + 1)
    ys = range(int(y0), int(y1) + 1)
    img = Image.new("RGB", (256 * len(xs), 256 * len(ys)))
    for j, ty in enumerate(ys):
        for i, tx in enumerate(xs):
            req = urllib.request.Request(URL.format(z=Z, x=tx, y=ty), headers={"User-Agent": "cyberpunks-hackathon"})
            with urllib.request.urlopen(req, timeout=30) as r:
                tile = Image.open(io.BytesIO(r.read())).convert("RGB")
            img.paste(tile, (256 * i, 256 * j))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, quality=92)
    meta = {"z": Z, "x_tiles": [xs.start, xs.stop - 1], "y_tiles": [ys.start, ys.stop - 1], "size": img.size}
    (OUT.with_suffix(".json")).write_text(__import__("json").dumps(meta, indent=2))
    print(OUT, img.size, meta)


if __name__ == "__main__":
    main()
