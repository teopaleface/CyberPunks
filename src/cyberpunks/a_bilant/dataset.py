"""Setul de date simulat al bilanțului: două loturi de posturi, cu probleme ascunse (SINTETIC).

- `train`: 300 de posturi sintetice noi (variante SimBench, 50 pe topologie, parametri realiști), grupate câte 5 în
  „cartiere” (vecinii pentru clientul trecut la postul greșit);
- `pop`: cele 300 de posturi din registrul comun al firului C (harta din București-Ilfov), cu vecinii după distanță.
  Rețelele lor nu se văd la antrenare: testul e pe rețele nevăzute.

Pentru fiecare post și fiecare zi (2024-07-01 … 2025-07-08): energia ieșită din post (contorul de bilanț), suma
contoarelor clienților din bază, golurile de date, semnalele contoarelor (zero, blocat, negativ noaptea), tensiunile
și adevărul din construcție (pierderea tehnică, furtul, consumul nemăsurat, clasa problemei).

    uv run python -m cyberpunks.a_bilant.dataset            # ambele loturi, cel mult 4 procese
    uv run python -m cyberpunks.a_bilant.dataset --pool pop
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

from cyberpunks.a_bilant import problems as P
from cyberpunks.a_bilant import registry, world
from cyberpunks.c_prosumatori import grids
from cyberpunks.common.paths import DATA_PROCESSED

OUT = DATA_PROCESSED / "bilant"
WINDOW = 14  # zile: fereastra diagnosticului
EVAL_EVERY = 7  # o fereastră de evaluare la 7 zile
SEEDS = {"train": 20261107, "pop": 8112026}
P_POST = {"train": 0.40, "pop": 0.25}  # ce parte din posturi au o problemă la nivel de post (IPOTEZĂ)


# ------------------------------------------------------------------------------------------------------------
# specificațiile loturilor
# ------------------------------------------------------------------------------------------------------------


def train_specs(n_per_topology: int = 50) -> tuple[list[grids.PostSpec], pd.DataFrame]:
    rng = np.random.default_rng(SEEDS["train"])
    specs, meta = [], []
    k = 0
    for topo in grids.TOPOLOGIES:
        for i in range(n_per_topology):
            pid = f"BT-{topo}-{i:03d}"
            specs.append(grids.sample_spec(topo, rng, pid, mode="population"))
            meta.append({"post_id": pid, "cluster": f"K{k // 5:03d}", "lat": np.nan, "lon": np.nan})
            k += 1
    # cartierele amestecă topologiile (vecinii nu au aceeași rețea)
    meta = pd.DataFrame(meta)
    perm = np.random.default_rng(SEEDS["train"] + 1).permutation(len(meta))
    meta["cluster"] = meta["cluster"].to_numpy()[perm]
    return specs, meta


def pop_specs() -> tuple[list[grids.PostSpec], pd.DataFrame]:
    reg = registry.load_posts()
    specs = [registry.spec_from_row(r) for _, r in reg.iterrows()]
    meta = reg[["post_id", "lat", "lon", "zone_id"]].copy()
    meta["cluster"] = meta["zone_id"]
    return specs, meta


def neighbors(meta: pd.DataFrame, k: int = 3) -> dict[str, list[str]]:
    """Vecinii fiecărui post: din același cartier (train) sau cei mai apropiați k (pop, după distanță)."""
    out: dict[str, list[str]] = {}
    if meta["lat"].notna().all():
        lat = np.radians(meta["lat"].to_numpy())
        lon = np.radians(meta["lon"].to_numpy())
        x = np.cos(lat) * np.cos(lon)
        y = np.cos(lat) * np.sin(lon)
        z = np.sin(lat)
        xyz = np.stack([x, y, z], 1)
        d = np.linalg.norm(xyz[:, None] - xyz[None], axis=2)
        np.fill_diagonal(d, np.inf)
        ids = meta["post_id"].to_numpy()
        for i, pid in enumerate(ids):
            out[pid] = list(ids[np.argsort(d[i])[:k]])
    else:
        for _, g in meta.groupby("cluster"):
            ids = list(g["post_id"])
            for pid in ids:
                out[pid] = [q for q in ids if q != pid]
    return out


def n_customers(spec: grids.PostSpec) -> int:
    return len(grids.base_net(spec.topology).load)


def plans_for(pool: str, specs: list[grids.PostSpec], meta: pd.DataFrame, n_days: int) -> dict[str, P.PostPlan]:
    rng = np.random.default_rng(SEEDS[pool] + 99)
    plans = {s.post_id: P.make_plan(s.post_id, n_customers(s), n_days, rng, p_post_problem=P_POST[pool]) for s in specs}
    # clientul la postul greșit: receptorul e un vecin fără altă problemă de post
    nb = neighbors(meta)
    taken = set()
    for pid, plan in plans.items():
        for pr in plan.problems:
            if pr.kind == "wrong_post_donor":
                cands = [q for q in nb[pid] if q not in taken and not any(x.kind != "meter_fault" and x.kind != "meter_tamper" for x in plans[q].problems)]
                if not cands:
                    plan.problems.remove(pr)
                    continue
                recv = cands[0]
                taken.add(recv)
                pr.params["receiver"] = recv
                plans[recv].problems.append(P.Problem("wrong_post_receiver", pr.onset_day, -1, {"donor": pid, "customer": pr.customer}))
    return plans


# ------------------------------------------------------------------------------------------------------------
# un post (rulat în procese separate)
# ------------------------------------------------------------------------------------------------------------

_W: dict = {}


def _init(wx: world.Weather, cluster_mv: dict[str, np.ndarray]) -> None:
    _W["wx"] = wx
    _W["cluster_mv"] = cluster_mv


def impute(rec: np.ndarray) -> np.ndarray:
    """Golurile unui contor: valoarea de acum 7 zile, apoi media orei din zi a aceluiași contor."""
    x = rec.astype("float64").copy()
    for _ in range(4):
        miss = np.isnan(x)
        if not miss.any():
            break
        shifted = np.full_like(x, np.nan)
        shifted[:, 168:] = x[:, :-168]
        x[miss] = shifted[miss]
    miss = np.isnan(x)
    if miss.any():
        T = x.shape[1]
        hod = np.arange(T) % 24
        for h in range(24):
            cols = hod == h
            m = np.nanmean(np.where(np.isnan(x[:, cols]), np.nan, x[:, cols]), axis=1)
            sub = x[:, cols]
            r, c = np.nonzero(np.isnan(sub))
            sub[r, c] = np.nan_to_num(m[r])
            x[:, cols] = sub
    return x


def _vcorr(volt: np.ndarray, vmed: np.ndarray, hours: np.ndarray) -> np.ndarray:
    """Corelația variațiilor orare de tensiune ale fiecărui contor cu mediana postului, pe orele date."""
    a = np.diff(volt[:, hours].astype("float64"), axis=1)
    b = np.diff(vmed[hours].astype("float64"))
    a = a - a.mean(1, keepdims=True)
    b = b - b.mean()
    den = np.sqrt((a**2).sum(1) * (b**2).sum()) + 1e-12
    return (a @ b) / den


def run_post(args: tuple[dict, dict, str]) -> dict:
    spec_d, plan_d, cluster = args
    wx: world.Weather = _W["wx"]
    spec = grids.PostSpec(**spec_d)
    plan = P.PostPlan(
        post_id=plan_d["post_id"],
        phase_shares=tuple(plan_d["phase_shares"]),
        problems=[P.Problem(**p) for p in plan_d["problems"]],
        benign=[tuple(b) for b in plan_d["benign"]],
    )
    t0 = time.perf_counter()
    w = world.simulate(spec, wx, plan, cluster_mv=_W["cluster_mv"].get(cluster))
    n, T, D = w.n_customers, wx.T, wx.D
    day = wx.local_day

    # clientul mutat în bază la alt post: iese din baza acestui post de la ziua mutării
    in_db = np.ones((n, T), dtype=bool)
    moved = None
    for pr in plan.problems:
        if pr.kind == "wrong_post_donor":
            c = pr.customer % n
            on = day >= pr.onset_day
            in_db[c, on] = False
            moved = {"customer": c, "onset": pr.onset_day, "receiver": pr.params["receiver"]}
    rec = w.cust_kwh
    missing = np.isnan(rec)
    imp = impute(rec)
    db = np.where(in_db, imp, 0.0).sum(0)
    nmiss = (missing & in_db).sum(0)
    keep = np.ones(n, dtype=bool)
    if moved:
        keep[moved["customer"]] = False
        moved["rec"] = np.where(day >= moved["onset"], imp[moved["customer"]], 0.0).astype("float32")
        moved["volt"] = w.cust_voltage[moved["customer"]]
    vmed = np.median(w.cust_voltage[keep], axis=0)

    # semnalele contoarelor, pe zi: zi cu zero, zi blocată (24 de valori egale), consum negativ noaptea la neprosumatori
    cust_daily = np.zeros((n, D))
    zero_d = np.zeros((n, D), bool)
    stuck_d = np.zeros((n, D), bool)
    neg_d = np.zeros((n, D), bool)
    pros = np.zeros(n, bool)
    pros[w.static["prosumer_idx"]] = True
    starts = np.searchsorted(day, np.arange(D + 1))
    with np.errstate(invalid="ignore"), __import__("warnings").catch_warnings():
        __import__("warnings").simplefilter("ignore", RuntimeWarning)
        for d in range(D):
            x = rec[:, starts[d] : starts[d + 1]]
            cust_daily[:, d] = np.nansum(x, 1)
            mx = np.nanmax(np.abs(x), 1)
            zero_d[:, d] = mx == 0
            stuck_d[:, d] = (np.nanstd(x, 1) == 0) & (mx > 0)
            neg_d[:, d] = np.nanmin(x[:, :6], 1) < -0.01  # primele 6 ore ale zilei locale: noapte, fără soare
    db_member = in_db[:, starts[:-1]]
    zero_d &= db_member
    stuck_d &= db_member
    neg_d &= db_member & ~pros[:, None]

    # adevărul pe zi
    def dsum(x: np.ndarray) -> np.ndarray:
        return np.bincount(day, weights=x, minlength=D)

    lh = (wx.index.tz_convert(world.TZ) - pd.Timedelta(hours=1)).hour.to_numpy()
    night = lh < 6
    resid = w.balance_kwh - db
    daily = pd.DataFrame(
        {
            "post_id": spec.post_id,
            "day": np.arange(D),
            "date": wx.days,
            "bal_kwh": dsum(w.balance_kwh),
            "db_kwh": dsum(db),
            "imp_kwh": dsum(np.maximum(db, 0)),
            "exp_kwh": dsum(np.maximum(-db, 0)),
            "sq_kwh2": dsum(db**2),
            "abs_kwh": dsum(np.abs(db)),
            "night_short_kwh": dsum(np.where(night, resid, 0.0)),
            "night_db_kwh": dsum(np.where(night, db, 0.0)),
            "night_sq_kwh2": dsum(np.where(night, db**2, 0.0)),
            "miss_hours": dsum(nmiss.astype(float)),
            "n_db": dsum(in_db.sum(0).astype(float)) / np.maximum(np.bincount(day, minlength=D), 1),
            "temp_c": dsum(wx.temp) / np.maximum(np.bincount(day, minlength=D), 1),
            "gti_kwh_m2": dsum(wx.gti) / 1000,
            "cnt_zero": zero_d.sum(0),
            "cnt_stuck": stuck_d.sum(0),
            "cnt_neg_night": neg_d.sum(0),
            "true_line_base_kwh": dsum(w.true_line_loss_base_kwh),
            "true_line_kwh": dsum(w.true_line_loss_kwh),
            "true_own_kwh": w.true_own_kwh * np.bincount(day, minlength=D),
            "true_theft_kwh": dsum(w.true_theft_kwh),
            "true_meter_deficit_kwh": dsum(w.true_meter_deficit_kwh),
            "true_moved_out_kwh": dsum(moved["rec"]) if moved else 0.0,
            "true_moved_in_kwh": 0.0,
        }
    )
    # tensiunile: corelația minimă din fereastră, pe zilele de evaluare
    ev = eval_days(D)
    vrows = []
    for e in ev:
        hours = np.flatnonzero((day > e - WINDOW) & (day <= e))
        cc = _vcorr(w.cust_voltage[keep], vmed, hours)
        idx = np.flatnonzero(keep)
        j = int(np.argmin(cc))
        vrows.append({"post_id": spec.post_id, "day": e, "vcorr_min": float(cc[j]), "vcorr_min_customer": int(idx[j]), "vcorr_med": float(np.median(cc))})
    return {
        "post_id": spec.post_id,
        "static": {**w.static, "n_customers": n},
        "plan": plan_d,
        "benign": {int(k): v for k, v in w.benign.items()},
        "daily": daily,
        "vcorr": pd.DataFrame(vrows),
        "cust_daily": cust_daily.astype("float32"),
        "bal_h": w.balance_kwh.astype("float32"),
        "db_h": db.astype("float32"),
        "vmed": vmed.astype("float32"),
        "moved": moved,
        "seconds": time.perf_counter() - t0,
    }


def eval_days(D: int) -> list[int]:
    ev = list(range(P.MIN_ONSET_DAY + WINDOW, D, EVAL_EVERY))
    if ev[-1] != D - 1:
        ev.append(D - 1)
    return ev


def plan_to_dict(plan: P.PostPlan) -> dict:
    return {
        "post_id": plan.post_id,
        "phase_shares": list(plan.phase_shares),
        "problems": [{"kind": p.kind, "onset_day": p.onset_day, "customer": p.customer, "params": p.params} for p in plan.problems],
        "benign": [list(b) for b in plan.benign],
    }


def cluster_voltage(meta: pd.DataFrame, T: int, seed: int) -> dict[str, np.ndarray]:
    """Variația comună de tensiune pe MT a posturilor din același cartier (aceeași linie de medie tensiune)."""
    rng = np.random.default_rng(seed)
    out = {}
    for c in sorted(meta["cluster"].unique()):
        e = rng.normal(0.0, 0.0015, T)
        ar = np.empty(T)
        acc = 0.0
        for i, x in enumerate(e):
            acc = 0.95 * acc + x
            ar[i] = acc
        out[c] = ar
    return out


# ------------------------------------------------------------------------------------------------------------
# lotul
# ------------------------------------------------------------------------------------------------------------


def build(pool: str, workers: int = 4, limit: int | None = None) -> pd.DataFrame:
    wx = world.load_weather()
    specs, meta = train_specs() if pool == "train" else pop_specs()
    if limit:
        specs, meta = specs[:limit], meta.iloc[:limit]
    plans = plans_for(pool, specs, meta, wx.D)
    cmv = cluster_voltage(meta, wx.T, SEEDS[pool] + 5)
    cl = dict(zip(meta["post_id"], meta["cluster"], strict=True))
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[k] = "1"
    jobs = [(s.to_dict(), plan_to_dict(plans[s.post_id]), cl[s.post_id]) for s in specs]
    t0 = time.perf_counter()
    res: dict[str, dict] = {}
    with ProcessPoolExecutor(max_workers=min(workers, 4), mp_context=get_context("spawn"), initializer=_init, initargs=(wx, cmv)) as ex:
        for i, r in enumerate(ex.map(run_post, jobs, chunksize=2), 1):
            res[r["post_id"]] = r
            if i % 25 == 0:
                print(f"  {pool}: {i}/{len(jobs)} posturi, {time.perf_counter() - t0:.0f} s", flush=True)

    # receptorii clientului mutat: baza lor primește clientul de la ziua mutării
    ev = eval_days(wx.D)
    extra_v = []
    for r in res.values():
        mv = r["moved"]
        if not mv or mv["receiver"] not in res:
            continue
        q = res[mv["receiver"]]
        q["db_h"] = q["db_h"] + mv["rec"]
        d = q["daily"]
        add = np.bincount(wx.local_day, weights=mv["rec"].astype(float), minlength=wx.D)
        db_new = q["db_h"].astype(float)
        d["db_kwh"] = np.bincount(wx.local_day, weights=db_new, minlength=wx.D)
        d["imp_kwh"] = np.bincount(wx.local_day, weights=np.maximum(db_new, 0), minlength=wx.D)
        d["exp_kwh"] = np.bincount(wx.local_day, weights=np.maximum(-db_new, 0), minlength=wx.D)
        d["sq_kwh2"] = np.bincount(wx.local_day, weights=db_new**2, minlength=wx.D)
        d["abs_kwh"] = np.bincount(wx.local_day, weights=np.abs(db_new), minlength=wx.D)
        lh = (wx.index.tz_convert(world.TZ) - pd.Timedelta(hours=1)).hour.to_numpy() < 6
        resid = q["bal_h"].astype(float) - db_new
        d["night_short_kwh"] = np.bincount(wx.local_day, weights=np.where(lh, resid, 0.0), minlength=wx.D)
        d["night_db_kwh"] = np.bincount(wx.local_day, weights=np.where(lh, db_new, 0.0), minlength=wx.D)
        d["night_sq_kwh2"] = np.bincount(wx.local_day, weights=np.where(lh, db_new**2, 0.0), minlength=wx.D)
        d["true_moved_in_kwh"] = add
        for e in ev:
            if e < mv["onset"]:
                continue
            hours = np.flatnonzero((wx.local_day > e - WINDOW) & (wx.local_day <= e))
            c = float(_vcorr(mv["volt"][None, :], q["vmed"], hours)[0])
            extra_v.append({"post_id": mv["receiver"], "day": e, "moved_corr": c})

    daily = pd.concat([r["daily"] for r in res.values()], ignore_index=True)
    vc = pd.concat([r["vcorr"] for r in res.values()], ignore_index=True)
    if extra_v:
        ex_v = pd.DataFrame(extra_v)
        vc = vc.merge(ex_v, on=["post_id", "day"], how="left")
        better = vc["moved_corr"].notna() & (vc["moved_corr"] < vc["vcorr_min"])
        vc.loc[better, "vcorr_min"] = vc.loc[better, "moved_corr"]
        vc.loc[better, "vcorr_min_customer"] = -1  # clientul venit din altă parte
        vc = vc.drop(columns="moved_corr")
    posts = pd.DataFrame([{"post_id": k, **{a: b for a, b in r["static"].items() if not isinstance(b, list)}} for k, r in res.items()]).merge(meta, on="post_id", how="left")
    out = OUT / pool
    out.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(out / "daily.parquet")
    vc.to_parquet(out / "vcorr.parquet")
    posts.to_parquet(out / "posts.parquet")
    np.savez_compressed(out / "hourly.npz", **{f"bal__{k}": r["bal_h"] for k, r in res.items()}, **{f"db__{k}": r["db_h"] for k, r in res.items()})
    np.savez_compressed(out / "cust_daily.npz", **{k: r["cust_daily"] for k, r in res.items()})
    (out / "plans.json").write_text(json.dumps({k: {**r["plan"], "benign_applied": r["benign"]} for k, r in res.items()}, ensure_ascii=False))
    (out / "neighbors.json").write_text(json.dumps(neighbors(meta)))
    meta_out = {"pool": pool, "posts": len(res), "days": wx.D, "start": str(wx.days[0].date()), "end": str(wx.days[-1].date()), "seconds": round(time.perf_counter() - t0, 1), "synthetic": True}
    (out / "meta.json").write_text(json.dumps(meta_out, indent=2))
    print(f"gata {pool}: {len(res)} posturi în {meta_out['seconds']} s -> {out}")
    return daily


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", choices=["train", "pop", "all"], default="all")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    for pool in (["train", "pop"] if a.pool == "all" else [a.pool]):
        build(pool, a.workers, a.limit)


if __name__ == "__main__":
    main()
