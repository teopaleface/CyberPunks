import "server-only";
import type { Alert, AuditRecord, Decision, Plan, Series, WorkItem } from "@/lib/contracts";
import {
  apiAudit,
  apiPlan,
  apiScenarios,
  apiSeries,
  apiUrl,
  apiWorkItem,
  apiWorkItems,
  apiMetrics,
  isApiRequestError,
} from "./api";
import { getConfig } from "./config";
import {
  fixturesDir,
  hasDemoPlan,
  readAreaConfig,
  readCrewsConfig,
  readDemoAudit,
  readDemoMetrics,
  readDemoPlan,
  readDemoSeries,
  readDemoWorkItems,
  readFixtureAudit,
  readFixtureInvalidWorkItems,
  readFixturePlan,
  readFixtureWorkItems,
  readScenariosConfig,
  relToRepo,
  splitWorkItems,
} from "./files";
import { atRequestTime } from "./request-time";
import { absent, missing, ok, probeApi, resolveData, resolveSource, type ResolveOptions } from "./source";
import type {
  AreaConfig,
  CrewsConfig,
  HealthView,
  MetricsBundle,
  ParseIssue,
  PlanView,
  ResolvedRoute,
  ScenarioInfo,
  SourceInfo,
  Sourced,
  WorkItemDetail,
  WorkItemSource,
} from "./types";

/**
 * Stratul de date al consolei. Doar pe server (componente server, acțiuni, rute).
 * Componentele client importă tipuri din `@/lib/data/types` și etichete din `@/lib/data/labels`.
 *
 * Fiecare funcție întoarce `{ data, source, fetchedAt, degradedReason?, detail?, parseErrors? }`
 * și nu aruncă niciodată spre pagină.
 *
 * Next 16 + Cache Components: funcțiile marchează singure randarea ca dinamică (`connection()`),
 * dar componenta care le cheamă trebuie să stea într-un `<Suspense>` (sau sub un `loading.tsx`).
 */

export { API_BASE, DATA_SOURCE, DEFAULT_SCENARIO, REPO_ROOT, getConfig } from "./config";
export { probeApi, resetProbeCache, type ResolveOptions } from "./source";
export type * from "./types";

const NO_DEMO = (scenario: string) => `nu există instantaneu demo pentru scenariul „${scenario}”`;

function filesDetail(files: string[]): string {
  return files.join(", ");
}

function byWorkItem(records: AuditRecord[], workItemId?: string): AuditRecord[] {
  return workItemId ? records.filter((r) => r.work_item_id === workItemId) : records;
}

// ---------------------------------------------------------------------------------------------
// Citiri simple
// ---------------------------------------------------------------------------------------------

export function getPlan(scenario: string, options: ResolveOptions = {}): Promise<Sourced<Plan | null>> {
  return resolveData<Plan | null>(
    {
      api: async () => ok(await apiPlan(scenario), { detail: apiUrl("/plan", { scenario }) }),
      demo: async () => {
        const read = await readDemoPlan(scenario);
        return read ? ok(read.data, { detail: filesDetail(read.files) }) : missing(NO_DEMO(scenario));
      },
      fixtures: async () => {
        const read = await readFixturePlan();
        return read
          ? ok(read.data, { detail: filesDetail(read.files) })
          : missing("lipsește contracts/fixtures/plan_example.json");
      },
    },
    null,
    { ...options, scenario },
  );
}

export function getWorkItems(
  scenario: string,
  source?: WorkItemSource,
  options: ResolveOptions = {},
): Promise<Sourced<WorkItem[]>> {
  return resolveData<WorkItem[]>(
    {
      api: async () => {
        const url = apiUrl("/work-items", { scenario, source });
        const split = splitWorkItems((await apiWorkItems(scenario, source)) as unknown as Record<string, unknown>[], url);
        return ok(split.records, { detail: url, parseErrors: split.errors });
      },
      demo: async () => {
        const read = await readDemoWorkItems(scenario, source);
        return read
          ? ok(read.data.records, { detail: filesDetail(read.files), parseErrors: read.data.errors })
          : missing(`nu există lucrări în instantaneul demo pentru „${scenario}”`);
      },
      fixtures: async () => {
        const read = await readFixtureWorkItems(source);
        return read
          ? ok(read.data.records, { detail: filesDetail(read.files), parseErrors: read.data.errors })
          : missing("lipsesc contracts/fixtures/work_items_*.jsonl");
      },
    },
    [],
    { ...options, scenario },
  );
}

