import { englishText } from "@/lib/english";
import { cn } from "cn";
import { SyntheticGlyph } from "@/components/shell/provenance";
import type { ModelReport, Source } from "@/lib/contracts";
import { fmtMoment, fmtPercent, plural, sentence } from "@/lib/format";
import { markerSvg } from "@/lib/marker-svg";
import { SOURCES } from "@/lib/sources";
import { CopyCommand } from "./copy-command";
import { englishMetricMeta as metricMeta, englishMetricExplanation as explainFor, englishMetricDelta as deltaSentence, englishReportText } from "./report-english";
import {
  EXPECTED_CMD,
  EXTERNAL_DATASET,
  compare,
  fmtMetric,
  fmtTick,
  niceAxis,
  splitBaseline,
  splitCitation,
} from "./metric-labels";

/** Ce problemă rezolvă fiecare model, cum o spune dispecerul. */
const PROBLEM: Record<Source, string> = {
  A: "Faulty or tampered meters",
  B: "Storm outage risk",
  C: "Prosumer overvoltage",
};

const SYNTHETIC_WORD = /SINTETIC/i;

/** Un model: antetul, comparația cu baseline-ul, setul de test, toate metricile și comanda. */
export function ModelColumn({ source, report, hasAnalysis }: { source: Source; report: ModelReport | null; hasAnalysis: boolean }) {
  const meta = SOURCES[source];
  return (
    <section aria-labelledby={`model-${source}`} className="min-w-0">
      <header className="flex items-center gap-3">
        <span className="size-9 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source }) }} />
        <div className="min-w-0">
          <h2 id={`model-${source}`} className="text-[22px] leading-tight font-[650]">
            {englishText(meta.name)}
          </h2>
          <p className="text-[15px] text-muted-foreground">{PROBLEM[source]}</p>
        </div>
      </header>
      {report ? <ReportBody source={source} report={report} hasAnalysis={hasAnalysis} /> : <MissingReport source={source} />}
    </section>
  );
}

/** Contoare: validarea pe furturi reale (SGCC), sub metrica principală. Referința e regula simplă pe același set. */
function SgccLine({ metrics, baseline }: { metrics: Record<string, number>; baseline: Record<string, number> }) {
  const m = metrics.sgcc_precision_at_k;
  const b = typeof metrics.sgcc_vee_precision_at_k === "number" ? metrics.sgcc_vee_precision_at_k : baseline.sgcc_precision_at_k;
  if (typeof m !== "number" || typeof b !== "number") return null;
  return (
    <p className="mt-2.5 border-t border-rule pt-2.5 text-[15px] leading-snug">
      <b className="font-[620]">Real theft cases with SGCC labels:</b> precision in the top K {fmtMetric("sgcc_precision_at_k", m)}, compared with {fmtMetric("sgcc_precision_at_k", b)} for the simple rule.
    </p>
  );
}

