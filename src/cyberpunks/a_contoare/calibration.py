"""Calibrare, interval de probabilitate și "nu sunt sigur", scrise de noi (fără pachete în plus).

- `VennAbers`: Venn-ABERS inductiv (Vovk & Petej, arXiv 1211.0025). Pentru un scor brut s potrivim două regresii
  izotone pe setul de calibrare plus punctul (s, 0), respectiv (s, 1) și obținem p0 <= p1. Scorul calibrat
  p = p1 / (1 - p0 + p1) stă mereu în [p0, p1]. Calculăm pe o grilă de cuantile și interpolăm (rapid).
- `MondrianConformal`: conformal pe clase (Angelopoulos & Bates, arXiv 2107.07511). Pe calibrare, scorul de
  neconformitate e 1 - p(clasa adevărată); pragul fiecărei clase e o cuantilă corectată pentru eșantion finit.
  Mulțimea de predicție {normal}, {problemă}, ambele sau niciuna; ambele sau niciuna = "nu sunt sigur".
  Garanția: dacă datele noi seamănă cu cele de calibrare, mulțimea conține clasa reală în cel puțin 1 - alpha
  din cazuri, separat pe fiecare clasă.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.isotonic import IsotonicRegression


@dataclass
class VennAbers:
    grid_size: int = 400
    grid: np.ndarray = field(default_factory=lambda: np.empty(0))
    p0: np.ndarray = field(default_factory=lambda: np.empty(0))
    p1: np.ndarray = field(default_factory=lambda: np.empty(0))

    def fit(self, s_cal: np.ndarray, y_cal: np.ndarray) -> VennAbers:
        s_cal = np.asarray(s_cal, dtype=float)
        y_cal = np.asarray(y_cal, dtype=float)
        qs = np.linspace(0, 1, self.grid_size)
        grid = np.unique(np.concatenate([np.quantile(s_cal, qs), [s_cal.min() - 1e-9, s_cal.max() + 1e-9]]))
        p0 = np.empty(len(grid))
        p1 = np.empty(len(grid))
        for i, g in enumerate(grid):
            xs = np.append(s_cal, g)
            for lab, arr in ((0.0, p0), (1.0, p1)):
                ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                ir.fit(xs, np.append(y_cal, lab))
                arr[i] = ir.predict([g])[0]
        self.grid, self.p0, self.p1 = grid, p0, p1
        return self

    def predict(self, s: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Întoarce (p, p0, p1): scorul calibrat și intervalul lui."""
        s = np.asarray(s, dtype=float)
        p0 = np.interp(s, self.grid, self.p0)
        p1 = np.interp(s, self.grid, self.p1)
        p1 = np.maximum(p1, p0)
        p = p1 / (1.0 - p0 + p1)
        return np.clip(p, p0, p1), p0, p1


@dataclass
class MondrianConformal:
    """Conformal pe clase pentru problema binară (0 = normal, 1 = problemă), pe scorul calibrat p."""

    alpha_normal: float = 0.05
    alpha_problem: float = 0.10
    q_normal: float = float("nan")  # includem "normal" dacă p <= q_normal
    q_problem: float = float("nan")  # includem "problemă" dacă 1 - p <= q_problem

    @staticmethod
    def _quantile(scores: np.ndarray, alpha: float) -> float:
        n = len(scores)
        if n == 0:
            return 1.0
        level = min(1.0, np.ceil((n + 1) * (1 - alpha)) / n)
        return float(np.quantile(scores, level, method="higher"))

    def fit(self, p_cal: np.ndarray, y_cal: np.ndarray) -> MondrianConformal:
        p_cal = np.asarray(p_cal, dtype=float)
        y_cal = np.asarray(y_cal).astype(int)
        self.q_normal = self._quantile(p_cal[y_cal == 0], self.alpha_normal)
        self.q_problem = self._quantile(1.0 - p_cal[y_cal == 1], self.alpha_problem)
        return self

    def sets(self, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """(conține_normal, conține_problemă) pentru fiecare scor."""
        p = np.asarray(p, dtype=float)
        return p <= self.q_normal, (1.0 - p) <= self.q_problem

    def decide(self, p: np.ndarray) -> np.ndarray:
        """'problem', 'normal' sau 'unsure' (ambele clase sau niciuna în mulțime)."""
        has0, has1 = self.sets(p)
        out = np.full(len(np.atleast_1d(p)), "unsure", dtype=object)
        out[has1 & ~has0] = "problem"
        out[has0 & ~has1] = "normal"
        return out

    def coverage(self, p: np.ndarray, y: np.ndarray) -> dict[str, float]:
        has0, has1 = self.sets(p)
        y = np.asarray(y).astype(int)
        dec = self.decide(p)
        return {
            "coverage_normal": float(has0[y == 0].mean()) if (y == 0).any() else float("nan"),
            "coverage_problem": float(has1[y == 1].mean()) if (y == 1).any() else float("nan"),
            "unsure_share": float((dec == "unsure").mean()),
            "problem_share": float((dec == "problem").mean()),
        }
