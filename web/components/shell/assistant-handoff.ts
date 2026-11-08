import { assistantIntent, assistantScenarioMatches } from "./assistant-context";

const PREFIX = "daybreak:assistant:intent:";
export const ASSISTANT_INTENT_MAX_AGE = 10 * 60 * 1000;
const MAX_SIZE = 16_384;
type IntentStorage = Pick<Storage, "length" | "key" | "getItem" | "setItem" | "removeItem">;

export function assistantIntentKey(accountId: string, scenario: string): string {
  return `${PREFIX}${encodeURIComponent(accountId)}:${encodeURIComponent(scenario)}`;
}
export function assistantDashboardPath(scenario: string): string {
  return `/app?scenariu=${encodeURIComponent(scenario)}#assistant`;
}
function validScope(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim()) && value.length <= 256 && !/[\u0000-\u001f\u007f]/.test(value);
}
function record(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/** A single untrusted navigation hint, never permission or a saved proposal. */
export function storeAssistantIntent(storage: IntentStorage, accountId: string, scenario: string, detail: unknown, now = Date.now()): boolean {
  if (!validScope(accountId) || !validScope(scenario) || !Number.isFinite(now) || !assistantScenarioMatches(detail, scenario)) return false;
  const parsed = assistantIntent(detail);
  if (!parsed) return false;
  const intent = { selection: parsed.selection, ...(parsed.requestedAction ? { action: parsed.requestedAction.action, data: parsed.requestedAction.data } : {}) };
  const serialized = JSON.stringify({ version: 1, accountId, scenario, createdAt: now, intent });
  if (serialized.length > MAX_SIZE) return false;
  // There is at most one outstanding handoff, including across account switches.
  for (let i = storage.length - 1; i >= 0; i--) {
    const key = storage.key(i);
    if (key?.startsWith(PREFIX)) storage.removeItem(key);
  }
  storage.setItem(assistantIntentKey(accountId, scenario), serialized);
  return true;
}

export function consumeAssistantIntent(storage: IntentStorage, accountId: string, scenario: string, now = Date.now()): ReturnType<typeof assistantIntent> {
  if (!validScope(accountId) || !validScope(scenario) || !Number.isFinite(now)) return null;
  const key = assistantIntentKey(accountId, scenario);
  const serialized = storage.getItem(key);
  if (!serialized) return null;
  storage.removeItem(key); // Remove before parsing, including invalid or expired data.
  if (serialized.length > MAX_SIZE) return null;
  try {
    const saved: unknown = JSON.parse(serialized);
    if (!record(saved) || saved.version !== 1 || saved.accountId !== accountId || saved.scenario !== scenario
      || typeof saved.createdAt !== "number" || !Number.isFinite(saved.createdAt)
      || saved.createdAt > now || now - saved.createdAt >= ASSISTANT_INTENT_MAX_AGE || !record(saved.intent)
      || !assistantScenarioMatches(saved.intent, scenario)) return null;
    return assistantIntent({ ...saved.intent, scenario });
  } catch { return null; }
}
