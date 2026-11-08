import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import type { Context, Row } from "@/lib/operations/types";
import {
  assignedVisits,
  caseNextStep,
  caseStatus,
  dashboardTitle,
  fieldFindingCount,
  isActiveCase,
  matchesDashboardQuery,
  newestCases,
  nextApprovedVisit,
  routeIsApproved,
  verifiedTimeline,
} from "./role-dashboard-model";
import { RoleList, RoleOverview } from "./role-overview";

// Synthetic fixtures mirror operations/service.py's role-scoped response shape.
function syntheticContext(): Context {
  return {
    actor: {
      user_id: "synthetic-customer",
      role: "customer",
      organization_id: "synthetic-org",
      crew_id: null,
      permissions: [],
      connection_ids: ["synthetic-connection"],
    },
    scenario: "synthetic-scenario",
    plan: { plan_date: "2025-07-08", approved: false },
    connections: [
      {
        connection_id: "synthetic-connection",
        label: "Home connection",
        meter_id: "MTR-001",
      },
    ],
    cases: [
      {
        case_id: "2ee680c1-59fe-4f6c-b032-de80217f0ce7",
        connection_id: "synthetic-connection",
        symptom: "The display is stuck",
        status: "awaiting_decision",
        created_at: "2025-07-08T08:00:00Z",
      },
    ],
    work_items: [],
    events: [],
    synthetic: true,
    next_stop: null,
    next_stop_status: "awaiting_approval",
  };
}
function syntheticTechnician(): Context {
  const context = syntheticContext();
  const workId = "synthetic-work";
  return {
    ...context,
    actor: { ...context.actor, role: "technician", crew_id: "synthetic-crew" },
    connections: [],
    cases: [{ ...context.cases[0], work_item_id: workId }],
    work_items: [{ work_item_id: workId, source: "A", asset_id: "MTR-001" }],
    plan: {
      ...context.plan,
      // Crew approval alone is sufficient. The entire plan can remain unapproved.
      approvals: [{ crew_id: "synthetic-crew", stale: false }],
      routes: [
        {
          crew_id: "synthetic-crew",
          stops: [{ work_item_id: workId, eta: "10:30" }],
        },
      ],
    },
    next_stop: { work_item_id: workId, eta: "10:30" },
    next_stop_status: "approved_plan",
  };
}
const idle = () => {
  throw new Error("Static rendering must not perform an action.");
};

describe("dashboard evidence and scoped routes", () => {
  test("assigned visits follow the scoped route order before unscheduled work", () => {
    const context = syntheticTechnician();
    context.work_items = [{ work_item_id: "unscheduled" }, { work_item_id: "second" }, ...context.work_items];
    context.plan.routes = [{ crew_id: "synthetic-crew", stops: [{ work_item_id: "synthetic-work", eta: "10:30" }, { work_item_id: "second", eta: "11:20" }] }];
    expect(assignedVisits(context).map((item) => item.work_item_id)).toEqual(["synthetic-work", "second", "unscheduled"]);
  });
  test("uses the backend's nested crew route and next_stop with a current crew approval", () => {
    const context = syntheticTechnician();
    const visits = assignedVisits(context);
    expect(routeIsApproved(context)).toBe(true);
    expect(visits[0].planned_start).toBe("10:30");
    expect(nextApprovedVisit(context, visits)?.work_item_id).toBe(
      "synthetic-work",
    );
    expect(context.work_items[0].planned_start).toBeUndefined();
    const html = renderToStaticMarkup(
      <RoleOverview context={context} role="technician" onRefresh={idle} />,
    );
    expect(html).toContain("Next approved visit");
    expect(html).toContain("Planned 10:30");
    expect(html).toContain("Meter inspection · MTR-001");
  });
  test("never substitutes a first assignment for a missing, unapproved or out-of-scope next stop", () => {
    const context = syntheticTechnician();
    const visits = assignedVisits(context);
    expect(
      nextApprovedVisit({ ...context, next_stop: null }, visits),
    ).toBeNull();
    expect(
      nextApprovedVisit(
        {
          ...context,
          next_stop: { work_item_id: "outside-scope", eta: "12:00" },
        },
        visits,
      ),
    ).toBeNull();
    const pending = {
      ...context,
      next_stop_status: "awaiting_approval",
      plan: {
        ...context.plan,
        approvals: [{ crew_id: "synthetic-crew", stale: true }],
      },
    };
    expect(routeIsApproved(pending)).toBe(false);
    expect(nextApprovedVisit(pending, visits)).toBeNull();
    expect(
      renderToStaticMarkup(
        <RoleOverview context={pending} role="technician" onRefresh={idle} />,
      ),
    ).not.toContain("Next approved visit");
  });
  test("route arrival times come only from matching scoped crew stops", () => {
    const context = syntheticTechnician();
    const route = {
      crew_id: "another-crew",
      stops: [{ work_item_id: "synthetic-work", eta: "13:00" }],
    };
    expect(
      assignedVisits({ ...context, routes: [route] })[0].planned_start,
    ).toBeUndefined();
    expect(
      assignedVisits({
        ...context,
        routes: [
          {
            ...route,
            crew_id: "synthetic-crew",
            stops: [{ work_item_id: "synthetic-work", arrival: "11:20" }],
          },
        ],
      })[0].planned_start,
    ).toBe("11:20");
  });
  test("confirmed findings do not close cases and no access still requires access", () => {
    for (const outcome of [
      "confirmed",
      "not_found",
      "other_problem",
      "no_access",
    ]) {
      const context = syntheticContext();
      context.cases[0] = {
        ...context.cases[0],
        status: "verification_after_visit",
        verdict: { outcome, repair_confirmed: false },
      };
      expect(isActiveCase(context.cases[0])).toBe(true);
      const html = renderToStaticMarkup(
        <RoleOverview context={context} role="customer" onRefresh={idle} />,
      );
      expect(html).not.toContain(">Resolved<");
      expect(html).not.toContain(">Closed<");
      expect(html).not.toContain("awaiting_decision");
      if (outcome === "confirmed")
        expect(html).toContain("Repair is not confirmed.");
      if (outcome === "no_access") {
        expect(caseStatus(context.cases[0]).label).toBe("Access needed");
        expect(caseNextStep(context.cases[0]).short).toBe("Arrange access");
        expect(html).toContain("case remains open");
      }
    }
  });
  test("counts distinct assigned visits with findings, including cases linked by backend events", () => {
    const context = syntheticTechnician();
    context.cases.push({
      case_id: "synthetic-second-case",
      work_item_id: "synthetic-work",
      verdict: { outcome: "no_access" },
    });
    context.events = [
      { action: "record_verdict", case_id: context.cases[0].case_id },
      { action: "record_verdict", case_id: "synthetic-second-case" },
    ];
    expect(fieldFindingCount(context)).toBe(1);
    context.cases.push({
      work_item_id: "outside-scope",
      verdict: { outcome: "confirmed" },
    });
    expect(fieldFindingCount(context)).toBe(1);
  });
  test("the timeline uses recorded events, deduplicates them and excludes other cases", () => {
    const context = syntheticContext();
    const item = context.cases[0];
    const event = {
      event_id: "synthetic-event",
      action: "set_availability",
      case_id: item.case_id,
      created_at: "2025-07-08T09:00:00Z",
    };
    context.events = [
      event,
      {
        event_id: "outside-case",
        case_id: "another-case",
        action: "approve_plan",
        created_at: "2025-07-08T10:00:00Z",
      },
    ];
    item.events = [event];
    expect(verifiedTimeline(context, item).map((entry) => entry.title)).toEqual(
      ["Report received", "Availability shared"],
    );
    expect(
      verifiedTimeline(
        { ...context, events: [] },
        { symptom: "No dated evidence" },
      ),
    ).toEqual([]);
  });
  test("newest case sorting preserves the input and presentation-only cleanup preserves meaningful synthetic wording", () => {
    const items: Row[] = [
      { case_id: "older", created_at: "2025-07-01" },
      { case_id: "newer", created_at: "2025-07-08" },
    ];
    expect(newestCases(items).map((item) => item.case_id)).toEqual([
      "newer",
      "older",
    ]);
    expect(items[0].case_id).toBe("older");
    const item = { symptom: "Synthetic UI validation: The lights flicker" };
    expect(dashboardTitle(item)).toBe("The lights flicker");
    expect(item.symptom).toBe("Synthetic UI validation: The lights flicker");
    expect(
      dashboardTitle({
        symptom: "Synthetic acceptance test a1b2c3: The meter display is stuck",
      }),
    ).toBe("The meter display is stuck");
    expect(
      dashboardTitle({ symptom: "Synthetic material near the meter" }),
    ).toBe("Synthetic material near the meter");
  });
});

