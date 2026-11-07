import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import YAML from "yaml";
import type { AuditRecord, ModelReport, Plan, Series, WorkItem } from "@/lib/contracts";
import { getConfig, isSafeSegment } from "./config";
import type {
  AreaConfig,
  CrewsConfig,
  Depot,
  Crew,
  MetricsBundle,
  ParseIssue,
  ScenarioInfo,
  WorkItemSource,
} from "./types";

/**
 * Cititoare de fișiere: contracts/fixtures/, instantaneul outputs/demo/, reports/ și config/*.yaml.
 * Nimic de aici nu aruncă pentru un fișier lipsă (întoarce null). Un JSON stricat aruncă
 * `FileFormatError`, pe care stratul de surse îl transformă într-un motiv afișabil.
 */

export const WORK_ITEM_SOURCES: readonly WorkItemSource[] = ["A", "B", "C"];

export interface JsonlResult<T> {
  records: T[];
  errors: ParseIssue[];
}

/** Rezultatul unei citiri, cu fișierele folosite (căi relative la rădăcina repo-ului). */
export interface FileRead<T> {
  data: T;
  files: string[];
}

export class FileFormatError extends Error {
  readonly file: string;
  constructor(file: string, message: string) {
    super(`${file}: ${message}`);
    this.name = "FileFormatError";
    this.file = file;
  }
}

function repoPath(...segments: string[]): string {
  return path.join(getConfig().repoRoot, ...segments);
}

export function relToRepo(file: string): string {
  return path.relative(getConfig().repoRoot, file) || file;
}

function clip(text: string, max = 200): string {
  return text.length > max ? `${text.slice(0, max)}…` : text;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

// ---------------------------------------------------------------------------------------------
// JSON și JSONL
// ---------------------------------------------------------------------------------------------

/**
 * Citește JSONL fără să se oprească la o linie stricată: liniile goale se sar, iar liniile
 * care nu sunt obiecte JSON ajung în `errors` (cu numărul liniei), nu opresc citirea.
 */
export function parseJsonl<T = Record<string, unknown>>(text: string, file = "<text>"): JsonlResult<T> {
  const records: T[] = [];
  const errors: ParseIssue[] = [];
  const lines = text.replace(/^﻿/, "").split(/\r?\n/);
  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    try {
      const value: unknown = JSON.parse(trimmed);
      if (!isRecord(value)) {
        errors.push({ file, line: index + 1, message: "Linia nu conține un obiect JSON.", raw: clip(trimmed) });
        return;
      }
      records.push(value as T);
    } catch (err) {
      errors.push({
        file,
        line: index + 1,
        message: `JSON invalid: ${(err as Error).message}`,
        raw: clip(trimmed),
      });
    }
  });
  return { records, errors };
}

/**
 * Verificare minimă de formă pentru o lucrare, ca o linie incompletă să nu strice harta sau
 * tabelele. Validarea completă o face planificatorul (Pydantic).
 */
export function workItemShapeProblem(value: Record<string, unknown>): string | null {
  if (typeof value.work_item_id !== "string" || !value.work_item_id) return "lipsește work_item_id";
  if (value.source !== "A" && value.source !== "B" && value.source !== "C") return "source nu e A, B sau C";
  const loc = value.location;
  if (!isRecord(loc) || !Number.isFinite(loc.lat) || !Number.isFinite(loc.lon)) {
    return "location.lat/lon lipsesc sau nu sunt numere";
  }
  if (typeof loc.zone_id !== "string") return "location.zone_id lipsește";
  if (typeof value.asset_id !== "string" || typeof value.asset_type !== "string") return "lipsesc asset_id sau asset_type";
  const prediction = value.prediction;
  if (!isRecord(prediction) || !Number.isFinite(prediction.score)) return "prediction.score lipsește";
  if (typeof prediction.prediction_id !== "string" || typeof prediction.model_version !== "string") {
    return "lipsesc prediction_id sau model_version (urmărirea până la model)";
  }
  if (typeof prediction.label !== "string" || typeof prediction.confidence !== "string") return "lipsesc prediction.label sau confidence";
  const impact = value.impact;
  const effort = value.effort;
  const explanation = value.explanation;
  if (!isRecord(impact) || !isRecord(effort) || !isRecord(explanation)) return "lipsesc impact, effort sau explanation";
  if (!Number.isFinite(impact.expected_value_lei)) return "impact.expected_value_lei lipsește";
  if (!Number.isFinite(effort.duration_min) || typeof effort.crew_skill !== "string") return "lipsesc effort.duration_min sau crew_skill";
  if (!Array.isArray(explanation.top_factors) || typeof explanation.summary_ro !== "string") {
    return "lipsesc explanation.top_factors sau summary_ro";
  }
  const dq = value.data_quality;
  if (!isRecord(dq) || typeof dq.synthetic !== "boolean" || !Array.isArray(dq.data_sources)) {
    return "lipsește data_quality (synthetic, data_sources)";
  }
  return null;
}

