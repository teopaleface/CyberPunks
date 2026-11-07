"""Regulile scrise în cod care transformă predicția în acțiune recomandată, cu valoarea în lei.

Modelul estimează tensiunea maximă și P(> 1,10 pu). Codul de aici decide ce recomandă. Planificatorul decide
final (echipe, praguri de cost). Fiecare regulă are un `rule_id`, scris în `extra.rule_id`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from cyberpunks.common.config import load

LIMIT_PU = 1.10
TAP_STEP_PU = 0.025  # o treaptă a comutatorului: 2,5%

# Ipoteze pentru valoare. Sursele sau eticheta IPOTEZĂ; cerute în config/economics.yaml (status, cereri).
ASSUMPTIONS = {
    "complaint_compensation_lei": 70.0,  # Ord. ANRE 46/2021, anexa 4: reclamație întemeiată, persoană fizică
    "complaint_rate_season": 0.10,  # IPOTEZĂ: un prosumator din 10 reclamă într-un sezon cu opriri dese
    "pv_season_end": (9, 30),  # IPOTEZĂ: după 30 sept. opririle devin rare (vezi rata lunară din simulare)
    "pv_season_start": (3, 1),  # IPOTEZĂ
    "sunny_day_fraction": 0.65,  # IPOTEZĂ: zile cu soare ca ziua țintă în sezon
    "min_horizon_days": 10,  # IPOTEZĂ: chiar în afara sezonului mai sunt câteva zile senine
    "notify_shift_share": 0.15,  # IPOTEZĂ: cât din kWh pierduți se salvează dacă prosumatorii mută consumul la prânz
    "complaint_full_season_days": 60,  # IPOTEZĂ: reclamațiile apar după câteva săptămâni de opriri dese
    "notify_min_p_season": 0.05,  # IPOTEZĂ: în martie-octombrie un mesaj costă puțin și consumul mutat ajută
    "notify_min_p_off_season": 0.2,  # IPOTEZĂ: în afara sezonului, fără mesaje la risc mic (oboseala clienților)
}
ORE_SMART = "PPC Ore Smart+: preț redus zilnic 11:00-14:59 între 1 martie și 31 octombrie"


def economics() -> dict:
    cfg = load("economics")
    v = dict(cfg.get("voltage", {}))
    v.setdefault("tap_change_visit_cost_lei", 450.0)
    v.setdefault("measurement_campaign_cost_lei", 300.0)
    v.setdefault("lost_pv_value_lei_per_kwh", 0.40)
    v.setdefault("planned_outage_hours", 1.0)
    v.setdefault("complaint_compensation_lei", ASSUMPTIONS["complaint_compensation_lei"])
    v["cost_per_customer_hour_lei"] = float(cfg.get("storm", {}).get("cost_per_customer_hour_lei", 12.0))
    v["planned_notice_working_days_lv"] = int(cfg.get("outages", {}).get("planned_notice_working_days_lv", 2))
    return v


def tap_cost_lei(n_customers: int, eco: dict | None = None) -> float:
    """Costul schimbării prizei: vizita echipei plus întreruperea planificată (clienți × ore × lei pe client-oră)."""
    eco = eco or economics()
    return eco["tap_change_visit_cost_lei"] + n_customers * eco["planned_outage_hours"] * eco["cost_per_customer_hour_lei"]


def add_working_days(d: date, n: int) -> date:
    """d plus n zile lucrătoare (fără weekend și sărbători legale), pentru preavizul întreruperii planificate."""
    from cyberpunks.c_prosumatori.profiles import is_free_day

    out, k = d, 0
    while k < n:
        out = out + timedelta(days=1)
        if not is_free_day(out):
            k += 1
    return out


def season_horizon_days(d: date) -> int:
    """Câte zile cu soare mai sunt în sezonul PV de la data țintă (IPOTEZĂ, vezi ASSUMPTIONS)."""
    m_end, d_end = ASSUMPTIONS["pv_season_end"]
    m_st, d_st = ASSUMPTIONS["pv_season_start"]
    start, end = date(d.year, m_st, d_st), date(d.year, m_end, d_end)
    if start <= d <= end:
        days = (end - d).days
    else:
        days = 0
    return max(int(days * ASSUMPTIONS["sunny_day_fraction"]), ASSUMPTIONS["min_horizon_days"])


def in_ore_smart_season(d: date) -> bool:
    return 3 <= d.month <= 10


@dataclass
class Decision:
    action: str
    rule_id: str
    reason_ro: str
    value_if_true_lei: float
    duration_min: int
    crew_size: int
    requires_outage: bool
    abstain: bool = False
    abstain_reason: str | None = None
    investment_flag: bool = False


def decide(
    *,
    p: float,
    q10: float,
    q50: float,
    q90: float,
    lost_kwh: float,
    n_prosumers: int,
    n_customers: int,
    tap_pos: int,
    q50_after_tap: float,
    target: date,
    issues_block: list[str],
    ood_reasons: list[str],
    weather_uncertain: bool,
) -> Decision | None:
    """Acțiunea recomandată pentru un post. None = nicio lucrare (risc neglijabil)."""
    eco = economics()
    horizon = season_horizon_days(target)
    lost_value = lost_kwh * horizon * eco["lost_pv_value_lei_per_kwh"]
    season_share = min(1.0, horizon / ASSUMPTIONS["complaint_full_season_days"])
    complaints = n_prosumers * ASSUMPTIONS["complaint_rate_season"] * season_share * eco["complaint_compensation_lei"]
    value_fix = round(lost_value + complaints, 2)
    measure_ok = p * value_fix >= eco["measurement_campaign_cost_lei"]

    if issues_block:
        return Decision("human_review", "C-R1-INTRARE-GRESITA", "Datele postului sunt greșite: " + "; ".join(issues_block),
                        0.0, 30, 1, False, True, "date de intrare greșite: " + "; ".join(issues_block))
    if ood_reasons:
        return Decision("human_review", "C-R2-RETEA-NOUA",
                        "Postul iese din plaja rețelelor pe care a învățat modelul: " + "; ".join(ood_reasons),
                        value_fix, 30, 1, False, True, "rețea în afara datelor de antrenare: " + "; ".join(ood_reasons))
    near = q10 <= LIMIT_PU <= q90
    if weather_uncertain and near and 0.2 <= p < 0.8:
        return Decision("human_review", "C-R3-PROGNOZA-INCERTA",
                        "Prognoza meteo e nesigură, iar intervalul tensiunii trece peste limită: decide un om.",
                        value_fix, 30, 1, False, True, "prognoză meteo nesigură și interval care trece peste 1,10 pu")
    if p >= 0.5 and q50 > LIMIT_PU:
        if tap_pos >= 2:
            return Decision("measurement_campaign", "C-R5-PRIZA-LA-CAPAT",
                            "Priza e deja la capăt: măsurăm și trecem postul în planul de investiții.",
                            value_fix, 60, 2, False, investment_flag=True)
        cost = tap_cost_lei(n_customers, eco)
        if p * value_fix >= cost:
            enough = q50_after_tap <= LIMIT_PU
            reason = (f"O treaptă de priză coboară tensiunea estimată la {q50_after_tap:.3f} pu".replace(".", ",")
                      + ("." if enough else ", tot peste limită: postul intră și în planul de investiții.")
                      + f" Valoarea în sezon ({value_fix:.0f} lei) acoperă vizita și întreruperea ({cost:.0f} lei);"
                      f" întreruperea se anunță cu {eco['planned_notice_working_days_lv']} zile lucrătoare înainte.")
            return Decision("adjust_tap", "C-R4-PRIZA", reason, value_fix, 120, 3, True, investment_flag=not enough)
        if measure_ok:
            return Decision("measurement_campaign", "C-R6-MASURARE-VALOARE-MICA",
                            f"Depășire probabilă, dar valoarea în sezon ({value_fix:.0f} lei) nu acoperă vizita și întreruperea "
                            f"pentru priză ({cost:.0f} lei): întâi măsurăm 7 zile.", value_fix, 60, 2, False)
    elif (p >= 0.2 or (near and p >= 0.1)) and measure_ok:
        return Decision("measurement_campaign", "C-R7-MASURARE",
                        "Risc real, dar nesigur: un analizor la post 7 zile (Ord. ANRE 46/2021) confirmă sau infirmă.",
                        value_fix, 60, 2, False)
    # mesajele pleacă doar când ajută: în sezon de la 5% risc, în afara lui (noiembrie-februarie) doar la risc real
    notify_min = ASSUMPTIONS["notify_min_p_season"] if in_ore_smart_season(target) else ASSUMPTIONS["notify_min_p_off_season"]
    if p >= notify_min and n_prosumers > 0:
        notify_value = round(lost_kwh * eco["lost_pv_value_lei_per_kwh"] * ASSUMPTIONS["notify_shift_share"] * horizon, 2)
        why = ("Risc mic" if p < 0.2 else "Risc real, dar o vizită nu se justifică în afara sezonului")
        return Decision("notify_customers", "C-R8-MESAJ",
                        f"{why}: mesaj către prosumatorii postului să mute consumul la prânz.", notify_value, 5, 1, False)
    # urmărire: intervalul atinge limita sau riscul nu e neglijabil (IPOTEZĂ: 5%)
    if p >= 0.05 or q90 >= LIMIT_PU:
        return Decision("watchlist", "C-R9-URMARIRE", "Aproape de limită, fără vizită: postul rămâne urmărit.", 0.0, 5, 1, False)
    return None


# Efortul pentru acțiunea principală aleasă din scara de soluții: (minute, oameni, cere întrerupere planificată, abilitate)
LADDER_EFFORT = {
    "phase_rebalance": (90, 3, True, "lv_grid"),  # cele 3 case mutate rămân fără curent cel mult o jumătate de oră
    "adjust_tap": (120, 3, True, "lv_grid"),
    "export_limit": (30, 1, False, "lv_grid"),  # setare la invertoare, de la distanță sau cu o vizită scurtă
    "notify_customers": (5, 1, False, "lv_grid"),
    "offer_battery": (5, 1, False, "lv_grid"),
    "transformer_upgrade": (720, 4, True, "mv_grid"),
    "measurement_campaign": (60, 2, False, "lv_grid"),
}


def needs_ladder(dec: Decision | None, q90: float, phase_evidence: bool = False) -> bool:
    """Scara se calculează pentru posturile la care o echipă ar avea de lucru (P90 peste limită) sau la care bilanțul
    a găsit și dezechilibru pe faze (o soluție ieftină posibilă)."""
    if dec is None or dec.abstain or q90 <= LIMIT_PU:
        return False
    return dec.action in ("adjust_tap", "measurement_campaign") or phase_evidence


def from_ladder(dec: Decision, ladder) -> Decision:
    """Acțiunea principală din scara de soluții (cea mai ieftină combinație care aduce P90 sub 1,10 pu)."""
    act = ladder.principal
    minutes, crew, outage, _ = LADDER_EFFORT.get(act, LADDER_EFFORT["measurement_campaign"])
    return Decision(
        action=act,
        rule_id="C-R10-SCARA-SOLUTII",
        reason_ro=ladder.reason_ro,
        value_if_true_lei=dec.value_if_true_lei,
        duration_min=minutes,
        crew_size=crew,
        requires_outage=outage,
        investment_flag=(not ladder.reaches_target) or "transformer_upgrade" in ladder.choice,
    )


def outage_notice(post_label: str, d_tap: date) -> str:
    """Anunțul întreruperii planificate pentru schimbarea prizei (doar demo: nu se trimite nimic)."""
    from cyberpunks.c_prosumatori.explain import MONTHS_RO

    return (f"Rețele Electrice: pe {d_tap.day} {MONTHS_RO[d_tap.month - 1]} {d_tap.year}, între 10:00 și 11:00, alimentarea din postul "
            f"{post_label} se întrerupe aproximativ o oră pentru reglajul tensiunii. După lucrare, invertoarele "
            "fotovoltaice ar trebui să se oprească mai rar la prânz.")


def customer_message(target: date, n_prosumers: int, window: tuple[int, int]) -> str:
    """Mesajul PPC Energy către prosumatori (doar demo: nu se trimite nimic)."""
    h0, h1 = window
    base = (f"Mâine, între {h0}:00 și {h1}:00, rețeaua din zona dumneavoastră poate avea tensiune mare din cauza "
            "producției solare. Dacă porniți atunci mașina de spălat, boilerul sau încărcați mașina electrică, folosiți "
            "energia produsă de panouri și invertorul are mai puține șanse să se oprească.")
    if in_ore_smart_season(target):
        base += f" Cu {ORE_SMART}, consumul mutat la prânz costă și mai puțin."
    return base
