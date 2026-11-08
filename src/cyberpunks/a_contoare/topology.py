"""Topologie SINTETICĂ pentru firul A (contoare defecte sau manipulate).

DE LA 7 NOV., 14:00: posturile vin din registrul COMUN al produsului, deținut de firul C
(`data/samples/C/posts.csv`, PT-1001..PT-1300, 300 de posturi cu numărul de clienți), ca A, C și bilanțul pe post
să se întâlnească la același post și harta să arate un singur set de posturi. `build_from_registry()` pune pe
fiecare post contoarele inteligente INTEGRATE: 58,81% din clienții postului, gradul de integrare a contoarelor
inteligente în Muntenia la 31 dec. 2025 (sursă: infobuz, rezumat în memory/12-probleme-reale-ppc-2026.md,
neverificat de noi), adică ~15.900 de contoare cu date la 30 de minute.

Varianta veche (păstrată ca rezervă, `build_topology()`): ~10.000 de contoare pe ~400 de posturi proprii, din OSM.

Surse:
- poziții de posturi: OpenStreetMap, prin Overpass API (`power=transformer` și `power=substation`, fără stații
  de înaltă tensiune, fără schimbătoare de căldură, tracțiune, transport sau generare). OSM are doar ~200 de
  posturi utilizabile în zonă, așa că restul sunt posturi sintetice plasate lângă locuri (`place=*`) din OSM;
- zone: poligoane administrative OSM (`admin_level=9` pentru sectoarele Bucureștiului, `admin_level=8` pentru
  localitățile din Ilfov). Un punct primește zona poligonului care îl conține (matplotlib.path, fără shapely).
  Dacă Overpass nu e disponibil și nu există cache, se folosește varianta de rezervă: ~45 de centre fixe,
  cu zona dată de cel mai apropiat centru (Voronoi) și toate posturile sintetice.

© OpenStreetMap contributors, ODbL 1.0 (https://www.openstreetmap.org/copyright)

ATENȚIE: conectivitatea electrică a posturilor (care post alimentează ce) și TOATE contoarele sunt SINTETICE.
Geografia reală dă doar poziții plauzibile. Numerele posturilor din etichete sunt inventate.

Rulare: `uv run python -m cyberpunks.a_contoare.topology`
"""

from __future__ import annotations

import json
import re
import time
import unicodedata
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

ROOT = Path(__file__).resolve().parents[3]
RAW_DIR = ROOT / "data" / "raw" / "A" / "osm"
OUT_DIR = ROOT / "data" / "samples" / "A"
POSTS_CSV = OUT_DIR / "posts.csv"  # doar varianta veche
METERS_CSV = OUT_DIR / "meters.csv"
C_POSTS_CSV = ROOT / "data" / "samples" / "C" / "posts.csv"  # registrul comun al posturilor (firul C)
SMART_METER_INTEGRATION = 0.5881  # Muntenia, 31.12.2025 (infobuz; memory/12-probleme-reale-ppc-2026.md)
METER_RADIUS_M = {"urban": (25, 150), "semiurban": (40, 250), "rural": (60, 400)}

BBOX = {"lat_min": 44.25, "lat_max": 44.65, "lon_min": 25.85, "lon_max": 26.40}
BBOX_STR = f"{BBOX['lat_min']},{BBOX['lon_min']},{BBOX['lat_max']},{BBOX['lon_max']}"
OVERPASS_URLS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
USER_AGENT = "CyberPunks-SmartHack-2026/0.1 (hackathon research)"

BUCHAREST_SHARE = 0.75  # ponderea posturilor din București
M_PER_DEG = 111_320.0

# Interogările Overpass (numele fișierului din cache => text)
QUERIES = {
    "power.json": f'[out:json][timeout:90];nw["power"~"^(transformer|substation)$"]({BBOX_STR});out center tags;',
    "admin.json": (
        '[out:json][timeout:200];(area["ISO3166-2"="RO-B"];area["ISO3166-2"="RO-IF"];)->.a;'
        'rel(area.a)["boundary"="administrative"]["admin_level"~"^(8|9)$"];out geom;'
    ),
    "places.json": (
        '[out:json][timeout:90];node["place"~"^(city|town|village|suburb|quarter|neighbourhood)$"]'
        f"({BBOX_STR});out tags;"
    ),
}

