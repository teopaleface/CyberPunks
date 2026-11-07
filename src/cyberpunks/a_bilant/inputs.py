"""Verificarea intrărilor bilanțului (intrări greșite, date lipsă), înainte de orice calcul.

Ce prindem și ce facem:
- contorul de post lipsește sau tace (toate orele lipsă): postul trece pe planul B (energia intrată estimată din
  suma clienților plus pierderea normală), fără lucrare de pierderi; `has_balance = False`;
- ore dublate (același timestamp de două ori, de la reîncercări de transmisie): păstrăm prima valoare;
- unități greșite (Wh în loc de kWh): raportul contor de post / suma clienților e ~1000 sau ~0,001; reducem la kWh
  și notăm;
- ore lipsă la contorul de post: sub 10% din zi le completăm din aceeași oră a zilei precedente; peste 10%, ziua e
  scoasă din bilanț;
- valori negative la contorul de post fără prosumatori: semn inversat (polaritate), le marcăm.
Fiecare corecție intră în `issues` (ajunge în `data_quality.input_issues` al lucrării).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MAX_MISSING_SHARE = 0.10


@dataclass
class CleanResult:
    balance_kwh: pd.Series  # orar, curățat (NaN unde nu se poate)
    customers_kwh: pd.Series  # suma orară a clienților
    has_balance: bool
    usable_days: list = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


def clean(balance: pd.Series | None, customers: pd.Series, has_prosumers: bool = False) -> CleanResult:
    """`balance` și `customers`: serii orare (index de timp, kWh). Întoarce seriile curățate și problemele găsite."""
    issues: list[str] = []
    cust = customers[~customers.index.duplicated(keep="first")].sort_index().astype(float)
    if balance is None or len(balance) == 0 or balance.isna().all():
        issues.append("contorul de balanță al postului lipsește sau nu transmite: planul B (energia intrată estimată din modelul rețelei)")
        return CleanResult(pd.Series(np.nan, index=cust.index), cust, False, [], issues)
    dup = int(balance.index.duplicated().sum())
    bal = balance[~balance.index.duplicated(keep="first")].sort_index().astype(float)
    if dup:
        issues.append(f"{dup} ore dublate la contorul de post: păstrată prima valoare")
    bal = bal.reindex(cust.index.union(bal.index))
    cust = cust.reindex(bal.index)
    # unitățile: raportul dintre totaluri pe orele cu ambele valori
    both = bal.notna() & cust.notna()
    if both.sum() >= 24 and abs(cust[both].sum()) > 1e-6:
        ratio = bal[both].sum() / cust[both].sum()
        if 300 < ratio < 3000:
            bal = bal / 1000.0
            issues.append(f"contorul de post pare în Wh (de {ratio:.0f} ori suma clienților): convertit în kWh")
        elif 3e-4 < ratio < 3e-3:
            cust = cust / 1000.0
            issues.append(f"contoarele clienților par în Wh (contorul de post e de {ratio:.4f} ori suma): convertite în kWh")
    if not has_prosumers and (bal < -0.01).mean() > 0.5:
        bal = bal.abs()
        issues.append("contorul de post are valori negative fără prosumatori: polaritate inversată, folosită valoarea absolută")
    # orele lipsă, pe zi
    day = bal.index.normalize() if bal.index.tz is None else bal.index.tz_convert("Europe/Bucharest").normalize()
    miss = bal.isna().groupby(day).mean()
    usable = [d for d, m in miss.items() if m <= MAX_MISSING_SHARE]
    dropped = [d for d, m in miss.items() if m > MAX_MISSING_SHARE]
    if (miss > 0).any():
        filled = bal.fillna(bal.shift(24))
        n_fill = int((bal.isna() & filled.notna()).sum())
        bal = filled
        if n_fill:
            issues.append(f"{n_fill} ore lipsă la contorul de post completate din ziua precedentă")
    if dropped:
        issues.append(f"{len(dropped)} zile cu peste {MAX_MISSING_SHARE:.0%} ore lipsă la contorul de post: scoase din bilanț")
    return CleanResult(bal, cust, True, usable, issues)
