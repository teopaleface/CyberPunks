import { expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import type { Context, WorkspaceAccount } from "@/lib/operations/types";
import { RoleList, RoleOverview } from "./role-overview";
import { Workspace } from "./workspace";
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
test("assistant renders functional text and consented voice without page chrome or role data", () => {
  const html = renderToStaticMarkup(
    <Workspace
      account={account}
      presentation="assistant"
      scenario="synthetic-scenario"
    />,
  );
  expect(html).toContain("Message Daybreak");
  expect(html).toContain("Talk to Daybreak");
  expect(html).toContain("I agree to send");
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
  expect(html).toContain("Your service");
  expect(html).toContain("Your connections");
  expect(html).toContain("Your cases");
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
  expect(html).toContain("Meter inspection · MTR-7");
  expect(html).not.toContain("MTR-8");
  expect(html).toContain("1 of 3");
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
