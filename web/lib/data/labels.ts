/** Etichete în română pentru valorile din contracte. Fără cod de server: se pot folosi și în client. */
import { englishText } from "@/lib/english";
import type { Confidence, CrewSkill, DecisionType, RecommendedAction } from "@/lib/contracts";
import type { DataSource } from "./types";

export const SOURCE_LABEL_RO: Record<DataSource, string> = {
  api: "API (live)",
  demo: "demo snapshot",
  fixtures: "test fixtures",
};

/** Eticheta scurtă a provenienței, pentru antet. */
export const PROVENANCE_SHORT_RO: Record<DataSource, string> = {
  api: "Live agent",
  demo: "Last saved plan",
  fixtures: "Test data",
};

export const DECISION_LABEL_RO: Record<DecisionType, string> = {
  assigned: "assigned",
  deferred: "deferred",
  human_review: "human review",
  remote_action: "remote action",
  notify: "customer message",
  rejected_invalid: "rejected (invalid data)",
};

export const CONFIDENCE_RO: Record<Confidence, string> = {
  high: "high confidence",
  medium: "medium confidence",
  low: "low confidence",
};

export const ACTION_RO: Record<RecommendedAction, string> = {
  inspect_on_site: "on-site inspection",
  remote_reading: "remote reading",
  watchlist: "monitor, no visit",
  human_review: "human review",
  preposition_crew: "crew prepositioning",
  adjust_tap: "transformer tap adjustment",
  measurement_campaign: "install a power quality analyser at the substation",
  notify_customers: "message to solar customers",
  office_correction: "office data correction, no visit",
  grid_inspection: "low-voltage grid inspection",
  phase_rebalance: "phase rebalancing",
  offer_battery: "battery offer for solar customers",
  export_limit: "limit exports to the grid",
  transformer_upgrade: "larger transformer",
  no_action: "no action",
};

export const SKILL_RO: Record<CrewSkill, string> = {
  metering: "metering",
  lv_grid: "low voltage",
  mv_grid: "medium voltage",
};

/** Ce estimează modelul (prediction.label). Necunoscutele rămân lizibile. */
const PREDICTION_LABEL_RO: Record<string, string> = {
  tamper: "suspected tampering",
  faulty: "suspected fault",
  outage_risk: "outage risk",
  overvoltage: "overvoltage",
  // bilanțul pe post: cauza probabilă a lipsei
  normal: "normal losses",
  contor_client: "faulty customer meter",
  furt_inainte_contor: "theft before the meter",
  pierdere_tehnica: "technical loss (cable, unbalanced phases)",
  client_post_gresit: "customer assigned to the wrong substation",
  contor_bilant_setat: "incorrectly configured balance meter",
};

export function predictionLabelRo(label: string): string {
  return PREDICTION_LABEL_RO[label] ?? label.replaceAll("_", " ");
}

/** Ce s-a confirmat în cazurile similare (similar_cases.outcome). */
const OUTCOME_RO: Record<string, string> = {
  furt_confirmat: "confirmed theft",
  contor_blocat: "stuck meter",
  contor_defect: "faulty meter",
  fals_pozitiv: "false positive, no fault found",
  avarii_extinse: "widespread outages",
  furtuna_confirmata: "confirmed storm",
  fara_avarii: "no outages",
  supratensiune_confirmata: "confirmed overvoltage",
};

export function outcomeRo(outcome: string): string {
  return OUTCOME_RO[outcome] ?? outcome.replaceAll("_", " ");
}

