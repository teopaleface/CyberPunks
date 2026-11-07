import "server-only";
import type { AuditRecord, Decision, ModelReport, Plan, Series, WorkItem } from "@/lib/contracts";
import { getConfig, TIMEOUTS } from "./config";
import type {
  ApiHealth,
  MetricsBundle,
  ReviewDecision,
  RunResult,
  ScenarioInfo,
  WorkItemSource,
} from "./types";

/**
 * Clientul pentru API-ul planificatorului (docs/CONTRACTS.md, secțiunea API).
 * Erori:
 * - `ApiUnavailableError`: API-ul nu răspunde, a depășit timpul, a dat 5xx sau a trimis ceva ilizibil;
 *   stratul de date trece atunci la instantaneul demo sau la fixtures.
 * - `ApiRequestError`: API-ul a răspuns, dar a refuzat cererea (4xx, de exemplu 404).
 */

export type ApiFailureKind = "timeout" | "network" | "server" | "invalid_response";

export class ApiUnavailableError extends Error {
  readonly url: string;
  readonly kind: ApiFailureKind;
  readonly status?: number;
  readonly detail?: string;

  constructor(
    message: string,
    info: { url: string; kind: ApiFailureKind; status?: number; detail?: string; cause?: unknown },
  ) {
    super(message, { cause: info.cause });
    this.name = "ApiUnavailableError";
    this.url = info.url;
    this.kind = info.kind;
    this.status = info.status;
    this.detail = info.detail;
  }
}

export class ApiRequestError extends Error {
  readonly url: string;
  readonly status: number;
  readonly detail?: string;

  constructor(message: string, info: { url: string; status: number; detail?: string }) {
    super(message);
    this.name = "ApiRequestError";
    this.url = info.url;
    this.status = info.status;
    this.detail = info.detail;
  }
}

export function isApiUnavailable(err: unknown): err is ApiUnavailableError {
  return err instanceof ApiUnavailableError || (err as Error | null)?.name === "ApiUnavailableError";
}

export function isApiRequestError(err: unknown): err is ApiRequestError {
  return err instanceof ApiRequestError || (err as Error | null)?.name === "ApiRequestError";
}

type Query = Record<string, string | undefined | null>;

export function apiUrl(pathname: string, query?: Query): string {
  const url = new URL(getConfig().apiBase + pathname);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  }
  return url.toString();
}

function isAbortLike(err: unknown): boolean {
  const name = (err as Error | null)?.name;
  return name === "TimeoutError" || name === "AbortError";
}

async function readDetail(res: Response): Promise<string | undefined> {
  try {
    const text = await res.text();
    if (!text) return undefined;
    try {
      const parsed = JSON.parse(text) as { detail?: unknown; error?: unknown; message?: unknown };
      const detail = parsed.detail ?? parsed.error ?? parsed.message;
      if (typeof detail === "string") return detail.slice(0, 500);
    } catch {
      // nu e JSON; păstrăm textul
    }
    return text.slice(0, 500);
  } catch {
    return undefined;
  }
}

