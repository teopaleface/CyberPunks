"""Varianta europeană a modelului B: avarii reale de joasă tensiune din nordul Scoției (SSEN, SHEPD).

Sursa: arhiva Zenodo „Power outages across three electricity distribution networks”, DOI 10.5281/zenodo.23303815,
CC BY 4.0 (datele NaFIRS LV ale SSEN Distribution). Un rând = o avarie JT, cu cauza, clienții afectați și minutele.

    uv run python -m cyberpunks.b_furtuna.ssen download     # fișierele SSEN, cu md5 (în afara git)
    uv run python -m cyberpunks.b_furtuna.ssen weather      # vremea Open-Meteo pe districte (~1.300 de apeluri)
    uv run python -m cyberpunks.b_furtuna.ssen dataset      # tabelul district × zi (în git, mic)
    uv run python -m cyberpunks.b_furtuna.ssen evaluate     # antrenare 2016-2023, test 2024-2025, reports/B/metrics_ssen.json

Eticheta: cel puțin o avarie JT cu cauză de vreme în district, în ziua respectivă (vânt și furtună, copaci căzuți,
materiale purtate de vânt, trăsnet, inundație, ploaie, zăpadă, gheață, ceață înghețată). „Copacii care cresc” nu e
o cauză de furtună și nu intră. Pragul sever: cel puțin 2 avarii de vreme în aceeași zi.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from cyberpunks.b_furtuna import openmeteo
from cyberpunks.b_furtuna.download import fetch
from cyberpunks.common.paths import DATA_RAW, DATA_SAMPLES

ZENODO = "https://zenodo.org/api/records/23303815/files/{name}/content"
SSEN_DIR = DATA_RAW / "B" / "ssen"
# nume fișier -> (octeți, md5), din API-ul Zenodo (verificat la descărcare)
SSEN_FILES = {
    "20260804_nafirs_lv_shepd_csv.csv": (7_436_861, "e02d35510457a656cb4b44a0d8844ab5"),
    "20260804_nafirs_lv_sepd_csv.csv": (32_329_849, "5f90b6f7dfb697e3a22dc1ae770c73f9"),
}
SHEPD = "20260804_nafirs_lv_shepd_csv.csv"

WEATHER_CAUSES = {
    "Wind and Gale (excluding Windborne Material)",
    "Falling live trees (not felled)",
    "Falling dead trees (not felled)",
    "Windborne Materials",
    "Lightning",
    "Flooding",
    "Rain",
    "Snow, Sleet and Blizzard",
    "Ice",
    "Freezing Fog and Frost",
}

# Districtele SHEPD folosite, cu un punct aproximativ pentru vreme (orașul principal sau centrul districtului).
# APROXIMARE: SSEN nu publică pozițiile stațiilor primare în arhiva Zenodo. Orkney și Shetland sunt lăsate deoparte
# (2 și 12 zile cu cel puțin 2 avarii de vreme în 10 ani: prea puțin pentru apelurile de vreme pe care le-ar costa).
DISTRICTS = {
    "ARGYLL": ("Lochgilphead (Argyll)", 56.038, -5.433),
    "HIGH": ("Inverness (Highland)", 57.478, -4.224),
    "N/EAST": ("Inverurie (Aberdeenshire)", 57.284, -2.374),
    "TAYCEN": ("Perth (Tayside și Central)", 56.396, -3.437),
    "WISLES": ("Stornoway (Insulele de Vest)", 58.209, -6.389),
}
START, END = "2016-01-01", "2025-12-31"
WX_START = "2015-12-25"  # 7 zile în plus pentru întârzieri (ploaia pe 7 zile, rafala din ajun)
TRAIN_YEARS, TEST_YEARS = tuple(range(2016, 2024)), (2024, 2025)

SSEN_WX_DIR = openmeteo.OM_DIR / "ssen"
SSEN_WEATHER_SAMPLE = DATA_SAMPLES / "B" / "ssen_weather_daily.parquet"
SSEN_TABLE = DATA_SAMPLES / "B" / "ssen_district_day.parquet"


def download() -> list[Path]:
    return [fetch(ZENODO.format(name=n), SSEN_DIR / n, size, md5) for n, (size, md5) in SSEN_FILES.items()]


def weather(calls_per_hour: float = 4000.0) -> None:
    """Vremea zilnică Open-Meteo pe districte, câte un fișier pe district (descărcarea se reia de unde a rămas)."""
    SSEN_WX_DIR.mkdir(parents=True, exist_ok=True)
    for code, (label, lat, lon) in DISTRICTS.items():
        dest = SSEN_WX_DIR / f"{code.replace('/', '_')}_{WX_START}_{END}.json"
        if dest.exists():
            continue
        t0 = time.time()
        payload = openmeteo.archive_daily([lat], [lon], WX_START, END, use_cache=False)[0]
        payload["_meta"] = {"district": code, "label": label, "fetched_utc": datetime.now(UTC).isoformat(timespec="seconds")}
        dest.write_text(json.dumps(payload), encoding="utf-8")
        cost = float(pd.read_csv(openmeteo.LEDGER).iloc[-1]["cost"] or 0)
        print(f"{code}: cost {cost:.1f}", flush=True)
        pause = cost / (calls_per_hour / 3600.0) - (time.time() - t0)
        if pause > 0:
            time.sleep(pause)
    export_weather()


def load_weather() -> pd.DataFrame:
    files = sorted(SSEN_WX_DIR.glob("*.json"))
    if not files:
        return pd.read_parquet(SSEN_WEATHER_SAMPLE) if SSEN_WEATHER_SAMPLE.exists() else pd.DataFrame()
    frames = []
    for p in files:
        payload = json.loads(p.read_text(encoding="utf-8"))
        d = openmeteo.daily_frame(payload)
        d["district"] = payload["_meta"]["district"]
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def export_weather() -> Path:
    df = load_weather()
    df.to_parquet(SSEN_WEATHER_SAMPLE, index=False, compression="zstd")
    print(f"{len(df):,} zile-district -> {SSEN_WEATHER_SAMPLE}")
    return SSEN_WEATHER_SAMPLE


def incidents() -> pd.DataFrame:
    d = pd.read_csv(SSEN_DIR / SHEPD, low_memory=False)
    d["t"] = pd.to_datetime(d["LV_INCIDENT_TIME"], format="%d/%m/%Y %H:%M", errors="coerce")
    d["date"] = d["t"].dt.normalize()
    d["weather_cause"] = d["CAUSE_DESCRIPTION"].isin(WEATHER_CAUSES)
    return d.rename(columns={"DISTRICT_SHORT_CODE": "district"})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["download", "weather", "dataset", "evaluate"])
    args = ap.parse_args(argv)
    if args.cmd == "download":
        download()
    elif args.cmd == "weather":
        weather()
    elif args.cmd == "dataset":
        from cyberpunks.b_furtuna.ssen_model import build_dataset
        build_dataset()
    elif args.cmd == "evaluate":
        from cyberpunks.b_furtuna.ssen_model import evaluate
        evaluate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
