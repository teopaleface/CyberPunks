/**
 * Datele ecranului „Planul de mâine”, pregătite pe server din PlanView (doar ce trebuie în browser).
 * Fără cod de server: tipurile se folosesc și în componentele client.
 */
import type { Alert, Decision, Notification, PlanSummary, Source, WorkItem } from "@/lib/contracts";
import type { Crew, Depot, PlanView, ResolvedRoute } from "@/lib/data/types";

export interface RegionView {
  id: string;
  label: string;
  counties: string[];
  /** [vest, sud, est, nord] */
  bounds: [number, number, number, number];
  itemCount: number;
  stopCount: number;
}

export interface QuarantineEntry {
  id: string;
  reason: string;
}

export interface PlanScreenData {
  scenario: string;
  planId: string;
  planDate: string;
  shift: { start: string; end: string } | null;
  summary: PlanSummary;
  items: WorkItem[];
  decisions: Record<string, Decision>;
  routes: ResolvedRoute[];
  depots: Depot[];
  crews: Crew[];
  alerts: Alert[];
  notifications: Notification[];
  quarantine: QuarantineEntry[];
  regions: RegionView[];
  /** Regiunea fiecărei lucrări (după județ), pentru hartă. */
  regionOf: Record<string, string | null>;
  defaultRegion: string;
  defaultSelected: string | null;
  /** Lucrări confirmate de om (aprobate) și valoarea lor așteptată: „lei recuperați”, estimat. */
  recovered: { count: number; lei: number };
}

/** Zona Rețele Electrice: Banat (vest) până la Dobrogea (est). */
export const RE_BOUNDS: [number, number, number, number] = [20.2, 43.6, 29.75, 46.65];

const REGION_FALLBACK: Record<string, [number, number, number, number]> = {
  muntenia_sud: [25.7, 43.85, 26.6, 44.75],
  dobrogea: [26.3, 43.7, 29.7, 45.5],
  banat: [20.25, 44.6, 23.3, 46.5],
};

function normCounty(s: string | null | undefined): string {
  return (s ?? "")
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/^municipiul\s+/, "")
    .trim();
}

function boundsOf(points: [number, number][], padKm = 6): [number, number, number, number] | null {
  if (!points.length) return null;
  let w = 180, s = 90, e = -180, n = -90;
  for (const [lon, lat] of points) {
    w = Math.min(w, lon);
    e = Math.max(e, lon);
    s = Math.min(s, lat);
    n = Math.max(n, lat);
  }
  const dLat = padKm / 111;
  const dLon = padKm / (111 * Math.cos(((s + n) / 2) * (Math.PI / 180)));
  return [w - dLon, s - dLat, e + dLon, n + dLat];
}

function invalidReason(raw: Record<string, unknown>, decision: Decision | undefined): string {
  if (decision?.reason_ro) return decision.reason_ro;
  const reasons: string[] = [];
  const loc = raw.location as { lat?: unknown; lon?: unknown } | undefined;
  const lat = typeof loc?.lat === "number" ? loc.lat : null;
  const lon = typeof loc?.lon === "number" ? loc.lon : null;
  if (lat !== null && (lat < 43.5 || lat > 48.5)) reasons.push(`latitudine ${String(lat).replace(".", ",")} (în afara României)`);
  if (lon !== null && (lon < 20 || lon > 30)) reasons.push(`longitudine ${String(lon).replace(".", ",")} (în afara României)`);
  const score = (raw.prediction as { score?: unknown } | undefined)?.score;
  if (typeof score === "number" && (score < 0 || score > 1)) reasons.push(`scor ${String(score).replace(".", ",")} (imposibil)`);
  return reasons.length ? `Intrare greșită: ${reasons.join(" și ")}.` : "Intrare greșită: nu respectă contractul.";
}

/**
 * Lucrarea fără câmpurile grele (factori, cazuri similare, extra, surse): ecranul planului are nevoie de ele
 * doar pentru lucrarea selectată, pe care o încarcă la cerere. Rezumatul și scorul rămân.
 */
export function slimItem(w: WorkItem): WorkItem {
  const extra = (w.extra ?? {}) as Record<string, unknown>;
  const keep: Record<string, unknown> = {};
  for (const k of ["post_id", "estimated_kwh_lost_per_day", "lei_per_month"]) if (k in extra) keep[k] = extra[k];
  return {
    ...w,
    explanation: { top_factors: [], similar_cases: [], summary_ro: w.explanation.summary_ro },
    data_quality: { missing_ratio: w.data_quality.missing_ratio, synthetic: w.data_quality.synthetic, data_sources: [], input_issues: [] },
    extra: { ...keep, _slim: true },
  };
}

export function isSlim(w: WorkItem): boolean {
  return Boolean((w.extra as Record<string, unknown> | undefined)?._slim);
}

