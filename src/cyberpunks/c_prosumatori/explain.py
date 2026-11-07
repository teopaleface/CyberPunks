"""Explicații: contribuțiile SHAP la scorul lucrării, grupate în motive spuse simplu, și cazuri similare din simulare.

Contribuțiile vin din TreeSHAP (LightGBM `pred_contrib`) pe clasificatorul P(tensiune > 1,10 pu), în log-odds:
pozitiv împinge spre depășire, negativ o îndepărtează. Pentru tensiunea estimată (P50) se pot cere și contribuțiile
în pu (`shap_groups(modelul_P50, X)`). Trăsăturile înrudite se adună într-un singur motiv (de exemplu toate cele
despre panouri), iar textul se scrie din șablon, cu cifrele postului.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

GROUPS: dict[str, list[str]] = {
    "panouri": ["pv_kw", "pv_kw_per_kva", "n_prosumers", "prosumer_share", "kva"],
    "soare": ["gti_max", "gti_sum", "ghi_max", "pvk_max", "cloud_mean", "dif_frac_noon"],
    "temperatura": ["temp_noon"],
    "pornire": ["v0_est", "tap_pos", "vk_percent"],
    "retea": ["line_km", "max_path_km", "r_max_ohm", "sens_pv_pu", "sens_load_pu"],
    "consum": ["annual_load_mwh", "n_customers", "load_ratio_noon", "free_day"],
    "baterii": ["battery_kwh", "battery_pv_share"],
    "fizica": ["dv_lin_max", "v_lin_max", "net_kw_per_kva_max"],
    "perioada": ["doy_sin", "doy_cos"],
}
REPRESENTATIVE = {
    "panouri": "pv_kw_per_kva",
    "soare": "gti_max",
    "temperatura": "temp_noon",
    "pornire": "v0_est",
    "retea": "max_path_km",
    "consum": "free_day",
    "baterii": "battery_pv_share",
    "fizica": "v_lin_max",
    "perioada": "doy_sin",
}
MONTHS_RO = ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"]
DAYS_RO = ["luni", "marți", "miercuri", "joi", "vineri", "sâmbătă", "duminică"]


def fmt(x: float, nd: int = 2) -> str:
    """Număr cu virgulă zecimală, ca în română."""
    return f"{x:.{nd}f}".replace(".", ",")


def label(group: str, r: pd.Series, target_date=None) -> str:
    if group == "panouri":
        return f"{r['pv_kw']:.0f} kW de panouri pe un transformator de {r['kva']:.0f} kVA ({int(r['n_prosumers'])} prosumatori)"
    if group == "soare":
        g = r["gti_max"]
        if g < 300:
            return f"cer acoperit: doar {g:.0f} W/m² pe panou la prânz"
        return f"soare {g:.0f} W/m² pe panou la prânz"
    if group == "temperatura":
        t = r["temp_noon"]
        tail = " (panourile reci produc mai mult)" if t < 15 else (" (căldura scade randamentul panourilor)" if t > 30 else "")
        return f"{t:.0f} °C la prânz{tail}"
    if group == "pornire":
        tap = int(r["tap_pos"])
        return f"priza pe {tap:+d}, tensiunea fără sarcină {fmt(r['v0_est'], 3)} pu" if tap else f"priza pe mijloc, tensiunea fără sarcină {fmt(r['v0_est'], 3)} pu"
    if group == "retea":
        return f"{r['max_path_km'] * 1000:.0f} m până la capătul rețelei, rezistență {fmt(r['r_max_ohm'])} ohm"
    if group == "consum":
        if target_date is not None:
            day = DAYS_RO[target_date.weekday()]
            return f"{day}, {'zi liberă, consum mic' if r['free_day'] else 'zi lucrătoare'} la prânz"
        return "zi liberă, consum mic la prânz" if r["free_day"] else "zi lucrătoare"
    if group == "baterii":
        if r["battery_kwh"] <= 0:
            return "fără baterii la prosumatori"
        return f"baterii la {r['battery_pv_share'] * 100:.0f}% din panouri ({r['battery_kwh']:.0f} kWh), pline repede la soare"
    if group == "fizica":
        dv = r["dv_lin_max"]
        verb = "ridică" if dv >= 0 else "coboară"
        return (f"de la {fmt(r['v0_est'], 3)} pu fără sarcină, panourile {verb} tensiunea cu {fmt(abs(dv), 3)} pu la soarele zilei "
                f"(estimare fizică: {fmt(r['v_lin_max'], 3)} pu)")
    if group == "perioada":
        if target_date is not None:
            return f"perioada din an: {MONTHS_RO[target_date.month - 1]}"
        return "perioada din an"
    return group


def shap_groups(model, X: pd.DataFrame) -> pd.DataFrame:
    """Contribuțiile SHAP adunate pe grupuri (în unitățile modelului: log-odds la clasificator, pu la P50)."""
    contrib = model.booster_.predict(X, pred_contrib=True)
    cols = list(X.columns)
    out = {}
    for g, feats in GROUPS.items():
        idx = [cols.index(f) for f in feats if f in cols]
        out[g] = contrib[:, idx].sum(axis=1)
    df = pd.DataFrame(out, index=X.index)
    df["_bias"] = contrib[:, -1]
    return df


def top_factors(contrib_row: pd.Series, feat_row: pd.Series, target_date=None, k: int = 5) -> list[dict]:
    groups = [g for g in GROUPS if g in contrib_row.index]
    order = sorted(groups, key=lambda g: -abs(contrib_row[g]))[:k]
    out = []
    for g in order:
        rep = REPRESENTATIVE[g]
        v = feat_row.get(rep)
        out.append({
            "feature": rep,
            "label_ro": label(g, feat_row, target_date),
            "value": round(float(v), 4) if isinstance(v, int | float | np.floating | np.integer) else v,
            "contribution": round(float(contrib_row[g]), 4),
        })
    return out


SIMILAR_SAMPLE = "similar_cases.parquet"  # în data/samples/C: o mostră a simulării de antrenare, pentru clone curate


def similar_reference() -> pd.DataFrame:
    """Zilele-post de referință: din simularea completă dacă există, altfel mostra din git."""
    from cyberpunks.common.paths import DATA_PROCESSED, DATA_SAMPLES

    full = DATA_PROCESSED / "C" / "train" / "daily_features.parquet"
    if full.exists():
        df = pd.read_parquet(full)
        df["exceed"] = (df["vmax_day"] > 1.10).astype(int)
        return df
    return pd.read_parquet(DATA_SAMPLES / "C" / SIMILAR_SAMPLE)


def export_similar_sample(n: int = 20_000, seed: int = 0) -> None:
    from cyberpunks.common.paths import DATA_SAMPLES

    d = similar_reference()
    d = d[d["pvk_max"] > 0.2].sample(n, random_state=seed)
    cols = ["post_id", "date", "topology", "vmax_day", "hours_over_110", *SimilarCases.KEYS]
    d[cols].assign(date=lambda x: pd.to_datetime(x["date"])).to_parquet(DATA_SAMPLES / "C" / SIMILAR_SAMPLE, index=False)


class SimilarCases:
    """Cele mai apropiate zile-post din simularea de antrenare (trăsături standardizate)."""

    KEYS: tuple[str, ...] = ("pv_kw_per_kva", "sens_pv_pu", "v0_est", "pvk_max", "load_ratio_noon", "battery_pv_share")

    def __init__(self, train_daily: pd.DataFrame, n: int = 120_000, seed: int = 0):
        from sklearn.neighbors import NearestNeighbors

        d = train_daily[train_daily["pvk_max"] > 0.2]
        d = d.sample(min(n, len(d)), random_state=seed)
        self.ref = d[["post_id", "date", "topology", "vmax_day", "hours_over_110", *self.KEYS]].reset_index(drop=True)
        X = self.ref[list(self.KEYS)].to_numpy(dtype=float)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-9
        self.nn = NearestNeighbors(n_neighbors=3).fit((X - self.mu) / self.sd)

    def query(self, row: pd.Series, k: int = 3) -> list[dict]:
        x = (row[list(self.KEYS)].to_numpy(dtype=float) - self.mu) / self.sd
        dist, idx = self.nn.kneighbors(x.reshape(1, -1), n_neighbors=k)
        out = []
        for d, i in zip(dist[0], idx[0], strict=True):
            c = self.ref.iloc[int(i)]
            exceeded = c["vmax_day"] > 1.10
            out.append({
                "case_id": f"SIM-{c['post_id']}-{pd.Timestamp(c['date']):%Y%m%d}",
                "outcome": "depasire_simulata" if exceeded else "fara_depasire_simulata",
                "similarity": round(float(1.0 / (1.0 + d)), 3),
                "note_ro": (f"post sintetic {c['topology']}, {pd.Timestamp(c['date']):%d.%m.%Y}: {fmt(c['vmax_day'], 3)} pu, "
                            f"{int(c['hours_over_110'])} ore peste 1,10 (simulare)"),
            })
        return out