# Tipuri de substații care NU sunt posturi de distribuție
EXCLUDED_SUBSTATION = {"heat-exchanger", "transmission", "traction", "generation", "transition"}
PLACE_WEIGHT = {"city": 3, "town": 3, "suburb": 2, "quarter": 2, "neighbourhood": 2, "village": 1}

# Ultima soluție: centre fixe (nume, lat, lon, zone_id, county), coordonate aproximative
_B = "București"
SEED_CENTRES = [
    ("Aviatorilor", 44.4690, 26.0850, "B-S1", _B), ("Băneasa", 44.5010, 26.0750, "B-S1", _B),
    ("Dorobanți", 44.4570, 26.0980, "B-S1", _B), ("Domenii", 44.4650, 26.0700, "B-S1", _B),
    ("Floreasca", 44.4680, 26.1050, "B-S1", _B), ("Bucureștii Noi", 44.4900, 26.0450, "B-S1", _B),
    ("Colentina", 44.4580, 26.1450, "B-S2", _B), ("Pantelimon", 44.4430, 26.1780, "B-S2", _B),
    ("Obor", 44.4520, 26.1250, "B-S2", _B), ("Iancului", 44.4410, 26.1370, "B-S2", _B),
    ("Moșilor", 44.4350, 26.1200, "B-S2", _B), ("Titan", 44.4260, 26.1650, "B-S3", _B),
    ("Dristor", 44.4180, 26.1350, "B-S3", _B), ("Vitan", 44.4040, 26.1300, "B-S3", _B),
    ("Balta Albă", 44.4180, 26.1850, "B-S3", _B), ("Dudești", 44.4090, 26.1180, "B-S3", _B),
    ("Berceni", 44.3750, 26.1250, "B-S4", _B), ("Tineretului", 44.4080, 26.1060, "B-S4", _B),
    ("Olteniței", 44.3830, 26.1180, "B-S4", _B), ("Giurgiului", 44.3820, 26.0900, "B-S4", _B),
    ("Rahova", 44.3950, 26.0600, "B-S5", _B), ("Cotroceni", 44.4350, 26.0650, "B-S5", _B),
    ("13 Septembrie", 44.4120, 26.0780, "B-S5", _B), ("Ferentari", 44.3990, 26.0750, "B-S5", _B),
    ("Drumul Taberei", 44.4240, 26.0230, "B-S6", _B), ("Militari", 44.4350, 25.9810, "B-S6", _B),
    ("Crângași", 44.4520, 26.0420, "B-S6", _B), ("Giulești", 44.4550, 26.0300, "B-S6", _B),
    ("Ghencea", 44.4130, 26.0100, "B-S6", _B),
    ("Voluntari", 44.4900, 26.1700, "IF-VOLUNTARI", "Ilfov"), ("Otopeni", 44.5500, 26.0700, "IF-OTOPENI", "Ilfov"),
    ("Chiajna", 44.4500, 25.9800, "IF-CHIAJNA", "Ilfov"), ("Bragadiru", 44.3700, 25.9800, "IF-BRAGADIRU", "Ilfov"),
    ("Popești-Leordeni", 44.3800, 26.1700, "IF-POPESTI-LEORDENI", "Ilfov"),
    ("Buftea", 44.5650, 25.9500, "IF-BUFTEA", "Ilfov"), ("Chitila", 44.5050, 25.9800, "IF-CHITILA", "Ilfov"),
    ("Mogoșoaia", 44.5200, 26.0050, "IF-MOGOSOAIA", "Ilfov"), ("Pantelimon", 44.4450, 26.2050, "IF-PANTELIMON", "Ilfov"),
    ("Măgurele", 44.3500, 26.0300, "IF-MAGURELE", "Ilfov"), ("Balotești", 44.6000, 26.0800, "IF-BALOTESTI", "Ilfov"),
    ("Dobroești", 44.4600, 26.2200, "IF-DOBROESTI", "Ilfov"), ("Cernica", 44.4150, 26.2400, "IF-CERNICA", "Ilfov"),
    ("Jilava", 44.3350, 26.0750, "IF-JILAVA", "Ilfov"), ("Corbeanca", 44.6200, 26.0500, "IF-CORBEANCA", "Ilfov"),
]  # fmt: skip


def ascii_slug(name: str) -> str:
    """Nume fără diacritice, cu majuscule și cratime: 'Popești-Leordeni' -> 'POPESTI-LEORDENI'."""
    text = unicodedata.normalize("NFKD", name)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^A-Z0-9]+", "-", text.upper()).strip("-")


