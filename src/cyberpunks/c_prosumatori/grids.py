"""Rețelele de joasă tensiune: cele 6 topologii SimBench și posturile sintetice construite din ele.

Fiecare post de transformare e o variantă SINTETICĂ a unei topologii SimBench (date ODbL): alt transformator,
alți conductori, linii mai lungi sau mai scurte, altă priză, altă tensiune pe medie tensiune și alți prosumatori
(puteri, baterii, orientări). Parametrii care nu au sursă sunt marcați IPOTEZĂ.
"""

from __future__ import annotations

import copy
import warnings
from dataclasses import asdict, dataclass, field
from functools import cache

import numpy as np

from cyberpunks.c_prosumatori.powerflow import GridModel

warnings.filterwarnings("ignore", message=".*numba.*")

TOPOLOGIES: dict[str, str] = {
    "rural1": "1-LV-rural1--0-no_sw",
    "rural2": "1-LV-rural2--0-no_sw",
    "rural3": "1-LV-rural3--0-no_sw",
    "semiurb4": "1-LV-semiurb4--0-no_sw",
    "semiurb5": "1-LV-semiurb5--0-no_sw",
    "urban6": "1-LV-urban6--0-no_sw",
}
AREA: dict[str, str] = {
    "rural1": "rural",
    "rural2": "rural",
    "rural3": "rural",
    "semiurb4": "semiurban",
    "semiurb5": "semiurban",
    "urban6": "urban",
}

# Conductori de joasă tensiune (r, x în ohm/km; curent maxim în kA). IPOTEZĂ: valori tipice de catalog.
# NAYY 4x150 e conductorul din SimBench; TYIR e cablul torsadat aerian folosit des în satele din România.
LINE_TYPES: dict[str, tuple[float, float, float]] = {
    "NAYY_4x150": (0.2067, 0.0804, 0.270),
    "NAYY_4x95": (0.320, 0.082, 0.215),
    "TYIR_70": (0.443, 0.090, 0.200),
    "TYIR_50": (0.641, 0.093, 0.165),
    "AL_35_vechi": (0.868, 0.300, 0.140),
}
LINE_TYPE_P: dict[str, dict[str, float]] = {  # IPOTEZĂ: cât de des apare fiecare conductor pe tip de zonă
    "urban": {"NAYY_4x150": 0.7, "NAYY_4x95": 0.3},
    "semiurban": {"NAYY_4x150": 0.3, "NAYY_4x95": 0.3, "TYIR_70": 0.3, "TYIR_50": 0.1},
    "rural": {"NAYY_4x150": 0.1, "TYIR_70": 0.35, "TYIR_50": 0.4, "AL_35_vechi": 0.15},
}
LINE_SCALE: dict[str, tuple[float, float]] = {"urban": (0.6, 1.3), "semiurban": (0.7, 1.6), "rural": (0.8, 2.0)}

# Transformatoare 20/0,4 kV, Dyn5, comutator fără sarcină ±2×2,5% pe MT: (vk %, vkr %, pfe kW, i0 %).
# 160-630 kVA: tipurile din SimBench; 100 kVA: IPOTEZĂ (valori tipice de catalog).
TRAFO_TYPES: dict[int, tuple[float, float, float, float]] = {
    100: (4.0, 1.75, 0.32, 0.50),
    160: (4.0, 1.46875, 0.46, 0.28751),
    250: (6.0, 1.32, 0.88, 0.35201),
    400: (6.0, 1.20, 1.20, 0.30001),
    630: (6.0, 1.0952, 1.65, 0.26192),
}
KVA_CHOICES: dict[str, list[int]] = {
    "rural1": [100, 160, 250],
    "rural2": [160, 250, 400],
    "rural3": [250, 400, 630],
    "semiurb4": [250, 400, 630],
    "semiurb5": [400, 630],
    "urban6": [400, 630],
}

# Prosumatori casnici: kWp pe casă. IPOTEZĂ calibrată pe ANRE (6,4 kW media persoanelor fizice, iun. 2026).
PV_KWP_HOUSE = ([3, 5, 6, 8, 10, 12, 15], [0.18, 0.25, 0.17, 0.15, 0.15, 0.06, 0.04])
PV_KWP_COMMERCIAL = ([15, 20, 30, 50], [0.3, 0.3, 0.25, 0.15])  # IPOTEZĂ
BATTERY_KWH = ([5.0, 10.0, 15.0], [0.5, 0.4, 0.1])  # IPOTEZĂ: module tipice 5 / 10 / 15 kWh
# Orientarea panourilor: factor față de panoul spre sud la 30° (IPOTEZĂ).
ORIENT = ([(0.95, 1.0), (0.88, 0.95), (0.75, 0.85)], [0.55, 0.25, 0.20])


