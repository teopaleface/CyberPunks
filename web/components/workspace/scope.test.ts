import { expect, test } from "bun:test";
import { SessionExpired } from "@/lib/operations/client";
import type {
  Context,
  Proposal,
  WorkspaceAccount,
} from "@/lib/operations/types";
import {
  assertProposalScenario,
  assertScope,
  itemTitle,
  openRequestedAction,
  readableDate,
  requestAssistant,
  resolveSelection,
  selectionKey,
  selectionOf,
  validateRequestedAction,
} from "./scope";

const membership = {
  role: "dispatcher" as const,
  organization_id: "synthetic-org",
  crew_id: null,
  connection_ids: [],
  permissions: ["approve_plan", "review_work_item", "create_case"],
};
const account: WorkspaceAccount = {
  id: "synthetic-actor",
  name: "Synthetic dispatcher",
  email: "synthetic@example.test",
  membership,
};
const context: Context = {
  actor: {
    ...membership,
    user_id: account.id,
    organization_id: "synthetic-org",
  },
  scenario: "synthetic-scenario",
  plan: { plan_id: "synthetic-plan" },
  connections: [{ connection_id: "synthetic-connection" }],
  work_items: [
    { work_item_id: "synthetic-work", asset_id: "MTR-012949", source: "A" },
  ],
  cases: [{ case_id: "synthetic-case", work_item_id: "synthetic-work" }],
};
test("selection checks every identifier against the current server scope", () => {
  expect(resolveSelection(context, { case_id: "synthetic-case" })).toBe(
    context.cases[0],
  );
  expect(() =>
    resolveSelection(context, {
      case_id: "synthetic-case",
      work_item_id: "outside-scope",
    }),
  ).toThrow("current scope");
  expect(() =>
    resolveSelection({ ...context, cases: [] }, { case_id: "synthetic-case" }),
  ).toThrow("current scope");
  expect(() => resolveSelection(context, { case_id: "" })).toThrow("invalid");
  expect(resolveSelection(context, {})).toBeNull();
});
test("row selection uses the primary object, without requiring related data hidden from a role", () => {
  expect(
    selectionOf({ case_id: "synthetic-case", work_item_id: "hidden-work" }),
  ).toEqual({ case_id: "synthetic-case" });
  expect(
    selectionKey({ case_id: "synthetic-case", work_item_id: "synthetic-work" }),
  ).toBe(
    selectionKey({ work_item_id: "synthetic-work", case_id: "synthetic-case" }),
  );
});
test("scope rejects changed accounts, roles, organization, crew and scenario", () => {
  expect(assertScope(context, account, context.scenario)).toBe(context);
  for (const actor of [
    { ...context.actor, user_id: "other" },
    { ...context.actor, organization_id: "other" },
    { ...context.actor, crew_id: "other" },
    { ...context.actor, role: "customer" as const },
  ]) {
    expect(() =>
      assertScope({ ...context, actor }, account, context.scenario),
    ).toThrow(SessionExpired);
  }
  expect(() => assertScope(context, account, "another-scenario")).toThrow(
    "different scenario",
  );
});
test("an action intent opens an editable form once per request ID without saving anything", () => {
  const seen = new Set<string>();
  const opened: unknown[] = [];
  const request = {
    action: "review_work_item" as const,
    data: { work_item_id: "synthetic-work", decision: "defer" },
    requestId: "synthetic-request",
  };
  const open = (...args: unknown[]) => opened.push(args);
  expect(openRequestedAction(context, request, seen, open)).toBe(true);
  expect(opened).toEqual([[request.action, request.data]]);
  expect(
    openRequestedAction(
      context,
      { ...request, data: { decision: "reject" } },
      seen,
      open,
    ),
  ).toBe(false);
  expect(opened).toHaveLength(1);
  expect(
    openRequestedAction(
      context,
      { ...request, requestId: "next-request" },
      seen,
      open,
    ),
  ).toBe(true);
});
test("invalid or unauthorized intents never open a form, including after a rerender", () => {
  const seen = new Set<string>();
  let opened = false;
  const request = {
    action: "review_work_item" as const,
    data: { work_item_id: "outside-scope" },
    requestId: "invalid-request",
  };
  expect(() =>
    openRequestedAction(context, request, seen, () => {
      opened = true;
    }),
  ).toThrow("current scope");
  expect(
    openRequestedAction(context, request, seen, () => {
      opened = true;
    }),
  ).toBe(false);
  expect(opened).toBe(false);
  expect(() =>
    validateRequestedAction(
      { ...context, actor: { ...context.actor, permissions: [] } },
      { ...request, data: {} },
    ),
  ).toThrow("unavailable");
  expect(() =>
    validateRequestedAction(context, {
      ...request,
      action: "record_verdict",
      data: {},
    }),
  ).toThrow("unavailable");
  expect(() =>
    validateRequestedAction(context, {
      ...request,
      action: "approve_plan",
      data: { plan_id: "old-plan" },
    }),
  ).toThrow("different plan");
});
test("linked drafts cannot be reviewed against a different scenario", () => {
  const proposal: Proposal = {
    proposal_id: "synthetic-proposal",
    scenario: context.scenario,
    action: "approve_plan",
    summary: "Synthetic plan",
    data: {},
    expires_at: "2026-11-08T10:00:00Z",
  };
  expect(assertProposalScenario(proposal, context.scenario)).toBe(proposal);
  expect(() => assertProposalScenario(proposal, "other")).toThrow(
    "different scenario",
  );
});
test("work titles distinguish actual work shapes and strip only known synthetic QA prefixes", () => {
  expect(itemTitle(context.work_items[0])).toBe(
    "Meter inspection · MTR-012949",
  );
  expect(itemTitle({ source: "C", asset_id: "PT-42" })).toBe(
    "Voltage inspection · PT-42",
  );
  const item = {
    symptom:
      "Synthetic acceptance test abc123: The meter display has stopped changing.",
  };
  expect(itemTitle(item)).toBe("The meter display has stopped changing.");
  expect(itemTitle({ symptom: "Synthetic UI validation: The meter display has stopped changing." })).toBe("The meter display has stopped changing.");
  expect(item.symptom).toStartWith("Synthetic acceptance test");
  expect(
    itemTitle({ symptom: "Synthetic acceptance test for the meter" }),
  ).toBe("Synthetic acceptance test for the meter");
});
test("dates show readable months while planned times stay compact", () => {
  expect(readableDate("2025-07-08")).toBe("8 Jul 2025");
  expect(readableDate("2026-11-08T10:30:00Z")).toContain("Nov 2026");
  expect(readableDate("13:20:00")).toBe("13:20");
  expect(readableDate(null)).toBe("Not available");
});
test("role selection dispatches a scoped assistant intent without invoking an operation", () => {
  const previous = globalThis.window;
  const target = new EventTarget();
  const received: unknown[] = [];
  target.addEventListener("daybreak:assistant", (event) =>
    received.push((event as CustomEvent).detail),
  );
  Object.defineProperty(globalThis, "window", {
    value: target,
    configurable: true,
  });
  try {
    requestAssistant(
      { case_id: "synthetic-case" },
      "set_availability",
      { case_id: "synthetic-case" },
      context.scenario,
    );
    expect(received).toEqual([
      {
        selection: { case_id: "synthetic-case" },
        action: "set_availability",
        data: { case_id: "synthetic-case" },
        scenario: context.scenario,
      },
    ]);
  } finally {
    Object.defineProperty(globalThis, "window", {
      value: previous,
      configurable: true,
    });
  }
});