# ---------------------------------------------------------------- descărcare OSM


def _fetch(name: str, use_cache: bool) -> dict | None:
    """Întoarce JSON-ul Overpass (din cache sau de pe net). None dacă nu merge deloc."""
    path = RAW_DIR / name
    if use_cache and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    for url in OVERPASS_URLS:
        for attempt in range(2):
            try:
                resp = httpx.post(url, data={"data": QUERIES[name]}, headers={"User-Agent": USER_AGENT}, timeout=240)
                if resp.status_code == 200:
                    RAW_DIR.mkdir(parents=True, exist_ok=True)
                    path.write_text(resp.text, encoding="utf-8")
                    return resp.json()
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(5 * (attempt + 1))
    return None


# ---------------------------------------------------------------- zone


class Zones:
    """Caută zona pentru puncte: poligoane OSM sau, la nevoie, cel mai apropiat centru fix."""

    def __init__(self, entries: list[dict], polygons: list[list[MplPath]] | None, centres: np.ndarray | None):
        self.entries = entries  # [{zone_id, county, name}]
        self.polygons = polygons
        self.centres = centres

    def locate(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        """Indexul zonei pentru fiecare punct, -1 dacă nu e în nicio zonă."""
        lat, lon = np.asarray(lat, float), np.asarray(lon, float)
        idx = np.full(lat.shape, -1, dtype=int)
        if self.polygons is not None:
            pts = np.column_stack([lon, lat])
            for i, rings in enumerate(self.polygons):
                free = idx < 0
                for ring in rings:
                    free = idx < 0
                    if free.any():
                        inside = ring.contains_points(pts[free])
                        idx[np.flatnonzero(free)[inside]] = i
            return idx
        assert self.centres is not None
        dy = (lat[:, None] - self.centres[None, :, 0]) * M_PER_DEG
        dx = (lon[:, None] - self.centres[None, :, 1]) * M_PER_DEG * np.cos(np.radians(44.4))
        return np.argmin(dx**2 + dy**2, axis=1)


def _assemble_rings(members: list[dict]) -> list[MplPath]:
    """Îmbină căile `outer` ale unei relații în inele închise (poligoane)."""
    ways = [[(p["lon"], p["lat"]) for p in m["geometry"]] for m in members if m.get("role") == "outer"]
    ways = [w for w in ways if len(w) >= 2]
    rings: list[MplPath] = []
    while ways:
        chain = ways.pop(0)
        grown = True
        while grown and chain[0] != chain[-1]:
            grown = False
            for i, w in enumerate(ways):
                if w[0] == chain[-1]:
                    chain += w[1:]
                elif w[-1] == chain[-1]:
                    chain += w[::-1][1:]
                elif w[-1] == chain[0]:
                    chain = w[:-1] + chain
                elif w[0] == chain[0]:
                    chain = w[::-1][:-1] + chain
                else:
                    continue
                ways.pop(i)
                grown = True
                break
        if len(chain) >= 4:
            rings.append(MplPath(np.array(chain)))
    return rings


def _zones_from_admin(admin: dict) -> Zones | None:
    """Zone din poligoane OSM: sectoare (nivel 9) și localități Ilfov (nivel 8)."""
    entries: list[dict] = []
    polygons: list[list[MplPath]] = []
    for el in admin.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name", "")
        rings = _assemble_rings(el.get("members", []))
        if not rings or not name:
            continue
        if tags.get("admin_level") == "9":
            match = re.search(r"(\d)", name)
            if not match or not name.lower().startswith("sector"):
                continue
            entries.append({"zone_id": f"B-S{match.group(1)}", "county": "București", "name": name})
        else:
            entries.append({"zone_id": f"IF-{ascii_slug(name)}", "county": "Ilfov", "name": name})
        polygons.append(rings)
    sectors = {e["zone_id"] for e in entries if e["county"] == "București"}
    if len(sectors) < 6 or len(entries) < 20:
        return None
    return Zones(entries, polygons, None)


def _zones_from_seeds() -> Zones:
    entries = [{"zone_id": z, "county": c, "name": n} for n, _, _, z, c in SEED_CENTRES]
    centres = np.array([[lat, lon] for _, lat, lon, _, _ in SEED_CENTRES])
    return Zones(entries, None, centres)


# ---------------------------------------------------------------- posturi


def _osm_posts(power: dict | None) -> pd.DataFrame:
    """Posturi reale din OSM (fără stații mari sau de alt tip), fără dubluri apropiate."""
    rows, seen = [], set()
    for el in (power or {}).get("elements", []):
        tags = el.get("tags", {})
        if tags.get("substation") in EXCLUDED_SUBSTATION:
            continue
        volts = [int(v) for v in re.findall(r"\d+", tags.get("voltage", ""))]
        if volts and max(volts) >= 110_000:
            continue
        lat = el.get("lat", el.get("center", {}).get("lat"))
        lon = el.get("lon", el.get("center", {}).get("lon"))
        if lat is None or lon is None:
            continue
        key = (round(lat / 0.0002), round(lon / 0.0002))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"lat": lat, "lon": lon, "osm_id": f"{el['type']}/{el['id']}"})
    return pd.DataFrame(rows, columns=["lat", "lon", "osm_id"])


