"""Populația demo: circa 300 de posturi de transformare SINTETICE în București-Ilfov.

Pozițiile vin, unde se poate, din posturi reale cartografiate în OpenStreetMap (ODbL, „© OpenStreetMap
contributors”); restul sunt poziții sintetice în jurul localităților din Ilfov. Rețeaua din spatele fiecărui
post, prosumatorii și bateriile sunt sintetice (variante SimBench). Codurile PT-xxxx sunt inventate.

    uv run python -m cyberpunks.c_prosumatori.population      # registrul + simularea fizică a populației
"""

from __future__ import annotations

import json
import math
import unicodedata

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import grids
from cyberpunks.common.paths import DATA_PROCESSED, DATA_RAW, DATA_SAMPLES

BBOX = (44.25, 25.85, 44.65, 26.40)  # config/area.yaml: demo_bbox_bucuresti_ilfov
CENTER = (44.4268, 26.1025)  # Piața Unirii, aproximativ
OSM_FILE = DATA_RAW / "C" / "osm_power_bbox.json"
OUT = DATA_PROCESSED / "C" / "population"
SAMPLE = DATA_SAMPLES / "C" / "posts.csv"
OVERPASS_QUERY = f"""[out:json][timeout:90];
(
  nwr["power"="transformer"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  nwr["power"="substation"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
  nwr["power"="pole"]["transformer"]({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});
);
out center tags;"""

# Centrele sectoarelor și ale localităților din Ilfov (coordonate aproximative, WGS84) și ponderea lor
# în pozițiile sintetice (IPOTEZĂ: după mărimea localității și numărul de case noi).
SECTORS = {
    "B-S1": ("Sector 1", 44.480, 26.070),
    "B-S2": ("Sector 2", 44.450, 26.130),
    "B-S3": ("Sector 3", 44.420, 26.150),
    "B-S4": ("Sector 4", 44.380, 26.110),
    "B-S5": ("Sector 5", 44.400, 26.060),
    "B-S6": ("Sector 6", 44.435, 26.020),
}
LOCALITIES = {
    "Voluntari": (44.490, 26.176, 8),
    "Popești-Leordeni": (44.380, 26.169, 8),
    "Chiajna": (44.459, 25.975, 8),
    "Bragadiru": (44.371, 25.975, 8),
    "Pantelimon": (44.452, 26.208, 5),
    "Buftea": (44.562, 25.948, 4),
    "Otopeni": (44.552, 26.069, 5),
    "Măgurele": (44.349, 26.029, 5),
    "Chitila": (44.508, 25.982, 4),
    "Mogoșoaia": (44.529, 25.996, 4),
    "Corbeanca": (44.602, 25.997, 5),
    "Ștefăneștii de Jos": (44.551, 26.193, 4),
    "Domnești": (44.398, 25.918, 4),
    "Cornetu": (44.344, 25.940, 3),
    "Jilava": (44.334, 26.077, 3),
    "Berceni": (44.315, 26.120, 3),
    "Glina": (44.383, 26.248, 3),
    "Cernica": (44.418, 26.283, 3),
    "Tunari": (44.548, 26.140, 4),
    "Balotești": (44.613, 26.093, 3),
    "Dobroești": (44.452, 26.182, 3),
    "Afumați": (44.497, 26.249, 3),
    "Clinceni": (44.373, 25.951, 3),
    "1 Decembrie": (44.290, 26.060, 2),
    "Dărăști-Ilfov": (44.310, 26.000, 2),
    "Ciorogârla": (44.437, 25.880, 2),
}
TOPOLOGY_BY_AREA = {
    "urban": (["urban6", "semiurb5", "semiurb4"], [0.65, 0.25, 0.10]),
    "semiurban": (["semiurb4", "semiurb5", "rural2", "rural3"], [0.30, 0.30, 0.20, 0.20]),
    "rural": (["rural1", "rural2", "rural3"], [0.25, 0.35, 0.40]),
}


def _ascii(s: str) -> str:
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper().replace(" ", "-")


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dy = (lat2 - lat1) * 111.2
    dx = (lon2 - lon1) * 111.2 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


OVERPASS_ENDPOINTS = ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter")


