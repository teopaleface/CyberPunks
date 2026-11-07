/** Etichete în română pentru valorile din contracte. Fără cod de server: se pot folosi și în client. */
import type { Confidence, CrewSkill, DecisionType, RecommendedAction } from "@/lib/contracts";
import type { DataSource } from "./types";

export const SOURCE_LABEL_RO: Record<DataSource, string> = {
  api: "API (în direct)",
  demo: "instantaneu demo",
  fixtures: "date de test (fixtures)",
};

/** Eticheta scurtă a provenienței, pentru antet. */
export const PROVENANCE_SHORT_RO: Record<DataSource, string> = {
  api: "Agentul, în direct",
  demo: "Ultimul plan salvat",
  fixtures: "Date de test",
};

export const DECISION_LABEL_RO: Record<DecisionType, string> = {
  assigned: "în traseu",
  deferred: "amânată",
  human_review: "decide un om",
  remote_action: "acțiune la distanță",
  notify: "mesaj către clienți",
  rejected_invalid: "respinsă (date greșite)",
};

export const CONFIDENCE_RO: Record<Confidence, string> = {
  high: "încredere mare",
  medium: "încredere medie",
  low: "încredere scăzută",
};

export const ACTION_RO: Record<RecommendedAction, string> = {
  inspect_on_site: "verificare la fața locului",
  remote_reading: "citire la distanță",
  watchlist: "urmărire, fără vizită",
  human_review: "decide un om",
  preposition_crew: "echipă trimisă din timp în zonă",
  adjust_tap: "schimbarea prizei transformatorului",
  measurement_campaign: "analizor de calitate montat la post",
  notify_customers: "mesaj către prosumatori",
  no_action: "nicio acțiune",
};

export const SKILL_RO: Record<CrewSkill, string> = {
  metering: "contorizare",
  lv_grid: "joasă tensiune",
  mv_grid: "medie tensiune",
};

/** Ce estimează modelul (prediction.label). Necunoscutele rămân lizibile. */
const PREDICTION_LABEL_RO: Record<string, string> = {
  tamper: "suspect de manipulare",
  faulty: "suspect de defect",
  outage_risk: "risc de avarii",
  overvoltage: "tensiune peste limită",
};

export function predictionLabelRo(label: string): string {
  return PREDICTION_LABEL_RO[label] ?? label.replaceAll("_", " ");
}

/** Ce s-a confirmat în cazurile similare (similar_cases.outcome). */
const OUTCOME_RO: Record<string, string> = {
  furt_confirmat: "furt confirmat",
  contor_blocat: "contor blocat",
  contor_defect: "contor defect",
  fals_pozitiv: "fals pozitiv, totul în regulă",
  avarii_extinse: "avarii extinse",
  furtuna_confirmata: "furtună confirmată",
  fara_avarii: "fără avarii",
  supratensiune_confirmata: "supratensiune confirmată",
};

export function outcomeRo(outcome: string): string {
  return OUTCOME_RO[outcome] ?? outcome.replaceAll("_", " ");
}

/** Regulile din stratul de decizie, explicate pe scurt (rule_id → frază). Necunoscutele se afișează ca atare. */
const RULE_RO: Record<string, string> = {
  "R-VALUE-OVER-COST": "valoarea așteptată depășește costul vizitei",
  "R-ABSTAIN": "modelul nu e sigur, decide un om",
  "R-SAFETY-FIRST": "risc pentru oameni, prioritate maximă",
  "R-LOW-CONFIDENCE": "încredere prea mică pentru o echipă",
  "R-CHEAP-ACTION": "o acțiune ieftină ajunge",
  "R-NO-CAPACITY": "nu mai e capacitate în ture",
  "R-INVALID-INPUT": "date de intrare greșite, puse în carantină",
  "R-STORM-PREPOSITION": "echipă trimisă înainte de furtună",
  "R-PLANNED-OUTAGE-NOTICE": "întreruperea planificată cere anunțarea clienților",
  "R-BELOW-THRESHOLD": "riscul e sub prag, zona rămâne urmărită",
  "R-QUARANTINE": "date de intrare greșite, puse în carantină",
};

export function ruleRo(ruleId: string | null | undefined): string | null {
  if (!ruleId) return null;
  return RULE_RO[ruleId] ?? null;
}
