"""Problemele ascunse în lumea simulată, etichetate din construcție (SINTETIC).

Clasele diagnosticului (tabelul din conceptul lui Teo, `memory/11-bilant-pe-post.md`):

| clasă                  | ce simulăm                                                              | cine merge |
|------------------------|-------------------------------------------------------------------------|------------|
| `contor_client`        | contor de client defect (zero, blocat, negativ) sau manipulat (h1, bypass) | echipa de contoare |
| `furt_inainte_contor`  | consum nemăsurat legat direct la rețea, constant sau cu profil de casă, de la o zi | echipa de control |
| `pierdere_tehnica`     | dezechilibru mare de faze sau îmbinare degradată: pierderea crește cu pătratul încărcării | echipa de rețea |
| `client_post_gresit`   | un client al postului X apare în bază la postul vecin Y (X are lipsă, Y are surplus) | corecție în birou |
| `contor_bilant_setat`  | contorul de bilanț numără exact de 2 ori mai mult (raport de transformare greșit) | echipa de contoare |

Defectele și manipulările de contor vin direct din generatorul firului A (`cyberpunks.a_contoare.inject`: zero, stuck,
negative, h1, bypass), cu parametrii trași de el, aplicate pe valori orare. Plajele parametrilor sunt IPOTEZE (vezi docs/data/bilant.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

CLASSES = ("normal", "contor_client", "furt_inainte_contor", "pierdere_tehnica", "client_post_gresit", "contor_bilant_setat")
CLASS_RO = {
    "normal": "pierdere normală",
    "contor_client": "contor de client defect sau manipulat",
    "furt_inainte_contor": "furt înainte de contor",
    "pierdere_tehnica": "pierdere tehnică (cablu, faze dezechilibrate)",
    "client_post_gresit": "client trecut la postul greșit în bază",
    "contor_bilant_setat": "contorul de bilanț al postului setat greșit",
}
KIND_CLASS = {
    "meter_fault": "contor_client",
    "meter_tamper": "contor_client",
    "theft_before_meter": "furt_inainte_contor",
    "technical": "pierdere_tehnica",
    "wrong_post_donor": "client_post_gresit",
    "wrong_post_receiver": "client_post_gresit",
    "balance_meter_config": "contor_bilant_setat",
}
METER_FAULTS = ("zero", "stuck", "negative")
METER_TAMPERS = ("h1", "bypass")
MIN_ONSET_DAY = 60  # primele 60 de zile sunt curate (istoricul postului pentru normal)


@dataclass
class Problem:
    kind: str  # cheie din KIND_CLASS
    onset_day: int  # indexul zilei locale de la care problema e activă
    customer: int = -1  # clientul (pentru contoare și client_post_gresit)
    params: dict = field(default_factory=dict)

    @property
    def cls(self) -> str:
        return KIND_CLASS[self.kind]

    def to_dict(self) -> dict:
        return {"kind": self.kind, "cls": self.cls, "onset_day": self.onset_day, "customer": self.customer, "params": self.params}


@dataclass
class PostPlan:
    post_id: str
    phase_shares: tuple[float, float, float]  # ce parte din case e pe fiecare fază (de bază)
    problems: list[Problem] = field(default_factory=list)
    benign: list[tuple[int, str, int, int | None, float]] = field(default_factory=list)  # (client, tip, start, durată, factor)


def make_plan(
    post_id: str,
    n_customers: int,
    n_days: int,
    rng: np.random.Generator,
    p_post_problem: float = 0.35,
    p_meter_problem: float = 0.012,
    min_onset: int = MIN_ONSET_DAY,
) -> PostPlan:
    """Alege la întâmplare (determinist din rng) problemele unui post. `wrong_post` se leagă după, la nivel de lot."""
    # IPOTEZĂ: cotele de bază pe faze (Dirichlet în jurul lui 1/3); peste jumătate din rețelele JT sunt vizibil
    # dezechilibrate (Fang & Ma 2020, IET GTD)
    shares = tuple(float(x) for x in rng.dirichlet([25.0, 25.0, 25.0]))
    plan = PostPlan(post_id=post_id, phase_shares=shares)
    last = max(min_onset + 1, n_days - 3)
    for i in range(n_customers):
        if rng.random() < p_meter_problem:
            if rng.random() < 0.6:
                k = str(rng.choice(METER_FAULTS))
                params = {"type": k, "seed": int(rng.integers(0, 2**31 - 1))}
                plan.problems.append(Problem("meter_fault", int(rng.integers(min_onset, last)), i, params))
            else:
                k = str(rng.choice(METER_TAMPERS))
                params = {"type": k, "seed": int(rng.integers(0, 2**31 - 1))}  # parametrii îi trage generatorul lui A
                plan.problems.append(Problem("meter_tamper", int(rng.integers(min_onset, last)), i, params))
        r = rng.random()
        if r < 0.03:  # concediu: 7-21 zile la consum de veghe (benign, A îl poate confunda cu o problemă)
            plan.benign.append((i, "concediu", int(rng.integers(0, n_days)), int(rng.integers(7, 22)), 0.15))
        elif r < 0.04:  # schimbare de ocupare, permanentă (benign)
            plan.benign.append((i, "ocupare_schimbata", int(rng.integers(0, n_days)), None, float(rng.choice([0.5, 1.5]))))
    if rng.random() < p_post_problem:
        onset = int(rng.integers(min_onset, last))
        kind = str(rng.choice(["theft_before_meter", "technical", "wrong_post", "balance_meter_config"], p=[0.3, 0.3, 0.25, 0.15]))
        if kind == "theft_before_meter":
            shape = "constant" if rng.random() < 0.5 else "H0-A"
            # IPOTEZĂ: 0,3-2 kW medii nemăsurate (o casă sau un atelier legat direct)
            plan.problems.append(Problem(kind, onset, int(rng.integers(0, n_customers)), {"kw": float(rng.uniform(0.3, 2.0)), "shape": shape, "near_customer": int(rng.integers(0, n_customers))}))
        elif kind == "technical":
            if rng.random() < 0.5:
                hi = float(rng.uniform(0.55, 0.8))  # o fază ia 55-80% din case (după o reconectare greșită)
                rest = float(rng.uniform(0.3, 0.7)) * (1 - hi)
                sh = [hi, rest, 1 - hi - rest]
                rng.shuffle(sh)
                plan.problems.append(Problem(kind, onset, -1, {"mode": "unbalance", "shares": [float(x) for x in sh]}))
            else:
                plan.problems.append(Problem(kind, onset, -1, {"mode": "joint", "mult": float(rng.uniform(1.8, 3.5))}))
        elif kind == "balance_meter_config":
            plan.problems.append(Problem(kind, onset, -1, {"factor": 2.0}))
        else:  # wrong_post: postul vecin se alege la nivel de lot (dataset.link_wrong_posts)
            plan.problems.append(Problem("wrong_post_donor", onset, int(rng.integers(0, n_customers)), {"receiver": None}))
    return plan


def apply_meter_problem(x: np.ndarray, on: np.ndarray, params: dict, local_day: np.ndarray) -> np.ndarray:
    """Aplică defectul sau manipularea pe seria orară `x` a unui contor (kWh), de la prima zi din `on`.

    Folosește generatorul firului A (`cyberpunks.a_contoare.inject.inject`), care lucrează pe zile de 48 de jumătăți
    de oră: fiecare oră se împarte în două jumătăți egale, se injectează, apoi jumătățile se adună la loc. Ora în plus
    din ziua schimbării orei (25 de ore) primește același raport înregistrat/real ca restul zilei.
    """
    from cyberpunks.a_contoare.inject import inject

    if not on.any():
        return x.copy()
    D = int(local_day.max()) + 1
    starts = np.searchsorted(local_day, np.arange(D + 1))
    grid = np.zeros((D, 48))
    for d in range(D):
        h = x[starts[d] : starts[d + 1]]
        k = min(24, len(h))
        grid[d, : 2 * k] = np.repeat(h[:k] / 2.0, 2)
    onset = int(local_day[on][0])
    overrides = {k: v for k, v in params.items() if k in ("alpha", "p", "s", "D")}
    if params["type"] in ("vacation", "occupancy_change", "none"):
        return x.copy()
    yg, _ = inject(grid, params["type"], np.random.default_rng(params["seed"]), start_day=onset, **overrides)
    y = x.copy()
    for d in range(onset, D):
        h = x[starts[d] : starts[d + 1]]
        k = min(24, len(h))
        yh = yg[d, : 2 * k].reshape(k, 2).sum(1)
        y[starts[d] : starts[d] + k] = yh
        if len(h) > 24:
            ratio = yh.sum() / h[:k].sum() if abs(h[:k].sum()) > 1e-9 else 1.0
            y[starts[d] + k : starts[d + 1]] = h[k:] * ratio
    return y
