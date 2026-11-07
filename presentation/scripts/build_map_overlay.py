"""Conturul României și al celor trei regiuni Rețele Electrice, în pixelii imaginii NASA de noapte.

Sursa granițelor: geoBoundaries ROU ADM1 (Banca Mondială), licență CC BY 4.0.
Rulare (din rădăcina repo-ului):
    uv run --with shapely python presentation/scripts/build_map_overlay.py
Scrie presentation/video/assets/geo/regions.json (căi SVG în pixelii imaginii romania_night_z8.png).
"""

from __future__ import annotations

import json
import math
import pathlib
import urllib.request

from shapely.geometry import shape
from shapely.ops import transform, unary_union

ROOT = pathlib.Path(__file__).resolve().parents[2]
PRES = ROOT / "presentation"
RAW = ROOT / "data" / "raw" / "presentation"
GEO_URL = (
    "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/ROU/ADM1/"
    "geoBoundaries-ROU-ADM1_simplified.geojson"
)
META = json.loads((PRES / "video/assets/img/romania_night_z8.json").read_text())
Z, X0, Y0 = META["z"], META["x_tiles"][0], META["y_tiles"][0]

REGIONS = {  # la fel ca în config/area.yaml
    "muntenia_sud": ["BUCURESTI", "ILFOV", "GIURGIU"],
    "dobrogea": ["CONSTANTA", "TULCEA", "CALARASI", "IALOMITA"],
    "banat": ["TIMIS", "ARAD", "CARAS-SEVERIN", "HUNEDOARA"],
}
POINTS = {  # bazele operative simulate din config/area.yaml, plus orașele mari pentru etichete
    "D-BUC-V": (26.0160, 44.4355),
    "D-BUC-E": (26.1650, 44.4310),
    "D-CTA": (28.6383, 44.1733),
    "D-TM": (21.2257, 45.7537),
    "Bucuresti": (26.1025, 44.4268),
}


def to_px(lon: float, lat: float, z: int = Z) -> tuple[float, float]:
    n = 2**z
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.log(math.tan(lat_r) + 1.0 / math.cos(lat_r)) / math.pi) / 2.0 * n
    return (x - X0) * 256.0, (y - Y0) * 256.0


def proj(x, y, z=None):  # shapely transform: tablouri de lon/lat
    import numpy as np

    lon = np.asarray(x)
    lat = np.asarray(y)
    n = 2**Z
    px = ((lon + 180.0) / 360.0 * n - X0) * 256.0
    lat_r = np.radians(lat)
    py = ((1.0 - np.log(np.tan(lat_r) + 1.0 / np.cos(lat_r)) / math.pi) / 2.0 * n - Y0) * 256.0
    return px, py


def to_path(geom) -> str:
    polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    parts = []
    for p in polys:
        for ring in [p.exterior, *p.interiors]:
            pts = list(ring.coords)
            parts.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return "".join(parts)


def write_svgs(out: dict, all3, regions: dict) -> None:
    """Straturi SVG de aceeași mărime cu imaginea de noapte, animate separat în video."""
    w, h = out["image_size"]
    geo = PRES / "video/assets/geo"
    geo.mkdir(parents=True, exist_ok=True)
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
    holes = "".join(r["path"] for r in out["regions"].values())
    (geo / "dim_outside.svg").write_text(
        head + f'<path fill="#07090D" fill-rule="evenodd" d="M0,0H{w}V{h}H0Z{holes}"/></svg>'
    )
    (geo / "regions_outline.svg").write_text(
        head
        + "".join(
            f'<path fill="none" stroke="#F2EFE8" stroke-width="2.2" stroke-linejoin="round" d="{r["path"]}"/>'
            for r in out["regions"].values()
        )
        + "</svg>"
    )
    (geo / "romania_outline.svg").write_text(
        head + f'<path fill="none" stroke="#F2EFE8" stroke-width="1.6" stroke-linejoin="round" d="{out["romania"]}"/></svg>'
    )
    out["labels"] = {}
    for reg, geom in regions.items():
        pt = geom.representative_point()
        out["labels"][reg] = [round(pt.x, 1), round(pt.y, 1)]


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    src = RAW / "geoBoundaries-ROU-ADM1_simplified.geojson"
    if not src.exists():
        urllib.request.urlretrieve(GEO_URL, src)
    fc = json.loads(src.read_text())
    counties = {f["properties"]["shapeName"]: transform(proj, shape(f["geometry"])) for f in fc["features"]}
    out = {
        "source": "geoBoundaries ROU ADM1 (World Bank), CC BY 4.0",
        "image": "assets/img/romania_night_z8.jpg",
        "image_size": META["size"],
        "romania": to_path(unary_union(list(counties.values())).simplify(0.6)),
        "regions": {},
        "counties": {},
        "points": {k: [round(v, 1) for v in to_px(*ll)] for k, ll in POINTS.items()},
    }
    for reg, names in REGIONS.items():
        geom = unary_union([counties[n] for n in names]).simplify(0.6)
        out["regions"][reg] = {"path": to_path(geom), "bbox": [round(v, 1) for v in geom.bounds]}
        for n in names:
            out["counties"][n] = to_path(counties[n].simplify(0.6))
    all3 = unary_union([counties[n] for ns in REGIONS.values() for n in ns])
    out["regions_bbox"] = [round(v, 1) for v in all3.bounds]
    write_svgs(out, all3, {reg: unary_union([counties[n] for n in names]) for reg, names in REGIONS.items()})
    dst = PRES / "video/assets/geo/regions.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(out))
    print(dst, "regions_bbox", out["regions_bbox"], "points", out["points"])
    print("size KB", round(dst.stat().st_size / 1024, 1))


if __name__ == "__main__":
    main()