def download_osm(tries: int = 3) -> None:
    """Descarcă posturile din OSM; încearcă două servere Overpass, cu reîncercări (serviciul cade uneori, 502/504)."""
    import time

    import httpx

    from cyberpunks.c_prosumatori.weather import record_checksum

    last = None
    for attempt in range(tries):
        for url in OVERPASS_ENDPOINTS:
            try:
                r = httpx.post(url, data={"data": OVERPASS_QUERY}, timeout=120, headers={"User-Agent": "CyberPunks-hackathon/0.1"})
                r.raise_for_status()
                OSM_FILE.parent.mkdir(parents=True, exist_ok=True)
                OSM_FILE.write_bytes(r.content)
                record_checksum(OSM_FILE)
                return
            except httpx.HTTPError as exc:
                last = exc
                print(f"Overpass {url}: {exc}; reîncerc", flush=True)
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"OpenStreetMap (Overpass) nu răspunde: {last}")


def _max_voltage(tag: str | None) -> float:
    if not tag:
        return 0.0
    vals = []
    for part in str(tag).replace(",", ";").split(";"):
        try:
            vals.append(float(part.strip()))
        except ValueError:
            continue
    return max(vals) if vals else 0.0


def osm_positions() -> pd.DataFrame:
    """Posturile de distribuție plauzibile din OSM (fără stații de 110 kV+, puncte termice, tracțiune)."""
    if not OSM_FILE.exists():
        download_osm()
    els = json.loads(OSM_FILE.read_text())["elements"]
    rows = []
    for e in els:
        t = e.get("tags", {})
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None or lon is None:
            continue
        power, sub, tr = t.get("power"), t.get("substation"), t.get("transformer")
        ok = (
            (power == "substation" and sub in (None, "minor_distribution", "distribution", "yes"))
            or (power == "transformer" and tr in (None, "distribution"))
            or (power == "pole" and tr == "distribution")
        )
        op = (t.get("operator") or "").lower()
        if not ok or _max_voltage(t.get("voltage")) >= 33000 or any(k in op for k in ("termo", "radet", "transelectrica")):
            continue
        rows.append({"lat": float(lat), "lon": float(lon), "osm_ref": f"{e['type']}/{e['id']}", "osm_tags": t.get("power") + (f"={sub or tr}" if (sub or tr) else "")})
    df = pd.DataFrame(rows).drop_duplicates(subset=["lat", "lon"])
    return df[(df.lat.between(BBOX[0], BBOX[2])) & (df.lon.between(BBOX[1], BBOX[3]))].reset_index(drop=True)


def _zone(lat: float, lon: float) -> tuple[str, str, str]:
    """(zone_id, county, nume localitate). În raza de 8,5 km de centru: cel mai apropiat sector (București are
    circa 228 km², adică o rază de circa 8,5 km); în afară: cea mai apropiată localitate din Ilfov."""
    if _km(lat, lon, *CENTER) < 8.5:
        zid, (name, _, _) = min(SECTORS.items(), key=lambda kv: _km(lat, lon, kv[1][1], kv[1][2]))
        return zid, "București", name
    name = min(LOCALITIES, key=lambda k: _km(lat, lon, LOCALITIES[k][0], LOCALITIES[k][1]))
    return f"IF-{_ascii(name)}", "Ilfov", name


def _area(lat: float, lon: float, county: str) -> str:
    d = _km(lat, lon, *CENTER)
    if county == "București":
        return "urban" if d < 6.0 else "semiurban"
    return "semiurban" if d < 12.0 else "rural"


