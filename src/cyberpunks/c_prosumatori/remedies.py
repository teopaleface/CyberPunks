"""Scara de soluții pentru posturile cu tensiune prea mare: fiecare treaptă e simulată pe rețeaua postului.

Pentru un post cu risc și o zi țintă, simularea fizică (aceeași ca la etichete) se rulează pe cele 24 de ore
de bază și apoi cu fiecare soluție. Efectul unei trepte = tensiunea maximă cu soluția − tensiunea maximă de bază.
Se aplică peste P90 al modelului: P90 după soluție = P90 de pornire + efect. Treptele:

1. `phase_rebalance`: trei case monofazate mutate pe faza cea mai puțin încărcată. Simularea e echilibrată, deci
   dezechilibrul se estimează analitic pe sensibilitatea rețelei: ΔU_fază ≈ (R_fază + R_neutru) · I (vezi
   `unbalance_factor`). P90 de pornire al scării include dezechilibrul estimat.
2. `adjust_tap`: priza cu o treaptă mai sus (tensiunea pe JT coboară cu 2,5%), doar pe sezonul de vară.
3. `notify_customers`: mesaj de grup pentru clienții cu contor inteligent de pe post (Ore Smart); participare
   10/20/30% (IPOTEZĂ din config); consumul mutat din seară în orele cu risc, energia rămâne aceeași.
4. `offer_battery`: baterii de 5/10/15 kWh calculate pe profilul fiecărui prosumator; se încarcă doar în orele
   cu risc și se descarcă seara (orele de deficit 18-22). Oferta doar la cei la care bateria ajută postul.
5. `export_limit`: limita de injecție la invertoare, cea mai blândă care aduce P90 sub 1,10 pu.
6. `transformer_upgrade`: post nou (transformator mai mare, rețeaua împărțită în două), intră în investiții.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date
from functools import cache

import numpy as np
import pandas as pd

from cyberpunks.c_prosumatori import actions, grids, posts, profiles, simulate, weather
from cyberpunks.common.config import load

LIMIT = 1.10
MARGIN = 0.002  # P90 după soluție trebuie să fie sub 1,10 − 0,002 pu
A3 = np.exp(2j * np.pi / 3)

# Ipoteze ale firului C (cerute în config; până atunci, implicite)
ASSUMPTIONS = {
    "single_phase_max_kwp": 5.0,  # IPOTEZĂ: casele cu cel mult 5 kWp sunt racordate monofazat
    "neutral_r_ratio": 1.0,  # IPOTEZĂ: neutrul are aceeași secțiune ca faza (R_neutru / R_fază)
    "rebalance_houses": 3,  # din conceptul lui Teo: 3 case mutate pe altă fază
    "shift_kwh_per_household": 2.5,  # IPOTEZĂ: mașina de spălat (circa 1 kWh) plus boilerul (circa 1,5 kWh)
    "evening_hours": (18, 22),  # orele din care se mută consumul (și orele de deficit din aug.-oct. 2026)
    "battery_accept_share": 0.3,  # IPOTEZĂ: ce parte din prosumatorii cărora li se face oferta o acceptă
    "battery_min_effect_pu": 0.0005,  # IPOTEZĂ: oferta merge doar dacă bateria coboară tensiunea postului vizibil
    "battery_max_payback_years": 15.0,  # IPOTEZĂ: peste atât oferta nu e cinstită pentru client
    "battery_margin_share": 0.15,  # IPOTEZĂ: marja PPC Energie din vânzarea bateriei și a montajului
    "battery_eta": 0.9,  # IPOTEZĂ: randamentul dus-întors al bateriei
    "export_caps": (0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3),  # fracții din kWp încercate pentru limita de export
    "upgrade_line_scale": 0.5,  # IPOTEZĂ: postul nou împarte rețeaua în două, drumurile scad la jumătate
    # EN 50160: factorul de dezechilibru al tensiunii ≤ 2% în 95% din timp; o rețea mai dezechilibrată ar fi deja
    # semnalată prin reclamații. Formula analitică (neutru cu aceeași secțiune, fără împământări repetate) dă mai mult.
    "unbalance_cap_pu": 0.02,
}


def cfg() -> dict:
    e = load("economics")
    r = dict(e.get("remedies", {}))
    v = actions.economics()
    r.setdefault("phase_rebalance_cost_lei", 300.0)
    r.setdefault("phase_rebalance_outage_hours", 0.5)
    r.setdefault("notify_participation_rate", 0.2)
    r.setdefault("notify_participation_range", [0.1, 0.2, 0.3])
    r.setdefault("battery_sizes_kwh", [5, 10, 15])
    r.setdefault("battery_price_lei_per_kwh", 1250.0)
    r.setdefault("battery_installation_cost_lei", 2500.0)
    r.setdefault("afm_grant_share", 0.75)
    r.setdefault("afm_grant_cap_lei", 15000.0)
    r.setdefault("afm_min_kwh", 10)
    r.setdefault("battery_offer_cost_lei_per_customer", 2.0)
    r.setdefault("export_limit_cost_lei", 50.0)
    r.setdefault("transformer_upgrade_cost_lei", 80000.0)
    r["retail_price"] = float(e.get("energy", {}).get("retail_price_lei_per_kwh", 1.56))
    r["export_value"] = float(v["lost_pv_value_lei_per_kwh"])
    r["notify_cost"] = float(e.get("voltage", {}).get("notification_cost_lei_per_customer", 0.05))
    r["smart_meter_share"] = float(e.get("meters", {}).get("smart_meter_share_2025", {}).get("muntenia_sud", 0.5881))
    r["customer_hour"] = v["cost_per_customer_hour_lei"]
    return r


# ------------------------------------------------------------------------------------------------
# intrările unei zile și simularea unei variante
# ------------------------------------------------------------------------------------------------


@dataclass
class Day:
    d: date
    wx: pd.DataFrame
    shapes: pd.DataFrame
    sysload: np.ndarray
    hour: np.ndarray  # ora locală (începutul orei), 0..23


def day_inputs(d: date, wx: pd.DataFrame) -> Day:
    loc = wx.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)
    return Day(d=d, wx=wx, shapes=profiles.shapes_for(wx.index), sysload=profiles.system_load_index(wx.index), hour=loc.hour.to_numpy())


@dataclass
class Sim:
    vmax_h: np.ndarray
    trips_h: np.ndarray
    lost_h: np.ndarray
    curtailed_h: np.ndarray
    detail: dict = field(repr=False, default_factory=dict)

    @property
    def vmax(self) -> float:
        return float(self.vmax_h.max())

    @property
    def trips(self) -> float:
        return float(self.trips_h.sum())


def run_sim(post: grids.Post, day: Day, vm: np.ndarray | None = None, **kw) -> Sim:
    r = simulate.simulate_post(post, day.wx, day.shapes, day.sysload, vm=vm, detail=True, **kw)
    return Sim(r["hourly"]["vmax"].to_numpy(dtype=float), r["trips"], r["lost_h"] if "lost_h" in r else r["hourly"]["lost_kwh"].to_numpy(),
               r["curtailed_kwh"], r)


@cache
def get_post(post_id: str) -> grids.Post:
    return posts.build_post(post_id)


def _lv_maps(post: grids.Post) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = post.model
    R = m.Zll.real[np.ix_(m.lv_pos, m.lv_pos)] / m.base_mva
    lv_index = {int(b): i for i, b in enumerate(m.lv_bus)}
    pv_lv = np.array([lv_index[int(b)] for b in post.pv_bus], dtype=int)
    ld_lv = np.array([lv_index[int(b)] for b in post.load_bus], dtype=int)
    return R, pv_lv, ld_lv


def risk_window(base: Sim, day: Day) -> list[int]:
    hrs = [int(h) for h, v in zip(day.hour, base.vmax_h, strict=True) if v > LIMIT - 0.01]
    if not hrs:
        k = int(np.argmax(base.vmax_h))
        hrs = [int(day.hour[k])]
    return list(range(min(hrs), max(hrs) + 1))


def fmt_window(hrs: list[int]) -> str:
    return f"{min(hrs):02d}:00-{max(hrs) + 1:02d}:00"


# ------------------------------------------------------------------------------------------------
# treapta 1: dezechilibrul pe faze (aproximare analitică documentată)
# ------------------------------------------------------------------------------------------------


def unbalance_factor(w: np.ndarray, rho: float | None = None) -> float:
    """Cât de mult crește tensiunea pe faza cea mai încărcată față de cazul echilibrat, pentru aceleași injecții.

    Pe o plecare cu patru conductoare, cu injecții monofazate cu ponderile w pe faze (ponderate cu rezistența):
    ΔU_fază_max / ΔU_echilibrat ≈ 3·max(s) + 3·ρ·|s_a + s_b·a + s_c·a²|, s = w / Σw, ρ = R_neutru / R_fază.
    Echilibrat: 1. Tot pe o fază: 3 + 3ρ (6 la neutru egal cu faza).
    """
    rho = ASSUMPTIONS["neutral_r_ratio"] if rho is None else rho
    tot = float(np.sum(w))
    if tot <= 0:
        return 1.0
    s = np.asarray(w, dtype=float) / tot
    return float(3 * s.max() + 3 * rho * abs(s[0] + s[1] * A3 + s[2] * A3**2))


def phase_unbalance(post: grids.Post, base: Sim) -> dict:
    """Excesul de tensiune din dezechilibru (fazele caselor monofazate atribuite la întâmplare) și după mutarea a 3 case."""
    k_peak = int(np.argmax(base.vmax_h))
    R, pv_lv, _ = _lv_maps(post)
    det = base.detail
    if not len(post.pv_bus):
        return {"before": 0.0, "after": 0.0, "moved": 0, "n_single": 0}
    net = det["pv"][:, k_peak] - det["bat"][:, k_peak] - det["load"][post.pv_load, k_peak]  # kW
    net = np.maximum(net, 0.0) / 1000.0  # MW exportați
    single = post.pv_kwp <= ASSUMPTIONS["single_phase_max_kwp"]
    j = int(np.argmax(det["vlv"][:, k_peak]))
    contrib = R[j, pv_lv] * net  # pu, contribuția fiecărui panou la creșterea tensiunii în nodul cel mai expus
    rng = np.random.default_rng(post.spec.seed + 7)
    phase = rng.integers(0, 3, len(post.pv_bus))
    idx = np.flatnonzero(single & (contrib > 0))
    dv_single = float(contrib[idx].sum())
    if len(idx) < 2 or dv_single <= 0:
        return {"before": 0.0, "after": 0.0, "moved": 0, "n_single": int(single.sum())}

    def excess(ph: np.ndarray) -> float:
        w = np.array([contrib[idx][ph[idx] == p].sum() for p in range(3)])
        return (unbalance_factor(w) - 1.0) * dv_single

    raw_before = excess(phase)
    ph = phase.copy()
    moved = 0
    for _ in range(ASSUMPTIONS["rebalance_houses"]):
        best = (excess(ph), None, None)
        for k in idx:
            for target in range(3):
                if target == ph[k]:
                    continue
                trial = ph.copy()
                trial[k] = target
                e = excess(trial)
                if e < best[0] - 1e-9:
                    best = (e, k, target)
        if best[1] is None:
            break
        ph[best[1]] = best[2]
        moved += 1
    raw_after = excess(ph)
    scale = min(1.0, ASSUMPTIONS["unbalance_cap_pu"] / raw_before) if raw_before > 0 else 1.0
    return {"before": float(raw_before * scale), "after": float(raw_after * scale), "moved": moved, "n_single": int(single.sum()),
            "raw_before": float(raw_before), "capped": scale < 1.0}


def shift_profile(load: np.ndarray, risk: np.ndarray, eve: np.ndarray, kwh: float) -> np.ndarray:
    """Consumul mutat din seară în orele cu risc, pe casă: aceeași energie scoasă și adăugată (cel mult cât consumă
    casa seara), scoasă proporțional cu consumul de seară, deci consumul nu devine negativ. load: (case, ore) în kW."""
    risk_idx, eve_idx = np.flatnonzero(risk & ~eve), np.flatnonzero(eve & ~risk)
    out = np.zeros_like(load, dtype=float)
    if not len(risk_idx) or not len(eve_idx):
        return out
    eve_load = load[:, eve_idx]
    avail = eve_load.sum(axis=1)
    e = np.minimum(kwh, avail)
    share = np.divide(eve_load, avail[:, None], out=np.zeros_like(eve_load, dtype=float), where=avail[:, None] > 0)
    out[:, eve_idx] -= e[:, None] * share
    out[:, risk_idx] += (e / len(risk_idx))[:, None]
    return out


# ------------------------------------------------------------------------------------------------
# treapta 4: bateria pe profilul fiecărui prosumator
# ------------------------------------------------------------------------------------------------


@cache
def _year_inputs(year: int = 2025) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    wx = weather.archive()
    wx = wx[(wx.index >= f"{year}-01-01") & (wx.index < f"{year + 1}-01-01")]
    loc = wx.index.tz_convert(profiles.TZ) - pd.Timedelta(hours=1)
    return wx, profiles.shapes_for(wx.index), np.array([d.toordinal() for d in loc.date]) * 100 + loc.hour.to_numpy()


def battery_profiles(post: grids.Post, day: Day, base: Sim, hours: list[int], c: dict) -> pd.DataFrame:
    """Pentru fiecare prosumator fără baterie: variantele 5/10/15 kWh pe profilul lui (anul 2025 și ziua țintă)."""
    if not len(post.pv_bus):
        return pd.DataFrame()
    R, pv_lv, _ = _lv_maps(post)
    det = base.detail
    k_peak = int(np.argmax(base.vmax_h))
    j = int(np.argmax(det["vlv"][:, k_peak]))
    risk = np.isin(day.hour, hours)
    surplus_day = det["pv"] - det["load"][post.pv_load]  # kW pe oră, ziua țintă
    # anul 2025 pe profilul fiecărui prosumator (aceeași producție și același consum ca în simulare)
    wx, shapes, keys = _year_inputs()
    pvk = weather.pv_per_kwp(wx["gti"].to_numpy(), wx["temp"].to_numpy())
    pv_y = np.minimum(post.pv_kwp[:, None] * post.pv_orient[:, None] * pvk[None, :], post.pv_ac_kw[:, None])
    load_y = post.load_annual_kwh[post.pv_load][:, None] * shapes[list(post.load_profile[post.pv_load])].to_numpy().T
    hour_y = keys % 100
    day_y = keys // 100
    starts = np.flatnonzero(np.r_[True, day_y[1:] != day_y[:-1]])
    noon_y = (hour_y >= 10) & (hour_y < 16)
    eve_y = (hour_y >= 17) | (hour_y < 1)
    rows = []
    eta = ASSUMPTIONS["battery_eta"]
    for i in range(len(post.pv_bus)):
        if post.bat_kwh[i] > 0 or not post.load_is_house[post.pv_load[i]]:
            continue
        sur_y = pv_y[i] - load_y[i]
        n_risk = max(int(risk.sum()), 1)
        for size in c["battery_sizes_kwh"]:
            # puterea de încărcare repartizată pe orele cu risc, ca bateria să nu fie plină înainte de vârf
            p_kw = float(min(np.clip(size / 2.0, 2.5, 5.0), size / n_risk))
            # pe an, oră cu oră: încărcarea limitată de putere și de capacitate, descărcarea limitată de putere
            charge = np.minimum(np.add.reduceat(np.where(noon_y, np.minimum(np.maximum(sur_y, 0), p_kw), 0.0), starts), size)
            need = np.add.reduceat(np.where(eve_y, np.minimum(np.maximum(-sur_y, 0), p_kw), 0.0), starts)
            delivered = np.minimum(charge * eta, need)  # kWh pe zi livrați seara
            # energia absorbită în orele cu risc din ziua țintă (limitată de putere și de capacitate)
            absorbed = float(min(np.minimum(np.maximum(surplus_day[i][risk], 0), p_kw).sum(), size))
            peak_abs = float(min(max(surplus_day[i][k_peak], 0.0), p_kw))
            dv = float(R[j, pv_lv[i]] * peak_abs / 1000.0)
            shifted = float(delivered.sum())  # kWh pe an livrați seara
            # economia: energia livrată seara la prețul de cumpărare minus energia PV folosită la încărcare,
            # care altfel ar fi fost injectată (cu pierderile bateriei)
            saving = shifted * c["retail_price"] - (shifted / eta) * c["export_value"]
            cost = size * c["battery_price_lei_per_kwh"] + c["battery_installation_cost_lei"]
            grant = min(c["afm_grant_share"] * cost, c["afm_grant_cap_lei"]) if size >= c["afm_min_kwh"] else 0.0
            payback = (cost - grant) / saving if saving > 0 else float("inf")
            rows.append({
                "post_id": post.spec.post_id, "prosumer": f"{post.spec.post_id}-P{i + 1:02d}", "pv_index": i,
                "kwp": float(post.pv_kwp[i]), "size_kwh": size, "power_kw": p_kw,
                "noon_kwh_absorbed": round(absorbed, 2), "dv_peak_pu": dv, "shifted_kwh_year": round(float(shifted), 0),
                "saving_lei_year": round(float(saving), 0), "cost_lei": cost, "grant_lei": round(grant, 0),
                "payback_years": round(float(payback), 1), "revenue_lei": round(cost * ASSUMPTIONS["battery_margin_share"], 0),
            })
    return pd.DataFrame(rows)


def pick_battery_offers(prof: pd.DataFrame) -> pd.DataFrame:
    """Pentru fiecare prosumator, mărimea cu cea mai scurtă recuperare; oferta doar dacă bateria ajută postul."""
    if prof.empty:
        return prof
    ok = prof[(prof.dv_peak_pu >= ASSUMPTIONS["battery_min_effect_pu"]) & (prof.payback_years <= ASSUMPTIONS["battery_max_payback_years"])]
    if ok.empty:
        return ok
    best = ok.sort_values(["prosumer", "payback_years", "dv_peak_pu"], ascending=[True, True, False]).groupby("prosumer").head(1)
    return best.sort_values(["dv_peak_pu", "revenue_lei"], ascending=False).reset_index(drop=True)


# ------------------------------------------------------------------------------------------------
# scara completă pentru un post
# ------------------------------------------------------------------------------------------------


@dataclass
class Ladder:
    post_id: str
    base_vmax_sim: float
    p90_model: float
    unbalance: dict
    p90_start: float
    options: list[dict]
    choice: list[str]
    principal: str
    reason_ro: str
    hours: list[int]
    base_trips: float
    battery_offers: pd.DataFrame = field(repr=False, default_factory=pd.DataFrame)
    reaches_target: bool = True


def _opt(action: str, cost: float, p90_start: float, effect: float, confidence: str, duration: int, crew: bool, note: str,
         skill: str | None = "lv_grid", combinable: bool = True, **extra) -> dict:
    o = {
        "action": action, "cost_lei": round(max(cost, 0.0), 2), "p90_after_pu": round(p90_start + effect, 4),
        "effect_pu": round(effect, 4), "confidence": confidence, "duration_min": int(duration), "needs_crew": crew,
        "crew_skill": skill if crew else None, "combinable": combinable, "note_ro": note,
    }
    o.update({k: v for k, v in extra.items() if v is not None})
    return o


def build_ladder(post_id: str, day: Day, p90_model: float, n_customers: int, horizon_days: int) -> Ladder:
    c = cfg()
    post = get_post(post_id)
    spec = post.spec
    base = run_sim(post, day)
    vm = base.detail["vm"]
    hours = risk_window(base, day)
    unb = phase_unbalance(post, base)
    p90_start = p90_model + unb["before"]
    opts: list[dict] = []

    # 1. faze
    eff = unb["after"] - unb["before"]
    cost = c["phase_rebalance_cost_lei"] + ASSUMPTIONS["rebalance_houses"] * c["phase_rebalance_outage_hours"] * c["customer_hour"]
    note = (f"Casele cu cel mult {ASSUMPTIONS['single_phase_max_kwp']:.0f} kWp sunt monofazate (IPOTEZĂ); cu fazele atribuite la întâmplare, "
            f"faza cea mai încărcată are cu {unb['before']:.4f} pu mai mult decât calculul echilibrat; mutarea a {unb['moved']} case "
            f"îl reduce la {unb['after']:.4f} pu. Aproximare analitică ΔU ≈ (R_fază + R_neutru)·I pe sensibilitatea rețelei; "
            "bilanțul pe post poate confirma fazele reale.")
    opts.append(_opt("phase_rebalance", cost, p90_start, eff, "low", 90, True, note))

    # 2. priza (o treaptă), echivalent cu tensiunea pe MT împărțită la raportul treptelor
    if spec.tap_pos < 2:
        k = (1 + 0.025 * spec.tap_pos) / (1 + 0.025 * (spec.tap_pos + 1))
        tap = run_sim(post, day, vm=vm * k)
        eff = tap.vmax - base.vmax
        winter = _winter_vmin(post_id)
        wnote = "" if winter is None else (
            f" Iarna seara tensiunea minimă ar coborî la {winter - 0.025:.3f} pu" + (", sub 0,90: priza revine în octombrie." if winter - 0.025 < 0.90 else
                                                                                      ", peste 0,90: priza poate rămâne și iarna."))
        opts.append(_opt("adjust_tap", actions.tap_cost_lei(n_customers), p90_start, eff, "high", 120, True,
                         f"Priza de la {spec.tap_pos:+d} la {spec.tap_pos + 1:+d} (vara). Cere oprirea postului circa o oră, anunțată cu 2 zile lucrătoare "
                         f"înainte; costul include întreruperea ({n_customers} clienți × 1 h × {c['customer_hour']:.0f} lei).{wnote}",
                         inverter_trips_avoided=round(max(base.trips - tap.trips, 0.0), 1)))

    # 3. mesaje de grup (consum mutat din seară în orele cu risc)
    houses = np.flatnonzero(post.load_is_house)
    targeted = round(len(houses) * c["smart_meter_share"])
    risk = np.isin(day.hour, hours)
    eve = (day.hour >= ASSUMPTIONS["evening_hours"][0]) & (day.hour < ASSUMPTIONS["evening_hours"][1])
    res_rate = {}
    base_load = base.detail["load"][houses]  # kW pe oră, consumul fiecărei case în ziua țintă
    for rate in c["notify_participation_range"]:
        extra = np.zeros((len(post.load_bus), len(day.hour)))
        extra[houses] = shift_profile(base_load, risk, eve, ASSUMPTIONS["shift_kwh_per_household"] * rate * c["smart_meter_share"])
        s = run_sim(post, day, vm=vm, extra_load=extra)
        res_rate[rate] = (s.vmax - base.vmax, max(base.trips - s.trips, 0.0))
    r_min = min(c["notify_participation_range"])
    r_mid = c["notify_participation_rate"]
    eff_min, trips_min = res_rate[r_min]
    _eff_mid, trips_mid = res_rate.get(r_mid, res_rate[r_min])
    window = fmt_window(hours)
    msg = (f"Mâine între {min(hours)} și {max(hours) + 1}, panourile solare de pe strada ta se pot opri de circa {base.trips:.0f} ori din cauza "
           f"tensiunii mari. Dacă 1 din {round(1 / r_mid)} vecini pornește atunci mașina de spălat și boilerul, se evită circa {trips_mid:.0f} opriri.")
    if actions.in_ore_smart_season(day.d):
        msg += " Cu PPC Ore Smart+, consumul de la prânz costă mai puțin."
    note = (f"Participare simulată 10/20/30% din cei {targeted} clienți cu contor inteligent (IPOTEZĂ): tensiunea scade cu "
            + "/".join(f"{abs(res_rate[r][0]):.4f}" for r in sorted(res_rate)) + " pu, opriri evitate "
            + "/".join(f"{res_rate[r][1]:.0f}" for r in sorted(res_rate)) + f". P90 după soluție e calculat la participarea minimă ({r_min:.0%}).")
    opts.append(_opt("notify_customers", c["notify_cost"] * targeted, p90_start, eff_min, "low", 0, False, note, skill=None,
                     participation_rate=r_min, risk_hours=[window], inverter_trips_avoided=round(trips_min, 1),
                     message_preview_ro=msg, customers_targeted=targeted))

    # 4. baterii pe profil, doar unde ajută postul
    prof = battery_profiles(post, day, base, hours, c)
    offers = pick_battery_offers(prof)
    if not offers.empty:
        n_acc = max(1, round(len(offers) * ASSUMPTIONS["battery_accept_share"]))
        acc = offers.head(n_acc)
        bkwh, bkw = post.bat_kwh.copy(), post.bat_kw.copy()
        bkwh[acc.pv_index.to_numpy()] = acc.size_kwh.to_numpy(dtype=float)
        bkw[acc.pv_index.to_numpy()] = acc.power_kw.to_numpy(dtype=float)
        allow = risk  # se încarcă doar în orele cu risc, cu puterea repartizată pe ele
        s = run_sim(post, day, vm=vm, bat_kwh=bkwh, bat_kw=bkw, bat_allow_charge=allow)
        opts.append(_opt("offer_battery", c["battery_offer_cost_lei_per_customer"] * len(offers), p90_start, s.vmax - base.vmax, "low", 0, False,
                         f"Ofertă la {len(offers)} prosumatori la care bateria ajută postul; simulat cu {n_acc} care acceptă ({ASSUMPTIONS['battery_accept_share']:.0%}, "
                         "IPOTEZĂ). Bateria se încarcă în orele cu risc și se descarcă seara, în orele de deficit 18-22. "
                         "Casa Verde Baterii 2026: grant de până la 75%, cel mult 15.000 lei, de la 10 kWh. Canal: magazinele PPC și Flanco.",
                         skill=None, battery_kwh_total=float(acc.size_kwh.sum()), revenue_lei=float(acc.revenue_lei.sum()),
                         payback_years=float(acc.payback_years.median()), customers_targeted=len(offers),
                         inverter_trips_avoided=round(max(base.trips - s.trips, 0.0), 1)))

    # 5. limita de export: cea mai blândă care aduce P90 sub limită
    if len(post.pv_bus):
        chosen = None
        for cap in ASSUMPTIONS["export_caps"]:
            s = run_sim(post, day, vm=vm, export_cap_kw=post.pv_kwp * cap)
            chosen = (cap, s)
            if p90_start + (s.vmax - base.vmax) < LIMIT - MARGIN:
                break
        cap, s = chosen
        curtailed = float(s.curtailed_h.sum())
        cost = c["export_limit_cost_lei"] * len(post.pv_bus) + curtailed * horizon_days * c["export_value"]
        opts.append(_opt("export_limit", cost, p90_start, s.vmax - base.vmax, "medium", 0, False,
                         f"Injecția limitată la {cap:.0%} din puterea instalată, la toți cei {len(post.pv_bus)} prosumatori: {curtailed:.0f} kWh "
                         f"neinjectați în ziua țintă; costul include energia pierdută pe {horizon_days} zile de sezon (IPOTEZĂ).",
                         skill=None, inverter_trips_avoided=round(max(base.trips - s.trips, 0.0), 1)))

    # 6. post nou: transformator mai mare, rețeaua împărțită în două
    up = copy.deepcopy(spec)
    bigger = [k for k in sorted(grids.TRAFO_TYPES) if k > spec.kva]
    up.kva = bigger[0] if bigger else spec.kva
    up.line_scale = spec.line_scale * ASSUMPTIONS["upgrade_line_scale"]
    s = run_sim(grids.build_post(up), day, vm=vm)
    opts.append(_opt("transformer_upgrade", c["transformer_upgrade_cost_lei"], p90_start, s.vmax - base.vmax, "high", 720, True,
                     f"Post nou: transformator de {up.kva} kVA și rețeaua împărțită în două (drumuri pe jumătate, IPOTEZĂ). "
                     "Intră în raportul de investiții; durează săptămâni, nu o zi.", skill="mv_grid"))

    choice, reason, reaches = choose(opts, p90_start)
    principal = next((a for a in ("adjust_tap", "phase_rebalance", "export_limit", "transformer_upgrade") if a in choice), choice[0])
    return Ladder(post_id, base.vmax, p90_model, unb, p90_start, opts, choice, principal, reason, hours, base.trips, offers, reaches)


ACTION_RO = {
    "phase_rebalance": "3 case mutate pe altă fază",
    "adjust_tap": "o treaptă de priză",
    "notify_customers": "mesaje de grup",
    "offer_battery": "oferte de baterii",
    "export_limit": "limita de export",
    "transformer_upgrade": "post nou",
    "measurement_campaign": "măsurători",
}


def _ro(acts: list[str]) -> str:
    return " + ".join(ACTION_RO.get(a, a) for a in acts)


def _pu(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def choose(opts: list[dict], p90_start: float) -> tuple[list[str], str, bool]:
    """Cea mai ieftină soluție sau combinație (până la 3 trepte) care aduce P90 sub 1,10 pu, cu măcar o treaptă de
    încredere medie sau mare. Efectele combinate se adună (aproximare liniară). Dacă nimic nu ajunge, varianta care
    coboară cel mai mult tensiunea, cu postul trecut în investiții."""
    from itertools import combinations

    target = LIMIT - MARGIN
    comb = [o for o in opts if o["combinable"]]
    cands = []
    for r in (1, 2, 3):
        for group in combinations(comb, r):
            if all(o["confidence"] == "low" for o in group):
                continue
            p = p90_start + sum(o["effect_pu"] for o in group)
            cands.append((sum(o["cost_lei"] for o in group), [o["action"] for o in group], p))
    ok = sorted([c for c in cands if c[2] < target], key=lambda c: (c[0], c[2]))
    cheaper = sorted(opts, key=lambda o: o["cost_lei"])
    if ok:
        cost, acts, p = ok[0]
        skipped = [o for o in cheaper if o["cost_lei"] < cost and o["action"] not in acts]
        why = "; ".join(_why_not(o, target) for o in skipped[:3])
        head = f"Soluția aleasă: {_ro(acts)} ({cost:.0f} lei), P90 după: {_pu(p)} pu" + (" (efecte adunate, aproximare)." if len(acts) > 1 else ".")
        return acts, head + (f" Mai ieftine, dar nu ajung: {why}." if why else ""), True
    if not cands:
        return ["measurement_campaign"], "Nicio treaptă nu are efect sigur: întâi măsurători, apoi decide un om.", False
    cost, acts, p = min(cands, key=lambda c: (round(c[2], 3), c[0]))
    return acts, (f"Nicio combinație nu aduce P90 sub 1,10 pu; cea mai bună, {_ro(acts)} ({cost:.0f} lei), îl coboară la "
                  f"{_pu(p)} pu. Postul intră prioritar în planul de investiții (cablu mai gros sau post nou)."), False


def _why_not(o: dict, target: float) -> str:
    name = ACTION_RO.get(o["action"], o["action"])
    if o["p90_after_pu"] >= target:
        return f"{name} lasă P90 la {_pu(o['p90_after_pu'])} pu"
    return f"{name} are efect nesigur (încredere mică)"


@cache
def _winter_vmin(post_id: str) -> float | None:
    """Tensiunea minimă din simularea anuală a postului (dacă există), pentru verificarea prizei iarna."""
    from cyberpunks.common.paths import DATA_PROCESSED

    p = DATA_PROCESSED / "C" / "population" / "hourly" / f"{post_id}.parquet"
    if not p.exists():
        return None
    return float(pd.read_parquet(p, columns=["vmin"])["vmin"].min())
