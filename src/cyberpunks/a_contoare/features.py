"""Features pentru contoare: fiecare are un motiv scris și o explicație în cuvinte simple.

Două niveluri:
- zilnic (merge pe SGCC, pe Londra și pe contoarele demo): `daily_features(x, peer)`;
- în cursul zilei, din citirile la 30 de minute (doar Londra și demo): `intraday_features(recent, base)`.

Convenții: `x` are forma (n_contoare, n_zile), kWh pe zi, NaN = lipsă; ultima coloană e ziua de evaluare.
Fereastra "recentă" = ultimele `recent` zile (implicit 28); "istoricul" = cele `base` zile dinaintea ei.
`peer` = consumul median al vecinilor (același post de transformare) în aceleași zile, forma (n_zile,) sau
(n_contoare, n_zile). Totul e vectorizat pe rânduri, fără bucle pe contoare.
"""

from __future__ import annotations

import warnings
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import pandas as pd

EPS = 1e-6


@dataclass(frozen=True)
class FeatureInfo:
    reason: str  # de ce ajută la detecție (motivul cerut de PPC: "features construite cu un motiv clar")
    label: Callable[[float], str]  # explicația pentru tehnician, cu cifra


def _pct(v: float) -> int:
    return round(abs(v) * 100)


FEATURE_INFO: dict[str, FeatureInfo] = {
    # goluri de comunicație
    "missing_ratio": FeatureInfo(
        "Golurile mari arată probleme de comunicație sau un contor scos din funcțiune.",
        lambda v: f"{_pct(v)}% din zile fără date",
    ),
    "missing_recent": FeatureInfo(
        "Golurile recente sunt cele care cer acum o citire la distanță sau o vizită.",
        lambda v: f"{_pct(v)}% din ultimele 4 săptămâni fără date",
    ),
    "longest_gap": FeatureInfo(
        "Un gol lung la rând e tipic pentru un modul de comunicație defect.",
        lambda v: f"cel mai lung gol: {v:.0f} zile fără date",
    ),
    # zerouri
    "zero_ratio": FeatureInfo(
        "Multe zile cu consum zero într-o locuință folosită arată un contor oprit sau ocolit.",
        lambda v: f"{_pct(v)}% din zile cu consum zero",
    ),
    "longest_zero_run": FeatureInfo(
        "Zerourile la rând, după un istoric normal, sunt regula VEE «consecutive zeros».",
        lambda v: f"{v:.0f} zile la rând cu consum zero",
    ),
    "zero_run_recent": FeatureInfo(
        "Un șir de zerouri care durează și azi înseamnă că problema e activă acum.",
        lambda v: f"consum zero în ultimele {v:.0f} zile",
    ),
    # valori blocate
    "longest_flat_run": FeatureInfo(
        "Aceeași valoare exactă, zi după zi, nu apare la consum real: registru blocat.",
        lambda v: f"{v:.0f} zile la rând cu exact aceeași valoare",
    ),
    "unique_ratio_recent": FeatureInfo(
        "Puține valori diferite în ultimele săptămâni arată o citire repetată sau înghețată.",
        lambda v: f"doar {_pct(v)}% valori diferite în ultimele 4 săptămâni",
    ),
    # schimbări față de propriul istoric
    "recent_vs_base": FeatureInfo(
        "O scădere bruscă față de propriul istoric e semnul clasic de furt sau de sub-înregistrare.",
        lambda v: (
            f"consumul a scăzut cu {_pct(1 - v)}% față de propriul istoric"
            if v < 1
            else f"consumul a crescut cu {_pct(v - 1)}% față de propriul istoric"
        ),
    ),
    "max_drop": FeatureInfo(
        "Cea mai mare scădere bruscă din fereastră prinde și furturile începute mai demult.",
        lambda v: f"o scădere bruscă de {_pct(v)}% la un moment dat",
    ),
    "trend_slope": FeatureInfo(
        "O pantă lentă în jos, fără motiv sezonier, arată un contor care înregistrează tot mai puțin.",
        lambda v: f"consumul scade constant cu {_pct(v)}% pe lună" if v < 0 else f"consumul crește cu {_pct(v)}% pe lună",
    ),
    "cv": FeatureInfo(
        "Variația zilnică foarte mică sau foarte mare față de medie iese din tiparul unei locuințe.",
        lambda v: f"variația zilnică: {v:.2f} din medie",
    ),
    # salturi și valori imposibile
    "spike_count": FeatureInfo(
        "Salturile izolate de 10-80 de ori peste normal sunt erori de măsură (regula VEE «spike check»).",
        lambda v: f"{v:.0f} salturi bruște, mult peste consumul obișnuit",
    ),
    "max_over_median": FeatureInfo(
        "Un maxim de zeci de ori peste mediană e o valoare imposibilă pentru o locuință.",
        lambda v: f"o zi cu de {v:.0f} ori mai mult decât de obicei",
    ),
    "negative_count": FeatureInfo(
        "Consumul negativ fără panouri solare arată conexiuni inversate (polaritate) sau o eroare.",
        lambda v: f"{v:.0f} zile cu consum negativ",
    ),
    # vecinii de pe același post
    "peer_ratio_recent": FeatureInfo(
        "Comparația cu vecinii de pe același post scoate efectul vremii și al sezonului.",
        lambda v: (
            f"cu {_pct(1 - v)}% sub mediana vecinilor de pe post"
            if v < 1
            else f"de {v:.1f} ori mediana vecinilor de pe post"
        ),
    ),
    "peer_ratio_change": FeatureInfo(
        "Dacă vecinii consumă la fel ca înainte și contorul nu, schimbarea nu vine din vreme.",
        lambda v: (
            f"față de vecini, consumul a scăzut cu {_pct(1 - v)}%"
            if v < 1
            else f"față de vecini, consumul a crescut cu {_pct(v - 1)}%"
        ),
    ),
    "peer_corr": FeatureInfo(
        "Un contor sănătos urmează aceleași zile reci sau calde ca vecinii; unul blocat nu.",
        lambda v: f"seamănă cu vecinii în proporție de {_pct(max(v, 0))}% (corelație)",
    ),
    "level_kwh": FeatureInfo(
        "Nivelul de consum contează pentru valoarea pierderii, dar consumul mic nu e dovadă de furt.",
        lambda v: f"consum obișnuit: {v:.1f} kWh pe zi",
    ),
    # în cursul zilei (30 min)
    "night_share_recent": FeatureInfo(
        "Ponderea consumului de noapte se schimbă la furtul de noapte și la ceasul decalat.",
        lambda v: f"{_pct(v)}% din consum noaptea (00-06)",
    ),
    "night_share_change": FeatureInfo(
        "O schimbare bruscă a consumului de noapte, față de istoric, iese din obiceiurile casei.",
        lambda v: (
            f"consumul de noapte a scăzut cu {_pct(1 - v)}% față de istoric"
            if v < 1
            else f"consumul de noapte a crescut cu {_pct(v - 1)}% față de istoric"
        ),
    ),
    "profile_corr": FeatureInfo(
        "Profilul zilei (când gătește, când doarme casa) e stabil; inversarea sau decalarea lui e suspectă.",
        lambda v: f"profilul zilei seamănă cu cel obișnuit doar {_pct(max(v, 0))}%",
    ),
    "intraday_cv_recent": FeatureInfo(
        "Un profil perfect plat în cursul zilei nu e consum real (raportare a mediei).",
        lambda v: f"variația în cursul zilei: {v:.2f} din medie",
    ),
    "intraday_cv_ratio": FeatureInfo(
        "Dacă variația din cursul zilei scade brusc față de istoric, citirile au fost aplatizate.",
        lambda v: f"variația în cursul zilei e {_pct(v)}% din cea obișnuită",
    ),
    "peak_shift": FeatureInfo(
        "Vârful zilnic mutat cu câteva ore arată un ceas decalat sau o inversare a orelor.",
        lambda v: f"vârful zilnic s-a mutat cu {v / 2:.1f} ore",
    ),
    "zero_slot_share_recent": FeatureInfo(
        "Intervalele de exact zero în timpul zilei apar când contorul e oprit câteva ore (atac h3).",
        lambda v: f"{_pct(v)}% din intervalele de 30 de minute sunt exact zero",
    ),
    "zero_slot_run_recent": FeatureInfo(
        "Un bloc zilnic de ore cu zero exact e tipic pentru oprirea programată a contorului.",
        lambda v: f"în medie {v / 2:.1f} ore pe zi cu consum exact zero, la rând",
    ),
    "negative_slot_share": FeatureInfo(
        "Citirile negative la 30 de minute arată conexiuni inversate.",
        lambda v: f"{_pct(v)}% din intervalele de 30 de minute sunt negative",
    ),
    "spike_slot_count": FeatureInfo(
        "Intervalele de 30 de minute de zeci de ori peste normal sunt erori de măsură.",
        lambda v: f"{v:.0f} intervale de 30 de minute cu salturi imposibile",
    ),
    "flat_slot_share_recent": FeatureInfo(
        "Aceeași valoare la fiecare 30 de minute arată o citire repetată (contor blocat).",
        lambda v: f"{_pct(v)}% din intervale repetă exact valoarea anterioară",
    ),
}