export function getAudit(
  scenario: string,
  workItemId?: string,
  options: ResolveOptions = {},
): Promise<Sourced<AuditRecord[]>> {
  return resolveData<AuditRecord[]>(
    {
      api: async () =>
        ok(await apiAudit(scenario, workItemId), {
          detail: apiUrl("/audit", { scenario, work_item_id: workItemId }),
        }),
      demo: async () => {
        const read = await readDemoAudit(scenario);
        return read
          ? ok(byWorkItem(read.data.records, workItemId), {
              detail: filesDetail(read.files),
              parseErrors: read.data.errors,
            })
          : missing(`nu există jurnal de audit în instantaneul demo pentru „${scenario}”`);
      },
      fixtures: async () => {
        const read = await readFixtureAudit();
        return read
          ? ok(byWorkItem(read.data.records, workItemId), {
              detail: filesDetail(read.files),
              parseErrors: read.data.errors,
            })
          : missing("lipsește contracts/fixtures/audit_example.jsonl");
      },
    },
    [],
    { ...options, scenario },
  );
}

/** Seria pentru graficul lucrării. `data: null` dacă nu există (fixtures nu au serii). */
export function getSeries(id: string, scenario: string, options: ResolveOptions = {}): Promise<Sourced<Series | null>> {
  return resolveData<Series | null>(
    {
      api: async () => {
        const url = apiUrl(`/series/${encodeURIComponent(id)}`, { scenario });
        try {
          return ok(await apiSeries(id, scenario), { detail: url });
        } catch (err) {
          if (isApiRequestError(err) && err.status === 404) return absent(url);
          throw err;
        }
      },
      demo: async () => {
        const read = await readDemoSeries(id, scenario);
        return read
          ? ok(read.data, { detail: filesDetail(read.files) })
          : missing(`nu există seria lui ${id} în instantaneul demo`);
      },
      fixtures: async () => absent("contracts/fixtures nu are serii"),
    },
    null,
    { ...options, scenario },
  );
}

/** Metricile modelelor A, B, C și ale planificatorului; `null` pentru fiecare raport care lipsește. */
export function getMetrics(options: ResolveOptions = {}): Promise<Sourced<MetricsBundle>> {
  const empty: MetricsBundle = { A: null, B: null, C: null, planner: null };
  return resolveData<MetricsBundle>(
    {
      api: async () => ok(await apiMetrics(), { detail: apiUrl("/metrics") }),
      demo: async () => {
        const read = await readDemoMetrics();
        return read
          ? ok(read.data, { detail: filesDetail(read.files), showing: "rapoartele din repo" })
          : missing("nu există încă rapoarte de evaluare (reports/<A|B|C>/metrics.json)");
      },
      fixtures: async () => absent("contracts/fixtures nu are metrici"),
    },
    empty,
    { ...options, scenario: null },
  );
}

/** Scenariile, de la API sau din config/scenarios.yaml, cu semn dacă au instantaneu demo. */
export async function getScenarios(options: ResolveOptions = {}): Promise<Sourced<ScenarioInfo[]>> {
  const fromYaml = async () =>
    ok(await readScenariosConfig(), { detail: "config/scenarios.yaml", showing: "lista din config/scenarios.yaml" });
  const result = await resolveData<ScenarioInfo[]>(
    {
      api: async () => ok(await apiScenarios(), { detail: apiUrl("/scenarios") }),
      // Fără API, lista vine din config/scenarios.yaml (fișier local, ca fixtures).
      fixtures: fromYaml,
    },
    [],
    { ...options, scenario: null },
  );
  const withDemo = await Promise.all(
    result.data.map(async (s) => ({ ...s, hasDemo: await hasDemoPlan(s.id) })),
  );
  return { ...result, data: withDemo };
}