/** Regulile din stratul de decizie, explicate pe scurt (rule_id → frază). Necunoscutele se afișează ca atare. */
const RULE_RO: Record<string, string> = {
  "R-VALUE-OVER-COST": "expected value exceeds visit cost",
  "R-ABSTAIN": "model is uncertain, human decision required",
  "R-SAFETY-FIRST": "safety risk, highest priority",
  "R-LOW-CONFIDENCE": "confidence too low to dispatch a crew",
  "R-CHEAP-ACTION": "a low-cost action is sufficient",
  "R-NO-CAPACITY": "no shift capacity left",
  "R-INVALID-INPUT": "invalid input, quarantined",
  "R-STORM-PREPOSITION": "crew positioned before the storm",
  "R-PLANNED-OUTAGE-NOTICE": "planned outage requires customer notice",
  "R-BELOW-THRESHOLD": "risk below threshold, continue monitoring",
  "R-QUARANTINE": "invalid input, quarantined",
  "R-REMEDY-LADDER": "cheapest remedy that brings voltage below 1.10 pu",
  "R-SAFETY": "safety risk, first stop on the route",
  "R-SAFETY-NO-CREW": "safety risk but no available crew, dispatcher alerted",
  "R-NO-CREW": "no suitable crew available",
  "R-CAPACITY": "shifts are full",
  "R-CAPACITY-REMOTE": "shifts are full, remote reading instead of a visit",
  "R-TIME-WINDOW": "crew cannot arrive within the required window",
  "R-WIDE-INTERVAL": "confidence interval is too wide",
  "R-NOT-WORTH-TRIP": "travel costs exceed the benefit",
  "R-DATA-QUALITY": "too much missing data",
  "R-HUMAN-APPROVE": "approved by dispatcher",
  "R-HUMAN-REJECT": "rejected by dispatcher",
  "R-HUMAN-DEFER": "deferred by dispatcher",
  "R-A-VISIT": "expected value exceeds visit cost",
  "R-A-VISIT-NO-REMOTE": "meter does not respond remotely, visit required",
  "R-A-REMOTE-FIRST": "remote reading first, at near-zero cost",
  "R-A-WATCH": "score below threshold, monitor without a visit",
  "R-B-PREPOSITION": "crew positioned before the storm",
  "R-B-BELOW-COST": "risk does not cover crew prepositioning cost",
  "R-B-REGION-CAP": "regional crew limit",
  "R-B-TOO-LATE": "crew cannot arrive before the storm",
  "R-C-TAP": "tap adjustment is justified",
  "R-C-TAP-NOTICE": "tap adjustment requires advance customer notice",
  "R-C-NOTIFY": "message to solar customers instead of a crew",
  "R-C-MEASURE": "measure at the substation first",
  "R-C-MEASURE-THEN-TAP": "measurements, then tap adjustment",
  "R-C-WATCH": "exceedance unlikely, continue monitoring",
  "R-A-VISIT-MEDIUM": "medium confidence, visit only with a large value margin",
  "R-BILANT-GRID": "energy balance indicates technical loss, grid crew required",
  "R-BILANT-METER": "energy balance indicates a faulty meter, metering crew required",
  "R-BILANT-OFFICE": "office data correction, no visit",
  // neutru: regula se aplică și când bilanțul nu confirmă (pragul `fusion_confirmed` spune care e cazul)
  "R-FUSION-BILANT": "meter checked against the substation energy balance",
  "R-BILANT-REMOTE": "energy balance, remote checks first",
  "R-BILANT-WATCH": "energy balance, value does not cover travel, continue monitoring",
  "R-SAFETY-OVER-CAP": "safety case above daily quota, triple priority without mandatory dispatch",
  "R-ABSTAIN-DATA": "invalid input, office data correction",
  "R-ABSTAIN-WATCH": "model is uncertain but value is low, continue monitoring",
  "R-HUMAN-QUEUE-FULL": "dispatcher's queue is full, carry over to the next plan",
  "R-B-BELOW-THRESHOLD": "storm below model threshold, no crew moved",
};

export function ruleRo(ruleId: string | null | undefined): string | null {
  if (!ruleId) return null;
  return RULE_RO[ruleId] ?? null;
}