@dataclass
class PostSpec:
    """Parametrii unui post sintetic. Din ei (și din seed) se reconstruiește exact aceeași rețea."""

    post_id: str
    topology: str
    seed: int
    kva: int
    line_type: str
    line_scale: float
    tap_pos: int  # comutatorul pe MT: -2..+2; negativ ridică tensiunea pe JT, +1 o coboară cu 2,5%
    vm_mv: float  # tensiunea medie pe MT la post, pu
    vm_mv_est: float  # ce știe distribuitorul despre ea (estimare cu eroare)
    prosumer_share: float  # ce parte din case au panouri
    battery_share: float  # ce parte din prosumatori au baterie
    mean_annual_kwh: float  # consumul mediu pe casă, kWh/an
    mv_pv_coef: float  # cât urcă tensiunea pe MT la soare plin (necunoscut modelului)
    mv_load_coef: float  # cât scade tensiunea pe MT la consum mare (necunoscut modelului)
    mode: str = "train"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Post:
    spec: PostSpec
    net: object
    model: GridModel
    load_bus: np.ndarray
    load_profile: np.ndarray  # numele profilului SimBench (H0-A, G1-C, ...)
    load_annual_kwh: np.ndarray
    load_tanphi: np.ndarray
    load_is_house: np.ndarray
    pv_load: np.ndarray  # indexul consumatorului (în load_*) care are panoul
    pv_bus: np.ndarray
    pv_kwp: np.ndarray
    pv_ac_kw: np.ndarray
    pv_orient: np.ndarray
    bat_kwh: np.ndarray  # 0 dacă nu are baterie
    bat_kw: np.ndarray
    features: dict = field(default_factory=dict)


def spec_from_row(row) -> PostSpec:
    """Reconstruiește PostSpec dintr-un rând de registru (coloanele spec_* dacă există, altfel cele simple)."""
    vals = {}
    for k in PostSpec.__dataclass_fields__:
        vals[k] = row[f"spec_{k}"] if f"spec_{k}" in row else row[k]
    for k in ("seed", "kva", "tap_pos"):
        vals[k] = int(vals[k])
    for k in ("line_scale", "vm_mv", "vm_mv_est", "prosumer_share", "battery_share", "mean_annual_kwh", "mv_pv_coef", "mv_load_coef"):
        vals[k] = float(vals[k])
    return PostSpec(**vals)


@cache
def _base_net(topology: str):
    import simbench as sb

    net = sb.get_simbench_net(TOPOLOGIES[topology])
    net.sgen.drop(net.sgen.index, inplace=True)
    net.storage.drop(net.storage.index, inplace=True)
    net.profiles = {}
    return net


def base_net(topology: str):
    """Copia rețelei SimBench (fără panourile și bateriile originale)."""
    return copy.deepcopy(_base_net(topology))


def _choice(rng: np.random.Generator, options, p):
    return options[int(rng.choice(len(options), p=np.asarray(p) / np.sum(p)))]


def sample_spec(topology: str, rng: np.random.Generator, post_id: str, mode: str = "train") -> PostSpec:
    """Alege parametrii unui post. `train`: plaje largi (acoperă spațiul); `population`: realist pentru Ilfov."""
    area = AREA[topology]
    lt = LINE_TYPE_P[area]
    line_type = _choice(rng, list(lt), list(lt.values()))
    lo, hi = LINE_SCALE[area]
    if mode == "train":
        prosumer_share = float(rng.choice([0.0, rng.uniform(0.02, 0.8)], p=[0.08, 0.92]))
        battery_share = float(rng.uniform(0.0, 0.7))
        tap = int(rng.choice([-2, -1, 0, 1, 2], p=[0.12, 0.25, 0.33, 0.18, 0.12]))
        v0 = float(rng.uniform(0.99, 1.075))  # tensiunea fără sarcină pe JT, pu
        kva = int(rng.choice(KVA_CHOICES[topology]))
    else:  # population: IPOTEZĂ realistă (Ilfov are mulți prosumatori la case, Bucureștiul puțini la blocuri)
        a, b = {"urban": (1.0, 12.0), "semiurban": (1.5, 4.5), "rural": (1.3, 5.0)}[area]
        prosumer_share = float(0.0 if rng.random() < 0.12 else min(0.85, rng.beta(a, b)))
        battery_share = float(np.clip(rng.normal(0.35, 0.15), 0.0, 0.8))  # ANRE: 127.084 din 359.378 au baterii
        tap = int(rng.choice([-2, -1, 0, 1], p=[0.08, 0.3, 0.47, 0.15]))
        v0 = float(np.clip(rng.normal(1.035, 0.015), 1.0, 1.07))
        kva = int(_choice(rng, KVA_CHOICES[topology], [1.0] * len(KVA_CHOICES[topology])))
    # IPOTEZĂ: priza e aleasă de distribuitor după tensiunea de pe MT, ca tensiunea fără sarcină pe JT
    # să rămână între 0,99 și 1,075 pu (priza +1 pe MT coboară JT cu 2,5%)
    vm_mv = float(np.clip(v0 * (1 + 0.025 * tap), 0.95, 1.06))
    return PostSpec(
        post_id=post_id,
        topology=topology,
        seed=int(rng.integers(0, 2**31 - 1)),
        kva=kva,
        line_type=line_type,
        line_scale=float(rng.uniform(lo, hi)),
        tap_pos=tap,
        vm_mv=round(vm_mv, 4),
        vm_mv_est=round(vm_mv + float(rng.normal(0.0, 0.004)), 4),
        prosumer_share=round(prosumer_share, 4),
        battery_share=round(battery_share, 4),
        mean_annual_kwh=float(np.clip(rng.lognormal(np.log(2500), 0.25), 1200, 5000)),
        mv_pv_coef=float(rng.uniform(0.0, 0.015)),
        mv_load_coef=float(rng.uniform(0.0, 0.012)),
        mode=mode,
    )


