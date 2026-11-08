import type { Message, Turn, WorkspaceAccount } from "./types";

export const CONVERSATION_THREAD_LIMIT = 10;
export const CONVERSATION_MESSAGE_LIMIT = 40;
export const CONVERSATION_CONTENT_LIMIT = 4000;
export const CONVERSATION_TOTAL_LIMIT = 120_000;
const STORAGE_LIMIT = 800_000;
type StorageAccess = Pick<Storage, "getItem" | "setItem">;
export interface ConversationThread {
  id: string;
  updatedAt: number;
  messages: Message[];
}
export interface ConversationStore {
  version: 1;
  scope: string;
  activeId: string | null;
  threads: ConversationThread[];
}

/** Call only with the server-verified account, after checking live scope. */
export function conversationScope(account: WorkspaceAccount, scenario: string): string {
  const membership = account.membership;
  return JSON.stringify([account.id, membership.organization_id, membership.role,
    membership.crew_id, [...membership.connection_ids].sort(), [...membership.permissions].sort(), scenario]);
}
export function emptyConversations(scope: string): ConversationStore {
  return { version: 1, scope, activeId: null, threads: [] };
}
function storageKey(scope: string): string {
  return `daybreak:conversations:v1:${encodeURIComponent(scope)}`;
}
function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
function bounded(store: ConversationStore): ConversationStore {
  const threads = store.threads.slice(0, CONVERSATION_THREAD_LIMIT).map((thread) => ({
    id: thread.id, updatedAt: thread.updatedAt,
    messages: thread.messages.slice(-CONVERSATION_MESSAGE_LIMIT).map(({ role, content }) => ({ role, content: content.slice(0, CONVERSATION_CONTENT_LIMIT) })),
  }));
  let total = threads.reduce((sum, thread) => sum + thread.messages.reduce((n, message) => n + message.content.length, 0), 0);
  // Retain complete turns. Remove old threads first and keep the active one last.
  for (const thread of [...threads].reverse().sort((a, b) => Number(a.id === store.activeId) - Number(b.id === store.activeId))) {
    while (total > CONVERSATION_TOTAL_LIMIT && thread.messages.length) {
      const removed = thread.messages.splice(0, 2);
      total -= removed.reduce((sum, message) => sum + message.content.length, 0);
    }
  }
  return { version: 1, scope: store.scope, activeId: store.activeId, threads };
}
export function readConversations(storage: StorageAccess | null, scope: string): ConversationStore {
  const empty = emptyConversations(scope);
  try {
    const raw = storage?.getItem(storageKey(scope));
    if (!raw || raw.length > STORAGE_LIMIT) return empty;
    const value: unknown = JSON.parse(raw);
    if (!record(value) || value.version !== 1 || value.scope !== scope || !Array.isArray(value.threads) || value.threads.length > CONVERSATION_THREAD_LIMIT) return empty;
    const threads: ConversationThread[] = [];
    for (const thread of value.threads) {
      if (!record(thread) || typeof thread.id !== "string" || !/^[a-zA-Z0-9-]{1,80}$/.test(thread.id) || threads.some((item) => item.id === thread.id) || typeof thread.updatedAt !== "number" || !Number.isFinite(thread.updatedAt) || !Array.isArray(thread.messages) || thread.messages.length > CONVERSATION_MESSAGE_LIMIT || thread.messages.length % 2) return empty;
      const messages: Message[] = [];
      for (const [index, message] of thread.messages.entries()) {
        if (!record(message) || message.role !== (index % 2 ? "assistant" : "user") || typeof message.content !== "string" || !message.content.trim() || message.content.length > CONVERSATION_CONTENT_LIMIT) return empty;
        // Storage is untrusted. Copy text only, never proposal objects or metadata.
        messages.push({ role: index % 2 ? "assistant" : "user", content: message.content });
      }
      threads.push({ id: thread.id, updatedAt: thread.updatedAt, messages });
    }
    if (value.activeId !== null && (typeof value.activeId !== "string" || !threads.some((thread) => thread.id === value.activeId))) return empty;
    return bounded({ version: 1, scope, activeId: value.activeId as string | null, threads });
  } catch { return empty; }
}
export function saveConversations(storage: StorageAccess | null, store: ConversationStore): void {
  try { storage?.setItem(storageKey(store.scope), JSON.stringify(bounded(store))); } catch { /* In-memory chat still works when storage is blocked or full. */ }
}
export function newConversation(store: ConversationStore, id = crypto.randomUUID(), now = Date.now()): ConversationStore {
  return bounded({ ...store, activeId: id, threads: [{ id, updatedAt: now, messages: [] }, ...store.threads.filter((thread) => thread.messages.length && thread.id !== id)] });
}
export function selectConversation(store: ConversationStore, id: string): ConversationStore {
  return store.threads.some((thread) => thread.id === id) ? { ...store, activeId: id } : store;
}
export function activeConversation(store: ConversationStore): ConversationThread | undefined {
  return store.threads.find((thread) => thread.id === store.activeId);
}
/** Only completed read-only exchanges belong in session history. Drafts stay on the server. */
export function rememberReadOnlyTurn(store: ConversationStore, input: string, answer: Turn, now = Date.now()): ConversationStore {
  if (answer.proposal || typeof answer.reply !== "string" || !answer.reply.trim() || !input.trim()) return store;
  const next = store.activeId ? store : newConversation(store);
  const active = activeConversation(next);
  if (!active) return next;
  const messages: Message[] = [...active.messages, { role: "user", content: input }, { role: "assistant", content: answer.reply }];
  return bounded({ ...next, threads: [{ id: active.id, updatedAt: now, messages }, ...next.threads.filter((thread) => thread.id !== active.id)] });
}