/** Valori implicite pentru listele opționale, ca afișarea să nu depindă de prezența lor. */
function normalizeWorkItem(record: Record<string, unknown>): WorkItem {
  const explanation = record.explanation as Record<string, unknown>;
  const dq = record.data_quality as Record<string, unknown>;
  return {
    ...record,
    explanation: { ...explanation, similar_cases: Array.isArray(explanation.similar_cases) ? explanation.similar_cases : [] },
    data_quality: { ...dq, input_issues: Array.isArray(dq.input_issues) ? dq.input_issues : [] },
    extra: isRecord(record.extra) ? record.extra : {},
  } as unknown as WorkItem;
}

/** Împarte înregistrările în lucrări folosibile și probleme (cu numărul de ordine al liniei). */
export function splitWorkItems(records: Record<string, unknown>[], file: string): JsonlResult<WorkItem> {
  const items: WorkItem[] = [];
  const errors: ParseIssue[] = [];
  records.forEach((record, index) => {
    const problem = workItemShapeProblem(record);
    if (problem) {
      errors.push({
        file,
        line: index + 1,
        message: `Lucrare incompletă: ${problem}.`,
        raw: clip(JSON.stringify(record)),
      });
    } else {
      items.push(normalizeWorkItem(record));
    }
  });
  return { records: items, errors };
}

function isMissingFileError(err: unknown): boolean {
  const code = (err as NodeJS.ErrnoException | null)?.code;
  return code === "ENOENT" || code === "ENOTDIR";
}

async function readTextIfExists(file: string): Promise<string | null> {
  try {
    return await readFile(file, "utf8");
  } catch (err) {
    if (isMissingFileError(err)) return null;
    throw err;
  }
}

async function readJson<T>(file: string): Promise<T | null> {
  const text = await readTextIfExists(file);
  if (text === null) return null;
  try {
    return JSON.parse(text.replace(/^﻿/, "")) as T;
  } catch (err) {
    throw new FileFormatError(relToRepo(file), `nu e JSON valid (${(err as Error).message})`);
  }
}

/** Primul fișier JSON care există din listă. */
async function readFirstJson<T>(candidates: string[]): Promise<FileRead<T> | null> {
  for (const file of candidates) {
    const data = await readJson<T>(file);
    if (data !== null) return { data, files: [relToRepo(file)] };
  }
  return null;
}

/** Primul fișier JSONL care există din listă. */
async function readFirstJsonl<T>(candidates: string[]): Promise<FileRead<JsonlResult<T>> | null> {
  for (const file of candidates) {
    const text = await readTextIfExists(file);
    if (text !== null) {
      const rel = relToRepo(file);
      return { data: parseJsonl<T>(text, rel), files: [rel] };
    }
  }
  return null;
}

/** Citește lucrările A, B, C (sau doar sursa cerută) și le unește. Null dacă nu există niciun fișier. */
async function readWorkItemFiles(
  candidatesFor: (source: WorkItemSource) => string[],
  source?: WorkItemSource,
): Promise<FileRead<JsonlResult<WorkItem>> | null> {
  const sources = source ? [source] : WORK_ITEM_SOURCES;
  const records: WorkItem[] = [];
  const errors: ParseIssue[] = [];
  const files: string[] = [];
  for (const src of sources) {
    const read = await readFirstJsonl<Record<string, unknown>>(candidatesFor(src));
    if (!read) continue;
    const file = read.files[0];
    const split = splitWorkItems(read.data.records, file);
    records.push(...split.records);
    errors.push(...read.data.errors, ...split.errors);
    files.push(file);
  }
  return files.length ? { data: { records, errors }, files } : null;
}

