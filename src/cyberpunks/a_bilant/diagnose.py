"""Modelul 2: diagnosticul cauzei lipsei de la post (clasificator multiclasă pe fereastra de 14 zile).

Clasele: `problems.CLASSES`. Metoda simplă de comparat: tabelul de reguli din conceptul lui Teo (`rules`).
Modelul spune „nu sunt sigur” (abstain) când cea mai probabilă cauză are sub 50% sau e la egalitate cu a doua
(diferență sub 15 puncte), ori când intervalul pierderii normale e prea larg față de lipsă.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import lightgbm as lgb
import numpy as np
import pandas as pd

from cyberpunks.a_bilant.normal import MODEL_DIR
from cyberpunks.a_bilant.problems import CLASSES
from cyberpunks.a_bilant.windows import WIN_FEATURES

ABSTAIN_PMAX = 0.5
ABSTAIN_MARGIN = 0.15
ABSTAIN_WIDTH_RATIO = 3.0  # intervalul P10-P90 mai mare de 3 ori decât lipsa peste normal: nu ne pronunțăm


@dataclass
class Diagnoser:
    model: lgb.LGBMClassifier | lgb.Booster

    def proba(self, X: pd.DataFrame) -> pd.DataFrame:
        if isinstance(self.model, lgb.Booster):
            p = self.model.predict(X[WIN_FEATURES])
        else:
            p = self.model.predict_proba(X[WIN_FEATURES])
        return pd.DataFrame(p, columns=list(CLASSES), index=X.index)

    def save(self) -> None:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        assert isinstance(self.model, lgb.LGBMClassifier)
        self.model.booster_.save_model(str(MODEL_DIR / "diagnose.txt"))
        (MODEL_DIR / "diagnose.json").write_text(json.dumps({"classes": list(CLASSES), "features": WIN_FEATURES}))


def load() -> Diagnoser:
    return Diagnoser(lgb.Booster(model_file=str(MODEL_DIR / "diagnose.txt")))


def fit(win: pd.DataFrame, seed: int = 0) -> Diagnoser:
    y = win["true_class"].map({c: i for i, c in enumerate(CLASSES)}).to_numpy()
    # clase echilibrate: problemele rare cântăresc cât cele dese
    counts = np.bincount(y, minlength=len(CLASSES)).astype(float)
    w = (len(y) / (len(CLASSES) * np.maximum(counts, 1)))[y]
    if "weight" in win.columns:  # verdictele după vizită (feedback.windows_with_verdicts) cântăresc mai mult
        w = w * win["weight"].to_numpy()
    m = lgb.LGBMClassifier(
        objective="multiclass",
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.8,
        subsample_freq=1,
        colsample_bytree=0.8,
        random_state=seed,
        verbose=-1,
        n_jobs=4,
    )
    m.fit(win[WIN_FEATURES], y, sample_weight=w)
    return Diagnoser(m)


def decide(proba: pd.DataFrame, win: pd.DataFrame) -> pd.DataFrame:
    """Clasa aleasă, încrederea și abținerea (cu motiv)."""
    p = proba.to_numpy()
    order = np.argsort(-p, axis=1)
    top, second = order[:, 0], order[:, 1]
    pmax = p[np.arange(len(p)), top]
    p2 = p[np.arange(len(p)), second]
    label = np.array(CLASSES)[top]
    reason = np.array([""] * len(p), dtype=object)
    low = pmax < ABSTAIN_PMAX
    tie = (pmax - p2) < ABSTAIN_MARGIN
    wide = (label != "normal") & (win["width_kwh"].to_numpy() > ABSTAIN_WIDTH_RATIO * np.abs(win["r_mean_kwh"].to_numpy()))
    reason[low] = "cauza cea mai probabilă are sub 50%"
    reason[tie & ~low] = "două cauze aproape la egalitate"
    reason[wide & ~low & ~tie] = "intervalul pierderii normale e prea larg față de lipsă"
    abstain = (low | tie | wide) & (label != "normal") | ((low | tie) & (label == "normal") & (p[:, 0] < 0.5))
    return pd.DataFrame(
        {"label": label, "p_label": pmax, "second": np.array(CLASSES)[second], "p_second": p2, "p_problem": 1 - p[:, 0], "abstain": abstain, "abstain_reason": reason},
        index=proba.index,
    )


def rules(win: pd.DataFrame) -> pd.Series:
    """Tabelul de reguli din concept (metoda simplă). Pragurile sunt alese de mână, nu învățate."""
    out = []
    for _, r in win.iterrows():
        over = r["z_mean"] > 1.5 and r["days_over_p90"] >= 7
        if 1.8 <= r["bal_db_ratio"] <= 2.3:
            out.append("contor_bilant_setat")
        elif over and (r["new_zero"] + r["new_stuck"] + r["new_neg"] > 0 or r["drop_match"] > 0.5):
            out.append("contor_client")
        elif over and r["neigh_match"] > 0.6 or r["z_mean"] < -1.5 and r["days_under_p10"] >= 7:
            out.append("client_post_gresit")
        elif over and r["corr_r_load2"] > 0.5:
            out.append("pierdere_tehnica")
        elif over and r["jump_vs_prev"] > 1.0 or over:
            out.append("furt_inainte_contor")
        else:
            out.append("normal")
    return pd.Series(out, index=win.index)


PAIR_MIRROR_CORR = -0.5
PAIR_MATCH = 0.5


def pair_consistency(win: pd.DataFrame, dec: pd.DataFrame) -> pd.DataFrame:
    """Leagă cele două capete ale unui client mutat în bază: dacă vecinul-oglindă (reziduuri în oglindă, corelație
    sub −0,5) are diagnosticul „client la postul greșit” cu surplus, iar postul are lipsă de aceeași mărime
    (potrivire ≥ 0,5), postul e donatorul aceleiași perechi: clasa devine `client_post_gresit`."""
    out = dec.copy()
    key = {(p, d): lab for p, d, lab in zip(win["post_id"], win["day"], dec["label"], strict=True)}
    rmean = {(p, d): r for p, d, r in zip(win["post_id"], win["day"], win["r_mean_kwh"], strict=True)}
    flip = np.zeros(len(win), dtype=bool)
    for i, (p, d, q, c, m, r) in enumerate(zip(win["post_id"], win["day"], win.get("mirror_post", pd.Series([""] * len(win))), win["neigh_mirror_corr"], win["neigh_mirror_match"], win["r_mean_kwh"], strict=True)):
        if not q or c > PAIR_MIRROR_CORR or m < PAIR_MATCH or r <= 0:
            continue
        if key.get((q, d)) == "client_post_gresit" and rmean.get((q, d), 0.0) < 0 and out["label"].iat[i] != "contor_bilant_setat":
            flip[i] = True
    out.loc[flip, "label"] = "client_post_gresit"
    out.loc[flip, "abstain"] = False
    out.loc[flip, "abstain_reason"] = ""
    out["pair_linked"] = flip
    return out


def apply_martor_rule(win: pd.DataFrame, dec: pd.DataFrame) -> pd.DataFrame:
    """Regula contorului martor (`martor.py`), aplicată după model, unde postul are martor:
    - diferență peste clasa de exactitate → contorul de balanță e defect sau setat greșit (sigur, fără abținere);
    - diferență în clasă, dar modelul spusese „contor de post setat greșit” → contorul de balanță e confirmat bun,
      deci se alege a doua cauză a modelului."""
    from cyberpunks.a_bilant.martor import MARTOR_DIFF_LIMIT

    out = dec.copy()
    d = win["martor_diff"].to_numpy() if "martor_diff" in win else np.full(len(win), np.nan)
    has = np.isfinite(d)
    over = has & (d > MARTOR_DIFF_LIMIT)
    ok_meter = has & ~over & (out["label"].to_numpy() == "contor_bilant_setat")
    out.loc[over, "label"] = "contor_bilant_setat"
    out.loc[over, "p_label"] = 1.0
    out.loc[over, "p_problem"] = 1.0
    out.loc[over, "abstain"] = False
    out.loc[over, "abstain_reason"] = ""
    out.loc[ok_meter, "label"] = out.loc[ok_meter, "second"]
    out.loc[ok_meter, "p_label"] = out.loc[ok_meter, "p_second"]
    out["martor_rule"] = np.where(over, "diferenta_peste_clasa", np.where(ok_meter, "contor_balanta_confirmat", np.where(has, "in_clasa", "fara_martor")))
    return out
