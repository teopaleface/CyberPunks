import "server-only";
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";
import { dotRowsPath, makeProjection, outlinePath, snap, type CountyFeature } from "./geo";

/**
 * Datele landing-ului se citesc la build din repo, nu se scriu de mână:
 * - planul real al agentului pentru ziua demo: `outputs/demo/plans/demo-vara/` (instantaneul din git);
 * - bazele operative: `config/area.yaml` (simulate);
 * - cifrele modelelor: `reports/<A|B|C|bilant>/metrics.json` și `reports/planner/agent_eval.json`.
 * Dacă un fișier lipsește, secțiunea arată „în lucru”, fără cifră.
 */

const ROOT = path.resolve(process.cwd(), "..");
const DEMO = path.join(ROOT, "outputs", "demo", "plans", "demo-vara");

function readJson<T>(file: string): T | null {
  try {
    return JSON.parse(readFileSync(file, "utf8")) as T;
  } catch {
    return null;
  }
}

export type Source = "A" | "B" | "C";
export type ItemState = "route" | "human" | "remote" | "deferred" | "notify";

interface WorkItem {
  work_item_id: string;
  source: Source;
  location: { lat: number; lon: number; county?: string; label?: string };
  prediction?: { score?: number; confidence?: string; model_id?: string };
}
interface Decision {
  work_item_id: string;
  decision: "assigned" | "human_review" | "remote_action" | "deferred" | "notify";
  crew_id: string | null;
}
interface Route {
  crew_id: string;
  depot_id: string;
  stops: { work_item_id: string }[];
  total_km: number;
}
interface Plan {
  plan_id: string;
  plan_date: string;
  summary: {
    items_in: number;
    assigned: number;
    deferred: number;
    human_review: number;
    remote_actions: number;
    notifications: number;
    crews_used: number;
    expected_value_lei: number;
    total_km: number;
  };
  routes: Route[];
  decisions: Decision[];
}
interface Depot {
  depot_id: string;
  lat: number;
  lon: number;
}

export interface DemoPlan {
  plan: Plan;
  items: Map<string, WorkItem>;
  state: Map<string, ItemState>;
  depots: Map<string, Depot>;
  bySource: Record<Source, number>;
}

let demoCache: DemoPlan | null | undefined;

export function loadDemoPlan(): DemoPlan | null {
  if (demoCache !== undefined) return demoCache;
  const plan = readJson<Plan>(path.join(DEMO, "plan.json"));
  const itemsFile = path.join(DEMO, "work_items.jsonl");
  if (!plan || !existsSync(itemsFile)) return (demoCache = null);
  const items = new Map<string, WorkItem>();
  for (const line of readFileSync(itemsFile, "utf8").split("\n")) {
    if (!line.trim()) continue;
    const it = JSON.parse(line) as WorkItem;
    items.set(it.work_item_id, it);
  }
  const toState: Record<Decision["decision"], ItemState> = {
    assigned: "route",
    human_review: "human",
    remote_action: "remote",
    deferred: "deferred",
    notify: "notify",
  };
  const state = new Map<string, ItemState>();
  for (const d of plan.decisions) state.set(d.work_item_id, toState[d.decision]);
  const area = (() => {
    try {
      return parseYaml(readFileSync(path.join(ROOT, "config", "area.yaml"), "utf8")) as { depots?: Depot[] };
    } catch {
      return null;
    }
  })();
  const depots = new Map<string, Depot>((area?.depots ?? []).map((d) => [d.depot_id, d]));
  const bySource: Record<Source, number> = { A: 0, B: 0, C: 0 };
  for (const it of items.values()) bySource[it.source] += 1;
  return (demoCache = { plan, items, state, depots, bySource });
}

/* ------------------------------------------------------------------ harta din hero */

export interface HeroMapData {
  width: number;
  height: number;
  pitch: number;
  restDots: string;
  reDots: string;
  reOutline: string;
  /** lucrările, adunate pe celulele grilei (o celulă = un punct aprins) */
  cells: { x: number; y: number; src: Source; n: number; human: boolean; order: number }[];
  /** traseele care se văd la scara țării (Banat), depou → opriri → depou */
  routes: { d: string; crew: string }[];
  depots: { x: number; y: number }[];
  /** lupa peste București și Ilfov */
  lens: {
    cx: number;
    cy: number;
    r: number;
    anchor: { x: number; y: number };
    size: number;
    items: { x: number; y: number; src: Source; state: ItemState }[];
    routes: { d: string; crew: string; km: number }[];
    depots: { x: number; y: number }[];
  } | null;
  plan: {
    date: string;
    itemsIn: number;
    assigned: number;
    remote: number;
    human: number;
    deferred: number;
    crews: number;
    km: number;
    bySource: Record<Source, number>;
  } | null;
}

