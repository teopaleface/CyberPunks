import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense, type ComponentType } from "react";
import { cn } from "cn";
import { BookOpen, Bot, ChartColumn, CircleCheck, Clock, Eye, Layers, ClipboardList, Network, Radio, UserRound, Waypoints, Zap, CircleAlert, Route } from "lucide-react";
import { Card, Donut, Kpi, Pill, SOURCE_TONE, btn, type Tone } from "@/components/ds";
import { ParamsButton, RunButton } from "@/components/queue/run-panel";
import { AppShell } from "@/components/shell/app-shell";
import type { Source } from "@/lib/contracts";
import { getMetrics } from "@/lib/data";
import { readDemoRun } from "@/lib/data/files";
import { auditActionRo, ruleRo } from "@/lib/data/labels";
import { fmtDec, fmtInt, fmtSeconds, fmtTime, sentence } from "@/lib/format";
import { stageCounts, totalOf, fmtMetric, type BySource } from "@/lib/queue-run";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { readPlannerParams } from "./params";

export const metadata: Metadata = { title: "Run agent" };

export default function RunPage({ searchParams }: PageProps<"/rulare">) {
  return (
    <Suspense
      fallback={
        <div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
          <span className="sr-only">Loading agent run…</span>
        </div>
      }
    >
      <Run searchParams={searchParams} />
    </Suspense>
  );
}

type IconCmp = ComponentType<{ size?: number; strokeWidth?: number; className?: string; "aria-hidden"?: boolean | "true" }>;
const SRC: Source[] = ["A", "B", "C"];
const SRC_VAR: Record<Source, string> = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" };
const SRC_DOT: Record<Source, string> = { A: "bg-src-a", B: "bg-src-b", C: "bg-src-c" };

const RULE_SENTENCE: Record<string, string> = {
  "R-ABSTAIN": "Uncertain scores require human review before a crew is assigned.",
  "R-ABSTAIN-DATA": "Invalid input requires human correction before any action.",
  "R-LOW-CONFIDENCE": "Low confidence requires human review before a crew is assigned.",
  "R-WIDE-INTERVAL": "A wide confidence interval requires human review.",
  "R-B-REGION-CAP": "A person decides remaining work once a region reaches its pre-positioned crew limit.",
};

const PARAM_COPY: Record<string, string> = {
  "Valoare minimă ca să întrebe un om": "Minimum value for human review",
  "Sub această sumă, un caz nesigur rămâne la urmărire.": "Uncertain cases below this value stay under monitoring.",
  "Cazuri pe zi pentru un dispecer": "Daily review limit per dispatcher",
  "Câte cazuri intră cel mult în „Nu sunt sigur”.": "Maximum number of cases sent to the review queue each day.",
  "Interval de încredere acceptat": "Maximum confidence interval width",
  "Mai larg de atât înseamnă că modelul nu e sigur.": "Wider intervals mean the model is uncertain.",
  "Date lipsă acceptate": "Allowed missing data",
  "Peste acest procent, scorul nu mai e de încredere.": "Above this percentage, the score is unreliable.",
  "Scor minim pentru risc de siguranță": "Minimum score for safety priority",
  "Sub el, semnalul e prea slab ca să treacă peste cost.": "Below this score, the signal cannot override the cost check.",
  "Scor minim pentru o vizită la contor": "Minimum score for a meter visit",
  "Echipa merge la ușa clientului doar peste acest scor.": "A crew visits a customer only above this score.",
  "Scor minim pentru o echipă trimisă din timp": "Minimum score for pre-positioning a crew",
  "Sub această probabilitate nu se mută echipe înainte de furtună.": "Below this probability, crews are not moved ahead of the storm.",
  "Echipe trimise din timp pe regiune": "Pre-positioned crews per region",
  "Restul rămân pentru lucrările curente.": "Other crews remain available for current work.",
};
const paramText = (text: string) => PARAM_COPY[text] ?? englishText(text);

const METRIC_NAME: Record<string, string> = {
  subtle_precision_at_k: "Precision on subtle test anomalies",
  sgcc_precision_at_k: "Precision on SGCC real theft labels",
  precision_at_k: "Meter precision",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  mae_vmax_pu: "Voltage error",
};

