"""Verificarea contorului de balanță cu contorul martor: o regulă, nu un model ML.

Codul de măsurare ANRE (Ord. 103/2015, https://reteleelectrice.ro/wp-content/uploads/cod-masurare-2015.pdf):
„contor martor - contor de energie electrică având rolul de a măsura energia electrică în paralel cu contorul de
decontare”, cu cel puțin aceeași clasă de exactitate, pe aceleași circuite. Mentorul PPC: diferența normală e „poate
0,1%”. Pragul de 0,5% e clasa de exactitate a contorului (0,5S): peste el, unul din contoare e defect sau setat greșit
(cazul „2×”: diferență de ~100%).

Atenție: 0,1% e precizia contoarelor pe același punct, NU pierderea din rețeaua de sub post (câteva procente, învățată
de modelul pierderii normale).

Pragul stă aici temporar; cerut planificatorului ca `config/economics.yaml` → `meters.martor_diff_limit_pct`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MARTOR_DIFF_LIMIT = 0.005  # 0,5%: clasa de exactitate 0,5S (Codul de măsurare ANRE 2015); planificatorul îl poate muta în config
MIN_DAY_KWH = 5.0  # zilele cu energie foarte mică la post (prosumatori la echilibru) nu intră în raport


def martor_diff(bal_kwh: pd.Series | np.ndarray, martor_kwh: pd.Series | np.ndarray) -> float:
    """Mediana pe zile a diferenței relative |contor de balanță − martor| / |martor|; NaN dacă nu există martor."""
    b = np.asarray(bal_kwh, dtype=float)
    m = np.asarray(martor_kwh, dtype=float)
    ok = np.isfinite(b) & np.isfinite(m) & (np.abs(m) > MIN_DAY_KWH)
    if ok.sum() < 2:
        return float("nan")
    return float(np.median(np.abs(b[ok] - m[ok]) / np.abs(m[ok])))


def verdict(diff: float) -> str:
    if not np.isfinite(diff):
        return "fara_martor"
    return "diferenta_peste_clasa" if diff > MARTOR_DIFF_LIMIT else "in_clasa"
