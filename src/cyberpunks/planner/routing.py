"""Traseele echipelor: rutare cu colectare de premii (prize-collecting VRP) cu ferestre de timp.

- Fiecare lucrare candidată e un nod opțional; dacă rămâne nefăcută, se plătește penalitatea = prioritatea ei (în bani).
- Abilități și mărimea echipei: doar echipele potrivite pot lua nodul.
- Depouri multiple: fiecare echipă pleacă de la baza ei și se întoarce acolo.
- Ferestre de timp: sosirea între `earliest` și `latest`; tura (cu instructajul și pauza) limitează traseul.
- Furtună (B): nodul e ultimul din traseu, echipa rămâne în zonă (drumul înapoi costă 0).
- Siguranță: penalitate foarte mare, deci nodul nu e lăsat afară dacă există o echipă care poate ajunge.

Solverul: OR-Tools (PATH_CHEAPEST_ARC, apoi GUIDED_LOCAL_SEARCH), cu limită de timp și de soluții.
Rezerva: inserare greedy în ordinea priorității, cu aceleași restricții, dacă OR-Tools nu dă soluție.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from cyberpunks.planner.geo import TravelModel
from cyberpunks.planner.settings import TZ, Crew, Depot

MANDATORY_PENALTY = 10**10  # bani; mult peste orice valoare reală


@dataclass
class Task:
    id: str
    lat: float
    lon: float
    service_min: int  # durata folosită în traseu (0 pentru nodurile B, unde echipa rămâne)
    display_min: int  # durata scrisă în plan
    skill: str
    crew_size: int
    earliest: int  # minute de la miezul nopții zilei planului
    latest: int
    terminal: bool
    penalty: int  # bani
    mandatory: bool
    allowed: list[int] = field(default_factory=list)  # indicii echipelor care pot lua nodul


@dataclass
class Vehicle:
    crew: Crew
    depot: Depot
    start_min: int
    end_min: int
    cost_per_km: float  # lei
    cost_per_min: float  # lei (oamenii echipei)


@dataclass
class StopOut:
    task_id: str
    seq: int
    arrival_min: int
    travel_km: float
    travel_min: float
    display_min: int


@dataclass
class RouteOut:
    vehicle: Vehicle
    stops: list[StopOut]
    total_km: float
    total_travel_min: float
    total_work_min: int
    depart_min: int = 0
    return_min: int | None = None  # None: echipa rămâne în zonă (furtună)


@dataclass
class RoutingResult:
    routes: list[RouteOut]
    assigned: dict[str, tuple[str, int]]  # task -> (crew_id, seq)
    dropped: dict[str, str]  # task -> motiv: capacity | time_window | no_crew
    solver: str
    status: str
    solve_seconds: float
    objective_lei: float | None = None


class Matrix:
    """Distanțe și timpi între toate punctele (bazele întâi, apoi lucrările)."""

    def __init__(self, points: list[tuple[float, float]], travel: TravelModel) -> None:
        n = len(points)
        self.km = [[0.0] * n for _ in range(n)]
        self.minutes = [[0] * n for _ in range(n)]
        self.minutes_f = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                km = travel.road_km(*points[i], *points[j])
                m = travel.minutes(km)
                self.km[i][j] = self.km[j][i] = km
                self.minutes_f[i][j] = self.minutes_f[j][i] = m
                self.minutes[i][j] = self.minutes[j][i] = round(m)


def minutes_of(t: datetime, plan_date: date) -> int:
    base = datetime.combine(plan_date, datetime.min.time(), tzinfo=TZ)
    return int((t.astimezone(TZ) - base).total_seconds() // 60)


def at_minutes(m: int, plan_date: date) -> datetime:
    return datetime.combine(plan_date, datetime.min.time(), tzinfo=TZ) + timedelta(minutes=m)


@dataclass
class Problem:
    tasks: list[Task]
    vehicles: list[Vehicle]
    depot_nodes: dict[str, int]  # depot_id -> nod
    matrix: Matrix
    value_scale: int = 100

    def node_of_task(self, k: int) -> int:
        return len(self.depot_nodes) + k

    def depot_node(self, v: int) -> int:
        return self.depot_nodes[self.vehicles[v].depot.depot_id]


def build_problem(tasks: list[Task], vehicles: list[Vehicle], travel: TravelModel, value_scale: int = 100) -> Problem:
    depot_ids: list[str] = []
    for v in vehicles:
        if v.depot.depot_id not in depot_ids:
            depot_ids.append(v.depot.depot_id)
    depots = {v.depot.depot_id: v.depot for v in vehicles}
    points = [(depots[d].lat, depots[d].lon) for d in depot_ids] + [(t.lat, t.lon) for t in tasks]
    return Problem(tasks, vehicles, {d: i for i, d in enumerate(depot_ids)}, Matrix(points, travel), value_scale)


# ------------------------------------------------------------------ obiectivul comun (OR-Tools, greedy, comparația lor)


def arc_cost_bani(pb: Problem, v: int, a: int, b: int) -> int:
    """Costul drumului de la nodul a la nodul b pentru echipa v, în bani, rotunjit pe fiecare arc exact ca în OR-Tools.
    Din nodul unei furtuni (terminal) drumul înapoi la bază costă 0: echipa rămâne în zonă."""
    nd = len(pb.depot_nodes)
    if b < nd and a >= nd and pb.tasks[a - nd].terminal:
        return 0
    veh = pb.vehicles[v]
    return round((pb.matrix.km[a][b] * veh.cost_per_km + pb.matrix.minutes_f[a][b] * veh.cost_per_min) * pb.value_scale)


def mandatory_bonus(pb: Problem) -> int:
    """Premiul în plus al unei lucrări obligatorii, în bani: mai mare decât toate premiile opționale la un loc plus orice drum
    posibil (cel mult un arc spre fiecare lucrare și unul de întoarcere pe echipă). Așa, o obligatorie în plus e mereu mai bună,
    la fel în OR-Tools și în solution_value, oricât de mari ar fi valorile de la intrare."""
    optional = sum(max(0, t.penalty) for t in pb.tasks if not t.mandatory)
    km = max((max(row) for row in pb.matrix.km), default=0.0)
    minutes = max((max(row) for row in pb.matrix.minutes_f), default=0.0)
    per_km = max((veh.cost_per_km for veh in pb.vehicles), default=0.0)
    per_min = max((veh.cost_per_min for veh in pb.vehicles), default=0.0)
    arc = round((km * per_km + minutes * per_min) * pb.value_scale) + 1
    return max(MANDATORY_PENALTY, optional + arc * (len(pb.tasks) + len(pb.vehicles)) + 1)


def solution_value(pb: Problem, res: RoutingResult) -> tuple[int, float]:
    """Criteriul comun pentru două soluții: (lucrări obligatorii făcute, premiile lucrărilor făcute minus drumul, în lei).
    Drumul se socotește în bani, rotunjit pe fiecare arc ca în OR-Tools; cu bonusul din mandatory_bonus, ordinea acestor
    perechi e exact ordinea dată de obiectivul OR-Tools."""
    idx = {t.id: k for k, t in enumerate(pb.tasks)}
    vehicle = {veh.crew.crew_id: v for v, veh in enumerate(pb.vehicles)}
    done = [pb.tasks[idx[tid]] for tid in res.assigned]
    travel = 0
    for r in res.routes:
        v = vehicle[r.vehicle.crew.crew_id]
        loc = pb.depot_node(v)
        for st in r.stops:
            node = pb.node_of_task(idx[st.task_id])
            travel += arc_cost_bani(pb, v, loc, node)
            loc = node
        travel += arc_cost_bani(pb, v, loc, pb.depot_node(v))
    return sum(t.mandatory for t in done), (sum(max(0, t.penalty) for t in done) - travel) / pb.value_scale


# ------------------------------------------------------------------ verificarea unui traseu (folosită de greedy și la explicații)


def schedule(pb: Problem, v: int, seq: list[int]) -> tuple[bool, list[int], int]:
    """Orele de sosire pentru o ordine de lucrări. Întoarce (fezabil, sosiri, ora întoarcerii)."""
    veh = pb.vehicles[v]
    t = veh.start_min
    loc = pb.depot_node(v)
    arrivals = []
    for pos, k in enumerate(seq):
        task = pb.tasks[k]
        if task.terminal and pos != len(seq) - 1:
            return False, [], 0
        node = pb.node_of_task(k)
        t = max(t + pb.matrix.minutes[loc][node], task.earliest)
        if t > task.latest or (task.terminal and t > veh.end_min):
            return False, [], 0
        arrivals.append(t)
        t += task.service_min
        loc = node
    if not seq or not pb.tasks[seq[-1]].terminal:
        t += pb.matrix.minutes[loc][pb.depot_node(v)]
        if t > veh.end_min:
            return False, [], 0
    return True, arrivals, t


def route_cost_lei(pb: Problem, v: int, seq: list[int]) -> float:
    veh = pb.vehicles[v]
    loc = pb.depot_node(v)
    cost = 0.0
    for k in seq:
        node = pb.node_of_task(k)
        cost += pb.matrix.km[loc][node] * veh.cost_per_km + pb.matrix.minutes_f[loc][node] * veh.cost_per_min
        loc = node
    if not seq or not pb.tasks[seq[-1]].terminal:
        back = pb.depot_node(v)
        cost += pb.matrix.km[loc][back] * veh.cost_per_km + pb.matrix.minutes_f[loc][back] * veh.cost_per_min
    return cost


def drop_reason(pb: Problem, k: int) -> str:
    """De ce a rămas o lucrare afară: no_crew, time_window (nimeni nu ajunge la timp), not_worth (nici singură
    în traseu drumul dus-întors nu e acoperit de valoarea ei) sau capacity (echipele potrivite sunt ocupate)."""
    task = pb.tasks[k]
    if not task.allowed:
        return "no_crew"
    feasible = [v for v in task.allowed if schedule(pb, v, [k])[0]]
    if not feasible:
        return "time_window"
    if not task.mandatory and all(route_cost_lei(pb, v, [k]) * pb.value_scale >= task.penalty for v in feasible):
        return "not_worth"
    return "capacity"


# ------------------------------------------------------------------ greedy (rezerva)


def solve_greedy(pb: Problem) -> RoutingResult:
    t0 = _time.perf_counter()
    seqs: dict[int, list[int]] = {v: [] for v in range(len(pb.vehicles))}
    order = sorted(range(len(pb.tasks)), key=lambda k: (not pb.tasks[k].mandatory, -pb.tasks[k].penalty))
    dropped: dict[str, str] = {}
    for k in order:
        task = pb.tasks[k]
        best: tuple[float, int, int] | None = None
        for v in task.allowed:
            seq = seqs[v]
            base_cost = route_cost_lei(pb, v, seq)
            last_terminal = bool(seq) and pb.tasks[seq[-1]].terminal
            positions = [len(seq)] if task.terminal else range(len(seq) + (0 if last_terminal else 1))
            if task.terminal and last_terminal:
                continue
            for pos in positions:
                cand = seq[:pos] + [k] + seq[pos:]
                ok, _, _ = schedule(pb, v, cand)
                if not ok:
                    continue
                delta = route_cost_lei(pb, v, cand) - base_cost
                if best is None or delta < best[0]:
                    best = (delta, v, pos)
        if best is not None and (task.mandatory or best[0] * pb.value_scale < task.penalty):
            _, v, pos = best
            seqs[v].insert(pos, k)
        else:
            dropped[task.id] = drop_reason(pb, k) if best is None else "capacity"
    result = _collect(pb, seqs, "greedy", "OK", _time.perf_counter() - t0)
    result.dropped.update(dropped)
    return result


# ------------------------------------------------------------------ OR-Tools


def solve_ortools(pb: Problem, time_limit_s: float = 10.0, solution_limit: int | None = 400,
                  initial: dict[int, list[int]] | None = None) -> RoutingResult | None:
    """VRP cu premii, ferestre de timp și abilități. Cu `initial` (echipă -> lucrări), căutarea pornește de la acele
    trasee; dacă nu se pot citi ca soluție validă, pornește de la zero."""
    from ortools.constraint_solver import pywrapcp, routing_enums_pb2

    t0 = _time.perf_counter()
    n_depots = len(pb.depot_nodes)
    n_nodes = n_depots + len(pb.tasks)
    nv = len(pb.vehicles)
    if nv == 0 or not pb.tasks:
        return _collect(pb, {v: [] for v in range(nv)}, "ortools", "EMPTY", 0.0)
    starts = [pb.depot_node(v) for v in range(nv)]
    manager = pywrapcp.RoutingIndexManager(n_nodes, nv, starts, starts)
    routing = pywrapcp.RoutingModel(manager)
    terminal_nodes = {pb.node_of_task(k) for k, t in enumerate(pb.tasks) if t.terminal}
    service = [0] * n_depots + [t.service_min for t in pb.tasks]
    scale = pb.value_scale
    mins = pb.matrix.minutes
    bonus = mandatory_bonus(pb)

    # Matrice precalculate (mult mai rapide decât funcțiile Python apelate de solver).
    # Din nodul B (terminal) drumul înapoi la bază costă 0: echipa rămâne în zonă.
    cost_idx: dict[tuple[float, float], int] = {}
    for v, veh in enumerate(pb.vehicles):
        key = (veh.cost_per_km, veh.cost_per_min)
        if key not in cost_idx:
            matrix = [[arc_cost_bani(pb, v, a, b) for b in range(n_nodes)] for a in range(n_nodes)]
            cost_idx[key] = routing.RegisterTransitMatrix(matrix)
        routing.SetArcCostEvaluatorOfVehicle(cost_idx[key], v)
    time_matrix = [[0 if a in terminal_nodes else mins[a][b] + service[a] for b in range(n_nodes)] for a in range(n_nodes)]
    t_idx = routing.RegisterTransitMatrix(time_matrix)
    routing.AddDimension(t_idx, 24 * 60, 24 * 60, False, "Time")
    tdim = routing.GetDimensionOrDie("Time")
    for v, veh in enumerate(pb.vehicles):
        tdim.CumulVar(routing.Start(v)).SetRange(veh.start_min, veh.end_min)
        tdim.CumulVar(routing.End(v)).SetRange(veh.start_min, veh.end_min)
        routing.AddVariableMinimizedByFinalizer(tdim.CumulVar(routing.End(v)))
    for k, task in enumerate(pb.tasks):
        index = manager.NodeToIndex(pb.node_of_task(k))
        if task.latest < task.earliest or not task.allowed:
            routing.AddDisjunction([index], 0)
            routing.ActiveVar(index).SetValue(0)
            continue
        tdim.CumulVar(index).SetRange(task.earliest, task.latest)
        # Obligatoriu: bonusul care domină orice altă combinație plus premiul real, ca între două lucrări obligatorii
        # solverul s-o aleagă pe cea mai valoroasă.
        routing.AddDisjunction([index], (bonus if task.mandatory else 0) + max(0, task.penalty))
        routing.VehicleVar(index).SetValues([-1] + list(task.allowed))  # -1 = nefăcut; restul = echipele potrivite
        if task.terminal:
            routing.NextVar(index).SetValues([index] + [routing.End(v) for v in task.allowed])

    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    params.time_limit.FromMilliseconds(max(1, int(time_limit_s * 1000)))
    if solution_limit:
        params.solution_limit = int(solution_limit)
    solution = None
    if initial:
        routing.CloseModelWithParameters(params)
        start_routes = [[manager.NodeToIndex(pb.node_of_task(k)) for k in initial.get(v, [])] for v in range(nv)]
        start = routing.ReadAssignmentFromRoutes(start_routes, True)
        if start is not None:
            solution = routing.SolveFromAssignmentWithParameters(start, params)
    if solution is None:
        solution = routing.SolveWithParameters(params)
    elapsed = _time.perf_counter() - t0
    if solution is None:
        return None
    seqs: dict[int, list[int]] = {}
    for v in range(nv):
        seq = []
        index = solution.Value(routing.NextVar(routing.Start(v)))
        while not routing.IsEnd(index):
            seq.append(manager.IndexToNode(index) - n_depots)
            index = solution.Value(routing.NextVar(index))
        seqs[v] = seq
    status = {0: "NOT_SOLVED", 1: "SUCCESS", 2: "PARTIAL_TIMEOUT", 3: "FAIL", 4: "FAIL_TIMEOUT", 5: "INVALID", 6: "INFEASIBLE", 7: "OPTIMAL"}
    label = status.get(routing.status(), str(routing.status()))
    if elapsed >= 0.98 * time_limit_s:
        # S-a oprit ceasul, nu limita de soluții: rezultatul depinde de viteza calculatorului.
        label = f"{label}, TIME_LIMIT ({time_limit_s:g} s; la altă rulare planul poate diferi)"
    result = _collect(pb, seqs, "ortools", label, elapsed)
    result.objective_lei = solution.ObjectiveValue() / scale
    return result


# ------------------------------------------------------------------ rezultatul


def _collect(pb: Problem, seqs: dict[int, list[int]], solver: str, status: str, seconds: float) -> RoutingResult:
    routes: list[RouteOut] = []
    assigned: dict[str, tuple[str, int]] = {}
    for v, seq in seqs.items():
        if not seq:
            continue
        ok, arrivals, _ = schedule(pb, v, seq)
        if not ok:  # OR-Tools rotunjește la fel ca greedy, deci nu ar trebui să se întâmple; păstrăm ordinea, recalculăm fără verificare
            arrivals = _arrivals_unchecked(pb, v, seq)
        if pb.tasks[seq[-1]].terminal:
            # Furtuna: echipa trebuie să fie în zonă până la ora limită; dimineața rămâne pentru lucrul obișnuit de la bază.
            # Fără să depășească tura: după ea echipa rămâne în zonă (ora suplimentară e în costul turei de furtună).
            arrivals[-1] = max(arrivals[-1], min(pb.tasks[seq[-1]].latest, pb.vehicles[v].end_min))
        veh = pb.vehicles[v]
        loc = pb.depot_node(v)
        stops, total_km, total_min, work = [], 0.0, 0.0, 0
        for pos, (k, arr) in enumerate(zip(seq, arrivals, strict=True), 1):
            node = pb.node_of_task(k)
            d_km, d_min = pb.matrix.km[loc][node], pb.matrix.minutes_f[loc][node]
            stops.append(StopOut(pb.tasks[k].id, pos, arr, round(d_km, 2), d_min, pb.tasks[k].display_min))
            assigned[pb.tasks[k].id] = (veh.crew.crew_id, pos)
            total_km += d_km
            total_min += d_min
            work += pb.tasks[k].display_min
            loc = node
        first = pb.node_of_task(seq[0])
        depart = max(veh.start_min, arrivals[0] - pb.matrix.minutes[pb.depot_node(v)][first])
        ret: int | None = None
        if not pb.tasks[seq[-1]].terminal:
            total_km += pb.matrix.km[loc][pb.depot_node(v)]
            total_min += pb.matrix.minutes_f[loc][pb.depot_node(v)]
            ret = arrivals[-1] + pb.tasks[seq[-1]].service_min + pb.matrix.minutes[loc][pb.depot_node(v)]
        routes.append(RouteOut(veh, stops, round(total_km, 2), total_min, work, depart, ret))
    dropped = {}
    for k, task in enumerate(pb.tasks):
        if task.id not in assigned:
            dropped[task.id] = drop_reason(pb, k)
    return RoutingResult(routes, assigned, dropped, solver, status, seconds)


def _arrivals_unchecked(pb: Problem, v: int, seq: list[int]) -> list[int]:
    t = pb.vehicles[v].start_min
    loc = pb.depot_node(v)
    out = []
    for k in seq:
        node = pb.node_of_task(k)
        t = max(t + pb.matrix.minutes[loc][node], pb.tasks[k].earliest)
        out.append(t)
        t += pb.tasks[k].service_min
        loc = node
    return out


def _subproblem(pb: Problem, keep: list[int]) -> Problem:
    """Aceleași echipe și baze, doar lucrările `keep` (matricea se taie, nu se recalculează)."""
    nd = len(pb.depot_nodes)
    nodes = list(range(nd)) + [nd + k for k in keep]
    m = Matrix([], TravelModel())
    m.km = [[pb.matrix.km[a][b] for b in nodes] for a in nodes]
    m.minutes = [[pb.matrix.minutes[a][b] for b in nodes] for a in nodes]
    m.minutes_f = [[pb.matrix.minutes_f[a][b] for b in nodes] for a in nodes]
    return Problem([pb.tasks[k] for k in keep], pb.vehicles, dict(pb.depot_nodes), m, pb.value_scale)


def solve_ortools_safety_first(pb: Problem, time_limit_s: float = 10.0, solution_limit: int | None = 400) -> RoutingResult | None:
    """Două faze. Întâi doar lucrările obligatorii (siguranța): intră câte încap în ture. Apoi toate lucrările, pornind de la
    traseele lor; penalitatea uriașă a obligatoriilor face ca faza a doua să nu scoată niciuna. Într-o singură fază, căutarea
    se poate bloca la o soluție cu o lucrare obligatorie mai puțin, deși ar fi încăput."""
    mandatory = [k for k, t in enumerate(pb.tasks) if t.mandatory]
    first: RoutingResult | None = None
    initial: dict[int, list[int]] | None = None
    if mandatory and len(mandatory) < len(pb.tasks):
        first = solve_ortools(_subproblem(pb, mandatory), time_limit_s, solution_limit)
        if first is not None and first.routes:
            pos = {t.id: k for k, t in enumerate(pb.tasks)}
            vehicle = {veh.crew.crew_id: v for v, veh in enumerate(pb.vehicles)}
            initial = {vehicle[r.vehicle.crew.crew_id]: [pos[st.task_id] for st in r.stops] for r in first.routes}
    t0 = _time.perf_counter()
    res = solve_ortools(pb, time_limit_s, solution_limit, initial=initial)
    if res is not None and initial:
        res.solve_seconds = round(_time.perf_counter() - t0 + (first.solve_seconds if first else 0.0), 3)
    return res


def solve(pb: Problem, solver: str = "ortools", time_limit_s: float = 10.0, solution_limit: int | None = 400) -> RoutingResult:
    """OR-Tools (întâi siguranța, apoi restul), cu rezerva greedy dacă nu găsește soluție (sau dacă așa cere config-ul).
    Se păstrează soluția mai bună dintre cele două (vezi solution_value)."""
    if solver == "ortools":
        try:
            res = solve_ortools_safety_first(pb, time_limit_s, solution_limit)
        except Exception as exc:  # noqa: BLE001 - orice eroare a solverului trebuie să lase loc rezervei
            res = None
            fallback_note = f"OR-Tools a dat eroare: {exc}"
        else:
            fallback_note = "OR-Tools nu a găsit soluție în timpul dat"
        greedy = solve_greedy(pb)
        if res is None:
            greedy.status = f"FALLBACK ({fallback_note})"
            return greedy
        # Plasă de siguranță ieftină (greedy durează milisecunde): dacă în timpul dat OR-Tools a găsit o soluție mai slabă
        # decât greedy, planul folosește soluția greedy și spune asta în status.
        if solution_value(pb, greedy) > solution_value(pb, res):
            greedy.status = f"GREEDY_BETTER (OR-Tools {res.status} în {res.solve_seconds:.1f} s a dat o soluție mai slabă)"
            greedy.solve_seconds += res.solve_seconds
            return greedy
        return res
    return solve_greedy(pb)

