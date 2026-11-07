"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ConversationProvider } from "@elevenlabs/react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CircleHelp,
  LogOut,
  RefreshCw,
  Zap,
} from "lucide-react";
import { englishText } from "@/lib/english";
import { api, SessionExpired } from "@/lib/operations/client";
import { conversationHistory } from "@/lib/operations/history";
import {
  label,
  rows,
  text,
  type Action,
  type Command,
  type Context,
  type Message,
  type Proposal,
  type Row,
  type Turn,
  type WorkspaceAccount,
} from "@/lib/operations/types";
import { ACTION_NAMES, ProposalForm } from "./proposal-form";
import { Voice } from "./voice";
import "./workspace.css";
const SCENARIO = "demo-vara";
const TITLE = {
  customer: "How can we help?",
  technician: "Your shift, in order.",
  dispatcher: "The decisions that move work forward.",
};
const INTRO = {
  customer:
    "Report a problem, follow your case and tell us when you are available.",
  technician:
    "Your assigned work and the reasons behind each visit. Record what you find when safely stopped.",
  dispatcher:
    "Review the evidence, make a decision and follow the same case through the field visit.",
};
function id(row: Row): string {
  return text(row.case_id ?? row.work_item_id ?? row.connection_id ?? row.id);
}
function date(value: unknown): string {
  const input = text(value);
  if (!input) return "Not available";
  const parsed = new Date(input);
  return Number.isNaN(parsed.getTime())
    ? input
    : parsed.toLocaleString("en-GB");
}
export function Workspace({ account }: { account: WorkspaceAccount }) {
  return (
    <ConversationProvider>
      <WorkspaceContent account={account} />
    </ConversationProvider>
  );
}
function WorkspaceContent({ account }: { account: WorkspaceAccount }) {
  const role = account.membership.role;
  const [context, setContext] = useState<Context | null>(null);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const history = useRef<Message[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const inFlight = useRef(false);
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [command, setCommand] = useState<Command | null>(null);
  const [form, setForm] = useState<{ action: Action; data: Row } | null>(null);
  const [selected, setSelected] = useState<Row | null>(null);
  const [provider, setProvider] = useState("Not started");
  const [updated, setUpdated] = useState("");
  const [notice, setNotice] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);
  const onError = useCallback((issue: unknown) => {
    if (issue instanceof SessionExpired) {
      setExpired(true);
      setContext(null);
      setSelected(null);
      setMessages([]);
      history.current = [];
      setProposal(null);
      setCommand(null);
      setForm(null);
    }
    setError(
      issue instanceof Error
        ? issue.message
        : "The request could not complete. Please try again.",
    );
  }, []);
  const refresh = useCallback(async () => {
    if (!account.membership.organization_id || expired) return;
    try {
      const next = await api<Context>(
        `operations/context?scenario=${SCENARIO}`,
      );
      if (next.actor.user_id !== account.id || next.actor.role !== role)
        throw new SessionExpired(
          "The signed-in account changed. Reopen the workspace.",
        );
      setContext(next);
      setUpdated(new Date().toLocaleTimeString("en-GB"));
    } catch (issue) {
      onError(issue);
    }
  }, [account.id, account.membership.organization_id, expired, onError, role]);
  useEffect(() => {
    const first = setTimeout(() => {
      void refresh();
    }, 0);
    const interval = setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, 2000);
    return () => {
      clearTimeout(first);
      clearInterval(interval);
    };
  }, [refresh]);
  useEffect(() => {
    messagesEnd.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [messages]);
  useEffect(() => {
    if (
      !command ||
      ["completed", "succeeded", "failed"].includes(command.status) ||
      expired
    )
      return;
    const timer = setInterval(() => {
      void api<Command>(
        `operations/commands/${encodeURIComponent(command.command_id)}`,
      )
        .then(setCommand)
        .catch(onError);
    }, 2000);
    return () => clearInterval(timer);
  }, [command, expired, onError]);
  const append = useCallback((next: Message[]) => {
    history.current = [...history.current, ...next].slice(-40);
    setMessages([...history.current]);
  }, []);
  const turn = useCallback(
    async (input: string): Promise<Turn> => {
      if (expired || inFlight.current)
        throw new Error(
          "Please wait for the current request before speaking or typing again.",
        );
      inFlight.current = true;
      setBusy(true);
      setError("");
      const previous = conversationHistory(history.current);
      append([{ role: "user", content: input }]);
      try {
        const answer = await api<Turn>("conversation/chat", {
          message: input,
          history: previous,
          scenario: SCENARIO,
          ...(selected
            ? {
                selection: {
                  ...(selected.case_id ? { case_id: selected.case_id } : {}),
                  ...(selected.work_item_id
                    ? { work_item_id: selected.work_item_id }
                    : {}),
                  ...(selected.connection_id
                    ? { connection_id: selected.connection_id }
                    : {}),
                },
              }
            : {}),
        });
        if (typeof answer.reply !== "string")
          throw new Error("The conversation service did not return a reply.");
        append([{ role: "assistant", content: answer.reply }]);
        setProvider(answer.provider || "Unknown provider");
        if (answer.proposal) {
          setProposal(answer.proposal);
          setForm(null);
          setCommand(null);
        }
        return answer;
      } catch (issue) {
        onError(issue);
        throw issue;
      } finally {
        inFlight.current = false;
        setBusy(false);
      }
    },
    [append, expired, onError, selected],
  );
  async function prepare(action: Action, data: Row) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const payload: Row = { ...data, idempotency_key: crypto.randomUUID() };
      if (action === "set_availability")
        for (const key of ["start", "end"])
          payload[key] = new Date(text(payload[key])).toISOString();
      setProposal(
        await api<Proposal>("operations/proposals", {
          action,
          data: payload,
          scenario: SCENARIO,
        }),
      );
      setCommand(null);
      setForm(null);
    } catch (issue) {
      onError(issue);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  async function confirm() {
    if (!proposal || inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      const saved = await api<Command>(
        `operations/proposals/${encodeURIComponent(proposal.proposal_id)}/confirm`,
        {},
      );
      setCommand(saved);
      setProposal(null);
      setNotice(
        "The server returned the command below. Its status is the saved result.",
      );
      await refresh();
    } catch (issue) {
      onError(issue);
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  function open(action: Action, data: Row = {}) {
    setForm({ action, data });
    setProposal(null);
    setNotice("");
    setCommand(null);
  }
  async function logout() {
    // Unmounts voice immediately, clears private state, then revokes the cookie on the server.
    setExpired(true);
    setContext(null);
    setSelected(null);
    setMessages([]);
    history.current = [];
    setProposal(null);
    setCommand(null);
    setForm(null);
    try {
      await api("cont/iesire", {});
      window.location.assign(new URL("/intra", window.location.origin).href);
    } catch (issue) {
      onError(issue);
    }
  }
  const cases = context?.cases ?? [];
  const work = context?.work_items ?? [];
  const connections = context?.connections ?? [];
  const current =
    (selected &&
      [...cases, ...work, ...connections].find(
        (row) => id(row) === id(selected),
      )) ||
    selected;
  const source = context?.plan.source ?? context?.source;
  const nextStop =
    context?.next_stop && typeof context.next_stop === "object"
      ? (context.next_stop as Row)
      : null;
  return (
    <main className="db-workspace">
      <header className="db-header">
        <a href="/" className="db-brand">
          <Zap size={24} fill="currentColor" />
          daybreak
        </a>
        <div className="db-account">
          <span className="db-role">{role}</span>
          <span>{account.name || account.email}</span>
          <button
            className="db-icon"
            aria-label="Sign out"
            onClick={() => void logout()}
          >
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <div className="db-page">
        <section className="db-intro">
          <p className="db-eyebrow">
            YOUR{" "}
            {role === "customer"
              ? "SERVICE"
              : role === "technician"
                ? "CREW"
                : "OPERATIONS"}{" "}
            WORKSPACE
          </p>
          <h1>{TITLE[role]}</h1>
          <p>{INTRO[role]}</p>
        </section>
        {expired ? (
          <div className="db-alert" role="alert">
            {error || "Your session ended."} <a href="/intra">Sign in again</a>
          </div>
        ) : (
          <>
            {!account.membership.organization_id && (
              <section className="db-panel">
                <h2>Your connection is not linked yet.</h2>
                <p>
                  Ask your administrator to verify your service connection.
                  Creating an account or changing your profile team does not
                  grant access to operational data.
                </p>
              </section>
            )}
            {account.membership.organization_id && (
              <>
                <div className="db-provenance">
                  <span>
                    <i /> Synthetic demo · Historical scenario, 8 July 2025
                  </span>
                  <span>
                    Source:{" "}
                    {source === "local_run"
                      ? "Local model run"
                      : source === "demo_snapshot"
                        ? "Saved demo, read only"
                        : text(source) || "Waiting for operations service"}{" "}
                    · Plan {text(context?.plan.plan_id) || "unavailable"} ·
                    Updated {updated || "waiting"}
                  </span>
                  <button
                    className="db-icon"
                    aria-label="Refresh workspace"
                    onClick={() => void refresh()}
                  >
                    <RefreshCw size={15} />
                  </button>
                </div>
                {error && (
                  <div className="db-alert" role="alert">
                    {error}
                    <button className="db-button" onClick={() => setError("")}>
                      Dismiss
                    </button>
                  </div>
                )}
                <div className="db-grid">
                  <section className="db-context">
                    {role === "customer" && (
                      <section className="db-panel">
                        <div className="db-section-title">
                          <h2>Your service connection</h2>
                          <span className="db-count">{connections.length}</span>
                        </div>
                        {connections.length ? (
                          connections.map((connection) => (
                            <article
                              className="db-connection"
                              key={id(connection)}
                            >
                              <p className="db-eyebrow">{id(connection)}</p>
                              <h3>
                                {text(
                                  connection.label ??
                                    connection.address ??
                                    connection.post_id,
                                ) || "Verified demo connection"}
                              </h3>
                              <p>
                                {text(
                                  connection.customer_summary ??
                                    connection.summary,
                                ) ||
                                  "Only the connection linked to your verified account is shown."}
                              </p>
                              <button
                                className="db-primary"
                                disabled={busy}
                                onClick={() => {
                                  setSelected(connection);
                                  open("create_case", {
                                    connection_id: id(connection),
                                  });
                                }}
                              >
                                Report a problem <ArrowUpRight size={16} />
                              </button>
                            </article>
                          ))
                        ) : (
                          <p className="db-muted">
                            {context
                              ? "No verified connection is available."
                              : "Loading your connection…"}
                          </p>
                        )}
                      </section>
                    )}
                    {role === "technician" && (
                      <section className="db-panel db-shift">
                        <p className="db-eyebrow">YOUR ASSIGNED ROUTE</p>
                        <h2>Crew {account.membership.crew_id}</h2>
                        <p className="db-badge">
                          {label(context?.next_stop_status) ||
                            "Waiting for approval"}
                        </p>
                        <p>
                          Plan date:{" "}
                          {text(context?.plan.plan_date) ||
                            "Waiting for the plan"}
                        </p>
                        <p className="db-muted">
                          {context?.next_stop_status === "approved_plan"
                            ? "Stops and times come from the approved plan."
                            : "This route is proposed and awaits dispatcher approval."}{" "}
                          Times are planned, with no live GPS position or
                          promise of arrival.
                        </p>
                        {nextStop && (
                          <p>
                            <strong>Next approved stop</strong>
                            <br />
                            {text(nextStop.work_item_id)} · {date(nextStop.eta)}
                          </p>
                        )}
                        {rows(context?.routes ?? context?.plan.routes).map(
                          (route, index) => (
                            <div key={index}>
                              {rows(route.stops).map((stop, i) => (
                                <div className="db-stop" key={i}>
                                  <span>{i + 1}</span>
                                  <div>
                                    {text(
                                      stop.work_item_id ??
                                        stop.post_id ??
                                        stop.asset_id,
                                    )}
                                    <p className="db-muted">
                                      {text(
                                        stop.arrival ??
                                          stop.arrival_time ??
                                          stop.planned_start ??
                                          stop.scheduled_start ??
                                          stop.start_time ??
                                          stop.eta,
                                      )}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          ),
                        )}
                      </section>
                    )}
                    {role === "dispatcher" && (
                      <section className="db-panel db-decision">
                        <p className="db-eyebrow">PLAN & CAPACITY</p>
                        <h2>
                          {work.length} work items. {cases.length} shared cases.
                        </h2>
                        <p>
                          Plan date:{" "}
                          {text(context?.plan.plan_date) || "Not available"}
                        </p>
                        <p className="db-muted">
                          Review the model evidence before approving. Everyone
                          sees the resulting operational state in their own
                          scope.
                        </p>
                        <div className="db-actions">
                          <button
                            className="db-primary"
                            disabled={
                              busy ||
                              !context?.plan.plan_id ||
                              !account.membership.permissions.includes(
                                "approve_plan",
                              )
                            }
                            onClick={() =>
                              open("approve_plan", {
                                plan_id: context?.plan.plan_id,
                              })
                            }
                          >
                            Review plan approval <ArrowRight size={16} />
                          </button>
                          {account.membership.permissions.includes(
                            "view_console",
                          ) && (
                            <a className="db-button" href="/app?console=1">
                              Open detailed console
                            </a>
                          )}
                        </div>
                      </section>
                    )}
                    <section className="db-panel">
                      <div className="db-section-title">
                        <h2>
                          {role === "customer" ? "Your cases" : "Shared cases"}
                        </h2>
                        <span className="db-count">{cases.length}</span>
                      </div>
                      {cases.length ? (
                        cases.map((item) => (
                          <button
                            className={`db-row ${id(current ?? {}) === id(item) ? "is-selected" : ""}`}
                            key={id(item)}
                            onClick={() => setSelected(item)}
                          >
                            <div>
                              <strong>
                                {text(
                                  item.symptom ?? item.summary ?? item.title,
                                ) || "Service case"}
                              </strong>
                              <p>
                                {id(item)} · {text(item.connection_id)}
                              </p>
                            </div>
                            <span className="db-badge">
                              {label(item.status) || "Open"}
                            </span>
                          </button>
                        ))
                      ) : (
                        <p className="db-muted">
                          {context
                            ? "No cases in your scope yet."
                            : "Loading cases…"}
                        </p>
                      )}
                    </section>
                    {role !== "customer" && (
                      <section className="db-panel">
                        <div className="db-section-title">
                          <h2>
                            {role === "technician"
                              ? "Your assigned work"
                              : "Work to review"}
                          </h2>
                          <span className="db-count">{work.length}</span>
                        </div>
                        <div className="db-work-list">
                          {work.map((item) => (
                            <button
                              className={`db-row ${id(current ?? {}) === id(item) ? "is-selected" : ""}`}
                              key={id(item)}
                              onClick={() => setSelected(item)}
                            >
                              <div>
                                <strong>
                                  {text(
                                    item.title ??
                                      item.action ??
                                      item.asset_id ??
                                      item.work_item_id,
                                  )}
                                </strong>
                                <p>
                                  {id(item)} ·{" "}
                                  {text(item.post_id ?? item.crew_id)}
                                </p>
                              </div>
                              <span className="db-badge">
                                {label(item.status ?? item.source)}
                              </span>
                            </button>
                          ))}
                          {context && !work.length && (
                            <p className="db-muted">
                              No assigned work is available in this scope.
                            </p>
                          )}
                        </div>
                      </section>
                    )}
                    {current && (
                      <section className="db-panel db-detail">
                        <p className="db-eyebrow">
                          SELECTED{" "}
                          {current.case_id
                            ? "CASE"
                            : current.work_item_id
                              ? "WORK"
                              : "CONNECTION"}
                        </p>
                        <h2>{id(current)}</h2>
                        {[
                          "symptom",
                          "status",
                          "next_step",
                          "customer_summary",
                          "explanation",
                          "reason",
                          "planned_start",
                          "planned_end",
                          "outcome",
                        ].map((key) =>
                          text(current[key]) ? (
                            <p key={key}>
                              <span className="db-field-label">
                                {label(key)}
                              </span>
                              {label(current[key])}
                            </p>
                          ) : null,
                        )}
                        {role !== "customer" && (
                          <>
                            <Assessment value={current.assessment} />
                            <WorkExplanation value={current.explanation} />
                          </>
                        )}
                        {rows(current.events).map((event, i) => (
                          <p key={i} className="db-event">
                            {date(event.created_at ?? event.ts)} ·{" "}
                            {label(
                              event.event_type ?? event.type ?? event.action,
                            )}{" "}
                            {text(event.summary ?? event.message)}
                          </p>
                        ))}
                        <div className="db-actions">
                          {role === "customer" && Boolean(current.case_id) && (
                            <button
                              className="db-button"
                              disabled={busy}
                              onClick={() =>
                                open("set_availability", {
                                  case_id: current.case_id,
                                })
                              }
                            >
                              Share availability
                            </button>
                          )}
                          {role === "technician" &&
                            Boolean(current.work_item_id) && (
                              <button
                                className="db-primary"
                                disabled={busy}
                                onClick={() =>
                                  open("record_verdict", {
                                    work_item_id: current.work_item_id,
                                    ...(current.case_id
                                      ? { case_id: current.case_id }
                                      : {}),
                                  })
                                }
                              >
                                Record finding
                              </button>
                            )}
                          {role === "dispatcher" &&
                            Boolean(current.work_item_id) &&
                            account.membership.permissions.includes(
                              "review_work_item",
                            ) && (
                              <button
                                className="db-primary"
                                disabled={busy}
                                onClick={() =>
                                  open("review_work_item", {
                                    work_item_id: current.work_item_id,
                                  })
                                }
                              >
                                Review work
                              </button>
                            )}
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() =>
                              open("request_human", {
                                ...(current.case_id
                                  ? { case_id: current.case_id }
                                  : {}),
                                ...(current.connection_id
                                  ? { connection_id: current.connection_id }
                                  : {}),
                              })
                            }
                          >
                            <CircleHelp size={16} /> Ask for help
                          </button>
                        </div>
                      </section>
                    )}
                  </section>
                  <aside className="db-conversation">
                    <section className="db-panel db-chat">
                      <div className="db-section-title">
                        <h2>Daybreak, with you.</h2>
                        <span className="db-badge">
                          {busy ? "Working…" : "Ready"}
                        </span>
                      </div>
                      <p className="db-muted">
                        Ask in English or Romanian. Actions stay as drafts until
                        you press Confirm.
                      </p>
                      <Voice
                        scenario={SCENARIO}
                        turn={turn}
                        onError={onError}
                        disabled={expired || !context}
                      />
                      <div
                        className="db-messages"
                        role="log"
                        aria-label="Conversation"
                        aria-live="polite"
                      >
                        {!messages.length && (
                          <div className="db-welcome">
                            <Zap size={25} />
                            <p>
                              {role === "customer"
                                ? "Tell me what happened at your connection."
                                : role === "technician"
                                  ? "Ask what is next, why it matters, or tell me what you found."
                                  : "Ask what needs a decision or compare the evidence behind two work items."}
                            </p>
                            <button
                              className="db-suggestion"
                              disabled={busy || !context}
                              onClick={() => {
                                void turn(
                                  role === "technician"
                                    ? "What is my next stop and why?"
                                    : role === "dispatcher"
                                      ? "What needs my decision?"
                                      : "What is the status of my case?",
                                ).catch(() => {});
                              }}
                            >
                              Start with an update <ArrowRight size={14} />
                            </button>
                          </div>
                        )}
                        {messages.map((entry, i) => (
                          <div className={`db-message ${entry.role}`} key={i}>
                            <span>
                              {entry.role === "user" ? "You" : "Daybreak"}
                            </span>
                            <p>{entry.content}</p>
                          </div>
                        ))}
                        <div ref={messagesEnd} />
                      </div>
                      <form
                        className="db-compose"
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (!message.trim() || busy) return;
                          const input = message;
                          setMessage("");
                          void turn(input).catch(() => {});
                        }}
                      >
                        <label className="sr-only" htmlFor="daybreak-message">
                          Message Daybreak
                        </label>
                        <textarea
                          id="daybreak-message"
                          placeholder="Type your message…"
                          maxLength={4000}
                          value={message}
                          onChange={(e) => setMessage(e.target.value)}
                          disabled={expired}
                        />
                        <button
                          className="db-primary"
                          disabled={busy || !context || !message.trim()}
                          aria-label="Send message"
                        >
                          <ArrowRight size={18} />
                        </button>
                      </form>
                      <p className="db-provider">
                        Conversation provider: {provider}. Technical estimates
                        come from local energy models when valid evidence is
                        available.
                      </p>
                    </section>
                    {form && (
                      <section className="db-panel">
                        <ProposalForm
                          key={`${form.action}-${JSON.stringify(form.data)}`}
                          action={form.action}
                          initial={form.data}
                          onSubmit={prepare}
                          onCancel={() => setForm(null)}
                          busy={busy}
                        />
                      </section>
                    )}
                    {proposal && (
                      <section
                        className="db-panel db-proposal"
                        aria-label="Action proposal"
                      >
                        <p className="db-eyebrow">REVIEW BEFORE SAVING</p>
                        <h2>{ACTION_NAMES[proposal.action]}</h2>
                        <p>{proposal.summary}</p>
                        <dl>
                          {Object.entries(proposal.data)
                            .filter(
                              ([key]) => !["idempotency_key"].includes(key),
                            )
                            .map(([key, value]) => (
                              <div key={key}>
                                <dt>{label(key)}</dt>
                                <dd>
                                  {typeof value === "object"
                                    ? JSON.stringify(value)
                                    : text(value)}
                                </dd>
                              </div>
                            ))}
                        </dl>
                        <p className="db-muted">
                          Expires {date(proposal.expires_at)}. No change has
                          been saved yet.
                        </p>
                        <div className="db-actions">
                          <button
                            className="db-primary"
                            disabled={busy}
                            onClick={() => void confirm()}
                          >
                            <Check size={17} />
                            Confirm
                          </button>
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() => {
                              setForm({
                                action: proposal.action,
                                data: proposal.data,
                              });
                              setProposal(null);
                            }}
                          >
                            Edit
                          </button>
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() => {
                              setProposal(null);
                              setNotice(
                                "Proposal cancelled. No change was saved.",
                              );
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </section>
                    )}
                    {notice && (
                      <p className="db-notice" role="status">
                        {notice}
                      </p>
                    )}
                    {command && (
                      <section
                        className="db-panel db-result"
                        aria-label="Saved command"
                      >
                        <p className="db-eyebrow">SERVER RESULT</p>
                        <h2>{label(command.status)}</h2>
                        <p>Command {command.command_id}</p>
                        {text(command.completed_at) && (
                          <p className="db-muted">
                            Saved {date(command.completed_at)}
                          </p>
                        )}
                        {command.status === "reconciling" && (
                          <p>
                            Pending verification. Check the saved result before
                            preparing another request.
                          </p>
                        )}
                        {command.result?.case &&
                        typeof command.result.case === "object" ? (
                          <p>
                            Case {text((command.result.case as Row).case_id)} ·{" "}
                            {label((command.result.case as Row).status)}
                          </p>
                        ) : null}
                        {command.result && (
                          <dl>
                            {Object.entries(command.result)
                              .filter(
                                ([, value]) =>
                                  typeof value === "string" ||
                                  typeof value === "number",
                              )
                              .map(([key, value]) => (
                                <div key={key}>
                                  <dt>{label(key)}</dt>
                                  <dd>{text(value)}</dd>
                                </div>
                              ))}
                          </dl>
                        )}
                        <button
                          className="db-button"
                          onClick={() => {
                            void api<Command>(
                              `operations/commands/${encodeURIComponent(command.command_id)}`,
                            )
                              .then(setCommand)
                              .catch(onError);
                          }}
                        >
                          Check saved result
                        </button>
                      </section>
                    )}
                  </aside>
                </div>
              </>
            )}
          </>
        )}
        <footer className="db-footer">
          Daybreak · SmartHack 2026 · Synthetic demo. No outgoing calls, emails
          or WhatsApp messages.
        </footer>
      </div>
    </main>
  );
}

function Assessment({ value }: { value: unknown }) {
  if (!value || typeof value !== "object") return null;
  const data = value as Row;
  return (
    <div className="db-assessment">
      <p className="db-eyebrow">MODEL EVIDENCE</p>
      <p>
        {label(data.status)}
        {text(data.reason) && ` · ${text(data.reason)}`}
      </p>
      <dl>
        {[
          "prediction_id",
          "model_version",
          "source",
          "score",
          "confidence",
          "generated_at",
          "plan_id",
        ]
          .filter((key) => data[key] !== undefined && data[key] !== null)
          .map((key) => (
            <div key={key}>
              <dt>{label(key)}</dt>
              <dd>{text(data[key])}</dd>
            </div>
          ))}
      </dl>
      {rows(data.top_factors ?? data.reasons).map((factor, i) => (
        <p key={i}>
          {text(factor.feature ?? factor.name ?? factor.description)}{" "}
          {text(factor.value ?? factor.contribution)}
        </p>
      ))}
      {Array.isArray(data.limitations) &&
        data.limitations.map((item, i) => (
          <p className="db-muted" key={i}>
            {text(item)}
          </p>
        ))}
    </div>
  );
}

function WorkExplanation({ value }: { value: unknown }) {
  if (!value || typeof value !== "object") return null;
  const explanation = value as Row;
  return (
    <div>
      <h3>Why this work matters</h3>
      <p>{englishText(text(explanation.summary_ro ?? explanation.summary))}</p>
      {rows(explanation.top_factors).map((factor, i) => (
        <p key={i}>
          {englishText(
            text(factor.label_ro ?? factor.description ?? factor.feature),
          )}{" "}
          {text(factor.value)}
        </p>
      ))}
    </div>
  );
}