const RO_BOUNDS: [number, number, number, number] = [20.243, 43.65, 29.7, 48.275];
// lupa: București și Ilfov, unde stau contoarele (A) și posturile (C) din scenariul demo
const LENS_BOUNDS: [number, number, number, number] = [25.86, 44.255, 26.33, 44.585];

export function loadHeroMap(): HeroMapData {
  const geo = readJson<{ features: CountyFeature[] }>(path.join(process.cwd(), "data", "ro-judete.json"));
  const width = 1000;
  const pitch = 9;
  const proj = makeProjection(RO_BOUNDS, width);
  const features = geo?.features ?? [];
  const re = features.filter((f) => f.properties.re_region);
  const rest = features.filter((f) => !f.properties.re_region);
  const reDots = dotRowsPath(re, proj, pitch).d;
  const restDots = dotRowsPath(rest, proj, pitch).d;
  const reOutline = outlinePath(re, proj);

  const demo = loadDemoPlan();
  if (!demo) {
    return { width, height: proj.height, pitch, restDots, reDots, reOutline, cells: [], routes: [], depots: [], lens: null, plan: null };
  }

  // celulele aprinse la scara țării
  const cellMap = new Map<string, { x: number; y: number; counts: Record<Source, number>; human: boolean }>();
  for (const it of demo.items.values()) {
    const x = snap(proj.x(it.location.lon), pitch);
    const y = snap(proj.y(it.location.lat), pitch);
    const key = `${x}|${y}`;
    const c = cellMap.get(key) ?? { x, y, counts: { A: 0, B: 0, C: 0 }, human: false };
    c.counts[it.source] += 1;
    if (demo.state.get(it.work_item_id) === "human") c.human = true;
    cellMap.set(key, c);
  }
  const cells = [...cellMap.values()]
    .map((c) => {
      // culoarea celulei: sursa rară câștigă (B și C se pierd altfel sub sutele de contoare A)
      const src: Source = c.counts.B > 0 ? "B" : c.counts.C > 0 ? "C" : "A";
      return { x: c.x, y: c.y, src, n: c.counts.A + c.counts.B + c.counts.C, human: c.human, order: 0 };
    })
    .sort((a, b) => a.x - b.x)
    .map((c, i, all) => ({ ...c, order: Math.round((i / Math.max(1, all.length - 1)) * 100) / 100 }));

  const lensR = 172;
  const bx = proj.x(26.1);
  const by = proj.y(44.43);
  const lensCenter = { x: proj.x(26.95), y: proj.y(47.02) };
  const lensProj = makeProjection(LENS_BOUNDS, lensR * 2);
  const inLens = (lat: number, lon: number) => lon >= LENS_BOUNDS[0] && lon <= LENS_BOUNDS[2] && lat >= LENS_BOUNDS[1] && lat <= LENS_BOUNDS[3];
  const lx = (lon: number) => lensCenter.x - lensR + lensProj.x(lon);
  const ly = (lat: number) => lensCenter.y - lensProj.height / 2 + lensProj.y(lat);

  const routes: HeroMapData["routes"] = [];
  const lensRoutes: NonNullable<HeroMapData["lens"]>["routes"] = [];
  const depotPts: HeroMapData["depots"] = [];
  const lensDepots: NonNullable<HeroMapData["lens"]>["depots"] = [];
  const seenDepots = new Set<string>();
  for (const r of demo.plan.routes) {
    const dep = demo.depots.get(r.depot_id);
    const stops = r.stops.map((s) => demo.items.get(s.work_item_id)).filter((x): x is WorkItem => !!x);
    if (!dep || stops.length === 0) continue;
    const pts = [dep, ...stops.map((s) => s.location), dep];
    const lensRoute = inLens(dep.lat, dep.lon);
    const fx = lensRoute ? lx : proj.x;
    const fy = lensRoute ? ly : proj.y;
    const d = `M${pts.map((p) => `${fx(p.lon).toFixed(1)},${fy(p.lat).toFixed(1)}`).join("L")}`;
    if (lensRoute) lensRoutes.push({ d, crew: r.crew_id, km: r.total_km });
    else routes.push({ d, crew: r.crew_id });
    if (!seenDepots.has(r.depot_id)) {
      seenDepots.add(r.depot_id);
      (lensRoute ? lensDepots : depotPts).push({ x: fx(dep.lon), y: fy(dep.lat) });
    }
  }

  const lensItems = [...demo.items.values()]
    .filter((it) => it.source !== "B" && inLens(it.location.lat, it.location.lon))
    .map((it) => ({ x: lx(it.location.lon), y: ly(it.location.lat), src: it.source, state: demo.state.get(it.work_item_id) ?? "deferred" }))
    // traseele și cazurile pentru om deasupra
    .sort((a, b) => rank(a.state) - rank(b.state));

  const s = demo.plan.summary;
  return {
    width,
    height: proj.height,
    pitch,
    restDots,
    reDots,
    reOutline,
    cells,
    routes,
    depots: depotPts,
    lens: { cx: lensCenter.x, cy: lensCenter.y, r: lensR, anchor: { x: bx, y: by }, size: lensR * 2, items: lensItems, routes: lensRoutes, depots: lensDepots },
    plan: {
      date: demo.plan.plan_date,
      itemsIn: s.items_in,
      assigned: s.assigned,
      remote: s.remote_actions,
      human: s.human_review,
      deferred: s.deferred,
      crews: s.crews_used,
      km: s.total_km,
      bySource: demo.bySource,
    },
  };
}

