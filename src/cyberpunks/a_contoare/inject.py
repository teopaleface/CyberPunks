"""Generator determinist de defecte și furturi peste consum real (contoare, 30 min).

ATENȚIE: date sintetice: defectele și furturile sunt injectate de noi peste consum real.
Etichetele (familie + tip) vin din construcție, nu din observații reale de fraudă.

Format: o gospodărie = `hh`, array (n_zile, 48) float64, kWh pe jumătate de oră, NaN = lipsă.
Rândurile sunt zile calendaristice consecutive, coloana 0 = 00:00-00:30. Intrarea nu se modifică.

Tipuri (x = valoarea originală pe jumătate de oră, aplicat doar pe zilele [start_day, end_day)):

| tip              | formulă                                              | parametri                         | sursă |
|------------------|------------------------------------------------------|-----------------------------------|-------|
| h1               | x * alpha                                            | alpha ~ U(0.1, 0.8), o dată       | [1][2][3] |
| h2               | x_t * beta_t                                         | beta_t ~ U(0.1, 0.8) pe t         | [1][2][3] |
| h3               | x_t = 0 pe [t_i, t_i+d) în fiecare zi                | t_i ~ U{0..42}, d ~ U{8..48}      | [1][2][3] |
| h4               | x_t = media zilei (profil plat, total păstrat)       | -                                 | [1][2][3] |
| h5               | beta_t * media zilei                                 | beta_t ~ U(0.1, 0.8)              | [1][2][3] |
| h6               | x_{47-t} (zi inversată, total păstrat)               | -                                 | [1][2][3] |
| bypass           | x * (1 - p * min(1, (zi-start+1)/D))                 | p ~ U(0.2, 0.6), D ~ U{1..30}     | modelul nostru |
| night            | x_t * (1-p) pentru t in 0..11 (00:00-06:00)          | p ~ U(0.3, 0.9)                   | modelul nostru |
| zero             | toate valorile 0.0 (contor mort)                     | -                                 | [4] Zero Consumption |
| stuck            | toate valorile = c (ultima valoare dinainte)         | c                                 | [4] Consecutive/flat intervals |
| gaps             | NaN în 1-4 episoade de 1-10 zile (+ salt de recuperare) | n, durate, catch_up (p=0.5)    | [4] (goluri), modelul nostru |
| spikes           | k vârfuri/săptămână: x * u (sau + u kWh), max 50 kWh | k ~ U{1..4}, u ~ U(10, 80)        | [4] Interval Spike Check |
| clock_drift      | profil deplasat cu k jumătăți de oră (np.roll)       | k in {1,2,3,4,-1,-2}              | modelul nostru |
| negative         | x -> -|x| pe o parte s din valori                    | s ~ U(0.3, 1.0)                   | [4] Negative Consumption |
| drift            | x * (1 - delta * (zi-start)/n_zile_perioadă)         | delta ~ U(0.2, 0.6)               | modelul nostru |
| vacation (normal)| nivel standby (percentila 5 a valorilor pozitive)    | durată 7-21 zile                  | negativ greu |
| occupancy_change (normal) | nivel * factor + deplasare de profil 0-2 slot-uri | factor U(0.45,0.8) sau U(1.25,1.7) | negativ greu |

Note:
- drift: îmbătrânirea reală a unui contor e mult mai lentă (~2-10%/an); noi o accelerăm ca să se vadă în luni.
- zero/stuck suprascriu și NaN-urile din perioadă (un contor mort raportează zerouri / valoare repetată).
  Restul tipurilor lasă NaN-ul original neschimbat.
- gaps: valoarea de recuperare (prima citire după gol) = valoarea ei + suma consumului din gol (registru cumulat).
- Regulile de defect (zero, stuck, gaps, spikes, negative) sunt familii VEE din documentația Oracle Utilities MDM;
  restul sunt modelări proprii.

Surse:
[1] Jokar, Arianpoo, Leung 2016, IEEE TSG, DOI 10.1109/TSG.2015.2425222
[2] https://arxiv.org/pdf/1809.01774 (Nabil et al. 2018, Tabelul I)
[3] https://arxiv.org/pdf/2010.09212
[4] https://docs.oracle.com/en/industries/utilities/rate-cloud/264/rcs-user-guides/Topics/D1_BG_About_IMD_Validations.html
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

FAMILIES = ("normal", "faulty", "tamper")
FAULT_KINDS = ("zero", "stuck", "gaps", "spikes", "clock_drift", "negative", "drift")
TAMPER_KINDS = ("h1", "h2", "h3", "h4", "h5", "h6", "bypass", "night")
BENIGN_KINDS = ("vacation", "occupancy_change")

KIND_FAMILY: dict[str, str] = {
    "none": "normal",
    **dict.fromkeys(BENIGN_KINDS, "normal"),
    **dict.fromkeys(FAULT_KINDS, "faulty"),
    **dict.fromkeys(TAMPER_KINDS, "tamper"),
}

KIND_LABEL_RO: dict[str, str] = {
    "none": "consum normal",
    "zero": "contor oprit (consum zero)",
    "stuck": "contor blocat (valoare repetată)",
    "gaps": "goluri de comunicație (date lipsă)",
    "spikes": "salturi false izolate",
    "clock_drift": "ceas decalat (profil mutat)",
    "negative": "citiri negative (polaritate inversată)",
    "drift": "subînregistrare progresivă (contor îmbătrânit)",
    "h1": "consum raportat redus constant",
    "h2": "consum redus cu factor aleator pe jumătate de oră",
    "h3": "consum zero la aceleași ore în fiecare zi",
    "h4": "profil zilnic aplatizat (media zilei)",
    "h5": "profil aplatizat și redus aleator",
    "h6": "profil zilnic inversat în timp",
    "bypass": "bypass parțial, cu instalare treptată",
    "night": "consum de noapte redus (00:00-06:00)",
    "vacation": "concediu (consum de așteptare)",
    "occupancy_change": "schimbare de ocupare (nivel nou, formă ușor diferită)",
}

KIND_OUTCOME: dict[str, str] = {
    "none": "normal",
    "zero": "contor_oprit",
    "stuck": "contor_blocat",
    "gaps": "goluri_comunicatie",
    "spikes": "salturi_false",
    "clock_drift": "ceas_decalat",
    "negative": "citiri_negative",
    "drift": "subinregistrare",
    **dict.fromkeys(TAMPER_KINDS, "manipulare_confirmata"),
    **dict.fromkeys(BENIGN_KINDS, "schimbare_normala"),
}

# Intervale de parametri (date, ca să fie documentate și ușor de schimbat).
# Tuplu (a, b) = U(a, b) continuu; ("int", a, b) = întreg uniform în [a, b]; listă = alegere.
PARAMS: dict[str, dict] = {
    "h1": {"alpha": (0.1, 0.8)},
    "h2": {"beta": (0.1, 0.8)},
    "h3": {"t_i": ("int", 0, 42), "d": ("int", 8, 48), "jitter": 2},
    "h4": {},
    "h5": {"beta": (0.1, 0.8)},
    "h6": {},
    "bypass": {"p": (0.2, 0.6), "ramp_days": ("int", 1, 30)},
    "night": {"p": (0.3, 0.9), "slots": 12},
    "zero": {},
    "stuck": {},
    "gaps": {"episodes": ("int", 1, 4), "duration_days": ("int", 1, 10), "catch_up_prob": 0.5},
    "spikes": {"per_week": ("int", 1, 4), "factor": (10.0, 80.0), "cap_kwh": 50.0, "near_zero": 0.01},
    "clock_drift": {"shift": [1, 2, 3, 4, -1, -2]},
    "negative": {"share": (0.3, 1.0)},
    "drift": {"delta": (0.2, 0.6)},
    "vacation": {"duration_days": ("int", 7, 21), "noise": (0.8, 1.2), "quantile": 0.05},
    "occupancy_change": {"factor_down": (0.45, 0.8), "factor_up": (1.25, 1.7), "shift": [-2, -1, 0, 1, 2]},
}

EPISODIC_KINDS = ("gaps", "vacation")

# Probabilități implicite (se renormalizează): fără problemă 0.80, fiecare defect 0.015,
# fiecare furt 0.01, evenimente benigne 0.03 în total (0.015 fiecare).
DEFAULT_PROBS: dict[str, float] = {
    "none": 0.80,
    **dict.fromkeys(FAULT_KINDS, 0.015),
    **dict.fromkeys(TAMPER_KINDS, 0.01),
    **dict.fromkeys(BENIGN_KINDS, 0.015),
}


def _clean(value):
    """Convertește valori numpy în tipuri Python serializabile JSON."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return [_clean(v) for v in value.tolist()]
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


