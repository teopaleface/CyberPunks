/**
 * Din liniile de audit (AuditRecord) în rânduri de tabel, cu textele deja în română.
 * Se cheamă pe server; tabelul doar filtrează și afișează.
 */
import type { AuditRecord, DecisionType, WorkItem } from "@/lib/contracts";
import { DECISION_LABEL_RO, ruleRo, thresholdLabelRo, thresholdValueRo } from "@/lib/data/labels";
import { fmtMoment, fmtScore, fmtTime, plural } from "@/lib/format";
import { markerKind, type MarkerKind } from "@/lib/marker-svg";
import { itemPlace, itemTitle } from "@/lib/plan-screen";
import { sourceOf } from "@/lib/sources";
import type { ActionOption, JournalKind, JournalRow, JournalThreshold } from "./types";

const RUN_ACTIONS = new Set(["run", "replan"]);

/** Ce a făcut omul (POST /review): `review_approve`, `review_reject`, `review_defer`. */
const REVIEW_LABEL: Record<string, string> = {
  review_approve: "aprobată de om",
  review_reject: "respinsă de om",
  review_defer: "amânată de om",
};

const RUN_LABEL: Record<string, string> = {
  run: "rulare a agentului",
  replan: "plan refăcut după decizia omului",
};

/** Ordinea din filtre și din rezumat: întâi ce face agentul, apoi omul, apoi rulările. */
export const ACTION_ORDER = [
  "assigned",
  "remote_action",
  "notify",
  "deferred",
  "human_review",
  "rejected_invalid",
  "review_approve",
  "review_reject",
  "review_defer",
  "run",
  "replan",
];

/** Explicația scurtă a fiecărui tip de decizie, pentru rezumat. */
export const DECISION_HINT_RO: Record<DecisionType, string> = {
  assigned: "cu echipă",
  remote_action: "fără deplasare",
  notify: "fără echipă",
  deferred: "nu merită acum",
  human_review: "agentul nu e sigur",
  rejected_invalid: "date greșite",
};

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Ce e și unde, fără să repete ID-ul și cu diacriticele din eticheta locului:
 * „Contor la PT 9979, Tineretului”, „Zona Timișoara (Timiș)”, „Post de transformare, Afumați (sintetic)”.
 */
export function shortTitle(w: WorkItem): string {
  const label = w.location.label?.trim() ?? "";
  const rest = label.replace(new RegExp(`^(Contor\\s+)?${escapeRe(w.asset_id)},?\\s*`), "").trim();
  if (w.asset_type === "meter") return rest ? `Contor la ${rest}` : `Contor, ${itemPlace(w)}`;
  if (w.asset_type === "transformer_post") return `Post de transformare, ${rest || itemPlace(w)}`;
  return label || itemTitle(w);
}

/** Praguri pe care etichetele comune nu le au încă. */
const EXTRA_THRESHOLD_RO: Record<string, string> = {
  abstain: "modelul nu e sigur",
  human: "decis de om",
  medium_confidence_margin_lei: "marja cerută la încredere medie",
  visit_min_score: "scor minim pentru vizită",
  smart_meter: "contor citit la distanță",
  planned_notice_working_days: "preaviz pentru clienți",
};

/** Praguri care sunt de fapt „da/nu”. */
const YES_NO = new Set(["abstain", "human", "smart_meter"]);

function cap(s: string): string {
  return s ? s.charAt(0).toLocaleUpperCase("ro-RO") + s.slice(1) : s;
}

export function actionLabel(action: string): string {
  const label =
    (DECISION_LABEL_RO as Record<string, string>)[action] ??
    REVIEW_LABEL[action] ??
    RUN_LABEL[action] ??
    action.replaceAll("_", " ");
  return cap(label);
}

function thresholdValue(key: string, v: number): string {
  if (YES_NO.has(key)) return v ? "da" : "nu";
  if (key === "planned_notice_working_days") return plural(Math.round(v), "zi lucrătoare", "zile lucrătoare");
  // `score_min` se termină în `_min`, dar e un scor, nu minute
  if (key === "score_min") return fmtScore(v);
  return thresholdValueRo(key, v);
}

