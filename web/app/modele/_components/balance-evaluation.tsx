import path from "node:path";
import { Card } from "@/components/ds";
import { Disclosure } from "@/components/simple/disclosure";
import type { ModelReport } from "@/lib/contracts";
import { REPO_ROOT } from "@/lib/data";
import { fmtDec, fmtInt, fmtMoment } from "@/lib/format";
import { CAUSE_LABELS } from "@/lib/prediction-confidence";
import { readText } from "@/lib/server/read-file";
import { CopyCommand } from "./copy-command";

const METRICS: Record<string, string> = {
  normal_mae_kwh_day: "Normal-loss error, kWh/day. Lower is better",
  diagnoza_macro_f1: "Cause diagnosis, macro F1. Higher is better",
  fuziune_precision_at_10: "Fusion precision in the top 10, simulated training population",
  fuziune_harta_v2_precision_at_10: "Fusion precision in the top 10, held-out map with simulated meter scores",
};

async function reportText(name: string) {
  try { return await readText(path.join(REPO_ROOT, "reports", "bilant", name)); }
  catch { return null; }
}

export async function BalanceEvaluation({ report }: { report: ModelReport | null }) {
  const [analysis, confusion] = await Promise.all([reportText("error_analysis.md"), reportText("diagnosis_confusion.csv")]);
  const csv = confusion?.trim().split(/\r?\n/).map((line) => line.split(","));
  const labels = csv?.[0]?.slice(1) ?? [];
  const rows = csv?.slice(1) ?? [];
  const validMatrix = labels.length === 6 && rows.length === labels.length && rows.every((r) => r.length === labels.length + 1 && r.slice(1).every((n) => Number.isFinite(Number(n)) && Number(n) >= 0));
  if (!report) return <Card title="Energy balance"><p>The energy-balance evaluation report is not available from this data source.</p></Card>;
  const headlineKeys = [...new Set(["normal_mae_kwh_day", "diagnoza_macro_f1", report.primary_metric])];
  return (
    <section id="model-bilant" className="mt-6 min-w-0 scroll-mt-6" aria-label="Energy-balance model evaluation">
      <Card title="Energy balance: loss and cause diagnosis">
        <p className="text-[15px] text-ink-soft">Synthetic network and fault labels. Validation on unseen substations; these results do not establish performance on PPC data.</p>
        <p className="mt-2 break-all text-[13px] text-muted-foreground">{report.model_version} · evaluated {fmtMoment(report.created_at)}</p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-[14px]">
            <caption className="sr-only">Energy balance compared with its baselines on the same test data</caption>
            <thead><tr><th className="py-2 pr-4">Metric</th><th className="px-2 text-right">Model</th><th className="px-2 text-right">Baseline</th></tr></thead>
            <tbody>{headlineKeys.map((key) => (
              <tr key={key} className="border-t border-rule"><th className="py-2 pr-4 font-normal">{METRICS[key] ?? key.replaceAll("_", " ")}</th><td className="px-2 text-right tabular-nums">{typeof report.metrics[key] === "number" ? fmtDec(report.metrics[key], 3) : "Unavailable"}</td><td className="px-2 text-right tabular-nums">{typeof report.baseline_metrics[key] === "number" ? fmtDec(report.baseline_metrics[key], 3) : "Unavailable"}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <p className="mt-3 text-[14px] text-ink-soft">Baselines: the physical I²R formula for normal loss, the rule table from the concept for diagnosis, and meter scores alone for fusion. Fusion experiments with simulated meter scores are separate from experiments with the actual meter model output.</p>
        <Disclosure title="Energy-balance test, errors and reproduction" hint="Six-class confusion matrix and source reports">
          <p className="text-[14px] text-ink-soft">The normal-loss test contains {fmtInt(report.metrics.normal_test_days ?? report.test_size)} substation-days across {fmtInt(report.metrics.normal_test_posts ?? 0)} held-out substations. Diagnosis is evaluated on {fmtInt(report.metrics.diagnoza_test_windows ?? 0)} windows. Normal operation is the sixth class alongside the five fault causes.</p>
          <p className="mt-3 text-[14px] text-ink-soft">Known limits: small losses can be hidden by normal-loss error; long-standing faults can enter the learned history of a substation. A confirmed substation loss does not prove which customer meter is faulty. Low cause confidence requires human review.</p>
          {validMatrix ? (
            <div className="mt-4 max-w-full overflow-x-auto">
              <table className="w-full text-[12px]">
                <caption className="mb-2 text-left text-[14px]">Confusion matrix: rows are actual causes, columns are predictions. Counts from the evaluation report.</caption>
                <thead><tr><th scope="col" className="p-2 text-left">Actual / predicted</th>{labels.map((key) => <th key={key} scope="col" className="min-w-24 p-2">{CAUSE_LABELS[key] ?? key}</th>)}</tr></thead>
                <tbody>{rows.map(([label, ...counts]) => <tr key={label} className="border-t border-rule"><th scope="row" className="p-2 text-left font-normal">{CAUSE_LABELS[label] ?? label}</th>{counts.map((n, i) => <td key={i} className="p-2 text-center tabular-nums">{fmtInt(Number(n))}</td>)}</tr>)}</tbody>
              </table>
            </div>
          ) : <p className="mt-3 text-[14px]">Confusion matrix unavailable.</p>}
          <details className="mt-4"><summary className="cursor-pointer text-[14px]">All energy-balance metrics</summary><div className="mt-2 overflow-x-auto"><table className="w-full text-[13px]"><thead><tr><th className="text-left">Metric</th><th className="text-right">Model</th><th className="text-right">Baseline</th></tr></thead><tbody>{Object.entries(report.metrics).map(([key, value]) => <tr key={key} className="border-t border-rule"><th className="py-1 pr-3 text-left font-normal break-all">{METRICS[key] ?? key.replaceAll("_", " ")}</th><td className="text-right tabular-nums">{fmtDec(value, 4)}</td><td className="pl-3 text-right tabular-nums">{typeof report.baseline_metrics[key] === "number" ? fmtDec(report.baseline_metrics[key], 4) : "—"}</td></tr>)}</tbody></table></div></details>
          <p className="mt-4 text-[14px]">Reproduce the report. The v2 experiment also requires the larger training populations and tuning step documented in the source guide.</p>
          <div className="mt-2"><CopyCommand cmd={report.primary_metric.includes("v2") ? "make bilant-data bilant-v2 bilant-eval" : report.reproduce_cmd} /></div>
          <div className="mt-4 flex flex-wrap gap-4 text-[14px] underline">
            {analysis ? <a download="energy-balance-errors.ro.md" href={`data:text/markdown;charset=utf-8,${encodeURIComponent(analysis)}`}>Full error analysis, Romanian</a> : null}
            <a download="energy-balance-report.json" href={`data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(report, null, 2))}`}>Full report, split and data sources</a>
          </div>
        </Disclosure>
      </Card>
    </section>
  );
}
