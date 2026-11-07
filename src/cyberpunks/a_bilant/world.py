"""Lumea simulată a bilanțului: un post de transformare, clienții lui, contorul de bilanț și problemele ascunse.

SIMULARE pe date publice, gândită pentru datele PPC. Pentru fiecare oră:
- consumul caselor și al firmelor mici (profile SimBench, consum anual românesc), producția panourilor (meteo
  Open-Meteo) și bateriile, exact ca în firul C (`cyberpunks.c_prosumatori`, folosit prin import);
- calculul de rețea vectorizat al lui C dă tensiunile; din ele calculăm curentul și pierderile pe fiecare cablu
  (|I|² R), adică pierderea tehnică normală a postului;
- corecția pentru faze (calculul lui C e echilibrat; casele sunt monofazate, iar fazele nu sunt perfect egale):
  factorul din `docs/research/bilant_faze.md`;
- consumul propriu al contoarelor (nemăsurat, IPOTEZĂ 1,5 W pe contor);
- contorul de bilanț al postului (pe joasă tensiune, clasa 0,5S, eroare mică fixă) și contoarele clienților
  (clasa 1, eroare mică fixă pe contor, goluri de comunicație);
- problemele ascunse de noi, etichetate din construcție (vezi `problems.py`).

Totul e determinist: aceeași specificație și același seed dau exact aceleași cifre.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from cyberpunks.a_bilant import problems as P
from cyberpunks.c_prosumatori import grids, profiles, weather
from cyberpunks.c_prosumatori.simulate import battery_dispatch, mv_voltage

TZ = profiles.TZ
PERIOD = ("2024-07-01", "2025-07-08")  # zile locale, inclusiv; 2025-07-08 e ziua demo (config/scenarios.yaml)

# Parametri de măsurare și pierderi mici. IPOTEZĂ, cu motivul în docs/data/bilant.md.
METER_OWN_W = 1.5  # consumul propriu al unui contor electronic, nemăsurat (IEC 62053-21 permite până la 2 W)
CUSTOMER_METER_SD = 0.004  # eroarea fixă a unui contor de client (clasa 1: ±1% la limită)
BALANCE_METER_SD = 0.002  # eroarea fixă a contorului de bilanț (clasa 0,5S cu transformatoare de curent)
VOLTAGE_NOISE_PU = 0.002  # zgomotul măsurării de tensiune în contor (±0,5%)
GAP_METER_SHARE = 0.03  # ce parte din contoare au episoade de goluri de comunicație
# Fazele: calculul lui C e echilibrat. Pierderea reală = pierderea echilibrată × SINGLE_PHASE_FACTOR × (1 + PHASE_K·u²),
# u = dezechilibrul de faze (sarcina fazei celei mai încărcate / media − 1). Valorile vin din docs/research/bilant_faze.md.
SINGLE_PHASE_FACTOR = 1.25
PHASE_K = 1.5


@dataclass
class Weather:
    """Meteo și profile pe perioada simulată (orar, UTC, ora care se încheie)."""

    index: pd.DatetimeIndex
    gti: np.ndarray
    temp: np.ndarray
    shapes: pd.DataFrame
    sysload: np.ndarray
    local_day: np.ndarray  # indexul zilei locale (0..D-1) pentru fiecare oră
    days: pd.DatetimeIndex  # zilele locale

    @property
    def T(self) -> int:
        return len(self.index)

    @property
    def D(self) -> int:
        return len(self.days)


def load_weather(period: tuple[str, str] = PERIOD) -> Weather:
    wx = weather.archive("2023-01-01", "2026-11-06")
    loc_start = wx.index.tz_convert(TZ) - pd.Timedelta(hours=1)
    d = pd.DatetimeIndex(loc_start.date)
    sel = (d >= pd.Timestamp(period[0])) & (d <= pd.Timestamp(period[1]))
    wx = wx[sel]
    d = d[sel]
    days = pd.DatetimeIndex(sorted(set(d)))
    day_idx = days.get_indexer(d)
    return Weather(
        index=wx.index,
        gti=wx["gti"].to_numpy(),
        temp=wx["temp"].to_numpy(),
        shapes=profiles.shapes_for(wx.index),
        sysload=profiles.system_load_index(wx.index),
        local_day=day_idx,
        days=days,
    )


def _ar1(rng: np.random.Generator, n: int, sd: float, phi: float = 0.9) -> np.ndarray:
    e = rng.normal(0.0, sd, n)
    out = np.empty(n)
    acc = 0.0
    for i, x in enumerate(e):
        acc = phi * acc + x
        out[i] = acc
    return out


@dataclass
class PostWorld:
    """Ce iese din simularea unui post (orar, T ore; zilnic, D zile)."""

    post_id: str
    n_customers: int
    customer_ids: list[str]
    # măsurători (ce vede distribuitorul)
    balance_kwh: np.ndarray  # (T,) contorul de bilanț, energia ieșită din post spre clienți
    cust_kwh: np.ndarray  # (n, T) contoarele clienților, net (consum − producție), NaN = lipsă
    cust_voltage: np.ndarray  # (n, T) tensiunea măsurată în contor, pu (float32)
    # adevărul din construcție (doar pentru etichete și evaluare)
    true_line_loss_kwh: np.ndarray  # (T,) pierderea tehnică pe cabluri, cu fazele
    true_own_kwh: float  # consumul propriu al contoarelor pe oră
    true_theft_kwh: np.ndarray  # (T,) furt înainte de contor
    true_meter_deficit_kwh: np.ndarray  # (T,) consum real nemăsurat din cauza contoarelor (defect, manipulare)
    unbalance: np.ndarray  # (T,) dezechilibrul de faze u
    problems: list[P.Problem] = field(default_factory=list)
    benign: dict[int, str] = field(default_factory=dict)  # client -> comportament benign (concediu etc.)
    static: dict = field(default_factory=dict)  # trăsături statice (GIS)


def simulate(spec: grids.PostSpec, wx: Weather, plan: P.PostPlan, cluster_mv: np.ndarray | None = None) -> PostWorld:
    """Simulează un post pe toată perioada, cu problemele din `plan`."""
    rng = np.random.default_rng(spec.seed + 7919)
    post = grids.build_post(spec)
    m = post.model
    T = wx.T
    n = len(post.load_bus)

    # --- consum, producție, baterii (ca în firul C) ---
    pvk = weather.pv_per_kwp(wx.gti, wx.temp)
    pv = np.minimum(post.pv_kwp[:, None] * post.pv_orient[:, None] * pvk[None, :], post.pv_ac_kw[:, None])
    load = post.load_annual_kwh[:, None] * wx.shapes[list(post.load_profile)].to_numpy().T
    # variație proprie a fiecărui client (profilele SimBench sunt medii; o casă reală e mai zgomotoasă)
    load = load * np.exp(rng.normal(0.0, 0.25, load.shape) - 0.25**2 / 2)

    # comportamente benigne (consumul real se schimbă; nu e problemă): concediu, schimbare de ocupare
    benign: dict[int, str] = {}
    for i, kind, start, dur, factor in plan.benign:
        if i >= n:
            continue
        sl = wx.local_day >= start if dur is None else (wx.local_day >= start) & (wx.local_day < start + dur)
        load[i, sl] *= factor
        benign[i] = kind

    bat = np.zeros_like(pv)
    has = post.bat_kwh > 0
    if has.any():
        bat[has] = battery_dispatch(pv[has] - load[post.pv_load[has]], post.bat_kwh[has], post.bat_kw[has])
    net_true = load.copy()  # kWh pe oră, net la contorul fiecărui client
    if len(post.pv_load):
        np.subtract.at(net_true, post.pv_load, pv - bat)

    # --- furt înainte de contor (consum nemăsurat, legat direct la rețea) ---
    theft = np.zeros(T)
    theft_bus = None
    for pr in plan.problems:
        if pr.kind == "theft_before_meter":
            on = wx.local_day >= pr.onset_day
            shape = np.ones(T) if pr.params["shape"] == "constant" else wx.shapes[pr.params["shape"]].to_numpy() * 8760
            theft += np.where(on, pr.params["kw"] * shape, 0.0)
            theft_bus = int(post.load_bus[pr.params.get("near_customer", 0) % n])

    # --- calculul de rețea (C, vectorizat) ---
    A_ld = m.incidence(post.load_bus)
    s_load = A_ld @ ((load / 1000) * (1 + 1j * post.load_tanphi[:, None]))
    S = -s_load
    if len(post.pv_load):
        S = S + m.incidence(post.pv_bus) @ ((pv - bat) / 1000)
    if theft_bus is not None:
        S[m.bus_pos[theft_bus]] -= theft / 1000 * (1 + 0.2j)
    vm = mv_voltage(post.spec, pvk, wx.sysload, post.spec.seed + 1)
    if cluster_mv is not None:
        vm = vm + cluster_mv
    V, _ = m.solve(S, vm)

    # --- pierderile pe cabluri, din curenți: |I|² R pe fiecare linie ---
    ln = post.net.line[post.net.line.in_service]
    z_base = 0.4**2 / m.base_mva
    z = (ln.r_ohm_per_km.to_numpy() + 1j * ln.x_ohm_per_km.to_numpy()) * ln.length_km.to_numpy() / z_base
    fb = np.array([m.bus_pos[int(b)] for b in ln.from_bus])
    tb = np.array([m.bus_pos[int(b)] for b in ln.to_bus])
    I = (V[fb] - V[tb]) / z[:, None]
    loss_bal = (np.abs(I) ** 2 * z.real[:, None]).sum(axis=0) * m.base_mva * 1000  # kW = kWh pe oră

    # dezechilibrul de faze: un nivel de bază al postului, plus problema tehnică
    u = np.full(T, plan.base_unbalance)
    loss_mult = np.ones(T)
    for pr in plan.problems:
        if pr.kind == "technical":
            on = wx.local_day >= pr.onset_day
            if pr.params["mode"] == "unbalance":
                u = np.where(on, pr.params["u"], u)
            else:  # îmbinare degradată sau cablu subdimensionat: rezistență mai mare
                loss_mult = np.where(on, pr.params["mult"], loss_mult)
    line_loss = loss_bal * SINGLE_PHASE_FACTOR * (1 + PHASE_K * u**2) * loss_mult
    own = n * METER_OWN_W / 1000.0

    # --- contorul de bilanț ---
    true_out = net_true.sum(axis=0) + theft + line_loss + own
    bal = true_out * (1 + rng.normal(0.0, BALANCE_METER_SD))
    for pr in plan.problems:
        if pr.kind == "balance_meter_config":
            bal = np.where(wx.local_day >= pr.onset_day, bal * pr.params["factor"], bal)

    # --- contoarele clienților ---
    rec = net_true * (1 + rng.normal(0.0, CUSTOMER_METER_SD, (n, 1)))
    deficit = np.zeros(T)
    for pr in plan.problems:
        if pr.kind in ("meter_fault", "meter_tamper"):
            i = pr.customer % n
            on = wx.local_day >= pr.onset_day
            before = rec[i].copy()
            rec[i] = P.apply_meter_problem(rec[i], on, pr.params, wx.local_day)
            deficit += np.where(on, before - rec[i], 0.0)
    # rotunjire la rezoluția contorului (0,001 kWh)
    rec = np.round(rec, 3)
    # goluri de comunicație (problemă de date, nu de energie)
    gap_rng = np.random.default_rng(spec.seed + 104729)
    for i in np.flatnonzero(gap_rng.random(n) < GAP_METER_SHARE):
        for _ in range(int(gap_rng.integers(1, 4))):
            d0 = int(gap_rng.integers(0, wx.D))
            dl = int(gap_rng.integers(1, 6))
            rec[i, (wx.local_day >= d0) & (wx.local_day < d0 + dl)] = np.nan

    # tensiunea măsurată în contor (pu): tensiunea nodului clientului plus zgomotul aparatului
    pos_of = {int(b): k for k, b in enumerate(m.lv_bus)}
    Vlv = np.abs(V[m.lv_pos])
    volt = Vlv[[pos_of[int(b)] for b in post.load_bus]] + rng.normal(0.0, VOLTAGE_NOISE_PU, (n, T))

    static = dict(post.features)
    static.update(
        line_r_ohm_km=float(grids.LINE_TYPES[spec.line_type][0]),
        topology=spec.topology,
        base_unbalance=float(plan.base_unbalance),
    )
    return PostWorld(
        post_id=spec.post_id,
        n_customers=n,
        customer_ids=[f"{spec.post_id}-C{i:03d}" for i in range(n)],
        balance_kwh=bal.astype("float64"),
        cust_kwh=rec.astype("float32"),
        cust_voltage=volt.astype("float32"),
        true_line_loss_kwh=line_loss,
        true_own_kwh=own,
        true_theft_kwh=theft,
        true_meter_deficit_kwh=deficit,
        unbalance=u,
        problems=list(plan.problems),
        benign=benign,
        static=static,
    )
