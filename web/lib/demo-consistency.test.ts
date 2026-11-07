import { expect, test } from "bun:test";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { readDemoMetrics } from "./data/files";
import { metricRows } from "./item-data";
import type { ModelReport } from "./contracts";

const root = process.env.REPO_ROOT!;
const json = async (file: string) => JSON.parse(await readFile(path.join(root, file), "utf8"));

test("landing figures and provenance match the console's saved demo plan", async () => {
  const [landing, plan] = await Promise.all([json("web/site/src/data/daybreak.json"), json("outputs/demo/plans/demo-vara/plan.json")]);
  expect(landing.planId).toBe(plan.plan_id);
  expect(landing.generatedAt).toBe(plan.generated_at);
  expect(landing.summary).toEqual(plan.summary);
  for (const source of ["A", "B", "C"]) {
    expect(landing.perSource[source].total).toBe(plan.decisions.filter((d: { work_item_id: string }) => d.work_item_id.startsWith(source + "-")).length);
  }
});

test("all four models use current reports consistently with the Python API", async () => {
  const bundle = await readDemoMetrics();
  for (const source of ["A", "B", "C", "bilant"] as const) {
    const report = await json(`reports/${source}/metrics.json`);
    expect(bundle?.data[source]?.model_version).toBe(report.model_version);
    expect(bundle?.data[source]?.metrics).toEqual(report.metrics);
  }
});

test("meter job scores do not headline overall precision inflated by obvious faults", async () => {
  const report: ModelReport = await json("reports/A/metrics.json");
  const rows = metricRows("A", report);
  expect(rows.some((r) => r.key === "subtle_precision_at_k")).toBe(true);
  expect(rows.some((r) => r.key === "sgcc_precision_at_k")).toBe(true);
  expect(rows.some((r) => r.key === "precision_at_k")).toBe(false);
});
