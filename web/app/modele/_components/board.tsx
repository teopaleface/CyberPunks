import type { ReactNode } from "react";
import { BotIcon, FileSearchIcon, Layers2Icon } from "lucide-react";
import { Card, Pill, type Tone } from "@/components/ds";
import { ChipGrid, type GridCard } from "@/components/misc/chip-grid";
import { Disclosure } from "@/components/simple/disclosure";
import { SyntheticGlyph } from "@/components/shell/provenance";
import type { ModelReport, Source } from "@/lib/contracts";
import { fmtDec, fmtLei, plural } from "@/lib/format";
import { SOURCE_ORDER } from "@/lib/sources";
import { ErrorAnalysis } from "./error-analysis";
import { compare, fmtMetric } from "./metric-labels";
import { englishMetricMeta as metricMeta } from "./report-english";

const TONE_OF: Record<Source, Tone> = { A: "blue", B: "violet", C: "amber" };
const NAME: Record<Source, string> = { A: "Meter anomalies", B: "Storm outages", C: "Maximum voltage" };
const CONTEXT: Record<Source, string> = {
  A: "London anomalies have synthetic labels. The primary subtle-anomaly test excludes obvious defects.",
  B: "Outage ranking on held-out test data. PR-AUC measures ranking across thresholds, not individual outage probability.",
  C: "Synthetic grid data with real weather. 1 pu is nominal voltage; the overvoltage limit is 1.10 pu.",
};

function fmtVal(key: string, value: number): string {
  if (/precision|recall/.test(key)) return `${fmtDec(value * 100, 1)}%`;
  if (/auc/.test(key)) return fmtDec(value, 3);
  return fmtMetric(key, value);
}

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj | null => (v && typeof v === "object" && !Array.isArray(v) ? v as Obj : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);
const STRATEGY_NAME: Record<string, string> = {
  agent: "Agent", top_k_scor: "Top K by score", primul_venit: "First come, first served", aleator: "Random", doar_contoare: "Meters only",
};
const strategyName = (key: string) => STRATEGY_NAME[key] ?? key.replaceAll("_", " ");

function ModelComparison({ source, report }: { source: Source; report: ModelReport | null }) {
  const key = report?.primary_metric ?? "";
  const meta = metricMeta(key);
  const model = num(report?.metrics[key]);
  const baseline = num(report?.baseline_metrics[key]);
  const sgcc = source === "A" && key !== "sgcc_precision_at_k" ? num(report?.metrics.sgcc_precision_at_k) : null;
  const sgccBase = num(report?.baseline_metrics.sgcc_precision_at_k);
  return (
    <Card title={NAME[source]} icon={Layers2Icon} iconTone="grey" action={<Pill tone={TONE_OF[source]}>Model {source}</Pill>} className="h-full">
      {report ? (
        <>
          <h3 className="min-h-12 text-[15px] leading-relaxed text-ink-soft">{meta.label}</h3>
          <dl className="mt-3 grid grid-cols-2 gap-3">
            <div className="min-w-0 rounded-xl border border-rule bg-surface-2 p-3">
              <dt className="text-[13px] text-ink-soft">Model</dt>
              <dd className="mt-1 text-[clamp(1.25rem,2vw,1.875rem)] leading-tight font-[650] tabular-nums">{model !== null ? fmtVal(key, model) : "Unavailable"}</dd>
            </div>
            <div className="min-w-0 p-3">
              <dt className="text-[13px] text-ink-soft">Simple baseline</dt>
              <dd className="mt-1 text-[clamp(1.25rem,2vw,1.875rem)] leading-tight font-[550] tabular-nums">{baseline !== null ? fmtVal(key, baseline) : "Unavailable"}</dd>
            </div>
          </dl>
          <p className="mt-3 text-[14px] font-[550]">
            {meta.better === "higher" ? "Higher is better." : meta.better === "lower" ? "Lower is better." : "See the metric definition in the report."} {model !== null && baseline !== null ? compare(meta, model, baseline) === 1 ? "Model performs better." : compare(meta, model, baseline) === -1 ? "Baseline performs better." : "No measured advantage." : ""}
          </p>
          {sgcc !== null && sgccBase !== null ? (
            <p className="mt-3 border-t border-rule pt-3 text-[14px] leading-relaxed">
              <span className="font-[600]">SGCC real theft labels</span>: {fmtVal("sgcc_precision_at_k", sgcc)} vs. {fmtVal("sgcc_precision_at_k", sgccBase)} baseline. A separately trained model.
            </p>
          ) : null}
          <p className="mt-3 text-[13px] leading-relaxed text-ink-soft">{CONTEXT[source]}</p>
        </>
      ) : <p className="text-[15px] text-ink-soft">Evaluation report unavailable. No result is assumed.</p>}
    </Card>
  );
}

