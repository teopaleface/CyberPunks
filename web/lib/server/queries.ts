import "server-only";
import { cookies } from "next/headers";
import { cache } from "react";
import { DEFAULT_SCENARIO, getPlanView, getScenarios } from "@/lib/data";
import type { DataSource, PlanView, Sourced } from "@/lib/data/types";

/**
 * Citirile folosite de mai multe componente din aceeași cerere, deduplicate cu React.cache
 * (antetul și ecranul cer același plan o singură dată).
 */
export const loadPlanView = cache((scenario: string) => getPlanView(scenario));
export const loadScenarios = cache(() => getScenarios());

const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;
export const SCENARIO_COOKIE = "scenariu";

/** Scenariul cerut: din adresă (?scenariu=), apoi din cookie (ultima alegere), apoi cel implicit. */
export async function resolveScenario(searchParams: Promise<Record<string, string | string[] | undefined>>): Promise<string> {
  const params = await searchParams;
  const fromQuery = typeof params.scenariu === "string" ? params.scenariu : undefined;
  if (fromQuery && SCENARIO_RE.test(fromQuery)) return fromQuery;
  const jar = await cookies();
  const fromCookie = jar.get(SCENARIO_COOKIE)?.value;
  if (fromCookie && SCENARIO_RE.test(fromCookie)) return fromCookie;
  return DEFAULT_SCENARIO;
}

/** Nume scurte pentru scenariile cunoscute; restul păstrează eticheta din config. */
const SHORT_LABEL: Record<string, string> = {
  "demo-vara": "Zi de vară cu furtuni",
  maine: "Mâine, cu prognoza reală",
};

export interface ShellInfo {
  scenario: string;
  scenarios: { id: string; label: string; detail: string }[];
  planDate: string | null;
  shift: { start: string; end: string } | null;
  generatedAt: string | null;
  planId: string | null;
  counts: { review: number; alerts: number; notifications: number };
  /** Ce se poate căuta din bara de sus: lucrări, posturi, echipe (ID, eticheta, adresa). */
  search: { id: string; label: string; href: string; kind: "lucrare" | "post" | "echipă" }[];
  provenance: {
    source: DataSource;
    degradedReason?: string;
    detail?: string;
    /** Câte lucrări sunt pe active sau date sintetice. */
    syntheticItems: number;
    totalItems: number;
  };
}

function searchIndex(view: PlanView | null, scenario: string): ShellInfo["search"] {
  if (!view) return [];
  const q = `?scenariu=${encodeURIComponent(scenario)}`;
  const out: ShellInfo["search"] = [];
  const posts = new Set<string>();
  for (const w of view.workItems) {
    const label = (w.location.label ?? w.asset_id).replace(/\s*\(sintetic\)\s*$/, "");
    out.push({ id: w.work_item_id, label, href: `/lucrari/${encodeURIComponent(w.work_item_id)}${q}`, kind: "lucrare" });
    const post = w.asset_type === "transformer_post" ? w.asset_id : (w.extra as Record<string, unknown> | undefined)?.post_id;
    if (typeof post === "string" && !posts.has(post)) {
      posts.add(post);
      out.push({ id: post, label: `Postul ${post}`, href: `/posturi/${encodeURIComponent(post)}${q}`, kind: "post" });
    }
  }
  for (const r of view.routes) {
    out.push({ id: r.crew_id, label: `Echipa ${r.crew_id}, ${r.stops.length} opriri`, href: `/lucrari?echipa=${encodeURIComponent(r.crew_id)}&scenariu=${encodeURIComponent(scenario)}`, kind: "echipă" });
  }
  return out;
}

export async function loadShellInfo(scenario: string): Promise<{ info: ShellInfo; view: Sourced<PlanView | null> }> {
  const [viewResult, scenariosResult] = await Promise.all([loadPlanView(scenario), loadScenarios()]);
  const view = viewResult.data;
  const list = scenariosResult.data.length ? scenariosResult.data : [{ id: scenario, label_ro: scenario }];
  const scenarios = list.map((s) => ({ id: s.id, label: SHORT_LABEL[s.id] ?? s.label_ro, detail: s.label_ro }));
  if (!scenarios.some((s) => s.id === scenario)) scenarios.unshift({ id: scenario, label: SHORT_LABEL[scenario] ?? scenario, detail: scenario });
  const decisions = view?.plan.decisions ?? [];
  const info: ShellInfo = {
    scenario,
    scenarios,
    planDate: view?.plan.plan_date ?? null,
    shift: view?.shift ?? null,
    generatedAt: view?.plan.generated_at ?? null,
    planId: view?.plan.plan_id ?? null,
    counts: {
      review: decisions.filter((d) => d.decision === "human_review").length,
      alerts: view?.plan.alerts?.length ?? 0,
      notifications: view?.plan.notifications?.length ?? 0,
    },
    search: searchIndex(view, scenario),
    provenance: {
      source: viewResult.source,
      degradedReason: viewResult.degradedReason,
      detail: viewResult.detail,
      syntheticItems: view?.workItems.filter((w) => w.data_quality.synthetic).length ?? 0,
      totalItems: view?.workItems.length ?? 0,
    },
  };
  return { info, view: viewResult };
}
