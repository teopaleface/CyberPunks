import type { Actor, Membership } from "./policy";
export type Row = Record<string, unknown>;
export type Action =
  | "create_case"
  | "record_verdict"
  | "review_work_item"
  | "approve_plan"
  | "set_availability"
  | "request_human";
export interface Proposal {
  proposal_id: string;
  action: Action;
  summary: string;
  data: Row;
  expires_at: string;
  [key: string]: unknown;
}
export interface Command {
  command_id: string;
  status: string;
  result?: Row;
  [key: string]: unknown;
}
export interface PendingCommand {
  command_id: string;
  proposal_id: string;
  action: Action;
  status: string;
  created_at: string;
  can_recover: boolean;
  recovery_action:
    "retrieve" | "cancel" | "requires_dispatcher" | "manual_review";
}
export type DraftRequest = Pick<
  Proposal,
  "proposal_id" | "action" | "summary" | "expires_at"
> & {
  scenario?: string;
  created_at?: string;
  requires_confirmation?: boolean;
};
export interface Context {
  actor: Actor;
  scenario: string;
  plan: Row;
  connections: Row[];
  work_items: Row[];
  cases: Row[];
  routes?: Row[];
  pending_commands?: PendingCommand[];
  pending_proposals?: DraftRequest[];
  [key: string]: unknown;
}
export interface Turn {
  reply: string;
  proposal?: Proposal | null;
  provider: string;
  [key: string]: unknown;
}
export interface Message {
  role: "user" | "assistant";
  content: string;
}
export interface WorkspaceAccount {
  id: string;
  email: string;
  name: string | null;
  membership: Membership;
}
export function text(value: unknown): string {
  return typeof value === "string" || typeof value === "number"
    ? String(value)
    : "";
}
export function label(value: unknown): string {
  return text(value).replaceAll("_", " ");
}
export function findingText(row: Row): string {
  const verdict = row.verdict;
  if (!verdict || typeof verdict !== "object" || Array.isArray(verdict))
    return "";
  const outcome = text((verdict as Row).outcome);
  return (
    (
      {
        confirmed: "The reported fault was confirmed. Repair is not confirmed.",
        not_found:
          "The reported fault was not observed during the visit. Follow-up is required.",
        other_problem:
          "A different problem was observed. Follow-up is required.",
        no_access:
          "The technician could not access the site. The case remains open.",
      } as Record<string, string>
    )[outcome] ?? ""
  );
}
export function rows(value: unknown): Row[] {
  return Array.isArray(value)
    ? (value.filter((x) => x && typeof x === "object") as Row[])
    : [];
}