def build_registry(n_total: int = 300, seed: int = 8112026) -> tuple[pd.DataFrame, list[grids.PostSpec]]:
    rng = np.random.default_rng(seed)
    osm = osm_positions()
    if len(osm) > n_total:
        osm = osm.sample(n_total, random_state=seed).reset_index(drop=True)
    osm["position_source"] = "osm"
    n_syn = n_total - len(osm)
    names = list(LOCALITIES)
    w = np.array([LOCALITIES[k][2] for k in names], dtype=float)
    syn = []
    for _ in range(n_syn):
        k = names[int(rng.choice(len(names), p=w / w.sum()))]
        la, lo, _ = LOCALITIES[k]
        syn.append({"lat": float(np.clip(la + rng.normal(0, 0.006), BBOX[0], BBOX[2])),
                    "lon": float(np.clip(lo + rng.normal(0, 0.008), BBOX[1], BBOX[3])),
                    "osm_ref": None, "osm_tags": None, "position_source": "sintetic"})
    reg = pd.concat([osm, pd.DataFrame(syn)], ignore_index=True)
    order = rng.permutation(len(reg))
    reg = reg.iloc[order].reset_index(drop=True)
    specs, extra = [], []
    for i, r in reg.iterrows():
        zid, county, loc = _zone(r.lat, r.lon)
        area = _area(r.lat, r.lon, county)
        topo_opts, p = TOPOLOGY_BY_AREA[area]
        topo = topo_opts[int(rng.choice(len(topo_opts), p=p))]
        pid = f"PT-{1001 + i}"
        specs.append(grids.sample_spec(topo, rng, pid, mode="population"))
        extra.append({"post_id": pid, "zone_id": zid, "county": county, "locality": loc, "area": area, "topology": topo,
                      "label": f"{pid}, {loc} (sintetic)"})
    reg = pd.concat([reg, pd.DataFrame(extra)], axis=1)
    reg["lat"], reg["lon"] = reg.lat.round(5), reg.lon.round(5)
    return reg, specs


def export_samples(reg: pd.DataFrame) -> None:
    """Registrul în git (`data/samples/C/posts.csv`): tot ce trebuie pentru predict.py și pentru firele care
    folosesc postul ca unitate comună, inclusiv parametrii exacți ai simulării (spec_*)."""
    from cyberpunks.c_prosumatori.features import STATIC

    reg = reg.copy()
    reg["simbench_code"] = reg["topology"].map(grids.TOPOLOGIES)
    cols = ["post_id", "label", "lat", "lon", "zone_id", "county", "locality", "area", "position_source", "osm_ref", "topology",
            "simbench_code", "kva", "n_customers", "n_houses", "n_prosumers", "pv_kw", "battery_kwh", "line_type", "tap_pos"]
    full = list(dict.fromkeys(cols + STATIC + ["vm_mv_est"] + [c for c in reg.columns if c.startswith("spec_")]))
    SAMPLE.parent.mkdir(parents=True, exist_ok=True)
    out = reg[full].assign(synthetic=True)
    for c in ("kva", "tap_pos", "n_customers", "n_houses", "n_prosumers", "spec_seed", "spec_kva", "spec_tap_pos"):
        if c in out:
            out[c] = out[c].astype(int)
    # fără rotunjire: parametrii spec_* trebuie să refacă exact aceeași rețea dintr-o clonă curată
    out.to_csv(SAMPLE, index=False)


LOCATION_COLS = ["post_id", "label", "lat", "lon", "zone_id", "county", "locality", "area", "position_source", "osm_ref", "osm_tags"]


def registry_from_git() -> tuple[pd.DataFrame, list[grids.PostSpec]]:
    """Registrul din git (`data/samples/C/posts.csv`): aceleași posturi și coduri PT pentru toate firele, fără OSM."""
    reg = pd.read_csv(SAMPLE)
    specs = [grids.spec_from_row(r) for _, r in reg.iterrows()]
    return reg[[c for c in LOCATION_COLS if c in reg.columns]], specs


def main(from_osm: bool = False) -> None:
    """Implicit refolosește registrul din git (posturile, pozițiile și parametrii exacți), apoi simulează.
    Cu --from-osm reconstruiește registrul de la zero din OpenStreetMap (codurile PT se pot schimba)."""
    from cyberpunks.c_prosumatori import simulate

    if from_osm or not SAMPLE.exists():
        reg, specs = build_registry()
        reg = reg.drop(columns=["topology"])
    else:
        reg, specs = registry_from_git()
    OUT.mkdir(parents=True, exist_ok=True)
    posts = simulate.run_pool("population", specs, workers=4)
    reg = reg.merge(posts, on="post_id")
    reg.to_parquet(OUT / "registry.parquet")
    export_samples(reg)
    print(reg.groupby(["county", "area"]).size(), "\n", reg.position_source.value_counts())
    print(reg[["pv_kw_per_kva", "n_prosumers", "pv_kw"]].describe().round(2))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--from-osm", action="store_true", help="reconstruiește registrul din OpenStreetMap (codurile PT se pot schimba)")
    main(ap.parse_args().from_osm)
