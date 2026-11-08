import { expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import type { Context, WorkspaceAccount } from "@/lib/operations/types";
import { RoleList, RoleOverview } from "./role-overview";
import { commandHeading, defaultAssistantSelection, Workspace } from "./workspace";
import { conversationSuggestions } from "./main-conversation";
const account: WorkspaceAccount = {
  id: "synthetic-user",
  email: "synthetic@example.test",
  name: "Synthetic customer",
  membership: {
    role: "customer",
    organization_id: "synthetic-org",
    crew_id: null,
    connection_ids: ["synthetic-connection"],
    permissions: [],
  },
};
const context: Context = {
  actor: {
    ...account.membership,
    user_id: account.id,
    organization_id: "synthetic-org",
  },
  scenario: "synthetic-scenario",
  plan: { plan_date: "2025-07-08" },
  connections: [
    { connection_id: "synthetic-connection", label: "Home connection" },
  ],
  cases: [
    {
      case_id: "synthetic-case",
      symptom: "The meter display is stuck",
      verdict: { outcome: "confirmed" },
    },
  ],
  work_items: [],
};
test("assistant defaults to text with a compact voice choice and no consent wall", () => {
  const html = renderToStaticMarkup(
    <Workspace
      account={account}
      presentation="assistant"
      scenario="synthetic-scenario"
    />,
  );
  expect(html).toContain("Message Daybreak");
  expect(html).toContain("Conversation mode");
  expect(html).toContain(">Text</button>");
  expect(html).toContain(">Voice</button>");
  expect(html).toContain('aria-pressed="true"');
  expect(html).not.toContain("Talk to Daybreak");
  expect(html).not.toContain("I agree to send");
  expect(html).toContain("press Confirm");
  for (const forbidden of [
    "<main",
    "<header",
    "<footer",
    "<h1",
    "YOUR SERVICE WORKSPACE",
    "Your connections",
    "Your cases",
    "SmartHack 2026",
    "Source:",
  ])
    expect(html).not.toContain(forbidden);
});
test("role presentation renders the console title and scoped lists without chat or standalone chrome", () => {
  const html = renderToStaticMarkup(
    <Workspace account={account} presentation="role" />,
  );
  expect(html).toContain("Service dashboard");
  expect(html).toContain("Your connections");
  expect(html).toContain("Recent cases");
  for (const forbidden of [
    "Message Daybreak",
    "Talk to Daybreak",
    "<main",
    "<footer",
    "db-brand",
    "db-chat",
  ])
    expect(html).not.toContain(forbidden);
});
test("customer data stays useful and findings never imply repair", () => {
  const html = renderToStaticMarkup(
    <RoleOverview
      context={context}
      role="customer"
      onRefresh={() => {
        throw new Error("render must remain idle");
      }}
    />,
  );
  expect(html).toContain("Home connection");
  expect(html).toContain("The meter display is stuck");
  expect(html).toContain("Repair is not confirmed");
  expect(html).toContain("Report a problem");
  expect(html).toContain("Share availability");
  expect(html).toContain("8 Jul 2025");
  expect(html).not.toContain("Work to review");
  expect(html).not.toContain("Model evidence");
});
test("large work queues are paginated and searchable, with distinct human work labels", () => {
  const items = Array.from({ length: 20 }, (_, i) => ({
    work_item_id: `synthetic-work-${i}`,
    asset_id: `MTR-${i}`,
    source: "A",
    asset_type: "meter",
  }));
  const html = renderToStaticMarkup(
    <RoleList
      title="Your assigned work"
      kind="work"
      items={items}
      context={context}
    />,
  );
  expect(html).toContain("Search by description or reference");
  expect(html).toContain("Meter inspection · MTR-0");
  expect(html).toContain("Meter inspection · MTR-3");
  expect(html).not.toContain("MTR-4");
  expect(html).toContain("1 of 5");
  expect(html).toContain("Next");
});
test("rendering an incoming action never confirms or posts a proposal", () => {
  const html = renderToStaticMarkup(
    <Workspace
      account={account}
      presentation="assistant"
      requestedAction={{
        action: "create_case",
        data: { connection_id: "synthetic-connection" },
        requestId: "synthetic-request",
      }}
    />,
  );
  expect(html).not.toContain('aria-label="Action proposal"');
  expect(html).not.toContain(">Confirm</button>");
});

test("assigned work keeps the planned arrival from the role-scoped route", () => {
  const tech: Context = {
    ...context,
    actor: { ...context.actor, role: "technician", crew_id: "synthetic-crew" },
    work_items: [
      { work_item_id: "synthetic-work", asset_id: "MTR-012949", source: "A" },
    ],
    plan: {
      ...context.plan,
      routes: [
        {
          crew_id: "synthetic-crew",
          stops: [
            { work_item_id: "synthetic-work", eta: "2025-07-08T10:30:00Z" },
          ],
        },
      ],
    },
  };
  const html = renderToStaticMarkup(
    <RoleOverview context={tech} role="technician" onRefresh={() => {}} />,
  );
  expect(html).toContain("Meter inspection · MTR-012949");
  expect(html).toContain("Planned 8 Jul 2025");
  expect(html).toContain("Record finding");
  expect(html).not.toContain("Review work");
});

test("role workspace passes exactly the supplied inline assistant slot", () => {
  const html = renderToStaticMarkup(<Workspace account={account} presentation="role" assistant={<section id="synthetic-assistant-slot">Inline assistant slot</section>} />);
  expect(html.match(/id="synthetic-assistant-slot"/g)).toHaveLength(1);
  expect(html).toContain("Inline assistant slot");
});

test("request states use human labels and never treat an uncertain result as saved", () => {
  expect(commandHeading("succeeded")).toBe("Saved");
  expect(commandHeading("processing")).toBe("Processing");
  expect(commandHeading("pending")).toBe("Processing");
  for (const status of ["reconciling", "failed", "unknown", ""]) expect(commandHeading(status)).toBe("Needs review");
  expect(commandHeading("cancelled")).toBe("Cancelled");
});

test("default context uses only the latest own case or the approved in-scope next visit", () => {
  expect(defaultAssistantSelection({ ...context, cases: [
    { case_id: "synthetic-old", created_at: "2025-07-07T10:00:00Z" },
    { case_id: "synthetic-latest", created_at: "2025-07-08T10:00:00Z" },
  ] })).toEqual({ case_id: "synthetic-latest" });
  const tech: Context = { ...context, actor: { ...context.actor, role: "technician" }, next_stop: { work_item_id: "synthetic-visit" }, next_stop_status: "approved_plan", work_items: [{ work_item_id: "synthetic-visit" }] };
  expect(defaultAssistantSelection(tech)).toEqual({ work_item_id: "synthetic-visit" });
  expect(defaultAssistantSelection({ ...tech, next_stop_status: "awaiting_approval" })).toBeUndefined();
  expect(defaultAssistantSelection({ ...tech, work_items: [] })).toBeUndefined();
  expect(defaultAssistantSelection({ ...context, actor: { ...context.actor, role: "dispatcher" } })).toBeUndefined();
});

test("main presentation contains only the conversation, with honest history and voice opt-in", () => {
  const html = renderToStaticMarkup(<Workspace account={account} presentation="main" scenario="synthetic-scenario" />);
  expect(html).toContain("What can I help you with?");
  expect(html).toContain("New chat");
  expect(html).toContain("No saved conversations yet.");
  expect(html).toContain('aria-label="Start voice"');
  expect(html).toContain("Report a problem");
  expect(html).toContain("press Confirm");
  for (const forbidden of ["Service dashboard", "Your connections", "Recent cases", "Model evidence", "Conversation mode", "Choose a case", "I agree to send", "Talk to Daybreak", "db-assistant-card", "db-role-view"]) expect(html).not.toContain(forbidden);
});

test("main role prompts stay relevant to each verified role", () => {
  expect(conversationSuggestions("customer")).toEqual(["Case update", "Report a problem", "Get help"]);
  expect(conversationSuggestions("technician")).toEqual(["Next visit", "Why this visit?", "Record a finding"]);
  expect(conversationSuggestions("dispatcher")).toEqual(["Review pending decisions", "Explain the plan", "Find a work item"]);
});

test("main proposal links and incoming forms remain idle until live scope and explicit review", () => {
  const html = renderToStaticMarkup(<Workspace account={account} presentation="main"
    linkedProposalId="11111111-1111-4111-8111-111111111111"
    requestedAction={{ action: "create_case", data: { connection_id: "synthetic-connection" }, requestId: "synthetic-request" }} />);
  expect(html).toContain("Loading your draft for review");
  expect(html).toContain("Back to chat");
  expect(html).not.toContain('aria-label="Action proposal"');
  expect(html).not.toContain(">Confirm</button>");
  expect(html).not.toContain("Review proposal</button>");
});
