import { SessionExpired } from "@/lib/operations/client";
import {
  text,
  type Action,
  type Context,
  type Proposal,
  type Row,
  type WorkspaceAccount,
} from "@/lib/operations/types";

export interface WorkspaceSelection {
  connection_id?: string;
  work_item_id?: string;
  case_id?: string;
}
export interface WorkspaceRequestedAction {
  action: Action;
  data: Row;
  requestId: string;
}
export const SELECTION_FIELDS = [
  "case_id",
  "work_item_id",
  "connection_id",
] as const;
const COLLECTIONS = {
  case_id: "cases",
  work_item_id: "work_items",
  connection_id: "connections",
} as const;

export function selectionKey(selection?: WorkspaceSelection): string {
  return JSON.stringify(
    SELECTION_FIELDS.map((key) => selection?.[key] ?? null),
  );
}
export function selectionOf(row: Row): WorkspaceSelection {
  // Select the primary entity. Related IDs may not all be exposed in this role's scope.
  for (const key of SELECTION_FIELDS)
    if (text(row[key])) return { [key]: text(row[key]) };
  return {};
}
export function resolveSelection(
  context: Context,
  selection?: WorkspaceSelection,
): Row | null {
  let selected: Row | null = null;
  for (const key of SELECTION_FIELDS) {
    const value = selection?.[key];
    if (value === undefined) continue;
    if (typeof value !== "string" || !value.trim())
      throw new Error(
        "The selected item is invalid. Select it again from the current page.",
      );
    const row = context[COLLECTIONS[key]].find(
      (item) => text(item[key] ?? item.id) === value,
    );
    if (!row)
      throw new Error(
        "The selected item is no longer available in your current scope. Select another item.",
      );
    selected ??= row;
  }
  return selected;
}
export function assertScope(
  context: Context,
  account: WorkspaceAccount,
  scenario: string,
): Context {
  if (
    context.actor.user_id !== account.id ||
    context.actor.role !== account.membership.role ||
    context.actor.organization_id !== account.membership.organization_id ||
    context.actor.crew_id !== account.membership.crew_id
  )
    throw new SessionExpired(
      "The signed-in account or its access changed. Reopen the console.",
    );
  if (context.scenario !== scenario)
    throw new Error(
      "The service returned a different scenario. Refresh before continuing.",
    );
  return context;
}
export function canPrepare(context: Context, action: Action): boolean {
  const role = context.actor.role;
  switch (action) {
    case "create_case":
      return (
        role === "customer" ||
        (role === "dispatcher" && context.actor.permissions.includes(action))
      );
    case "record_verdict":
      return role === "technician";
    case "review_work_item":
    case "approve_plan":
      return (
        role === "dispatcher" && context.actor.permissions.includes(action)
      );
    case "set_availability":
      return role === "customer";
    case "request_human":
      return true;
    default:
      return false;
  }
}
export function validateRequestedAction(
  context: Context,
  request: WorkspaceRequestedAction,
): void {
  if (
    typeof request.requestId !== "string" ||
    !request.requestId.trim() ||
    !canPrepare(context, request.action)
  )
    throw new Error(
      "This action is unavailable for your current account. No action was taken.",
    );
  if (
    !request.data ||
    typeof request.data !== "object" ||
    Array.isArray(request.data)
  )
    throw new Error("The requested form is invalid. No action was taken.");
  const selection: WorkspaceSelection = {};
  for (const key of SELECTION_FIELDS) {
    if (request.data[key] !== undefined && request.data[key] !== "") {
      if (typeof request.data[key] !== "string")
        throw new Error("The requested item is invalid. No action was taken.");
      selection[key] = request.data[key];
    }
  }
  resolveSelection(context, selection);
  if (
    request.data.plan_id !== undefined &&
    request.data.plan_id !== context.plan.plan_id
  )
    throw new Error(
      "This request belongs to a different plan. Select the action again on the current plan.",
    );
}
export function requestAssistant(
  selection: WorkspaceSelection,
  action?: Action,
  data?: Row,
  scenario?: string,
): void {
  window.dispatchEvent(
    new CustomEvent("daybreak:assistant", {
      detail: {
        selection,
        ...(scenario ? { scenario } : {}),
        ...(action ? { action, data: data ?? {} } : {}),
      },
    }),
  );
}
export function readableDate(value: unknown): string {
  const input = text(value);
  if (!input) return "Not available";
  // A time without a date is already a readable planned arrival time.
  if (/^\d{1,2}:\d{2}(:\d{2})?$/.test(input)) return input.slice(0, 5);
  const parsed = new Date(input);
  if (Number.isNaN(parsed.getTime())) return input;
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    ...(!/^\d{4}-\d{2}-\d{2}$/.test(input)
      ? ({ hour: "2-digit", minute: "2-digit" } as const)
      : {}),
  }).format(parsed);
}
export function itemTitle(row: Row, fallback = "Service connection"): string {
  const title = text(
    row.title ?? row.symptom ?? row.summary ?? row.label ?? row.address,
  );
  if (title)
    return title
      .replace(/^Synthetic acceptance test [a-f0-9]+:\s*/i, "")
      .replace(/^Synthetic UI validation:\s*/i, "");
  if (row.work_item_id || row.asset_id) {
    const kind =
      row.asset_type === "meter" || row.source === "A"
        ? "Meter inspection"
        : row.source === "B"
          ? "Connection inspection"
          : row.source === "C"
            ? "Voltage inspection"
            : "Site inspection";
    const location =
      row.location && typeof row.location === "object"
        ? (row.location as Row)
        : {};
    const reference = text(row.asset_id ?? row.post_id ?? location.zone_id);
    return reference ? `${kind} · ${reference}` : kind;
  }
  return text(row.action) ? text(row.action).replaceAll("_", " ") : fallback;
}

/** Opens an incoming intent once. It can only open a form, never save an operation. */
export function openRequestedAction(
  context: Context,
  request: WorkspaceRequestedAction,
  seen: Set<string>,
  open: (action: Action, data: Row) => void,
): boolean {
  if (seen.has(request.requestId)) return false;
  try {
    validateRequestedAction(context, request);
    open(request.action, request.data);
    return true;
  } finally {
    seen.add(request.requestId);
  }
}
export function assertProposalScenario(
  proposal: Proposal,
  scenario: string,
): Proposal {
  if (proposal.scenario !== scenario)
    throw new Error(
      "This draft belongs to a different scenario. Open it on the matching plan.",
    );
  return proposal;
}
