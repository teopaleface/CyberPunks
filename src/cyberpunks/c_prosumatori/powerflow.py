"""Calculul de rețea vectorizat pentru rețelele de joasă tensiune.

pandapower construiește modelul fizic al rețelei (linii, transformator cu priză, magnetizare) și matricea de
admitanțe. Pe matricea lui rezolvăm toate orele deodată, cu metoda Z-bus (punct fix):

    V_L = Z_LL · conj(S_L / V_L) − Z_LL · Y_LS · V_s

Rezultatul e același ca la `pandapower.runpp` (verificat de `validate`), dar un an întreg de ore se rezolvă
într-o fracțiune de secundă. Banca de măsurare:

    uv run python -m cyberpunks.c_prosumatori.powerflow     # scrie reports/C/powerflow_bench.json
"""

from __future__ import annotations

import copy
import json
import time
import warnings
from dataclasses import dataclass

import numpy as np

warnings.filterwarnings("ignore", message=".*numba.*")


@dataclass
class GridModel:
    """Modelul liniarizat al unei rețele: ce trebuie ca să rezolvi circulația de puteri pentru T ore."""

    base_mva: float
    ref: int  # nodul de echilibru (rețeaua de medie tensiune), în indexarea internă pandapower
    L: np.ndarray  # nodurile care nu sunt de echilibru (indexare internă)
    Zll: np.ndarray  # inversa lui Y_LL, complexă (nL, nL)
    w: np.ndarray  # Z_LL · Y_LS, complex (nL,)
    Yss: complex
    Ysl: np.ndarray  # rândul nodului de echilibru, (nL,)
    bus_pos: dict[int, int]  # bus pandapower -> poziția în L
    lv_pos: np.ndarray  # pozițiile în L ale nodurilor de joasă tensiune
    lv_bus: np.ndarray  # busurile pandapower corespunzătoare lui lv_pos
    va_slack_rad: float
    trafo_sn_mva: float

    @classmethod
    def from_net(cls, net) -> GridModel:
        import pandapower as pp

        net = copy.deepcopy(net)
        pp.runpp(net, numba=False)
        internal = net._ppc["internal"]
        Y = internal["Ybus"].toarray()
        ref = int(internal["ref"][0])
        nb = Y.shape[0]
        L = np.setdiff1d(np.arange(nb), [ref])
        Yll = Y[np.ix_(L, L)]
        Yls = Y[L, ref]
        Zll = np.linalg.inv(Yll)
        lookup = net._pd2ppc_lookups["bus"]
        pos_in_L = {int(b): i for i, b in enumerate(L)}
        bus_pos = {int(pd_bus): pos_in_L[int(lookup[pd_bus])] for pd_bus in net.bus.index if int(lookup[pd_bus]) in pos_in_L}
        lv_bus = net.bus.index[(net.bus.vn_kv < 1.0) & net.bus.in_service].to_numpy()
        lv_pos = np.array([bus_pos[int(b)] for b in lv_bus])
        va = float(np.deg2rad(net.ext_grid.va_degree.iloc[0]))
        return cls(
            base_mva=float(net._ppc["baseMVA"]),
            ref=ref,
            L=L,
            Zll=Zll,
            w=Zll @ Yls,
            Yss=complex(Y[ref, ref]),
            Ysl=Y[ref, L],
            bus_pos=bus_pos,
            lv_pos=lv_pos,
            lv_bus=lv_bus,
            va_slack_rad=va,
            trafo_sn_mva=float(net.trafo.sn_mva.sum()),
        )

    @property
    def n(self) -> int:
        return len(self.L)

    def incidence(self, buses: np.ndarray) -> np.ndarray:
        """Matricea (nL, n_elemente) care adună injecțiile elementelor pe noduri."""
        A = np.zeros((self.n, len(buses)))
        for j, b in enumerate(buses):
            A[self.bus_pos[int(b)], j] = 1.0
        return A

    def solve(self, S_mw: np.ndarray, vm_slack: float | np.ndarray, tol: float = 1e-9, maxit: int = 80) -> tuple[np.ndarray, int]:
        """Rezolvă pentru T instantanee deodată.

        S_mw: injecția netă pe noduri (nL, T), complexă, în MW + j·Mvar (generare pozitivă, consum negativ).
        vm_slack: tensiunea rețelei de medie tensiune (pu), scalar sau (T,).
        Întoarce tensiunile complexe (nL, T) și numărul de iterații.
        """
        S = np.asarray(S_mw, dtype=complex) / self.base_mva
        T = S.shape[1]
        vs = np.broadcast_to(np.asarray(vm_slack, dtype=float), (T,)) * np.exp(1j * self.va_slack_rad)
        c = np.outer(self.w, vs)  # (nL, T)
        V = -c.copy()  # tensiunile fără sarcină
        it = 0
        for it in range(1, maxit + 1):
            Vn = self.Zll @ np.conj(S / V) - c
            delta = np.max(np.abs(Vn - V)) if V.size else 0.0
            V = Vn
            if delta < tol:
                break
        return V, it

    def slack_power_mva(self, V: np.ndarray, vm_slack: float | np.ndarray) -> np.ndarray:
        """Puterea schimbată cu rețeaua de medie tensiune (MVA complex, pozitiv = consum din MT)."""
        T = V.shape[1]
        vs = np.broadcast_to(np.asarray(vm_slack, dtype=float), (T,)) * np.exp(1j * self.va_slack_rad)
        i_s = self.Yss * vs + self.Ysl @ V
        return vs * np.conj(i_s) * self.base_mva