# Limite de realism (IPOTEZĂ): un distribuitor n-ar ține în funcțiune o rețea în care panourile ridică tensiunea
# cu peste 25% la soare plin sau în care consumul mediu o coboară cu peste 4% (la vârf ar fi sub 0,85 pu).
MAX_SENS_PV = 0.25
MAX_SENS_LOAD = 0.04


def build_realistic(spec: PostSpec, max_tries: int = 12) -> Post:
    """Ca build_post, dar reduce prosumatorii sau lungimea liniilor până când rețeaua e plauzibilă."""
    post = build_post(spec)
    for _ in range(max_tries):
        f = post.features
        if f["sens_pv_pu"] <= MAX_SENS_PV and f["sens_load_pu"] <= MAX_SENS_LOAD:
            break
        if f["sens_load_pu"] > MAX_SENS_LOAD:
            spec.line_scale = round(spec.line_scale * 0.85, 4)
        if f["sens_pv_pu"] > MAX_SENS_PV:
            spec.prosumer_share = round(spec.prosumer_share * 0.8, 4)
        post = build_post(spec)
    return post


def build_post(spec: PostSpec) -> Post:
    """Construiește rețeaua pandapower a postului, prosumatorii și trăsăturile statice."""
    import pandapower as pp
    import pandapower.topology as top

    rng = np.random.default_rng(spec.seed)
    net = base_net(spec.topology)

    # conductori și lungimi
    r, x, imax = LINE_TYPES[spec.line_type]
    net.line["r_ohm_per_km"] = r
    net.line["x_ohm_per_km"] = x
    net.line["max_i_ka"] = imax
    net.line["length_km"] = net.line["length_km"] * spec.line_scale

    # transformator, priză, tensiunea pe MT
    vk, vkr, pfe, i0 = TRAFO_TYPES[spec.kva]
    t = net.trafo.index[0]
    net.trafo.loc[t, ["sn_mva", "vk_percent", "vkr_percent", "pfe_kw", "i0_percent"]] = [spec.kva / 1000, vk, vkr, pfe, i0]
    # pandapower 3.x ignoră priza dacă tipul comutatorului nu e declarat (SimBench îl lasă gol): îl declarăm explicit
    net.trafo["tap_changer_type"] = "Ratio"
    net.trafo.loc[t, "tap_pos"] = spec.tap_pos
    net.ext_grid["vm_pu"] = spec.vm_mv

    # consumatori: case (profile H0) și firme mici (G); consumul anual românesc pentru case (IPOTEZĂ)
    prof = net.load["profile"].astype(str).to_numpy()
    is_house = np.char.startswith(prof.astype("U8"), "H0")
    annual = np.where(
        is_house,
        np.clip(rng.lognormal(np.log(spec.mean_annual_kwh), 0.45, len(prof)), 600, 9000),
        np.clip(rng.lognormal(np.log(8000), 0.5, len(prof)), 2000, 40000),
    )
    p = net.load["p_mw"].to_numpy()
    q = net.load["q_mvar"].to_numpy()
    tanphi = np.where(p > 0, q / np.maximum(p, 1e-9), 0.3)

    # prosumatori
    houses = np.flatnonzero(is_house)
    n_pros = round(spec.prosumer_share * len(houses))
    pv_load = list(rng.choice(houses, size=n_pros, replace=False)) if n_pros else []
    kwp = [float(_choice(rng, *PV_KWP_HOUSE)) for _ in pv_load]
    shops = np.flatnonzero(~is_house)
    if len(shops) and spec.prosumer_share > 0 and rng.random() < 0.3:
        s = int(rng.choice(shops))
        pv_load.append(s)
        kwp.append(float(_choice(rng, *PV_KWP_COMMERCIAL)))
    pv_load = np.array(pv_load, dtype=int)
    pv_kwp = np.array(kwp, dtype=float)
    pv_ac = pv_kwp * rng.uniform(0.85, 1.0, len(pv_kwp))
    orient = np.array([rng.uniform(*_choice(rng, *ORIENT)) for _ in pv_load], dtype=float)
    has_bat = (rng.random(len(pv_load)) < spec.battery_share) & is_house[pv_load] if len(pv_load) else np.zeros(0, bool)
    bat_kwh = np.where(has_bat, [float(_choice(rng, *BATTERY_KWH)) for _ in pv_load], 0.0) if len(pv_load) else np.zeros(0)
    bat_kw = np.clip(bat_kwh / 2.0, 2.5, 5.0) * (bat_kwh > 0)
    load_bus = net.load["bus"].to_numpy()
    pv_bus = load_bus[pv_load] if len(pv_load) else np.zeros(0, dtype=int)

    # elementele pandapower (pentru verificare cu runpp): consumul mediu, PV la puterea instalată
    net.load["p_mw"] = annual / 8760 / 1000
    net.load["q_mvar"] = net.load["p_mw"] * tanphi
    for b, k in zip(pv_bus, pv_ac, strict=True):
        pp.create_sgen(net, bus=int(b), p_mw=float(k) / 1000, q_mvar=0.0, type="PV")

    model = GridModel.from_net(net)

    # trăsături statice (ce poate ști distribuitorul din GIS și din avizele de racordare)
    lv_trafo_bus = int(net.trafo.lv_bus.iloc[0])
    dist = top.calc_distance_to_bus(net, lv_trafo_bus, weight="weight")
    dist = dist[dist.index.isin(model.lv_bus)]
    R_lv = model.Zll.real[np.ix_(model.lv_pos, model.lv_pos)]
    pos_of = {int(b): i for i, b in enumerate(model.lv_bus)}
    z_base = 0.4**2 / model.base_mva
    pv_idx = np.array([pos_of[int(b)] for b in pv_bus], dtype=int)
    load_idx = np.array([pos_of[int(b)] for b in load_bus], dtype=int)
    sens_pv = float((R_lv[:, pv_idx] @ (pv_kwp / 1000)).max()) if len(pv_idx) else 0.0
    sens_load = float((R_lv[:, load_idx] @ (annual / 8760 / 1000)).max())
    features = {
        "kva": float(spec.kva),
        "n_customers": len(prof),
        "n_houses": len(houses),
        "n_prosumers": len(pv_load),
        "pv_kw": float(pv_kwp.sum()),
        "pv_kw_per_kva": float(pv_kwp.sum() / spec.kva),
        "prosumer_share": float(len(pv_load) / max(len(houses), 1)),
        "battery_kwh": float(bat_kwh.sum()),
        "battery_pv_share": float(pv_kwp[bat_kwh > 0].sum() / pv_kwp.sum()) if pv_kwp.sum() > 0 else 0.0,
        "annual_load_mwh": float(annual.sum() / 1000),
        "line_km": float(net.line.length_km.sum()),
        "max_path_km": float(dist.max()),
        "r_max_ohm": float(np.diag(R_lv).max() * z_base),
        "sens_pv_pu": sens_pv,  # creșterea liniară a tensiunii în nodul cel mai sensibil, la 1 kW/kWp
        "sens_load_pu": sens_load,  # scăderea liniară la consum mediu
        "vk_percent": float(vk),
        "tap_pos": float(spec.tap_pos),
        "vm_mv_est": float(spec.vm_mv_est),
        "v0_est": float(spec.vm_mv_est / (1 + 0.025 * spec.tap_pos)),  # tensiunea estimată fără sarcină pe JT
    }
    return Post(
        spec=spec,
        net=net,
        model=model,
        load_bus=load_bus,
        load_profile=prof,
        load_annual_kwh=annual,
        load_tanphi=tanphi,
        load_is_house=is_house,
        pv_load=pv_load,
        pv_bus=pv_bus,
        pv_kwp=pv_kwp,
        pv_ac_kw=pv_ac,
        pv_orient=orient,
        bat_kwh=np.asarray(bat_kwh, dtype=float),
        bat_kw=np.asarray(bat_kw, dtype=float),
        features=features,
    )