// ---------------------------------------------------------------------------------------------
// contracts/fixtures/
// ---------------------------------------------------------------------------------------------

export function fixturesDir(): string {
  return repoPath("contracts", "fixtures");
}

export function readFixturePlan(): Promise<FileRead<Plan> | null> {
  return readFirstJson<Plan>([path.join(fixturesDir(), "plan_example.json")]);
}

export function readFixtureWorkItems(source?: WorkItemSource): Promise<FileRead<JsonlResult<WorkItem>> | null> {
  return readWorkItemFiles((src) => [path.join(fixturesDir(), `work_items_${src}.jsonl`)], source);
}

/** Seria de exemplu pentru o lucrare din fixture-uri (contracts/fixtures/series_<id>.json). */
export function readFixtureSeries(workItemId: string): Promise<FileRead<Series> | null> {
  if (!isSafeSegment(workItemId)) return Promise.resolve(null);
  return readFirstJson<Series>([path.join(fixturesDir(), `series_${workItemId}.json`)]);
}

/** Lucrările greșite intenționat (pentru demo-ul „respinsă la intrare”), ca obiecte brute. */
export async function readFixtureInvalidWorkItems(): Promise<FileRead<JsonlResult<Record<string, unknown>>> | null> {
  return readFirstJsonl<Record<string, unknown>>([path.join(fixturesDir(), "work_items_invalid.jsonl")]);
}

export function readFixtureAudit(): Promise<FileRead<JsonlResult<AuditRecord>> | null> {
  return readFirstJsonl<AuditRecord>([path.join(fixturesDir(), "audit_example.jsonl")]);
}

// ---------------------------------------------------------------------------------------------
// outputs/demo/ (instantaneul demo)
// ---------------------------------------------------------------------------------------------

/** Instantaneul demo: implicit outputs/demo; DEMO_DIR îl poate muta (de exemplu pe outputs/ al unei rulări locale). */
export function demoDir(): string {
  const custom = process.env.DEMO_DIR;
  return custom ? path.resolve(custom) : repoPath("outputs", "demo");
}

export interface DemoCandidates {
  plan: string[];
  audit: string[];
  /** Formatul stabilit în docs/CONTRACTS.md: toate lucrările într-un singur fișier. */
  combinedWorkItems: string[];
  /** Timpii ultimei rulări (Perceive, Estimate, Decide, Act). */
  run: string[];
  /** Lucrările respinse la intrare. */
  quarantine: string[];
  workItems: (source: WorkItemSource) => string[];
  series: (workItemId: string) => string[];
  metrics: (source: WorkItemSource | "planner") => string[];
}

/**
 * Unde căutăm instantaneul demo. Formatul final îl decide firul planificator; până atunci
 * încercăm, în ordine (primul fișier găsit câștigă):
 *   1. outputs/demo/<scenariu>/plan.json, audit.jsonl, work_items/<A|B|C>.jsonl, series/<id>.json
 *   2. oglinda lui outputs/: outputs/demo/plans/<scenariu>/plan.json, work_items/<scenariu>/<A>.jsonl,
 *      series/<scenariu>/<id>.json
 *   3. plat: outputs/demo/plan.json etc., doar dacă planul plat e al scenariului cerut
 *      (`plan.scenario`) sau dacă e cerut scenariul implicit (DEFAULT_SCENARIO)
 * Seriile au și o ultimă variantă: outputs/series/<scenariu>/<id>.json din checkout (ieșirea directă a modelelor).
 * Metricile: outputs/demo/metrics/<A|B|C>.json, apoi reports/<A|B|C>/metrics.json (în git);
 * pentru planificator: outputs/demo/metrics/planner.json, apoi reports/planner/agent_eval.json.
 */