async function request<T>(
  method: "GET" | "POST",
  pathname: string,
  options: { query?: Query; body?: unknown; timeoutMs?: number } = {},
): Promise<T> {
  const url = apiUrl(pathname, options.query);
  const timeoutMs = options.timeoutMs ?? TIMEOUTS.getMs;
  const hasBody = options.body !== undefined;
  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers: hasBody
        ? { accept: "application/json", "content-type": "application/json" }
        : { accept: "application/json" },
      body: hasBody ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(timeoutMs),
      cache: "no-store",
    });
  } catch (err) {
    throw isAbortLike(err)
      ? new ApiUnavailableError(`API-ul nu a răspuns în ${timeoutMs} ms`, { url, kind: "timeout", cause: err })
      : new ApiUnavailableError("API-ul nu poate fi contactat", { url, kind: "network", cause: err });
  }

  if (res.status >= 500) {
    const detail = await readDetail(res);
    throw new ApiUnavailableError(`API-ul a răspuns cu eroarea ${res.status}`, {
      url,
      kind: "server",
      status: res.status,
      detail,
    });
  }
  if (!res.ok) {
    const detail = await readDetail(res);
    throw new ApiRequestError(`API-ul a refuzat cererea (${res.status})`, { url, status: res.status, detail });
  }

  try {
    return (await res.json()) as T;
  } catch (err) {
    if (isAbortLike(err)) {
      throw new ApiUnavailableError(`API-ul nu a răspuns în ${timeoutMs} ms`, { url, kind: "timeout", cause: err });
    }
    throw new ApiUnavailableError("API-ul a trimis un răspuns care nu e JSON valid", {
      url,
      kind: "invalid_response",
      cause: err,
    });
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Acceptă atât o listă, cât și `{items: [...]}` sau o cheie asemănătoare. */
function asList<T>(payload: unknown, url: string, keys: string[]): T[] {
  if (Array.isArray(payload)) return payload as T[];
  if (isRecord(payload)) {
    for (const key of keys) {
      if (Array.isArray(payload[key])) return payload[key] as T[];
    }
  }
  throw new ApiUnavailableError("API-ul a trimis o listă într-un format neașteptat", {
    url,
    kind: "invalid_response",
  });
}

// ---------------------------------------------------------------------------------------------
// Rutele API-ului
// ---------------------------------------------------------------------------------------------

export function apiHealth(): Promise<ApiHealth> {
  return request<ApiHealth>("GET", "/health", { timeoutMs: TIMEOUTS.probeMs });
}

export async function apiScenarios(): Promise<ScenarioInfo[]> {
  const url = apiUrl("/scenarios");
  return normalizeScenarios(await request<unknown>("GET", "/scenarios"), url);
}

export function apiPlan(scenario: string): Promise<Plan> {
  return request<Plan>("GET", "/plan", { query: { scenario } });
}

export async function apiWorkItems(scenario: string, source?: WorkItemSource): Promise<WorkItem[]> {
  const query = { scenario, source };
  const payload = await request<unknown>("GET", "/work-items", { query });
  return asList<WorkItem>(payload, apiUrl("/work-items", query), ["items", "work_items", "data"]);
}

/** GET /work-items/{id}: lucrarea plus decizia ei. Acceptă `{work_item, decision}` sau lucrarea cu `decision` lipită. */
export async function apiWorkItem(
  id: string,
  scenario: string,
): Promise<{ workItem: WorkItem; decision: Decision | null }> {
  const pathname = `/work-items/${encodeURIComponent(id)}`;
  const payload = await request<unknown>("GET", pathname, { query: { scenario } });
  if (isRecord(payload) && isRecord(payload.work_item)) {
    return {
      workItem: payload.work_item as unknown as WorkItem,
      decision: isRecord(payload.decision) ? (payload.decision as unknown as Decision) : null,
    };
  }
  if (isRecord(payload) && typeof payload.work_item_id === "string") {
    const { decision, ...rest } = payload;
    return {
      workItem: rest as unknown as WorkItem,
      decision: isRecord(decision) ? (decision as unknown as Decision) : null,
    };
  }
  throw new ApiUnavailableError("API-ul a trimis lucrarea într-un format neașteptat", {
    url: apiUrl(pathname, { scenario }),
    kind: "invalid_response",
  });
}

export function apiSeries(id: string, scenario: string): Promise<Series> {
  return request<Series>("GET", `/series/${encodeURIComponent(id)}`, { query: { scenario } });
}

export async function apiAudit(scenario: string, workItemId?: string): Promise<AuditRecord[]> {
  const query = { scenario, work_item_id: workItemId };
  const payload = await request<unknown>("GET", "/audit", { query });
  return asList<AuditRecord>(payload, apiUrl("/audit", query), ["records", "audit", "items", "data"]);
}

export async function apiMetrics(): Promise<MetricsBundle> {
  const payload = await request<unknown>("GET", "/metrics");
  if (!isRecord(payload)) {
    throw new ApiUnavailableError("API-ul a trimis metricile într-un format neașteptat", {
      url: apiUrl("/metrics"),
      kind: "invalid_response",
    });
  }
  const report = (value: unknown) => (isRecord(value) ? (value as unknown as ModelReport) : null);
  return {
    A: report(payload.A),
    B: report(payload.B),
    C: report(payload.C),
    planner: isRecord(payload.planner) ? payload.planner : null,
  };
}

/** POST /run: rulează agentul cap-coadă (poate dura; timp maxim 120 s). */
export function apiRun(body: { scenario: string; date?: string }): Promise<RunResult> {
  return request<RunResult>("POST", "/run", { body, timeoutMs: TIMEOUTS.runMs });
}

/** POST /review/{id}: decizia omului; întoarce înregistrarea de audit (`actor: human`). */
export function apiReview(
  id: string,
  body: { decision: ReviewDecision; note: string; reviewer: string },
): Promise<AuditRecord> {
  return request<AuditRecord>("POST", `/review/${encodeURIComponent(id)}`, { body });
}

/** Lista de scenarii poate veni ca listă de obiecte, listă de nume sau dicționar (ca în YAML). */
export function normalizeScenarios(payload: unknown, url = "/scenarios"): ScenarioInfo[] {
  const fromEntry = (id: string, value: unknown): ScenarioInfo => {
    const v = isRecord(value) ? value : {};
    return {
      id,
      label_ro: typeof v.label_ro === "string" ? v.label_ro : id,
      date: v.date == null ? null : String(v.date),
      weather: v.weather == null ? null : String(v.weather),
      ...(typeof v.has_plan === "boolean" ? { hasPlan: v.has_plan } : {}),
      ...(typeof v.mode === "string" ? { mode: v.mode } : {}),
    };
  };
  const container = isRecord(payload) && payload.scenarios !== undefined ? payload.scenarios : payload;
  if (Array.isArray(container)) {
    return container.flatMap((entry): ScenarioInfo[] => {
      if (typeof entry === "string") return [fromEntry(entry, {})];
      if (!isRecord(entry)) return [];
      const id = entry.scenario_id ?? entry.id ?? entry.scenario ?? entry.name;
      return typeof id === "string" ? [fromEntry(id, entry)] : [];
    });
  }
  if (isRecord(container)) {
    return Object.entries(container).map(([id, value]) => fromEntry(id, value));
  }
  throw new ApiUnavailableError("API-ul a trimis scenariile într-un format neașteptat", {
    url,
    kind: "invalid_response",
  });
}