describe("dashboard layout contract", () => {
  test("customer has a single primary action, one focus, compact cases and the inline assistant slot", () => {
    const context = syntheticContext();
    const html = renderToStaticMarkup(
      <RoleOverview
        context={context}
        role="customer"
        onRefresh={idle}
        assistant={<section id="assistant">Synthetic inline assistant</section>}
      />,
    );
    expect(html).toContain("Service dashboard");
    expect(html.match(/id="cases"/g)?.length).toBe(1);
    expect(html.match(/id="connection"/g)?.length).toBe(1);
    expect(html.match(/id="assistant"/g)?.length).toBe(1);
    expect(html.match(/Report a problem/g)?.length).toBe(1);
    expect(html.match(/rd-focus-card/g)?.length).toBe(1);
    expect(html.indexOf("rd-focus")).toBeLessThan(
      html.indexOf('id="assistant"'),
    );
    expect(html.indexOf('id="assistant"')).toBeLessThan(
      html.indexOf('id="cases"'),
    );
    expect(html).not.toContain(context.cases[0].case_id as string);
    expect(html).not.toContain("Model evidence");
    expect(html).not.toContain('role="dialog"');
  });
  test("technician has unique route, work, case and supplied assistant anchors", () => {
    const html = renderToStaticMarkup(
      <RoleOverview
        context={syntheticTechnician()}
        role="technician"
        onRefresh={idle}
        assistant={<section id="assistant">Synthetic inline assistant</section>}
      />,
    );
    for (const id of ["route", "work", "cases", "assistant"])
      expect(html.match(new RegExp(`id="${id}"`, "g"))?.length).toBe(1);
    expect(html).toContain("Shift dashboard");
    expect(html).not.toContain('id="connection"');
  });
  test("work lists expose the full count and four rows per page; later rows remain searchable", () => {
    const items = Array.from({ length: 21 }, (_, i) => ({
      work_item_id: `synthetic-work-${i}`,
      asset_id: `MTR-${i}`,
      source: "A",
    }));
    const html = renderToStaticMarkup(
      <RoleList
        title="Assigned visits"
        kind="work"
        items={items}
        context={syntheticTechnician()}
      />,
    );
    expect(html.match(/class="rd-item-select"/g)?.length).toBe(4);
    expect(html).toContain("1 of 6");
    expect(html).toContain("of 21");
    expect(html).toContain("Search by description or reference");
    expect(html).not.toContain("MTR-4");
    expect(matchesDashboardQuery(items[20], "MTR-20")).toBe(true);
    expect(
      matchesDashboardQuery({ status: "access_blocked" }, "access needed"),
    ).toBe(true);
  });
});