export async function demoCandidates(scenario: string): Promise<DemoCandidates> {
  const base = demoDir();
  const safe = isSafeSegment(scenario);
  const flat = safe && (await flatDemoBelongsTo(scenario));
  const pick = (...groups: [boolean, string[]][]) => groups.flatMap(([enabled, files]) => (enabled ? files : []));

  return {
    plan: pick(
      [safe, [path.join(base, "plans", scenario, "plan.json"), path.join(base, scenario, "plan.json")]],
      [flat, [path.join(base, "plan.json")]],
    ),
    audit: pick(
      [safe, [path.join(base, "plans", scenario, "audit.jsonl"), path.join(base, scenario, "audit.jsonl")]],
      [flat, [path.join(base, "audit.jsonl")]],
    ),
    combinedWorkItems: pick(
      [safe, [path.join(base, "plans", scenario, "work_items.jsonl"), path.join(base, scenario, "work_items.jsonl")]],
      [flat, [path.join(base, "work_items.jsonl")]],
    ),
    run: pick(
      [safe, [path.join(base, "plans", scenario, "run.json"), path.join(base, scenario, "run.json")]],
      [flat, [path.join(base, "run.json")]],
    ),
    quarantine: pick(
      [safe, [path.join(base, "plans", scenario, "quarantine.jsonl"), path.join(base, scenario, "quarantine.jsonl")]],
      [flat, [path.join(base, "quarantine.jsonl")]],
    ),
    workItems: (source) =>
      pick(
        [
          safe,
          [
            path.join(base, scenario, "work_items", `${source}.jsonl`),
            path.join(base, "work_items", scenario, `${source}.jsonl`),
          ],
        ],
        [flat, [path.join(base, "work_items", `${source}.jsonl`)]],
      ),
    series: (workItemId) =>
      isSafeSegment(workItemId)
        ? pick(
            [
              safe,
              [
                path.join(base, scenario, "series", `${workItemId}.json`),
                path.join(base, "series", scenario, `${workItemId}.json`),
              ],
            ],
            [flat, [path.join(base, "series", `${workItemId}.json`)]],
            // ieșirea modelelor din acest checkout (de exemplu seriile bilanțului după `make bilant-predict`),
            // calea din `extra.series_ref`, dacă instantaneul nu are seria
            [safe, [repoPath("outputs", "series", scenario, `${workItemId}.json`)]],
          )
        : [],
    metrics: (source) =>
      source === "planner"
        ? [
            path.join(base, "reports", "planner", "agent_eval.json"),
            path.join(base, "metrics", "planner.json"),
            repoPath("reports", "planner", "agent_eval.json"),
          ]
        : [
            path.join(base, "reports", source, "metrics.json"),
            path.join(base, "metrics", `${source}.json`),
            repoPath("reports", source, "metrics.json"),
          ],
  };
}

async function flatDemoBelongsTo(scenario: string): Promise<boolean> {
  if (scenario === getConfig().defaultScenario) return true;
  try {
    const flatPlan = await readJson<{ scenario?: unknown }>(path.join(demoDir(), "plan.json"));
    return flatPlan !== null && flatPlan.scenario === scenario;
  } catch {
    return false;
  }
}

export async function readDemoPlan(scenario: string): Promise<FileRead<Plan> | null> {
  return readFirstJson<Plan>((await demoCandidates(scenario)).plan);
}

/** Există un plan demo pentru scenariu? (Nu aruncă, chiar dacă fișierul e stricat.) */
export async function hasDemoPlan(scenario: string): Promise<boolean> {
  try {
    return (await readDemoPlan(scenario)) !== null;
  } catch {
    return true; // există, dar e stricat; citirea propriu-zisă va explica de ce
  }
}

export async function readDemoWorkItems(
  scenario: string,
  source?: WorkItemSource,
): Promise<FileRead<JsonlResult<WorkItem>> | null> {
  const candidates = await demoCandidates(scenario);
  const combined = await readFirstJsonl<Record<string, unknown>>(candidates.combinedWorkItems);
  if (combined) {
    const file = combined.files[0];
    const split = splitWorkItems(combined.data.records, file);
    const records = source ? split.records.filter((w) => w.source === source) : split.records;
    return { data: { records, errors: [...combined.data.errors, ...split.errors] }, files: combined.files };
  }
  return readWorkItemFiles(candidates.workItems, source);
}

