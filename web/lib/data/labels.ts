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
  office_correction: "corecție în bază, fără deplasare",
  grid_inspection: "inspecția rețelei de joasă tensiune",
  phase_rebalance: "reechilibrarea fazelor",
  offer_battery: "ofertă de baterii pentru prosumatori",
  export_limit: "limitarea injecției în rețea",
  transformer_upgrade: "transformator mai mare",
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
  // bilanțul pe post: cauza probabilă a lipsei
  normal: "pierderi normale",
  contor_client: "contor defect la un client",
  furt_inainte_contor: "furt înainte de contor",
  pierdere_tehnica: "pierdere tehnică (cablu, faze dezechilibrate)",
  client_post_gresit: "client trecut la postul greșit în bază",
  contor_bilant_setat: "contorul de bilanț setat greșit",
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
  "R-REMEDY-LADDER": "cea mai ieftină soluție care aduce tensiunea sub 1,10",
  "R-SAFETY": "risc pentru oameni: intră primul în traseu",
  "R-SAFETY-NO-CREW": "risc pentru oameni, dar nicio echipă liberă: alertă la dispecerat",
  "R-NO-CREW": "nicio echipă potrivită liberă",
  "R-CAPACITY": "turele sunt pline",
  "R-CAPACITY-REMOTE": "turele sunt pline: citire la distanță în loc de vizită",
  "R-TIME-WINDOW": "echipa nu ajunge în fereastra în care contează",
  "R-WIDE-INTERVAL": "intervalul de încredere e prea larg",
  "R-NOT-WORTH-TRIP": "drumul costă mai mult decât câștigul",
  "R-DATA-QUALITY": "prea multe date lipsă",
  "R-HUMAN-APPROVE": "aprobat de dispecer",
  "R-HUMAN-REJECT": "respins de dispecer",
  "R-HUMAN-DEFER": "amânat de dispecer",
  "R-A-VISIT": "valoarea așteptată depășește costul vizitei",
  "R-A-VISIT-NO-REMOTE": "contorul nu răspunde la distanță: vizită",
  "R-A-REMOTE-FIRST": "întâi citire la distanță, aproape gratuită",
  "R-A-WATCH": "scor sub prag: urmărire, fără vizită",
  "R-B-PREPOSITION": "echipă trimisă înainte de furtună",
  "R-B-BELOW-COST": "riscul nu acoperă costul unei echipe trimise din timp",
  "R-B-REGION-CAP": "limita de echipe pe regiune",
  "R-B-TOO-LATE": "echipa n-ar ajunge înainte de furtună",
  "R-C-TAP": "schimbarea prizei se justifică",
  "R-C-TAP-NOTICE": "schimbarea prizei cere anunțarea clienților din timp",
  "R-C-NOTIFY": "mesaj către prosumatori în loc de echipă",
  "R-C-MEASURE": "întâi măsurători la post",
  "R-C-MEASURE-THEN-TAP": "măsurători, apoi schimbarea prizei",
  "R-C-WATCH": "depășire puțin probabilă: urmărire",
  "R-A-VISIT-MEDIUM": "încredere medie: vizită doar dacă marja de valoare e mare",
  "R-BILANT-GRID": "bilanțul arată pierdere tehnică: echipa de rețea",
  "R-BILANT-METER": "bilanțul arată contor defect: echipa de contoare",
  "R-BILANT-OFFICE": "corecție în bază, fără deplasare",
  "R-FUSION-BILANT": "contorul e confirmat de bilanțul postului",
};

export function ruleRo(ruleId: string | null | undefined): string | null {
  if (!ruleId) return null;
  return RULE_RO[ruleId] ?? null;
}