export function toPlanScreenData(view: PlanView, fullIds: string[] = []): PlanScreenData {
  const { plan } = view;
  const decisions = view.decisionsByWorkItemId;

  // regiunile din config/area.yaml, cu județele lor
  const regionEntries = Object.entries(view.area.regions ?? {});
  const countyToRegion = new Map<string, string>();
  for (const [id, r] of regionEntries) for (const c of r.counties ?? []) countyToRegion.set(normCounty(c), id);
  const depotRegion = new Map(view.depots.map((d) => [d.depot_id, d.region ?? null]));

  const regionOf: Record<string, string | null> = {};
  for (const w of view.workItems) {
    let r = countyToRegion.get(normCounty(w.location.county)) ?? null;
    if (!r) {
      const crewId = decisions[w.work_item_id]?.crew_id;
      const route = crewId ? view.routes.find((x) => x.crew_id === crewId) : undefined;
      r = route ? (depotRegion.get(route.depot_id) ?? null) : null;
    }
    regionOf[w.work_item_id] = r;
  }

  const stopsByRegion = new Map<string, number>();
  for (const route of view.routes) {
    const r = depotRegion.get(route.depot_id) ?? null;
    if (r) stopsByRegion.set(r, (stopsByRegion.get(r) ?? 0) + route.stops.length);
  }

  const regions: RegionView[] = regionEntries.map(([id, r]) => {
    const items = view.workItems.filter((w) => regionOf[w.work_item_id] === id);
    // încadrarea urmărește unde merg echipele; fără trasee, toate lucrările regiunii
    const routePts: [number, number][] = [];
    for (const route of view.routes) if (depotRegion.get(route.depot_id) === id) routePts.push(...route.path);
    const itemPts: [number, number][] = items.map((w) => [w.location.lon, w.location.lat]);
    const bb = boundsOf(routePts.length >= 2 ? routePts : itemPts, routePts.length >= 2 ? 2.5 : 6) ?? REGION_FALLBACK[id] ?? RE_BOUNDS;
    return {
      id,
      label: r.label_ro,
      counties: r.counties ?? [],
      bounds: bb,
      itemCount: items.length,
      stopCount: stopsByRegion.get(id) ?? 0,
    };
  });

  const defaultRegion =
    regions.toSorted((a, b) => b.stopCount - a.stopCount || b.itemCount - a.itemCount)[0]?.id ?? "toata_zona";

  const ranked = plan.decisions
    .filter((d) => d.decision === "assigned" && d.rank != null)
    .toSorted((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
  const firstInDefault = ranked.find((d) => regionOf[d.work_item_id] === defaultRegion) ?? ranked[0];

  const quarantine: QuarantineEntry[] = view.invalidItems.map((raw) => {
    const id = String(raw.work_item_id ?? "fără ID");
    return { id, reason: invalidReason(raw, decisions[id]) };
  });
  for (const d of plan.decisions) {
    if (d.decision === "rejected_invalid" && !quarantine.some((q) => q.id === d.work_item_id)) {
      quarantine.push({ id: d.work_item_id, reason: d.reason_ro });
    }
  }

  // lei recuperați (estimat): valoarea așteptată a lucrărilor aprobate de om, câte o dată
  const lastHuman = new Map<string, { ts: string; approve: boolean }>();
  for (const a of view.audit ?? []) {
    if (a.actor !== "human" || !a.work_item_id) continue;
    const act = (a.action ?? "").toLowerCase();
    const approve = act.includes("approve") || act === "aprob" || a.rule_id === "R-HUMAN-APPROVE";
    const prev = lastHuman.get(a.work_item_id);
    if (!prev || a.ts >= prev.ts) lastHuman.set(a.work_item_id, { ts: a.ts, approve });
  }
  const approved = new Set([...lastHuman].filter(([, v]) => v.approve).map(([id]) => id));
  const recovered = {
    count: approved.size,
    lei: [...approved].reduce((sum, id) => sum + (view.workItemsById[id]?.impact.expected_value_lei ?? 0), 0),
  };

  return {
    recovered,
    scenario: view.scenario,
    planId: plan.plan_id,
    planDate: plan.plan_date,
    shift: view.shift,
    summary: plan.summary,
    items: view.workItems.map((w) => (fullIds.includes(w.work_item_id) ? w : slimItem(w))),
    decisions,
    routes: view.routes.map((r) => ({
      ...r,
      stops: r.stops.map((s) => ({ ...s, workItem: null, decision: null })),
    })),
    depots: view.depots,
    crews: view.crews,
    alerts: plan.alerts ?? [],
    notifications: plan.notifications ?? [],
    quarantine,
    regions,
    regionOf,
    defaultRegion,
    defaultSelected: firstInDefault?.work_item_id ?? view.workItems[0]?.work_item_id ?? null,
  };
}

/** Eticheta din date, fără marcajul „(sintetic)” (transparența o arată pătratul hașurat). */
function cleanLabel(w: WorkItem): string | null {
  const l = w.location.label?.replace(/\s*\(sintetic\)\s*$/i, "").trim();
  return l || null;
}

export function itemTitle(w: WorkItem): string {
  if (w.asset_type === "meter") return `Contor ${w.asset_id}`;
  if (w.asset_type === "transformer_post") return w.asset_id;
  const l = cleanLabel(w);
  return l ? l.replace(/\s*\([^)]*\)\s*$/, "") : w.asset_id;
}

/** Locul, în cuvinte, cu diacriticele din date: „PT-1208, Chiajna”, „Afumați, Ilfov”, „Ilfov”. */
export function itemPlace(w: WorkItem): string {
  const county = w.location.county ?? "";
  const l = cleanLabel(w);
  if (l) {
    const parts = l.split(",").map((x) => x.trim()).filter(Boolean);
    if (w.asset_type === "meter" && parts.length >= 2) return parts.slice(1).join(", ");
    if (w.asset_type === "transformer_post" && parts.length >= 2) {
      const place = parts.slice(1).join(", ");
      return county && !place.includes(county) ? `${place}, ${county}` : place;
    }
    if (w.asset_type === "zone") return county || l;
  }
  // rezervă: din zone_id (fără diacritice)
  const z = w.location.zone_id;
  const sector = /^B-S(\d)$/.exec(z);
  if (sector) return `București, sectorul ${sector[1]}`;
  const local = z.includes("-") ? z.split("-").slice(1).join(" ") : "";
  const pretty = local ? local.charAt(0) + local.slice(1).toLowerCase() : "";
  if (pretty && county) return `${pretty}, ${county}`;
  return county || pretty || z;
}

export function sourceName(s: Source): string {
  return { A: "Contoare", B: "Furtună", C: "Tensiune" }[s];
}