def _places(places: dict | None, zones: Zones) -> pd.DataFrame:
    """Locuri (suburbii, sate, orașe) cu zona lor; folosite ca ancore pentru posturile sintetice."""
    rows = []
    if places is not None and zones.polygons is not None:
        for el in places.get("elements", []):
            name = el.get("tags", {}).get("name")
            if name and "lat" in el:
                rows.append(
                    {
                        "name": name,
                        "lat": el["lat"],
                        "lon": el["lon"],
                        "weight": PLACE_WEIGHT.get(el["tags"].get("place"), 1),
                    }
                )
    if not rows:  # varianta de rezervă: centrele fixe
        rows = [{"name": n, "lat": la, "lon": lo, "weight": 2} for n, la, lo, _, _ in SEED_CENTRES]
    df = pd.DataFrame(rows).drop_duplicates(["name", "lat", "lon"]).reset_index(drop=True)
    df["zone_idx"] = zones.locate(df["lat"].to_numpy(), df["lon"].to_numpy())
    df = df[df["zone_idx"] >= 0].reset_index(drop=True)
    df["county"] = [zones.entries[i]["county"] for i in df["zone_idx"]]
    if zones.polygons is not None:
        # localitățile Ilfov fără loc în OSM primesc centrul poligonului ca ancoră
        missing = [i for i, e in enumerate(zones.entries) if e["county"] == "Ilfov" and i not in set(df["zone_idx"])]
        extra = []
        for i in missing:
            verts = max(zones.polygons[i], key=lambda r: len(r.vertices)).vertices
            lon, lat = verts.mean(axis=0)
            if zones.locate(np.array([lat]), np.array([lon]))[0] == i:
                extra.append(
                    {
                        "name": zones.entries[i]["name"],
                        "lat": lat,
                        "lon": lon,
                        "weight": 1,
                        "zone_idx": i,
                        "county": "Ilfov",
                    }
                )
        df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
        # în Ilfov fiecare localitate are șanse apropiate, indiferent de câte noduri `place` are
        per_zone = df.groupby("zone_idx")["name"].transform("count")
        ilfov = df["county"] == "Ilfov"
        df.loc[ilfov, "weight"] = df.loc[ilfov, "weight"] / per_zone[ilfov]
    return df


def _synthetic_posts(n: int, county_quota: dict[str, int], places: pd.DataFrame, zones: Zones, rng) -> pd.DataFrame:
    """n posturi sintetice lângă locuri OSM, cu zgomot (~500 m), respectând cota pe județe."""
    rows = []
    for county, quota in county_quota.items():
        pl = places[places["county"] == county].reset_index(drop=True)
        if pl.empty or quota <= 0:
            continue
        probs = pl["weight"].to_numpy(float) / pl["weight"].sum()
        sigma = 450.0 if county == "București" else 700.0
        got, tries = 0, 0
        while got < quota and tries < 200:
            tries += 1
            k = quota - got
            pick = rng.choice(len(pl), size=k * 2, p=probs)
            lat = pl["lat"].to_numpy()[pick] + rng.normal(0, sigma, k * 2) / M_PER_DEG
            lon = pl["lon"].to_numpy()[pick] + rng.normal(0, sigma, k * 2) / (M_PER_DEG * np.cos(np.radians(lat)))
            ok = (
                (lat >= BBOX["lat_min"])
                & (lat <= BBOX["lat_max"])
                & (lon >= BBOX["lon_min"])
                & (lon <= BBOX["lon_max"])
            )
            zi = zones.locate(lat, lon)
            ok &= np.array([i >= 0 and zones.entries[i]["county"] == county for i in zi])
            for a, b in zip(lat[ok][:k], lon[ok][:k], strict=True):
                rows.append({"lat": a, "lon": b, "osm_id": ""})
                got += 1
    return pd.DataFrame(rows, columns=["lat", "lon", "osm_id"])