@dataclass(frozen=True)
class Injection:
    """Ce s-a injectat: tipul, familia, perioada, parametrii și consumul adevărat vs. înregistrat."""

    kind: str
    family: str
    start_day: int
    end_day: int
    params: dict
    kwh_true: float
    kwh_recorded: float

    def to_dict(self) -> dict:
        d = asdict(self)
        d["params"] = _clean(self.params)
        return d


def _draw(rng: np.random.Generator, kind: str, name: str, size=None):
    """Trage un parametru după PARAMS."""
    spec = PARAMS[kind][name]
    if isinstance(spec, list):
        return rng.choice(spec) if size is None else rng.choice(spec, size=size)
    if spec[0] == "int":
        return rng.integers(spec[1], spec[2] + 1, size=size)
    return rng.uniform(spec[0], spec[1], size=size)


def _day_means(block: np.ndarray) -> np.ndarray:
    """Media pe zi (ignoră NaN); zi fără valori -> NaN, fără avertismente."""
    cnt = np.isfinite(block).sum(axis=1)
    tot = np.nansum(block, axis=1)
    return np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)


def _positive_values(hh: np.ndarray) -> np.ndarray:
    flat = hh[np.isfinite(hh)]
    return flat[flat > 0]


def inject(
    hh: np.ndarray,
    kind: str,
    rng: np.random.Generator,
    start_day: int,
    end_day: int | None = None,
    **overrides,
) -> tuple[np.ndarray, Injection]:
    """Injectează `kind` pe zilele [start_day, end_day) și întoarce (copie modificată, Injection).

    `overrides` forțează parametri (ex. alpha=0.5, t_i=10, d=12, p=0.4, k=2).
    Tipurile episodice (gaps, vacation) își stabilesc singure end_day (sfârșitul ultimei zile afectate).
    """
    if kind != "none" and kind not in KIND_FAMILY:
        raise ValueError(f"tip necunoscut: {kind}")
    out = np.array(hh, dtype=np.float64, copy=True)
    if kind == "none":
        return out, Injection("none", "normal", -1, -1, {}, 0.0, 0.0)

    n_days = out.shape[0]
    end = n_days if end_day is None else min(int(end_day), n_days)
    s = int(start_day)
    if not 0 <= s < n_days or end <= s:
        raise ValueError(f"perioadă invalidă: start={s}, end={end}, n_zile={n_days}")

    params: dict = {}
    block = out[s:end]  # view; scrierile merg în `out`
    n_per = end - s

    if kind == "h1":
        alpha = float(overrides.get("alpha", _draw(rng, "h1", "alpha")))
        params["alpha"] = alpha
        block *= alpha
    elif kind == "h2":
        beta = rng.uniform(*PARAMS["h2"]["beta"], size=block.shape)
        if "beta" in overrides:
            beta = np.full(block.shape, float(overrides["beta"]))
        block *= beta
    elif kind == "h3":
        t_i = int(overrides.get("t_i", _draw(rng, "h3", "t_i")))
        d = int(overrides.get("d", _draw(rng, "h3", "d")))
        jit = PARAMS["h3"]["jitter"]
        jitters = rng.integers(-jit, jit + 1, size=n_per)
        if "jitter" in overrides:
            jitters = np.zeros(n_per, dtype=int)
        params.update(t_i=t_i, d=d)
        for r in range(n_per):
            a = int(np.clip(t_i + jitters[r], 0, 47))
            block[r, a : min(48, a + d)] = np.where(np.isfinite(block[r, a : min(48, a + d)]), 0.0, np.nan)
    elif kind == "h4":
        m = _day_means(block)
        flat_block = np.repeat(m[:, None], 48, axis=1)
        block[:] = np.where(np.isfinite(block), flat_block, np.nan)
    elif kind == "h5":
        beta = rng.uniform(*PARAMS["h5"]["beta"], size=block.shape)
        m = _day_means(block)
        block[:] = np.where(np.isfinite(block), beta * m[:, None], np.nan)
    elif kind == "h6":
        block[:] = block[:, ::-1].copy()
    elif kind == "bypass":
        p = float(overrides.get("p", _draw(rng, "bypass", "p")))
        ramp = int(overrides.get("ramp_days", _draw(rng, "bypass", "ramp_days")))
        params.update(p=p, ramp_days=ramp)
        factor = 1.0 - p * np.minimum(1.0, (np.arange(n_per) + 1) / ramp)
        block *= factor[:, None]
    elif kind == "night":
        p = float(overrides.get("p", _draw(rng, "night", "p")))
        params["p"] = p
        block[:, : PARAMS["night"]["slots"]] *= 1.0 - p
    elif kind == "zero":
        block[:] = 0.0
    elif kind == "stuck":
        prev = out[:s].ravel()
        prev = prev[np.isfinite(prev)]
        c = float(prev[-1]) if prev.size else 0.0
        if c <= 0:
            pos = _positive_values(hh)
            c = float(np.median(pos)) if pos.size else 0.1
        c = float(overrides.get("c", c))
        params["c"] = c
        block[:] = c
    elif kind == "gaps":
        n_ep = int(overrides.get("episodes", _draw(rng, "gaps", "episodes")))
        catch_up = bool(overrides.get("catch_up", rng.random() < PARAMS["gaps"]["catch_up_prob"]))
        episodes: list[list[int]] = []
        cursor = s
        for i in range(n_ep):
            if i > 0:
                cursor += int(rng.integers(0, 6))
            if cursor >= end:
                break
            dur = int(_draw(rng, "gaps", "duration_days"))
            dur = min(dur, end - cursor)
            episodes.append([cursor, cursor + dur])
            cursor += dur + 1  # cel puțin o zi între goluri
        for a, b in episodes:
            gap_sum = float(np.nansum(hh[a:b]))
            out[a:b] = np.nan
            if catch_up and b < n_days:
                out[b, 0] = (0.0 if np.isnan(out[b, 0]) else out[b, 0]) + gap_sum
        end = episodes[-1][1]
        params.update(episodes=episodes, catch_up=catch_up)
    elif kind == "spikes":
        cap = PARAMS["spikes"]["cap_kwh"]
        near0 = PARAMS["spikes"]["near_zero"]
        spikes = []
        for w in range(s, end, 7):
            week = out[w : min(w + 7, end)]
            k = int(_draw(rng, "spikes", "per_week"))
            idx = rng.choice(week.size, size=min(k, week.size), replace=False)
            for flat_i in idx:
                r, t = divmod(int(flat_i), 48)
                u = float(_draw(rng, "spikes", "factor"))
                x = week[r, t]
                if np.isnan(x):
                    continue
                week[r, t] = min(cap, x + u if x < near0 else x * u)
                spikes.append([w + r, t])
        params.update(spikes=spikes)
    elif kind == "clock_drift":
        k = int(overrides.get("k", _draw(rng, "clock_drift", "shift")))
        params["k"] = k
        block[:] = np.roll(block.ravel(), k).reshape(block.shape)
    elif kind == "negative":
        share = float(overrides.get("share", _draw(rng, "negative", "share")))
        params["share"] = share
        mask = rng.random(block.shape) < share
        block[:] = np.where(mask & np.isfinite(block), -np.abs(block), block)
    elif kind == "drift":
        delta = float(overrides.get("delta", _draw(rng, "drift", "delta")))
        params["delta"] = delta
        factor = 1.0 - delta * np.arange(n_per) / n_per
        block *= factor[:, None]
    elif kind == "vacation":
        dur = int(overrides.get("duration_days", _draw(rng, "vacation", "duration_days")))
        end = min(n_days, s + dur)
        pos = _positive_values(hh)
        standby = float(np.quantile(pos, PARAMS["vacation"]["quantile"])) if pos.size else 0.0
        seg = out[s:end]
        noise = rng.uniform(*PARAMS["vacation"]["noise"], size=seg.shape)
        seg[:] = np.where(np.isfinite(seg), standby * noise, np.nan)
        params.update(standby=standby, duration_days=end - s)
    elif kind == "occupancy_change":
        up = bool(overrides.get("up", rng.random() < 0.5))
        factor = float(overrides.get("factor", _draw(rng, "occupancy_change", "factor_up" if up else "factor_down")))
        shift = int(overrides.get("shift", _draw(rng, "occupancy_change", "shift")))
        params.update(factor=factor, shift=shift, up=up)
        block *= factor
        block[:] = np.roll(block.ravel(), shift).reshape(block.shape)

    info = Injection(
        kind=kind,
        family=KIND_FAMILY[kind],
        start_day=s,
        end_day=int(end),
        params=_clean(params),
        kwh_true=float(np.nansum(hh[s:end])),
        kwh_recorded=float(np.nansum(out[s:end])),
    )
    return out, info