function layer(it: { src: Source; state: ItemState }): number {
  if (it.state === "route" || it.state === "human") return 10 + rank(it.state);
  return it.src === "C" ? 5 : rank(it.state);
}

function rank(s: ItemState): number {
  return { deferred: 0, notify: 1, remote: 2, human: 3, route: 4 }[s];
}

/* ------------------------------------------------------------------ harta orașului (secțiunea „How it works”) */

export interface CityMapData {
  width: number;
  height: number;
  pitch: number;
  dots: string;
  items: { x: number; y: number; src: Source; state: ItemState; score: number }[];
  routes: { d: string; crew: string; km: number }[];
  depots: { x: number; y: number }[];
  counts: { items: number; route: number; human: number; remote: number; crews: number; km: number };
}

// București și Ilfov, unde stau contoarele (A) și posturile (C) din scenariul demo
const CITY_BOUNDS: [number, number, number, number] = [25.84, 44.24, 26.36, 44.6];

export function loadCityMap(): CityMapData | null {
  const demo = loadDemoPlan();
  const geo = readJson<{ features: CountyFeature[] }>(path.join(process.cwd(), "data", "ro-judete.json"));
  if (!demo || !geo) return null;
  const width = 1000;
  const pitch = 14;
  const proj = makeProjection(CITY_BOUNDS, width);
  const area = geo.features.filter((f) => ["București", "Ilfov"].includes(f.properties.name));
  const dots = dotRowsPath(area, proj, pitch).d;
  const inBox = (lat: number, lon: number) => lon >= CITY_BOUNDS[0] && lon <= CITY_BOUNDS[2] && lat >= CITY_BOUNDS[1] && lat <= CITY_BOUNDS[3];
  const items = [...demo.items.values()]
    .filter((it) => it.source !== "B" && inBox(it.location.lat, it.location.lon))
    .map((it) => ({
      x: proj.x(it.location.lon),
      y: proj.y(it.location.lat),
      src: it.source,
      state: demo.state.get(it.work_item_id) ?? ("deferred" as ItemState),
      score: Math.max(0, Math.min(1, it.prediction?.score ?? 0.5)),
    }))
    // ordinea desenării: lucrările stinse jos, posturile C peste lucrările de bilanț de pe același post,
    // cazurile pentru om și opririle din trasee deasupra
    .sort((a, b) => layer(a) - layer(b));
  const routes: CityMapData["routes"] = [];
  const depots: CityMapData["depots"] = [];
  const seen = new Set<string>();
  for (const r of demo.plan.routes) {
    const dep = demo.depots.get(r.depot_id);
    if (!dep || !inBox(dep.lat, dep.lon)) continue;
    const stops = r.stops.map((st) => demo.items.get(st.work_item_id)).filter((x): x is WorkItem => !!x);
    const pts = [dep, ...stops.map((st) => st.location), dep];
    routes.push({ d: `M${pts.map((pt) => `${proj.x(pt.lon).toFixed(1)},${proj.y(pt.lat).toFixed(1)}`).join("L")}`, crew: r.crew_id, km: r.total_km });
    if (!seen.has(r.depot_id)) {
      seen.add(r.depot_id);
      depots.push({ x: proj.x(dep.lon), y: proj.y(dep.lat) });
    }
  }
  const s = demo.plan.summary;
  return {
    width,
    height: proj.height,
    pitch,
    dots,
    items,
    routes,
    depots,
    counts: { items: s.items_in, route: s.assigned, human: s.human_review, remote: s.remote_actions, crews: s.crews_used, km: s.total_km },
  };
}

