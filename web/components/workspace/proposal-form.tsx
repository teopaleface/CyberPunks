"use client";
import { useState } from "react";
import type { Action, Row } from "@/lib/operations/types";
import { text } from "@/lib/operations/types";
export const ACTION_NAMES: Record<Action, string> = {
  create_case: "Report a problem",
  record_verdict: "Record a finding",
  review_work_item: "Review this work",
  approve_plan: "Approve this plan",
  set_availability: "Share access availability",
  request_human: "Ask for human review",
};
const FIELDS: Record<Action, string[]> = {
  create_case: ["connection_id", "symptom", "symptom_type"],
  record_verdict: ["work_item_id", "case_id", "outcome", "note"],
  review_work_item: ["work_item_id", "decision", "note"],
  approve_plan: ["plan_id", "crew_id", "note"],
  set_availability: ["case_id", "start", "end"],
  request_human: ["case_id", "connection_id", "reason", "priority"],
};
const LABELS: Record<string, string> = {
  connection_id: "Service connection",
  symptom: "What happened?",
  symptom_type: "Problem type",
  work_item_id: "Assigned work",
  case_id: "Case",
  outcome: "What did you find?",
  note: "Notes",
  decision: "Decision",
  plan_id: "Plan",
  crew_id: "Crew, optional",
  start: "Available from",
  end: "Available until",
  reason: "Why do you need help?",
  priority: "Priority",
};
const OPTIONS: Record<string, [string, string][]> = {
  symptom_type: [
    ["voltage", "Voltage or inverter"],
    ["meter", "Meter"],
    ["outage", "Power outage"],
    ["other", "Other"],
  ],
  outcome: [
    ["confirmed", "Predicted problem confirmed"],
    ["not_found", "Predicted problem not found"],
    ["other_problem", "A different problem"],
    ["no_access", "Could not get access"],
  ],
  decision: [
    ["approve", "Approve"],
    ["defer", "Defer"],
    ["reject", "Reject"],
  ],
  priority: [
    ["normal", "Normal"],
    ["urgent", "Urgent"],
  ],
};
export function ProposalForm({
  action,
  initial,
  onSubmit,
  onCancel,
  busy,
}: {
  action: Action;
  initial: Row;
  onSubmit: (action: Action, data: Row) => Promise<void>;
  onCancel: () => void;
  busy: boolean;
}) {
  const [data, setData] = useState<Row>({
    symptom_type: "voltage",
    outcome: "confirmed",
    decision: "approve",
    priority: "normal",
    ...initial,
  });
  function change(key: string, value: string) {
    setData((old) => ({ ...old, [key]: value }));
  }
  return (
    <form
      className="db-form"
      onSubmit={(e) => {
        e.preventDefault();
        const submitted = Object.fromEntries(
          FIELDS[action]
            .filter((k) => text(data[k]).trim())
            .map((k) => [k, data[k]]),
        );
        void onSubmit(action, submitted);
      }}
    >
      <h3>{ACTION_NAMES[action]}</h3>
      {FIELDS[action].map((key) => (
        <label key={key}>
          {LABELS[key]}
          {OPTIONS[key] ? (
            <select
              value={text(data[key])}
              onChange={(e) => change(key, e.target.value)}
            >
              {OPTIONS[key].map(([value, name]) => (
                <option value={value} key={value}>
                  {name}
                </option>
              ))}
            </select>
          ) : ["symptom", "note", "reason"].includes(key) ? (
            <textarea
              value={text(data[key])}
              maxLength={2000}
              required={key !== "note"}
              onChange={(e) => change(key, e.target.value)}
            />
          ) : (
            <input
              value={text(data[key])}
              type={["start", "end"].includes(key) ? "datetime-local" : "text"}
              onChange={(e) => change(key, e.target.value)}
            />
          )}
        </label>
      ))}
      {action === "set_availability" && (
        <p className="db-muted">
          Times use your device timezone. This requests access availability. It
          does not reserve a visit.
        </p>
      )}
      {action === "record_verdict" && (
        <p className="db-muted">
          A confirmed finding records the problem. It does not mark it repaired.
        </p>
      )}
      <div className="db-actions">
        <button className="db-primary" disabled={busy}>
          Review proposal
        </button>
        <button
          type="button"
          className="db-button"
          onClick={onCancel}
          disabled={busy}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
