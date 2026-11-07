/**
 * Modelul ecranului „Nu sunt sigur”: categoriile de motive, întrebarea cazului, cele două fapte
 * din dreptul scorului, paginarea. Fără cod de server (se testează direct).
 */
import type { WorkItem } from "@/lib/contracts";
import { ruleRo } from "@/lib/data/labels";
import { fmtDec, fmtInt, fmtTime, sentence } from "@/lib/format";

export type CategoryTone = "blue" | "violet" | "amber" | "orange" | "grey";

export interface Category {
  id: string;
  label: string;
  tone: CategoryTone;
}

/** Regulile care trimit la om, grupate în câteva categorii ușor de citit. */
export function categoryOf(ruleId: string): Category {
  if (ruleId === "R-ABSTAIN" || ruleId === "R-ABSTAIN-DATA") return { id: "abtineri", label: "Uncertain cause", tone: "blue" };
  if (ruleId === "R-LOW-CONFIDENCE" || ruleId === "R-WIDE-INTERVAL") return { id: "incredere", label: "Low confidence", tone: "amber" };
  if (ruleId.startsWith("R-SAFETY")) return { id: "siguranta", label: "Safety risk", tone: "orange" };
  const text = ruleRo(ruleId);
  return { id: ruleId.toLowerCase(), label: text ? sentence(text).replace(/[.]$/, "").split(":")[0] : ruleId, tone: "violet" };
}

export interface Fact {
  icon: "rain" | "wind" | "data" | "kwh" | "volt" | "limit";
  value: string;
  label: string;
}

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function factorValue(w: WorkItem, re: RegExp): number | null {
  return num(w.explanation.top_factors.find((f) => re.test(f.feature))?.value);
}

/** Cele două cifre din dreptul scorului, doar cele care există în date. */
export function caseFacts(w: WorkItem, limitPu?: number | null): Fact[] {
  const extra = (w.extra ?? {}) as Record<string, unknown>;
  const out: Fact[] = [];
  if (w.source === "B") {
    const rain = num(extra.precip_48h_mm) ?? factorValue(w, /precip_48/);
    const gust = num(extra.gust_max_kmh) ?? factorValue(w, /gust/);
    if (rain != null) out.push({ icon: "rain", value: `${fmtDec(rain, rain < 10 ? 1 : 0)} mm`, label: "rain over 48 h" });
    if (gust != null) out.push({ icon: "wind", value: `${fmtInt(gust)} km/h`, label: "gusts" });
  } else if (w.source === "C") {
    const p90 = w.prediction.point_interval?.[1] ?? null;
    if (p90 != null) out.push({ icon: "volt", value: `${fmtDec(p90, 3)} pu`, label: "maximum P90 voltage" });
    if (limitPu != null) out.push({ icon: "limit", value: `${fmtDec(limitPu, 2)} pu`, label: "voltage limit" });
  } else {
    const miss = w.data_quality.missing_ratio;
    if (Number.isFinite(miss)) out.push({ icon: "data", value: `${fmtDec(miss * 100, 0)}%`, label: "missing data" });
    const kwh = num(extra.estimated_kwh_lost_per_day);
    if (kwh != null) out.push({ icon: "kwh", value: `${fmtDec(kwh, 1)} kWh/day`, label: "estimated loss" });
  }
  return out;
}

/** Întrebarea cazului: o propoziție simplă, cu ID-ul separat (ca să poată fi marcat translate="no"). */
export function questionFor(w: WorkItem, place: string): { before: string; id: string | null; after: string } {
  if (w.source === "B") return { before: `Send a crew to the ${place} before the storm?`, id: null, after: "" };
  if (w.source === "C") return { before: "Apply the remedy at substation ", id: w.asset_id, after: "?" };
  if (w.asset_type === "transformer_post") return { before: "Inspect substation ", id: w.asset_id, after: "?" };
  return { before: "Send a crew to meter ", id: w.asset_id, after: "?" };
}

/** Intervalul orar al lucrării („15:00 – 21:00”) sau, fără fereastră, urgența. */
export function whenText(w: WorkItem): string {
  if (w.time_window) return `${fmtTime(w.time_window.start)} – ${fmtTime(w.time_window.end)}`;
  return `in ${fmtInt(w.impact.urgency_hours)} h`;
}

/** Numerele paginilor de arătat, cu „…” între salturi. */
export function pageList(total: number, current: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const set = new Set([1, total, current, current - 1, current + 1]);
  const nums = [...set].filter((n) => n >= 1 && n <= total).sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  nums.forEach((n, i) => {
    if (i && n - nums[i - 1] > 1) out.push("…");
    out.push(n);
  });
  return out;
}