def sample_kind(rng: np.random.Generator, probs: dict[str, float] | None = None) -> str:
    """Alege un tip. Implicit: none 0.80, defecte 0.015 fiecare, furturi 0.01 fiecare, benigne 0.015 fiecare.

    Probabilitățile se renormalizează; cheile lipsă au probabilitate 0.
    """
    probs = DEFAULT_PROBS if probs is None else probs
    bad = [k for k in probs if k != "none" and k not in KIND_FAMILY]
    if bad:
        raise ValueError(f"tipuri necunoscute: {bad}")
    kinds = list(probs)
    p = np.array([probs[k] for k in kinds], dtype=float)
    if p.sum() <= 0 or (p < 0).any():
        raise ValueError("probabilități invalide")
    return str(kinds[int(rng.choice(len(kinds), p=p / p.sum()))])


def sample_and_inject(
    hh: np.ndarray,
    rng: np.random.Generator,
    *,
    min_onset_day: int,
    probs: dict[str, float] | None = None,
    max_duration_days: int | None = None,
) -> tuple[np.ndarray, Injection]:
    """Alege tipul și începutul (uniform în [min_onset_day, n_zile-7]) și injectează.

    end_day = n_zile, dacă nu e dat `max_duration_days`; tipurile episodice își aleg singure sfârșitul.
    """
    kind = sample_kind(rng, probs)
    if kind == "none":
        return inject(hh, "none", rng, -1)
    n_days = hh.shape[0]
    last = n_days - 7
    if min_onset_day > last:
        raise ValueError("istoric prea scurt pentru min_onset_day")
    start = int(rng.integers(min_onset_day, last + 1))
    end = None if max_duration_days is None else min(n_days, start + int(max_duration_days))
    return inject(hh, kind, rng, start, end)
