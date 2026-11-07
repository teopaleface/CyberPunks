"""Fuziunea bilanț + A: confirmarea independentă a contoarelor marcate de modelul A.

Pentru un contor marcat de A, cu lipsa estimată d (kWh/zi), aflat pe un post unde bilanțul vede lipsa peste normal E
(kWh/zi, cu incertitudinea σ a pierderii normale), raportul de verosimilitate spune cât de bine explică defectul
contorului lipsa de la post:

    LR = N(E; d, σ_t) / N(E; 0, σ_t),   σ_t² = σ² + (0,5·d)²,   log LR limitat la [0, +3]
    scor combinat = sigmoid(logit(scor A) + log LR)

Bilanțul doar confirmă: dacă la post lipsește cât spune A, scorul urcă; dacă bilanțul nu confirmă, scorul rămâne al lui
A (doar o notă). Pe ziua demo, cu scorurile reale ale lui A, coborârea scorurilor strica clasamentul (AUC 0,918 →
0,907), iar varianta care doar confirmă îl păstrează (0,919): un contor găsit de A nu se ascunde niciodată.

„Nu sunt sigur” rămâne la om: rezolvarea automată (o lucrare A cu abstain, confirmată de bilanț, trecută la citire la
distanță) e în cod, dar oprită (`RESOLVE_ABSTAIN`), pentru că pe ziua demo nu a nimerit nicio problemă reală. Planificatorul aplică `fuse` înainte de decizie și scrie
regula `R-FUSION-BILANT` în jurnal.
"""

from __future__ import annotations

import json
import math
from datetime import date as Date
from pathlib import Path

import numpy as np

from cyberpunks.common.contracts import BilantFusion, Factor, WorkItem
from cyberpunks.common.paths import OUTPUTS

LOG_LR_CAP = 3.0
RESOLVE_ABSTAIN_LOG_LR = 1.5  # raportul e plafonat la ~2 de incertitudinea lipsei contorului
# Oprit (7 nov., 14:45): pe ziua demo, cele 5 lucrări A „nu sunt sigur” rezolvate așa nu aveau nicio problemă reală
# (lipsa estimată de A vine din curbele lui, nu din contorul din lumea bilanțului). Le decide omul.
RESOLVE_ABSTAIN = False
LEI_MONTH_DAYS = 30.0


def state_path(scenario: str, date: str | Date) -> Path:
    return OUTPUTS / "bilant" / scenario / f"posts_{date}.json"


def combine(a_score: float, excess_kwh: float, sigma_kwh: float, meter_deficit_kwh: float, demote: bool = False) -> tuple[float, float]:
    """(scor combinat, log LR). Toate valorile pe zi. Fără `demote`, log LR negativ devine 0 (doar confirmare)."""
    d = max(float(meter_deficit_kwh), 0.0)
    s = math.sqrt(max(sigma_kwh, 0.1) ** 2 + (0.5 * d) ** 2)
    log_lr = (-((excess_kwh - d) ** 2) + excess_kwh**2) / (2 * s**2)
    log_lr = float(np.clip(log_lr, -LOG_LR_CAP if demote else 0.0, LOG_LR_CAP))
    a = float(np.clip(a_score, 1e-4, 1 - 1e-4))
    z = math.log(a / (1 - a)) + log_lr
    return float(1 / (1 + math.exp(-z))), log_lr


def combine_arrays(a_score: np.ndarray, excess: np.ndarray, sigma: np.ndarray, deficit: np.ndarray, demote: bool = False) -> np.ndarray:
    d = np.maximum(deficit, 0.0)
    s = np.sqrt(np.maximum(sigma, 0.1) ** 2 + (0.5 * d) ** 2)
    log_lr = np.clip((-((excess - d) ** 2) + excess**2) / (2 * s**2), -LOG_LR_CAP if demote else 0.0, LOG_LR_CAP)
    a = np.clip(a_score, 1e-4, 1 - 1e-4)
    return 1 / (1 + np.exp(-(np.log(a / (1 - a)) + log_lr)))


def _load_state(scenario: str, date: str | Date) -> dict:
    p = state_path(scenario, date)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _nearest_post(state: dict, lat: float, lon: float) -> str | None:
    best, bd = None, float("inf")
    for pid, s in state.get("posts", {}).items():
        d = (s["lat"] - lat) ** 2 + ((s["lon"] - lon) * math.cos(math.radians(lat))) ** 2
        if d < bd:
            best, bd = pid, d
    return best


