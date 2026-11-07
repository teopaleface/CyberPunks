"""Etichetele din fizică: circulația de puteri orară pentru fiecare post sintetic, pe toată perioada meteo.

Pentru fiecare oră: producția PV din meteo, consumul din profile, bateriile (autoconsum), tensiunea pe MT,
apoi calculul de rețea (pandapower + Z-bus vectorizat). Dacă un invertor vede peste 1,10 pu, se oprește
(cascadă: se oprește întâi cel mai expus, se recalculează). Rezultatul: tensiunea maximă fără opriri,
tensiunea minimă, încărcarea transformatorului, kWh fotovoltaici pierduți.

    uv run python -m cyberpunks.c_prosumatori.simulate one              # M0: un post, un an, cu timpi
    uv run python -m cyberpunks.c_prosumatori.simulate pool train --n 80 --workers 4
"""

from __future__ import annotations

import argparse
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import grids, profiles, weather
from cyberpunks.common.paths import DATA_PROCESSED

LIMIT_PU = 1.10  # EN 50160 / Ord. ANRE 46/2021 (limita de 100%) și protecția invertoarelor pe 10 min
OUT = DATA_PROCESSED / "C"
HOURLY_COLS = ["vmax", "vmin", "n_over", "lost_kwh", "pv_kw", "load_kw", "export_kw", "loading"]


def battery_dispatch(
    surplus: np.ndarray, cap_kwh: np.ndarray, p_kw: np.ndarray, eta: float = 0.95, allow_charge: np.ndarray | None = None
) -> np.ndarray:
    """Autoconsum: bateria se încarcă din surplusul PV și se descarcă când casa consumă. >0 = încărcare (kW).

    allow_charge (T,): orele în care bateria are voie să se încarce (de exemplu doar la prânz, ca să nu fie
    deja plină când tensiunea e maximă). Implicit: oricând.
    """
    n, T = surplus.shape
    soc = cap_kwh * 0.3
    out = np.empty((n, T))
    allow = np.ones(T, dtype=bool) if allow_charge is None else np.asarray(allow_charge, dtype=bool)
    for t in range(T):
        s = surplus[:, t]
        ch = np.minimum(np.minimum(np.maximum(s, 0.0), p_kw), (cap_kwh - soc) / eta) if allow[t] else np.zeros(n)
        dis = np.minimum(np.minimum(np.maximum(-s, 0.0), p_kw), soc * eta)
        soc = soc + ch * eta - dis / eta
        out[:, t] = ch - dis
    return out


def mv_voltage(spec: grids.PostSpec, pvk: np.ndarray, sysload: np.ndarray, seed: int) -> np.ndarray:
    """Tensiunea pe MT la post: nivelul de bază, urcă la soare (PV pe MT), scade la consum mare, plus zgomot AR(1)."""
    rng = np.random.default_rng(seed)
    e = rng.normal(0.0, 0.0012, len(pvk))
    ar = np.empty_like(e)
    acc = 0.0
    for i, x in enumerate(e):
        acc = 0.9 * acc + x
        ar[i] = acc
    return spec.vm_mv + spec.mv_pv_coef * (pvk / 0.85) - spec.mv_load_coef * sysload + ar