DAILY_FEATURES = [
    "missing_ratio",
    "missing_recent",
    "longest_gap",
    "zero_ratio",
    "longest_zero_run",
    "zero_run_recent",
    "longest_flat_run",
    "unique_ratio_recent",
    "recent_vs_base",
    "max_drop",
    "trend_slope",
    "cv",
    "spike_count",
    "max_over_median",
    "negative_count",
    "peer_ratio_recent",
    "peer_ratio_change",
    "peer_corr",
    "level_kwh",
]
INTRADAY_FEATURES = [
    "night_share_recent",
    "night_share_change",
    "profile_corr",
    "intraday_cv_recent",
    "intraday_cv_ratio",
    "peak_shift",
    "zero_slot_share_recent",
    "zero_slot_run_recent",
    "negative_slot_share",
    "spike_slot_count",
    "flat_slot_share_recent",
]
ALL_FEATURES = DAILY_FEATURES + INTRADAY_FEATURES


def label_ro(feature: str, value: float | None) -> str:
    """Explicația unui feature, în cuvinte simple, cu valoarea lui."""
    info = FEATURE_INFO.get(feature)
    if info is None or value is None or (isinstance(value, float) and not np.isfinite(value)):
        return f"{feature}: fără valoare"
    return info.label(float(value))


