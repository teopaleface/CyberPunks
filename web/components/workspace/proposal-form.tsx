"use client";
import { useId, useState } from "react";
import { CheckCircle2, HelpCircle, LockKeyhole, SearchX, Wrench } from "lucide-react";
import type { Action, Context, Row } from "@/lib/operations/types";
import { rows, text } from "@/lib/operations/types";
import { itemTitle } from "./scope";
import { FindingPhotoInput } from "@/components/operations/finding-photos";
import "./proposal-form.css";

export const ACTION_NAMES: Record<Action, string> = {
  create_case: "Report a problem", record_verdict: "Record a finding", review_work_item: "Review this work",
  approve_plan: "Approve this plan", set_availability: "Share access availability", request_human: "Ask for human review",
};
const FIELDS: Record<Action, string[]> = {
  create_case: ["connection_id", "symptom", "symptom_type"], record_verdict: ["work_item_id", "case_id", "outcome", "note"],
  review_work_item: ["work_item_id", "decision", "note"], approve_plan: ["plan_id", "crew_id", "note"],
  set_availability: ["case_id", "start", "end"], request_human: ["case_id", "connection_id", "reason", "priority"],
};
export const FIELD_LABELS: Record<string, string> = {
  connection_id: "Service connection", symptom: "What happened?", symptom_type: "Problem type", work_item_id: "Assigned work",
  case_id: "Case", outcome: "What did you find?", note: "Notes", decision: "Your decision", plan_id: "Plan", crew_id: "Crew, optional",
  start: "Available from", end: "Available until", reason: "Why do you need help?", priority: "Priority",
};
const OPTIONS: Record<string, [string, string][]> = {
  symptom_type: [["voltage", "Voltage or inverter"], ["meter", "Meter"], ["outage", "Power outage"], ["other", "Other"]],
  outcome: [["confirmed", "Problem confirmed"], ["not_found", "Problem not found"], ["other_problem", "Different problem"], ["no_access", "Could not get access"]],
  decision: [["approve", "Approve"], ["defer", "Defer"], ["reject", "Reject"]], priority: [["normal", "Normal"], ["urgent", "Urgent"]],
};
const OUTCOME_HINTS: Record<string, string> = {
  confirmed: "The predicted issue is present.", not_found: "You could not confirm the predicted issue.",
  other_problem: "You found an issue different from the prediction.", no_access: "Access was blocked. The issue remains unverified.",
};
const OUTCOME_ICONS = { confirmed: CheckCircle2, not_found: SearchX, other_problem: Wrench, no_access: LockKeyhole };
export function fieldValueLabel(key: string, value: unknown): string {
  return OPTIONS[key]?.find(([id]) => id === value)?.[1] ?? text(value);
}
export function ProposalForm({ action, initial, onSubmit, onCancel, busy, context }: {
  action: Action; initial: Row; onSubmit: (action: Action, data: Row) => Promise<void>; onCancel: () => void; busy: boolean; context?: Context;
}) {
  const id = useId();
  const [data, setData] = useState<Row>({ symptom_type: "voltage", outcome: "", decision: "approve", priority: "normal", ...initial });
  const [photoBusy, setPhotoBusy] = useState(false);
  const [changeWork, setChangeWork] = useState(false);
  const correction = action === "review_work_item" && data.is_correction === true;
  const finding = action === "record_verdict";
  const locked = busy || photoBusy;
  const workId = text(data.work_item_id);
  const selectedWork = context?.work_items.find((item) => item.work_item_id === workId);
  const photoIds = Array.isArray(data.photo_ids) ? data.photo_ids.filter((value): value is string => typeof value === "string") : [];
  function change(key: string, value: string) {
    setData((old) => key === "work_item_id" ? { ...old, work_item_id: value, case_id: "", photo_ids: [], photos: [] } : { ...old, [key]: value });
  }
  return <form className={`db-form pf-form${finding ? " pf-finding" : ""}`} onSubmit={(event) => {
    event.preventDefault();
    if (locked || (finding && !data.outcome)) return;
    const submitted: Row = Object.fromEntries(FIELDS[action].filter((key) => text(data[key]).trim()).map((key) => [key, data[key]]));
    if (finding) submitted.photo_ids = photoIds;
    if (correction) submitted.is_correction = true;
    void onSubmit(action, submitted);
  }}>
    <div className="pf-header"><h3>{correction ? "Correct the AI decision" : ACTION_NAMES[action]}</h3>
      <p>{finding ? "Record what you observed. Add photos if they help explain the finding." : correction ? "Choose the right action and explain why. You will review the change before it is saved." : "Review the details before making a change."}</p></div>
    {selectedWork && !changeWork && (finding || correction) ? <div className="pf-work"><span className="pf-work-icon"><Wrench size={19} /></span><div><span>Selected visit</span><strong>{itemTitle(selectedWork, "Assigned visit")}</strong></div><button type="button" disabled={locked} onClick={() => setChangeWork(true)}>Change</button></div> : null}
    <div className="pf-fields">{FIELDS[action].map((key) => {
      if (key === "work_item_id" && selectedWork && !changeWork && (finding || correction)) return null;
      if (finding && key === "case_id") return null;
      if (finding && key === "outcome") return <fieldset className="pf-outcomes" key={key}><legend>What did you find?</legend><div>{OPTIONS.outcome.map(([value, name]) => {
        const Icon = OUTCOME_ICONS[value as keyof typeof OUTCOME_ICONS] ?? HelpCircle;
        return <label key={value} className="pf-outcome" data-selected={data.outcome === value}><input type="radio" name={`${id}-outcome`} value={value} checked={data.outcome === value} required disabled={busy} onChange={() => change("outcome", value)} /><Icon size={18} aria-hidden="true" /><span><strong>{name}</strong><small>{OUTCOME_HINTS[value]}</small></span></label>;
      })}</div></fieldset>;
      const title = correction && key === "note" ? "Why should this decision change?" : key === "case_id" && finding ? "Link a case, optional" : FIELD_LABELS[key];
      return <label key={key} className={`pf-field pf-${key}`}><span>{title}{key === "note" && !correction ? <small>Optional</small> : null}</span>
        {context && ["connection_id", "case_id", "work_item_id", "plan_id", "crew_id"].includes(key) ? <select value={text(data[key])} disabled={locked}
          required={(key === "connection_id" && action === "create_case") || (key === "case_id" && action === "set_availability") || (key === "work_item_id" && ["record_verdict", "review_work_item"].includes(action)) || (key === "plan_id" && action === "approve_plan")}
          onChange={(event) => change(key, event.target.value)}><option value="">{key === "crew_id" ? "All authorized crews" : `Choose ${FIELD_LABELS[key].toLowerCase()}`}</option>
          {referenceOptions(context, key, finding ? workId : undefined).map(([value, title]) => <option key={value} value={value}>{title}</option>)}</select>
        : OPTIONS[key] ? <select value={text(data[key])} disabled={locked} onChange={(event) => change(key, event.target.value)}>{OPTIONS[key].map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select>
        : ["symptom", "note", "reason"].includes(key) ? <textarea value={text(data[key])} disabled={busy} maxLength={2000} required={key !== "note" || correction} minLength={correction ? 3 : undefined} rows={finding || correction ? 5 : 3} placeholder={finding ? "What did you observe? Include anything the next person should know." : correction ? "Explain what the AI missed and why your decision is more appropriate." : "Add the details that will help the team."} onChange={(event) => change(key, event.target.value)} />
        : <input value={text(data[key])} disabled={locked} required={["start", "end"].includes(key)} type={["start", "end"].includes(key) ? "datetime-local" : "text"} onChange={(event) => change(key, event.target.value)} />}
      </label>;
    })}</div>
    {finding ? <FindingPhotoInput key={workId} workItemId={workId} scenario={context?.scenario ?? "demo-vara"} photoIds={photoIds} initialPhotos={data.photos} disabled={busy} onBusy={setPhotoBusy} onChange={(ids) => setData((old) => ({ ...old, photo_ids: ids }))} /> : null}
    {action === "set_availability" ? <p className="db-muted">Times use your device timezone. This requests availability; it does not reserve a visit.</p> : null}
    {finding ? <p className="pf-assurance">A finding records the issue. It does not confirm a repair or close the case.</p> : null}
    <div className="db-actions pf-footer"><button className="db-primary" disabled={locked || (finding && !data.outcome)}>{photoBusy ? "Wait for photos…" : "Review proposal"}</button><button type="button" className="db-button" onClick={onCancel} disabled={busy}>Cancel</button></div>
  </form>;
}
function referenceOptions(context: Context, key: string, workId?: string): [string, string][] {
  if (key === "plan_id") return text(context.plan.plan_id) ? [[text(context.plan.plan_id), `Current plan${text(context.plan.plan_date) ? ` · ${text(context.plan.plan_date)}` : ""}`]] : [];
  if (key === "crew_id") {
    const crews = rows(context.crews ?? context.plan.crews ?? context.routes ?? context.plan.routes);
    return [...new Map(crews.filter((row) => text(row.crew_id)).map((row) => [text(row.crew_id), text(row.name ?? row.label ?? row.crew_name) || `Crew ${text(row.crew_id)}`])).entries()];
  }
  const items = key === "connection_id" ? context.connections : key === "case_id" ? context.cases.filter((item) => !workId || item.work_item_id === workId) : context.work_items;
  return items.map((row) => [text(row[key] ?? row.id), `${itemTitle(row, key === "case_id" ? "Service case" : key === "work_item_id" ? "Assigned visit" : "Service connection")}${key === "case_id" ? ` · #${text(row[key] ?? row.id).slice(0, 8)}` : ""}`]);
}
