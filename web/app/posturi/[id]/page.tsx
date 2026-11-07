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
        <span className="sr-only">Se încarcă postul…</span>
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
const BAND_TONE: Record<string, Tone> = { Probabil: "blue", Posibil: "violet", "Puțin probabil": "grey" };
const PIN_TEXT = { verde: "text-[#4ade80]", galben: "text-[#facc15]", roșu: "text-[#f87171]", necunoscut: "text-ink-soft" } as const;

const clean = (t: string) => { const x = t.replace(/\.\s*$/, "").trim(); return x.charAt(0).toUpperCase() + x.slice(1); };
const short = (t: string) => clean(t.replace(/\s*\([^)]*\)/g, ""));

async function Post({ params, searchParams }: Pick<PageProps<"/posturi/[id]">, "params" | "searchParams">) {
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
            Înapoi la posturi
          </Link>
          <h1 className="mt-6 text-[26px] font-[650]">Postul {id} nu apare în scenariul „{scenario}”</h1>
          <p className="mt-3 text-[16px] text-muted-foreground">Alege un post din lista posturilor sau de pe hartă.</p>
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
    ? `Fără bilanț la ${post.post_id}.`
    : normal
      ? `Bilanț în limite la ${post.post_id}.`
      : `${short(predictionLabelRo(label!))} la ${post.post_id}.`;
  const detail = !bilant
    ? "Bilanțul pe acest post nu e calculat încă; contoarele sunt semnalate separat."
    : normal
      ? "Ce iese din post se potrivește cu suma clienților."
      : "Iese din post mai mult decât suma clienților, peste banda normală.";

  let pill: { tone: Tone; text: string } | null = null;
  if (bd) {
    pill =
      bd.decision === "human_review" ? { tone: "orange", text: "Necesită decizie umană" }
      : bd.decision === "assigned" ? { tone: "blue", text: crew ? `În traseu, ${crew}` : "În traseu" }
      : bd.decision === "remote_action" ? { tone: "violet", text: "Verificare la distanță" }
      : bd.decision === "deferred" ? { tone: "grey", text: "Amânată" }
      : { tone: "grey", text: sentence(DECISION_LABEL_RO[bd.decision]) };
  }

  const stare = (
    <Card title="Stare post" icon={ClipboardList} iconTone="blue" id="stare" className="h-full">
      <p className="text-[21px] leading-tight font-[700] tracking-[-0.015em]">{headline}</p>
      <p className="mt-1.5 text-[15px] text-ink-soft">{detail}</p>
      <dl className="mt-4 grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3">
          <UtilityPole aria-hidden="true" size={30} strokeWidth={1.5} className={PIN_TEXT[color]} />
          <div>
            <dt className="text-[13px] text-ink-soft">Post</dt>
            <dd className="font-[650]" translate="no">{post.post_id}</dd>
          </div>
        </div>
        <div className="flex items-center gap-3 border-l border-rule pl-4">
          <MapPin aria-hidden="true" size={26} strokeWidth={1.5} className="text-ink-soft" />
          <div className="min-w-0">
            <dt className="text-[13px] text-ink-soft">Locație</dt>
            <dd className="truncate font-[650]">{place || "fără locație în registru"}</dd>
          </div>
        </div>
      </dl>
      {post.loss_lei_month != null ? (
        <p className="mt-3 text-[14.5px] text-ink-soft">
          Pierdere estimată: <b className="font-[650] text-ink">{approxLei(post.loss_lei_month)} pe lună</b>
          {post.derived ? " (din contoarele A)" : ""}.
        </p>
      ) : null}
      {pill ? <div className="mt-3"><Pill tone={pill.tone} size="lg">{pill.text}</Pill></div> : null}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <a href="#cauze" className={btn("primary", "md")}>Analizează</a>
        {bilant ? (
          <Link href={wi(bilant)} className={btn(bd?.decision === "human_review" ? "danger" : "outline", "md")}>Vezi lucrarea</Link>
        ) : cItem ? (
          <Link href={wi(cItem)} className={btn("outline", "md")}>Vezi lucrarea</Link>
        ) : null}
      </div>
    </Card>
  );

  const chart = (
    <Card title="Bilanț: ieșit din post vs. suma clienților" icon={TrendingUp} iconTone="blue" className="h-full">
      {bilantSeries?.data && bilant ? (
        <>
          <SeriesChart series={bilantSeries.data} workItem={bilant} />
          <div className="mt-2">
            <SeriesLegend source="A" bilant={isBilantSeries(bilantSeries.data)} series={bilantSeries.data} />
          </div>
        </>
      ) : (
        <div role="status" className="py-6 text-[15px]">
          <p className="font-[560]">{bilant ? "Seria bilanțului pentru grafic nu e publicată încă." : "Bilanțul pe acest post nu e calculat încă."}</p>
          <p className="mt-1 text-ink-soft">
            {bilant
              ? "Cifrele și cauza vin deja din bilanț; graficul apare când firul bilanțului publică seria."
              : `Până vine bilanțul, pierderea afișată e estimată din contoarele semnalate de modelul A${posts.lossCost ? ` (kWh pe zi × scor × 30 de zile × ${fmtDec(posts.lossCost.value, 2)} lei/kWh)` : ""}.`}
          </p>
        </div>
      )}
      <p className="mt-2 text-[12.5px] text-muted-foreground">{BILANT_LABEL}</p>
    </Card>
  );

  const causes = bilant ? causeProbs(bilant.extra) : [];
  const causeCard = (
    <Card title="Cauze (din bilanț)" icon={Search} iconTone="blue" id="cauze" className="h-full scroll-mt-20">
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
                <Pill tone={BAND_TONE[band]} size="sm">{band}</Pill>
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">{bilant ? "Bilanțul nu a publicat probabilitățile pe cauze." : "Fără bilanț, nu putem separa pierderea normală de furt, contoare defecte sau clienți trecuți la postul greșit."}</p>
      )}
      <p className="mt-3 text-[12.5px] text-muted-foreground">Probabilități estimate de model; niciuna nu e confirmată de un om.</p>
    </Card>
  );

  const meterCard = (
    <Card title="Contoare în post" icon={Gauge} iconTone="blue" className="h-full">
      {meters.length ? (
        <table className="w-full text-[14px]">
          <thead className="text-left text-[13px] text-ink-soft">
            <tr className="border-b border-rule">
              <th scope="col" className="py-1.5 font-[500]">Contor</th>
              <th scope="col" className="py-1.5 font-[500]">Stare</th>
              <th scope="col" className="py-1.5 text-right font-[500]">Scor</th>
              <th scope="col" className="w-7"><span className="sr-only">Deschide</span></th>
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
                  <Link href={wi(w)} aria-label={`Deschide lucrarea contorului ${w.asset_id}`} className="inline-grid size-7 place-items-center rounded-full hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-ring">
                    <ChevronRight aria-hidden="true" size={18} />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">Niciun contor de sub acest post nu e semnalat de modelul A.</p>
      )}
    </Card>
  );

  const voltageCard = (
    <Card title="Tensiunea la prânz (P10–P90)" icon={Zap} iconTone="amber" className="h-full">
      {cItem && cSeries?.data ? (
        <>
          <SeriesChart series={cSeries.data} workItem={cItem} />
          <div className="mt-2"><SeriesLegend source="C" /></div>
        </>
      ) : (
        <p role="status" className="py-4 text-[15px] text-ink-soft">
          {cItem ? "Seria de tensiune nu e publicată încă." : "Acest post nu are lucrare de tensiune: nu se măsoară supratensiune aici."}
        </p>
      )}
    </Card>
  );

  const options = cItem ? remedyOptions(cItem).toSorted((a, b) => a.cost_lei - b.cost_lei) : [];
  const cChoice = cItem ? remedies?.data.find((r) => r.work_item_id === cItem.work_item_id) : undefined;
  const chosen = new Set(cItem ? ladderChoice(cItem, cChoice) : []);
  const ladderCard = (
    <Card title="Scară de remediere" icon={Layers} iconTone="violet" className="h-full">
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
                <Pill tone={on ? "blue" : "grey"} size="sm">{on ? "Ales" : o.p90_after_pu >= 1.1 ? "Nu ajunge" : "Neales"}</Pill>
              </li>
            );
          })}
        </ol>
      ) : bilant ? (
        <div className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3 py-2.5 text-[14.5px]">
          <span aria-hidden="true" className="grid size-7 place-items-center rounded-full border border-src-a bg-src-a text-[13px] font-[650] text-white">1</span>
          <span className="flex-1">{clean(ACTION_RO[bilant.recommended_action] ?? bilant.recommended_action)}</span>
          <Pill tone="blue" size="sm">Recomandat</Pill>
        </div>
      ) : (
        <p className="py-4 text-[15px] text-ink-soft">Nicio remediere propusă încă pentru acest post.</p>
      )}
    </Card>
  );

  const work = [bilant && { w: bilant, d: bd }, cItem && { w: cItem, d: cd }].filter((x): x is { w: WorkItem; d: typeof bd } => Boolean(x));
  const decisionText = work.length
    ? work.map(({ w, d }) => `${w.source === "C" ? "Tensiune" : "Bilanț"}: ${d ? DECISION_LABEL_RO[d.decision] : "fără decizie"}`).join("; ") + "."
    : "Postul nu are încă nicio lucrare în plan.";
  const works = (
    <Card className="h-full" bodyClassName="flex flex-wrap items-center gap-x-6 gap-y-3 !py-4">
      <div className="flex items-center gap-3">
        <HardHat aria-hidden="true" size={30} strokeWidth={1.5} className="text-att-ink" />
        <h2 className="text-[19px] font-[700]">Lucrări</h2>
      </div>
      <span className="h-8 w-px bg-rule max-md:hidden" aria-hidden="true" />
      <p className="min-w-[220px] flex-1 text-[15.5px]">{sentence(decisionText)}</p>
      <div className="flex flex-wrap items-center gap-2.5">
        {bd?.decision === "human_review" && bilant ? <ReviewActions workItemId={bilant.work_item_id} scenario={scenario} /> : null}
        {work.map(({ w }) => (
          <Link key={w.work_item_id} href={wi(w)} className={btn("outline")}>{work.length > 1 ? `Vezi lucrarea (${w.source === "C" ? "tensiune" : "bilanț"})` : "Vezi lucrarea"}</Link>
        ))}
        {crew ? <Link href={`/ordine/${encodeURIComponent(crew)}${q}`} className={btn("primary")}>Ordin de lucru</Link> : null}
      </div>
    </Card>
  );

  const ids = new Set([bilant?.work_item_id, cItem?.work_item_id, ...meters.map((m) => m.work_item_id)].filter(Boolean) as string[]);
  const audit = (view.data?.audit ?? []).filter((a) => a.work_item_id && ids.has(a.work_item_id)).toSorted((a, b) => b.ts.localeCompare(a.ts)).slice(0, 8);
  const journal = (
    <Card title="Jurnal" icon={ScrollText} iconTone="blue">
      {audit.length ? (
        <ul className="divide-y divide-rule text-[14.5px]">
          {audit.map((a) => (
            <li key={a.audit_id} className="flex flex-wrap items-baseline gap-x-4 gap-y-0.5 py-2">
              <span className="w-[220px] whitespace-nowrap text-ink-soft tabular-nums">{fmtMoment(a.ts)}</span>
              <span className="flex-1">{sentence(auditActionRo(a.action))}</span>
              <span className="text-ink-soft">{a.actor === "human" ? "om" : "agent"}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-[15px] text-ink-soft">Nicio intrare în jurnal pentru lucrările acestui post.</p>
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
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        <PageTitle
          icon={UtilityPole}
          title={`Post ${post.post_id}${place ? ` ${place}` : ""}${post.synthetic !== false ? " (sintetic)" : ""}`}
          subtitle="Bilanț, contoare, tensiune, cauze și remediere."
        />
        <PostSections sections={sections} stare={stare} initial={parseSection(typeof sp.sectiune === "string" ? sp.sectiune : null)} />
        <p className="mt-5 text-[13px] text-muted-foreground">
          Postul e unitatea comună: contoarele (A), bilanțul și tensiunea (C) se întâlnesc aici. {fmtInt(post.meters_flagged ?? 0)} contoare semnalate.
        </p>
      </div>
    </AppShell>
  );
}
