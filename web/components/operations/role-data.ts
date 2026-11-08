import { rows, text, type Context, type Row } from "@/lib/operations/types";
import type { MapItem, Bounds } from "@/components/plan/plan-map";
import { dashboardTitle } from "@/components/workspace/role-dashboard-model";

export const record = (value: unknown): Row => value && typeof value === "object" && !Array.isArray(value) ? value as Row : {};
export function scopedItem(context: Context, kind: "case" | "work", id?: string): Row | undefined {
  if (!id) return undefined;
  return (kind === "case" ? context.cases : context.work_items).find((item) => item[kind === "case" ? "case_id" : "work_item_id"] === id);
}
export function ownRoute(context: Context): Row | undefined {
  return rows(context.routes ?? context.plan.routes).find((route) => route.crew_id === context.actor.crew_id);
}
export function routeMap(context: Context): { items: MapItem[]; bounds: Bounds } {
  const allowed = new Map(context.work_items.map((item) => [text(item.work_item_id), item]));
  const stops = rows(ownRoute(context)?.stops);
  const items: MapItem[] = stops.flatMap((stop) => {
    const work = allowed.get(text(stop.work_item_id));
    if (!work || !["A", "B", "C"].includes(text(work.source))) return [];
    const location = record(work.location);
    if (typeof location.lat !== "number" || !Number.isFinite(location.lat) || Math.abs(location.lat) > 90 ||
        typeof location.lon !== "number" || !Number.isFinite(location.lon) || Math.abs(location.lon) > 180) return [];
    return [{ id: text(work.work_item_id), source: work.source as "A" | "B" | "C", lat: location.lat, lon: location.lon, kind: "assigned" as const,
      title: dashboardTitle(work), sub: text(location.label), prominent: true, pinned: true }];
  });
  const lon = items.map((item) => item.lon), lat = items.map((item) => item.lat);
  return { items, bounds: items.length ? [Math.min(...lon) - .025, Math.min(...lat) - .025, Math.max(...lon) + .025, Math.max(...lat) + .025] : [20, 43, 30, 49] };
}
export const EVENT_NAMES: Record<string, string> = {
  create_case: "Report received", set_availability: "Access availability shared", request_human: "Human help requested",
  record_verdict: "Field finding recorded", approve_plan: "Crew assignments approved", review_work_item: "Work reviewed",
};
export function recentEvents(context: Context): Row[] {
  return [...rows(context.events)].sort((a, b) => (Date.parse(text(b.created_at ?? b.ts)) || 0) - (Date.parse(text(a.created_at ?? a.ts)) || 0));
}
