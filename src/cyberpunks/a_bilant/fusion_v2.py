"""Fuziunea v2: reglaj automat (Optuna) al regulii de fuziune și o fuziune învățată, judecate pe testul hărții.

Antrenarea și reglajul: contoarele lotului `trainL` (~3.000 de posturi), cu scoruri de tip A simulate (AUC 0,907, ca
în `fusion_eval.simulate_a_scores`), validare pe 20% din cartiere. Testul: cele 300 de posturi ale hărții, cu
defectele reale ale lui A: (a) mai multe zile, scoruri A simulate; (b) ziua demo, scorurile REALE ale lui A.
Varianta v1 (regula din `fuse.py`) rămâne rezervă; v2 se păstrează doar dacă bate v1 pe același test.

    uv run python -m cyberpunks.a_bilant.fusion_v2 --trials 60
"""

from __future__ import annotations

import argparse
import json
import time

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from cyberpunks.a_bilant import fusion_eval as FE
from cyberpunks.common.paths import DATA_PROCESSED, REPORTS

BASE = DATA_PROCESSED / "bilant"
OUT = REPORTS / "bilant"
KS = (10, 20, 50, 100)
TOP_SHARE = 0.05  # din fiecare zi păstrăm contoarele din primele 5% după scorul A (doar ele pot ajunge în primele K)
LEARN_FEATS = ["la", "drop", "drop_share", "zero", "excess", "z", "dz", "match", "n_drop_post", "drop_rank", "share_of_post_drops", "p_contor_client", "p_normal"]


def meter_rows(pool: str, win: pd.DataFrame, sigma_scale: float, days: list[int], truth_fn) -> pd.DataFrame:
    """Contor × zi: scăderea vizibilă, adevărul, creșterea lipsei la post, plus contextul postului."""
    cust = np.load(BASE / pool / "cust_daily.npz")
    w = win.set_index(["post_id", "day"])
    rows = []
    for pid in cust.files:
        cd = cust[pid].astype(float)
        n = cd.shape[0]
        for e in days:
            if (pid, e) not in w.index:
                continue
            r = w.loc[(pid, e)]
            before = cd[:, e - 34 : e - 13].mean(1)
            after = cd[:, e - 6 : e + 1].mean(1)
            drop = before - after
            truth, keep = truth_fn(pid, e, n)
            pos = np.clip(drop, 0, None)
            df = pd.DataFrame(
                {
                    "post_id": pid,
                    "day": e,
                    "customer": np.arange(n),
                    "before": before,
                    "drop": drop,
                    "zero": ((after == 0) & (before > 0.5)).astype(float),
                    "truth": truth,
                    "excess": float(r["delta_kwh"]),
                    "sigma": float(r["width_kwh"]) / 2.56 * sigma_scale,
                    "n_drop_post": float(((drop / np.maximum(np.abs(before), 0.5)) > 0.5).sum()),
                    "drop_rank": (-drop).argsort().argsort().astype(float),
                    "share_of_post_drops": pos / max(pos.sum(), 1e-6),
                    "p_contor_client": float(r.get("p_contor_client", np.nan)),
                    "p_normal": float(r.get("p_normal", np.nan)),
                }
            )
            rows.append(df[keep])
    return pd.concat(rows, ignore_index=True)


def add_feats(t: pd.DataFrame, a: np.ndarray) -> pd.DataFrame:
    t = t.copy()
    t["a"] = a
    ac = np.clip(a, 1e-4, 1 - 1e-4)
    t["la"] = np.log(ac / (1 - ac))
    t["drop_share"] = np.clip(t["drop"] / np.maximum(np.abs(t["before"]), 0.5), -0.5, 1.5)
    t["z"] = t["excess"] / t["sigma"].clip(lower=0.1)
    t["dz"] = t["drop"] / t["sigma"].clip(lower=0.1)
    dpos = t["drop"].clip(lower=0)
    t["match"] = 1 - (dpos - t["excess"]).abs() / np.maximum(np.maximum(dpos, t["excess"].abs()), 1.0)
    return t


def fused_param(t: pd.DataFrame, p: dict) -> np.ndarray:
    """Regula din `fuse.combine_arrays`, cu parametri: σ ×k, incertitudinea lipsei u·d, plafonul log LR, coborâre."""
    d = np.maximum(t["drop"].to_numpy(), 0.0)
    s = np.sqrt(np.maximum(t["sigma"].to_numpy() * p["k_sigma"], 0.1) ** 2 + (p["u_def"] * d) ** 2)
    e = t["excess"].to_numpy()
    llr = (-((e - d) ** 2) + e**2) / (2 * s**2)
    llr = np.clip(llr, -p["cap"] if p["demote"] else 0.0, p["cap"])
    return 1 / (1 + np.exp(-(t["la"].to_numpy() + llr)))