function ReportBody({ source, report: r, hasAnalysis }: { source: Source; report: ModelReport; hasAnalysis: boolean }) {
  const external = r.dataset.filter((d) => EXTERNAL_DATASET.test(d)).map((d) => splitCitation(englishReportText(d)).name);
  const baseline = splitBaseline(r.baseline_id);
  const baselineId = r.baseline_id.split(/\s*\(/, 1)[0];
  const key = r.primary_metric;
  const pm = metricMeta(key);
  const model = r.metrics[key];
  const base = r.baseline_metrics[key];
  const shared = [key, ...Object.keys(r.metrics).filter((k) => k !== key && typeof r.baseline_metrics[k] === "number")].filter(
    (k) => typeof r.metrics[k] === "number" && typeof r.baseline_metrics[k] === "number",
  );
  const only = Object.keys(r.metrics).filter((k) => typeof r.baseline_metrics[k] !== "number" && typeof r.metrics[k] === "number");
  const prevalence = key === "pr_auc" && typeof r.metrics.prevalence === "number" ? r.metrics.prevalence : null;

  return (
    <>
      <ul className="mt-3 flex flex-wrap gap-2 text-[14px]">
        {external.length ? (
          <li className="rounded-[4px] border border-ink px-2.5 py-1 font-[560]" title={`Public datasets: ${external.join(", ")}`}>
            Validated on external data
          </li>
        ) : null}
        <li className="flex items-center gap-2 rounded-[4px] border border-rule px-2.5 py-1">
          {r.synthetic_share > 0 ? (
            <>
              <SyntheticGlyph size={14} />
              Synthetic data: {fmtPercent(r.synthetic_share)} of the test set
            </>
          ) : (
            "No synthetic test data"
          )}
        </li>
      </ul>
      <p className="mt-2 text-[14px] text-muted-foreground">
        <span className="dense font-[560] text-ink">{r.model_version}</span>, evaluated {fmtMoment(r.created_at)}
      </p>

      {/* metrica principală: modelul față de baseline, pe aceeași axă */}
      <div className="mt-4 border-y border-rule bg-panel px-4 pt-3.5 pb-4">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <h3 className="text-[17px] font-[650]">{pm.label}</h3>
          <span className="text-[13.5px] text-muted-foreground">primary metric</span>
        </div>
        {explainFor(source, key) ? <p className="mt-1 text-[14.5px] leading-snug text-muted-foreground">{explainFor(source, key)}</p> : null}
        {typeof model === "number" && typeof base === "number" ? (
          <>
            <HeroBars metric={key} model={model} baseline={base} modelId={r.model_id} baselineId={baselineId} prevalence={prevalence} />
            <p className="mt-2.5 text-[17px] leading-snug font-[620]">{deltaSentence(key, pm, model, base)}</p>
            {source === "A" && !key.startsWith("sgcc_") ? <SgccLine metrics={r.metrics} baseline={r.baseline_metrics} /> : null}
          </>
        ) : (
          <p className="mt-3 text-[15px] text-muted-foreground">Primary metric missing from the report.</p>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-[112px_minmax(0,1fr)] gap-x-4 text-[15px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-2 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-2 [&>dt]:text-[14px] [&>dt]:text-muted-foreground">
        <dt>Test set</dt>
        <dd>
          {sentence(englishReportText(r.split))}
          <span className="mt-0.5 block text-muted-foreground">{plural(r.test_size, "example", "examples")}, unseen during training.</span>
        </dd>
        <dt>Baseline</dt>
        <dd>
          <span className="dense font-[560]">{baselineId}</span>
          {baseline.detail ? <span className="block text-muted-foreground">{sentence(englishReportText(baseline.detail))}</span> : r.baseline_id !== baselineId ? <span className="block text-muted-foreground">{englishReportText(r.baseline_id.slice(baselineId.length))}</span> : null}
        </dd>
        <dt>Prediction target</dt>
        <dd>{sentence(englishReportText(r.task))}</dd>
      </dl>

      <h3 className="mt-5 text-[16px] font-[650]">All metrics vs. baseline</h3>
      <table className="mt-1.5 w-full border-collapse text-[14.5px]">
        <thead>
          <tr className="text-[13.5px] text-muted-foreground">
            <th scope="col" className="py-1.5 pr-2 text-left font-[500]">
              Metric
            </th>
            <th scope="col" className="px-2 py-1.5 text-right font-[500]">
              Model
            </th>
            <th scope="col" className="px-2 py-1.5 text-right font-[500]">
              Baseline
            </th>
            <th scope="col" className="py-1.5 pl-2 text-right font-[500]">
              Difference
            </th>
          </tr>
        </thead>
        <tbody>
          {shared.map((k) => {
            const m = r.metrics[k];
            const b = r.baseline_metrics[k];
            const meta = metricMeta(k);
            const c = compare(meta, m, b);
            const diff = m - b;
            return (
              <tr key={k} className="border-t border-rule align-baseline">
                <th scope="row" className="py-1.5 pr-2 text-left font-[450]" title={k}>
                  {meta.label}
                  {k === key ? <span className="text-muted-foreground">, primary</span> : null}
                </th>
                <td className={cn("px-2 py-1.5 text-right whitespace-nowrap tabular-nums", c === 1 && "font-[700]")}>{fmtMetric(k, m)}</td>
                <td className={cn("px-2 py-1.5 text-right whitespace-nowrap tabular-nums", c === -1 ? "font-[700]" : "text-muted-foreground")}>
                  {fmtMetric(k, b)}
                </td>
                <td className="py-1.5 pl-2 text-right whitespace-nowrap text-muted-foreground tabular-nums">
                  {diff === 0 ? "0" : `${diff > 0 ? "+" : "−"}${fmtMetric(k, Math.abs(diff))}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-1.5 text-[13.5px] text-muted-foreground">Bold marks the better value. Difference is model minus baseline.</p>

      {only.length ? (
        <details className="group mt-3 border-y border-rule">
          <summary className="cursor-pointer list-none py-2.5 text-[15px] font-[560] marker:hidden">
            <span className="mr-2 inline-block text-muted-foreground transition-transform duration-150 group-open:rotate-90" aria-hidden="true">
              ›
            </span>
            {only.length === 1 ? "One additional metric without a baseline" : `Additional ${plural(only.length, "metric", "metrics")} without a baseline`}
          </summary>
          <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 pb-2 text-[14.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1.5 [&>dd]:text-right [&>dd]:tabular-nums [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1.5">
            {only.map((k) => (
              <div key={k} className="contents">
                <dt title={k}>{metricMeta(k).label}</dt>
                <dd className="whitespace-nowrap">{fmtMetric(k, r.metrics[k])}</dd>
              </div>
            ))}
          </dl>
        </details>
      ) : null}

      <h3 className="mt-5 text-[16px] font-[650]">Data sources</h3>
      <ul className="mt-1.5 space-y-2 text-[14.5px] leading-snug">
        {r.dataset.map((d) => {
          const { name, rest } = splitCitation(englishReportText(d));
          return (
            <li key={d} className="flex gap-2">
              <span className="mt-[3px] w-[14px] shrink-0" aria-hidden={!SYNTHETIC_WORD.test(d)}>
                {SYNTHETIC_WORD.test(d) ? <SyntheticGlyph size={14} /> : null}
              </span>
              <span className="min-w-0">
                <span className="font-[600]">{name}</span>
                {rest ? <span className="text-muted-foreground">, {rest}</span> : null}
                {SYNTHETIC_WORD.test(d) ? <span className="sr-only"> (contains synthetic data)</span> : null}
              </span>
            </li>
          );
        })}
      </ul>

      <h3 className="mt-5 text-[16px] font-[650]">Reproduce results</h3>
      <div className="mt-1.5">
        <CopyCommand cmd={r.reproduce_cmd} />
      </div>
      <p className="mt-3 text-[14.5px]">
        {hasAnalysis ? (
          <a href={`#erori-${source}`} className="font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink">
            Error analysis below
          </a>
        ) : (
          <span className="text-muted-foreground">
            Error analysis not published yet (<span className="dense">reports/{source}/error_analysis.md</span>).
          </span>
        )}
      </p>
    </>
  );
}

const LABEL_COL = 128;
const VALUE_COL = 150;

/** Două bare pe aceeași axă de la zero: modelul (închis) și baseline-ul (gri), cu valorile scrise. */
function HeroBars({
  metric,
  model,
  baseline,
  modelId,
  baselineId,
  prevalence,
}: {
  metric: string;
  model: number;
  baseline: number;
  modelId: string;
  baselineId: string;
  prevalence: number | null;
}) {
  const bounded = !/_lei$|_pu$|seconds|_pct$|_kwh_day$/.test(metric) && Math.max(model, baseline) <= 1;
  const axis = niceAxis(Math.max(model, baseline, prevalence ?? 0));
  const top = bounded ? Math.min(axis.max, 1) : axis.max;
  const ticks = axis.ticks.filter((t) => t <= top + 1e-9);
  const pct = (v: number) => `${(Math.max(0, Math.min(1, v / top)) * 100).toFixed(2)}%`;
  const rows = [
    { name: "Model", id: modelId, v: model, color: "var(--ink)" },
    { name: "Baseline", id: baselineId, v: baseline, color: "var(--idle)" },
  ];
  const grid = { gridTemplateColumns: `${LABEL_COL}px minmax(0,1fr) ${VALUE_COL}px` };
  const plot = { left: LABEL_COL + 12, right: VALUE_COL + 12 };

  return (
    <figure className="mt-3" aria-label={`${metricMeta(metric).label}: model ${fmtMetric(metric, model)}, baseline ${fmtMetric(metric, baseline)}`}>
      <div className="relative">
        <div className="pointer-events-none absolute inset-y-0" style={plot} aria-hidden="true">
          {ticks.map((t) => (
            <span key={t} className="absolute inset-y-0 w-px bg-grid" style={{ left: pct(t) }} />
          ))}
          {prevalence != null ? (
            <span className="absolute -top-1 -bottom-1 border-l border-dashed border-ink" style={{ left: pct(prevalence) }} />
          ) : null}
        </div>
        <ul className="relative">
          {rows.map((row) => (
            <li key={row.name} className="grid items-center gap-x-3 py-1.5" style={grid} title={`${row.name} ${row.id}: ${fmtMetric(metric, row.v)}`}>
              <span className="min-w-0">
                <span className="block text-[15px] leading-tight font-[600]">{row.name}</span>
                <span className="dense block truncate text-[13px] text-muted-foreground">{row.id}</span>
              </span>
              <span className="relative h-[22px]" aria-hidden="true">
                <i className="absolute inset-y-0 left-0 rounded-r-[4px]" style={{ width: pct(row.v), background: row.color }} />
              </span>
              <HeroValue text={fmtMetric(metric, row.v)} />
            </li>
          ))}
        </ul>
      </div>
      <div className="grid gap-x-3" style={grid} aria-hidden="true">
        <span />
        <span className="relative h-5 text-[13px] text-muted-foreground tabular-nums">
          {ticks.map((t, i) => (
            <span
              key={t}
              className={cn("absolute top-1 whitespace-nowrap", i === 0 ? "" : i === ticks.length - 1 ? "-translate-x-full" : "-translate-x-1/2")}
              style={{ left: pct(t) }}
            >
              {fmtTick(t)}
            </span>
          ))}
        </span>
      </div>
      {prevalence != null ? (
        <figcaption className="mt-1 text-[13.5px] text-muted-foreground">
          Dotted line shows random ordering, equal to prevalence ({fmtMetric("prevalence", prevalence)}).
        </figcaption>
      ) : null}
    </figure>
  );
}

/** Valoarea mare a barei; unitatea (pu, lei, s) mai mică, pe același rând. */
function HeroValue({ text }: { text: string }) {
  const m = /^(.*?)(\s(?:pu|lei|s|kWh))$/.exec(text);
  return (
    <span className="text-right leading-none whitespace-nowrap">
      <span className="num-wide text-[24px]">{m ? m[1] : text}</span>
      {m ? <span className="text-[15px] text-muted-foreground">{m[2]}</span> : null}
    </span>
  );
}

function MissingReport({ source }: { source: Source }) {
  return (
    <div className="mt-4 border-y border-rule bg-panel px-4 py-5">
      <p className="text-[17px] leading-snug font-[620]">Evaluation report for model {source} not published yet.</p>
      <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
        Metrics will appear once the report is published, with test data, baseline comparisons and reproduction commands.
      </p>
      <p className="mt-3 text-[14.5px]">
        Expected file: <span className="dense">reports/{source}/metrics.json</span>, generated with:
      </p>
      <div className="mt-1.5">
        <CopyCommand cmd={EXPECTED_CMD[source]} />
      </div>
    </div>
  );
}