def snapshot_injections(net, model: GridModel) -> np.ndarray:
    """Injecția netă pe noduri (nL,) din tabelele pandapower (load, sgen), pentru verificare."""
    S = np.zeros(model.n, dtype=complex)
    for tab, sign in (("load", -1.0), ("sgen", 1.0)):
        df = getattr(net, tab)
        df = df[df.in_service]
        for b, p, q, s in zip(df.bus, df.p_mw, df.q_mvar, df.scaling, strict=True):
            S[model.bus_pos[int(b)]] += sign * (p + 1j * q) * s
    return S


def validate(net, model: GridModel, n: int = 100, seed: int = 0) -> dict:
    """Compară calculul vectorizat cu pandapower.runpp pe n instantanee aleatoare (consum și PV variate)."""
    import pandapower as pp

    net = copy.deepcopy(net)
    rng = np.random.default_rng(seed)
    p_s0, q_s0 = net.sgen.p_mw.to_numpy().copy(), net.sgen.q_mvar.to_numpy().copy()
    p_l0, q_l0 = net.load.p_mw.to_numpy().copy(), net.load.q_mvar.to_numpy().copy()
    vm0 = float(net.ext_grid.vm_pu.iloc[0])
    S_cols, vms, v_pp, t_pp = [], [], [], []
    lv_mask = np.isin(net.bus.index.to_numpy(), model.lv_bus)
    for _ in range(n):
        a = rng.uniform(0.0, 1.0, len(p_s0))
        b = rng.uniform(0.05, 1.3, len(p_l0))
        vm = vm0 + rng.uniform(-0.02, 0.02)
        net.sgen.p_mw, net.sgen.q_mvar = p_s0 * a, q_s0 * a
        net.load.p_mw, net.load.q_mvar = p_l0 * b, q_l0 * b
        net.ext_grid.vm_pu = vm
        t0 = time.perf_counter()
        pp.runpp(net, numba=False)
        t_pp.append(time.perf_counter() - t0)
        res = net.res_bus.vm_pu.to_numpy()[lv_mask]
        order = np.argsort(net.bus.index.to_numpy()[lv_mask])
        v_pp.append(res[order])
        S_cols.append(snapshot_injections(net, model))
        vms.append(vm)
    S = np.array(S_cols).T
    t0 = time.perf_counter()
    V, iters = model.solve(S, np.array(vms))
    t_vec = time.perf_counter() - t0
    lv_order = np.argsort(model.lv_bus)
    v_vec = np.abs(V[model.lv_pos[lv_order], :]).T
    diff = np.abs(v_vec - np.array(v_pp))
    return {
        "snapshots": n,
        "max_abs_diff_pu": float(diff.max()),
        "pandapower_ms_per_snapshot_median": float(np.median(t_pp) * 1e3),
        "vectorized_ms_per_snapshot": float(t_vec / n * 1e3),
        "iterations": int(iters),
        "vmax_range_pu": [float(np.array(v_pp).max(1).min()), float(np.array(v_pp).max(1).max())],
    }


def bench(out_path=None, hours: int = 8760, seed: int = 0) -> dict:
    """Pentru fiecare topologie SimBench: verificare față de pandapower și timpul pentru un an de ore."""
    from cyberpunks.c_prosumatori import grids
    from cyberpunks.common.paths import REPORTS

    rng = np.random.default_rng(seed)
    rows = {}
    for topo in grids.TOPOLOGIES:
        spec = grids.sample_spec(topo, rng, post_id=f"BENCH-{topo}", mode="train")
        post = grids.build_post(spec)
        model = post.model
        val = validate(post.net, model, n=100, seed=seed)
        # un an de ore cu injecții aleatoare plauzibile
        S = snapshot_injections(post.net, model)[:, None] * rng.uniform(0.0, 1.0, (1, hours))
        t0 = time.perf_counter()
        _, it = model.solve(S, 1.02)
        t_year = time.perf_counter() - t0
        rows[topo] = {
            "lv_buses": len(model.lv_bus),
            "pv_kw": round(float(post.pv_kwp.sum()), 1),
            **val,
            "year_hours": hours,
            "vectorized_s_per_year": round(t_year, 4),
            "pandapower_s_per_year_est": round(val["pandapower_ms_per_snapshot_median"] * hours / 1e3, 1),
            "iterations_year": int(it),
        }
    out = {
        "what": "Calcul vectorizat Z-bus pe matricea de admitanțe pandapower, comparat cu pandapower.runpp",
        "pandapower_numba": False,
        "machine_note": "MacBook M5 Max, mașină împărțită cu alte 5 fire; timpii variază",
        "topologies": rows,
    }
    out_path = out_path or (REPORTS / "C" / "powerflow_bench.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    res = bench()
    print(f"{'topologie':10} {'noduri':>6} {'dif. max pu':>12} {'pp ms/oră':>10} {'vect ms/oră':>12} {'an vect s':>10} {'an pp s':>8}")
    for k, r in res["topologies"].items():
        print(
            f"{k:10} {r['lv_buses']:6d} {r['max_abs_diff_pu']:12.2e} {r['pandapower_ms_per_snapshot_median']:10.2f} "
            f"{r['vectorized_ms_per_snapshot']:12.4f} {r['vectorized_s_per_year']:10.3f} {r['pandapower_s_per_year_est']:8.1f}"
        )
