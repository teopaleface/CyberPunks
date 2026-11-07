import { cn } from "cn";
import { SyntheticGlyph } from "@/components/shell/provenance";
import type { ModelReport, Source } from "@/lib/contracts";
import { fmtMoment, fmtPercent, plural, sentence } from "@/lib/format";
import { markerSvg } from "@/lib/marker-svg";
import { SOURCES } from "@/lib/sources";
import { CopyCommand } from "./copy-command";
import {
  EXPECTED_CMD,
  EXTERNAL_DATASET,
  compare,
  deltaSentence,
  fmtMetric,
  fmtTick,
  metricMeta,
  niceAxis,
  splitBaseline,
  splitCitation,
} from "./metric-labels";

/** Ce problemă rezolvă fiecare model, cum o spune dispecerul. */
const PROBLEM: Record<Source, string> = {
  A: "Contoare defecte sau manipulate",
  B: "Risc de avarii la furtună",
  C: "Depășiri de tensiune la prosumatori",
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
            {meta.name}
          </h2>
          <p className="text-[15px] text-muted-foreground">{PROBLEM[source]}</p>
        </div>
      </header>
      {report ? <ReportBody source={source} report={report} hasAnalysis={hasAnalysis} /> : <MissingReport source={source} />}
    </section>
  );
}

