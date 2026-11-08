import { englishText } from "@/lib/english";
import { rows, text, type Context, type Row } from "@/lib/operations/types";
import { itemTitle, readableDate } from "./scope";

export type DashboardStatus = {
  label: string;
  tone: "blue" | "amber" | "grey";
};
const STATUSES: Record<string, DashboardStatus> = {
  awaiting_decision: { label: "Under review", tone: "blue" },
  awaiting_data: { label: "Checking details", tone: "amber" },
  awaiting_plan_approval: { label: "Visit awaiting approval", tone: "amber" },
  intervention_approved: { label: "Visit approved", tone: "blue" },
  verification_after_visit: { label: "Follow-up needed", tone: "amber" },
  access_blocked: { label: "Access needed", tone: "amber" },
  open: { label: "Open", tone: "blue" },
  closed: { label: "Closed", tone: "grey" },
  resolved: { label: "Resolved", tone: "grey" },
  cancelled: { label: "Cancelled", tone: "grey" },
};
export function findingOutcome(item?: Row | null): string {
  const verdict = item?.verdict;
  return verdict && typeof verdict === "object"
    ? text((verdict as Row).outcome)
    : "";
}
export function caseStatus(item: Row): DashboardStatus {
  const outcome = findingOutcome(item);
  if (outcome === "no_access") return STATUSES.access_blocked;
  if (outcome) return STATUSES.verification_after_visit;
  return (
    STATUSES[text(item.status)] ?? { label: "Awaiting update", tone: "grey" }
  );
}
export function isActiveCase(item: Row): boolean {
  return (
    Boolean(findingOutcome(item)) ||
    !["closed", "resolved", "cancelled"].includes(text(item.status))
  );
}
export function dashboardTitle(item: Row, fallback = "Service case"): string {
  return englishText(itemTitle(item, fallback))
    .replace(
      /^(?:Synthetic acceptance test|UI validation)(?:\s+(?:test|case))?(?:\s+[a-f\d-]+)?\s*:\s*/i,
      "",
    )
    .replace(
      /\b[a-f\d]{8}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{4}-[a-f\d]{12}\b/gi,
      (id) => id.slice(0, 8),
    );
}
export function shortCaseReference(item: Row): string {
  const id = text(item.case_id ?? item.id).replace(/^case[-_:]?/i, "");
  return id ? `#${id.slice(0, 8).toUpperCase()}` : "Case";
}
export function newestCases(items: Row[]): Row[] {
  const time = (item: Row) =>
    Date.parse(text(item.created_at ?? item.updated_at)) || 0;
  return [...items].sort((a, b) => time(b) - time(a));
}
export function caseNextStep(item?: Row | null): {
  short: string;
  detail: string;
} {
  if (!item)
    return {
      short: "Report an issue",
      detail: "Report a problem with your connection to start a service case.",
    };
  if (findingOutcome(item) === "no_access" || item.status === "access_blocked")
    return {
      short: "Arrange access",
      detail:
        "Share a time when the technician can access the site. Your case remains open.",
    };
  if (findingOutcome(item) || item.status === "verification_after_visit")
    return {
      short: "Team follow-up",
      detail:
        "A dispatcher needs to review the finding and confirm the next action.",
    };
  if (item.human_requested)
    return {
      short: "Team review",
      detail: "Your request is waiting for a team member to review it.",
    };
  if (item.status === "intervention_approved")
    return {
      short: "Visit planning",
      detail:
        "Your visit is approved. The team still needs to confirm an arrival time.",
    };
  if (!isActiveCase(item))
    return {
      short: "No action due",
      detail: "You can ask the team about this case or report a new problem.",
    };
  if (item.status === "awaiting_data")
    return {
      short: "Details check",
      detail:
        "The team needs to check the available information before deciding on a visit.",
    };
  if (item.status === "awaiting_plan_approval")
    return {
      short: "Visit approval",
      detail: "The dispatcher needs to approve the visit plan.",
    };
  return {
    short: "Team review",
    detail:
      "The dispatcher will review your report and decide whether a visit is needed.",
  };
}
export function workSource(item: Row): string {
  return (
    (
      {
        A: "Meter inspection",
        B: "Connection inspection",
        C: "Voltage inspection",
      } as Record<string, string>
    )[text(item.source)] ?? "Site inspection"
  );
}
export function routeIsApproved(context: Context): boolean {
  return (
    context.next_stop_status === "approved_plan" ||
    context.plan.approved === true ||
    rows(context.plan.approvals).some(
      (approval) =>
        approval.stale === false && approval.crew_id === context.actor.crew_id,
    )
  );
}
export function assignedVisits(context: Context): Row[] {
  const stops = rows(context.routes ?? context.plan.routes)
    .filter(
      (route) =>
        !route.crew_id ||
        route.crew_id === context.actor.crew_id ||
        context.actor.role === "dispatcher",
    )
    .flatMap((route) => rows(route.stops));
  const routeOrder = new Map(stops.map((stop, index) => [text(stop.work_item_id), index]));
  return context.work_items.map<Row>((item) => {
    const stop = stops.find(
      (candidate) => candidate.work_item_id === item.work_item_id,
    );
    return {
      ...item,
      planned_start:
        item.planned_start ?? stop?.eta ?? stop?.arrival ?? stop?.planned_start,
    };
  }).sort((a, b) => (routeOrder.get(text(a.work_item_id)) ?? Number.MAX_SAFE_INTEGER) - (routeOrder.get(text(b.work_item_id)) ?? Number.MAX_SAFE_INTEGER));
}
export function nextApprovedVisit(context: Context, visits: Row[]): Row | null {
  const stop = context.next_stop;
  if (!stop || typeof stop !== "object" || !routeIsApproved(context))
    return null;
  const item = visits.find(
    (visit) => visit.work_item_id === (stop as Row).work_item_id,
  );
  return item
    ? {
        ...item,
        planned_start:
          item.planned_start ??
          (stop as Row).eta ??
          (stop as Row).arrival ??
          (stop as Row).planned_start,
      }
    : null;
}
export function fieldFindingCount(context: Context): number {
  const assigned = new Set(
    context.work_items.map((item) => text(item.work_item_id)),
  );
  const findings = new Set<string>();
  for (const item of [...context.work_items, ...context.cases]) {
    const id = text(item.work_item_id);
    if (id && assigned.has(id) && findingOutcome(item)) findings.add(id);
  }
  for (const event of rows(context.events)) {
    if (event.action !== "record_verdict") continue;
    const linkedCase = context.cases.find(
      (item) => item.case_id === event.case_id,
    );
    const id = text(event.work_item_id ?? linkedCase?.work_item_id);
    if (id && assigned.has(id)) findings.add(id);
  }
  return findings.size;
}
export interface TimelineEntry {
  key: string;
  title: string;
  date: string;
}
export function verifiedTimeline(context: Context, item: Row): TimelineEntry[] {
  const caseIds = new Set(
    [
      text(item.case_id),
      ...context.cases
        .filter(
          (entry) =>
            item.work_item_id && entry.work_item_id === item.work_item_id,
        )
        .map((entry) => text(entry.case_id)),
    ].filter(Boolean),
  );
  const events = [...rows(context.events), ...rows(item.events)].filter(
    (event) =>
      rows(item.events).includes(event) ||
      (text(event.case_id) && caseIds.has(text(event.case_id))) ||
      (item.work_item_id && event.work_item_id === item.work_item_id),
  );
  if (
    item.case_id &&
    item.created_at &&
    !events.some((event) => event.action === "create_case")
  )
    events.push({ action: "create_case", created_at: item.created_at });
  const labels: Record<string, string> = {
    create_case: "Report received",
    set_availability: "Availability shared",
    request_human: "Help requested",
    review_work_item: "Case reviewed",
    approve_plan: "Visit approved",
    record_verdict: "Finding recorded",
  };
  const seen = new Set<string>();
  return events
    .filter((event) => text(event.created_at ?? event.ts))
    .sort(
      (a, b) =>
        (Date.parse(text(a.created_at ?? a.ts)) || 0) -
        (Date.parse(text(b.created_at ?? b.ts)) || 0),
    )
    .flatMap((event) => {
      const date = text(event.created_at ?? event.ts);
      const action = text(event.action ?? event.event_type ?? event.type);
      const key = text(event.event_id) || `${action}-${date}`;
      if (seen.has(key)) return [];
      seen.add(key);
      return [
        {
          key,
          title: labels[action] ?? "Case updated",
          date: readableDate(date),
        },
      ];
    })
    .slice(-3);
}
export function matchesDashboardQuery(item: Row, query: string): boolean {
  const fields = [
    dashboardTitle(item),
    caseStatus(item).label,
    workSource(item),
    item.asset_id,
    item.post_id,
    item.case_id,
    item.work_item_id,
    item.connection_id,
    item.meter_id,
  ];
  return fields.some((value) =>
    text(value).toLowerCase().includes(query.trim().toLowerCase()),
  );
}
