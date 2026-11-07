import "server-only";
import { apiHealth, isApiRequestError, isApiUnavailable } from "./api";
import { getConfig, TIMEOUTS } from "./config";
import { hasDemoPlan } from "./files";
import { atRequestTime } from "./request-time";
import type { ApiProbe, DataSource, DataSourceMode, ParseIssue, Sourced } from "./types";

/**
 * Alegerea sursei de date.
 *
 * - `auto`: dacă API-ul răspunde la /health → api; altfel, dacă există plan demo pentru scenariu → demo;
 *   altfel → fixtures.
 * - `api`, `demo`, `fixtures`: forțează sursa, dar nu aruncă niciodată spre pagină. Dacă sursa nu
 *   merge, coboară pe lanțul api → demo → fixtures și explică de ce în `degradedReason`.
 */

const CHAIN: readonly DataSource[] = ["api", "demo", "fixtures"];

const SHOWING: Record<DataSource, string> = {
  api: "datele de la API",
  demo: "instantaneul demo",
  fixtures: "datele de test (fixtures)",
};

// ---------------------------------------------------------------------------------------------
// Verificarea API-ului (GET /health), ținută minte 5 s
// ---------------------------------------------------------------------------------------------

let probeCache: { base: string; at: number; result: ApiProbe } | null = null;
let probeInFlight: { base: string; promise: Promise<ApiProbe> } | null = null;

export async function probeApi(options: { force?: boolean } = {}): Promise<ApiProbe> {
  await atRequestTime();
  const base = getConfig().apiBase;
  if (!options.force) {
    if (probeCache && probeCache.base === base && Date.now() - probeCache.at < TIMEOUTS.probeCacheMs) {
      return probeCache.result;
    }
    if (probeInFlight && probeInFlight.base === base) return probeInFlight.promise;
  }

  const started = performance.now();
  const elapsed = () => Math.round(performance.now() - started);
  const promise = apiHealth()
    .then(
      (health): ApiProbe => ({ ok: true, base, latencyMs: elapsed(), checkedAt: new Date().toISOString(), health }),
      (err: unknown): ApiProbe => ({
        ok: false,
        base,
        latencyMs: elapsed(),
        checkedAt: new Date().toISOString(),
        error: err instanceof Error ? err.message : String(err),
      }),
    )
    .then((result) => {
      probeCache = { base, at: Date.now(), result };
      return result;
    })
    .finally(() => {
      if (probeInFlight?.promise === promise) probeInFlight = null;
    });
  probeInFlight = { base, promise };
  return promise;
}

/** Uită rezultatul verificării (după POST /run sau în teste). */
export function resetProbeCache(): void {
  probeCache = null;
  probeInFlight = null;
}

// ---------------------------------------------------------------------------------------------
// Alegerea sursei pentru un scenariu
// ---------------------------------------------------------------------------------------------

export interface ResolveOptions {
  /** Suprascrie DATA_SOURCE (teste, pagina de diagnostic). */
  mode?: DataSourceMode;
  /** Pornește lanțul de la această sursă (ca toate citirile unei pagini să vină din aceeași sursă). */
  startAt?: DataSource;
}

export interface ResolvedSource {
  source: DataSource;
  /** De ce nu s-a putut folosi o sursă mai bună (gol dacă s-a folosit prima alegere). */
  reasons: string[];
}

/**
 * Alege sursa pentru un scenariu. Fără scenariu (metrici, sănătate), sare peste verificarea
 * planului demo și pornește de la demo când API-ul nu răspunde.
 */
export async function resolveSource(scenario: string | null, mode: DataSourceMode): Promise<ResolvedSource> {
  if (mode === "fixtures") return { source: "fixtures", reasons: [] };
  const reasons: string[] = [];
  if (mode === "auto" || mode === "api") {
    const probe = await probeApi();
    if (probe.ok) return { source: "api", reasons };
    reasons.push("API-ul nu răspunde");
  }
  if (scenario === null || (await hasDemoPlan(scenario))) return { source: "demo", reasons };
  reasons.push(`nu există instantaneu demo pentru scenariul „${scenario}”`);
  return { source: "fixtures", reasons };
}