/** Pragurile și cifrele din `Decision.threshold`, în cuvinte simple, cu unitatea potrivită. */
const THRESHOLD_RO: Record<string, string> = {
  score: "work item score",
  a_score: "model A score",
  combined_score: "combined score (A and energy balance)",
  fusion_a_score: "A score before energy balance",
  fusion_combined_score: "combined score",
  fusion_post_loss_lei_month: "substation loss from energy balance",
  fusion_confirmed: "confirmed by energy balance",
  post_excess_loss_lei_month: "excess substation loss",
  post_excess_loss_kwh_day: "excess substation energy deficit",
  safety_max_mandatory_per_day: "mandatory safety cases per day",
  human_review_max_per_day: "daily dispatcher queue capacity",
  preposition_min_score: "minimum score for crew prepositioning",
  participation_rate: "simulated participation",
  score_min: "minimum score",
  min_score: "minimum score",
  remote_min_score: "minimum score for remote reading",
  alert_min_score: "minimum score for an alert",
  breakeven_score: "break-even score",
  confidence_low: "low confidence",
  min_net_value_lei: "minimum net value",
  net_value_lei: "net value",
  expected_value_lei: "expected value",
  human_review_min_ev_lei: "minimum value for human review",
  visit_cost_lei: "visit cost",
  cost_lei: "total cost",
  action_cost_lei: "action cost",
  travel_cost_lei: "travel cost",
  travel_km_est: "estimated km",
  lei_per_work_hour: "RON per work hour",
  preposition_cost_lei: "crew prepositioning cost",
  tap_cost_lei: "tap adjustment cost",
  tap_change_visit_cost_lei: "tap adjustment cost",
  measurement_cost_lei: "measurement cost",
  net_tap_value_lei: "net value of tap adjustment",
  chosen_cost_lei: "chosen remedy cost",
  overvoltage_limit_pu: "voltage limit",
  vmax_p90_pu: "maximum P90 voltage",
  interval_width: "interval width",
  max_interval_width: "maximum accepted width",
  missing_ratio: "missing data",
  max_missing_ratio: "accepted missing data",
  max_crews_per_region: "maximum crews per region",
  arrive_before_start_min: "arrival ahead of storm by",
  safety_flag: "safety risk",
  safety_priority_multiplier: "safety priority multiplier",
  smart_meter: "smart meter",
  planned_notice_working_days: "working days of planned outage notice",
  abstain: "model abstained",
  human: "referred to human review",
  visit_min_score: "minimum visit score",
  medium_confidence_margin_lei: "required margin at medium confidence",
  p90_before_pu: "P90 voltage before remedy",
  p90_after_pu: "P90 voltage after remedy",
  remedy_cost_lei: "chosen remedy cost",
  remedy_steps: "combined steps",
  remedy_options_checked: "options checked",
};

const FLAG_KEYS = new Set(["safety_flag", "smart_meter", "abstain", "human", "fusion_confirmed"]);

export function thresholdLabelRo(key: string): string {
  return THRESHOLD_RO[key] ?? key.replaceAll("_", " ");
}