/* ------------------------------------------------------------------ cifrele modelelor (doar din reports/) */

interface ModelReport {
  model_id: string;
  model_version: string;
  created_at: string;
  test_size: number;
  synthetic_share: number;
  reproduce_cmd: string;
  metrics: Record<string, number>;
  baseline_metrics: Record<string, number>;
}

export interface ModelResult {
  key: "A" | "bilant" | "B" | "C";
  version: string;
  file: string;
  createdAt: string;
  reproduce: string;
  syntheticShare: number;
  /** cifra principală afișată mare și reperul simplu cel mai puternic, cu numele lui */
  ours: number;
  baseline: number;
  baselineName: string;
  /** câte ori mai bine (raport sau inversul lui, după direcția metricii) */
  factor: number;
  extra: Record<string, number>;
}

function readReport(key: string): ModelReport | null {
  return readJson<ModelReport>(path.join(ROOT, "reports", key, "metrics.json"));
}

/** cel mai puternic reper simplu dintr-o listă [valoare, nume], pentru metrici unde mai mare = mai bine */
function bestOf(cands: [number | undefined, string][]): [number, string] {
  const ok = cands.filter((c): c is [number, string] => typeof c[0] === "number");
  return ok.reduce((a, b) => (b[0] > a[0] ? b : a), ok[0] ?? [Number.NaN, ""]);
}

export function loadModelResults(): Partial<Record<ModelResult["key"], ModelResult>> {
  const out: Partial<Record<ModelResult["key"], ModelResult>> = {};
  const base = (key: string, r: ModelReport) => ({
    version: r.model_version,
    file: `reports/${key}/metrics.json`,
    createdAt: r.created_at,
    reproduce: r.reproduce_cmd,
    syntheticShare: r.synthetic_share,
  });

  const a = readReport("A");
  if (a) {
    // problemele subtile (Londra): precizia@K; reperul: cea mai bună dintre regula simplă și regula VEE completă
    const [bS, nS] = bestOf([
      [a.baseline_metrics.subtle_precision_at_k, "simple rule"],
      [a.metrics.subtle_vee_precision_at_k, "full VEE rule"],
    ]);
    const [bG, nG] = bestOf([
      [a.baseline_metrics.sgcc_precision_at_k, "simple rule"],
      [a.metrics.sgcc_vee_precision_at_k, "full VEE rule"],
      [a.metrics.sgcc_iforest_precision_at_k, "Isolation Forest"],
    ]);
    out.A = {
      key: "A",
      ...base("A", a),
      ours: a.metrics.subtle_precision_at_k,
      baseline: bS,
      baselineName: nS,
      factor: a.metrics.subtle_precision_at_k / bS,
      extra: { sgcc: a.metrics.sgcc_precision_at_k, sgccBaseline: bG, sgccFactor: a.metrics.sgcc_precision_at_k / bG, sgccIsIforest: nG === "Isolation Forest" ? 1 : 0 },
    };
  }

  const bil = readReport("bilant");
  if (bil) {
    const ours = bil.metrics.normal_mae_kwh_day;
    const baseline = bil.baseline_metrics.normal_mae_kwh_day;
    out.bilant = {
      key: "bilant",
      ...base("bilant", bil),
      ours,
      baseline,
      baselineName: "physics formula (I²R)",
      factor: baseline / ours,
      extra: {
        f1: bil.metrics.diagnoza_macro_f1,
        f1Baseline: bil.baseline_metrics.diagnoza_macro_f1,
        fusionP10: bil.metrics.fuziune_precision_at_10,
        fusionP10Baseline: bil.baseline_metrics.fuziune_precision_at_10,
        invisibleShare: bil.metrics.invizibil_share_invisible_to_meters,
      },
    };
  }

  const b = readReport("B");
  if (b) {
    const [bb, nb] = bestOf([
      [b.baseline_metrics.pr_auc, "county climatology"],
      [b.metrics.pr_auc_gust_rule, "wind-gust rule"],
    ]);
    out.B = {
      key: "B",
      ...base("B", b),
      ours: b.metrics.pr_auc,
      baseline: bb,
      baselineName: nb,
      factor: b.metrics.pr_auc / bb,
      extra: { coverage: b.metrics.coverage_p10_p90, recallSevere: b.metrics.recall_severe_at_thr },
    };
  }

  const c = readReport("C");
  if (c) {
    const ours = c.metrics.mae_vmax_pu;
    const baseline = c.baseline_metrics.mae_vmax_pu;
    out.C = {
      key: "C",
      ...base("C", c),
      ours,
      baseline,
      baselineName: "linear regression on sunlight",
      factor: baseline / ours,
      extra: {
        prAuc: c.metrics.pr_auc_exceed,
        prAucBaseline: c.baseline_metrics.pr_auc_exceed,
        surrogateSeconds: c.metrics.surrogate_seconds_300_posts_day,
        powerflowSeconds: c.metrics.powerflow_seconds_300_posts_day_pandapower,
      },
    };
  }
  return out;
}

