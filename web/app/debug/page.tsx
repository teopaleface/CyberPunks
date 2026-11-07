import { englishText } from "@/lib/english";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import {
  getAudit,
  getConfig,
  getHealth,
  getMetrics,
  getPlan,
  getScenarios,
  getSeries,
  getWorkItem,
  getWorkItems,
  probeApi,
  type Sourced,
} from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";

export const metadata = { title: "Diagnostics · Dispatcher console" };

export default function DebugPage() {
  return (
    <main className="mx-auto w-full max-w-5xl space-y-6 p-6 text-sm">
      <header>
        <h1 className="text-xl font-semibold">Diagnostics</h1>
        <p>
          API health and data sources. <Link href="/app">Back</Link>
        </p>
      </header>
      <Suspense fallback={<p>Checking sources…</p>}>
        <DebugInfo />
      </Suspense>
    </main>
  );
}

function count(result: Sourced<unknown>): string {
  const data = result.data;
  if (data === null || data === undefined) return "none";
  if (Array.isArray(data)) return `${data.length} records`;
  return "yes";
}

async function DebugInfo() {
  await connection();
  const config = getConfig();
  const probe = await probeApi({ force: true });
  const scenario = config.defaultScenario;

  const [health, plan, workItems, audit, metrics, scenarios] = await Promise.all([
    getHealth(),
    getPlan(scenario),
    getWorkItems(scenario),
    getAudit(scenario),
    getMetrics(),
    getScenarios(),
  ]);
  const firstId = workItems.data[0]?.work_item_id;
  const [workItem, series] = firstId
    ? await Promise.all([getWorkItem(firstId, scenario), getSeries(firstId, scenario)])
    : [null, null];

  const rows: [string, Sourced<unknown> | null][] = [
    ["getHealth()", health],
    [`getPlan("${scenario}")`, plan],
    [`getWorkItems("${scenario}")`, workItems],
    [`getAudit("${scenario}")`, audit],
    [`getWorkItem("${firstId ?? "—"}")`, workItem],
    [`getSeries("${firstId ?? "—"}")`, series],
    ["getMetrics()", metrics],
    ["getScenarios()", scenarios],
  ];

  return (
    <>
      <section>
        <h2 className="font-semibold">Configuration</h2>
        <dl className="grid grid-cols-[max-content_1fr] gap-x-4">
          <dt>API_BASE</dt>
          <dd>{config.apiBase}</dd>
          <dt>DATA_SOURCE</dt>
          <dd>
            {config.dataSource}
            {config.invalidDataSource ? ` (unknown value "${config.invalidDataSource}")` : ""}
          </dd>
          <dt>REPO_ROOT</dt>
          <dd>{config.repoRoot}</dd>
          <dt>DEFAULT_SCENARIO</dt>
          <dd>{config.defaultScenario}</dd>
          <dt>Current data source</dt>
          <dd data-source={health.data.resolvedSource}>{health.data.resolvedSource}</dd>
        </dl>
      </section>

      <section>
        <h2 className="font-semibold">API</h2>
        <p>
          {probe.ok ? "Responding" : "Not responding"} ({probe.latencyMs} ms, checked at {probe.checkedAt})
          {probe.error ? ` · ${englishText(probe.error)}` : ""}
        </p>
        {probe.health ? <pre>{JSON.stringify(probe.health, null, 2)}</pre> : null}
        <p>
          Demo snapshot for &quot;{scenario}&quot;: {health.data.demoAvailable ? "yes" : "no"} · Fixtures:{" "}
          {health.data.fixturesAvailable ? "yes" : "no"}
        </p>
      </section>

      <section>
        <h2 className="font-semibold">Data source by function</h2>
        <table className="w-full text-left">
          <thead>
            <tr>
              <th>Function</th>
              <th>Source</th>
              <th>Data</th>
              <th>Reason</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([name, result]) => (
              <tr key={name} className="align-top">
                <td>{name}</td>
                <td data-source={result?.source}>{result ? englishText(SOURCE_LABEL_RO[result.source]) : "—"}</td>
                <td>{result ? count(result) : "—"}</td>
                <td>{englishText(result?.degradedReason ?? "")}</td>
                <td className="break-all">{englishText(result?.detail ?? "")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
