import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import { ClipboardList, HardHat, Layers, ChevronRight, Gauge, ScrollText, Search, UtilityPole, Waypoints, Zap, Network, SlidersHorizontal, Link2, MapPin, TrendingUp } from "lucide-react";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { ReviewActions } from "@/components/detail/review-actions";
import { SeriesChart, SeriesLegend } from "@/components/detail/series-chart";
import { Card, Pill, btn, PageTitle, type Tone } from "@/components/ds";
import { PostSections, type SectionDef } from "@/components/posts/post-sections";
import { AppShell } from "@/components/shell/app-shell";
import type { WorkItem } from "@/lib/contracts";
import { getSeries } from "@/lib/data";
import { ACTION_RO, DECISION_LABEL_RO, auditActionRo, predictionLabelRo } from "@/lib/data/labels";
import { getPosts, withBilantLoss } from "@/lib/data/posts";
import { getRemedies } from "@/lib/data/remedies";
import { BILANT_LABEL, ladderChoice, remedyOptions } from "@/lib/extras";
import { fmtDec, fmtInt, fmtLei, fmtMoment, sentence } from "@/lib/format";
import { approxLei, roundPct } from "@/lib/human";
import { causeBand, causeProbs, parseSection, postColor, postPlace } from "@/lib/posts-view";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { isBilantSeries } from "@/lib/series-utils";

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default function PostPage({ params, searchParams }: PageProps<"/posturi/[id]">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Loading substation…</span>
      </div>}>
      <Post params={params} searchParams={searchParams} />
    </Suspense>
  );
}

const CAUSE_ICON: Record<string, typeof Zap> = {
  contor_client: Zap,
  furt_inainte_contor: Network,
  pierdere_tehnica: SlidersHorizontal,
  client_post_gresit: Link2,
  contor_bilant_setat: Gauge,
};
const BAND_TONE: Record<string, Tone> = { Likely: "blue", Possible: "violet", Unlikely: "grey" };
const PIN_TEXT = { verde: "text-ok-ink", galben: "text-src-c-ink", roșu: "text-red-700 dark:text-red-300", necunoscut: "text-ink-soft" } as const;

const clean = (t: string) => { const x = englishText(t).replace(/\.\s*$/, "").trim(); return x.charAt(0).toUpperCase() + x.slice(1); };
const short = (t: string) => clean(t.replace(/\s*\([^)]*\)/g, ""));

