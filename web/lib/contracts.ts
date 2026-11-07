// generat din contracts/*.schema.json — nu edita manual
// Regenerează cu: cd web && bun run gen:types

export type Source = "A" | "B" | "C";
export type Kind = "meter_inspection" | "storm_prepositioning" | "voltage_mitigation";
export type AssetType = "meter" | "zone" | "transformer_post";
export type Confidence = "high" | "medium" | "low";
export type CrewSkill = "metering" | "lv_grid" | "mv_grid";
export type RecommendedAction =
  | "inspect_on_site"
  | "remote_reading"
  | "watchlist"
  | "human_review"
  | "preposition_crew"
  | "adjust_tap"
  | "measurement_campaign"
  | "notify_customers"
  | "office_correction"
  | "grid_inspection"
  | "phase_rebalance"
  | "offer_battery"
  | "export_limit"
  | "transformer_upgrade"
  | "no_action";
export type DecisionType =
  "assigned" | "deferred" | "human_review" | "remote_action" | "notify" | "rejected_invalid";

/**
 * Toate contractele, după numele fișierului de schemă din contracts/.
 */
export interface Contracts {
  work_item: WorkItem;
  plan: Plan;
  audit: AuditRecord;
  model_report: ModelReport;
  series: Series;
}
export interface WorkItem {
  contract_version?: "1.0";
  /**
   * <sursă>-<YYYYMMDD>-<asset_id>
   */
  work_item_id: string;
  source: Source;
  kind: Kind;
  asset_id: string;
  asset_type: AssetType;
  location: Location;
  target_date: string;
  time_window?: TimeWindow | null;
  prediction: Prediction;
  impact: Impact;
  effort: Effort;
  explanation: Explanation;
  data_quality: DataQuality;
  recommended_action: RecommendedAction;
  created_at: string;
  /**
   * Câmpuri specifice sursei (serii pentru grafice etc.)
   */
  extra?: {
    [k: string]: unknown;
  };
}
export interface Location {
  /**
   * Latitudine WGS84, în România
   */
  lat: number;
  /**
   * Longitudine WGS84, în România
   */
  lon: number;
  /**
   * Zona operativă (vezi config/area.yaml)
   */
  zone_id: string;
  county?: string | null;
  /**
   * Etichetă lizibilă, de exemplu 'PT 1432, Chiajna'
   */
  label?: string | null;
}
export interface TimeWindow {
  start: string;
  end: string;
}
export interface Prediction {
  /**
   * De exemplu 'a-lgbm', 'b-lgbm-quantile', 'c-surrogate'
   */
  model_id: string;
  /**
   * Versiunea modelului, de exemplu 'a-lgbm@3f2c1ab'
   */
  model_version: string;
  /**
   * ID unic al predicției (uuid4)
   */
  prediction_id: string;
  /**
   * Clasa sau problema estimată: 'faulty', 'tamper', 'outage_risk', 'overvoltage'
   */
  label: string;
  /**
   * Probabilitate calibrată ca problema să fie reală
   */
  score: number;
  interval_low?: number | null;
  interval_high?: number | null;
  /**
   * Valoare estimată: tensiune maximă (pu), clienți afectați etc.
   */
  point_estimate?: number | null;
  point_unit?: string | null;
  /**
   * Interval pentru point_estimate (P10, P90)
   */
  point_interval?: [number, number] | null;
  confidence: Confidence;
  /**
   * Modelul spune 'nu sunt sigur'
   */
  abstain?: boolean;
  abstain_reason?: string | null;
}
export interface Impact {
  /**
   * score × value_if_true_lei, minus nimic; costul vizitei îl scade planificatorul
   */
  expected_value_lei: number;
  /**
   * Câți lei se câștigă sau se evită dacă problema e reală și o rezolvăm
   */
  value_if_true_lei: number;
  customers_affected?: number;
  /**
   * În câte ore trebuie acționat ca să mai conteze
   */
  urgency_hours: number;
  /**
   * Risc pentru oameni (de exemplu șuntare cu risc de incendiu)
   */
  safety_flag?: boolean;
  /**
   * Cheia din config/economics.yaml folosită la calcul
   */
  assumptions_ref?: string | null;
}
export interface Effort {
  duration_min: number;
  crew_skill: CrewSkill;
  crew_size?: number;
  requires_planned_outage?: boolean;
}
export interface Explanation {
  /**
   * @minItems 1
   * @maxItems 8
   */
  top_factors: Factor[];
  /**
   * @maxItems 5
   */
  similar_cases?: SimilarCase[];
  /**
   * O frază generată din șablon, cu cifrele verificate în cod
   */
  summary_ro: string;
}
export interface Factor {
  feature: string;
  /**
   * Motivul în cuvinte simple, de exemplu '9 zile cu consum zero'
   */
  label_ro: string;
  value?: number | string | null;
  /**
   * Contribuția la scor (de exemplu valoarea SHAP)
   */
  contribution: number;
}
export interface SimilarCase {
  case_id: string;
  /**
   * Ce s-a confirmat atunci, de exemplu 'contor_blocat', 'furtuna_confirmata'
   */
  outcome: string;
  similarity: number;
  note_ro?: string | null;
}
export interface DataQuality {
  missing_ratio: number;
  /**
   * Probleme găsite la intrare și cum au fost tratate
   */
  input_issues?: string[];
  /**
   * True dacă activul sau datele sunt sintetice
   */
  synthetic: boolean;
  /**
   * Surse citate, de exemplu 'SGCC', 'Open-Meteo forecast'
   *
   * @minItems 1
   */
  data_sources: string[];
}
export interface Plan {
  contract_version?: "1.0";
  plan_id: string;
  plan_date: string;
  generated_at: string;
  planner_version: string;
  scenario: string;
  summary: PlanSummary;
  routes: Route[];
  decisions: Decision[];
  alerts?: Alert[];
  notifications?: Notification[];
  sources_status: {
    A?: "ok" | "missing" | "degraded";
    B?: "ok" | "missing" | "degraded";
    C?: "ok" | "missing" | "degraded";
  };
}
export interface PlanSummary {
  items_in: number;
  items_valid: number;
  items_invalid: number;
  assigned: number;
  deferred: number;
  human_review: number;
  remote_actions: number;
  notifications: number;
  crews_used: number;
  expected_value_lei: number;
  total_km: number;
}
export interface Route {
  crew_id: string;
  depot_id: string;
  /**
   * Plecarea din bază
   */
  depart_at?: string | null;
  /**
   * Întoarcerea în bază
   */
  return_at?: string | null;
  stops: Stop[];
  total_km: number;
  total_work_min: number;
  total_travel_min: number;
}
export interface Stop {
  seq: number;
  work_item_id: string;
  eta: string;
  duration_min: number;
  travel_km: number;
}
export interface Decision {
  work_item_id: string;
  decision: DecisionType;
  reason_ro: string;
  /**
   * Regula din stratul de decizie care a produs decizia
   */
  rule_id: string;
  /**
   * Pragurile folosite, cu valorile lor
   */
  threshold?: {
    [k: string]: number;
  };
  priority_score?: number | null;
  rank?: number | null;
  crew_id?: string | null;
  audit_id: string;
}
export interface Alert {
  alert_id: string;
  severity: "info" | "warning" | "critical";
  title_ro: string;
  body_ro: string;
  work_item_ids?: string[];
  channel: "dispecerat" | "echipa" | "clienti";
  created_at: string;
}
export interface Notification {
  notification_id: string;
  audience: "prosumatori" | "clienti_zona" | "echipa";
  asset_id: string;
  message_ro: string;
  scheduled_for: string;
  work_item_id?: string | null;
  /**
   * În demo nu se trimite nimic în afară
   */
  demo_only?: boolean;
}
export interface AuditRecord {
  audit_id: string;
  ts: string;
  actor: "agent" | "human";
  action: string;
  work_item_id?: string | null;
  prediction_id?: string | null;
  model_version?: string | null;
  rule_id?: string | null;
  threshold?: {
    [k: string]: number;
  };
  inputs_sha256?: string | null;
  note?: string | null;
}
export interface ModelReport {
  contract_version?: "1.0";
  source: Source;
  model_id: string;
  model_version: string;
  /**
   * De exemplu 'clasificare dezechilibrată', 'regresie cuantilă'
   */
  task: string;
  /**
   * Surse de date folosite, citate
   *
   * @minItems 1
   */
  dataset: string[];
  /**
   * Cum e făcut setul de test (pe timp, pe clienți, pe rețele nevăzute)
   */
  split: string;
  test_size: number;
  primary_metric: string;
  metrics: {
    [k: string]: number;
  };
  baseline_id: string;
  baseline_metrics: {
    [k: string]: number;
  };
  /**
   * Ce parte din datele de test e sintetică
   */
  synthetic_share: number;
  created_at: string;
  /**
   * Comanda care refăce exact aceste cifre
   */
  reproduce_cmd: string;
}
export interface Series {
  contract_version?: "1.0";
  work_item_id: string;
  source: Source;
  title_ro: string;
  /**
   * kWh, km/h, pu etc.
   */
  unit: string;
  /**
   * @minItems 1
   */
  points: SeriesPoint[];
  /**
   * De exemplu {'limita_tensiune_pu': 1.10}
   */
  thresholds?: {
    [k: string]: number;
  };
  annotations?: SeriesAnnotation[];
  synthetic: boolean;
}
export interface SeriesPoint {
  t: string;
  /**
   * Valoarea observată sau prognozată
   */
  value?: number | null;
  /**
   * Ce ar fi fost normal (A) sau P50 (B, C)
   */
  expected?: number | null;
  /**
   * Marginea de jos a intervalului (P10)
   */
  low?: number | null;
  /**
   * Marginea de sus a intervalului (P90)
   */
  high?: number | null;
  /**
   * De exemplu 'zero', 'gol', 'salt', 'peste_limita'
   */
  flag?: string | null;
}
export interface SeriesAnnotation {
  t: string;
  label_ro: string;
}