/* ------------------------------------------------------------------ evaluarea agentului (reports/planner/agent_eval.json) */

export interface AgentEval {
  file: string;
  reproduce: string;
  days: number;
  synthetic: boolean;
  strategies: { key: string; label: string; perDay: number; kmPerDay: number; urgentMissed: number; useless: number }[];
  uplift: number;
  bestSimple: string;
}

const STRATEGY_LABELS: Record<string, string> = {
  agent: "Daybreak",
  top_k_scor: "Highest score first",
  primul_venit: "First come, first served",
  aleator: "Random",
  doar_contoare: "Meters only",
};

export function loadAgentEval(): AgentEval | null {
  const e = readJson<{
    reproduce_cmd: string;
    synthetic: boolean;
    main: {
      days: number;
      strategies: Record<
        string,
        { net_value_lei_per_day: number; km_per_day: number; urgent_missed_rate: number; useless_visit_rate: number }
      >;
    };
  }>(path.join(ROOT, "reports", "planner", "agent_eval.json"));
  if (!e?.main?.strategies?.agent) return null;
  const strategies = Object.entries(e.main.strategies)
    .map(([key, v]) => ({
      key,
      label: STRATEGY_LABELS[key] ?? key,
      perDay: v.net_value_lei_per_day,
      kmPerDay: v.km_per_day,
      urgentMissed: v.urgent_missed_rate,
      useless: v.useless_visit_rate,
    }))
    .sort((x, y) => y.perDay - x.perDay);
  const agent = strategies.find((s) => s.key === "agent")!;
  const best = strategies.filter((s) => s.key !== "agent").sort((x, y) => y.perDay - x.perDay)[0];
  return {
    file: "reports/planner/agent_eval.json",
    reproduce: e.reproduce_cmd,
    days: e.main.days,
    synthetic: e.synthetic,
    strategies,
    uplift: agent.perDay / best.perDay - 1,
    bestSimple: best.label,
  };
}

/* ------------------------------------------------------------------ cazurile reale din planul demo, pentru secțiuni */

interface FullItem extends WorkItem {
  kind: string;
  prediction: {
    model_id: string;
    model_version: string;
    prediction_id: string;
    label: string;
    score: number;
    interval_low: number | null;
    interval_high: number | null;
    confidence: string;
    point_estimate: number | null;
  };
  impact: { expected_value_lei: number; customers_affected: number | null; safety_flag: boolean };
  time_window: { start: string; end: string } | null;
  explanation: {
    top_factors: { feature: string; value: number; contribution: number }[];
    similar_cases: { outcome: string; similarity: number }[];
  };
  extra?: { remedy_options?: RemedyOption[] };
}
interface RemedyOption {
  action: string;
  cost_lei: number;
  p90_after_pu: number;
  needs_crew: boolean;
  participation_rate?: number;
}
interface FullDecision extends Decision {
  rule_id: string;
  threshold: Record<string, number>;
  audit_id: string;
}
interface ArrivalStop {
  work_item_id: string;
  seq: number;
  eta: string;
}

