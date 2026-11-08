"use client";
import { ArrowRight, History, UserRoundPen } from "lucide-react";
import { rows, text, type Row } from "@/lib/operations/types";
import { readableDate } from "@/components/workspace/scope";
import "./decision-correction.css";

const record = (value: unknown): Row => value && typeof value === "object" && !Array.isArray(value) ? value as Row : {};
export function decisionLabel(value: unknown): string {
  const decision = typeof value === "object" ? text(record(value).decision) : text(value);
  return ({ assigned: "Assigned to a crew", human_review: "Needs human review", deferred: "Deferred", remote_action: "Remote action", notify: "Notify customer", rejected_invalid: "Invalid data", approved: "Approved", approve: "Approve", reject: "Reject", defer: "Defer", rejected: "Rejected", no_action: "No action" } as Record<string, string>)[decision] ?? (decision ? decision.replaceAll("_", " ") : "Not recorded");
}
function DecisionValue({ value }: { value: unknown }) {
  const row = record(value);
  return <><strong>{decisionLabel(value)}</strong>{text(row.crew_id) ? <small>Crew {text(row.crew_id)}</small> : null}{text(row.rule_id) ? <small>Rule {text(row.rule_id)}</small> : null}</>;
}
/** Only server-returned provenance is accepted. Requested action is never shown as the applied planner result. */
export function DecisionComparison({ data, saved = false }: { data: Row; saved?: boolean }) {
  const verified = data.original_ai_decision_status === "verified" && Boolean(data.original_ai_decision);
  return <section className="dc-comparison" aria-label={saved ? "Saved decision correction" : "Proposed decision correction"}>
    <div className="dc-heading"><UserRoundPen size={18} /><h3>{data.is_correction === true ? saved ? "AI decision corrected" : "Your correction" : "Human review"}</h3></div>
    <div className="dc-values"><div><span>Before this change</span><DecisionValue value={data.decision_before} /></div><ArrowRight size={18} aria-hidden="true" /><div><span>{saved ? "Applied by the planner" : "Your requested action"}</span><DecisionValue value={saved ? data.decision_after : data.requested_decision ?? data.decision} /></div></div>
    <details className="dc-original"><summary>Original AI decision</summary>{verified ? <DecisionValue value={data.original_ai_decision} /> : <p>The original AI decision cannot be verified for this historical item.</p>}</details>
    {text(data.reason ?? data.note).trim() ? <div className="dc-reason"><span>Reason</span><p>{text(data.reason ?? data.note)}</p></div> : null}
    {saved ? <p className="dc-meta">{text(data.actor_role) === "dispatcher" ? "Dispatcher" : "Team member"} · {text(data.actor_id).slice(0, 8)} · {readableDate(data.created_at)}</p> : <p className="dc-meta">Confirm asks the planner to apply this action. The resulting assignment is shown after saving.</p>}
  </section>;
}
export function DecisionHistory({ corrections }: { corrections: unknown }) {
  const history = rows(corrections);
  if (!history.length) return null;
  const latest = history.at(-1)!;
  return <section className="dc-history" aria-label="Human decision history"><div className="dc-heading"><History size={18} /><h3>Human decision history <span>{history.length}</span></h3></div>
    <DecisionComparison data={latest} saved />{history.length > 1 ? <details className="dc-older"><summary>Earlier changes ({history.length - 1})</summary>{[...history.slice(0, -1)].reverse().map((item, index) => <DecisionComparison key={text(item.command_id) || index} data={item} saved />)}</details> : null}
    <p className="dc-meta">The model prediction is preserved. Human decisions change the operational plan.</p>
  </section>;
}
