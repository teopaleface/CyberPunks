"use client";
import type { Action, Row } from "./types";
/** Opens review inside the current console. Never prepares or confirms an operation. */
export function requestAssistantAction(action: Action, data: Row, scenario?: string) {
  const selection = typeof data.work_item_id === "string" ? { work_item_id: data.work_item_id }
    : typeof data.case_id === "string" ? { case_id: data.case_id } : undefined;
  window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { action, data, selection, scenario } }));
}
export function requestAssistantContext(workItemId: string, scenario?: string) {
  window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { selection: {work_item_id: workItemId}, scenario } }));
}