/** etichetele în engleză ale factorilor (din valorile structurate, nu din textul românesc) */
function factorLabel(feature: string, v: number): string | null {
  const pct = (x: number) => `${Math.round(x * 100)}%`;
  switch (feature) {
    case "missing_recent":
      return `${pct(v)} of the last four weeks without data`;
    case "longest_gap":
      return `${Math.round(v)} days in a row without data`;
    case "missing_ratio":
      return `${pct(v)} of all readings missing`;
    case "max_over_median":
      return `Peak reading ${v.toFixed(1)}× the median`;
    case "spike_slot_count":
      return `${Math.round(v)} half-hour reading${Math.round(v) === 1 ? "" : "s"} with an impossible jump`;
    case "zero_slot_run_recent":
      return `${v.toFixed(1)} hours a day at exactly zero`;
    case "negative_slot_share":
      return `${pct(v)} of readings negative`;
    case "flat_slot_share_recent":
      return `${pct(v)} of readings perfectly flat`;
    case "night_share_recent":
      return `${pct(v)} of consumption at night`;
    case "peer_ratio_slope":
      return `${pct(Math.abs(v))} a month ${v < 0 ? "below" : "above"} the neighbors`;
    case "precip_48h":
      return `${Math.round(v)} mm of rain in 48 hours`;
    case "gust_prev":
      return `${Math.round(v)} km/h gusts the day before`;
    case "gust_max":
      return `${Math.round(v)} km/h gusts forecast`;
    case "precip_hours":
      return `${Math.round(v)} hours of rain`;
    case "log_density":
      return `${Math.round(v)} customers per km² of grid`;
    default:
      return null;
  }
}

const ACTION_LABELS: Record<string, string> = {
  notify_customers: "Ask neighbors to use power at noon",
  offer_battery: "Offer home batteries, sized per home",
  phase_rebalance: "Move three homes to another phase",
  adjust_tap: "Lower the transformer tap for summer",
  export_limit: "Cap solar export at peak hours",
  transformer_upgrade: "Install a bigger transformer",
};

export interface Stories {
  ladder: {
    label: string;
    before: number;
    after: number;
    cost: number;
    steps: { action: string; label: string; cost: number; aloneAfter: number; chosen: boolean; needsCrew: boolean }[];
    battery: { kwh: number; customers: number; revenue: number; payback: number } | null;
    tripsAvoided: number | null;
  } | null;
  human: {
    title: string;
    place: string;
    window: string | null;
    score: number;
    customers: number | null;
    value: number;
    factors: string[];
    model: string;
    queue: { total: number; abstain: number; cap: number; low: number };
  } | null;
  explain: {
    meter: string;
    place: string;
    label: string;
    score: number;
    low: number | null;
    high: number | null;
    model: string;
    predictionId: string;
    factors: { label: string; contribution: number }[];
    similar: { outcome: string; n: number } | null;
    value: number;
    cost: number;
    actionCost: number | null;
    travelCost: number | null;
    km: number | null;
    crew: string | null;
    stop: number | null;
    eta: string | null;
    rule: string;
    auditId: string;
  } | null;
}

