"""Verificarea fuziunii cu bilanțul pe post (`cyberpunks.a_bilant.fuse`), pe testul firului A.

    uv run python -m cyberpunks.a_contoare.fusion_check        # scrie reports/A/fusion_check.json

Testul: populația demo (15.850 de contoare SINTETICE pe cele 300 de posturi din registrul comun), unde știm exact
ce problemă are fiecare contor și câtă energie lipsește din ce raportează el în ultimele 4 săptămâni.

Bilanțul fiecărui post îl construim din adevărul nostru: lipsa peste normal E = suma energiei nemăsurate de
contoarele postului (pozitivă la furt și la contorul oprit, negativă la salturi), plus zgomotul pierderilor normale
din rețea, cu abaterea sigma = o parte din consumul postului (1%, 2% sau 4%: cât de precis e bilanțul). Clienții
fără contor inteligent integrat (41%) intră doar în consumul postului, fără probleme.

Apoi aplicăm EXACT formula bilanțului (`fuse.combine_arrays`, doar confirmare) pe scorul calibrat al modelului A și
pe lipsa estimată de A pentru fiecare contor, și comparăm clasamentul cu și fără fuziune: pe tot testul, pe
defecte față de furt și pe tipuri. Codul bilanțului nu îl schimbăm.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

from cyberpunks.a_contoare import metrics as M
from cyberpunks.a_contoare.demo import target_date_from_scenario
from cyberpunks.a_contoare.inject import FAULT_KINDS, TAMPER_KINDS
from cyberpunks.a_contoare.predict import _deficit_kwh_day, _expected_band, score_population
from cyberpunks.a_contoare.topology import SMART_METER_INTEGRATION
from cyberpunks.common.paths import REPORTS

KS = (10, 20, 50, 100, 250)
SIGMA_REL = (0.01, 0.02, 0.04)


def _table(scenario: str) -> pd.DataFrame:
    target = target_date_from_scenario(scenario, None)
    tab, _feats, daily, peer, _ = score_population(target, scenario)
    deficits = []
    for i in range(len(tab)):
        exp, _, _ = _expected_band(daily[i], peer[i])
        deficits.append(_deficit_kwh_day(daily[i], exp))
    tab = tab.copy()
    tab["deficit"] = deficits
    return tab


def _fuse(tab: pd.DataFrame, sigma_rel: float, seed: int) -> np.ndarray:
    from cyberpunks.a_bilant.fuse import combine_arrays

    rng = np.random.default_rng(seed)
    post = tab.groupby("post_id").agg(loss=("true_recent_loss_kwh_day", "sum"), load=("true_recent_kwh_day", "sum"))
    post["load"] = post["load"] / SMART_METER_INTEGRATION  # tot postul, nu doar contoarele integrate
    post["sigma"] = sigma_rel * post["load"]
    post["excess"] = post["loss"] + rng.normal(0.0, post["sigma"])
    e = tab["post_id"].map(post["excess"]).to_numpy()
    sg = tab["post_id"].map(post["sigma"]).to_numpy()
    return combine_arrays(tab["score"].to_numpy(), e, sg, np.maximum(tab["deficit"].to_numpy(), 0.0))


def _summary(tab: pd.DataFrame, fused: np.ndarray) -> dict:
    y = tab["true_problem"].to_numpy()
    a = tab["score"].to_numpy()
    out = {"roc_auc_a": round(M.roc_auc(y, a), 4), "roc_auc_fused": round(M.roc_auc(y, fused), 4),
           "pr_auc_a": round(M.pr_auc(y, a), 4), "pr_auc_fused": round(M.pr_auc(y, fused), 4)}
    for k in KS:
        out[f"precision_at_{k}_a"] = round(M.precision_at_k(y, a, k), 4)
        out[f"precision_at_{k}_fused"] = round(M.precision_at_k(y, fused, k), 4)
    # câte lucrări sigure (conformal "problemă") sunt furturi sau defecte reale confirmate de bilanț
    with np.errstate(divide="ignore", invalid="ignore"):
        log_lr = np.log(fused / (1 - fused)) - np.log(np.clip(a, 1e-4, 1 - 1e-4) / (1 - np.clip(a, 1e-4, 1 - 1e-4)))
    confirmed = log_lr > 0.5
    fam = tab["true_family"].to_numpy()
    kind = tab["true_kind"].to_numpy()
    out["confirmed_share"] = {
        "furt_real": round(float(confirmed[fam == "tamper"].mean()), 4),
        "defect_real": round(float(confirmed[fam == "faulty"].mean()), 4),
        "fara_problema": round(float(confirmed[fam == "normal"].mean()), 4),
    }
    out["confirmed_share_by_kind"] = {
        k: round(float(confirmed[kind == k].mean()), 3) for k in (*FAULT_KINDS, *TAMPER_KINDS, "vacation", "occupancy_change")
        if (kind == k).any()
    }
    # în zona gri a lui A ("nu sunt sigur"): ajută bilanțul să separe problemele reale?
    unsure = tab["conformal"].to_numpy() == "unsure"
    out["gray_zone"] = {
        "meters": int(unsure.sum()),
        "real_problem_share": round(float(y[unsure].mean()), 4) if unsure.any() else None,
        "confirmed": int((unsure & confirmed).sum()),
        "real_problem_share_if_confirmed": round(float(y[unsure & confirmed].mean()), 4) if (unsure & confirmed).any() else None,
        "real_problem_share_if_not_confirmed": round(float(y[unsure & ~confirmed].mean()), 4) if (unsure & ~confirmed).any() else None,
    }
    # câștigul pe familii: precizia în primele 100, socotind ca "reale" doar furturile, apoi doar defectele
    for name, fam_name in (("doar_furt", "tamper"), ("doar_defecte", "faulty")):
        yy = (fam == fam_name).astype(int)
        out[f"precision_at_100_{name}_a"] = round(M.precision_at_k(yy, a, 100), 4)
        out[f"precision_at_100_{name}_fused"] = round(M.precision_at_k(yy, fused, 100), 4)
        out[f"roc_auc_{name}_a"] = round(M.roc_auc(yy, a), 4)
        out[f"roc_auc_{name}_fused"] = round(M.roc_auc(yy, fused), 4)
    return out


def run(scenarios: tuple[str, ...] = ("demo-vara", "maine"), seeds: tuple[int, ...] = (11, 12, 13)) -> dict:
    np.seterr(all="ignore")
    res: dict = {"note": ("Bilanț construit din adevărul injectat (populația demo, sintetic); formula de fuziune "
                          "a firului bilanț, neschimbată; rezultate mediate pe 3 trageri ale zgomotului de bilanț.")}
    for sc in scenarios:
        tab = _table(sc)
        res[sc] = {"meters": len(tab), "real_problems": int(tab["true_problem"].sum())}
        for rel in SIGMA_REL:
            runs = [_summary(tab, _fuse(tab, rel, seed)) for seed in seeds]
            agg = {}
            for key in runs[0]:
                if isinstance(runs[0][key], dict):
                    agg[key] = {k: (round(float(np.mean([r[key][k] for r in runs if r[key][k] is not None])), 4)
                                    if any(r[key][k] is not None for r in runs) else None) for k in runs[0][key]}
                else:
                    agg[key] = round(float(np.mean([r[key] for r in runs])), 4)
            res[sc][f"sigma_{int(rel * 100)}pct"] = agg
            print(f"{sc}, sigma {rel:.0%}: P@10 {agg['precision_at_10_a']} -> {agg['precision_at_10_fused']}, "
                  f"P@100 {agg['precision_at_100_a']} -> {agg['precision_at_100_fused']}, "
                  f"PR-AUC {agg['pr_auc_a']} -> {agg['pr_auc_fused']}; confirmate: {agg['confirmed_share']}")
    path = REPORTS / "A" / "fusion_check.json"
    path.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"scris: {path}")
    return res


if __name__ == "__main__":
    run()
    sys.exit(0)
