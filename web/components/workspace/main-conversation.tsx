"use client";
import { useRef, type ReactNode, type RefObject } from "react";
import { ArrowUp, History, Mic, Plus, X } from "lucide-react";
import type { Message } from "@/lib/operations/types";
import type { Role } from "@/lib/operations/policy";
import type { ConversationStore } from "@/lib/operations/conversation-store";

export function conversationSuggestions(role: Role): string[] {
  if (role === "dispatcher") return ["Review pending decisions", "Explain the plan", "Find a work item"];
  if (role === "technician") return ["Next visit", "Why this visit?", "Record a finding"];
  return ["Case update", "Report a problem", "Get help"];
}

export function MainConversation({
  role, messages, message, messageId, setMessage, busy, unavailable, reviewing,
  mode, setMode, onSend, onSuggestion, conversations, onNew, onSelect,
  messageList, contextControls, review, voice, pending, notice,
}: {
  role: Role;
  messages: Message[];
  message: string;
  messageId: string;
  setMessage: (value: string) => void;
  busy: boolean;
  unavailable: boolean;
  reviewing: boolean;
  mode: "text" | "voice";
  setMode: (value: "text" | "voice") => void;
  onSend: () => void;
  onSuggestion: (index: number) => void;
  conversations: ConversationStore;
  onNew: () => void;
  onSelect: (id: string) => void;
  messageList: RefObject<HTMLDivElement | null>;
  contextControls: ReactNode;
  review: ReactNode;
  voice: ReactNode;
  pending: ReactNode;
  notice: string;
}) {
  const historyMenu = useRef<HTMLDetailsElement>(null);
  const savedThreads = conversations.threads.filter((thread) => thread.messages.length);
  const empty = !messages.length && !reviewing;
  const locked = busy || unavailable || reviewing || mode === "voice";
  const title = messages[0]?.content || "New conversation";
  return <>
    <header className="db-main-header">
      <p className="db-conversation-title" title={title}>{title}</p>
      <div className="db-main-header-actions">
        <details className="db-history" ref={historyMenu}>
          <summary><History size={16} aria-hidden="true" /><span>History</span></summary>
          <div className="db-history-menu">
            <p>Conversations in this tab</p>
            {savedThreads.length ? <ul>{savedThreads.map((thread) => <li key={thread.id}>
              <button type="button" disabled={locked} aria-current={thread.id === conversations.activeId ? "true" : undefined} onClick={() => {
                onSelect(thread.id);
                if (historyMenu.current) historyMenu.current.open = false;
              }}>
                <span>{thread.messages[0].content}</span>
                <small>{new Date(thread.updatedAt).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}</small>
              </button>
            </li>)}</ul> : <p className="db-muted">No saved conversations yet.</p>}
            <small>Only completed chats are saved. Draft requests are listed separately.</small>
          </div>
        </details>
        <button type="button" className="db-button db-new-chat" disabled={locked} onClick={onNew}><Plus size={16} aria-hidden="true" />New chat</button>
      </div>
    </header>
    <div className={`db-main-body${empty ? " is-empty" : ""}`}>
      {!empty && <div className="db-main-scroll" ref={messageList}>
        <div className="db-main-thread">
          {contextControls}
          <div className="db-main-messages" role="log" aria-label="Conversation" aria-live="polite" aria-busy={busy}>
            {messages.map((entry, index) => <div className={`db-main-message ${entry.role}`} key={index}>
              <span className="sr-only">{entry.role === "user" ? "You" : "Daybreak"}</span>
              <p>{entry.content}</p>
            </div>)}
            {busy && <p className="db-thinking" role="status">Daybreak is working…</p>}
          </div>
          {reviewing && review}
          {notice && <p className="db-notice" role="status">{notice}</p>}
        </div>
      </div>}
      <div className="db-main-input-area">
        {empty && <div className="db-main-welcome">
          <h1>What can I help you with?</h1>
          <p>{role === "customer" ? "Ask about your case or tell me what happened." : role === "technician" ? "Make sense of your next visit and record what you find." : "Review decisions, understand the plan and find the work that matters."}</p>
        </div>}
        {empty && contextControls}
        {!reviewing && <>
          {mode === "voice" && <div className="db-main-voice">
            <div className="db-main-voice-title"><span>Voice conversation</span><button type="button" className="db-icon" aria-label="Back to text" onClick={() => setMode("text")}><X size={16} /></button></div>
            {voice}
          </div>}
          <form className="db-main-compose" onSubmit={(event) => { event.preventDefault(); onSend(); }}>
            <label className="sr-only" htmlFor={messageId}>Message Daybreak</label>
            <textarea id={messageId} rows={2} placeholder="Ask anything about your work or service" maxLength={4000} value={message} onChange={(event) => {
              setMessage(event.target.value);
              event.target.style.height = "auto";
              event.target.style.height = `${Math.min(event.target.scrollHeight, 180)}px`;
            }} onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                onSend();
              }
            }} disabled={unavailable || busy || mode === "voice"} />
            <div className="db-main-compose-actions">
              <span className="db-main-input-hint">{busy ? "Preparing your answer…" : unavailable ? "Checking your access…" : "Daybreak"}</span>
              <button type="button" className="db-icon" aria-label={mode === "voice" ? "Close voice" : "Start voice"} aria-pressed={mode === "voice"} disabled={unavailable || busy} onClick={() => setMode(mode === "voice" ? "text" : "voice")}><Mic size={20} /></button>
              <button className="db-primary db-main-send" disabled={busy || unavailable || mode === "voice" || !message.trim()} aria-label="Send message"><ArrowUp size={19} /></button>
            </div>
          </form>
          {empty && <div className="db-main-suggestions">{conversationSuggestions(role).map((suggestion, index) => <button key={suggestion} type="button" className="db-suggestion" disabled={busy || unavailable || mode === "voice"} onClick={() => onSuggestion(index)}>{suggestion}</button>)}</div>}
          <p className="db-provider">Changes stay as drafts until you press Confirm.</p>
        </>}
        {empty && notice && <p className="db-notice" role="status">{notice}</p>}
        {pending}
      </div>
    </div>
  </>;
}