def _label_posts(posts: pd.DataFrame, zones: Zones, places: pd.DataFrame, rng) -> pd.DataFrame:
    """Adaugă zone_id, county și eticheta 'PT <număr inventat>, <loc>'."""
    zi = zones.locate(posts["lat"].to_numpy(), posts["lon"].to_numpy())
    posts = posts.assign(
        zone_id=[zones.entries[i]["zone_id"] for i in zi],
        county=[zones.entries[i]["county"] for i in zi],
    )
    locality = [zones.entries[i]["name"] for i in zi]
    buch = places[places["county"] == "București"]
    if not buch.empty:
        for j, (lat, lon, county) in enumerate(zip(posts["lat"], posts["lon"], posts["county"], strict=True)):
            if county != "București":
                continue
            dy = (buch["lat"].to_numpy() - lat) * M_PER_DEG
            dx = (buch["lon"].to_numpy() - lon) * M_PER_DEG * np.cos(np.radians(lat))
            d = np.hypot(dx, dy)
            k = int(np.argmin(d))
            if d[k] < 1500:
                locality[j] = buch["name"].iloc[k]
    numbers = rng.permutation(np.arange(1000, 10000))[: len(posts)]
    posts["label"] = [f"PT {num}, {loc}" for num, loc in zip(numbers, locality, strict=True)]
    return posts


def _meter_counts(n_posts: int, n_meters: int, rng) -> np.ndarray:
    """Număr de contoare pe post: lognormal, 5-80, suma exact n_meters."""
    raw = rng.lognormal(mean=np.log(25) - 0.18, sigma=0.6, size=n_posts)
    counts = np.clip(np.rint(raw * n_meters / raw.sum()), 5, 80).astype(int)
    while counts.sum() != n_meters:
        diff = n_meters - counts.sum()
        step = 1 if diff > 0 else -1
        movable = np.flatnonzero((counts + step >= 5) & (counts + step <= 80))
        take = rng.choice(movable, size=min(abs(diff), len(movable)), replace=False)
        counts[take] += step
    return counts