/** Posturile din instantaneul demo (outputs/demo/plans/<s>/posts.json, aceeași formă ca GET /posts). */
export async function readDemoPosts(scenario: string): Promise<FileRead<unknown> | null> {
  if (!isSafeSegment(scenario)) return null;
  const base = demoDir();
  try {
    return await readFirstJson<unknown>([path.join(base, "plans", scenario, "posts.json"), path.join(base, scenario, "posts.json")]);
  } catch {
    return null;
  }
}

/** Costul energiei pierdute (lei/kWh) din config/economics.yaml, cu comentariul de sursă. */
export async function readLossCost(): Promise<{ value: number; note: string } | null> {
  try {
    const text = await readFile(repoPath("config", "economics.yaml"), "utf8");
    const line = text.split("\n").find((l) => /^\s*loss_cost_lei_per_kwh\s*:/.test(l));
    if (!line) return null;
    const value = Number(line.split(":")[1].split("#")[0].trim());
    const note = line.includes("#") ? line.slice(line.indexOf("#") + 1).trim() : "";
    return Number.isFinite(value) ? { value, note } : null;
  } catch {
    return null;
  }
}

/**
 * Pragurile de culoare ale posturilor, din config/planner.yaml (`posts.yellow_lei_month`, `posts.red_lei_month`),
 * aceleași cu care planificatorul colorează posturile în /posts. Null dacă fișierul sau cheile lipsesc.
 */
export async function readPostThresholds(): Promise<{ yellow: number; red: number } | null> {
  try {
    const text = await readFile(repoPath("config", "planner.yaml"), "utf8");
    const value = (key: string) => {
      const m = new RegExp(`^\\s*${key}\\s*:\\s*([0-9.]+)`, "m").exec(text);
      return m ? Number(m[1]) : Number.NaN;
    };
    const yellow = value("yellow_lei_month");
    const red = value("red_lei_month");
    return Number.isFinite(yellow) && Number.isFinite(red) && yellow < red ? { yellow, red } : null;
  } catch {
    return null;
  }
}

/** Timpii ultimei rulări salvate (outputs/demo/plans/<s>/run.json). Null dacă lipsesc. */
export async function readDemoRun(scenario: string): Promise<FileRead<Record<string, unknown>> | null> {
  try {
    return await readFirstJson<Record<string, unknown>>((await demoCandidates(scenario)).run);
  } catch {
    return null;
  }
}

/** Lucrările respinse la intrare din instantaneul demo, ca obiecte brute. */
export async function readDemoQuarantine(scenario: string): Promise<FileRead<JsonlResult<Record<string, unknown>>> | null> {
  try {
    return await readFirstJsonl<Record<string, unknown>>((await demoCandidates(scenario)).quarantine);
  } catch {
    return null;
  }
}

export async function readDemoAudit(scenario: string): Promise<FileRead<JsonlResult<AuditRecord>> | null> {
  return readFirstJsonl<AuditRecord>((await demoCandidates(scenario)).audit);
}

export async function readDemoSeries(workItemId: string, scenario: string): Promise<FileRead<Series> | null> {
  return readFirstJson<Series>((await demoCandidates(scenario)).series(workItemId));
}

/** Metricile din instantaneul demo sau din reports/. Null dacă nu există niciun raport. */
export async function readDemoMetrics(): Promise<FileRead<MetricsBundle> | null> {
  const candidates = await demoCandidates(getConfig().defaultScenario);
  const files: string[] = [];
  const read = async <T>(list: string[]): Promise<T | null> => {
    const result = await readFirstJson<T>(list);
    if (result) files.push(...result.files);
    return result?.data ?? null;
  };
  const [A, B, C, planner] = await Promise.all([
    read<ModelReport>(candidates.metrics("A")),
    read<ModelReport>(candidates.metrics("B")),
    read<ModelReport>(candidates.metrics("C")),
    read<Record<string, unknown>>(candidates.metrics("planner")),
  ]);
  if (!files.length) return null;
  return { data: { A, B, C, planner }, files: files.sort() };
}

// ---------------------------------------------------------------------------------------------
// config/*.yaml
// ---------------------------------------------------------------------------------------------