def simulate_post(
    post: grids.Post,
    wx: pd.DataFrame,
    shapes: pd.DataFrame,
    sysload: np.ndarray,
    *,
    extra_load: np.ndarray | None = None,
    bat_kwh: np.ndarray | None = None,
    bat_kw: np.ndarray | None = None,
    bat_allow_charge: np.ndarray | None = None,
    export_cap_kw: np.ndarray | None = None,
    vm: np.ndarray | None = None,
    detail: bool = False,
):
    """Simularea orară a unui post. Întoarce un tabel orar (index UTC) cu coloanele din HOURLY_COLS.

    Parametrii opționali servesc scara de soluții (efectul fiecărei trepte, calculat, nu ghicit):
    extra_load (n_consumatori, T) kW adăugați consumului (mesaje „consumă la prânz”), bat_kwh / bat_kw pe panou
    (baterii noi), bat_allow_charge (T,) orele în care bateriile se încarcă, export_cap_kw pe panou (limită de
    export), vm tensiunea pe MT (aceeași pentru toate variantele comparate). Cu detail=True întoarce și opririle
    invertoarelor și energia tăiată, pe oră.
    """
    m = post.model
    T = len(wx)
    pvk = weather.pv_per_kwp(wx["gti"].to_numpy(), wx["temp"].to_numpy())
    pv = np.minimum(post.pv_kwp[:, None] * post.pv_orient[:, None] * pvk[None, :], post.pv_ac_kw[:, None])
    load = post.load_annual_kwh[:, None] * shapes[list(post.load_profile)].to_numpy().T  # kW (kWh pe oră)
    if extra_load is not None:
        load = np.maximum(load + extra_load, 0.0)
    bkwh = post.bat_kwh if bat_kwh is None else np.asarray(bat_kwh, dtype=float)
    bkw = post.bat_kw if bat_kw is None else np.asarray(bat_kw, dtype=float)
    bat = np.zeros_like(pv)
    has = bkwh > 0
    if has.any():
        bat[has] = battery_dispatch(pv[has] - load[post.pv_load[has]], bkwh[has], bkw[has], allow_charge=bat_allow_charge)
    curtailed = np.zeros_like(pv)
    if export_cap_kw is not None and len(pv):
        net = pv - bat - load[post.pv_load]
        curtailed = np.clip(net - np.asarray(export_cap_kw, dtype=float)[:, None], 0.0, pv)
        pv = pv - curtailed
    A_pv = m.incidence(post.pv_bus)
    A_ld = m.incidence(post.load_bus)
    s_load = A_ld @ ((load / 1000) * (1 + 1j * post.load_tanphi[:, None]))
    inj_pv = pv - bat
    S = A_pv @ (inj_pv / 1000) - s_load
    if vm is None:
        vm = mv_voltage(post.spec, pvk, sysload, post.spec.seed + 1)
    V, _ = m.solve(S, vm)
    Vlv = np.abs(V[m.lv_pos])
    vmax = Vlv.max(axis=0)
    vmin = Vlv.min(axis=0)
    n_over = (Vlv > LIMIT_PU).sum(axis=0)

    # cascada de opriri ale invertoarelor în orele cu depășiri
    lost = np.zeros(T)
    trips = np.zeros(T)
    if len(post.pv_bus):
        lv_index = {int(b): i for i, b in enumerate(m.lv_bus)}
        pv_lv = np.array([lv_index[int(b)] for b in post.pv_bus])
        hours = np.flatnonzero(Vlv[pv_lv].max(axis=0) > LIMIT_PU)
        if len(hours):
            tripped = np.zeros((len(pv_lv), len(hours)), dtype=bool)
            Vh = Vlv[:, hours]
            for _ in range(10):
                new = (Vh[pv_lv] > LIMIT_PU) & ~tripped & (pv[:, hours] > 0)
                if not new.any():
                    break
                # se oprește cel mai expus invertor de pe fiecare oră, apoi se recalculează
                vv = np.where(new, Vh[pv_lv], -np.inf)
                worst = np.argmax(vv, axis=0)
                cols = np.flatnonzero(new.any(axis=0))
                tripped[worst[cols], cols] = True
                inj = np.where(tripped, 0.0, inj_pv[:, hours])
                Sh = A_pv @ (inj / 1000) - s_load[:, hours]
                Vc, _ = m.solve(Sh, vm[hours])
                Vh = np.abs(Vc[m.lv_pos])
            lost[hours] = (pv[:, hours] * tripped).sum(axis=0)
            trips[hours] = tripped.sum(axis=0)

    s_slack = m.slack_power_mva(V, vm)
    out = pd.DataFrame(
        {
            "vmax": vmax,
            "vmin": vmin,
            "n_over": n_over,
            "lost_kwh": lost,
            "pv_kw": pv.sum(axis=0),
            "load_kw": load.sum(axis=0),
            "export_kw": -s_slack.real * 1000,
            "loading": np.abs(s_slack) / m.trafo_sn_mva,
        },
        index=wx.index,
    )
    out = out.astype("float32")
    if detail:
        return {"hourly": out, "trips": trips, "curtailed_kwh": curtailed.sum(axis=0), "vlv": Vlv, "vm": vm, "pv": pv, "load": load}
    return out


def daily(h: pd.DataFrame) -> pd.DataFrame:
    """Agregarea pe zi locală: tensiunea maximă, ora ei, orele peste 1,10 și 1,05, kWh pierduți."""
    loc = h.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)  # începutul orei, ora locală
    g = h.groupby(loc.date)
    d = pd.DataFrame(
        {
            "vmax_day": g["vmax"].max(),
            "vmin_day": g["vmin"].min(),
            "hours_over_110": g["vmax"].apply(lambda s: int((s > LIMIT_PU).sum())),
            "hours_over_105": g["vmax"].apply(lambda s: int((s > 1.05).sum())),
            "lost_kwh_day": g["lost_kwh"].sum(),
            "pv_kwh_day": g["pv_kw"].sum(),
            "load_kwh_day": g["load_kw"].sum(),
            "max_loading": g["loading"].max(),
        }
    )
    d["hour_vmax"] = g["vmax"].apply(lambda s: int(loc[h.index.get_indexer([s.idxmax()])[0]].hour))
    d.index.name = "date"
    return d


# ---------------------------------------------------------------------------------------------------------
# rularea pe un lot de posturi (cel mult 4 procese)
# ---------------------------------------------------------------------------------------------------------

_W: dict = {}


def _init_worker(wx: pd.DataFrame, shapes: pd.DataFrame, sysload: np.ndarray, out_dir: str) -> None:
    _W.update(wx=wx, shapes=shapes, sysload=sysload, out_dir=out_dir)


