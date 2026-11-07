import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
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

export const metadata: Metadata = { title: "Rulare agent" };

export default function RunPage({ searchParams }: PageProps<"/rulare">) {
  return (
    <Suspense
      fallback={
        <div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
          <span className="sr-only">Se încarcă pagina de rulare…</span>
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
  "R-ABSTAIN": "Când modelul nu e sigur de scor, nu trimite singur o echipă: cazul așteaptă o persoană.",
  "R-ABSTAIN-DATA": "Când datele de intrare sunt greșite, un om le corectează înainte de orice acțiune.",
  "R-LOW-CONFIDENCE": "Când încrederea e prea mică pentru o echipă, cazul merge la un om.",
  "R-WIDE-INTERVAL": "Când intervalul de încredere e prea larg, modelul nu e sigur și întreabă un om.",
  "R-B-REGION-CAP": "Când o regiune și-a folosit toate echipele trimise din timp, un om hotărăște ce rămâne.",
};

const METRIC_NAME: Record<string, string> = {
  precision_at_k: "Precizie contoare",
  pr_auc: "PR-AUC",
  roc_auc: "ROC-AUC",
  mae_vmax_pu: "Eroare tensiune",
};

async function Run({ searchParams }: { searchParams: PageProps<"/rulare">["searchParams"] }) {
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

  // aprobarea listei: din jurnal sau din cookie-ul acestui browser (ca pe pagina „Planul de mâine”)
  let approved = false;
  if (plan) {
    const fromAudit = plan.audit.some(
      (a) => a.actor === "human" && /plan/i.test(a.action) && /aprob|approv/i.test(a.action) && Date.parse(a.ts) >= Date.parse(plan.plan.generated_at),
    );
    const cookie = (await cookies()).get(`aprobat_${scenario}`)?.value;
    const [cookiePlan, cookieAt] = cookie ? cookie.split("|") : [];
    approved = fromAudit || (cookiePlan === plan.plan.plan_id && Boolean(cookieAt));
  }
  const waiting = plan ? plan.plan.decisions.filter((d) => d.decision === "human_review") : [];

  // regula care trimite cele mai multe cazuri la om
  const byRule = new Map<string, number>();
  for (const d of waiting) byRule.set(d.rule_id, (byRule.get(d.rule_id) ?? 0) + 1);
  const topRule = [...byRule.entries()].sort((a, b) => b[1] - a[1])[0] ?? null;

  const stages: { name: string; what: string; icon: IconCmp; tone: string; counts: BySource; time: string }[] = counts
    ? [
        { name: "Percepe", what: "Primește lucrările și citește datele din spatele lor.", icon: Eye, tone: "text-src-a", counts: counts.perceive, time: stepTime("perceive") },
        { name: "Estimează", what: "Modelele A, B și C estimează riscul pentru fiecare lucrare validă.", icon: Layers, tone: "text-violet", counts: counts.estimate, time: stepTime("estimate") },
        { name: "Decide", what: "Regulile din cod aleg: în traseu, la distanță, la urmărire sau la om.", icon: Network, tone: "text-src-c", counts: counts.decide, time: stepTime("decide") },
        { name: "Acționează", what: "Trasee, citiri la distanță și mesaje, cu jurnalul fiecărei decizii.", icon: Zap, tone: "text-ok-ink", counts: counts.act, time: stepTime("act") },
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
    log.push({ t, text: `Lucrări primite: ${fmtInt(received)} (A ${fmtInt(counts.perceive.A)}, B ${fmtInt(counts.perceive.B)}, C ${fmtInt(counts.perceive.C)})` });
    log.push({ t, text: `Decizii: în trasee ${fmtInt(s.assigned)}, la distanță ${fmtInt(s.remote_actions)}, la om ${fmtInt(s.human_review)}` });
    log.push({ t, text: `Plan nou: ${plan.plan.plan_id}` });
  }

  const q = `?scenariu=${encodeURIComponent(scenario)}`;
  const m = metrics.data;
  const scoreRows: { name: string; unit: string; key: string; tone: Tone; cur: number | null; ref: number | null }[] = [
    m.A ? { name: METRIC_NAME[m.A.primary_metric] ?? sentence(m.A.primary_metric.replaceAll("_", " ")).replace(/\.$/, ""), key: m.A.primary_metric, unit: "", tone: "blue" as Tone, cur: m.A.metrics[m.A.primary_metric] ?? null, ref: m.A.baseline_metrics[m.A.primary_metric] ?? null } : null,
    m.B ? { name: "PR-AUC furtună", key: "pr_auc", unit: "", tone: "violet" as Tone, cur: m.B.metrics.pr_auc ?? null, ref: m.B.baseline_metrics.pr_auc ?? null } : null,
    m.C ? { name: "Eroare tensiune", key: "mae_vmax_pu", unit: " pu", tone: "amber" as Tone, cur: m.C.metrics.mae_vmax_pu ?? null, ref: m.C.baseline_metrics.mae_vmax_pu ?? null } : null,
  ].filter((x): x is NonNullable<typeof x> => x !== null);

  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        <div className="flex items-start gap-4">
          <Bot aria-hidden="true" size={44} strokeWidth={1.4} className="mt-1 shrink-0 text-violet" />
          <div className="min-w-0">
            <h1 className="text-[34px] leading-[1.12] font-[750] tracking-[-0.025em] max-md:text-[28px]">Rulare agent</h1>
            <p className="mt-1 max-w-[90ch] text-[17px] text-ink-soft">Execuție operațională: percepe, estimează, decide și acționează asupra lucrărilor.</p>
          </div>
        </div>

        {!plan || !counts || !s ? (
          <Card className="mt-6" bodyClassName="py-6">
            <p className="text-[18px] font-[620]">Nu există încă un plan pentru „{label}”.</p>
            <p className="mt-1.5 mb-4 text-[15.5px] text-ink-soft">{view.degradedReason ?? "Agentul n-a rulat încă pentru acest scenariu."} Pornește-l acum.</p>
            <RunButton scenario={scenario} />
          </Card>
        ) : (
          <>
            <div className="mt-5 grid grid-cols-6 gap-4 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
              <div className="col-span-2 flex min-w-0 items-center gap-5 rounded-[14px] border border-rule bg-panel px-5 py-4 max-xl:col-span-3 max-md:col-span-2 max-sm:col-span-1 max-sm:flex-wrap">
                <div className="flex items-center gap-4">
                  <Layers aria-hidden="true" size={34} strokeWidth={1.5} className="shrink-0 text-src-a" />
                  <div>
                    <p className="text-[15px] text-ink-soft">Lucrări primite</p>
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
              <Kpi icon={Route} tone="violet" value={fmtInt(s.assigned)} label="În trasee" />
              <Kpi icon={Radio} tone="blue" value={fmtInt(s.remote_actions)} label="La distanță" />
              <Kpi icon={UserRound} tone="orange" value={fmtInt(s.human_review)} label="La om" />
              <Kpi icon={Clock} tone="grey" value={totalTime != null ? fmtSeconds(totalTime) : "—"} label="Timp procesare" className="max-xl:col-span-1" />
            </div>

            <Card title="Sarcină agent" className="mt-4" bodyClassName="pt-2">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[560px] border-separate border-spacing-y-2 text-[16px]">
                  <thead>
                    <tr className="text-left text-[15px] text-ink-soft">
                      <th scope="col" className="px-4 pb-1 font-[450]"><span className="sr-only">Pas</span></th>
                      <th scope="col" className="pb-1 font-[450] max-lg:hidden"><span className="sr-only">Ce face</span></th>
                      <th scope="col" className="px-3 pb-1 text-center font-[450]">Total</th>
                      {SRC.map((k) => (
                        <th key={k} scope="col" className="px-1 pb-1 text-center font-[450]">{k}</th>
                      ))}
                      <th scope="col" className="px-3 pb-1 text-center font-[450]">Timp</th>
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
                <ParamsButton rows={params} />
                <div className="ml-auto flex flex-wrap items-center gap-3">
                  <Pill tone={approved ? "green" : "grey"} size="lg" icon={approved ? CircleCheck : CircleAlert} className="h-11 rounded-[10px] px-5">
                    {approved ? "Lista aprobată" : "Lista neaprobată"}
                  </Pill>
                  <Link href={`/coada${q}`} className={cn(btn("danger", "md"), "gap-2")}>
                    <UserRound aria-hidden="true" size={18} strokeWidth={1.8} />
                    {fmtInt(waiting.length)} decizie umană
                  </Link>
                </div>
              </div>
            </Card>

            <div className="mt-4 grid grid-cols-[1fr_1fr_1.15fr] items-start gap-4 max-xl:grid-cols-2 max-md:grid-cols-1">
              <Card title="Distribuția lucrărilor" icon={ChartColumn}>
                <div className="flex items-center gap-5 max-sm:flex-wrap">
                  <Donut
                    size={124}
                    center={fmtInt(received)}
                    sub="lucrări"
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
                  {([["În trasee", s.assigned, Waypoints], ["La distanță", s.remote_actions, Radio], ["La om", s.human_review, UserRound]] as [string, number, IconCmp][]).map(([name, n, Icon]) => (
                    <li key={name} className="flex items-center gap-3 border-b border-rule py-2 last:border-b-0">
                      <Icon aria-hidden="true" size={18} strokeWidth={1.6} className="text-ink-soft" />
                      {name}
                      <span className="ml-auto text-[16px] font-[650] tabular-nums">{fmtInt(n)}</span>
                    </li>
                  ))}
                </ul>
              </Card>

              <Card title="Scoruri model" icon={Layers}>
                {scoreRows.length ? (
                  <table className="w-full text-[15px]">
                    <thead>
                      <tr className="text-left text-[14px] text-ink-soft">
                        <th scope="col" className="pb-2 font-[450]">Metrică</th>
                        <th scope="col" className="pb-2 text-center font-[450]">Model curent</th>
                        <th scope="col" className="pb-2 text-center font-[450]">Referință</th>
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
                  <p className="text-[15px] text-ink-soft">Nu există încă rapoarte de evaluare.</p>
                )}
                <p className="mt-3 text-[13px] text-ink-soft">Referința e modelul simplu cu care se compară fiecare model. Precizia și PR-AUC: mai mare e mai bine; eroarea: mai mică e mai bine.</p>
              </Card>

              <div className="grid gap-4">
                <Card title="Regula activă" icon={ClipboardList} iconTone="orange" bodyClassName="pt-2">
                  {topRule ? (
                    <>
                      <p className="text-[19px] leading-snug font-[680]">{sentence(ruleRo(topRule[0]) ?? topRule[0])}</p>
                      <p className="mt-1 text-[14.5px] text-ink-soft">
                        {RULE_SENTENCE[topRule[0]] ?? "Aici ajung cazurile pe care agentul nu le poate decide singur."} {fmtInt(topRule[1])} {topRule[1] === 1 ? "caz" : "cazuri"} azi.
                      </p>
                    </>
                  ) : (
                    <p className="text-[15px] text-ink-soft">Nicio regulă nu trimite cazuri la om în planul curent.</p>
                  )}
                </Card>
                <Card title="Jurnal rulare" icon={BookOpen} action={<span className="text-[14px] font-[450] text-ink-soft">Ultimele evenimente</span>} bodyClassName="pt-2">
                  <ul className="text-[14.5px]">
                    {log.slice(0, 4).map((l, i) => (
                      <li key={i} className="grid grid-cols-[48px_minmax(0,1fr)] gap-3 border-b border-rule py-2 last:border-b-0">
                        <span className="text-ink-soft tabular-nums">{l.t}</span>
                        <span className="min-w-0 break-words">{l.text}</span>
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
