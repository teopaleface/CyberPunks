/** Compile the immutable, public demo order inputs before the Worker starts. */
import { mock } from "bun:test";
import path from "node:path";
import { writeFileSync } from "node:fs";
// These framework guards have no runtime context in this isolated build process.
mock.module("server-only", () => ({}));
mock.module("next/headers", () => ({ cookies: () => { throw new Error("Build must not read user cookies"); } }));
process.env.DATA_SOURCE = "demo";
process.env.DATA_ASSETS = "0";
process.env.REPO_ROOT = path.resolve(import.meta.dir, "../..");
const { loadShellInfo, loadScenarios } = await import("../lib/server/queries");
const scenarios = await loadScenarios();
const output: Record<string, unknown> = {};
for (const scenario of scenarios.data) {
  const { info, view } = await loadShellInfo(scenario.id);
  if (!view.data || view.source !== "demo") throw new Error(`Missing complete demo: ${scenario.id}`);
  const data = view.data;
  const ids = new Set(data.routes.flatMap((r) => r.stops.map((s) => s.work_item_id)));
  output[scenario.id] = { info, data: {
    plan: { plan_date: data.plan.plan_date },
    routes: data.routes,
    workItemsById: Object.fromEntries([...ids].map((id) => [id, data.workItemsById[id]])),
    decisionsByWorkItemId: Object.fromEntries([...ids].map((id) => [id, data.decisionsByWorkItemId[id]])),
  }};
}
writeFileSync(path.resolve(import.meta.dir, "../lib/generated/order-pages.json"), JSON.stringify(output));
console.log(`Compiled immutable order inputs for ${Object.keys(output).length} scenarios`);
