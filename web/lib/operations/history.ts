import type { Message } from "./types";

export const CHAT_HISTORY_LIMIT = 12;
export const CHAT_MESSAGE_LIMIT = 4000;

/** History is conversational context only; operational facts come from the server. */
export function conversationHistory(messages: readonly Message[]): Message[] {
  return messages.slice(-CHAT_HISTORY_LIMIT).map(({ role, content }) => ({
    role,
    content: content.slice(0, CHAT_MESSAGE_LIMIT),
  }));
}