# --------------------------------------------------------------------------------------------
# Unelte vectorizate pe rânduri
# --------------------------------------------------------------------------------------------


def longest_run(mask: np.ndarray) -> np.ndarray:
    """Cel mai lung șir de True pe fiecare rând (mask: n × W)."""
    n, w = mask.shape
    best = np.zeros(n, dtype=np.int32)
    cur = np.zeros(n, dtype=np.int32)
    for j in range(w):
        cur = np.where(mask[:, j], cur + 1, 0)
        np.maximum(best, cur, out=best)
    return best


def trailing_zero_streak(x: np.ndarray) -> np.ndarray:
    """Câte zile cu zero exact are șirul care ține până azi (zilele lipsă nu întrerup și nu se numără)."""
    n, w = x.shape
    count = np.zeros(n, dtype=np.int32)
    active = np.ones(n, dtype=bool)
    for j in range(w - 1, -1, -1):
        col = x[:, j]
        is_zero = col == 0
        stop = active & (col != 0) & ~np.isnan(col)
        count = np.where(active & is_zero, count + 1, count)
        active &= ~stop
        if not active.any():
            break
    return count


def _nanmedian(a: np.ndarray, axis: int = 1) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmedian(a, axis=axis)


def _nanmean(a: np.ndarray, axis: int = 1) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmean(a, axis=axis)


def _nanstd(a: np.ndarray, axis: int = 1) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanstd(a, axis=axis)


