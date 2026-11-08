/**
 * Everything the site shows comes from the agent's real run, copied from the
 * team repo (teopaleface/CyberPunks, branch design, outputs/demo) by
 * scripts/extract-daybreak.py. Assets (meters, posts, crews, depots) are
 * synthetic, placed on the real map; weather and days are real.
 */
import raw from "./daybreak.json"
import { EVALUATION_NAMES_EN } from "./daybreak-copy"
import { englishText } from "../../../lib/english"

export type SourceKey = "A" | "B" | "C"
export type Decision = "assigned" | "remote_action" | "human_review" | "deferred" | "notify"

export interface PostRow {
  id: string
  label: string
  lat: number
  lng: number
  zone: string
  lossLeiMonth: number | null
  diagnosis: string | null
  color: "verde" | "galben" | "rosu"
  score: number | null
  decision: Decision | null
  metersFlagged: number
  voltageP90: number | null
  kva: number
  workItem: string | null
}

export interface Case {
  id: string
  post: string
  label: string
  county: string | null
  lat: number
  lng: number
  diagnosis: string
  diagnosisRo: string
  score: number
  excessKwhDay: number | null
  lossLeiMonth: number | null
  expectedValueLei: number
  customers: number
  decision: Decision
  decisionRo: string
  rule: string | null
  reason: string | null
  crew: string | null
  factors: { label: string; contribution: number }[]
  proba: Record<string, number>
  suspectMeter: string | null
  model: string | null
  predictionId: string | null
}

export interface RankRow {
  id: string
  source: SourceKey
  label: string
  kind: string
  expectedValueLei: number
  score: number
  decision: Decision
  decisionRo: string
  rule: string | null
  reason: string | null
  crew: string | null
}

export interface QueueRow {
  id: string
  source: SourceKey
  label: string
  score: number
  low: number | null
  high: number | null
  reason: string | null
  expectedValueLei: number
}

export interface Route {
  crew: string
  depot: string
  depart: string
  back: string
  stops: number
  km: number
  sources: Partial<Record<SourceKey, number>>
}

export interface EvalRow {
  key: string
  name: string
  netLeiDay: number
  kmDay: number
  uselessRate: number
  urgentMissedRate: number
  stormsCovered: number
  stormsTotal: number
}

interface Data {
  source: string
  planId: string
  planDate: string
  generatedAt: string
  plannerVersion: string
  summary: {
    items_in: number
    items_valid: number
    items_invalid: number
    assigned: number
    deferred: number
    human_review: number
    remote_actions: number
    notifications: number
    crews_used: number
    expected_value_lei: number
    total_km: number
  }
  decisionCounts: Record<string, number>
  perSource: Record<SourceKey, Record<string, number>>
  posts: PostRow[]
  cases: Case[]
  ranking: RankRow[]
  queue: QueueRow[]
  routes: Route[]
  alerts: { id: string; severity: string; title: string; body: string }[]
  notifications: { id: string; audience: string; message: string }[]
  models: {
    A: { version: string; rocAuc: number; prAuc: number; precisionAtK: number; sgccRocAuc: number; iforestRocAuc: number }
    B: { version: string; roc_auc: number; pr_auc: number; recall_at_thr: number; recall_severe_at_thr: number; brier: number }
    C: { version: string; mae_vmax_pu: number; coverage_p10_p90: number; roc_auc_exceed: number; pr_auc_exceed: number }
    bilant: {
      version: string
      diagnosisAccuracy: number
      diagnosisMacroF1: number
      normalMaeKwhDay: number
      fixedPctMaeKwhDay: number
      coverageP10P90: number
      testPosts: number
    }
  }
  evaluation: {
    days: number
    synthetic: boolean
    rows: EvalRow[]
    reproduce: string
    robust: { days: number; rows: { key: string; name: string; netLeiDay: number; urgentMissedRate: number }[] }
    ablations: { key: string; label: string; netLeiDay: number; uselessRate: number; urgentMissedRate: number }[]
  }
  items: Item[]
  /** [id, source, lat, lng, decision, expectedValueLei, score] */
  allItems: [string, SourceKey, number, number, Decision | null, number | null, number | null][]
  routeStops: { crew: string; seq: number; id: string; eta: string; lat: number; lng: number; source: SourceKey; label: string; km: number }[]
  audit: { id: string; ts: string; actor: string; action: string; workItem: string | null; prediction: string | null; model: string | null; rule: string | null; note: string | null }[]
  auditCounts: Record<string, number>
  modelCards: Record<"A" | "B" | "C" | "bilant", ModelCard>
  crews: Crew[]
  shift: { start: string; end: string }
}

