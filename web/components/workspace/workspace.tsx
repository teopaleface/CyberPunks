"use client";
import { useCallback, useEffect, useId, useRef, useState } from "react";
import { ConversationProvider } from "@elevenlabs/react";
import { ArrowRight, Check, X } from "lucide-react";
import { api, SessionExpired } from "@/lib/operations/client";
import { loadLinkedProposal } from "@/lib/operations/linked-proposal";
import { proposalSignInPath } from "@/lib/operations/proposal-link";
import { conversationHistory } from "@/lib/operations/history";
import {
  label,
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
import { DraftRequests } from "./draft-requests";
import { PendingCommands } from "./pending-commands";
import { recoveryControl } from "@/lib/operations/recovery";
import { ACTION_NAMES, ProposalForm } from "./proposal-form";
import { RoleOverview } from "./role-overview";
import {
  assertProposalScenario,
  assertScope,
  canPrepare,
  itemTitle,
  readableDate,
  openRequestedAction,
  resolveSelection,
  selectionKey,
  validateRequestedAction,
  type WorkspaceRequestedAction,
  type WorkspaceSelection,
} from "./scope";
import { Voice } from "./voice";
import "./workspace.css";
export type { WorkspaceAccount } from "@/lib/operations/types";
export type { WorkspaceRequestedAction, WorkspaceSelection } from "./scope";
export interface WorkspaceProps {
  account: WorkspaceAccount;
  presentation?: "page" | "assistant" | "role";
  initialSelection?: WorkspaceSelection;
  requestedAction?: WorkspaceRequestedAction;
  scenario?: string;
  linkedProposalId?: string | null;
  initialError?: string;
}
export function Workspace(props: WorkspaceProps) {
  // Remount private state and voice when the account, scope or scenario changes.
  const key = JSON.stringify([
    props.account.id,
    props.account.membership,
    props.scenario ?? "demo-vara",
  ]);
  const content = <WorkspaceContent key={key} {...props} />;
  return props.presentation === "role" ? (
    content
  ) : (
    <ConversationProvider key={key}>{content}</ConversationProvider>
  );
}
function WorkspaceContent({
  account,
  linkedProposalId,
  initialError,
  initialSelection,
  requestedAction,
  scenario = "demo-vara",
  presentation = "page",
}: WorkspaceProps) {
  const role = account.membership.role;
  const messageId = useId();
  const [validated, setValidated] = useState<{
    key: string;
    selection?: WorkspaceSelection;
  } | null>(null);
  const [selectionIssue, setSelectionIssue] = useState<{
    key: string;
    message: string;
  } | null>(null);
  const [clearedSelection, setClearedSelection] = useState<{
    value?: WorkspaceSelection;
  } | null>(null);
  const effectiveSelection =
    clearedSelection && clearedSelection.value === initialSelection
      ? undefined
      : initialSelection;
  const currentKey = selectionKey(effectiveSelection);
  const selectionPending = validated?.key !== currentKey;
  const appliedRequests = useRef(new Set<string>());
  const scopeSequence = useRef(0);
  const previousSelectionKey = useRef(currentKey);
  const [context, setContext] = useState<Context | null>(null);
  const [error, setError] = useState(initialError ?? "");
  const [proposalLoading, setProposalLoading] = useState(
    Boolean(linkedProposalId),
  );
  const [expired, setExpired] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const history = useRef<Message[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(Boolean(linkedProposalId));
  const inFlight = useRef(Boolean(linkedProposalId));
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [command, setCommand] = useState<Command | null>(null);
  const [form, setForm] = useState<{ action: Action; data: Row } | null>(null);
  const [provider, setProvider] = useState("Not started");
  const [updated, setUpdated] = useState("");
  const [notice, setNotice] = useState("");
  const messagesEnd = useRef<HTMLDivElement>(null);
  const proposalCard = useRef<HTMLElement>(null);
  const open = useCallback((action: Action, data: Row = {}) => {
    setForm({ action, data });
    setProposal(null);
    setNotice("");
    setCommand(null);
  }, []);
  const onError = useCallback((issue: unknown) => {
    if (issue instanceof SessionExpired) {
      setExpired(true);
      setContext(null);
      setValidated(null);
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
  useEffect(() => {
    if (!linkedProposalId || expired || !account.membership.organization_id)
      return;
    let active = true;
    const timer = setTimeout(() => {
      void loadLinkedProposal(linkedProposalId, (path) => api<Proposal>(path))
        .then((saved) => {
          if (!active) return;
          setProposal(assertProposalScenario(saved, scenario));
          setNotice(
            "Linked proposal loaded. Review it below. Nothing has been confirmed.",
          );
        })
        .catch((issue) => {
          if (active) onError(issue);
        })
        .finally(() => {
          if (active) {
            setProposalLoading(false);
            setBusy(false);
            inFlight.current = false;
          }
        });
    }, 0);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [
    linkedProposalId,
    expired,
    account.membership.organization_id,
    onError,
    scenario,
  ]);
  useEffect(() => {
    if (proposal?.proposal_id)
      proposalCard.current?.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
  }, [proposal?.proposal_id]);
  const loadScope = useCallback(async () => {
    if (!account.membership.organization_id)
      throw new Error("Your account is not linked to operational data.");
    const sequence = ++scopeSequence.current;
    const next = assertScope(
      await api<Context>(
        `operations/context?scenario=${encodeURIComponent(scenario)}`,
      ),
      account,
      scenario,
    );
    if (sequence === scopeSequence.current) setContext(next);
    return next;
  }, [account, scenario]);
  const refresh = useCallback(async (): Promise<Context | null> => {
    if (!account.membership.organization_id || expired) return null;
    try {
      const next = await loadScope();
      setUpdated(new Date().toLocaleTimeString("en-GB"));
      return next;
    } catch (issue) {
      onError(issue);
      return null;
    }
  }, [account.membership.organization_id, expired, loadScope, onError]);
  useEffect(() => {
    if (expired || !account.membership.organization_id) return;
    let active = true;
    const timer = setTimeout(() => {
      if (previousSelectionKey.current !== currentKey) {
        previousSelectionKey.current = currentKey;
        setForm(null);
        setProposal(null);
        setCommand(null);
        setNotice("");
      }
      void loadScope()
        .then((next) => {
          resolveSelection(next, effectiveSelection);
          if (active) {
            setValidated({ key: currentKey, selection: effectiveSelection });
            setSelectionIssue(null);
          }
        })
        .catch((issue) => {
          if (!active) return;
          setValidated({ key: currentKey });
          setSelectionIssue({
            key: currentKey,
            message:
              issue instanceof Error
                ? issue.message
                : "The selection could not be checked.",
          });
          onError(issue);
        });
    }, 0);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [
    currentKey,
    effectiveSelection,
    expired,
    account.membership.organization_id,
    loadScope,
    onError,
  ]);
  useEffect(() => {
    if (
      !requestedAction ||
      presentation === "role" ||
      expired ||
      busy ||
      selectionPending ||
      appliedRequests.current.has(requestedAction.requestId)
    )
      return;
    let active = true;
    const timer = setTimeout(() => {
      setForm(null);
      setProposal(null);
      setCommand(null);
      setError("");
      void loadScope()
        .then((next) => {
          if (!active) return;
          // Intent only: validation and opening the editable form never POST or confirm.
          resolveSelection(next, effectiveSelection);
          openRequestedAction(
            next,
            requestedAction,
            appliedRequests.current,
            open,
          );
        })
        .catch((issue) => {
          if (!active) return;
          appliedRequests.current.add(requestedAction.requestId);
          onError(issue);
        });
    }, 0);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [
    requestedAction,
    presentation,
    expired,
    busy,
    selectionPending,
    effectiveSelection,
    loadScope,
    onError,
    open,
  ]);
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
  const append = useCallback((next: Message[]) => {
    history.current = [...history.current, ...next].slice(-40);
    setMessages([...history.current]);
  }, []);
  const { current, selectionError } = (() => {
    const issue =
      selectionIssue?.key === currentKey ? selectionIssue.message : "";
    if (selectionPending || !context || issue)
      return { current: null, selectionError: issue };
    try {
      return {
        current: resolveSelection(context, validated?.selection),
        selectionError: "",
      };
    } catch (error) {
      return {
        current: null,
        selectionError:
          error instanceof Error ? error.message : "Selection unavailable.",
      };
    }
  })();
  async function turn(input: string): Promise<Turn> {
    if (expired || inFlight.current || selectionPending || selectionError)
      throw new Error(
        "Please wait for the current request before speaking or typing again.",
      );
    inFlight.current = true;
    setBusy(true);
    setError("");
    const previous = conversationHistory(history.current);
    append([{ role: "user", content: input }]);
    try {
      const fresh = await loadScope();
      resolveSelection(fresh, validated?.selection);
      const answer = await api<Turn>("conversation/chat", {
        message: input,
        history: previous,
        scenario,
        ...(validated?.selection ? { selection: validated.selection } : {}),
      });
      if (typeof answer.reply !== "string")
        throw new Error("The conversation service did not return a reply.");
      append([{ role: "assistant", content: answer.reply }]);
      setProvider(answer.provider || "Unknown provider");
      if (answer.proposal) {
        setProposal(assertProposalScenario(answer.proposal, scenario));
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
  }
  async function openDraft(proposalId: string) {
    if (expired || inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setProposalLoading(true);
    setError("");
    try {
      const saved = await loadLinkedProposal(proposalId, (path) =>
        api<Proposal>(path),
      );
      setProposal(assertProposalScenario(saved, scenario));
      setForm(null);
      setCommand(null);
      setNotice(
        "Draft loaded from the server. Review it before confirming. No change has been saved.",
      );
    } catch (issue) {
      onError(issue);
    } finally {
      inFlight.current = false;
      setBusy(false);
      setProposalLoading(false);
    }
  }
  async function prepare(action: Action, data: Row) {
    if (expired || inFlight.current || selectionPending || selectionError)
      return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const fresh = await loadScope();
      resolveSelection(fresh, validated?.selection);
      validateRequestedAction(fresh, {
        action,
        data,
        requestId: "form-review",
      });
      const payload: Row = { ...data, idempotency_key: crypto.randomUUID() };
      if (action === "set_availability")
        for (const key of ["start", "end"])
          payload[key] = new Date(text(payload[key])).toISOString();
      setProposal(
        assertProposalScenario(
          await api<Proposal>("operations/proposals", {
            action,
            data: payload,
            scenario,
          }),
          scenario,
        ),
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
    if (
      !proposal ||
      expired ||
      inFlight.current ||
      selectionPending ||
      selectionError
    )
      return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      assertProposalScenario(proposal, scenario);
      const fresh = await loadScope();
      validateRequestedAction(fresh, {
        action: proposal.action,
        data: proposal.data,
        requestId: "confirm-review",
      });
      const saved = await api<Command>(
        `operations/proposals/${encodeURIComponent(proposal.proposal_id)}/confirm`,
        {},
      );
      setCommand(saved);
      setProposal(null);
      window.dispatchEvent(
        new CustomEvent("daybreak:changed", { detail: { scenario } }),
      );
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
  async function recoverCommand(
    commandId: string,
    reason?: string,
  ): Promise<boolean> {
    if (!context || expired || inFlight.current) return false;
    const pending = context.pending_commands?.find(
      (item) => item.command_id === commandId,
    );
    const control = pending ? recoveryControl(context.actor, pending) : null;
    if (
      !control ||
      (reason === undefined
        ? control !== "retrieve"
        : control !== "cancel" || reason.trim().length < 3)
    )
      return false;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await api<Command>(
        `operations/commands/${encodeURIComponent(commandId)}${reason === undefined ? "" : "/recover"}`,
        reason === undefined
          ? undefined
          : { decision: "cancel", reason: reason.trim() },
      );
      setCommand(result);
      setNotice(
        result.status === "cancelled"
          ? "The server confirmed cancellation. The original operation was not executed."
          : result.status === "succeeded"
            ? "The server recovered the saved result."
            : "The command is still pending. Check its current recovery instructions.",
      );
      await refresh();
      window.dispatchEvent(
        new CustomEvent("daybreak:changed", { detail: { scenario } }),
      );
      return true;
    } catch (issue) {
      onError(issue);
      await refresh();
      return false;
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  return (
    <div className={`db-workspace db-${presentation}`}>
      {expired ? (
        <div className="db-alert" role="alert">
          {error || "Your session ended."}{" "}
          <a href={proposalSignInPath(linkedProposalId)}>Sign in again</a>
        </div>
      ) : (
        <>
          {!account.membership.organization_id ? (
            <section className="db-panel">
              <h2>Your connection is not linked yet.</h2>
              <p>
                Ask your administrator to verify your service connection.
                Creating an account or changing your profile team does not grant
                access to operational data.
              </p>
            </section>
          ) : (
            <>
              {error && (
                <div className="db-alert" role="alert">
                  {error}
                  <button className="db-button" onClick={() => setError("")}>
                    Dismiss
                  </button>
                </div>
              )}
              {presentation !== "assistant" && (
                <RoleOverview
                  context={context}
                  role={role}
                  onRefresh={() => void refresh()}
                />
              )}
              {presentation !== "role" && (
                <div className="db-assistant-content">
                  {context && context.cases.length > 0 && (
                    <label className="db-filter" htmlFor={`${messageId}-case`}>
                      Case to discuss
                      <select id={`${messageId}-case`} value={current?.case_id ? text(current.case_id) : ""} onChange={(event) => {
                        const caseId = event.target.value;
                        if (caseId) window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { selection: { case_id: caseId }, scenario } }));
                      }}>
                        <option value="">Choose one of your cases</option>
                        {context.cases.slice(0, 50).map((item) => <option key={text(item.case_id)} value={text(item.case_id)}>{itemTitle(item, "Service case")}</option>)}
                      </select>
                    </label>
                  )}
                  {selectionPending && (
                    <p className="db-muted" role="status">
                      Checking your current scope…
                    </p>
                  )}
                  {selectionError && (
                    <p className="db-alert" role="alert">
                      {selectionError}
                    </p>
                  )}
                  {(current || selectionError) && (
                    <div className="db-selection">
                      <span>
                        {current
                          ? `About ${itemTitle(current, current.case_id ? "this case" : current.work_item_id ? "this visit" : "this connection")}`
                          : "Selection unavailable"}
                      </span>
                      <button
                        className="db-icon"
                        aria-label="Clear selection"
                        onClick={() => {
                          setClearedSelection({ value: initialSelection });
                          setForm(null);
                          setProposal(null);
                          setError("");
                        }}
                      >
                        <X size={16} />
                      </button>
                    </div>
                  )}
                  {context &&
                    current &&
                    !selectionPending &&
                    !selectionError && (
                      <div className="db-actions db-context-actions">
                        {current.connection_id &&
                        !current.case_id &&
                        canPrepare(context, "create_case") ? (
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() =>
                              open("create_case", {
                                connection_id: current.connection_id,
                              })
                            }
                          >
                            Report a problem
                          </button>
                        ) : null}
                        {current.case_id &&
                        canPrepare(context, "set_availability") ? (
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
                        ) : null}
                        {current.work_item_id &&
                        canPrepare(context, "record_verdict") ? (
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() =>
                              open("record_verdict", {
                                work_item_id: current.work_item_id,
                              })
                            }
                          >
                            Record finding
                          </button>
                        ) : null}
                        {current.work_item_id &&
                        canPrepare(context, "review_work_item") ? (
                          <button
                            className="db-button"
                            disabled={busy}
                            onClick={() =>
                              open("review_work_item", {
                                work_item_id: current.work_item_id,
                              })
                            }
                          >
                            Review work
                          </button>
                        ) : null}
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
                          Ask for help
                        </button>
                      </div>
                    )}
                  {proposalLoading && (
                    <p role="status">Loading your draft for review…</p>
                  )}
                  <section className="db-panel db-chat">
                    <div className="db-section-title">
                      <h2>Conversation</h2>
                      <span className="db-badge">
                        {busy ? "Working…" : "Ready"}
                      </span>
                    </div>
                    <p className="db-muted">
                      Ask in English or Romanian. Actions stay as drafts until
                      you press Confirm.
                    </p>
                    <Voice
                      scenario={scenario}
                      turn={turn}
                      onError={onError}
                      disabled={
                        expired ||
                        !context ||
                        selectionPending ||
                        Boolean(selectionError)
                      }
                    />
                    <div
                      className="db-messages"
                      role="log"
                      aria-label="Conversation"
                      aria-live="polite"
                    >
                      {!messages.length && (
                        <div className="db-welcome">
                          <p>
                            {role === "customer"
                              ? "Tell me what happened at your connection."
                              : role === "technician"
                                ? "Ask what is next, why it matters, or tell me what you found."
                                : "Ask what needs a decision or compare the evidence behind two work items."}
                          </p>
                          <button
                            className="db-suggestion"
                            disabled={
                              busy ||
                              !context ||
                              selectionPending ||
                              Boolean(selectionError)
                            }
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
                      <label className="sr-only" htmlFor={messageId}>
                        Message Daybreak
                      </label>
                      <textarea
                        id={messageId}
                        placeholder="Type your message…"
                        maxLength={4000}
                        value={message}
                        onChange={(e) => setMessage(e.target.value)}
                        disabled={expired || selectionPending}
                      />
                      <button
                        className="db-primary"
                        disabled={
                          busy ||
                          !context ||
                          selectionPending ||
                          Boolean(selectionError) ||
                          !message.trim()
                        }
                        aria-label="Send message"
                      >
                        <ArrowRight size={18} />
                      </button>
                    </form>
                    <p className="db-provider">
                      {busy
                        ? "Working…"
                        : provider === "Not started"
                          ? "Ready for your message"
                          : "Reply received"}
                    </p>
                  </section>
                  {form && !selectionPending && (
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
                  {proposal && !selectionPending && (
                    <section
                      className="db-panel db-proposal"
                      ref={proposalCard}
                      aria-label="Action proposal"
                    >
                      <p className="db-eyebrow">REVIEW BEFORE SAVING</p>
                      <h2>{ACTION_NAMES[proposal.action]}</h2>
                      <p>{proposal.summary}</p>
                      <dl>
                        {Object.entries(proposal.data)
                          .filter(([key]) => !["idempotency_key"].includes(key))
                          .map(([key, value]) => (
                            <div key={key}>
                              <dt>{label(key)}</dt>
                              <dd>
                                {typeof value === "object"
                                  ? JSON.stringify(value)
                                  : [
                                        "start",
                                        "end",
                                        "planned_start",
                                        "planned_end",
                                      ].includes(key)
                                    ? readableDate(value)
                                    : text(value)}
                              </dd>
                            </div>
                          ))}
                      </dl>
                      <p className="db-muted">
                        Expires {readableDate(proposal.expires_at)}. No change
                        has been saved yet.
                      </p>
                      <div className="db-actions">
                        <button
                          className="db-primary"
                          disabled={
                            busy || selectionPending || Boolean(selectionError)
                          }
                          onClick={() => void confirm()}
                        >
                          <Check size={17} />
                          Confirm
                        </button>
                        <button
                          className="db-button"
                          disabled={
                            busy || selectionPending || Boolean(selectionError)
                          }
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
                          disabled={
                            busy || selectionPending || Boolean(selectionError)
                          }
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
                          Saved {readableDate(command.completed_at)}
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

                  <DraftRequests
                    proposals={context?.pending_proposals ?? []}
                    busy={busy}
                    onOpen={(id) => void openDraft(id)}
                  />
                  <PendingCommands
                    commands={context?.pending_commands ?? []}
                    actor={context?.actor ?? account.membership}
                    busy={busy}
                    onRetrieve={(id) => recoverCommand(id)}
                    onCancel={(id, reason) => recoverCommand(id, reason)}
                  />
                  {presentation === "page" && (
                    <p className="db-muted">
                      Synthetic demo · Current scope updated{" "}
                      {updated || "when the service is ready"}.
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