async function Post({ params, searchParams }: Pick<PageProps<"/posturi/[id]">, "params" | "searchParams">) {
  await requireConsole();
  await connection();
  const id = safeDecode((await params).id);
  const sp = await searchParams;
  const scenario = await resolveScenario(searchParams);
  const q = `?scenariu=${encodeURIComponent(scenario)}`;
  const [{ info }, posts, view, remedies] = await Promise.all([
    loadShellInfo(scenario),
    getPosts(scenario),
    loadPlanView(scenario),
    getRemedies(scenario).catch(() => null),
  ]);
  const items = view.data?.workItems ?? [];
  const decisions = view.data?.decisionsByWorkItemId ?? {};
  const byId = new Map(items.map((w) => [w.work_item_id, w]));
  const post = withBilantLoss(posts.data, view.data?.workItemsById ?? {}).find((p) => p.post_id === id);

  if (!post) {
    return (
      <AppShell info={info}>
        <div className="mx-auto w-full max-w-[680px] px-8 py-16 max-md:px-4">
          <Link href={`/posturi${q}`} className="text-[15px] underline decoration-rule underline-offset-4">
            Back to substations
          </Link>
          <h1 className="mt-6 text-[26px] font-[650]">Substation {id} not found in scenario &quot;{scenario}&quot;</h1>
          <p className="mt-3 text-[16px] text-muted-foreground">Choose a substation from the list or map.</p>
        </div>
      </AppShell>
    );
  }

  const bilant = post.bilant_work_item_id ? byId.get(post.bilant_work_item_id) : undefined;
  const cItem = post.c_work_item_id ? byId.get(post.c_work_item_id) : undefined;
  const meters = (post.meter_work_item_ids ?? []).map((m) => byId.get(m)).filter((w): w is WorkItem => Boolean(w)).toSorted((a, b) => b.prediction.score - a.prediction.score);
  const [bilantSeries, cSeries] = await Promise.all([
    bilant ? getSeries(bilant.work_item_id, scenario) : Promise.resolve(null),
    cItem ? getSeries(cItem.work_item_id, scenario) : Promise.resolve(null),
  ]);
  const bd = bilant ? decisions[bilant.work_item_id] : undefined;
  const cd = cItem ? decisions[cItem.work_item_id] : undefined;
  const color = postColor(post, posts.thresholds);
  const place = postPlace(post);
  const wi = (w: WorkItem) => `/lucrari/${encodeURIComponent(w.work_item_id)}${q}`;
  const crew = bd?.crew_id ?? cd?.crew_id ?? null;

  // starea, în cuvinte simple, din bilanț
  const label = bilant?.prediction.label;
  const normal = label === "normal";
  const headline = !bilant
    ? `No energy balance for ${post.post_id}.`
    : normal
      ? `Energy balance within limits at ${post.post_id}.`
      : `${short(predictionLabelRo(label!))} at ${post.post_id}.`;
  const detail = !bilant
    ? "Energy balance not calculated yet. Meters are flagged separately."
    : normal
      ? "Substation output matches total customer consumption."
      : "Substation output exceeds total customer consumption beyond the normal range.";

  let pill: { tone: Tone; text: string } | null = null;
  if (bd) {
    pill =
      bd.decision === "human_review" ? { tone: "orange", text: "Human decision required" }
      : bd.decision === "assigned" ? { tone: "blue", text: crew ? `On route, ${crew}` : "On route" }
      : bd.decision === "remote_action" ? { tone: "violet", text: "Remote check" }
      : bd.decision === "deferred" ? { tone: "grey", text: "Deferred" }
      : { tone: "grey", text: sentence(DECISION_LABEL_RO[bd.decision]) };
  }

  const stare = (
    <Card title="Substation status" icon={ClipboardList} iconTone="blue" id="stare" className="h-full">
      <p className="text-[21px] leading-tight font-[700] tracking-[-0.015em]">{headline}</p>
      <p className="mt-1.5 text-[15px] text-ink-soft">{detail}</p>
      <dl className="mt-4 grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3">
          <UtilityPole aria-hidden="true" size={30} strokeWidth={1.5} className={PIN_TEXT[color]} />
          <div>
            <dt className="text-[13px] text-ink-soft">Substation</dt>
            <dd className="font-[650]" translate="no">{post.post_id}</dd>
          </div>
        </div>
        <div className="flex items-center gap-3 border-l border-rule pl-4">
          <MapPin aria-hidden="true" size={26} strokeWidth={1.5} className="text-ink-soft" />
          <div className="min-w-0">
            <dt className="text-[13px] text-ink-soft">Location</dt>
            <dd className="truncate font-[650]">{place || "no location in the register"}</dd>
          </div>
        </div>
      </dl>
      {post.loss_lei_month != null ? (
        <p className="mt-3 text-[14.5px] text-ink-soft">
          Estimated loss: <b className="font-[650] text-ink">{approxLei(post.loss_lei_month)} per month</b>
          {post.derived ? " (from model A meters)" : ""}.
        </p>
      ) : null}
      {pill ? <div className="mt-3"><Pill tone={pill.tone} size="lg">{pill.text}</Pill></div> : null}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <a href="#cauze" className={btn("primary", "md")}>Investigate</a>
        {bilant ? (
          <Link href={wi(bilant)} className={btn(bd?.decision === "human_review" ? "danger" : "outline", "md")}>View work item</Link>
        ) : cItem ? (
          <Link href={wi(cItem)} className={btn("outline", "md")}>View work item</Link>
        ) : null}
      </div>
    </Card>
  );

  const chart = (
    <Card title="Substation output vs. customer consumption" icon={TrendingUp} iconTone="blue" className="h-full">
      {bilantSeries?.data && bilant ? (
        <>
          <SeriesChart series={bilantSeries.data} workItem={bilant} />
          <div className="mt-2">
            <SeriesLegend source="A" bilant={isBilantSeries(bilantSeries.data)} series={bilantSeries.data} />
          </div>
        </>
      ) : (
        <div role="status" className="py-6 text-[15px]">
          <p className="font-[560]">{bilant ? "Energy balance time series not published yet." : "Energy balance not calculated yet."}</p>
          <p className="mt-1 text-ink-soft">
            {bilant
              ? "Balance results are available; the chart awaits its time series."
              : `Until the balance is available, loss is estimated from meters flagged by model A${posts.lossCost ? ` (daily kWh × score × 30 days × ${fmtDec(posts.lossCost.value, 2)} lei/kWh)` : ""}.`}
          </p>
        </div>
      )}
      <p className="mt-2 text-[12.5px] text-muted-foreground">{englishText(BILANT_LABEL)}</p>
    </Card>
  );

  const causes = bilant ? causeProbs(bilant.extra) : [];
  const causeCard = (
    <Card title="Estimated causes" icon={Search} iconTone="blue" id="cauze" className="h-full scroll-mt-20">
      {causes.length ? (
        <ul className="space-y-2">
          {causes.slice(0, 5).map((c) => {
            const Icon = CAUSE_ICON[c.key] ?? Waypoints;
            const band = causeBand(c.p);
            return (
              <li key={c.key} className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3.5 py-2.5 text-[14.5px]">
                <Icon aria-hidden="true" size={20} strokeWidth={1.6} className="shrink-0 text-src-a" />
                <span className="min-w-0 flex-1">{clean(predictionLabelRo(c.key))}</span>
                <span className="sr-only">{roundPct(c.p)}</span>
                <Pill tone={BAND_TONE[band]} size="sm">{englishText(band)}</Pill>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">{bilant ? "Cause probabilities not published yet." : "Without an energy balance, normal losses cannot be separated from theft, faulty meters or incorrectly linked customers."}</p>
      )}
      <p className="mt-3 text-[12.5px] text-muted-foreground">Model estimates. No cause has been confirmed by a person.</p>
    </Card>
  );

  const meterCard = (
    <Card title="Meters at this substation" icon={Gauge} iconTone="blue" className="h-full">
      {meters.length ? (
        <table className="w-full text-[14px]">
          <thead className="text-left text-[13px] text-ink-soft">
            <tr className="border-b border-rule">
              <th scope="col" className="py-1.5 font-[500]">Meter</th>
              <th scope="col" className="py-1.5 font-[500]">Status</th>
              <th scope="col" className="py-1.5 text-right font-[500]">Score</th>
              <th scope="col" className="w-7"><span className="sr-only">Open</span></th>
            </tr>
          </thead>
          <tbody>
            {meters.map((w) => (
              <tr key={w.work_item_id} className="border-b border-rule/60 last:border-0">
                <td className="py-2 pr-2 font-[600] whitespace-nowrap" translate="no">{w.asset_id}</td>
                <td className="py-2">
                  <Pill tone={w.prediction.label === "normal" ? "green" : "red"} size="sm">{clean(predictionLabelRo(w.prediction.label))}</Pill>
                </td>
                <td className="py-2 text-right"><Pill tone="grey" size="sm">{roundPct(w.prediction.score)}</Pill></td>
                <td className="py-2 text-right">
                  <Link href={wi(w)} aria-label={`Open work item for meter ${w.asset_id}`} className="inline-grid size-7 place-items-center rounded-full hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-ring">
                    <ChevronRight aria-hidden="true" size={18} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">No meters at this substation are flagged by model A.</p>
      )}
    </Card>
  );

  const voltageCard = (
    <Card title="Midday voltage (P10–P90)" icon={Zap} iconTone="amber" className="h-full">
      {cItem && cSeries?.data ? (
        <>
          <SeriesChart series={cSeries.data} workItem={cItem} />
          <div className="mt-2"><SeriesLegend source="C" /></div>
        </>
      ) : (
        <p role="status" className="py-4 text-[15px] text-ink-soft">
          {cItem ? "Voltage time series not published yet." : "No voltage work item exists for this substation. This does not confirm that voltage is within limits."}
        </p>
      )}
    </Card>
  );

  const options = cItem ? remedyOptions(cItem).toSorted((a, b) => a.cost_lei - b.cost_lei) : [];
  const cChoice = cItem ? remedies?.data.find((r) => r.work_item_id === cItem.work_item_id) : undefined;
  const chosen = new Set(cItem ? ladderChoice(cItem, cChoice) : []);
  const ladderCard = (
    <Card title="Remedy options" icon={Layers} iconTone="violet" className="h-full">
      {options.length ? (
        <ol className="space-y-2">
          {options.map((o, i) => {
            const on = chosen.has(o.action);
            return (
              <li key={`${o.action}-${i}`} className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3 py-2 text-[14px]">
                <span aria-hidden="true" className={`grid size-7 shrink-0 place-items-center rounded-full border text-[13px] font-[650] ${on ? "border-src-a bg-src-a text-white" : "border-rule"}`}>{i + 1}</span>
                <span className="min-w-0 flex-1">
                  {clean(ACTION_RO[o.action] ?? o.action)}
                  <span className="block text-[12.5px] text-ink-soft">{fmtLei(o.cost_lei)}</span>
                </span>
                <Pill tone={on ? "blue" : "grey"} size="sm">{on ? "Selected" : o.p90_after_pu >= 1.1 ? "Insufficient" : "Not selected"}</Pill>
              </li>
            );
          })}
        </ol>
      ) : bilant ? (
        <div className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3 py-2.5 text-[14.5px]">
          <span aria-hidden="true" className="grid size-7 place-items-center rounded-full border border-src-a bg-src-a text-[13px] font-[650] text-white">1</span>
          <span className="flex-1">{clean(ACTION_RO[bilant.recommended_action] ?? bilant.recommended_action)}</span>
          <Pill tone="blue" size="sm">Recommended</Pill>
        </div>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">No remedy proposed for this substation yet.</p>
      )}
    </Card>
  );

  const work = [bilant && { w: bilant, d: bd }, cItem && { w: cItem, d: cd }].filter((x): x is { w: WorkItem; d: typeof bd } => Boolean(x));
  const decisionText = work.length
    ? work.map(({ w, d }) => `${w.source === "C" ? "Voltage" : "Energy balance"}: ${d ? englishText(DECISION_LABEL_RO[d.decision]) : "no decision"}`).join("; ") + "."
    : "No work items for this substation in the plan yet.";
  const works = (
    <Card className="h-full" bodyClassName="flex flex-wrap items-center gap-x-6 gap-y-3 !py-4">
      <div className="flex items-center gap-3">
        <HardHat aria-hidden="true" size={30} strokeWidth={1.5} className="text-att-ink" />
        <h2 className="text-[19px] font-[700]">Work items</h2>
      </div>
      <span className="h-8 w-px bg-rule max-md:hidden" aria-hidden="true" />
      <p className="min-w-[220px] flex-1 text-[15.5px]">{sentence(decisionText)}</p>
      <div className="flex flex-wrap items-center gap-2.5">
        {bd?.decision === "human_review" && bilant ? <ReviewActions workItemId={bilant.work_item_id} scenario={scenario} /> : null}
        {work.map(({ w }) => (
          <Link key={w.work_item_id} href={wi(w)} className={btn("outline")}>{work.length > 1 ? `View work item (${w.source === "C" ? "voltage" : "energy balance"})` : "View work item"}</Link>
        ))}
        {crew ? <Link href={`/ordine/${encodeURIComponent(crew)}${q}`} className={btn("primary")}>Work order</Link> : null}
      </div>
    </Card>
  );

  const ids = new Set([bilant?.work_item_id, cItem?.work_item_id, ...meters.map((m) => m.work_item_id)].filter(Boolean) as string[]);
  const audit = (view.data?.audit ?? []).filter((a) => a.work_item_id && ids.has(a.work_item_id)).toSorted((a, b) => b.ts.localeCompare(a.ts)).slice(0, 8);
  const journal = (
    <Card title="History" icon={ScrollText} iconTone="blue">
      {audit.length ? (
        <ul className="divide-y divide-rule text-[14.5px]">
          {audit.map((a) => (
            <li key={a.audit_id} className="flex flex-wrap items-baseline gap-x-4 gap-y-0.5 py-2">
              <span className="w-[220px] whitespace-nowrap text-ink-soft tabular-nums">{fmtMoment(a.ts)}</span>
              <span className="flex-1">{sentence(auditActionRo(a.action))}</span>
              <span className="text-ink-soft">{a.actor === "human" ? "human" : "agent"}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[15px] text-ink-soft">No history for this substation&apos;s work items.</p>
      )}
    </Card>
  );

  const sections: SectionDef[] = [
    { id: "bilant", node: chart },
    { id: "cauze", node: causeCard },
    { id: "contoare", node: meterCard },
    { id: "tensiune", node: voltageCard },
    { id: "remediere", node: ladderCard },
    { id: "lucrari", node: works, className: "col-span-full" },
    { id: "jurnal", node: journal, className: "col-span-full" },
  ];

  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1440px] px-8 pt-7 pb-14 max-md:px-4">
        <PageTitle
          icon={UtilityPole}
          title={`Substation ${post.post_id}${place ? ` ${place}` : ""}${post.synthetic !== false ? " (synthetic)" : ""}`}
          subtitle="Energy balance, meters and voltage evidence."
        />
        <PostSections sections={sections} stare={stare} initial={parseSection(typeof sp.sectiune === "string" ? sp.sectiune : null)} />
        <p className="mt-5 text-[13px] text-muted-foreground">
          Linked work at this substation. {fmtInt(post.meters_flagged ?? 0)} flagged meters.
        </p>
      </div>
    </AppShell>
  );
}