async function readYaml(relative: string): Promise<unknown | null> {
  const file = repoPath(...relative.split("/"));
  const text = await readTextIfExists(file);
  if (text === null) return null;
  try {
    return YAML.parse(text);
  } catch (err) {
    throw new FileFormatError(relative, `YAML invalid (${(err as Error).message})`);
  }
}

function toNumber(value: unknown): number | null {
  const n = typeof value === "string" ? Number(value) : value;
  return typeof n === "number" && Number.isFinite(n) ? n : null;
}

export async function readAreaConfig(): Promise<AreaConfig> {
  const raw = await readYaml("config/area.yaml");
  if (raw === null) throw new FileFormatError("config/area.yaml", "fișierul lipsește");
  const doc = isRecord(raw) ? raw : {};
  const depots: Depot[] = (Array.isArray(doc.depots) ? doc.depots : []).flatMap((d): Depot[] => {
    if (!isRecord(d) || typeof d.depot_id !== "string") return [];
    const lat = toNumber(d.lat);
    const lon = toNumber(d.lon);
    if (lat === null || lon === null) return [];
    return [
      {
        depot_id: d.depot_id,
        label_ro: typeof d.label_ro === "string" ? d.label_ro : d.depot_id,
        lat,
        lon,
        region: typeof d.region === "string" ? d.region : undefined,
      },
    ];
  });
  const regions: AreaConfig["regions"] = {};
  if (isRecord(doc.regions)) {
    for (const [id, r] of Object.entries(doc.regions)) {
      if (!isRecord(r)) continue;
      regions[id] = {
        label_ro: typeof r.label_ro === "string" ? r.label_ro : id,
        counties: Array.isArray(r.counties) ? r.counties.map(String) : [],
      };
    }
  }
  const box = isRecord(doc.demo_bbox_bucuresti_ilfov) ? doc.demo_bbox_bucuresti_ilfov : null;
  const bboxValues = box
    ? [toNumber(box.lat_min), toNumber(box.lat_max), toNumber(box.lon_min), toNumber(box.lon_max)]
    : [];
  const bbox =
    bboxValues.length === 4 && bboxValues.every((v) => v !== null)
      ? { lat_min: bboxValues[0]!, lat_max: bboxValues[1]!, lon_min: bboxValues[2]!, lon_max: bboxValues[3]! }
      : null;
  return {
    operator: typeof doc.operator === "string" ? doc.operator : undefined,
    timezone: typeof doc.timezone === "string" ? doc.timezone : undefined,
    regions,
    bbox,
    depots,
  };
}

export async function readCrewsConfig(): Promise<CrewsConfig> {
  const raw = await readYaml("config/crews.yaml");
  if (raw === null) throw new FileFormatError("config/crews.yaml", "fișierul lipsește");
  const doc = isRecord(raw) ? raw : {};
  const crews: Crew[] = (Array.isArray(doc.crews) ? doc.crews : []).flatMap((c): Crew[] => {
    if (!isRecord(c) || typeof c.crew_id !== "string" || typeof c.depot_id !== "string") return [];
    return [
      {
        crew_id: c.crew_id,
        depot_id: c.depot_id,
        skills: Array.isArray(c.skills) ? c.skills.map(String) : [],
        size: toNumber(c.size) ?? 2,
      },
    ];
  });
  const shift = isRecord(doc.shift) && doc.shift.start != null && doc.shift.end != null
    ? { start: String(doc.shift.start), end: String(doc.shift.end) }
    : null;
  return { shift, crews };
}

export async function readScenariosConfig(): Promise<ScenarioInfo[]> {
  const raw = await readYaml("config/scenarios.yaml");
  if (raw === null) throw new FileFormatError("config/scenarios.yaml", "fișierul lipsește");
  const scenarios = isRecord(raw) && isRecord(raw.scenarios) ? raw.scenarios : {};
  return Object.entries(scenarios).map(([id, value]) => {
    const v = isRecord(value) ? value : {};
    return {
      id,
      label_ro: typeof v.label_ro === "string" ? v.label_ro : id,
      date: v.date == null ? null : String(v.date),
      weather: v.weather == null ? null : String(v.weather),
    };
  });
}