export async function getHealth(options: ResolveOptions = {}): Promise<Sourced<HealthView>> {
  await atRequestTime();
  const config = getConfig();
  const mode = options.mode ?? config.dataSource;
  const [api, demoAvailable, fixturesAvailable, resolved] = await Promise.all([
    probeApi(),
    hasDemoPlan(config.defaultScenario),
    readFixturePlan().then(
      (r) => r !== null,
      () => false,
    ),
    resolveSource(config.defaultScenario, mode),
  ]);
  const showing = { api: "datele de la API", demo: "instantaneul demo", fixtures: "datele de test (fixtures)" };
  return {
    data: {
      mode,
      apiBase: config.apiBase,
      repoRoot: config.repoRoot,
      defaultScenario: config.defaultScenario,
      api,
      demoAvailable,
      fixturesAvailable,
      resolvedSource: resolved.source,
    },
    source: resolved.source,
    fetchedAt: new Date().toISOString(),
    degradedReason: resolved.reasons.length
      ? `${resolved.reasons.join("; ")}; afișez ${showing[resolved.source]}`
      : undefined,
    detail: apiUrl("/health"),
  };
}

// ---------------------------------------------------------------------------------------------
// O lucrare, cu decizia și auditul ei
// ---------------------------------------------------------------------------------------------

function alertsFor(plan: Plan | null | undefined, id: string): Alert[] {
  return (plan?.alerts ?? []).filter((a) => a.work_item_ids?.includes(id));
}

function decisionFor(plan: Plan | null | undefined, id: string): Decision | null {
  return plan?.decisions.find((d) => d.work_item_id === id) ?? null;
}

export function getWorkItem(
  id: string,
  scenario: string,
  options: ResolveOptions = {},
): Promise<Sourced<WorkItemDetail | null>> {
  return resolveData<WorkItemDetail | null>(
    {
      api: async () => {
        const url = apiUrl(`/work-items/${encodeURIComponent(id)}`, { scenario });
        let item: Awaited<ReturnType<typeof apiWorkItem>>;
        try {
          item = await apiWorkItem(id, scenario);
        } catch (err) {
          if (isApiRequestError(err) && err.status === 404) return absent(url);
          throw err;
        }
        const [audit, plan] = await Promise.allSettled([apiAudit(scenario, id), apiPlan(scenario)]);
        const planValue = plan.status === "fulfilled" ? plan.value : null;
        return ok(
          {
            workItem: item.workItem,
            decision: item.decision ?? decisionFor(planValue, id),
            audit: audit.status === "fulfilled" ? byWorkItem(audit.value, id) : [],
            alerts: alertsFor(planValue, id),
            invalid: false,
          },
          { detail: url },
        );
      },
      demo: async () => {
        const [items, plan, audit] = await Promise.all([
          readDemoWorkItems(scenario),
          readDemoPlan(scenario),
          readDemoAudit(scenario),
        ]);
        const workItem = items?.data.records.find((w) => w.work_item_id === id);
        if (!workItem) return missing(`lucrarea ${id} nu e în instantaneul demo`);
        return ok(
          {
            workItem,
            decision: decisionFor(plan?.data, id),
            audit: byWorkItem(audit?.data.records ?? [], id),
            alerts: alertsFor(plan?.data, id),
            invalid: false,
          },
          { detail: filesDetail(items?.files ?? []) },
        );
      },
      fixtures: async () => {
        const [items, plan, audit] = await Promise.all([readFixtureWorkItems(), readFixturePlan(), readFixtureAudit()]);
        const workItem = items?.data.records.find((w) => w.work_item_id === id);
        if (workItem) {
          return ok(
            {
              workItem,
              decision: decisionFor(plan?.data, id),
              audit: byWorkItem(audit?.data.records ?? [], id),
              alerts: alertsFor(plan?.data, id),
              invalid: false,
            },
            { detail: filesDetail(items?.files ?? []) },
          );
        }
        const invalid = await readFixtureInvalidWorkItems();
        const raw = invalid?.data.records.find((r) => r.work_item_id === id);
        if (raw) {
          return ok(
            { workItem: raw as unknown as WorkItem, decision: null, audit: [], alerts: [], invalid: true },
            { detail: filesDetail(invalid?.files ?? []) },
          );
        }
        return absent(relToRepo(fixturesDir()));
      },
    },
    null,
    { ...options, scenario },
  );
}

// ---------------------------------------------------------------------------------------------
// Ecranul principal: tot ce trebuie, legat
// ---------------------------------------------------------------------------------------------

function info<T>(result: Sourced<T>): SourceInfo {
  return { source: result.source, degradedReason: result.degradedReason, detail: result.detail };
}

async function safeConfig<T>(read: () => Promise<T>, empty: T, issues: string[]): Promise<T> {
  try {
    return await read();
  } catch (err) {
    issues.push(err instanceof Error ? err.message : String(err));
    return empty;
  }
}

