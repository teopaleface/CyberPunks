import {
  BotIcon,
  FileSearchIcon,
  FlaskConicalIcon,
  Layers2Icon,
} from "lucide-react";
import { Card, Pill, TONE, type Tone } from "@/components/ds";
import { ChipGrid, type GridCard } from "@/components/misc/chip-grid";
import { SyntheticGlyph } from "@/components/shell/provenance";
import type { ModelReport, Source } from "@/lib/contracts";
import { fmtDec, fmtInt, fmtLei, plural } from "@/lib/format";
import { SOURCE_ORDER } from "@/lib/sources";
import { ErrorAnalysis } from "./error-analysis";
import { fmtMetric } from "./metric-labels";
import { englishMetricMeta as metricMeta } from "./report-english";

const TONE_OF: Record<Source, Tone> = { A: "blue", B: "violet", C: "amber" };

/** Procente pentru precizie și recall („62,5%”), formatul metricii pentru restul. */
function fmtVal(key: string, v: number): string {
  if (/precision|recall/.test(key)) {
    if (v >= 0.995) return "over 99%";
    const p = Math.round(v * 1000) / 10;
    return `${Number.isInteger(p) ? fmtInt(p) : fmtDec(p, 1)}%`;
  }
  return fmtMetric(key, v);
}

interface Row {
  id: string;
  source: Source;
  key: string;
  label: string;
  model: number;
  base: number;
  better: "higher" | "lower";
}

/** Rândurile reale: metrica principală a fiecărui raport și, la A, precizia pe furturi reale (SGCC), cu valoarea baseline-ului. */
function rowsOf(bundle: Record<Source, ModelReport | null>): Row[] {
  const out: Row[] = [];
  for (const s of SOURCE_ORDER) {
    const r = bundle[s];
    if (!r) continue;
    const key = r.primary_metric;
    const m = r.metrics[key];
    const b = r.baseline_metrics[key];
    const meta = metricMeta(key);
    if (typeof m === "number" && typeof b === "number" && meta.better !== "none" && meta.better !== "target") {
      out.push({ id: `${s}-${key}`, source: s, key, label: meta.label, model: m, base: b, better: meta.better });
    }
    if (s === "A" && key !== "sgcc_precision_at_k") {
      const sm = r.metrics.sgcc_precision_at_k;
      const sb = r.baseline_metrics.sgcc_precision_at_k;
      if (typeof sm === "number" && typeof sb === "number") {
        out.push({ id: "A-sgcc", source: "A", key: "sgcc_precision_at_k", label: metricMeta("sgcc_precision_at_k").label, model: sm, base: sb, better: "higher" });
      }
    }
  }
  return out;
}

type Obj = Record<string, unknown>;
const obj = (v: unknown): Obj | null => (v && typeof v === "object" && !Array.isArray(v) ? (v as Obj) : null);
const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

interface Strat {
  key: string;
  s: Obj;
  net: number;
}

function strategies(planner: Obj | null): Strat[] {
  const all = obj(obj(planner?.main)?.strategies);
  if (!all) return [];
  return Object.entries(all)
    .map(([key, v]) => ({ key, s: obj(v) ?? {}, net: num(obj(v)?.net_value_lei_per_day) ?? NaN }))
    .filter((x) => Number.isFinite(x.net))
    .sort((a, b) => b.net - a.net);
}

const STRATEGY_NAME: Record<string, string> = {
  agent: "Agent",
  top_k_scor: "top K by score",
  primul_venit: "first come, first served",
  aleator: "random",
  doar_contoare: "meters only",
};
const strategyName = (k: string) => STRATEGY_NAME[k] ?? k.replaceAll("_", " ");

function SourcePill({ s, children }: { s: Source; children: React.ReactNode }) {
  return (
    <Pill tone={TONE_OF[s]} size="md" className="min-w-[64px] justify-center">
      {children}
    </Pill>
  );
}

function Pale({ children }: { children?: React.ReactNode }) {
  return (
    <span className="inline-flex min-w-[84px] justify-center rounded-full border border-rule bg-surface-2 whitespace-nowrap px-2.5 py-1 text-[14px] text-ink-soft">{children ?? "—"}</span>
  );
}

function ValPill({ tone, children }: { tone: Tone; children: React.ReactNode }) {
  const t = TONE[tone];
  return <span className={`inline-flex min-w-[84px] justify-center rounded-full border px-2.5 py-1 text-[14.5px] whitespace-nowrap font-[560] tabular-nums ${t.text} ${t.bg} ${t.border}`}>{children}</span>;
}

