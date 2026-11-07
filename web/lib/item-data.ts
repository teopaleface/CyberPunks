/**
 * Piese pure pentru pagina unei lucrări (/lucrari/[id]): locul, fraza despre serie, rândurile din „Scoruri”,
 * ora opririi din traseu, rafala maximă, tensiunea în volți. Doar câmpuri reale; fără cod de server.
 */
import type { ModelReport, Notification, Series, Source, WorkItem } from "@/lib/contracts";
import type { ResolvedRoute } from "@/lib/data/types";
import { clampPercentRo } from "@/lib/data/labels";
import { fmtDayMonth, fmtDec, fmtPercent, fmtTime, isWholeDay, sentence } from "@/lib/format";

export const NOMINAL_V = 230;

/** Tensiunea în volți din valoarea în pu (230 V nominal). */
export const puToVolts = (pu: number) => Math.round(pu * NOMINAL_V);

const cleanLabel = (w: WorkItem) => (w.location.label ?? "").replace(/\s*\(sintetic\)\s*$/i, "").trim();

/** Localitatea, pe scurt: „Chiajna” (contor), „Afumați” (post), „Timișoara” (zonă). */
export function localityOf(w: WorkItem): string {
  const parts = cleanLabel(w).split(",").map((x) => x.trim()).filter(Boolean);
  if (w.asset_type === "meter") return parts.at(-1) ?? w.location.zone_id;
  if (w.asset_type === "transformer_post") return parts[1] ?? w.location.county ?? w.location.zone_id;
  return (parts[0] ?? w.asset_id).replace(/^Zona\s+/i, "").replace(/\s*\([^)]*\)\s*$/, "");
}

/** Postul unui contor (din `extra.post_id`, altfel din etichetă). */
export function postOf(w: WorkItem): string | null {
  const id = (w.extra as Record<string, unknown> | undefined)?.post_id;
  if (typeof id === "string") return id;
  return cleanLabel(w).split(",").map((x) => x.trim()).find((x) => /^PT-\d+/.test(x)) ?? null;
}

/** Zona unei lucrări B, fără județ: „Zona Timișoara”. */
export function zoneName(w: WorkItem): string {
  return cleanLabel(w).replace(/\s*\([^)]*\)\s*$/, "") || w.asset_id;
}

/** Scorul ca procent întreg; 100% devine „peste 99%”. */
export function pctText(ratio: number): string {
  return ratio >= 0.995 ? "above 99%" : `${Math.round(ratio * 100)}%`;
}

/** Intervalul scorului în cuvinte: „98–100%”, sau „peste 98%” când ajunge la capăt. */
export function intervalText(low?: number | null, high?: number | null): string | null {
  if (low == null || high == null) return null;
  const lo = Math.round(low * 100);
  if (high >= 0.995) return `above ${lo}%`;
  return `${lo}–${Math.round(high * 100)}%`;
}

const FLAG_RO: Record<string, string> = {
  negativ: "negative readings",
  zero: "zero consumption",
  gol: "days without data",
  salt: "consumption jumps",
  peste_limita: "above the limit",
};

/** O frază despre serie, din adnotările și semnele ei reale. */
export function seriesSentence(series: Series | null): { headline: string; detail: string | null } {
  if (!series) return { headline: "Series unavailable.", detail: null };
  const a = series.annotations?.[0];
  const counts = new Map<string, number>();
  for (const p of series.points) if (p.flag) counts.set(p.flag, (counts.get(p.flag) ?? 0) + 1);
  const top = [...counts.entries()].sort((x, y) => y[1] - x[1])[0];
  const when = a ? (isWholeDay(String(a.t)) ? `from ${fmtDayMonth(String(a.t))}` : `at ${fmtTime(String(a.t))}`) : null;
  const headline = a ? `${sentence(clampPercentRo(a.label_ro)).replace(/\.$/, "")}${when ? ` ${when}` : ""}.` : top ? `Signals in the series: ${FLAG_RO[top[0]] ?? top[0]}.` : "No unusual consumption signals.";
  const detail = top ? `${top[1]} of ${series.points.length} days with ${FLAG_RO[top[0]] ?? top[0]}.` : null;
  return { headline, detail };
}

/** Rafala maximă din seria B (km/h) și momentul ei. */
export function maxGust(series: Series | null): { value: number; t: string } | null {
  let best: { value: number; t: string } | null = null;
  for (const p of series?.points ?? []) {
    if (typeof p.value === "number" && (!best || p.value > best.value)) best = { value: p.value, t: String(p.t) };
  }
  return best;
}

/** Durata ferestrei în ore întregi („6 ore”), din început și sfârșit. */
export function windowHours(start: string, end: string): number {
  return Math.round((new Date(end).getTime() - new Date(start).getTime()) / 3_600_000);
}

export interface StopInfo {
  crew_id: string;
  seq: number;
  eta: string;
  travel_km: number;
  duration_min: number;
}

/** Oprirea lucrării în traseele planului. */
export function stopFor(routes: Pick<ResolvedRoute, "crew_id" | "stops">[] | undefined, id: string): StopInfo | null {
  for (const r of routes ?? []) {
    const s = r.stops.find((x) => x.work_item_id === id);
    if (s) return { crew_id: r.crew_id, seq: s.seq, eta: s.eta, travel_km: s.travel_km, duration_min: s.duration_min };
  }
  return null;
}

export interface MetricRow {
  key: string;
  label: string;
  model: string;
  base: string | null;
}