export interface Crew {
  id: string
  depot: string
  depotRo: string
  skills: string[]
  size: number
}

export const SKILL_RO: Record<string, string> = {
  metering: "metering",
  lv_grid: "LV grid",
  mv_grid: "MV grid",
}

export interface ModelCard {
  id: string
  version: string
  task: string
  dataset: string[]
  split: string
  testSize: number
  primary: string
  metrics: Record<string, number>
  baselineId: string
  baseline: Record<string, number>
  syntheticShare: number | null
  reproduce: string
}

export interface Series {
  title: string
  unit: string
  /** [time, value, expected, low, high] */
  points: [string, number | null, number | null, number | null, number | null][]
  thresholds: Record<string, number>
  annotations: { t: string; label: string }[]
  synthetic: boolean | null
}

export interface Item {
  id: string
  source: SourceKey
  kind: string
  label: string
  county: string | null
  lat: number
  lng: number
  prediction: {
    model: string
    id: string
    label: string
    score: number | null
    low: number | null
    high: number | null
    point: number | null
    pointUnit: string | null
    pointInterval: [number, number] | null
    confidence: string | null
    abstain: boolean | null
    abstainReason: string | null
  }
  impact: { expectedValueLei: number; valueIfTrueLei: number; customers: number; urgencyHours: number | null; safety: boolean }
  effort: { duration_min: number; crew_skill: string; crew_size: number; requires_planned_outage: boolean } | null
  summary: string | null
  factors: { label: string; contribution: number }[]
  similar: { id: string; outcome: string; similarity: number; note: string }[]
  quality: { synthetic: boolean | null; issues: string[]; sources: string[] }
  action: string | null
  decision: Decision | null
  decisionRo: string | null
  rule: string | null
  threshold: Record<string, number | string | null>
  reason: string | null
  crew: string | null
  auditId: string | null
  series: Series | null
}


/** Source names and colours from the team's console (checked for colour blindness). */
export const SOURCES: Record<SourceKey, { name: string; long: string; color: string }> = {
  A: { name: "Meters", long: "Faulty or tampered meters and transformer energy balance", color: "#3b82f0" },
  B: { name: "Storms", long: "Outage risk over the next 24 hours", color: "#ff5cff" },
  C: { name: "Voltage", long: "Transformers where solar export raises voltage above 1.10 pu", color: "#ffc502" },
}

export const DECISION_RO: Record<Decision, string> = {
  assigned: "Crew assigned",
  remote_action: "Remote check",
  human_review: "Human review",
  deferred: "Deferred",
  notify: "Notification",
}

export const DIAGNOSIS_RO: Record<string, string> = {
  contor_client: "Faulty customer meter",
  furt_inainte_contor: "Theft upstream of the meter",
  pierdere_tehnica: "Technical loss in cables or phases",
  client_post_gresit: "Customer mapped to the wrong transformer",
  contor_bilant_setat: "Misconfigured transformer meter",
  normal: "Normal",
}

export const STATUS_OF_COLOR = { verde: "ok", galben: "watch", rosu: "bad" } as const

// Only presentation fields are localised. The source run and its contracts stay intact.
const sourceData = raw as unknown as Data
export const DB: Data = {
  ...sourceData,
  cases: sourceData.cases.map((c) => {
    return {
      ...c,
      label: c.label.replace(" (sintetic)", " (synthetic)"),
      diagnosisRo: DIAGNOSIS_RO[c.diagnosis],
      decisionRo: DECISION_RO[c.decision],
      reason: c.reason ? englishText(c.reason) : null,
      factors: c.factors.map((f) => ({ ...f, label: englishText(f.label) })),
    }
  }),
  evaluation: {
    ...sourceData.evaluation,
    rows: sourceData.evaluation.rows.map((r) => ({ ...r, name: EVALUATION_NAMES_EN[r.key] })),
  },
}

const months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
/** "8 July 2025" */
export function dateRo(iso: string) {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number)
  return `${d} ${months[m - 1]} ${y}`
}

export const PLAN_DATE_RO = dateRo(DB.planDate)

/** Shown wherever data appears, as the team requires. */
export const SYNTHETIC_NOTE = "Synthetic meters, transformers and crews on a real map. Weather and dates are real."
export const BILANT_NOTE = "Simulation using public data, designed for future validation with PPC data"
