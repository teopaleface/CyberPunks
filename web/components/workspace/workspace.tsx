"use client";
import { useCallback, useEffect, useId, useRef, useState, type ReactNode } from "react";
import { ConversationProvider } from "@elevenlabs/react";
import { ArrowLeft, ArrowRight, Check, MessageSquare, Mic, Sparkles, X } from "lucide-react";
import { api, SessionExpired } from "@/lib/operations/client";
import { loadLinkedProposal } from "@/lib/operations/linked-proposal";
import { proposalSignInPath } from "@/lib/operations/proposal-link";
import { conversationHistory } from "@/lib/operations/history";
import { activeConversation, conversationScope, emptyConversations, newConversation, readConversations, rememberReadOnlyTurn, saveConversations, selectConversation, type ConversationStore } from "@/lib/operations/conversation-store";
import { TaskPanel } from "@/components/agentic/task-panel";
import { getTask, resumeTask, type TaskView } from "@/lib/agentic/client";
import { MainConversation } from "./main-conversation";
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
import { ACTION_NAMES, FIELD_LABELS, fieldValueLabel, ProposalForm } from "./proposal-form";
import { FindingPhotoGallery, findingPhotos } from "@/components/operations/finding-photos";
import { DecisionComparison } from "@/components/operations/decision-correction";
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
  presentation?: "page" | "assistant" | "role" | "main";
  initialSelection?: WorkspaceSelection;
  requestedAction?: WorkspaceRequestedAction;
  scenario?: string;
  linkedProposalId?: string | null;
  initialError?: string;
  assistant?: ReactNode;
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
  assistant,
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
  const [defaultSelection, setDefaultSelection] = useState<WorkspaceSelection>();
  const defaultAttempted = useRef(false);
  const effectiveSelection =
    clearedSelection && clearedSelection.value === initialSelection
      ? undefined
      : initialSelection ?? defaultSelection;
  const currentKey = selectionKey(effectiveSelection);
  const selectionPending = validated?.key !== currentKey;
  const appliedRequests = useRef(new Set<string>());
  const scopeSequence = useRef(0);
  const scopeRead = useRef<Promise<Context> | null>(null);
  const previousSelectionKey = useRef(currentKey);
  const [context, setContext] = useState<Context | null>(null);
  const [error, setError] = useState(initialError ?? "");
  const [proposalLoading, setProposalLoading] = useState(
    Boolean(linkedProposalId),
  );
  const [expired, setExpired] = useState(false);
  const [task, setTask] = useState<TaskView | null>(null);
  const taskOutdated = Boolean(task && context && (
    text(context.plan.version ?? context.plan.plan_version) !== task.plan_version ||
    (Array.isArray(task.result.cases) && task.result.cases.some((value) => {
      const saved = value as Row;
      const current = context.cases.find((item) => item.case_id === saved.case_id);
      return !current || current.version !== saved.version;
    }))
  ));
  const [messages, setMessages] = useState<Message[]>([]);
  const history = useRef<Message[]>([]);
  const conversationKey = conversationScope(account, scenario);
  const [conversations, setConversations] = useState(() => emptyConversations(conversationKey));
  const conversationsRef = useRef(conversations);
  const conversationsLoaded = useRef(false);
  const [conversationsReady, setConversationsReady] = useState(false);
  const alive = useRef(true);
  const sessionCurrent = useRef(true);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(Boolean(linkedProposalId));
  const inFlight = useRef(Boolean(linkedProposalId));
  const [proposal, setProposal] = useState<Proposal | null>(null);
  const [command, setCommand] = useState<Command | null>(null);
  const [form, setForm] = useState<{ action: Action; data: Row } | null>(null);
  const [mode, setMode] = useState<"text" | "voice">("text");
  const [updated, setUpdated] = useState("");
  const [notice, setNotice] = useState("");
  const messageList = useRef<HTMLDivElement>(null);
  const proposalCard = useRef<HTMLElement>(null);
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);
  const updateConversations = useCallback((next: ConversationStore) => {
    conversationsRef.current = next;
    setConversations(next);
    try { saveConversations(window.sessionStorage, next); } catch { /* Optional session storage. */ }
  }, []);
  const open = useCallback((action: Action, data: Row = {}) => {
    setForm({ action, data });
    setProposal(null);
    setNotice("");
    setCommand(null);
  }, []);
  const onError = useCallback((issue: unknown) => {
    if (issue instanceof SessionExpired) {
      sessionCurrent.current = false;
      setExpired(true);
      setContext(null);
      setValidated(null);
      setTask(null);
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
        behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth",
        block: "center",
      });
  }, [proposal?.proposal_id]);
  useEffect(() => {
    const controller = new AbortController();
    let taskId: string | null = null;
    try { taskId = window.sessionStorage.getItem(`agentic-task:${conversationKey}`); } catch { /* Optional storage. */ }
    if (taskId) {
      getTask(taskId, scenario, controller.signal).then((saved) => {
        if (!controller.signal.aborted && sessionCurrent.current) setTask(saved);
      }).catch(() => { /* A stale or revoked task is never restored as current evidence. */ });
    }
    return () => controller.abort();
  }, [conversationKey, scenario]);
  useEffect(() => {
    if (task) {
      try { window.sessionStorage.setItem(`agentic-task:${conversationKey}`, task.task_id); } catch { /* Optional storage. */ }
    }
  }, [task, conversationKey]);
  const loadScope = useCallback(async (): Promise<Context> => {
    if (!account.membership.organization_id)
      throw new Error("Your account is not linked to operational data.");
    // Polls and selection checks share one authenticated read. Starting a new
    // read every two seconds used to invalidate every slower response.
    if (scopeRead.current) return scopeRead.current;
    const pending = (async () => {
      const sequence = ++scopeSequence.current;
      const next = assertScope(
        await api<Context>(
          `operations/context?scenario=${encodeURIComponent(scenario)}`,
        ),
        account,
        scenario,
      );
      if (conversationScope({ ...account, membership: next.actor }, scenario) !== conversationKey)
        throw new SessionExpired("Your operational access changed. Reopen the console.");
      if (alive.current && sessionCurrent.current && sequence === scopeSequence.current) setContext(next);
      return next;
    })();
    scopeRead.current = pending;
    try { return await pending; }
    finally { if (scopeRead.current === pending) scopeRead.current = null; }
  }, [account, scenario, conversationKey]);
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
  const scopeVerified = Boolean(context);
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
            // Use only a freshly verified role scope, once. An explicit selection,
            // a linked review or Clear selection always takes precedence.
            if (!defaultAttempted.current && !clearedSelection && initialSelection === undefined && !requestedAction && !linkedProposalId && !initialError && presentation !== "role") {
              defaultAttempted.current = true;
              const preferred = defaultAssistantSelection(next);
              if (preferred) setDefaultSelection(preferred);
            }
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
    clearedSelection,
    initialSelection,
    requestedAction,
    linkedProposalId,
    initialError,
    presentation,
  ]);
  useEffect(() => {
    if (
      !requestedAction ||
      Boolean(linkedProposalId) ||
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
    linkedProposalId,
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
    // Never read a previous chat until this account's scope has been checked live.
    if (presentation !== "main" || !scopeVerified || expired || conversationsLoaded.current) return;
    let restored = emptyConversations(conversationKey);
    try { restored = readConversations(window.sessionStorage, conversationKey); } catch { /* Private browsing can deny storage. */ }
    const timer = setTimeout(() => {
      conversationsLoaded.current = true;
      setConversationsReady(true);
      conversationsRef.current = restored;
      setConversations(restored);
      // A proposal or explicit action link always opens its own review, ahead of saved chat.
      if (!linkedProposalId && !requestedAction && !initialSelection && !initialError) {
        history.current = activeConversation(restored)?.messages ?? [];
        setMessages([...history.current]);
      } else {
        updateConversations(newConversation(restored));
      }
    }, 0);
    return () => clearTimeout(timer);
  }, [presentation, scopeVerified, expired, conversationKey, linkedProposalId, requestedAction, initialSelection, initialError, updateConversations]);
  useEffect(() => {
    const list = messageList.current;
    if (list) list.scrollTop = list.scrollHeight;
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
      if (!alive.current || !sessionCurrent.current) throw new SessionExpired("Your session changed. Reopen the console.");
      resolveSelection(fresh, validated?.selection);
      const answer = await api<Turn>("conversation/chat", {
        message: input,
        history: previous,
        scenario,
        ...(validated?.selection ? { selection: validated.selection } : {}),
      });
      if (!alive.current || !sessionCurrent.current) throw new SessionExpired("Your session changed. Reopen the console.");
      if (typeof answer.reply !== "string")
        throw new Error("The conversation service did not return a reply.");
      append([{ role: "assistant", content: answer.reply }]);
      if (presentation === "main" && conversationsLoaded.current) {
        updateConversations(rememberReadOnlyTurn(conversationsRef.current, input, answer));
      }

      if (answer.task) setTask(answer.task);
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
  async function continueTask(taskId: string) {
    if (expired || inFlight.current) return;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);
    try {
      setBusy(true);
      inFlight.current = true;
      const result = await resumeTask(taskId, scenario, controller.signal);
      if (alive.current && sessionCurrent.current) setTask(result);
    } catch (issue) { onError(issue); }
    finally { clearTimeout(timer); inFlight.current = false; setBusy(false); }
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
      if (!alive.current || !sessionCurrent.current) return;
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
      if (!alive.current || !sessionCurrent.current) throw new SessionExpired("Your session changed. Reopen the console.");
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
      if (!alive.current || !sessionCurrent.current) throw new SessionExpired("Your session changed. Reopen the console.");
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
      setNotice("");
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
          ? "Request cancelled. The original operation was not executed."
          : result.status === "succeeded"
            ? "Saved result retrieved."
            : "Still processing. Check the request instructions below.",
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
  function backToChat() {
    setForm(null);
    setProposal(null);
    setCommand(null);
    setNotice("");
    setMode("text");
  }
  const reviewing = Boolean(form || proposal || proposalLoading || command);
  const unavailable = expired || !context || selectionPending || Boolean(selectionError) || (presentation === "main" && !conversationsReady);
  const pendingCount = (context?.pending_proposals?.length ?? 0) + (context?.pending_commands?.length ?? 0);
  const reviewContent = (
<div className="db-assistant-review">
                  <button type="button" className="db-button db-back-chat" disabled={busy} onClick={backToChat}><ArrowLeft size={14} />Back to chat</button>
                  {proposalLoading && <p role="status">Loading your draft for review…</p>}
                  {form && !selectionPending && <section className="db-panel">
                    <ProposalForm key={`${form.action}-${JSON.stringify(form.data)}`} action={form.action} initial={form.data} context={context ?? undefined} onSubmit={prepare} onCancel={backToChat} busy={busy} />
                  </section>}
                  {proposal && !selectionPending && <section className="db-panel db-proposal" ref={proposalCard} aria-label="Action proposal">
                    <p className="db-eyebrow">Review before saving</p>
                    <h2>{proposal.action === "review_work_item" && proposal.data.is_correction === true ? "Review your correction" : ACTION_NAMES[proposal.action]}</h2>
                    <p>{proposal.summary}</p>
                    <dl>{Object.entries(proposal.data).filter(([key]) => !["idempotency_key", "plan_version", "case_version", "linked_case_versions", "photo_ids", "photos", "decision_before", "original_ai_decision", "original_ai_decision_status", "is_correction"].includes(key) && !(proposal.action === "review_work_item" && ["decision", "note"].includes(key))).map(([key, value]) => <div key={key}>
                      <dt>{FIELD_LABELS[key] ?? label(key)}</dt>
                      <dd>{proposalField(context, key, value)}</dd>
                    </div>)}</dl>
                    {proposal.action === "record_verdict" ? <FindingPhotoGallery photos={findingPhotos(proposal.data.photos)} scenario={scenario} /> : null}
                    {proposal.action === "review_work_item" ? <DecisionComparison data={proposal.data} /> : null}
                    <p className="db-muted">Expires {readableDate(proposal.expires_at)}. No change has been saved yet.</p>
                    {proposal.action === "record_verdict" && <p className="db-muted">This records a finding. It does not confirm a repair or close the case.</p>}
                    <div className="db-actions">
                      <button className="db-primary" disabled={busy || unavailable} onClick={() => void confirm()}><Check size={17} />Confirm</button>
                      <button className="db-button" disabled={busy || unavailable} onClick={() => { setForm({ action: proposal.action, data: proposal.data }); setProposal(null); }}>Edit</button>
                      <button className="db-button" disabled={busy || unavailable} onClick={() => { setProposal(null); setNotice("Proposal cancelled. No change was saved."); }}>Cancel</button>
                    </div>
                  </section>}
                  {command && <section className="db-panel db-result" aria-label="Request result">
                    <h2>{commandHeading(command.status)}</h2>
                    <p>{command.status === "succeeded" ? "Your request was saved." : command.status === "cancelled" ? "This request was cancelled." : command.status === "failed" ? "The request could not complete. Review its details before trying again." : "This request is awaiting verification. Check its result before starting another."}</p>
                    <p className="db-muted">Request {command.command_id.slice(0, 8)} · {label(command.status)}{text(command.completed_at) ? ` · ${readableDate(command.completed_at)}` : ""}</p>
                    {command.result?.case && typeof command.result.case === "object" ? <p>Case status: {label((command.result.case as Row).status)}</p> : null}
                    {command.status === "succeeded" && command.result?.finding && typeof command.result.finding === "object" ? <div className="db-saved-finding"><h3>{fieldValueLabel("outcome", (command.result.finding as Row).outcome)}</h3><p>{text((command.result.finding as Row).note)}</p><FindingPhotoGallery photos={findingPhotos((command.result.finding as Row).photos)} scenario={scenario} /><p className="db-muted">Finding saved. Repair and case closure are not confirmed.</p></div> : null}
                    {command.status === "succeeded" && command.result?.manual_correction && typeof command.result.manual_correction === "object" ? <DecisionComparison data={command.result.manual_correction as Row} saved /> : null}
                    <details className="db-details">
                      <summary>Request receipt</summary>
                      <p>Reference: {command.command_id}</p>
                      <dl>{Object.entries(command.result ?? {}).filter(([, value]) => typeof value === "string" || typeof value === "number").map(([key, value]) => <div key={key}><dt>{label(key)}</dt><dd>{text(value)}</dd></div>)}</dl>
                    </details>
                    <button className="db-button" disabled={busy} onClick={() => {
                      void api<Command>(`operations/commands/${encodeURIComponent(command.command_id)}`).then(setCommand).catch(onError);
                    }}>Check request status</button>
                  </section>}
                </div>
  );
  const pendingControls = pendingCount > 0 && <details className="db-assistant-requests">
                <summary>Drafts and pending requests <span className="db-count">{pendingCount}</span></summary>
                <div>
                  <DraftRequests proposals={context?.pending_proposals ?? []} busy={busy} onOpen={(id) => void openDraft(id)} />
                  <PendingCommands commands={context?.pending_commands ?? []} actor={context?.actor ?? account.membership} busy={busy} onRetrieve={(id) => recoverCommand(id)} onCancel={(id, reason) => recoverCommand(id, reason)} />
                </div>
              </details>;
  function selectChat(id?: string) {
    setTask(null);
    try { window.sessionStorage.removeItem(`agentic-task:${conversationKey}`); } catch { /* Optional storage. */ }
    if (busy || unavailable || reviewing || mode === "voice") return;
    const next = id ? selectConversation(conversationsRef.current, id) : newConversation(conversationsRef.current);
    updateConversations(next);
    history.current = activeConversation(next)?.messages ?? [];
    setMessages([...history.current]);
    setMessage("");
    setNotice("");
    setError("");
    // Thread navigation never mutates drafts, commands or confirmations.
  }
  function sendMessage() {
    if (!message.trim() || busy || unavailable || mode === "voice") return;
    const input = message.trim();
    setMessage("");
    void turn(input).catch(() => {});
  }
  function suggest(index: number) {
    if (!context || busy || unavailable) return;
    if (role === "customer" && index > 0) {
      const action = index === 1 ? "create_case" : "request_human";
      if (!canPrepare(context, action)) return;
      const connectionId = current?.connection_id ?? (context.connections.length === 1 ? context.connections[0].connection_id : undefined);
      open(action, { ...(connectionId ? { connection_id: connectionId } : {}), ...(action === "request_human" && current?.case_id ? { case_id: current.case_id } : {}) });
      return;
    }
    if (role === "technician" && index === 2) {
      if (canPrepare(context, "record_verdict")) open("record_verdict", current?.work_item_id ? { work_item_id: current.work_item_id } : {});
      return;
    }
    const prompts = role === "dispatcher" ? ["What decisions are waiting for my review?", "Explain the current plan and why these visits were chosen.", "Help me find a work item."] : role === "technician" ? ["What is my next approved visit?", "Why was this visit chosen?"] : ["What is the current status of my case?"];
    if (prompts[index]) void turn(prompts[index]).catch(() => {});
  }
  if (presentation === "main") {
    const showContext = Boolean(initialSelection && Object.keys(initialSelection).length) || messages.length > 0;
    const contextControls = showContext && current && !reviewing ? <details className="db-main-context">
      <summary>About {itemTitle(current, current.case_id ? "this case" : current.work_item_id ? "this visit" : "this connection")}</summary>
      <div>
        {context && context.cases.length > 1 && Boolean(current.case_id) && <label className="db-filter">Discuss another case<select value={text(current?.case_id)} disabled={busy} onChange={(event) => {
          window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { selection: { case_id: event.target.value }, scenario } }));
        }}>{context.cases.map((item) => <option key={text(item.case_id)} value={text(item.case_id)}>{itemTitle(item, "Service case")}</option>)}</select></label>}
        <div className="db-actions">
          {Boolean(current.case_id) && context && canPrepare(context, "set_availability") && <button className="db-button" disabled={busy || unavailable} onClick={() => open("set_availability", { case_id: current.case_id })}>Share availability</button>}
          {Boolean(current.work_item_id) && context && canPrepare(context, "record_verdict") && <button className="db-button" disabled={busy || unavailable} onClick={() => open("record_verdict", { work_item_id: current.work_item_id })}>Record a finding</button>}
          {Boolean(current.work_item_id) && context && canPrepare(context, "review_work_item") && <button className="db-button" disabled={busy || unavailable} onClick={() => open("review_work_item", { work_item_id: current.work_item_id })}>Review this work</button>}
          <button type="button" className="db-button" disabled={busy || unavailable} onClick={() => { setClearedSelection({ value: initialSelection }); backToChat(); setError(""); }}>Clear selection</button>
        </div>
      </div>
    </details> : null;
    return <div className="db-workspace db-main">
      {expired ? <div className="db-alert" role="alert">{error || "Your session ended."} <a href={proposalSignInPath(linkedProposalId)}>Sign in again</a></div>
        : !account.membership.organization_id ? <section className="db-panel"><h2>Your connection is not linked yet.</h2><p>Ask your administrator to verify your service connection.</p></section>
        : <>
          {error && <div className="db-alert" role="alert">{error}{!context && <button className="db-button" disabled={busy} onClick={() => { setError(""); void refresh(); }}>Retry loading access</button>}<button className="db-button" onClick={() => setError("")}>Dismiss</button></div>}
          {selectionError && <div className="db-alert" role="alert">{selectionError}<button className="db-button" disabled={busy} onClick={() => { setClearedSelection({ value: initialSelection }); backToChat(); setError(""); }}>Clear selection</button></div>}
          <MainConversation taskResult={task ? <TaskPanel task={taskOutdated ? {...task, result: {...task.result, snapshot_outdated: true}} : task} onReview={(work_item_id) => open("review_work_item", {work_item_id})} onResume={continueTask} /> : null} role={role} messages={messages} message={message} messageId={messageId} setMessage={setMessage} busy={busy} unavailable={unavailable} reviewing={reviewing} mode={mode} setMode={setMode} onSend={sendMessage} onSuggestion={suggest} conversations={conversations} onNew={() => selectChat()} onSelect={selectChat} messageList={messageList} contextControls={contextControls} review={reviewContent} voice={<Voice scenario={scenario} turn={turn} onError={onError} disabled={unavailable} />} pending={pendingControls} notice={notice} />
        </>}
    </div>;
  }
  return (
    <div className={`db-workspace db-${presentation}`}>
      {presentation !== "role" && (
        <div className="db-assistant-heading">
          <span className="db-assistant-symbol"><Sparkles size={19} aria-hidden="true" /></span>
          <div>
            <h2>Daybreak assistant</h2>
            <p>{role === "customer" ? "Help with your connections and cases." : role === "technician" ? "Your visits, findings and next steps." : "Help with cases, evidence and plan decisions."}</p>
          </div>
        </div>
      )}
      {expired ? (
        <div className="db-alert" role="alert">
          {error || "Your session ended."}{" "}
          <a href={proposalSignInPath(linkedProposalId)}>Sign in again</a>
        </div>
      ) : !account.membership.organization_id ? (
        <section className="db-panel">
          <h2>Your connection is not linked yet.</h2>
          <p>Ask your administrator to verify your service connection. Creating an account or changing your profile team does not grant access to operational data.</p>
        </section>
      ) : (
        <>
          {error && <div className="db-alert" role="alert">{error}{!context && <button className="db-button" disabled={busy} onClick={() => { setError(""); void refresh(); }}>Retry loading access</button>}<button className="db-button" onClick={() => setError("")}>Dismiss</button></div>}
          {presentation !== "assistant" && <RoleOverview context={context} role={role} onRefresh={() => void refresh()} assistant={assistant} />}
          {presentation !== "role" && (
            <div className="db-assistant-content">
              <div className="db-assistant-context">
                {!reviewing && <div className="db-assistant-toolbar">
                  <div className="db-mode-toggle" role="group" aria-label="Conversation mode">
                    <button type="button" aria-pressed={mode === "text"} onClick={() => setMode("text")}><MessageSquare size={14} aria-hidden="true" />Text</button>
                    <button type="button" aria-pressed={mode === "voice"} disabled={unavailable || busy} onClick={() => setMode("voice")}><Mic size={14} aria-hidden="true" />Voice</button>
                  </div>
                  <span className="db-assistant-status" role="status">{busy ? "Working…" : context && !selectionPending ? "Ready" : "Connecting…"}</span>
                </div>}
                {!reviewing && context && context.cases.length > 0 && (!current || Boolean(current.case_id)) && (
                  <label className="db-filter db-case-picker" htmlFor={`${messageId}-case`}>
                    Case
                    <select id={`${messageId}-case`} value={current?.case_id ? text(current.case_id) : ""} disabled={busy} onChange={(event) => {
                      window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { selection: event.target.value ? { case_id: event.target.value } : {}, scenario } }));
                    }}>
                      <option value="">Choose a case to discuss</option>
                      {context.cases.map((item) => <option key={text(item.case_id)} value={text(item.case_id)}>{itemTitle(item, "Service case")} · #{text(item.case_id).slice(0, 8)}</option>)}
                    </select>
                  </label>
                )}
                {selectionPending && <p className="db-muted" role="status">Checking your current access…</p>}
                {selectionError && <p className="db-alert" role="alert">{selectionError}</p>}
                {((current && !current.case_id) || selectionError) && <div className="db-selection">
                  <span>{current ? `About ${itemTitle(current, current.case_id ? "this case" : current.work_item_id ? "this visit" : "this connection")}` : "Selection unavailable"}</span>
                  <button type="button" className="db-icon" disabled={busy} aria-label="Clear selection" onClick={() => {
                    setClearedSelection({ value: initialSelection });
                    backToChat();
                    setError("");
                  }}><X size={16} /></button>
                </div>}
                {!reviewing && context && current && !unavailable && <details className="db-context-menu"><summary>Actions</summary><div className="db-actions db-context-actions">
                  {current.connection_id && !current.case_id && canPrepare(context, "create_case") ? <button className="db-button" disabled={busy} onClick={() => open("create_case", { connection_id: current.connection_id })}>Report a problem</button> : null}
                  {current.case_id && canPrepare(context, "set_availability") ? <button className="db-button" disabled={busy} onClick={() => open("set_availability", { case_id: current.case_id })}>Share availability</button> : null}
                  {current.work_item_id && canPrepare(context, "record_verdict") ? <button className="db-button" disabled={busy} onClick={() => open("record_verdict", { work_item_id: current.work_item_id })}>Record finding</button> : null}
                  {current.work_item_id && canPrepare(context, "review_work_item") ? <button className="db-button" disabled={busy} onClick={() => open("review_work_item", { work_item_id: current.work_item_id })}>Review work</button> : null}
                  <button className="db-button" disabled={busy} onClick={() => open("request_human", {
                    ...(current.case_id ? { case_id: current.case_id } : {}),
                    ...(current.connection_id ? { connection_id: current.connection_id } : {}),
                  })}>Ask for help</button>
                </div></details>}
              </div>
              {!reviewing ? (
                <section className="db-panel db-chat" aria-label="Chat with Daybreak">
                  {mode === "voice" && <Voice scenario={scenario} turn={turn} onError={onError} disabled={unavailable} />}
                  <div className="db-messages" role="log" aria-label="Conversation" aria-live="polite" ref={messageList}>
                    {!messages.length && <div className="db-welcome">
                      <p>{role === "customer" ? "How can I help with your service today?" : role === "technician" ? "Ask about your next visit or record what you found." : "What would you like to review today?"}</p>
                      <div className="db-quick-chips">
                        <button className="db-suggestion" disabled={busy || unavailable} onClick={() => void turn(role === "technician" ? "What is my next stop and why?" : role === "dispatcher" ? "What needs my decision?" : "What is the status of my case?").catch(() => {})}>{role === "technician" ? "Next visit" : role === "dispatcher" ? "Needs review" : "Case update"}</button>
                        <button className="db-suggestion" disabled={busy || unavailable} onClick={() => {
                          if (context && canPrepare(context, "create_case")) open("create_case", current?.connection_id ? { connection_id: current.connection_id } : {});
                          else { setMessage("I need help with a new request: "); document.getElementById(messageId)?.focus(); }
                        }}>New request</button>
                        <button className="db-suggestion" disabled={busy || unavailable} onClick={() => document.getElementById(messageId)?.focus()}>Ask a question</button>
                      </div>
                    </div>}
                    {messages.map((entry, i) => <div className={`db-message ${entry.role}`} key={i}><span>{entry.role === "user" ? "You" : "Daybreak"}</span><p>{entry.content}</p></div>)}
                  </div>
                  <form className="db-compose" onSubmit={(e) => {
                    e.preventDefault();
                    if (!message.trim() || busy || unavailable) return;
                    const input = message;
                    setMessage("");
                    void turn(input).catch(() => {});
                  }}>
                    <label className="sr-only" htmlFor={messageId}>Message Daybreak</label>
                    <textarea id={messageId} rows={2} placeholder="Ask Daybreak…" maxLength={4000} value={message} onChange={(e) => setMessage(e.target.value)} disabled={unavailable || busy} />
                    <button className="db-primary" disabled={busy || unavailable || !message.trim()} aria-label="Send message"><ArrowRight size={18} /></button>
                  </form>
                  <p className="db-provider">Changes stay as drafts until you press Confirm.</p>
                </section>
              ) : reviewContent}
              {notice && <p className="db-notice" role="status">{notice}</p>}
              {pendingControls}
              {presentation === "page" && <p className="db-muted">Synthetic demo · Current scope updated {updated || "when the service is ready"}.</p>}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export function commandHeading(status: string): string {
  if (status === "succeeded") return "Saved";
  if (status === "cancelled") return "Cancelled";
  if (status === "pending" || status === "running" || status === "processing") return "Processing";
  return "Needs review";
}
export function defaultAssistantSelection(context: Context): WorkspaceSelection | undefined {
  if (context.actor.role === "customer") {
    const latest = [...context.cases].sort((a, b) => (Date.parse(text(b.created_at ?? b.updated_at)) || 0) - (Date.parse(text(a.created_at ?? a.updated_at)) || 0))[0];
    return latest && text(latest.case_id) ? { case_id: text(latest.case_id) } : undefined;
  }
  if (context.actor.role === "technician" && (context.plan.approved === true || context.next_stop_status === "approved_plan") && context.next_stop && typeof context.next_stop === "object") {
    const id = text((context.next_stop as Row).work_item_id);
    if (id && context.work_items.some((item) => item.work_item_id === id)) return { work_item_id: id };
  }
  return undefined;
}
function proposalField(context: Context | null, key: string, value: unknown): string {
  const items = key === "connection_id" ? context?.connections : key === "case_id" ? context?.cases : key === "work_item_id" ? context?.work_items : undefined;
  const item = items?.find((row) => row[key] === value);
  if (item) return itemTitle(item, key === "case_id" ? "Service case" : key === "work_item_id" ? "Assigned visit" : "Service connection");
  if (["start", "end", "planned_start", "planned_end"].includes(key)) return readableDate(value);
  return typeof value === "object" ? JSON.stringify(value) : fieldValueLabel(key, value);
}