// ---------------------------------------------------------------------------------------------
// Lanțul de citire
// ---------------------------------------------------------------------------------------------

export type StepOutcome<T> =
  /** Am găsit datele. `showing` înlocuiește descrierea sursei în motiv (de exemplu un fișier din config/). */
  | { kind: "ok"; data: T; detail?: string; parseErrors?: ParseIssue[]; showing?: string }
  /** Nu sunt aici; încerc sursa următoare. */
  | { kind: "missing"; reason: string }
  /** Răspuns sigur: datele nu există (de exemplu 404 pentru o serie). Nu mai caut în alte surse. */
  | { kind: "absent"; detail?: string };

export type Steps<T> = Partial<Record<DataSource, () => Promise<StepOutcome<T>>>>;

export const ok = <T,>(data: T, extra: Omit<Extract<StepOutcome<T>, { kind: "ok" }>, "kind" | "data"> = {}) =>
  ({ kind: "ok", data, ...extra }) as const;
export const missing = (reason: string) => ({ kind: "missing", reason }) as const;
export const absent = (detail?: string) => ({ kind: "absent", detail }) as const;

/** Explică în cuvinte simple de ce o sursă nu a mers. */
export function describeFailure(source: DataSource, err: unknown): string {
  if (source === "api") {
    if (isApiUnavailable(err)) {
      switch (err.kind) {
        case "timeout":
          return "API-ul nu a răspuns la timp";
        case "network":
          return "API-ul nu răspunde";
        case "server":
          return `API-ul a dat o eroare (${err.status ?? "5xx"})`;
        default:
          return "API-ul a trimis date care nu se pot citi";
      }
    }
    if (isApiRequestError(err)) {
      return err.status === 404 ? "API-ul nu are aceste date (404)" : `API-ul a refuzat cererea (${err.status})`;
    }
  }
  const message = err instanceof Error ? err.message : String(err);
  return `nu am putut citi ${SHOWING[source]}: ${message}`;
}

function chainFrom(start: DataSource): DataSource[] {
  return CHAIN.slice(CHAIN.indexOf(start));
}

/**
 * Rulează pașii în ordinea lanțului, începând cu sursa aleasă, și întoarce primul rezultat bun.
 * Nu aruncă: dacă nu merge nimic, întoarce `fallback` cu motivul.
 */
export async function resolveData<T>(
  steps: Steps<T>,
  fallback: T,
  options: ResolveOptions & { scenario?: string | null } = {},
): Promise<Sourced<T>> {
  await atRequestTime();
  const mode = options.mode ?? getConfig().dataSource;
  const reasons: string[] = [];
  let start: DataSource;
  if (options.startAt) {
    start = options.startAt;
  } else {
    const resolved = await resolveSource(options.scenario ?? null, mode);
    start = resolved.source;
    reasons.push(...resolved.reasons);
  }

  let last: DataSource = start;
  for (const source of chainFrom(start)) {
    const step = steps[source];
    if (!step) continue;
    last = source;
    if (source === "api" && options.startAt === "api" && !(await probeApi()).ok) {
      reasons.push("API-ul nu răspunde");
      continue;
    }
    let outcome: StepOutcome<T>;
    try {
      outcome = await step();
    } catch (err) {
      reasons.push(describeFailure(source, err));
      continue;
    }
    const fetchedAt = new Date().toISOString();
    if (outcome.kind === "ok") {
      return {
        data: outcome.data,
        source,
        fetchedAt,
        degradedReason: reasons.length ? `${reasons.join("; ")}; afișez ${outcome.showing ?? SHOWING[source]}` : undefined,
        detail: outcome.detail,
        parseErrors: outcome.parseErrors?.length ? outcome.parseErrors : undefined,
      };
    }
    if (outcome.kind === "absent") {
      return {
        data: fallback,
        source,
        fetchedAt,
        degradedReason: reasons.length ? reasons.join("; ") : undefined,
        detail: outcome.detail,
      };
    }
    reasons.push(outcome.reason);
  }

  return {
    data: fallback,
    source: last,
    fetchedAt: new Date().toISOString(),
    degradedReason: `${reasons.length ? reasons.join("; ") : "nicio sursă disponibilă"}; nu am date de afișat`,
  };
}
