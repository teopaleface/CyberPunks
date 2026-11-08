import { expect, test } from "bun:test";
import { ASSISTANT_INTENT_MAX_AGE, assistantDashboardPath, assistantIntentKey, consumeAssistantIntent, storeAssistantIntent } from "./assistant-handoff";
import { openRequestedAction } from "@/components/workspace/scope";
import type { Context } from "@/lib/operations/types";

// Synthetic navigation state only. No account session or operations API.
function storage() {
  const items = new Map<string, string>();
  return { get length() { return items.size; }, key: (i: number) => [...items.keys()][i] ?? null, getItem: (key: string) => items.get(key) ?? null, setItem: (key: string, value: string) => { items.set(key, value); }, removeItem: (key: string) => { items.delete(key); } };
}
const detail = { scenario: "synthetic-summer", selection: { case_id: "synthetic-case" }, action: "set_availability", data: { case_id: "synthetic-case" } };
const account = "synthetic-account";
const scenario = "synthetic-summer";
const now = 100_000;

test("one matching intent is consumed once and opens only an editable form", () => {
  const store = storage();
  expect(storeAssistantIntent(store, account, scenario, detail, now)).toBe(true);
  const intent = consumeAssistantIntent(store, account, scenario, now + 1)!;
  expect(intent.selection).toEqual(detail.selection);
  expect(intent.requestedAction?.action).toBe("set_availability");
  expect(store.length).toBe(0);
  expect(consumeAssistantIntent(store, account, scenario, now + 2)).toBeNull();
  const context: Context = { actor: { user_id: account, organization_id: "synthetic-org", role: "customer", permissions: [], crew_id: null, connection_ids: [] }, scenario, plan: {}, cases: [{ case_id: "synthetic-case" }], connections: [], work_items: [] };
  let opened = 0;
  openRequestedAction(context, intent.requestedAction!, new Set(), () => { opened++; });
  expect(opened).toBe(1);
  expect(() => openRequestedAction({ ...context, cases: [] }, intent.requestedAction!, new Set(), () => { opened++; })).toThrow("no longer available");
  expect(opened).toBe(1);
});

test("account and scenario keys cannot consume one another's intent", () => {
  const store = storage();
  storeAssistantIntent(store, account, scenario, detail, now);
  expect(consumeAssistantIntent(store, "another-account", scenario, now)).toBeNull();
  expect(consumeAssistantIntent(store, account, "another-scenario", now)).toBeNull();
  expect(consumeAssistantIntent(store, account, scenario, now)).not.toBeNull();
});

test("storing a new handoff replaces the previous one without touching unrelated storage", () => {
  const store = storage();
  store.setItem("theme", "dark");
  storeAssistantIntent(store, account, scenario, detail, now);
  storeAssistantIntent(store, "synthetic-other", "synthetic-winter", { selection: {} }, now);
  expect(store.length).toBe(2);
  expect(store.getItem("theme")).toBe("dark");
  expect(consumeAssistantIntent(store, account, scenario, now)).toBeNull();
});

test("expiry at ten minutes and future timestamps fail closed and are removed", () => {
  for (const offset of [ASSISTANT_INTENT_MAX_AGE, ASSISTANT_INTENT_MAX_AGE + 1, -1]) {
    const store = storage();
    storeAssistantIntent(store, account, scenario, detail, now);
    expect(consumeAssistantIntent(store, account, scenario, now + offset)).toBeNull();
    expect(store.length).toBe(0);
  }
  const store = storage();
  storeAssistantIntent(store, account, scenario, detail, now);
  expect(consumeAssistantIntent(store, account, scenario, now + ASSISTANT_INTENT_MAX_AGE - 1)).not.toBeNull();
});

test("tampered identity, scenario, age, malformed JSON and actions cannot be consumed", () => {
  const base = { version: 1, accountId: account, scenario, createdAt: now, intent: detail };
  for (const saved of [null, [], { ...base, accountId: "foreign-account" }, { ...base, scenario: "foreign-scenario" }, { ...base, version: 2 }, { ...base, createdAt: "yesterday" }, { ...base, intent: { action: "delete_everything", data: {} } }, { ...base, intent: { scenario: "foreign-scenario" } }]) {
    const store = storage();
    store.setItem(assistantIntentKey(account, scenario), JSON.stringify(saved));
    expect(consumeAssistantIntent(store, account, scenario, now)).toBeNull();
    expect(store.length).toBe(0);
  }
  const store = storage();
  store.setItem(assistantIntentKey(account, scenario), "{");
  expect(consumeAssistantIntent(store, account, scenario, now)).toBeNull();
});

test("invalid scope, scenario mismatch and oversized data cannot replace an intent", () => {
  const store = storage();
  expect(storeAssistantIntent(store, "", scenario, detail, now)).toBe(false);
  expect(storeAssistantIntent(store, account, scenario, { ...detail, scenario: "foreign-scenario" }, now)).toBe(false);
  expect(storeAssistantIntent(store, account, scenario, { ...detail, data: { reason: "x".repeat(20_000) } }, now)).toBe(false);
  expect(store.length).toBe(0);
  expect(assistantDashboardPath("synthetic & #scenario")).toBe("/app?scenariu=synthetic%20%26%20%23scenario#assistant");
});
