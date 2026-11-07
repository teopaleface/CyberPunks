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
  location: { lat: number; lon: number; county?: string };
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

function rank(s: ItemState): number {
  return { deferred: 0, notify: 1, remote: 2, human: 3, route: 4 }[s];
}