export function thresholdValueRo(key: string, v: unknown): string {
  if (typeof v === "boolean") return v ? "yes" : "no";
  if (typeof v !== "number") return String(v);
  const ro = (n: number, d: number) =>
    new Intl.NumberFormat("en-GB", { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
  if (FLAG_KEYS.has(key)) return v ? "yes" : "no";
  // scorurile întâi: „score_min” e un scor, nu minute
  if (key.includes("score") || key === "confidence_low") return ro(v, 2);
  if (key.endsWith("_lei")) return `${ro(v, Math.abs(v) >= 100 || Number.isInteger(v) ? 0 : 2)} RON`;
  if (key.endsWith("_lei_month")) return `${ro(v, 0)} RON per month`;
  if (key.endsWith("_kwh_day")) return `${ro(v, 1)} kWh/day`;
  if (key.endsWith("_rate")) return `${ro(v * 100, 0)}%`;
  if (key.endsWith("_pu")) return `${ro(v, 3).replace(/0$/, "")} pu`;
  if (key.endsWith("_days")) return `${ro(v, 0)} days`;
  if (key.endsWith("_min")) return `${ro(v, 0)} min`;
  if (key.startsWith("travel_km")) return `${ro(v, 1)} km`;
  if (key.includes("ratio") || key.includes("width")) return ro(v, 2);
  if (key.endsWith("multiplier")) return `×${ro(v, Number.isInteger(v) ? 0 : 1)}`;
  return Number.isInteger(v) ? ro(v, 0) : ro(v, 2);
}

// Un procent, cu „cu”/„de” dinainte dacă există: „cu 18273047%”, „de 1250,5%”, „~-1.500.000%”.
const PERCENT = /(?:\b(?:cu|de)\s+)?~?[+\-−]?(\d{1,3}(?:[.,]\d{3}){2,}|\d+(?:[.,]\d+)?)\s?%/g;

function percentValue(n: string): number {
  // „18.273.047” are separatori de mii; „1827.5” sau „1827,5” are zecimale.
  if (/^\d{1,3}(?:[.,]\d{3}){2,}$/.test(n)) return Number(n.replace(/[.,]/g, ""));
  return Number(n.replace(",", "."));
}

/**
 * Plasa de siguranță pentru procente absurde (împărțiri la aproape zero): orice procent peste 999%
 * se afișează „de peste 10 ori” (decizia lui Teo, 7 nov., 15:30). „A crescut cu 18273047%” devine
 * „a crescut de peste 10 ori”. Datele originale rămân neatinse; e doar o protecție la afișare.
 */
export function clampPercentRo(text: string): string {
  const guarded = text
    .replace(PERCENT, (m, n: string) => (percentValue(n) > 999 ? "de peste 10 ori" : m))
    // o probabilitate de 100% sună a certitudine: „peste 99%” (cererea din QA)
    .replace(/(probabilit\p{L}*(?:\s+\p{L}+)?\s+(?:de\s+)?)100\s?%/giu, "$1peste 99%");
  return englishText(guarded);
}

/**
 * Textul unui factor, pregătit pentru afișare: procentele peste 999% devin „de peste 10 ori”,
 * zecimalele cu punct devin virgulă („0.46” → „0,46”), prima literă e mare, fără punct la final.
 */
export function factorLabelRo(label: string): string {
  const out = clampPercentRo(label).trim();
  if (!out) return out;
  return (out.charAt(0).toLocaleUpperCase("en-GB") + out.slice(1)).replace(/\.$/, "");
}

/**
 * Ce a decis agentul pentru lucrările unei alerte, numărat din decizii: „12 în trasee, 175 verificate de la
 * distanță, 18 la om”. Textul alertei vine de la planificator; numărătoarea arată ce s-a întâmplat de fapt.
 * Null dacă alerta are sub două lucrări sau nicio decizie cunoscută.
 */
export function alertOutcomeRo(ids: string[] | undefined, decisions: Record<string, { decision: string } | undefined>): string | null {
  if (!ids || ids.length < 2) return null;
  const counts = new Map<string, number>();
  for (const id of ids) {
    const d = decisions[id]?.decision;
    if (d) counts.set(d, (counts.get(d) ?? 0) + 1);
  }
  if (!counts.size) return null;
  const n = (v: number) => new Intl.NumberFormat("en-GB").format(v);
  const phrase: Record<string, (v: number) => string> = {
    assigned: (v) => (v === 1 ? "1 assigned" : `${n(v)} Assigned`),
    remote_action: (v) => (v === 1 ? "1 checked remotely" : `${n(v)} checked remotely`),
    human_review: (v) => `${n(v)} Human review`,
    notify: (v) => `${n(v)} with customer message`,
    deferred: (v) => (v === 1 ? "1 deferred" : `${n(v)} deferred`),
    rejected_invalid: (v) => (v === 1 ? "1 rejected at intake" : `${n(v)} rejected at intake`),
  };
  const order = ["assigned", "human_review", "remote_action", "notify", "deferred", "rejected_invalid"];
  const parts = order.filter((k) => counts.get(k)).map((k) => phrase[k](counts.get(k)!));
  const known = [...counts.values()].reduce((a, b) => a + b, 0);
  if (known < ids.length) parts.push(`${n(ids.length - known)} without a decision`);
  return parts.join(", ");
}

/** Acțiunile din jurnal (AuditRecord.action), în cuvinte. */
const AUDIT_ACTION_RO: Record<string, string> = {
  run: "agent generated the plan",
  fusion: "checked against the energy balance",
  replan: "agent recalculated the plan",
  review_approve: "human approved",
  review_reject: "human rejected",
  review_defer: "human deferred",
  approve: "human approved",
  reject: "human rejected",
  defer: "human deferred",
  plan_approved: "human approved crew assignments",
};

export function auditActionRo(action: string): string {
  return AUDIT_ACTION_RO[action] ?? (DECISION_LABEL_RO as Record<string, string>)[action] ?? action.replaceAll("_", " ");
}