export async function getPlanView(scenario: string, options: ResolveOptions = {}): Promise<Sourced<PlanView | null>> {
  const planResult = await getPlan(scenario, options);
  const plan = planResult.data;
  if (!plan) return { ...planResult, data: null };

  // Restul vine din aceeași sursă ca planul, ca ID-urile să se potrivească.
  const sameSource: ResolveOptions = { ...options, startAt: planResult.source };
  const configIssues: string[] = [];
  const emptyArea: AreaConfig = { regions: {}, bbox: null, depots: [] };
  const emptyCrews: CrewsConfig = { shift: null, crews: [] };
  const [itemsResult, auditResult, area, crewsConfig, invalid] = await Promise.all([
    getWorkItems(scenario, undefined, sameSource),
    getAudit(scenario, undefined, sameSource),
    safeConfig(readAreaConfig, emptyArea, configIssues),
    safeConfig(readCrewsConfig, emptyCrews, configIssues),
    planResult.source === "fixtures"
      ? readFixtureInvalidWorkItems().catch(() => null)
      : Promise.resolve(null),
  ]);

  const workItems = itemsResult.data;
  const workItemsById: Record<string, WorkItem> = {};
  for (const item of workItems) workItemsById[item.work_item_id] = item;

  const decisionsByWorkItemId: Record<string, Decision> = {};
  for (const decision of plan.decisions) decisionsByWorkItemId[decision.work_item_id] = decision;

  const alertsByWorkItemId: Record<string, Alert[]> = {};
  for (const alert of plan.alerts ?? []) {
    for (const id of alert.work_item_ids ?? []) (alertsByWorkItemId[id] ??= []).push(alert);
  }

  const depotsById = new Map(area.depots.map((d) => [d.depot_id, d]));
  const crewsById = new Map(crewsConfig.crews.map((c) => [c.crew_id, c]));
  const unresolved = new Set<string>();

  const routes: ResolvedRoute[] = plan.routes.map((route) => {
    const depot = depotsById.get(route.depot_id) ?? null;
    const stops = [...route.stops]
      .sort((a, b) => a.seq - b.seq)
      .map((stop) => {
        const workItem = workItemsById[stop.work_item_id] ?? null;
        if (!workItem) unresolved.add(stop.work_item_id);
        return {
          ...stop,
          workItem,
          decision: decisionsByWorkItemId[stop.work_item_id] ?? null,
          lat: workItem?.location.lat ?? null,
          lon: workItem?.location.lon ?? null,
          label: workItem?.location.label ?? null,
        };
      });
    const path: [number, number][] = [];
    if (depot) path.push([depot.lon, depot.lat]);
    for (const stop of stops) if (stop.lat !== null && stop.lon !== null) path.push([stop.lon, stop.lat]);
    if (depot && path.length > 1) path.push([depot.lon, depot.lat]);
    return { ...route, stops, depot, crew: crewsById.get(route.crew_id) ?? null, path };
  });

  const unplannedItems = workItems.filter((w) => !decisionsByWorkItemId[w.work_item_id]);

  const parseErrors: ParseIssue[] = [
    ...(planResult.parseErrors ?? []),
    ...(itemsResult.parseErrors ?? []),
    ...(auditResult.parseErrors ?? []),
  ];
  const reasons = [planResult, itemsResult, auditResult]
    .map((r) => r.degradedReason)
    .filter((r, i, all): r is string => Boolean(r) && all.indexOf(r) === i);

  return {
    data: {
      scenario,
      plan,
      workItems,
      workItemsById,
      decisionsByWorkItemId,
      alertsByWorkItemId,
      routes,
      unplannedItems,
      unresolvedStopIds: [...unresolved],
      invalidItems: invalid?.data.records ?? [],
      audit: auditResult.data,
      area,
      depots: area.depots,
      crews: crewsConfig.crews,
      shift: crewsConfig.shift,
      sources: { plan: info(planResult), workItems: info(itemsResult), audit: info(auditResult) },
      configIssues,
    },
    source: planResult.source,
    fetchedAt: planResult.fetchedAt,
    degradedReason: reasons.length ? reasons.join(" · ") : undefined,
    detail: planResult.detail,
    parseErrors: parseErrors.length ? parseErrors : undefined,
  };
}