type Fmt = (v: number) => string;
const pct: Fmt = (v) => (v >= 0.995 ? "above 99%" : fmtPercent(v, 1));
const dec3: Fmt = (v) => fmtDec(v, 3);
const pu: Fmt = (v) => `${fmtDec(v, 4)} pu`;

const METRIC_ROWS: Record<Source, { key: string; label: string; fmt: Fmt }[]> = {
  A: [
    { key: "subtle_precision_at_k", label: "Precision on subtle test anomalies", fmt: pct },
    { key: "sgcc_precision_at_k", label: "Precision on SGCC real theft labels", fmt: pct },
    { key: "recall_at_k", label: "Recall at selection", fmt: pct },
    { key: "pr_auc", label: "PR-AUC", fmt: dec3 },
  ],
  B: [
    { key: "pr_auc", label: "PR-AUC (storm)", fmt: dec3 },
    { key: "recall_at_thr", label: "Recall at threshold", fmt: pct },
    { key: "roc_auc", label: "ROC-AUC", fmt: dec3 },
  ],
  C: [
    { key: "mae_vmax_pu", label: "Voltage error", fmt: pu },
    { key: "pr_auc_exceed", label: "PR-AUC for exceedances", fmt: dec3 },
    { key: "recall_exceed", label: "Exceedance recall", fmt: pct },
  ],
};

/** Rândurile din „Scoruri”: modelul față de baza lui, doar metricile care există în raport. */
export function metricRows(source: Source, report: ModelReport | null): MetricRow[] {
  if (!report) return [];
  return METRIC_ROWS[source].flatMap((m) => {
    const v = report.metrics[m.key];
    if (typeof v !== "number") return [];
    const b = report.baseline_metrics[m.key];
    return [{ key: m.key, label: m.label, model: m.fmt(v), base: typeof b === "number" ? m.fmt(b) : null }];
  });
}

/** Mesajul pentru clienți: din `extra.customer_message_ro`, apoi din notificările planului, apoi din treapta „mesaje”. */
export function customerMessage(w: WorkItem, notifications: Notification[] | undefined): string | null {
  const extra = (w.extra ?? {}) as Record<string, unknown>;
  if (typeof extra.customer_message_ro === "string" && extra.customer_message_ro.trim()) return extra.customer_message_ro;
  const mine = (notifications ?? []).filter((n) => n.work_item_id === w.work_item_id);
  const pick = mine.find((n) => n.audience !== "echipa") ?? mine[0];
  if (pick) return pick.message_ro;
  const opts = Array.isArray(extra.remedy_options) ? (extra.remedy_options as Record<string, unknown>[]) : [];
  const prev = opts.find((o) => typeof o.message_preview_ro === "string")?.message_preview_ro;
  return typeof prev === "string" ? prev : null;
}

/** Contribuțiile la tensiune (pu), din `extra.voltage_contributions_pu`, de la mare la mic după valoarea absolută. */
export function voltageContributions(w: WorkItem): { key: string; pu: number }[] {
  const raw = (w.extra as Record<string, unknown> | undefined)?.voltage_contributions_pu;
  if (typeof raw !== "object" || raw === null || Array.isArray(raw)) return [];
  return Object.entries(raw as Record<string, unknown>)
    .filter((e): e is [string, number] => typeof e[1] === "number" && Number.isFinite(e[1]))
    .map(([key, v]) => ({ key, pu: v }))
    .sort((a, b) => Math.abs(b.pu) - Math.abs(a.pu));
}

export const CONTRIBUTION_RO: Record<string, string> = {
  fizica: "Grid physics (solar panels, load)",
  panouri: "Solar panels",
  soare: "Sunlight",
  temperatura: "Temperature",
  pornire: "Starting voltage",
  retea: "Grid (length, resistance)",
  consum: "Consumption",
  baterii: "Batteries",
  perioada: "Time of year",
};

/** Costul cu care se compară valoarea așteptată, din pragurile deciziei. */
export function ruleCost(t: Record<string, number> | undefined): number | null {
  if (!t) return null;
  for (const k of ["visit_cost_lei", "preposition_cost_lei", "remedy_cost_lei", "tap_cost_lei", "cost_lei", "action_cost_lei"]) {
    if (typeof t[k] === "number") return t[k];
  }
  return null;
}

export type Tag = "predictii" | "recomandari" | "rute" | "urme" | "reguli" | "scoruri" | "harti" | "tensiune";

export const TAG_CHIPS: { id: Tag; label: string; tone: "blue" | "violet" | "amber" | "orange" }[] = [
  { id: "predictii", label: "Predictions", tone: "blue" },
  { id: "recomandari", label: "Recommendations", tone: "violet" },
  { id: "rute", label: "Routes", tone: "blue" },
  { id: "urme", label: "Decision trace", tone: "amber" },
  { id: "reguli", label: "Rules", tone: "orange" },
  { id: "scoruri", label: "Scores", tone: "blue" },
  { id: "harti", label: "Maps", tone: "violet" },
  { id: "tensiune", label: "Voltage", tone: "amber" },
];

/** Filtrul din adresă (?vedere=), doar dacă e o etichetă cunoscută. */
export function parseTag(v: string | string[] | undefined): Tag | null {
  const s = Array.isArray(v) ? v[0] : v;
  return TAG_CHIPS.some((c) => c.id === s) ? (s as Tag) : null;
}
