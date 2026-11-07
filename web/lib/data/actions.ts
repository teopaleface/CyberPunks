"use server";

import { revalidatePath } from "next/cache";
import { apiReview, apiRun, isApiRequestError, isApiUnavailable } from "./api";
import { getConfig } from "./config";
import { resetProbeCache } from "./source";
import type { ActionResult, ReviewDecision, RunResult } from "./types";
import type { AuditRecord } from "@/lib/contracts";

/**
 * Acțiunile de server ale consolei. Nu aruncă niciodată spre client: întorc
 * `{ ok: true, ... }` sau `{ ok: false, error }`, cu mesajul în română.
 */

const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;
const WORK_ITEM_RE = /^[ABC]-\d{8}-[A-Za-z0-9_.-]{1,96}$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const DECISIONS: readonly ReviewDecision[] = ["approve", "reject", "defer"];
const MAX_NOTE = 2000;

function explain(err: unknown, what: string): string {
  if (isApiUnavailable(err)) {
    if (err.kind === "timeout") return `${what}: API-ul nu a răspuns la timp. Încearcă din nou.`;
    if (err.kind === "server") {
      return `${what}: API-ul a dat o eroare (${err.status ?? "5xx"})${err.detail ? `: ${err.detail}` : ""}.`;
    }
    if (err.kind === "invalid_response") return `${what}: API-ul a trimis un răspuns care nu se poate citi.`;
    return `${what}: API-ul nu răspunde (${getConfig().apiBase}). Pornește API-ul și încearcă din nou.`;
  }
  if (isApiRequestError(err)) {
    if (err.status === 404) return `${what}: API-ul nu găsește ce am cerut (404).`;
    return `${what}: API-ul a refuzat cererea (${err.status})${err.detail ? `: ${err.detail}` : ""}.`;
  }
  return `${what}: ${err instanceof Error ? err.message : "eroare necunoscută"}.`;
}

/** Pornește agentul cap-coadă (POST /run). */
export async function runAgent(scenario: string, date?: string): Promise<ActionResult<RunResult>> {
  if (typeof scenario !== "string" || !SCENARIO_RE.test(scenario)) {
    return { ok: false, error: "Scenariul nu e valid." };
  }
  if (date !== undefined && (typeof date !== "string" || !DATE_RE.test(date))) {
    return { ok: false, error: "Data trebuie să fie în formatul AAAA-LL-ZZ." };
  }
  try {
    const result = await apiRun(date ? { scenario, date } : { scenario });
    if (!result || typeof result.plan_id !== "string") {
      return { ok: false, error: "Agentul a terminat, dar API-ul nu a trimis ID-ul planului." };
    }
    resetProbeCache();
    revalidatePath("/");
    return { ok: true, plan_id: result.plan_id, timings: result.timings };
  } catch (err) {
    return { ok: false, error: explain(err, "Agentul nu a putut rula") };
  }
}

/** Decizia omului pentru o lucrare (POST /review/{id}). */
export async function submitReview(
  workItemId: string,
  decision: ReviewDecision,
  note: string,
  reviewer: string = process.env.REVIEWER_NAME ?? "dispecer",
): Promise<ActionResult<{ audit: AuditRecord }>> {
  if (typeof workItemId !== "string" || !WORK_ITEM_RE.test(workItemId)) {
    return { ok: false, error: "ID-ul lucrării nu e valid." };
  }
  if (!DECISIONS.includes(decision)) {
    return { ok: false, error: "Decizia trebuie să fie: aprob, resping sau amân." };
  }
  if (typeof note !== "string" || note.length > MAX_NOTE) {
    return { ok: false, error: `Nota poate avea cel mult ${MAX_NOTE} de caractere.` };
  }
  const who = typeof reviewer === "string" && reviewer.trim() ? reviewer.trim().slice(0, 80) : "dispecer";
  try {
    const audit = await apiReview(workItemId, { decision, note: note.trim(), reviewer: who });
    revalidatePath("/");
    revalidatePath(`/lucrari/${workItemId}`);
    return { ok: true, audit };
  } catch (err) {
    return { ok: false, error: explain(err, "Decizia nu a putut fi trimisă") };
  }
}