export function loadStories(): Stories {
  const demo = loadDemoPlan();
  if (!demo) return { ladder: null, human: null, explain: null };
  const items = demo.items as Map<string, FullItem>;
  const decisions = demo.plan.decisions as FullDecision[];

  // scara de soluții: postul cu tensiunea cea mai mare care se rezolvă fără investiție
  const remedies =
    readJson<{ work_item_id: string; label: string; feasible: boolean; invest: boolean; chosen: string[]; cost_lei: number; p90_before_pu: number; p90_after_pu: number; battery?: { battery_kwh_total: number; customers_targeted: number; revenue_lei: number; payback_years: number }; inverter_trips_avoided?: number }[]>(
      path.join(DEMO, "remedies.json"),
    ) ?? [];
  const pick = remedies.filter((r) => r.feasible && !r.invest).sort((x, y) => y.p90_before_pu - x.p90_before_pu)[0];
  let ladder: Stories["ladder"] = null;
  if (pick) {
    const opts = items.get(pick.work_item_id)?.extra?.remedy_options ?? [];
    ladder = {
      label: pick.label.replace(" (sintetic)", ""),
      before: pick.p90_before_pu,
      after: pick.p90_after_pu,
      cost: pick.cost_lei,
      steps: [...opts]
        .sort((x, y) => x.cost_lei - y.cost_lei)
        .map((o) => ({
          action: o.action,
          label: ACTION_LABELS[o.action] ?? o.action,
          cost: o.cost_lei,
          aloneAfter: o.p90_after_pu,
          chosen: pick.chosen.includes(o.action),
          needsCrew: o.needs_crew,
        })),
      battery: pick.battery
        ? { kwh: pick.battery.battery_kwh_total, customers: pick.battery.customers_targeted, revenue: pick.battery.revenue_lei, payback: pick.battery.payback_years }
        : null,
      tripsAvoided: pick.inverter_trips_avoided ?? null,
    };
  }

  // omul în buclă: cazul cu încredere mică (sau primul caz trimis la om)
  const humans = decisions.filter((d) => d.decision === "human_review");
  const hd = humans.find((d) => d.rule_id === "R-LOW-CONFIDENCE") ?? humans.find((d) => items.get(d.work_item_id)?.source === "B") ?? humans[0];
  let human: Stories["human"] = null;
  if (hd) {
    const it = items.get(hd.work_item_id)!;
    const place = (it.location.label ?? "").replace(/^Zona /, "").replace(" (sintetic)", "");
    const hhmm = (iso: string) => iso.slice(11, 16);
    human = {
      title: it.source === "B" ? `Send a crew to ${place.split(" (")[0]} before the storm?` : `Check ${it.location.label?.split(",")[0] ?? "this asset"}?`,
      place,
      window: it.time_window ? `${hhmm(it.time_window.start)}–${hhmm(it.time_window.end)}` : null,
      score: it.prediction.score,
      customers: it.impact.customers_affected,
      value: it.impact.expected_value_lei,
      factors: it.explanation.top_factors.map((f) => factorLabel(f.feature, f.value)).filter((x): x is string => !!x).slice(0, 3),
      model: it.prediction.model_version,
      queue: {
        total: humans.length,
        abstain: humans.filter((d) => d.rule_id === "R-ABSTAIN").length,
        cap: humans.filter((d) => d.rule_id === "R-B-REGION-CAP").length,
        low: humans.filter((d) => d.rule_id === "R-LOW-CONFIDENCE").length,
      },
    };
  }

  // explicabilitatea: o vizită la un contor, decisă pe valoare față de cost
  const visits = decisions.filter((d) => d.decision === "assigned" && d.rule_id === "R-A-VISIT");
  const ed = visits.find((d) => d.work_item_id === "A-20250708-MTR-011921") ?? visits[0];
  let explain: Stories["explain"] = null;
  if (ed) {
    const it = items.get(ed.work_item_id)!;
    const route = demo.plan.routes.find((r) => r.stops.some((s) => s.work_item_id === ed.work_item_id));
    const stop = route?.stops.find((s) => s.work_item_id === ed.work_item_id) as ArrivalStop | undefined;
    const [meter, post, place] = (it.location.label ?? "").replace(" (sintetic)", "").split(", ");
    const similar = it.explanation.similar_cases;
    const t = ed.threshold;
    explain = {
      meter: meter?.replace("Contor ", "Meter ") ?? it.work_item_id,
      place: [post, place].filter(Boolean).join(", "),
      label: it.prediction.label,
      score: it.prediction.score,
      low: it.prediction.interval_low,
      high: it.prediction.interval_high,
      model: it.prediction.model_version,
      predictionId: it.prediction.prediction_id,
      factors: it.explanation.top_factors
        .filter((f) => f.contribution > 0)
        .map((f) => ({ label: factorLabel(f.feature, f.value) ?? f.feature, contribution: f.contribution }))
        .slice(0, 5),
      similar: similar.length ? { outcome: similar[0].outcome, n: similar.filter((s) => s.outcome === similar[0].outcome).length } : null,
      value: t.expected_value_lei,
      cost: t.visit_cost_lei,
      actionCost: t.action_cost_lei ?? null,
      travelCost: t.travel_cost_lei ?? null,
      km: t.travel_km_est ?? null,
      crew: ed.crew_id,
      stop: stop?.seq ?? null,
      eta: stop?.eta ? stop.eta.slice(11, 16) : null,
      rule: ed.rule_id,
      auditId: ed.audit_id,
    };
  }
  return { ladder, human, explain };
}
