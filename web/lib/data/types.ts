/**
 * Tipurile stratului de date. Fără cod la rulare: pot fi importate și din componente client
 * (`import type { PlanView } from "@/lib/data/types"`).
 */
import type {
  Alert,
  AuditRecord,
  Decision,
  ModelReport,
  Plan,
  Route,
  Source,
  Stop,
  WorkItem,
} from "@/lib/contracts";

/** De unde au venit datele afișate. */
export type DataSource = "api" | "demo" | "fixtures";
/** Ce sursă cere configurarea (DATA_SOURCE). `auto` alege singur. */
export type DataSourceMode = "auto" | DataSource;
/** Sursa unei lucrări: A (contoare), B (furtună), C (prosumatori). */
export type WorkItemSource = Source;

/** O linie dintr-un fișier care nu a putut fi citită (JSON stricat sau lucrare incompletă). */
export interface ParseIssue {
  file: string;
  line: number;
  message: string;
  raw?: string;
}

/** Orice citire întoarce datele plus proveniența lor, ca interfața să afișeze sursa. */
export interface Sourced<T> {
  data: T;
  source: DataSource;
  /** Momentul citirii, ISO 8601. */
  fetchedAt: string;
  /** Explicație în cuvinte simple când nu s-a putut folosi sursa dorită. */
  degradedReason?: string;
  /** URL-ul sau fișierele citite. */
  detail?: string;
  parseErrors?: ParseIssue[];
}

export interface SourceInfo {
  source: DataSource;
  degradedReason?: string;
  detail?: string;
}

/** Răspunsul de la GET /health. */
export interface ApiHealth {
  status: string;
  version?: string;
  sources_status?: Record<string, string>;
  [key: string]: unknown;
}

export interface ApiProbe {
  ok: boolean;
  base: string;
  latencyMs: number;
  checkedAt: string;
  health?: ApiHealth;
  error?: string;
}

export interface HealthView {
  mode: DataSourceMode;
  apiBase: string;
  repoRoot: string;
  defaultScenario: string;
  api: ApiProbe;
  /** Există instantaneu demo (outputs/demo) pentru scenariul implicit. */
  demoAvailable: boolean;
  fixturesAvailable: boolean;
  /** Sursa pe care o alege acum modul curent pentru scenariul implicit. */
  resolvedSource: DataSource;
}

export interface ScenarioInfo {
  id: string;
  label_ro: string;
  date?: string | null;
  weather?: string | null;
  /** Există instantaneu demo pentru scenariu (outputs/demo). */
  hasDemo?: boolean;
  /** API: scenariul are deja un plan calculat. */
  hasPlan?: boolean;
  /** API: „live” (modelele rulează) sau „fixtures”. */
  mode?: string;
}

export interface Depot {
  depot_id: string;
  label_ro: string;
  lat: number;
  lon: number;
  region?: string;
}

export interface Crew {
  crew_id: string;
  depot_id: string;
  skills: string[];
  size: number;
  /** it_mt (înaltă și medie tensiune) | jt (joasă tensiune) */
  crew_type?: string;
  crew_type_label?: string;
}

export interface AreaConfig {
  operator?: string;
  timezone?: string;
  regions: Record<string, { label_ro: string; counties: string[] }>;
  /** Caseta demo București-Ilfov, pentru încadrarea inițială a hărții. */
  bbox: { lat_min: number; lat_max: number; lon_min: number; lon_max: number } | null;
  depots: Depot[];
}

export interface CrewsConfig {
  shift: { start: string; end: string } | null;
  crews: Crew[];
}

export interface ResolvedStop extends Stop {
  workItem: WorkItem | null;
  decision: Decision | null;
  lat: number | null;
  lon: number | null;
  label: string | null;
}

export interface ResolvedRoute extends Omit<Route, "stops"> {
  stops: ResolvedStop[];
  crew: Crew | null;
  depot: Depot | null;
  /** Traseul pentru hartă, [lon, lat] (ordinea MapLibre): bază → opriri → bază. */
  path: [number, number][];
}

export interface PlanView {
  scenario: string;
  plan: Plan;
  workItems: WorkItem[];
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  alertsByWorkItemId: Record<string, Alert[]>;
  routes: ResolvedRoute[];
  /** Lucrări primite care nu au nicio decizie în plan. */
  unplannedItems: WorkItem[];
  /** Opriri din trasee pentru care nu avem lucrarea (deci nici coordonatele). */
  unresolvedStopIds: string[];
  /** Lucrări respinse la intrare (doar în fixtures: work_items_invalid.jsonl), obiecte brute. */
  invalidItems: Record<string, unknown>[];
  audit: AuditRecord[];
  area: AreaConfig;
  depots: Depot[];
  crews: Crew[];
  shift: CrewsConfig["shift"];
  sources: { plan: SourceInfo; workItems: SourceInfo; audit: SourceInfo };
  /** Probleme la citirea config/*.yaml. */
  configIssues: string[];
}

export interface WorkItemDetail {
  workItem: WorkItem;
  decision: Decision | null;
  audit: AuditRecord[];
  alerts: Alert[];
  /** Lucrare respinsă la intrare (date greșite); obiectul nu respectă contractul. */
  invalid: boolean;
}

export interface MetricsBundle {
  A: ModelReport | null;
  B: ModelReport | null;
  C: ModelReport | null;
  bilant?: ModelReport | null;
  planner: Record<string, unknown> | null;
}

export type ReviewDecision = "approve" | "reject" | "defer";

export interface RunTimings {
  perceive: number;
  estimate: number;
  decide: number;
  act: number;
}

export interface RunResult {
  plan_id: string;
  timings: RunTimings;
}

/** Rezultatul unei acțiuni de server: nu aruncă niciodată spre client. */
export type ActionResult<T extends object = object> = ({ ok: true } & T) | { ok: false; error: string };

/** Un post de transformare, unitatea comună pentru A (contoare, bilanț) și C (tensiune). Forma din GET /posts. */
export interface PostSummary {
  post_id: string;
  lat: number;
  lon: number;
  zone_id?: string | null;
  label?: string | null;
  loss_lei_month?: number | null;
  loss_kwh_day?: number | null;
  diagnosis?: string | null;
  bilant_score?: number | null;
  bilant_work_item_id?: string | null;
  bilant_decision?: string | null;
  bilant_rule_id?: string | null;
  voltage_p90_pu?: number | null;
  c_work_item_id?: string | null;
  c_decision?: string | null;
  c_rule_id?: string | null;
  meters_flagged?: number;
  meter_work_item_ids?: string[];
  synthetic?: boolean;
  /** verde, galben, roșu sau necunoscut (după lei pierduți pe lună). */
  color?: string | null;
  /** Doar la derivare (fără API): de unde vine pierderea estimată. */
  derived?: boolean;
  approx_position?: boolean;
}