export function ModelsBoard({ bundle, planner, analysisBy, balance }: {
  bundle: Record<Source, ModelReport | null>;
  planner: Obj | null;
  analysisBy: Record<Source, string | null>;
  balance: ReactNode;
}) {
  const all = obj(obj(planner?.main)?.strategies);
  const strategies = Object.entries(all ?? {})
    .map(([key, value]) => ({ key, data: obj(value), net: num(obj(value)?.net_value_lei_per_day) }))
    .filter((s): s is typeof s & { net: number } => s.net !== null)
    .sort((a, b) => b.net - a.net);
  const agent = strategies.find((s) => s.key === "agent");
  const best = strategies.find((s) => s.key !== "agent");
  const days = num(obj(planner?.main)?.days);
  const synthetic = planner?.synthetic !== false;
  const cards: GridCard[] = SOURCE_ORDER.map((source) => ({
    id: `model-${source}`, tags: [source, "reguli"], span: "lg:col-span-4", filteredSpan: "lg:col-span-6",
    node: <ModelComparison source={source} report={bundle[source]} />,
  }));

  cards.push({
    id: "agent", tags: ["agent"], span: "lg:col-span-12", filteredSpan: "lg:col-span-12",
    node: (
      <Card title="Agent strategy comparison" icon={BotIcon} iconTone="grey" action={<Pill tone="grey">Simulation</Pill>}>
        {agent && best ? (
          <>
            <div className="grid gap-5 md:grid-cols-[1fr_1fr_1.2fr]">
              <dl>
                <dt className="text-[14px] text-ink-soft">Agent, simulated net value per day</dt>
                <dd className="mt-2 text-[28px] leading-tight font-[650] tabular-nums">{fmtLei(agent.net)}</dd>
              </dl>
              <dl>
                <dt className="text-[14px] text-ink-soft">Best simple strategy, per day</dt>
                <dd className="mt-2 text-[28px] leading-tight font-[550] tabular-nums">{fmtLei(best.net)}</dd>
                <dd className="mt-1 text-[14px] text-ink-soft">{strategyName(best.key)}</dd>
              </dl>
              <p className="text-[14px] leading-relaxed text-ink-soft">
                {synthetic ? <SyntheticGlyph size={14} /> : null}{" "}
                {days ? plural(days, "simulated day", "simulated days") : "Simulation"}. {synthetic ? "Synthetic world with known outcomes." : "Evaluation on the report's data."} These values are simulated, not realised savings or revenue.
              </p>
            </div>
            <Disclosure title="Simulation outcomes" hint="All strategies, visits, urgency and distance" className="mt-5">
              <div className="max-w-full overflow-x-auto">
                <table className="w-full min-w-[680px] text-left text-[14px]">
                  <caption className="mb-3 text-left text-ink-soft">Net value and distance are per day. Unnecessary visits and missed urgent cases are totals over the simulation.</caption>
                  <thead><tr className="border-b border-rule"><th scope="col" className="py-3 pr-4">Strategy</th><th scope="col" className="px-3 text-right">Net value, RON/day</th><th scope="col" className="px-3 text-right">Unnecessary visits</th><th scope="col" className="px-3 text-right">Missed urgent cases</th><th scope="col" className="pl-3 text-right">Km/day</th></tr></thead>
                  <tbody>{strategies.map((s) => (
                    <tr key={s.key} className="border-b border-rule last:border-0">
                      <th scope="row" className="py-3 pr-4 font-[550]">{strategyName(s.key)}</th>
                      <td className="px-3 text-right tabular-nums">{fmtLei(s.net)}</td>
                      {(["useless_visits_total", "urgent_missed_total", "km_per_day"] as const).map((k) => <td key={k} className="px-3 text-right tabular-nums">{num(s.data?.[k]) !== null ? fmtDec(num(s.data?.[k])!, k === "km_per_day" ? 1 : 0) : "Unavailable"}</td>)}
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              <div className="mt-4 max-w-full overflow-x-auto">
                <table className="w-full min-w-[480px] text-left text-[14px]">
                  <caption className="mb-2 text-left text-ink-soft">Simulated gross value recovered by source over the full evaluation period. Separate from daily net value above.</caption>
                  <thead><tr><th scope="col" className="py-2">Strategy</th>{SOURCE_ORDER.map((s) => <th scope="col" key={s} className="px-3 text-right">Source {s}</th>)}</tr></thead>
                  <tbody>{[agent, best].map((s) => <tr key={s.key} className="border-t border-rule"><th scope="row" className="py-3 font-[500]">{strategyName(s.key)}</th>{SOURCE_ORDER.map((source) => { const n = num(obj(s.data?.value_by_source_lei)?.[source]); return <td key={source} className="px-3 text-right tabular-nums">{n !== null ? fmtLei(n) : "Unavailable"}</td>; })}</tr>)}</tbody>
                </table>
              </div>
            </Disclosure>
          </>
        ) : <p className="text-[15px] text-ink-soft">Agent evaluation not published yet. No economic outcome is assumed.</p>}
      </Card>
    ),
  });
  for (const source of SOURCE_ORDER) {
    cards.push({
      id: `errors-${source}`, tags: [source, "erori"], span: "lg:col-span-4", filteredSpan: "lg:col-span-6",
      node: (
        <Card title={`Model ${source}: known limits`} icon={FileSearchIcon} iconTone="grey">
          {analysisBy[source] ? <ErrorAnalysis source={source} md={analysisBy[source]!} /> : <p className="text-[14px] text-ink-soft">Error analysis not published yet.</p>}
        </Card>
      ),
    });
  }
  cards.push({ id: "balance", tags: ["A", "reguli", "erori"], span: "lg:col-span-12", filteredSpan: "lg:col-span-12", node: balance });
  return <ChipGrid label="Filter model evaluation" columns="lg:grid-cols-12" chips={[
    { id: "A", label: "Model A", tone: "blue" }, { id: "B", label: "Model B", tone: "violet" }, { id: "C", label: "Model C", tone: "amber" },
    { id: "reguli", label: "Simple rules" }, { id: "agent", label: "Agent" }, { id: "erori", label: "Error analysis" },
  ]} cards={cards} />;
}