V1_PARAMS = {"k_sigma": 1.0, "u_def": 0.5, "cap": 3.0, "demote": False}


def topk(t: pd.DataFrame, col: str, price: float) -> dict:
    out = {}
    for K in KS:
        prec, wasted, val = [], [], []
        for _, g in t.groupby("day"):
            top = g.nlargest(K, col)
            prec.append(top["truth"].mean())
            wasted.append(K - top["truth"].sum())
            val.append((top["truth"] * top["drop"].clip(lower=0)).sum() * price * 90)
        out[f"precision_at_{K}"] = float(np.mean(prec))
        out[f"wasted_trips_per_day_at_{K}"] = float(np.mean(wasted))
        out[f"value_lei_per_day_at_{K}"] = float(np.mean(val))
    return out


def objective_value(t: pd.DataFrame, col: str) -> float:
    """Ținta reglajului: precizia medie în primele 10, 20 și 50 de contoare pe zi."""
    return float(np.mean([np.mean([g.nlargest(K, col)["truth"].mean() for _, g in t.groupby("day")]) for K in (10, 20, 50)]))


def main() -> None:
    import optuna

    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=60)
    ap.add_argument("--train-pool", default="trainLA", choices=["trainL", "trainLA"])
    a = ap.parse_args()
    pool = a.train_pool
    t0 = time.perf_counter()
    from cyberpunks.a_bilant.normal import MODEL_DIR
    from cyberpunks.common.config import load as load_config

    price = float(load_config("economics")["energy"]["loss_cost_lei_per_kwh"])
    sig = json.loads((MODEL_DIR / "fusion_sigma.json").read_text())["delta"]

    # --- antrenare și validare: trainL, scoruri A simulate
    from cyberpunks.a_bilant import diagnose as G
    from cyberpunks.a_bilant import features as F
    from cyberpunks.a_bilant import normal as N
    from cyberpunks.a_bilant import windows as W

    wpath = BASE / f"windows_{pool}.parquet"
    if not wpath.exists():
        models = {"warm": N.load("normal"), "cold": N.load("normal_cold")}
        dl = F.load_pool(pool)
        W.build_windows_parallel(dl, W.predict_normal(models, dl), pool, workers=8).to_parquet(wpath)
    wl = pd.read_parquet(wpath)
    diag = G.load("diagnose")
    wl = wl.join(diag.proba(wl).add_prefix("p_"))
    plans = json.loads((BASE / pool / "plans.json").read_text())
    probs = {pid: [(p["customer"] % 10**6, p["onset_day"]) for p in pl["problems"] if p["kind"] in ("meter_fault", "meter_tamper")] for pid, pl in plans.items()}

    def truth_train(pid: str, e: int, n: int) -> tuple[np.ndarray, np.ndarray]:
        truth = np.zeros(n, bool)
        old = np.zeros(n, bool)
        for c, on in probs[pid]:
            c %= n
            if e - 12 <= on <= e - 2:
                truth[c] = True
            elif on < e - 12:
                old[c] = True
        return truth, ~old

    Dl = int(wl["day"].max())
    # trainLA: aceleași zile ca testul (ultimele 50); trainL: o zi din trei, pe tot anul
    days = sorted(d for d in wl["day"].unique() if d >= Dl - 50) if pool == "trainLA" else sorted(wl["day"].unique())[2::3]
    tl = meter_rows(pool, wl, sig, days, truth_train)
    a_sim, _, auc = FE.simulate_a_scores(tl)
    tl = add_feats(tl, a_sim)
    tl = tl[tl.groupby("day")["a"].rank(ascending=False, pct=True) <= TOP_SHARE].reset_index(drop=True)
    posts = pd.read_parquet(BASE / pool / "posts.parquet")[["post_id", "cluster"]]
    cl = sorted(posts["cluster"].unique())
    val_cl = set(np.random.default_rng(1).choice(cl, size=len(cl) // 5, replace=False))
    is_val = tl["post_id"].isin(set(posts.loc[posts["cluster"].isin(val_cl), "post_id"])).to_numpy()
    tr, va = tl[~is_val], tl[is_val]
    print(f"contoare {pool}: {len(tl)} (antrenare {len(tr)}, validare {len(va)}), AUC scor simulat {auc:.3f}, {time.perf_counter() - t0:.0f} s", flush=True)

    # (1) regula cu parametri căutați
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def obj(trial: optuna.Trial) -> float:
        p = {
            "k_sigma": trial.suggest_float("k_sigma", 0.2, 4.0, log=True),
            "u_def": trial.suggest_float("u_def", 0.05, 1.5, log=True),
            "cap": trial.suggest_float("cap", 0.5, 6.0),
            "demote": trial.suggest_categorical("demote", [False, True]),
        }
        return objective_value(va.assign(f=fused_param(va, p)), "f")

    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=0))
    st.enqueue_trial(V1_PARAMS)
    st.optimize(obj, n_trials=a.trials)
    best_rule = dict(st.best_params)

    # (2) fuziunea învățată (LightGBM), oprire timpurie pe validare
    clf = lgb.LGBMClassifier(n_estimators=600, learning_rate=0.03, num_leaves=15, min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8)
    clf.fit(tr[LEARN_FEATS], tr["truth"], eval_set=[(va[LEARN_FEATS], va["truth"])], callbacks=[lgb.early_stopping(50, verbose=False)])
    val = {
        "A_singur": objective_value(va, "a"),
        "regula_v1": objective_value(va.assign(f=fused_param(va, V1_PARAMS)), "f"),
        "regula_reglata": objective_value(va.assign(f=fused_param(va, best_rule)), "f"),
        "invatata": objective_value(va.assign(f=clf.predict_proba(va[LEARN_FEATS])[:, 1]), "f"),
    }
    print("validare", val, flush=True)

    # --- test (a): harta, mai multe zile, scoruri A simulate; adevărul = defectele lui A apărute în ultimele 2-12 zile
    wte = pd.read_parquet(BASE / "windows_pop_v2.parquet") if (BASE / "windows_pop_v2.parquet").exists() else pd.read_parquet(BASE / "windows_pop.parquet")
    wte = wte.join(diag.proba(wte).add_prefix("p_"))
    pplans = json.loads((BASE / "pop" / "plans.json").read_text())
    pprobs = {pid: [(p["customer"], p["onset_day"]) for p in pl["problems"] if p["kind"] in ("meter_fault", "meter_tamper")] for pid, pl in pplans.items()}

    def truth_pop(pid: str, e: int, n: int) -> tuple[np.ndarray, np.ndarray]:
        truth = np.zeros(n, bool)
        old = np.zeros(n, bool)
        for c, on in pprobs.get(pid, []):
            c %= n
            if e - 12 <= on <= e - 2:
                truth[c] = True
            elif on < e - 12:
                old[c] = True
        return truth, ~old

    D = int(wte["day"].max())
    pdays = sorted(d for d in wte["day"].unique() if d >= D - 50)
    tp = meter_rows("pop", wte, sig, pdays, truth_pop)
    a_p, _, auc_p = FE.simulate_a_scores(tp)
    tp = add_feats(tp, a_p)
    variants = {"A_singur": tp["a"].to_numpy(), "regula_v1": fused_param(tp, V1_PARAMS), "regula_reglata": fused_param(tp, best_rule), "invatata": clf.predict_proba(tp[LEARN_FEATS])[:, 1]}
    test_sim = {k: {**topk(tp.assign(s=v), "s", price), "roc_auc": float(roc_auc_score(tp["truth"], v))} for k, v in variants.items()}

    # --- test (b): ziua demo, scorurile REALE ale lui A
    real = pd.read_parquet(BASE / "fusion_real_a_demo.parquet")
    # tabelul real nu are consumul de dinainte: aproximăm `before` ca |scădere| + 0,5 (doar pentru drop_share)
    rr = add_feats(real.assign(before=real["drop"].abs() + 0.5, zero=0.0), real["a"].to_numpy())
    wd = wte[wte["day"] == D].set_index("post_id")
    for c in ("p_contor_client", "p_normal"):
        rr[c] = rr["post_id"].map(wd[c])
    rr["n_drop_post"] = rr.groupby("post_id")["drop"].transform(lambda s: float((s > 2).sum()))
    rr["drop_rank"] = rr.groupby("post_id")["drop"].rank(ascending=False) - 1
    rr["share_of_post_drops"] = rr["drop"].clip(lower=0) / rr.groupby("post_id")["drop"].transform(lambda s: max(s.clip(lower=0).sum(), 1e-6))
    vr = {"A_singur": rr["a"].to_numpy(), "regula_v1": fused_param(rr, V1_PARAMS), "regula_reglata": fused_param(rr, best_rule), "invatata": clf.predict_proba(rr[LEARN_FEATS])[:, 1]}
    test_real = {}
    for k, v in vr.items():
        x = rr.assign(s=v)
        test_real[k] = {"roc_auc": float(roc_auc_score(x["truth"], x["s"])), **{f"precision_at_{K}": float(x.nlargest(K, "s")["truth"].mean()) for K in (10, 100, 300, 500, 865)}}
    out = {"train_pool": pool, "validation_objective": val, "best_rule_params": best_rule, "test_sim_multi_day": test_sim, "test_real_a_demo": test_real, "a_sim_auc_train": auc, "a_sim_auc_test": auc_p, "test_days": len(pdays), "seconds": round(time.perf_counter() - t0, 1)}
    (OUT / f"fusion_v2_comparison_{pool}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    # regula reglată se păstrează doar dacă bate v1 pe testul simulat al hărții și nu e mai slabă pe scorurile reale
    better = test_sim["regula_reglata"]["precision_at_10"] > test_sim["regula_v1"]["precision_at_10"] and test_real["regula_reglata"]["roc_auc"] >= test_real["regula_v1"]["roc_auc"]
    if better and pool == "trainLA":
        (OUT / "fusion_v2_params.json").write_text(json.dumps({
            "version": "fuziune-v2", "params": best_rule,
            "source": f"fusion_v2.py --train-pool {pool} (Optuna, {a.trials} încercări, validare pe 20% din cartiere)",
            "test_pop_sim_precision_at_10": {k: test_sim[k]["precision_at_10"] for k in ("A_singur", "regula_v1", "regula_reglata")},
            "test_real_a_auc": {k: test_real[k]["roc_auc"] for k in ("A_singur", "regula_v1", "regula_reglata")},
        }, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()


def test_on_map(wte: pd.DataFrame, sig: float, price: float, rules: dict[str, dict]) -> tuple[dict, dict]:
    """Testul hărții pentru regulile date (nume → parametri): (a) mai multe zile, scoruri A simulate; (b) ziua demo,
    scorurile reale ale lui A. Varianta `A_singur` e mereu inclusă."""
    pplans = json.loads((BASE / "pop" / "plans.json").read_text())
    pprobs = {pid: [(p["customer"], p["onset_day"]) for p in pl["problems"] if p["kind"] in ("meter_fault", "meter_tamper")] for pid, pl in pplans.items()}

    def truth_pop(pid: str, e: int, n: int) -> tuple[np.ndarray, np.ndarray]:
        truth = np.zeros(n, bool)
        old = np.zeros(n, bool)
        for c, on in pprobs.get(pid, []):
            c %= n
            if e - 12 <= on <= e - 2:
                truth[c] = True
            elif on < e - 12:
                old[c] = True
        return truth, ~old

    D = int(wte["day"].max())
    pdays = sorted(d for d in wte["day"].unique() if d >= D - 50)
    tp = meter_rows("pop", wte, sig, pdays, truth_pop)
    a_p, _, _ = FE.simulate_a_scores(tp)
    tp = add_feats(tp, a_p)
    sim = {"A_singur": {**topk(tp.assign(s=tp["a"]), "s", price), "roc_auc": float(roc_auc_score(tp["truth"], tp["a"]))}}
    for name, prm in rules.items():
        v = fused_param(tp, prm)
        sim[name] = {**topk(tp.assign(s=v), "s", price), "roc_auc": float(roc_auc_score(tp["truth"], v))}
    real = pd.read_parquet(BASE / "fusion_real_a_demo.parquet")
    rr = add_feats(real.assign(before=real["drop"].abs() + 0.5, zero=0.0), real["a"].to_numpy())
    res_real = {}
    for name, v in {"A_singur": rr["a"].to_numpy(), **{n: fused_param(rr, p) for n, p in rules.items()}}.items():
        x = rr.assign(s=v)
        res_real[name] = {"roc_auc": float(roc_auc_score(x["truth"], x["s"])), **{f"precision_at_{K}": float(x.nlargest(K, "s")["truth"].mean()) for K in (10, 100, 300, 500)}}
    return sim, res_real