/** Pragurile și cifrele din `Decision.threshold`, în cuvinte simple, cu unitatea potrivită. */
const THRESHOLD_RO: Record<string, string> = {
  score: "scorul lucrării",
  score_min: "scor minim",
  min_score: "scor minim",
  remote_min_score: "scor minim pentru citire la distanță",
  alert_min_score: "scor minim pentru alertă",
  breakeven_score: "scorul de la care merită",
  confidence_low: "încredere scăzută",
  min_net_value_lei: "valoare netă minimă",
  net_value_lei: "valoare netă",
  expected_value_lei: "valoare așteptată",
  human_review_min_ev_lei: "valoare minimă pentru a întreba un om",
  visit_cost_lei: "costul vizitei",
  cost_lei: "cost total",
  action_cost_lei: "costul acțiunii",
  travel_cost_lei: "costul drumului",
  travel_km_est: "km estimați",
  lei_per_work_hour: "lei pe oră de lucru",
  preposition_cost_lei: "costul echipei trimise din timp",
  tap_cost_lei: "costul schimbării prizei",
  tap_change_visit_cost_lei: "costul schimbării prizei",
  measurement_cost_lei: "costul măsurătorilor",
  net_tap_value_lei: "valoarea netă a schimbării prizei",
  chosen_cost_lei: "costul soluției alese",
  overvoltage_limit_pu: "limita de tensiune",
  vmax_p90_pu: "tensiunea maximă P90",
  interval_width: "lățimea intervalului",
  max_interval_width: "lățime maximă acceptată",
  missing_ratio: "date lipsă",
  max_missing_ratio: "date lipsă acceptate",
  max_crews_per_region: "echipe maxime pe regiune",
  arrive_before_start_min: "ajunge înainte de furtună cu",
  safety_flag: "risc pentru oameni",
  safety_priority_multiplier: "prioritate înmulțită pentru siguranță",
  smart_meter: "contor inteligent",
  planned_notice_working_days: "zile lucrătoare de anunț pentru întrerupere",
  abstain: "modelul s-a abținut",
  human: "trimis la om",
  visit_min_score: "scor minim pentru vizită",
  medium_confidence_margin_lei: "marja cerută la încredere medie",
  p90_before_pu: "tensiunea P90 fără soluție",
  p90_after_pu: "tensiunea P90 după soluție",
  remedy_cost_lei: "costul soluției alese",
  remedy_steps: "trepte combinate",
  remedy_options_checked: "variante verificate",
};

const FLAG_KEYS = new Set(["safety_flag", "smart_meter", "abstain", "human"]);

export function thresholdLabelRo(key: string): string {
  return THRESHOLD_RO[key] ?? key.replaceAll("_", " ");
}

export function thresholdValueRo(key: string, v: unknown): string {
  if (typeof v !== "number") return String(v);
  const ro = (n: number, d: number) =>
    new Intl.NumberFormat("ro-RO", { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
  if (FLAG_KEYS.has(key)) return v ? "da" : "nu";
  // scorurile întâi: „score_min” e un scor, nu minute
  if (key.includes("score") || key === "confidence_low") return ro(v, 2);
  if (key.endsWith("_lei")) return `${ro(v, Math.abs(v) >= 100 || Number.isInteger(v) ? 0 : 2)} lei`;
  if (key.endsWith("_pu")) return `${ro(v, 3).replace(/0$/, "")} pu`;
  if (key.endsWith("_days")) return `${ro(v, 0)} zile`;
  if (key.endsWith("_min")) return `${ro(v, 0)} min`;
  if (key.startsWith("travel_km")) return `${ro(v, 1)} km`;
  if (key.includes("ratio") || key.includes("width")) return ro(v, 2);
  if (key.endsWith("multiplier")) return `×${ro(v, Number.isInteger(v) ? 0 : 1)}`;
  return Number.isInteger(v) ? ro(v, 0) : ro(v, 2);
}

/**
 * Textul unui factor, pregătit pentru afișare: zecimalele cu punct devin virgulă („0.46” → „0,46”),
 * iar procentele absurde (împărțiri la aproape zero, de exemplu „18273047%”) devin „peste 1.000%”.
 * Datele originale rămân neatinse; e doar o protecție la afișare.
 */
export function factorLabelRo(label: string): string {
  const t = label
    .replace(/(\d)\.(\d)/g, "$1,$2")
    .replace(/(\d+(?:,\d+)?)\s?%/g, (m, n: string) => (Number(n.replace(",", ".")) > 1000 ? "peste 1.000%" : m));
  const out = t.trim();
  if (!out) return out;
  return (out.charAt(0).toLocaleUpperCase("ro-RO") + out.slice(1)).replace(/\.$/, "");
}

/** Acțiunile din jurnal (AuditRecord.action), în cuvinte. */
const AUDIT_ACTION_RO: Record<string, string> = {
  run: "agentul a făcut planul",
  replan: "agentul a refăcut planul",
  review_approve: "omul a aprobat",
  review_reject: "omul a respins",
  review_defer: "omul a amânat",
  approve: "omul a aprobat",
  reject: "omul a respins",
  defer: "omul a amânat",
  plan_approved: "omul a aprobat lista echipelor",
};

export function auditActionRo(action: string): string {
  return AUDIT_ACTION_RO[action] ?? (DECISION_LABEL_RO as Record<string, string>)[action] ?? action.replaceAll("_", " ");
}