function thresholds(t: AuditRecord["threshold"]): JournalThreshold[] {
  return Object.entries(t ?? {})
    .filter(([, v]) => typeof v === "number" && Number.isFinite(v))
    .map(([key, v]) => ({ key, label: EXTRA_THRESHOLD_RO[key] ?? thresholdLabelRo(key), value: thresholdValue(key, v) }));
}

function kindOf(r: AuditRecord): JournalKind {
  if (RUN_ACTIONS.has(r.action)) return "run";
  return r.actor === "human" ? "review" : "decision";
}

function markerOf(r: AuditRecord): MarkerKind {
  if (r.action === "review_approve") return "assigned";
  if (r.action.startsWith("review_")) return "pending";
  return markerKind(r.action as DecisionType);
}

/** Nota omului vine ca „Ana: am sunat clientul” sau doar „Ana”. */
function splitReviewer(note: string | null | undefined): { reviewer: string | null; note: string | null } {
  if (!note) return { reviewer: null, note: null };
  const i = note.indexOf(": ");
  if (i < 0) return { reviewer: cap(note.trim()) || null, note: null };
  return { reviewer: cap(note.slice(0, i).trim()) || null, note: note.slice(i + 2).trim() || null };
}

function time(ts: string): number {
  const t = Date.parse(ts);
  return Number.isNaN(t) ? 0 : t;
}

function safe(fn: () => string, fallback: string): string {
  try {
    return fn();
  } catch {
    return fallback;
  }
}

/**
 * Cele mai noi primele. Deciziile unei rulări au aceeași oră ca rularea, așa că rularea vine prima
 * și deciziile ei rămân în ordinea în care le-a scris agentul: rularea arată ca un titlu de grup.
 */
export function buildRows(records: AuditRecord[], workItemsById: Record<string, WorkItem>): JournalRow[] {
  const batch = new Map<string, number>();
  for (const r of records) {
    if (!RUN_ACTIONS.has(r.action) && r.actor === "agent") batch.set(r.ts, (batch.get(r.ts) ?? 0) + 1);
  }
  const sorted = records
    .map((r, i) => ({ r, i }))
    .sort((a, b) => {
      const dt = time(b.r.ts) - time(a.r.ts);
      if (dt !== 0) return dt;
      const ra = RUN_ACTIONS.has(a.r.action) ? 0 : 1;
      const rb = RUN_ACTIONS.has(b.r.action) ? 0 : 1;
      return ra - rb || a.i - b.i;
    });

  return sorted.map(({ r }) => {
    const kind = kindOf(r);
    const id = r.work_item_id ?? null;
    const w = id ? workItemsById[id] : undefined;
    const human = kind === "review" ? splitReviewer(r.note) : { reviewer: null, note: r.note ?? null };
    return {
      id: r.audit_id,
      ts: r.ts,
      time: safe(() => fmtTime(r.ts), r.ts),
      moment: safe(() => fmtMoment(r.ts), r.ts),
      actor: r.actor,
      kind,
      action: r.action,
      actionLabel: actionLabel(r.action),
      attention: r.action === "human_review",
      workItemId: id,
      source: id ? sourceOf(id) : null,
      marker: markerOf(r),
      itemTitle: w ? shortTitle(w) : null,
      ruleId: r.rule_id ?? null,
      ruleText: ruleRo(r.rule_id),
      thresholds: thresholds(r.threshold),
      predictionId: r.prediction_id ?? null,
      modelVersion: r.model_version ?? null,
      inputsSha: r.inputs_sha256 ?? null,
      note: human.note,
      reviewer: human.reviewer,
      decisions: kind === "run" ? (batch.get(r.ts) ?? 0) : 0,
    };
  });
}

/** Tipurile prezente în jurnal, în ordinea fixă, cu câte rânduri are fiecare. */
export function actionOptions(rows: JournalRow[]): ActionOption[] {
  const counts = new Map<string, { label: string; count: number }>();
  for (const r of rows) {
    const c = counts.get(r.action);
    if (c) c.count += 1;
    else counts.set(r.action, { label: r.actionLabel, count: 1 });
  }
  const rank = (a: string) => {
    const i = ACTION_ORDER.indexOf(a);
    return i < 0 ? ACTION_ORDER.length : i;
  };
  return [...counts.entries()]
    .sort(([a], [b]) => rank(a) - rank(b) || a.localeCompare(b))
    .map(([action, c]) => ({ action, label: c.label, count: c.count }));
}
