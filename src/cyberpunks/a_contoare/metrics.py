"""Metricile firului A. Toate primesc etichete binare (1 = problemă reală) și un scor (mai mare = mai suspect).

Clasamentul (top K) rupe egalitățile la întâmplare, cu seed fix: în SGCC primele rânduri sunt chiar clienții cu
furt, deci o sortare stabilă ar favoriza pe nedrept regulile cu multe scoruri egale.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

BUDGET_SHARE = 0.01  # K = 1% din contoare: ~100 de vizite pe săptămână la 10.000 de contoare (3 echipe × ~7 × 5 zile)


def k_for(n: int, share: float = BUDGET_SHARE) -> int:
    return max(1, round(share * n))


def rank(score: np.ndarray, seed: int = 0) -> np.ndarray:
    """Indicii în ordinea descrescătoare a scorului; egalitățile se rup aleator (reproductibil)."""
    s = np.nan_to_num(np.asarray(score, dtype=float), nan=-np.inf)
    jitter = np.random.default_rng(seed).random(len(s))
    return np.lexsort((jitter, -s))


def precision_at_k(y: np.ndarray, score: np.ndarray, k: int, seed: int = 0) -> float:
    top = rank(score, seed)[:k]
    return float(np.asarray(y)[top].mean())


def recall_at_k(y: np.ndarray, score: np.ndarray, k: int, seed: int = 0) -> float:
    y = np.asarray(y)
    if y.sum() == 0:
        return float("nan")
    top = rank(score, seed)[:k]
    return float(y[top].sum() / y.sum())


def value_at_k(value_true: np.ndarray, score: np.ndarray, k: int, seed: int = 0) -> float:
    """Lei recuperați dacă vizităm primele K: suma valorilor reale (0 pentru contoarele fără problemă)."""
    top = rank(score, seed)[:k]
    return float(np.asarray(value_true, dtype=float)[top].sum())


def pr_auc(y: np.ndarray, score: np.ndarray) -> float:
    return float(average_precision_score(y, np.nan_to_num(score, nan=-1e9)))


def roc_auc(y: np.ndarray, score: np.ndarray) -> float:
    return float(roc_auc_score(y, np.nan_to_num(score, nan=-1e9)))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def _bins(p: np.ndarray, n_bins: int, extra_edges: tuple[float, ...] = ()) -> tuple[np.ndarray, np.ndarray]:
    """Marginile bin-urilor (cuantile + praguri fixe) și bin-ul fiecărui scor. Un singur scor unic = un bin."""
    edges = np.unique(np.concatenate([np.quantile(p, np.linspace(0, 1, n_bins + 1)),
                                      [e for e in extra_edges if p.min() < e < p.max()]]))
    if len(edges) < 2:
        return np.array([p.min(), p.max()]), np.zeros(len(p), dtype=int)
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    return edges, idx


def ece(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    """Eroarea de calibrare așteptată, pe bin-uri pe cuantile (scorurile se adună lângă 0)."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    edges, idx = _bins(p, n_bins)
    total = 0.0
    for b in range(len(edges) - 1):
        m = idx == b
        if m.any():
            total += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(total)


def reliability_table(y: np.ndarray, p: np.ndarray, n_bins: int = 10,
                      extra_edges: tuple[float, ...] = (0.1, 0.2, 0.4, 0.6, 0.8)) -> list[dict[str, float]]:
    """Pentru diagrama de calibrare: scorul mediu și frecvența reală pe bin-uri (cuantile + praguri fixe, ca
    scorurile mari, rare la prevalență mică, să nu fie înghesuite într-un singur punct)."""
    y = np.asarray(y, dtype=float)
    p = np.asarray(p, dtype=float)
    edges, idx = _bins(p, n_bins, extra_edges)
    rows = []
    for b in range(len(edges) - 1):
        m = idx == b
        if m.any():
            rows.append({"p_mean": float(p[m].mean()), "freq": float(y[m].mean()), "n": int(m.sum())})
    return rows


def ranking_metrics(y: np.ndarray, score: np.ndarray, k: int, value_true: np.ndarray | None = None) -> dict[str, float]:
    out = {
        "pr_auc": pr_auc(y, score),
        "roc_auc": roc_auc(y, score),
        "precision_at_k": precision_at_k(y, score, k),
        "recall_at_k": recall_at_k(y, score, k),
    }
    if value_true is not None:
        out["value_at_k_lei"] = value_at_k(value_true, score, k)
        best = np.sort(np.asarray(value_true, dtype=float))[::-1][:k].sum()
        out["value_share_at_k"] = float(out["value_at_k_lei"] / best) if best > 0 else float("nan")
    return out


def bootstrap_ci(
    fn: Callable[[np.ndarray, np.ndarray], float], y: np.ndarray, score: np.ndarray, n: int = 300, seed: int = 0
) -> tuple[float, float]:
    """Interval de încredere 95% prin bootstrap (re-eșantionare cu înlocuire a setului de test)."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    score = np.asarray(score)
    vals = []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        if y[i].min() == y[i].max():
            continue
        vals.append(fn(y[i], score[i]))
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def paired_bootstrap_win(
    fn: Callable[[np.ndarray, np.ndarray], float],
    y: np.ndarray,
    score_a: np.ndarray,
    score_b: np.ndarray,
    n: int = 300,
    seed: int = 0,
    groups: np.ndarray | None = None,
) -> float:
    """Ce parte din re-eșantionări dau metrica lui A strict peste a lui B (pe aceleași contoare).

    Cu `groups` (de exemplu gospodăria), re-eșantionăm grupuri întregi, la fel ca intervalele de încredere.
    """
    rng = np.random.default_rng(seed)
    y, a, b = np.asarray(y), np.asarray(score_a), np.asarray(score_b)
    if groups is not None:
        _, inv = np.unique(np.asarray(groups), return_inverse=True)
        members = [np.flatnonzero(inv == g) for g in range(inv.max() + 1)]
    wins = total = 0
    for _ in range(n):
        if groups is None:
            i = rng.integers(0, len(y), len(y))
        else:
            i = np.concatenate([members[g] for g in rng.integers(0, len(members), len(members))])
        if y[i].min() == y[i].max():
            continue
        total += 1
        wins += fn(y[i], a[i]) > fn(y[i], b[i])
    return wins / max(total, 1)
