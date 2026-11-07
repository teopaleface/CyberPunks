"""Calibrare, interval de probabilitate și "nu sunt sigur", scrise de noi (fără pachete în plus).

- `VennAbers`: Venn-ABERS inductiv (Vovk & Petej, arXiv 1211.0025). Pentru un scor brut s potrivim două regresii
  izotone pe setul de calibrare plus punctul (s, 0), respectiv (s, 1) și obținem p0 <= p1. Scorul calibrat
  p = p1 / (1 - p0 + p1) stă mereu în [p0, p1]. Pentru viteză calculăm exact pe o grilă de ~400 de cuantile și
  interpolăm între ele: e o APROXIMARE a metodei exacte; `approx_error()` măsoară abaterea față de calculul exact
  (raportată în reports/A/metrics_full.json).
- `MondrianConformal`: conformal pe clase (Angelopoulos & Bates, arXiv 2107.07511), pe scorul BRUT al modelului
  (funcția de scor e fixată înainte de setul de calibrare, deci split conformal e valid). Scorul de
  neconformitate e s pentru clasa "normal" și 1 - s pentru "problemă"; pragul fiecărei clase e a k-a valoare
  sortată, k = ceil((n + 1)(1 - alpha)). Mulțimea de predicție: {normal}, {problemă}, ambele sau niciuna; ambele
  sau niciuna = "nu sunt sigur". Garanția (dacă rândurile de calibrare și cele noi sunt interschimbabile): mulțimea
  conține clasa reală în cel puțin 1 - alpha din cazuri, separat pe clasă. La Londra, calibrarea are mai multe
  ferestre din aceeași gospodărie, deci raportăm acoperirea ca empirică (măsurată pe test). Atenție: e acoperirea
  MULȚIMII, nu precizia deciziilor; cele două se raportează separat.
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
    s_cal: np.ndarray = field(default_factory=lambda: np.empty(0))
    y_cal: np.ndarray = field(default_factory=lambda: np.empty(0))

    def fit(self, s_cal: np.ndarray, y_cal: np.ndarray) -> VennAbers:
        s_cal = np.asarray(s_cal, dtype=float)
        y_cal = np.asarray(y_cal, dtype=float)
        self.s_cal, self.y_cal = s_cal, y_cal
        qs = np.linspace(0, 1, self.grid_size)
        # cuantile (dese unde sunt multe scoruri) plus puncte egal distanțate (acoperă și zonele rare, cu scoruri mari)
        grid = np.unique(np.concatenate([
            np.quantile(s_cal, qs),
            np.linspace(s_cal.min(), s_cal.max(), self.grid_size),
            [s_cal.min() - 1e-9, s_cal.max() + 1e-9],
        ]))
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
        """Întoarce (p, p0, p1): scorul calibrat și intervalul lui (aproximarea pe grilă)."""
        s = np.asarray(s, dtype=float)
        p0 = np.interp(s, self.grid, self.p0)
        p1 = np.interp(s, self.grid, self.p1)
        p1 = np.maximum(p1, p0)
        p = p1 / (1.0 - p0 + p1)
        return np.clip(p, p0, p1), p0, p1

    def predict_exact(self, s: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Venn-ABERS exact (două regresii izotone pentru fiecare scor). Lent: doar pentru puține puncte."""
        s = np.asarray(s, dtype=float)
        p0 = np.empty(len(s))
        p1 = np.empty(len(s))
        for i, g in enumerate(s):
            xs = np.append(self.s_cal, g)
            for lab, arr in ((0.0, p0), (1.0, p1)):
                ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
                ir.fit(xs, np.append(self.y_cal, lab))
                arr[i] = ir.predict([g])[0]
        p1 = np.maximum(p1, p0)
        p = p1 / (1.0 - p0 + p1)
        return np.clip(p, p0, p1), p0, p1

    def approx_error(self, s: np.ndarray, n: int = 300, seed: int = 0) -> dict[str, float]:
        """Abaterea aproximării pe grilă față de calculul exact, pe n scoruri luate la întâmplare."""
        s = np.asarray(s, dtype=float)
        pick = np.random.default_rng(seed).choice(len(s), size=min(n, len(s)), replace=False)
        a, a0, a1 = self.predict(s[pick])
        e, e0, e1 = self.predict_exact(s[pick])
        return {
            "n": len(pick),
            "max_abs_p": float(np.max(np.abs(a - e))),
            "mean_abs_p": float(np.mean(np.abs(a - e))),
            "max_abs_p0": float(np.max(np.abs(a0 - e0))),
            "max_abs_p1": float(np.max(np.abs(a1 - e1))),
        }


@dataclass
class MondrianConformal:
    """Conformal pe clase pentru problema binară (0 = normal, 1 = problemă), pe un scor s în [0, 1]
    (mai mare = mai suspect). În model folosim scorul brut al LightGBM, nu pe cel calibrat."""

    alpha_normal: float = 0.05
    alpha_problem: float = 0.10
    q_normal: float = float("nan")  # includem "normal" dacă s <= q_normal
    q_problem: float = float("nan")  # includem "problemă" dacă 1 - s <= q_problem

    @staticmethod
    def _quantile(scores: np.ndarray, alpha: float) -> float:
        """A k-a valoare sortată, k = ceil((n + 1)(1 - alpha)); dacă k > n, clasa se include mereu (1,0)."""
        n = len(scores)
        k = int(np.ceil((n + 1) * (1 - alpha)))
        if n == 0 or k > n:
            return 1.0  # scorurile sunt în [0, 1], deci pragul 1,0 include clasa pentru orice contor
        return float(np.sort(np.asarray(scores, dtype=float))[k - 1])

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
        """Acoperirea mulțimilor (garanția) separat de ce înseamnă deciziile (precizie, recall, câte ajung la om)."""
        has0, has1 = self.sets(p)
        y = np.asarray(y).astype(int)
        dec = self.decide(p)
        n0, n1 = (y == 0), (y == 1)

        def share(mask: np.ndarray, cond: np.ndarray) -> float:
            return float(cond[mask].mean()) if mask.any() else float("nan")

        return {
            "set_coverage_normal": share(n0, has0),  # garanția: >= 1 - alpha_normal
            "set_coverage_problem": share(n1, has1),  # garanția: >= 1 - alpha_problem
            "problem_recall_sure": share(n1, dec == "problem"),  # probleme recunoscute SIGUR (mulțimea = {problemă})
            "problem_precision_sure": float(y[dec == "problem"].mean()) if (dec == "problem").any() else float("nan"),
            "problem_to_unsure": share(n1, dec == "unsure"),
            "problem_missed": share(n1, dec == "normal"),
            "normal_to_problem": share(n0, dec == "problem"),  # contoare normale care ar merge spre echipă
            "normal_to_unsure": share(n0, dec == "unsure"),  # contoare normale care ar merge la om
            "unsure_share": float((dec == "unsure").mean()),
            "problem_share": float((dec == "problem").mean()),
        }
