/** Numerele ecranului „Rulare agent”: ce intră și ce iese din fiecare pas, pe surse. Fără cod de server. */
import type { Source } from "@/lib/contracts";
import { sourceOf } from "@/lib/sources";

export type BySource = Record<Source, number>;

export interface StageCounts {
  perceive: BySource;
  estimate: BySource;
  decide: BySource;
  act: BySource;
}

const zero = (): BySource => ({ A: 0, B: 0, C: 0 });
export const totalOf = (b: BySource) => b.A + b.B + b.C;

function add(b: BySource, id: string, src?: Source | null) {
  const s = src ?? sourceOf(id);
  if (s) b[s] += 1;
}

/**
 * Percepe: tot ce a primit agentul (valid sau nu). Estimează: lucrările valide, cu predicție.
 * Decide: lucrările cu o decizie (fără cele respinse la intrare). Acționează: trasee, citiri la distanță și mesaje.
 */
export function stageCounts(input: {
  items: { work_item_id: string; source?: Source | null }[];
  invalidIds: string[];
  decisions: { work_item_id: string; decision: string }[];
}): StageCounts {
  const out: StageCounts = { perceive: zero(), estimate: zero(), decide: zero(), act: zero() };
  const rejected = new Set(input.decisions.filter((d) => d.decision === "rejected_invalid").map((d) => d.work_item_id));
  const seen = new Set<string>();
  for (const w of input.items) {
    if (!seen.has(w.work_item_id)) {
      seen.add(w.work_item_id);
      add(out.perceive, w.work_item_id, w.source);
    }
    if (!rejected.has(w.work_item_id)) add(out.estimate, w.work_item_id, w.source);
  }
  for (const id of [...input.invalidIds, ...rejected]) {
    if (!seen.has(id)) {
      seen.add(id);
      add(out.perceive, id);
    }
  }
  for (const d of input.decisions) {
    if (d.decision === "rejected_invalid") continue;
    add(out.decide, d.work_item_id);
    if (d.decision === "assigned" || d.decision === "remote_action" || d.decision === "notify") add(out.act, d.work_item_id);
  }
  return out;
}

/** O metrică cu 3 cifre semnificative; 1,00 devine „peste 0,99”. */
export function fmtMetric(v: number, key: string): string {
  const ratio = !/mae|rmse|brier|ece|loss/.test(key);
  if (ratio && v >= 0.995 && v <= 1.005) return "peste 0,99";
  return v.toLocaleString("ro-RO", { minimumSignificantDigits: 3, maximumSignificantDigits: 3 });
}
