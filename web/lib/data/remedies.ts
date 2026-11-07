import "server-only";
import path from "node:path";
import { readFile } from "node:fs/promises";
import { apiUrl, isApiRequestError } from "./api";
import { TIMEOUTS, isSafeSegment } from "./config";
import { demoDir } from "./files";
import { missing, ok, resolveData } from "./source";
import type { Sourced } from "./types";

/**
 * Scara de soluții aleasă de agent pentru fiecare post C (GET /remedies sau plans/<s>/remedies.json):
 * combinația aleasă, costul, P90 înainte și după, de ce nu ajung treptele mai ieftine, oferta de baterii.
 */
export interface RemedyChoice {
  post_id: string;
  work_item_id: string;
  label?: string | null;
  feasible: boolean;
  chosen: string[];
  cost_lei: number;
  p90_before_pu: number;
  p90_after_pu: number;
  why_not_cheaper: string[];
  invest?: boolean;
  battery?: { battery_kwh_total?: number; revenue_lei?: number; payback_years?: number; customers_targeted?: number } | null;
  inverter_trips_avoided?: number | null;
}

function normalize(list: unknown): RemedyChoice[] {
  if (!Array.isArray(list)) return [];
  return list.filter(
    (r): r is RemedyChoice =>
      typeof r === "object" && r !== null && typeof (r as RemedyChoice).work_item_id === "string" && Array.isArray((r as RemedyChoice).chosen),
  );
}

async function fetchApi(scenario: string): Promise<unknown> {
  const url = apiUrl("/remedies", { scenario });
  const res = await fetch(url, { signal: AbortSignal.timeout(TIMEOUTS.getMs), cache: "no-store" });
  if (!res.ok) {
    const err = new Error(`API ${res.status}`) as Error & { status?: number };
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function getRemedies(scenario: string): Promise<Sourced<RemedyChoice[]>> {
  return resolveData<RemedyChoice[]>(
    {
      api: async () => {
        try {
          const list = normalize(await fetchApi(scenario));
          return ok(list, { detail: apiUrl("/remedies", { scenario }) });
        } catch (err) {
          const status = (err as { status?: number }).status;
          if (status === 404 || isApiRequestError(err)) return missing("API-ul nu are /remedies");
          throw err;
        }
      },
      demo: async () => {
        if (!isSafeSegment(scenario)) return missing("scenariu invalid");
        for (const file of [path.join(demoDir(), "plans", scenario, "remedies.json"), path.join(demoDir(), scenario, "remedies.json")]) {
          try {
            return ok(normalize(JSON.parse(await readFile(file, "utf8"))), { detail: file });
          } catch {
            // următorul
          }
        }
        return missing("instantaneul demo nu are remedies.json");
      },
      fixtures: async () => ok<RemedyChoice[]>([], { detail: "fixture-urile nu au scara de soluții" }),
    },
    [],
    { scenario },
  );
}