def _run_one(spec_dict: dict) -> dict:
    spec = grids.PostSpec(**spec_dict)
    t0 = time.perf_counter()
    post = grids.build_realistic(spec)
    h = simulate_post(post, _W["wx"], _W["shapes"], _W["sysload"])
    h.to_parquet(os.path.join(_W["out_dir"], "hourly", f"{spec.post_id}.parquet"))
    d = daily(h)
    d.insert(0, "post_id", spec.post_id)
    return {"spec": spec.to_dict(), "features": post.features, "daily": d, "seconds": time.perf_counter() - t0}


def weather_inputs(start: str = "2023-01-01", end: str = "2026-11-06") -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    wx = weather.archive(start, end)
    return wx, profiles.shapes_for(wx.index), profiles.system_load_index(wx.index)


def train_specs(n_per_topology: int, seed: int = 20261107) -> list[grids.PostSpec]:
    rng = np.random.default_rng(seed)
    return [grids.sample_spec(t, rng, f"S-{t}-{i:03d}", mode="train") for t in grids.TOPOLOGIES for i in range(n_per_topology)]


def run_pool(name: str, specs: list[grids.PostSpec], workers: int = 4) -> pd.DataFrame:
    out_dir = OUT / name
    (out_dir / "hourly").mkdir(parents=True, exist_ok=True)
    wx, shapes, sysload = weather_inputs()
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[k] = "1"
    t0 = time.perf_counter()
    results = []
    with ProcessPoolExecutor(
        max_workers=min(workers, 4), mp_context=get_context("spawn"), initializer=_init_worker, initargs=(wx, shapes, sysload, str(out_dir))
    ) as ex:
        for i, r in enumerate(ex.map(_run_one, [s.to_dict() for s in specs], chunksize=2), 1):
            results.append(r)
            if i % 20 == 0:
                print(f"  {i}/{len(specs)} posturi, {time.perf_counter() - t0:.0f} s", flush=True)
    # spec_* = parametrii exacți ai simulării (după limitele de realism), ca rețeaua să se poată reconstrui identic
    posts = pd.DataFrame([{**r["spec"], **r["features"], **{f"spec_{k}": v for k, v in r["spec"].items()}, "sim_seconds": r["seconds"]}
                          for r in results])
    posts.to_parquet(out_dir / "posts.parquet")
    pd.concat([r["daily"] for r in results]).reset_index().to_parquet(out_dir / "daily.parquet")
    meta = {"posts": len(specs), "hours": len(wx), "start": str(wx.index[0]), "end": str(wx.index[-1]), "seconds": time.perf_counter() - t0}
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"gata: {len(specs)} posturi în {meta['seconds']:.0f} s -> {out_dir}")
    return posts


def one() -> None:
    """M0: un post sintetic pe topologia rural3, simulat orar pe 2025, cu timpii."""
    t0 = time.perf_counter()
    wx, shapes, sysload = weather_inputs()
    sel = (wx.index >= "2025-01-01") & (wx.index < "2026-01-01")
    wx, shapes, sysload = wx[sel], shapes[sel], sysload[sel]
    t1 = time.perf_counter()
    rng = np.random.default_rng(7)
    spec = grids.sample_spec("rural3", rng, "M0-rural3", mode="train")
    spec.prosumer_share, spec.line_type = 0.45, "TYIR_50"
    post = grids.build_post(spec)
    t2 = time.perf_counter()
    h = simulate_post(post, wx, shapes, sysload)
    t3 = time.perf_counter()
    d = daily(h)
    print({k: v for k, v in spec.to_dict().items() if k not in ("seed",)})
    print(f"post {spec.post_id}: {post.features['n_prosumers']} prosumatori, {post.features['pv_kw']:.0f} kWp pe {spec.kva} kVA, conductor {spec.line_type}")
    print(f"timp: meteo+profile {t1 - t0:.1f} s, rețea {t2 - t1:.1f} s, simulare {len(h)} ore {t3 - t2:.2f} s")
    print(f"tensiune maximă în an: {h.vmax.max():.4f} pu; zile cu depășire 1,10: {(d.vmax_day > LIMIT_PU).sum()}; ore: {(h.vmax > LIMIT_PU).sum()}")
    print(f"kWh PV pierduți în an: {h.lost_kwh.sum():.0f} din {h.pv_kw.sum():.0f} ({h.lost_kwh.sum() / max(h.pv_kw.sum(), 1) * 100:.1f}%)")
    print(d.groupby(pd.to_datetime(d.index).month)[["vmax_day", "hours_over_110", "lost_kwh_day"]].agg({"vmax_day": "max", "hours_over_110": "sum", "lost_kwh_day": "sum"}).round(3).T)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["one", "pool"])
    ap.add_argument("pool", nargs="?", default="train")
    ap.add_argument("--n", type=int, default=80, help="posturi pe topologie (lotul train)")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    if a.cmd == "one":
        one()
    elif a.pool == "train":
        run_pool("train", train_specs(a.n), a.workers)