function ReportBody({ source, report: r, hasAnalysis }: { source: Source; report: ModelReport; hasAnalysis: boolean }) {
  const external = r.dataset.filter((d) => EXTERNAL_DATASET.test(d)).map((d) => splitCitation(d).name);
  const baseline = splitBaseline(r.baseline_id);
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
          <li className="rounded-[4px] border border-ink px-2.5 py-1 font-[560]" title={`Seturi publice: ${external.join(", ")}`}>
            Model validat pe date externe
          </li>
        ) : null}
        <li className="flex items-center gap-2 rounded-[4px] border border-rule px-2.5 py-1">
          {r.synthetic_share > 0 ? (
            <>
              <SyntheticGlyph size={14} />
              Date sintetice: {fmtPercent(r.synthetic_share)} din setul de test
            </>
          ) : (
            "Fără date sintetice în setul de test"
          )}
        </li>
      </ul>
      <p className="mt-2 text-[14px] text-muted-foreground">
        <span className="dense font-[560] text-ink">{r.model_version}</span>, evaluat {fmtMoment(r.created_at)}
      </p>

      {/* metrica principală: modelul față de baseline, pe aceeași axă */}
      <div className="mt-4 border-y border-rule bg-panel px-4 pt-3.5 pb-4">
        <div className="flex flex-wrap items-baseline justify-between gap-x-3">
          <h3 className="text-[17px] font-[650]">{pm.label}</h3>
          <span className="text-[13.5px] text-muted-foreground">metrica principală</span>
        </div>
        {pm.explain ? <p className="mt-1 text-[14.5px] leading-snug text-muted-foreground">{pm.explain}</p> : null}
        {typeof model === "number" && typeof base === "number" ? (
          <>
            <HeroBars metric={key} model={model} baseline={base} modelId={r.model_id} baselineId={baseline.short} prevalence={prevalence} />
            <p className="mt-2.5 text-[17px] leading-snug font-[620]">{deltaSentence(key, pm, model, base)}</p>
          </>
        ) : (
          <p className="mt-3 text-[15px] text-muted-foreground">Metrica principală lipsește din raport.</p>
        )}
      </div>

      <dl className="mt-4 grid grid-cols-[112px_minmax(0,1fr)] gap-x-4 text-[15px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-2 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-2 [&>dt]:text-[14px] [&>dt]:text-muted-foreground">
        <dt>Setul de test</dt>
        <dd>
          {sentence(r.split)}
          <span className="mt-0.5 block text-muted-foreground">{plural(r.test_size, "exemplu", "exemple")}, nevăzute la antrenare.</span>
        </dd>
        <dt>Baseline-ul</dt>
        <dd>
          <span className="dense font-[560]">{baseline.short}</span>
          {baseline.detail ? <span className="block text-muted-foreground">{sentence(baseline.detail)}</span> : null}
        </dd>
        <dt>Ce prezice</dt>
        <dd>{sentence(r.task)}</dd>
      </dl>

      <h3 className="mt-5 text-[16px] font-[650]">Toate metricile față de baseline</h3>
      <table className="mt-1.5 w-full border-collapse text-[14.5px]">
        <thead>
          <tr className="text-[13.5px] text-muted-foreground">
            <th scope="col" className="py-1.5 pr-2 text-left font-[500]">
              Metrica
            </th>
            <th scope="col" className="px-2 py-1.5 text-right font-[500]">
              Modelul
            </th>
            <th scope="col" className="px-2 py-1.5 text-right font-[500]">
              Baseline
            </th>
            <th scope="col" className="py-1.5 pl-2 text-right font-[500]">
              Diferența
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
                  {k === key ? <span className="text-muted-foreground">, principală</span> : null}
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
      <p className="mt-1.5 text-[13.5px] text-muted-foreground">Cu gros: valoarea mai bună din rând. Diferența e modelul minus baseline-ul.</p>

      {only.length ? (
        <details className="group mt-3 border-y border-rule">
          <summary className="cursor-pointer list-none py-2.5 text-[15px] font-[560] marker:hidden">
            <span className="mr-2 inline-block text-muted-foreground transition-transform duration-150 group-open:rotate-90" aria-hidden="true">
              ›
            </span>
            {only.length === 1 ? "Încă o măsurătoare, fără pereche la baseline" : `Încă ${plural(only.length, "măsurătoare", "măsurători")}, fără pereche la baseline`}
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

      <h3 className="mt-5 text-[16px] font-[650]">Sursele de date</h3>
      <ul className="mt-1.5 space-y-2 text-[14.5px] leading-snug">
        {r.dataset.map((d) => {
          const { name, rest } = splitCitation(d);
          return (
            <li key={d} className="flex gap-2">
              <span className="mt-[3px] w-[14px] shrink-0" aria-hidden={!SYNTHETIC_WORD.test(d)}>
                {SYNTHETIC_WORD.test(d) ? <SyntheticGlyph size={14} /> : null}
              </span>
              <span className="min-w-0">
                <span className="font-[600]">{name}</span>
                {rest ? <span className="text-muted-foreground">, {rest}</span> : null}
                {SYNTHETIC_WORD.test(d) ? <span className="sr-only"> (conține date sintetice)</span> : null}
              </span>
            </li>
          );
        })}
      </ul>

      <h3 className="mt-5 text-[16px] font-[650]">Refă cifrele</h3>
      <div className="mt-1.5">
        <CopyCommand cmd={r.reproduce_cmd} />
      </div>
      <p className="mt-3 text-[14.5px]">
        {hasAnalysis ? (
          <a href={`#erori-${source}`} className="font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink">
            Unde greșește modelul: analiza erorilor, mai jos
          </a>
        ) : (
          <span className="text-muted-foreground">
            Analiza erorilor nu e publicată încă (<span className="dense">reports/{source}/error_analysis.md</span>).
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
    { name: "Modelul", id: modelId, v: model, color: "var(--ink)" },
    { name: "Baseline-ul", id: baselineId, v: baseline, color: "var(--idle)" },
  ];
  const grid = { gridTemplateColumns: `${LABEL_COL}px minmax(0,1fr) ${VALUE_COL}px` };
  const plot = { left: LABEL_COL + 12, right: VALUE_COL + 12 };

  return (
    <figure className="mt-3" aria-label={`${metricMeta(metric).label}: modelul ${fmtMetric(metric, model)}, baseline-ul ${fmtMetric(metric, baseline)}`}>
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
          Linia punctată: o ordine la întâmplare, egală cu prevalența ({fmtMetric("prevalence", prevalence)}).
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
      <p className="text-[17px] leading-snug font-[620]">Raportul de evaluare al modelului {source} nu e publicat încă.</p>
      <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
        Va conține metrica principală față de un baseline simplu, toate metricile pe un set de test separat, sursele de date citate, cum e
        ales setul de test, cât din el e sintetic și comanda care refăce cifrele. Până atunci nu arătăm nicio cifră.
      </p>
      <p className="mt-3 text-[14.5px]">
        Fișierul așteptat: <span className="dense">reports/{source}/metrics.json</span>, scris de comanda:
      </p>
      <div className="mt-1.5">
        <CopyCommand cmd={EXPECTED_CMD[source]} />
      </div>
    </div>
  );
}
