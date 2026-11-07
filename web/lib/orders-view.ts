/**
 * Ordinul de lucru al unei echipe, pregătit din traseul real: opriri, ore, lucrarea vizată, verificări.
 * Fără cod de server (se folosește și în componentele client).
 */
import type { Decision, Source, WorkItem } from "@/lib/contracts";
import type { Depot, ResolvedRoute } from "@/lib/data/types";
import { predictionLabelRo } from "@/lib/data/labels";
import { fmtTime } from "@/lib/format";

export interface OrderStop {
  workItemId: string;
  assetId: string;
  source: Source | null;
  eta: string;
  etaEnd: string;
  title: string;
  place: string;
  action: string;
  predictionLabel: string | null;
  score: number | null;
  ruleId: string | null;
  costLei: number | null;
}

export interface OrderView {
  crewId: string;
  depot: Depot | null;
  departAt: string | null;
  returnAt: string | null;
  returnEstimated: boolean;
  totalKm: number;
  stops: OrderStop[];
}

/** Costul vizitei din pragurile deciziei (primul câmp de cost care există). */
export function decisionCost(d: Decision | null | undefined): number | null {
  const t = d?.threshold;
  if (!t) return null;
  for (const k of ["cost_lei", "visit_cost_lei", "action_cost_lei"]) if (typeof t[k] === "number") return t[k];
  return null;
}

export function pickCrew(routes: { crew_id: string }[], requested: string | undefined): string | null {
  if (requested && routes.some((r) => r.crew_id === requested)) return requested;
  return routes[0]?.crew_id ?? null;
}

export function buildOrder(
  route: ResolvedRoute,
  items: Record<string, WorkItem>,
  decisions: Record<string, Decision>,
  placeOf: (w: WorkItem) => string,
  titleOf: (w: WorkItem) => string,
): OrderView {
  const stops: OrderStop[] = route.stops.map((s) => {
    const w = items[s.work_item_id] ?? s.workItem ?? null;
    const d = decisions[s.work_item_id] ?? s.decision ?? null;
    const end = new Date(Date.parse(s.eta) + s.duration_min * 60_000).toISOString();
    return {
      workItemId: s.work_item_id,
      assetId: w?.asset_id ?? s.work_item_id,
      source: w?.source ?? null,
      eta: s.eta,
      etaEnd: end,
      title: w ? titleOf(w) : s.work_item_id,
      place: w ? placeOf(w) : (s.label ?? ""),
      action: w?.recommended_action ?? "",
      predictionLabel: w ? predictionLabelRo(w.prediction.label) : null,
      score: w ? w.prediction.score : null,
      ruleId: d?.rule_id ?? null,
      costLei: decisionCost(d),
    };
  });
  const last = stops.at(-1);
  const returnAt = route.return_at ?? last?.etaEnd ?? null;
  return {
    crewId: route.crew_id,
    depot: route.depot,
    departAt: route.depart_at ?? stops[0]?.eta ?? null,
    returnAt,
    returnEstimated: !route.return_at,
    totalKm: route.total_km,
    stops,
  };
}

export interface CheckItem {
  id: string;
  text: string;
}

/** Verificările de bifat, din opririle reale. */
export function buildChecklist(order: OrderView): CheckItem[] {
  const out: CheckItem[] = [];
  for (const s of order.stops) {
    out.push({ id: `sosire-${s.workItemId}`, text: `Confirm arrival at ${s.assetId}` });
    if (s.predictionLabel) out.push({ id: `verif-${s.workItemId}`, text: `Inspect ${s.predictionLabel} at ${s.assetId}` });
  }
  out.push({ id: "jurnal", text: "Update the intervention log" });
  out.push({ id: "intoarcere", text: `Return to depot${order.returnAt ? ` (${fmtTime(order.returnAt)})` : ""}` });
  return out;
}
