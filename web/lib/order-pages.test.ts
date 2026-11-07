import { mock, test, expect } from "bun:test";
mock.module("server-only", () => ({}));
import prepared from "./generated/order-pages.json";
import { getPlanView } from "./data";
import { buildOrder } from "./orders-view";
import { itemPlace, itemTitle } from "./plan-screen";
for (const [scenario, compiled] of Object.entries(prepared)) {
  test(`compiled ${scenario} preserves every route and order`, async () => {
    const result = await getPlanView(scenario, { mode: "demo" });
    const full = result.data!;
    expect(full).not.toBeNull();
    expect(compiled.info.planId).toBe(full.plan.plan_id);
    expect(compiled.info.counts.review).toBe(full.plan.decisions.filter(d => d.decision === "human_review").length);
    expect(JSON.stringify(compiled.data.routes)).toBe(JSON.stringify(full.routes));
    expect(Object.keys(compiled.data.workItemsById).sort()).toEqual([...new Set(full.routes.flatMap(r => r.stops.map(s => s.work_item_id)))].sort());
    for (const route of full.routes) {
      const subset = compiled.data as unknown as typeof full;
      expect(buildOrder(route, subset.workItemsById, subset.decisionsByWorkItemId, itemPlace, itemTitle))
        .toEqual(buildOrder(route, full.workItemsById, full.decisionsByWorkItemId, itemPlace, itemTitle));
    }
  });
}