export function ModelsBoard({
  bundle,
  planner,
  analysisBy,
}: {
  bundle: Record<Source, ModelReport | null>;
  planner: Record<string, unknown> | null;
  analysisBy: Record<Source, string | null>;
}) {
  const rows = rowsOf(bundle);
  const strat = strategies(planner);
  const agent = strat.find((x) => x.key === "agent");
  const best = strat.find((x) => x.key !== "agent");
  const gainPct = agent && best && best.net > 0 ? ((agent.net - best.net) / best.net) * 100 : null;
  const days = num(obj(planner?.main)?.days);
  const synthetic = planner?.synthetic !== false;
  const cards: GridCard[] = [];
  const cardClass = "rounded-[18px]";

  // 1. Performanță
  if (rows.length) {
    cards.push({
      id: "performanta",
      tags: ["A", "B", "C", "reguli"],
      span: "lg:col-span-6",
      node: (
        <Card title="Models vs. simple rules" icon={Layers2Icon} className={cardClass}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] border-separate border-spacing-y-1.5 text-[15px]">
              <caption className="sr-only">Primary metric on the same test set</caption>
              <thead>
                <tr>
                  <th scope="col" className="pr-3 pb-1 text-left text-[14.5px] font-[600]">
                    Metric
                  </th>
                  {SOURCE_ORDER.map((s) => (
                    <th key={s} scope="col" className="px-1 pb-1 text-center">
                      <SourcePill s={s}>
                        <span translate="no">{s}</span>
                      </SourcePill>
                    </th>
                  ))}
                  <th scope="col" className="px-1 pb-1 text-center">
                    <Pill tone="grey" className="min-w-[64px] justify-center">
                      Rules
                    </Pill>
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.id}>
                    <th scope="row" className="pr-3 text-left text-[14.5px] leading-snug font-[450]" title={r.key}>
                      {r.label}
                    </th>
                    {SOURCE_ORDER.map((s) => (
                      <td key={s} className="px-1 text-center">
                        {s === r.source ? <ValPill tone={TONE_OF[s]}>{fmtVal(r.key, r.model)}</ValPill> : <Pale />}
                      </td>
                    ))}
                    <td className="px-1 text-center">
                      <Pale>{fmtVal(r.key, r.base)}</Pale>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[13.5px] text-ink-soft">
            Rules are each model&apos;s baseline on the same test data. A dash means the metric is unavailable.
          </p>
        </Card>
      ),
    });
  }

  // 2. Agentul: câștig net
  if (agent && best) {
    cards.push({
      id: "agent",
      tags: ["agent"],
      span: "lg:col-span-3",
      node: (
        <Card title="Agent net gain" icon={BotIcon} className={cardClass} bodyClassName="flex h-full flex-col px-5 pt-3 pb-5">
          {gainPct !== null ? (
            <p className="mt-2 text-center text-[44px] leading-none font-[750] tracking-[-0.03em] text-ok-ink tabular-nums">
              {gainPct >= 0 ? "+" : "−"}
              {fmtDec(Math.abs(gainPct), 0)}% <span className="text-[30px]">net/day</span>
            </p>
          ) : null}
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <span className="rounded-[12px] border border-ok/60 bg-ok/10 text-ok-ink px-4 py-2 text-[20px] font-[650] tabular-nums">{fmtLei(agent.net)}/day</span>
            <span className="text-[14px] text-ink-soft">vs.</span>
            <span className="rounded-[12px] border border-rule px-4 py-2 text-[20px] font-[650] tabular-nums">{fmtLei(best.net)}/day</span>
          </div>
          <p className="mt-4 text-center text-[14.5px] leading-snug text-ink-soft">
            Agent vs. the best simple strategy ({strategyName(best.key)}).
          </p>
          <p className="mt-4 flex items-center justify-center gap-2 text-center text-[14.5px] text-ink-soft">
            {synthetic ? <SyntheticGlyph size={14} /> : null}
            Simulation: {days ? plural(days, "day", "days") : "multiple days"}, {synthetic ? "synthetic world" : "real data"}
          </p>
        </Card>
      ),
    });
  } else {
    cards.push({
      id: "agent",
      tags: ["agent"],
      span: "lg:col-span-3",
      node: (
        <Card title="Agent net gain" icon={BotIcon} className={cardClass}>
          <p className="text-[15.5px] leading-relaxed text-ink-soft">
            Agent evaluation not published yet (<span translate="no">reports/planner/agent_eval.json</span>).
          </p>
        </Card>
      ),
    });
  }

  // 5. Analiza erorilor
  const withAnalysis = SOURCE_ORDER.filter((s) => analysisBy[s]);
  cards.push({
    id: "erori",
    tags: ["erori", ...withAnalysis],
    span: "lg:col-span-7",
    node: (
      <Card title="Error analysis" icon={FileSearchIcon} className={cardClass}>
        {withAnalysis.length ? (
          <div className="flex max-h-[430px] flex-col gap-6 overflow-y-auto pr-1" tabIndex={0} role="region" aria-label="Error analysis by model">
            {withAnalysis.map((s) => (
              <ErrorAnalysis key={s} source={s} md={analysisBy[s]!} />
            ))}
          </div>
        ) : (
          <p className="text-[15px] text-ink-soft">
            No error analysis published yet (<span translate="no">reports/&lt;A|B|C&gt;/error_analysis.md</span>).
          </p>
        )}
      </Card>
    ),
  });

  // 6. Simulare
  if (agent && best) {
    const bySrc = (s: Obj) => obj(s.value_by_source_lei);
    const av = bySrc(agent.s);
    const bv = bySrc(best.s);
    const total = (v: Obj | null) => (v ? Object.values(v).reduce<number>((t, x) => t + (num(x) ?? 0), 0) : null);
    const stat = (label: string, a: number | null, b: number | null, f: (n: number) => string) =>
      a !== null && b !== null ? { label, a: f(a), b: f(b) } : null;
    const lines = [
      stat("Net gain per day", agent.net, best.net, (n) => fmtLei(n)),
      stat("Unnecessary visits", num(agent.s.useless_visits_total), num(best.s.useless_visits_total), fmtInt),
      stat("Missed urgent cases", num(agent.s.urgent_missed_total), num(best.s.urgent_missed_total), fmtInt),
      stat("Km per day", num(agent.s.km_per_day), num(best.s.km_per_day), fmtInt),
    ].filter((x): x is { label: string; a: string; b: string } => x !== null);
    cards.push({
      id: "simulare",
      tags: ["agent"],
      span: "lg:col-span-6",
      node: (
        <Card title={`Simulation summary for ${days ? plural(days, "day", "days") : "multiple days"}`} icon={FlaskConicalIcon} className={cardClass}>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[480px] border-separate border-spacing-y-1.5 text-[15px]">
              <caption className="sr-only">Agent and best simple strategy by work source</caption>
              <thead>
                <tr>
                  <th scope="col" className="pr-3 pb-1 text-left text-[14.5px] font-[600]">
                    Value recovered
                  </th>
                  {SOURCE_ORDER.map((s) => (
                    <th key={s} scope="col" className="px-1 pb-1 text-center">
                      <SourcePill s={s}>
                        <span translate="no">{s}</span>
                      </SourcePill>
                    </th>
                  ))}
                  <th scope="col" className="px-1 pb-1 text-center">
                    <Pill tone="grey" className="min-w-[64px] justify-center">
                      Total
                    </Pill>
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: "Agent", v: av, bold: true },
                  { name: `Rules: ${strategyName(best.key)}`, v: bv, bold: false },
                ].map((r) => (
                  <tr key={r.name}>
                    <th scope="row" className={`pr-3 text-left text-[14.5px] ${r.bold ? "font-[650]" : "font-[450]"}`}>
                      {r.name}
                    </th>
                    {SOURCE_ORDER.map((s) => {
                      const v = num(r.v?.[s]);
                      return (
                        <td key={s} className="px-1 text-center">
                          {v === null ? <Pale /> : <ValPill tone={TONE_OF[s]}>{fmtLei(v)}</ValPill>}
                        </td>
                      );
                    })}
                    <td className="px-1 text-center">{total(r.v) === null ? <Pale /> : <Pale>{fmtLei(total(r.v) ?? 0)}</Pale>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {lines.length ? (
            <dl className="mt-3 grid grid-cols-[minmax(0,1fr)_auto_auto] gap-x-5 text-[14.5px]">
              <dt className="sr-only">Indicator</dt>
              <dd className="sr-only">Agent / simple rule</dd>
              {lines.map((l) => (
                <div key={l.label} className="col-span-3 grid grid-cols-subgrid items-center border-t border-rule py-2">
                  <dt className="text-ink-soft">{l.label}</dt>
                  <dd className="font-[650] tabular-nums">{l.a}</dd>
                  <dd className="text-ink-soft tabular-nums">vs. {l.b}</dd>
                </div>
              ))}
            </dl>
          ) : null}
          <p className="mt-2 flex items-center gap-2 text-[13.5px] text-ink-soft">
            {synthetic ? <SyntheticGlyph size={14} /> : null}
            {synthetic ? "Synthetic data from a simulated world with known outcomes." : "Real data."}
          </p>
        </Card>
      ),
    });
  }

  return (
    <ChipGrid
      label="Filter cards"
      columns="lg:grid-cols-12"
      chips={[
        { id: "A", label: "Model A", tone: "blue" },
        { id: "B", label: "Model B", tone: "violet" },
        { id: "C", label: "Model C", tone: "amber" },
        { id: "reguli", label: "Simple rules" },
        { id: "agent", label: "Agent" },
        { id: "erori", label: "Error analysis" },
      ]}
      cards={cards}
    />
  );
}