def _safe_ratio(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        r = a / b
    r[~np.isfinite(r)] = np.nan
    return r


def _row_corr(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Corelația Pearson pe rânduri, doar pe pozițiile unde ambele au valori."""
    m = ~np.isnan(a) & ~np.isnan(b)
    cnt = m.sum(axis=1)
    a0 = np.where(m, a, 0.0)
    b0 = np.where(m, b, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ma = a0.sum(axis=1) / cnt
        mb = b0.sum(axis=1) / cnt
        da = np.where(m, a - ma[:, None], 0.0)
        db = np.where(m, b - mb[:, None], 0.0)
        cov = (da * db).sum(axis=1)
        r = cov / np.sqrt((da**2).sum(axis=1) * (db**2).sum(axis=1))
    r[(cnt < 10) | ~np.isfinite(r)] = np.nan
    return r


# --------------------------------------------------------------------------------------------
# Features zilnice
# --------------------------------------------------------------------------------------------


def daily_features(x: np.ndarray, peer: np.ndarray | None = None, recent: int = 28, base: int = 120) -> pd.DataFrame:
    """Features zilnice pentru fiecare rând din `x` (n × W, kWh/zi). Vezi FEATURE_INFO pentru motive."""
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError("x trebuie să aibă forma (n_contoare, n_zile)")
    n, w = x.shape
    recent = min(recent, w)
    r = x[:, w - recent :]
    b = x[:, max(0, w - recent - base) : w - recent]
    valid = ~np.isnan(x)
    n_valid = valid.sum(axis=1)
    out: dict[str, np.ndarray] = {}

    out["missing_ratio"] = 1.0 - n_valid / w
    out["missing_recent"] = np.isnan(r).mean(axis=1)
    out["longest_gap"] = longest_run(~valid).astype(float)

    zero = x == 0
    with np.errstate(divide="ignore", invalid="ignore"):
        out["zero_ratio"] = np.where(n_valid > 0, zero.sum(axis=1) / n_valid, np.nan)
    out["longest_zero_run"] = longest_run(zero).astype(float)
    out["zero_run_recent"] = trailing_zero_streak(x).astype(float)

    # valori identice consecutive (diferență exact 0), nenule
    same = np.zeros_like(zero)
    same[:, 1:] = (x[:, 1:] == x[:, :-1]) & (x[:, 1:] != 0)
    out["longest_flat_run"] = (longest_run(same) + (longest_run(same) > 0)).astype(float)
    r_valid = ~np.isnan(r)
    uniq = np.array([len(np.unique(row[m])) for row, m in zip(r, r_valid, strict=True)], dtype=float)
    out["unique_ratio_recent"] = np.where(r_valid.sum(axis=1) > 0, uniq / np.maximum(r_valid.sum(axis=1), 1), np.nan)

    med_r = _nanmedian(r)
    med_b = _nanmedian(b) if b.shape[1] else np.full(n, np.nan)
    out["recent_vs_base"] = _safe_ratio(med_r, med_b + EPS)

    # cea mai mare scădere bruscă: mediana pe 28 de zile după t față de mediana pe 90 de zile înainte de t
    drops = []
    for t in range(90, w - 28 + 1, 7):
        before = _nanmedian(x[:, t - 90 : t])
        after = _nanmedian(x[:, t : t + 28])
        drops.append(1.0 - _safe_ratio(after, before + EPS))
    if drops:
        d = np.vstack(drops)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            out["max_drop"] = np.clip(np.nanmax(d, axis=0), -5.0, 1.0)
    else:
        out["max_drop"] = np.full(n, np.nan)

    # panta: regresie pe medianele săptămânale ale lui log(1 + x), exprimată ca schimbare relativă pe 30 de zile
    n_weeks = w // 7
    if n_weeks >= 4:
        weeks = x[:, w - n_weeks * 7 :].reshape(n, n_weeks, 7)
        wm = np.log1p(np.clip(_nanmedian(weeks, axis=2), 0, None))
        t_idx = np.arange(n_weeks, dtype=float)
        m = ~np.isnan(wm)
        cnt = m.sum(axis=1)
        tm = np.where(m, t_idx, 0).sum(axis=1) / np.maximum(cnt, 1)
        ym = np.where(m, wm, 0).sum(axis=1) / np.maximum(cnt, 1)
        dt = np.where(m, t_idx - tm[:, None], 0)
        dy = np.where(m, wm - ym[:, None], 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            slope_week = (dt * dy).sum(axis=1) / (dt**2).sum(axis=1)
        slope = np.expm1(slope_week * 30 / 7)
        slope[cnt < 4] = np.nan
        out["trend_slope"] = np.clip(slope, -1.0, 5.0)
    else:
        out["trend_slope"] = np.full(n, np.nan)

    mean_all = _nanmean(x)
    out["cv"] = _safe_ratio(_nanstd(x), np.abs(mean_all) + EPS)

    med_all = _nanmedian(x)
    mad = _nanmedian(np.abs(x - med_all[:, None]))
    thr = np.maximum(med_all + 8 * (mad + 0.05), 3 * np.abs(med_all) + 0.5)
    with np.errstate(invalid="ignore"):
        out["spike_count"] = (x > thr[:, None]).sum(axis=1).astype(float)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        out["max_over_median"] = _safe_ratio(np.nanmax(x, axis=1), np.abs(med_all) + 0.1)
    with np.errstate(invalid="ignore"):
        out["negative_count"] = (x < 0).sum(axis=1).astype(float)

    if peer is not None:
        p = np.broadcast_to(np.asarray(peer, dtype=np.float64), x.shape)
        pr = p[:, w - recent :]
        pb = p[:, max(0, w - recent - base) : w - recent]
        ratio_r = _nanmedian(_safe_ratio(r, pr + EPS))
        ratio_b = _nanmedian(_safe_ratio(b, pb + EPS)) if b.shape[1] else np.full(n, np.nan)
        out["peer_ratio_recent"] = ratio_r
        out["peer_ratio_change"] = _safe_ratio(ratio_r, ratio_b + EPS)
        out["peer_corr"] = _row_corr(x, p)
    else:
        for k in ("peer_ratio_recent", "peer_ratio_change", "peer_corr"):
            out[k] = np.full(n, np.nan)

    out["level_kwh"] = med_b if b.shape[1] else med_all
    df = pd.DataFrame(out, columns=DAILY_FEATURES)
    return df.astype("float32")


# --------------------------------------------------------------------------------------------
# Features din citirile la 30 de minute
# --------------------------------------------------------------------------------------------

NIGHT_SLOTS = slice(0, 12)  # 00:00-06:00


def intraday_features(recent: np.ndarray, base: np.ndarray) -> pd.DataFrame:
    """Features din profilul zilnic. `recent` și `base`: (n, zile, 48), kWh pe 30 de minute, NaN = lipsă."""
    recent = np.asarray(recent, dtype=np.float64)
    base = np.asarray(base, dtype=np.float64)
    n = recent.shape[0]
    out: dict[str, np.ndarray] = {}

    def night_share(a: np.ndarray) -> np.ndarray:
        tot = np.nansum(np.nansum(a, axis=2), axis=1)
        night = np.nansum(np.nansum(a[:, :, NIGHT_SLOTS], axis=2), axis=1)
        return _safe_ratio(night, np.abs(tot) + EPS)

    ns_r, ns_b = night_share(recent), night_share(base)
    out["night_share_recent"] = ns_r
    out["night_share_change"] = _safe_ratio(ns_r, ns_b + EPS)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        prof_r = np.nanmean(recent, axis=1)  # (n, 48)
        prof_b = np.nanmean(base, axis=1)
    out["profile_corr"] = _row_corr(prof_r, prof_b)

    def intraday_cv(a: np.ndarray) -> np.ndarray:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            day_mean = np.nanmean(a, axis=2)
            day_std = np.nanstd(a, axis=2)
            cv = day_std / (np.abs(day_mean) + 1e-3)
            return np.nanmedian(cv, axis=1)

    cv_r, cv_b = intraday_cv(recent), intraday_cv(base)
    out["intraday_cv_recent"] = cv_r
    out["intraday_cv_ratio"] = _safe_ratio(cv_r, cv_b + EPS)

    pk_r = np.nanargmax(np.nan_to_num(prof_r, nan=-np.inf), axis=1)
    pk_b = np.nanargmax(np.nan_to_num(prof_b, nan=-np.inf), axis=1)
    diff = np.abs(pk_r - pk_b)
    shift = np.minimum(diff, 48 - diff).astype(float)
    shift[np.all(np.isnan(prof_r), axis=1) | np.all(np.isnan(prof_b), axis=1)] = np.nan
    out["peak_shift"] = shift

    flat_r = recent.reshape(n, -1)
    valid_r = ~np.isnan(flat_r)
    n_valid = np.maximum(valid_r.sum(axis=1), 1)
    out["zero_slot_share_recent"] = (flat_r == 0).sum(axis=1) / n_valid

    # cel mai lung bloc de zero exact în fiecare zi, mediat pe zile
    d = recent.shape[1]
    zero_days = (recent == 0).reshape(n * d, 48)
    runs = longest_run(zero_days).reshape(n, d).astype(float)
    day_has_data = ~np.all(np.isnan(recent), axis=2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        out["zero_slot_run_recent"] = np.nanmean(np.where(day_has_data, runs, np.nan), axis=1)

    with np.errstate(invalid="ignore"):
        out["negative_slot_share"] = (flat_r < 0).sum(axis=1) / n_valid
    pos = np.where(flat_r > 0, flat_r, np.nan)
    med_pos = _nanmedian(pos)
    with np.errstate(invalid="ignore"):
        out["spike_slot_count"] = (flat_r > np.maximum(10 * med_pos, 2.0)[:, None]).sum(axis=1).astype(float)
    same = (flat_r[:, 1:] == flat_r[:, :-1]) & (flat_r[:, 1:] != 0)
    out["flat_slot_share_recent"] = same.sum(axis=1) / n_valid

    df = pd.DataFrame(out, columns=INTRADAY_FEATURES)
    return df.astype("float32")
