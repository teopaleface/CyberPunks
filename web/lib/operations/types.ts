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
export interface Context {
  actor: Actor;
  scenario: string;
  plan: Row;
  connections: Row[];
  work_items: Row[];
  cases: Row[];
  routes?: Row[];
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
export function rows(value: unknown): Row[] {
  return Array.isArray(value)
    ? (value.filter((x) => x && typeof x === "object") as Row[])
    : [];
}