def build_topology(
    n_meters: int = 10_000, n_posts: int = 400, seed: int = 7, use_cache: bool = True
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construiește (posts, meters). Tot ce iese e SINTETIC, cu poziții plauzibile din OSM."""
    rng = np.random.default_rng(seed)
    admin = _fetch("admin.json", use_cache)
    zones = _zones_from_admin(admin) if admin else None
    power = _fetch("power.json", use_cache) if zones else None
    if zones is None:
        zones = _zones_from_seeds()
    places = _places(_fetch("places.json", use_cache) if zones.polygons is not None else None, zones)

    # posturi OSM reale, doar cele din București-Ilfov
    osm = _osm_posts(power)
    if len(osm):
        zi = zones.locate(osm["lat"].to_numpy(), osm["lon"].to_numpy())
        osm = osm[zi >= 0].reset_index(drop=True)
        if len(osm) > n_posts:
            osm = osm.sample(n_posts, random_state=seed).reset_index(drop=True)
    osm["source"] = "osm"
    zi = zones.locate(osm["lat"].to_numpy(), osm["lon"].to_numpy()) if len(osm) else np.array([], int)
    osm_county = [zones.entries[i]["county"] for i in zi]

    # cote pe județe pentru posturile sintetice (București ~75% din total)
    target_b = round(n_posts * BUCHAREST_SHARE)
    n_synth = n_posts - len(osm)
    osm_b = sum(c == "București" for c in osm_county)
    synth_b = min(max(target_b - osm_b, 0), n_synth)
    quota = {"București": synth_b, "Ilfov": n_synth - synth_b}
    synth = _synthetic_posts(n_synth, quota, places, zones, rng)
    synth["source"] = "sintetic"

    posts = pd.concat([osm, synth], ignore_index=True)
    posts = _label_posts(posts, zones, places, rng)
    posts = posts.sort_values(["county", "zone_id", "lat", "lon"], ignore_index=True)
    posts.insert(0, "post_id", [f"PT-{i + 1:04d}" for i in range(len(posts))])
    posts["n_meters"] = _meter_counts(len(posts), n_meters, rng)
    posts["lat"] = posts["lat"].round(6)
    posts["lon"] = posts["lon"].round(6)

    # contoare: în jurul postului, la 30-250 m, în orice direcție
    idx = np.repeat(np.arange(len(posts)), posts["n_meters"].to_numpy())
    radius = rng.uniform(30, 250, len(idx))
    angle = rng.uniform(0, 2 * np.pi, len(idx))
    plat = posts["lat"].to_numpy()[idx]
    lat = plat + radius * np.sin(angle) / M_PER_DEG
    lon = posts["lon"].to_numpy()[idx] + radius * np.cos(angle) / (M_PER_DEG * np.cos(np.radians(plat)))
    meters = pd.DataFrame(
        {
            "meter_id": [f"MTR-{i + 1:06d}" for i in range(len(idx))],
            "post_id": posts["post_id"].to_numpy()[idx],
            "lat": np.clip(lat, BBOX["lat_min"], BBOX["lat_max"]).round(6),
            "lon": np.clip(lon, BBOX["lon_min"], BBOX["lon_max"]).round(6),
            "zone_id": posts["zone_id"].to_numpy()[idx],  # contorul moștenește zona postului
            "county": posts["county"].to_numpy()[idx],
            "synthetic": True,
            "profile_slot": np.arange(len(idx)),
        }
    )
    posts = posts[["post_id", "lat", "lon", "zone_id", "county", "label", "osm_id", "source", "n_meters"]]
    return posts, meters


def load_registry_posts() -> pd.DataFrame:
    """Registrul comun al posturilor (firul C), coloanele de care are nevoie A."""
    cols = ["post_id", "label", "lat", "lon", "zone_id", "county", "locality", "area", "n_customers", "kva"]
    posts = pd.read_csv(C_POSTS_CSV)
    return posts[[c for c in cols if c in posts.columns]].copy()


def build_from_registry(rate: float = SMART_METER_INTEGRATION, seed: int = 7) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Contoarele inteligente integrate, pe posturile din registrul comun: round(rate × clienți) pe fiecare post."""
    rng = np.random.default_rng(seed)
    posts = load_registry_posts().sort_values("post_id").reset_index(drop=True)
    posts["n_meters"] = np.maximum(1, np.round(posts["n_customers"].to_numpy() * rate)).astype(int)
    rows = []
    mid = 0
    for _, p in posts.iterrows():
        lo, hi = METER_RADIUS_M.get(str(p.get("area", "semiurban")), (40, 250))
        k = int(p["n_meters"])
        ang = rng.uniform(0, 2 * np.pi, k)
        rad = rng.uniform(lo, hi, k)
        dlat = rad * np.cos(ang) / M_PER_DEG
        dlon = rad * np.sin(ang) / (M_PER_DEG * np.cos(np.radians(p["lat"])))
        for j in range(k):
            mid += 1
            rows.append(
                {
                    "meter_id": f"MTR-{mid:06d}",
                    "post_id": p["post_id"],
                    "lat": round(float(np.clip(p["lat"] + dlat[j], BBOX["lat_min"], BBOX["lat_max"])), 6),
                    "lon": round(float(np.clip(p["lon"] + dlon[j], BBOX["lon_min"], BBOX["lon_max"])), 6),
                    "zone_id": p["zone_id"],
                    "county": p["county"],
                    "synthetic": True,
                    "profile_slot": mid - 1,
                }
            )
    return posts, pd.DataFrame(rows)


def write_topology(posts: pd.DataFrame, meters: pd.DataFrame) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meters.sort_values("meter_id").to_csv(METERS_CSV, index=False, encoding="utf-8")


def load_topology() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(posturi din registrul comun, cu n_meters; contoarele A din data/samples/A/meters.csv)."""
    meters = pd.read_csv(METERS_CSV)
    posts = load_registry_posts()
    posts = posts.merge(meters.groupby("post_id").size().rename("n_meters"), on="post_id", how="left")
    posts["n_meters"] = posts["n_meters"].fillna(0).astype(int)
    return posts, meters


def main() -> None:
    posts, meters = build_from_registry()
    write_topology(posts, meters)
    print(f"Posturi din registrul comun: {len(posts)}, contoare integrate: {len(meters)} (SINTETICE)")
    print(posts.groupby("county").agg(posturi=("post_id", "count"), clienti=("n_customers", "sum"),
                                      contoare=("n_meters", "sum")).to_string())


if __name__ == "__main__":
    main()
