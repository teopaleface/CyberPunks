"use server";
import { consoleDenied } from "@/lib/server/operations";
import type { ActionResult, ReviewDecision, RunResult } from "./types";
import type { AuditRecord } from "@/lib/contracts";
const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;
const WORK_ITEM_RE = /^[ABC]-\d{8}-[A-Za-z0-9_.-]{1,96}$/;
export async function runAgent(scenario: string, date?: string): Promise<ActionResult<RunResult>> {
  void [scenario, date];
  const denied = await consoleDenied();
  return { ok: false, error: denied ? "This action requires an authorized dispatcher account." : "Open the shared workspace to prepare, review and confirm this action." };
}

/** Decizia omului pentru o lucrare (POST /review/{id}). */
export async function submitReview(
  workItemId: string,
  decision: ReviewDecision,
  note: string,
  scenario?: string,
  reviewer: string = process.env.REVIEWER_NAME ?? "dispecer",
): Promise<ActionResult<{ audit: AuditRecord }>> {
  void [workItemId, decision, note, scenario, reviewer];
  const denied = await consoleDenied();
  return { ok: false, error: denied ? "This action requires an authorized dispatcher account." : "Open the shared workspace to prepare, review and confirm this action." };
}

/**
 * Compatibilitate cu butonul vechi. Aprobarea se face în workspace, prin propunerea comună.
 */
export async function approvePlan(
  scenario: string,
  planId: string,
  note = "",
): Promise<ActionResult<{ local: boolean; at: string; audit?: AuditRecord }>> {
  void [scenario, planId, note];
  const denied = await consoleDenied();
  return { ok: false, error: denied ? "This action requires an authorized dispatcher account." : "Open the shared workspace to prepare, review and confirm this action." };
}

/** Lucrarea întreagă (factori, cazuri similare, extra), pentru detaliul de pe ecranul planului. */
export async function loadWorkItemDetail(
  workItemId: string,
  scenario: string,
): Promise<ActionResult<{ workItem: import("@/lib/contracts").WorkItem }>> {
  const denied = await consoleDenied();
  if (denied) return { ok: false, error: "This detail requires an authorized dispatcher account." };
  if (typeof workItemId !== "string" || !WORK_ITEM_RE.test(workItemId)) return { ok: false, error: "ID-ul lucrării nu e valid." };
  if (typeof scenario !== "string" || !SCENARIO_RE.test(scenario)) return { ok: false, error: "Scenariul nu e valid." };
  const { getWorkItem } = await import("./index");
  const r = await getWorkItem(workItemId, scenario);
  if (!r.data) return { ok: false, error: `Lucrarea ${workItemId} nu s-a găsit.` };
  return { ok: true, workItem: r.data.workItem };
}
