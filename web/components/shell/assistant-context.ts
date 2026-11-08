import type { Action, Row } from "@/lib/operations/types";

export interface AssistantSelection {
  case_id?: string;
  work_item_id?: string;
  connection_id?: string;
}

export interface AssistantRequest {
  action: Action;
  data: Row;
  requestId: string;
}

const ACTIONS: readonly Action[] = [
  "create_case", "record_verdict", "review_work_item", "approve_plan",
  "set_availability", "request_human",
];

function object(value: unknown): value is Row {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function assistantScenarioMatches(value: unknown, scenario: string): boolean {
  return object(value) && (value.scenario === undefined || value.scenario === scenario);
}

function identifier(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() && value.length <= 256
    && !/[\u0000-\u001f\u007f]/.test(value) ? value : undefined;
}

/** Selection is context, never an authorization grant or an actor. */
export function assistantSelection(value: unknown): AssistantSelection {
  if (!object(value)) return {};
  const selection: AssistantSelection = {};
  for (const key of ["case_id", "work_item_id", "connection_id"] as const) {
    const id = identifier(value[key]);
    if (id) selection[key] = id;
  }
  return selection;
}

/** Legacy `caz` is a work item, not an operations case UUID. */
export function routeSelection(pathname: string, query: URLSearchParams): AssistantSelection {
  const selection = assistantSelection(Object.fromEntries(
    ["case_id", "work_item_id", "connection_id"].map((key) => [key, query.getAll(key).length === 1 ? query.get(key) : null]),
  ));
  const detail = /^\/lucrari\/([^/]+)\/?$/.exec(pathname);
  if (detail) {
    try {
      const work = identifier(decodeURIComponent(detail[1]));
      if (work) selection.work_item_id = work;
    } catch { /* A malformed URL is not a selection. */ }
  }
  if (!selection.work_item_id) {
    const key = pathname === "/coada" ? "caz" : "lucrare";
    if (query.getAll(key).length === 1) {
      const work = identifier(query.get(key));
      if (work) selection.work_item_id = work;
    }
  }
  return selection;
}

/** A fresh request opens a form only. The server still validates permissions/data. */
export function assistantIntent(value: unknown): {
  selection: AssistantSelection;
  requestedAction?: AssistantRequest;
} | null {
  if (!object(value)) return null;
  const selection = assistantSelection(value.selection);
  if ("action" in value) {
    if (!ACTIONS.includes(value.action as Action) || !object(value.data)) return null;
    return {
      selection,
      requestedAction: { action: value.action as Action, data: value.data, requestId: crypto.randomUUID() },
    };
  }
  return { selection };
}