def fuse(items: list[WorkItem], scenario: str, date: str | Date) -> list[WorkItem]:
    """Întoarce lucrările, cu cele A pe contoare confirmate sau infirmate de bilanțul postului.

    Lucrările care nu sunt A pe contor, sau al căror post nu are contor de bilanț, rămân neschimbate. Fără starea bilanțului pentru scenariu și dată, funcția nu schimbă nimic.
    """
    state = _load_state(scenario, date)
    if not state:
        return list(items)
    posts = state["posts"]
    price = float(state.get("loss_cost_lei_per_kwh", 0.70))
    out: list[WorkItem] = []
    for w in items:
        if w.source.value != "A" or w.asset_type.value != "meter" or "fusion" in w.extra:
            out.append(w)
            continue
        pid = str(w.extra.get("post_id", ""))
        approx = False
        if pid not in posts:
            pid = _nearest_post(state, w.location.lat, w.location.lon) or ""
            approx = True
        s = posts.get(pid)
        if not s or not s.get("has_balance", True):
            out.append(w)
            continue
        d = float(w.extra.get("estimated_kwh_lost_per_day", w.prediction.point_estimate or 0.0) or 0.0)
        a = float(w.prediction.score)
        comb, log_lr = combine(a, float(s["excess_kwh_day"]), float(s["sigma_kwh_day"]), d)
        if approx:
            # contorul nu e în registrul de posturi: legătura după poziție nu e o dovadă, scorul rămâne cel al lui A
            comb, log_lr = a, 0.0
        comb = round(comb, 4)
        if approx:
            note = f"Contorul nu e legat în bază de un post din registru; cel mai apropiat post e {pid}, dar fără legătură sigură bilanțul nu schimbă scorul."
        elif log_lr > 0.5:
            note = f"Confirmat de bilanțul postului {pid}: lipsa la post a crescut cu ~{s['excess_kwh_day']:.1f} kWh/zi, iar contorul explică ~{d:.1f} kWh/zi."
        else:
            note = f"Bilanțul postului {pid} nu confirmă (lipsa a crescut cu ~{s['excess_kwh_day']:.1f} kWh/zi); scorul rămâne al modelului A."
        fusion = BilantFusion(
            post_id=pid,
            bilant_prediction_id=str(s["prediction_id"]),
            post_excess_loss_kwh_day=round(float(s["excess_kwh_day"]), 3),
            post_excess_loss_lei_month=round(max(float(s["excess_kwh_day"]), 0.0) * LEI_MONTH_DAYS * price, 2),
            a_score=round(a, 4),
            combined_score=round(comb, 4),
            note_ro=note,
        )
        data = w.model_dump(mode="json")
        pred = data["prediction"]
        pred["score"] = comb
        if pred.get("interval_low") is not None and pred.get("interval_high") is not None:
            pred["interval_low"] = min(pred["interval_low"], pred["score"])
            pred["interval_high"] = max(pred["interval_high"], pred["score"])
        data["impact"]["expected_value_lei"] = round(comb * float(data["impact"]["value_if_true_lei"]), 2)
        fac = Factor(feature="bilant_post", label_ro=note[:200], value=round(float(s["excess_kwh_day"]), 2), contribution=round(log_lr, 3)).model_dump(mode="json")
        tf = data["explanation"]["top_factors"]
        data["explanation"]["top_factors"] = ([fac] + tf)[:8]
        data["explanation"]["summary_ro"] = f"{data['explanation']['summary_ro']} {note}"
        if RESOLVE_ABSTAIN and pred.get("abstain") and log_lr >= RESOLVE_ABSTAIN_LOG_LR:
            pred["abstain"] = False
            pred["abstain_reason"] = None
            pred["confidence"] = "medium"
            data["recommended_action"] = "remote_reading"
            data["effort"]["duration_min"] = min(int(data["effort"]["duration_min"]), 10)
            data["explanation"]["summary_ro"] += " Bilanțul rezolvă îndoiala: întâi citire la distanță, fără verificare umană."
            data["extra"]["fusion_resolved_abstain"] = True
        data["extra"]["fusion"] = fusion.model_dump(mode="json")
        data["extra"]["fusion_approx_post"] = approx
        out.append(WorkItem.model_validate(data))
    return out