async function Run({ searchParams }: { searchParams: PageProps<"/rulare">["searchParams"] }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, metrics, run, params] = await Promise.all([
    loadShellInfo(scenario),
    getMetrics(),
    readDemoRun(scenario),
    readPlannerParams(),
  ]);
  const plan = view.data;
  const label = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;

  const counts = plan
    ? stageCounts({
        items: plan.workItems,
        invalidIds: plan.invalidItems.map((r) => String(r.work_item_id ?? "")).filter(Boolean),
        decisions: plan.plan.decisions,
      })
    : null;
  const s = plan?.plan.summary;
  const received = counts ? totalOf(counts.perceive) : 0;
  const timings = (run?.data.timings ?? null) as Record<string, number> | null;
  const stepTime = (k: string) => (timings && typeof timings[k] === "number" ? fmtSeconds(timings[k]) : "—");
  const totalTime = timings ? ["perceive", "estimate", "decide", "act"].reduce((n, k) => n + (Number(timings[k]) || 0), 0) : null;

  // Approval comes only from the server audit, never a browser-only flag.
  let approved = false;
  if (plan) {
    const fromAudit = plan.audit.some(
      (a) => a.actor === "human" && /plan/i.test(a.action) && /aprob|approv/i.test(a.action) && Date.parse(a.ts) >= Date.parse(plan.plan.generated_at),
    );
    approved = fromAudit;
  }
  const waiting = plan ? plan.plan.decisions.filter((d) => d.decision === "human_review") : [];

  // regula care trimite cele mai multe cazuri la om
  const byRule = new Map<string, number>();
  for (const d of waiting) byRule.set(d.rule_id, (byRule.get(d.rule_id) ?? 0) + 1);
  const topRule = [...byRule.entries()].sort((a, b) => b[1] - a[1])[0] ?? null;

  const stages: { name: string; what: string; icon: IconCmp; tone: string; counts: BySource; time: string }[] = counts
    ? [
        { name: "Perceive", what: "Read work items and their supporting data.", icon: Eye, tone: "text-src-a", counts: counts.perceive, time: stepTime("perceive") },
        { name: "Estimate", what: "Models A, B and C estimate risk for valid work items.", icon: Layers, tone: "text-violet", counts: counts.estimate, time: stepTime("estimate") },
        { name: "Decide", what: "Rules assign a route, remote check, monitoring or human review.", icon: Network, tone: "text-src-c", counts: counts.decide, time: stepTime("decide") },
        { name: "Act", what: "Produce routes, remote reads and messages, with a decision history.", icon: Zap, tone: "text-ok-ink", counts: counts.act, time: stepTime("act") },
      ]
    : [];

  const humanLog = (plan?.audit ?? [])
    .filter((a) => a.actor === "human")
    .toSorted((a, b) => b.ts.localeCompare(a.ts))
    .slice(0, 2);
  const log: { t: string; text: string }[] = [];
  for (const a of humanLog) log.push({ t: fmtTime(a.ts), text: `${sentence(auditActionRo(a.action)).replace(/\.$/, "")}${a.work_item_id ? `: ${a.work_item_id}` : ""}` });
  if (plan && counts && s) {
    const t = fmtTime(plan.plan.generated_at);
    log.push({ t, text: `Work items received: ${fmtInt(received)} (A ${fmtInt(counts.perceive.A)}, B ${fmtInt(counts.perceive.B)}, C ${fmtInt(counts.perceive.C)})` });
    log.push({ t, text: `Decisions: on routes ${fmtInt(s.assigned)}, remote ${fmtInt(s.remote_actions)}, human review ${fmtInt(s.human_review)}` });
    log.push({ t, text: `New plan: ${plan.plan.plan_id}` });
  }

  const q = `?scenariu=${encodeURIComponent(scenario)}`;
  const m = metrics.data;
  const scoreRows: { name: string; unit: string; key: string; tone: Tone; cur: number | null; ref: number | null }[] = [
    m.A ? { name: METRIC_NAME[m.A.primary_metric] ?? sentence(m.A.primary_metric.replaceAll("_", " ")).replace(/\.$/, ""), key: m.A.primary_metric, unit: "", tone: "blue" as Tone, cur: m.A.metrics[m.A.primary_metric] ?? null, ref: m.A.baseline_metrics[m.A.primary_metric] ?? null } : null,
    m.B ? { name: "Storm PR-AUC", key: "pr_auc", unit: "", tone: "violet" as Tone, cur: m.B.metrics.pr_auc ?? null, ref: m.B.baseline_metrics.pr_auc ?? null } : null,
    m.C ? { name: "Voltage error", key: "mae_vmax_pu", unit: " pu", tone: "amber" as Tone, cur: m.C.metrics.mae_vmax_pu ?? null, ref: m.C.baseline_metrics.mae_vmax_pu ?? null } : null,
  ].filter((x): x is NonNullable<typeof x> => x !== null);

  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        <div className="flex items-start gap-4">
          <Bot aria-hidden="true" size={44} strokeWidth={1.4} className="mt-1 shrink-0 text-violet" />
          <div className="min-w-0">
            <h1 className="text-[34px] leading-[1.12] font-[750] tracking-[-0.025em] max-md:text-[28px]">Run agent</h1>
            <p className="mt-1 max-w-[90ch] text-[17px] text-ink-soft">Latest run and decisions.</p>
          </div>
        </div>

        {!plan || !counts || !s ? (
          <Card className="mt-6" bodyClassName="py-6">
            <p className="text-[18px] font-[620]">No plan yet for &quot;{englishText(label)}&quot;.</p>
            <p className="mt-1.5 mb-4 text-[15.5px] text-ink-soft">{englishText(view.degradedReason ?? "The agent has not run for this scenario yet.")} Run it now.</p>
            <RunButton scenario={scenario} />
          </Card>
        ) : (
          <>
            <div className="mt-5 grid grid-cols-6 gap-4 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
              <div className="col-span-2 flex min-w-0 items-center gap-5 rounded-[14px] border border-rule bg-panel px-5 py-4 max-xl:col-span-3 max-md:col-span-2 max-sm:col-span-1 max-sm:flex-wrap">
                <div className="flex items-center gap-4">
                  <Layers aria-hidden="true" size={34} strokeWidth={1.5} className="shrink-0 text-src-a" />
                  <div>
                    <p className="text-[15px] text-ink-soft">Work items received</p>
                    <p className="text-[34px] leading-tight font-[700] tracking-[-0.02em] tabular-nums">{fmtInt(received)}</p>
                  </div>
                </div>
                <ul className="ml-auto grid min-w-[130px] gap-0.5 border-l border-rule pl-5 text-[15px]">
                  {SRC.map((k) => (
                    <li key={k} className="flex items-center gap-2.5">
                      <span aria-hidden="true" className={cn("size-2.5 rounded-full", SRC_DOT[k])} />
                      <span className="w-4 font-[560]">{k}</span>
                      <span className="ml-auto tabular-nums">{fmtInt(counts.perceive[k])}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <Kpi icon={Route} tone="violet" value={fmtInt(s.assigned)} label="On routes" />
              <Kpi icon={Radio} tone="blue" value={fmtInt(s.remote_actions)} label="Remote" />
              <Kpi icon={UserRound} tone="orange" value={fmtInt(s.human_review)} label="Human review" />
              <Kpi icon={Clock} tone="grey" value={totalTime != null ? fmtSeconds(totalTime) : "—"} label="Processing time" className="max-xl:col-span-1" />
            </div>

            <Card title="Run stages" className="mt-4" bodyClassName="pt-2">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] border-separate border-spacing-y-2 text-[16px]">
                  <thead>
                    <tr className="text-left text-[15px] text-ink-soft">
                      <th scope="col" className="px-4 pb-1 font-[450]"><span className="sr-only">Step</span></th>
                      <th scope="col" className="pb-1 font-[450] max-lg:hidden"><span className="sr-only">Action</span></th>
                      <th scope="col" className="px-3 pb-1 text-center font-[450]">Total</th>
                      {SRC.map((k) => (
                        <th key={k} scope="col" className="px-1 pb-1 text-center font-[450]">{k}</th>
                      ))}
                      <th scope="col" className="px-3 pb-1 text-center font-[450]">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stages.map((st) => {
                      const Icon = st.icon;
                      return (
                        <tr key={st.name} className="[&>*]:border-y [&>*]:border-rule [&>*]:bg-surface-2 [&>*:first-child]:rounded-l-[12px] [&>*:first-child]:border-l [&>*:last-child]:rounded-r-[12px] [&>*:last-child]:border-r">
                          <th scope="row" className="py-3 pr-3 pl-4 text-left font-[620] whitespace-nowrap">
                            <span className="flex items-center gap-3.5">
                              <Icon aria-hidden="true" size={28} strokeWidth={1.5} className={st.tone} />
                              {st.name}
                            </span>
                          </th>
                          <td className="py-3 pr-4 text-[14.5px] text-ink-soft max-lg:hidden">{st.what}</td>
                          <td className="px-3 py-3 text-center text-[19px] font-[650] tabular-nums">{fmtInt(totalOf(st.counts))}</td>
                          {SRC.map((k) => (
                            <td key={k} className="px-1 py-3 text-center">
                              <Pill tone={SOURCE_TONE[k]} className="min-w-[68px] justify-center text-[16px] tabular-nums" size="lg">{fmtInt(st.counts[k])}</Pill>
                            </td>
                          ))}
                          <td className="px-3 py-3 text-center tabular-nums">{st.time}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-3">
                <RunButton scenario={scenario} />
                <ParamsButton rows={params.map((p) => ({ ...p, label: paramText(p.label), note: paramText(p.note) }))} />
                <div className="ml-auto flex flex-wrap items-center gap-3">
                  <Pill tone={approved ? "green" : "grey"} size="lg" icon={approved ? CircleCheck : CircleAlert} className="h-11 rounded-[10px] px-5">
                    {approved ? "Plan approved" : "Plan awaiting approval"}
                  </Pill>
                  <Link href={`/coada${q}`} className={cn(btn("danger", "md"), "gap-2")}>
                    <UserRound aria-hidden="true" size={18} strokeWidth={1.8} />
                    {fmtInt(waiting.length)} human review
                  </Link>
                </div>
              </div>
            </Card>

            <div className="mt-4 grid grid-cols-[1fr_1fr_1.15fr] items-start gap-4 max-xl:grid-cols-2 max-md:grid-cols-1">
              <Card title="Work distribution" icon={ChartColumn}>
                <div className="flex items-center gap-5 max-sm:flex-wrap">
                  <Donut
                    size={124}
                    center={fmtInt(received)}
                    sub="work items"
                    parts={SRC.map((k) => ({ value: counts.perceive[k], color: SRC_VAR[k], label: k }))}
                  />
                  <ul className="min-w-0 flex-1 text-[15.5px]">
                    {SRC.map((k) => (
                      <li key={k} className="flex items-center gap-2.5 py-1.5">
                        <span aria-hidden="true" className={cn("size-2.5 rounded-full", SRC_DOT[k])} />
                        <span className="w-4 font-[560]">{k}</span>
                        <span className="ml-auto tabular-nums">{fmtInt(counts.perceive[k])}</span>
                        <span className="w-14 text-right text-ink-soft tabular-nums">{received ? `${fmtDec((counts.perceive[k] / received) * 100, 1)}%` : "—"}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <ul className="mt-3 border-t border-rule pt-1 text-[15px]">
                  {([["On routes", s.assigned, Waypoints], ["Remote", s.remote_actions, Radio], ["Human review", s.human_review, UserRound]] as [string, number, IconCmp][]).map(([name, n, Icon]) => (
                    <li key={name} className="flex items-center gap-3 border-b border-rule py-2 last:border-b-0">
                      <Icon aria-hidden="true" size={18} strokeWidth={1.6} className="text-ink-soft" />
                      {name}
                      <span className="ml-auto text-[16px] font-[650] tabular-nums">{fmtInt(n)}</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card title="Model scores" icon={Layers}>
                {scoreRows.length ? (
                  <table className="w-full text-[15px]">
                    <thead>
                      <tr className="text-left text-[14px] text-ink-soft">
                        <th scope="col" className="pb-2 font-[450]">Metric</th>
                        <th scope="col" className="pb-2 text-center font-[450]">Current model</th>
                        <th scope="col" className="pb-2 text-center font-[450]">Baseline</th>
                      </tr>
                    </thead>
                    <tbody>
                      {scoreRows.map((r) => (
                        <tr key={r.key} className="border-t border-rule">
                          <th scope="row" className="py-3 text-left font-[450]">{r.name}</th>
                          <td className="py-3 text-center">
                            {r.cur != null ? <Pill tone={r.tone} className="text-[14.5px] tabular-nums">{fmtMetric(r.cur, r.key)}{r.unit}</Pill> : "—"}
                          </td>
                          <td className="py-3 text-center">
                            {r.ref != null ? <Pill tone="grey" className="text-[14.5px] tabular-nums">{fmtMetric(r.ref, r.key)}{r.unit}</Pill> : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="text-[15px] text-ink-soft">No evaluation reports yet.</p>
                )}
                <p className="mt-3 text-[13px] text-ink-soft">Baseline is the simple comparison model. Higher precision and PR-AUC are better; lower error is better.</p>
              </Card>

              <div className="grid gap-4">
                <Card title="Active review rule" icon={ClipboardList} iconTone="orange" bodyClassName="pt-2">
                  {topRule ? (
                    <>
                      <p className="text-[19px] leading-snug font-[680]">{englishText(sentence(ruleRo(topRule[0]) ?? topRule[0]))}</p>
                      <p className="mt-1 text-[14.5px] text-ink-soft">
                        {RULE_SENTENCE[topRule[0]] ?? "Cases requiring a human decision."} {fmtInt(topRule[1])} {topRule[1] === 1 ? "case" : "cases"} today.
                      </p>
                    </>
                  ) : (
                    <p className="text-[15px] text-ink-soft">No rules sent cases to human review in this plan.</p>
                  )}
                </Card>
                <Card title="Run history" icon={BookOpen} action={<span className="text-[14px] font-[450] text-ink-soft">Latest events</span>} bodyClassName="pt-2">
                  <ul className="text-[14.5px]">
                    {log.slice(0, 4).map((l, i) => (
                      <li key={i} className="grid grid-cols-[48px_minmax(0,1fr)] gap-3 border-b border-rule py-2 last:border-b-0">
                        <span className="text-ink-soft tabular-nums">{l.t}</span>
                        <span className="min-w-0 break-words">{englishText(l.text)}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
