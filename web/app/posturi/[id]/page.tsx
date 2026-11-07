import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { RemedyLadder } from "@/components/detail/remedy-ladder";
import { ReviewActions } from "@/components/detail/review-actions";
import { SeriesChart, SeriesLegend } from "@/components/detail/series-chart";
import { isBilantSeries } from "@/lib/series-utils";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { Disclosure } from "@/components/simple/disclosure";
import { VerdictBlock } from "@/components/simple/verdict-block";
import { AppShell } from "@/components/shell/app-shell";
import type { WorkItem } from "@/lib/contracts";
import { getSeries } from "@/lib/data";
import { clampPercentRo, factorLabelRo, DECISION_LABEL_RO, predictionLabelRo, ruleRo } from "@/lib/data/labels";
import { scoreText } from "@/lib/human";
import { getPosts } from "@/lib/data/posts";
import { getRemedies } from "@/lib/data/remedies";
import { BILANT_LABEL, bilantFusion, ladderBaseP90, remedyOptions } from "@/lib/extras";
import { fmtDec, fmtInt, fmtScore, sentence } from "@/lib/format";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { approxLei } from "@/lib/human";
import { ladderChoice } from "@/lib/extras";
import { postVerdictRo } from "@/lib/verdict";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";

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

const STATUS: Record<string, { label: string; color: string }> = {
  verde: { label: "pierderi mici", color: "#2f8f5b" },
  galben: { label: "pierderi de urmărit", color: "#d9a400" },
  roșu: { label: "pierderi mari", color: "#c8321e" },
  necunoscut: { label: "fără bilanț încă", color: "#9aa4a9" },
};

async function Post({ params, searchParams }: Pick<PageProps<"/posturi/[id]">, "params" | "searchParams">) {
  await connection();
  const id = safeDecode((await params).id);
  const scenario = await resolveScenario(searchParams);
  const [{ info }, posts, view, remedies] = await Promise.all([
    loadShellInfo(scenario),
    getPosts(scenario),
    loadPlanView(scenario),
    getRemedies(scenario).catch(() => null),
  ]);
  const post = posts.data.find((p) => p.post_id === id);
  const items = view.data?.workItems ?? [];
  const decisions = view.data?.decisionsByWorkItemId ?? {};
  const byId = new Map(items.map((w) => [w.work_item_id, w]));

  if (!post) {
    return (
      <AppShell info={info}>
        <div className="mx-auto max-w-[680px] px-7 py-20">
          <Link href="/" className="text-[15px] underline decoration-rule underline-offset-4">
            Înapoi la planul de mâine
          </Link>
          <h1 className="mt-6 text-[26px] font-[650]">Postul {id} nu apare în scenariul „{scenario}”</h1>
          <p className="mt-3 text-[16px] text-muted-foreground">Alege un post din harta planului, în modul „Posturile”.</p>
        </div>
      </AppShell>
    );
  }

  const bilant = post.bilant_work_item_id ? byId.get(post.bilant_work_item_id) : undefined;
  const cItem = post.c_work_item_id ? byId.get(post.c_work_item_id) : undefined;
  const meters = (post.meter_work_item_ids ?? []).map((m) => byId.get(m)).filter((w): w is WorkItem => Boolean(w));
  const meterRows = meters.toSorted((a, b) => b.prediction.score - a.prediction.score);
  const [bilantSeries, cSeries] = await Promise.all([
    bilant ? getSeries(bilant.work_item_id, scenario) : Promise.resolve(null),
    cItem ? getSeries(cItem.work_item_id, scenario) : Promise.resolve(null),
  ]);
  const status = STATUS[post.color ?? "necunoscut"] ?? STATUS.necunoscut;
  const bilantDecision = bilant ? decisions[bilant.work_item_id] : undefined;
  const cDecision = cItem ? decisions[cItem.work_item_id] : undefined;
  const options = cItem ? remedyOptions(cItem) : [];
  const cChoice = cItem ? remedies?.data.find((r) => r.work_item_id === cItem.work_item_id) : undefined;
  const chosen = cItem ? ladderChoice(cItem, cChoice) : [];
  // lipsa pe zi: din /posts, altfel din estimarea bilanțului (media pe 14 zile)
  const lossKwhDay = post.loss_kwh_day ?? bilant?.prediction.point_estimate ?? null;
  const cause = bilant ? (bilant.prediction.label === "normal" ? null : predictionLabelRo(bilant.prediction.label)) : post.diagnosis;
  const verdict = postVerdictRo({
    postId: post.post_id,
    lossLeiMonth: post.loss_lei_month,
    causeRo: cause,
    chosen: chosen.length > 1 ? chosen : [],
    costLei: cChoice?.cost_lei ?? null,
    metersFlagged: post.meters_flagged,
  });
  const place = [post.label && post.label !== post.post_id ? post.label : post.zone_id, post.approx_position ? "poziție aproximativă (media contoarelor)" : null]
    .filter(Boolean)
    .join(", ");

  return (
    <AppShell info={info}>
      <section className="border-b border-rule bg-panel">
        <div className="mx-auto flex max-w-[1100px] flex-wrap items-center gap-x-5 gap-y-2 px-7 py-3.5">
          <Link href="/posturi" className="text-[15px] text-muted-foreground underline decoration-rule underline-offset-4 hover:text-ink">
            Toate posturile
          </Link>
          <span className="h-5 w-px bg-rule" aria-hidden="true" />
          <span className="size-5 shrink-0 rounded-full" style={{ background: status.color }} aria-hidden="true" />
          <span translate="no" className="code-id text-[15px]">{post.post_id}</span>
          <span className="text-[15px] text-muted-foreground">{place || "fără locație în registru"}</span>
        </div>
      </section>

      <div className="mx-auto max-w-[1100px] space-y-10 px-7 pt-10 pb-20 text-[18px] leading-[1.5]">
        <VerdictBlock verdict={verdict}>
          {bilantDecision?.decision === "human_review" ? (
            <div role="group" aria-labelledby="hr-title" className="max-w-[640px] border-l-[3px] border-att bg-att-surface px-5 py-4">
              <h2 id="hr-title" className="text-[20px] font-[620] text-att-ink">Nu sunt sigur: decide tu</h2>
              <p className="mt-1 mb-3 text-[16px]">{bilantDecision.reason_ro}</p>
              <ReviewActions workItemId={bilant!.work_item_id} scenario={scenario} />
            </div>
          ) : null}
        </VerdictBlock>

        <section aria-labelledby="bal-title">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 id="bal-title" className="text-[20px] font-[620]">
              Energia ieșită din post față de suma clienților
            </h2>
            <span className="flex items-center gap-2 text-[14px] text-muted-foreground">
              <SyntheticGlyph size={14} /> {BILANT_LABEL}
            </span>
          </div>
          <div className="mt-3 border-y border-rule bg-panel px-4 pt-3 pb-4">
            {bilantSeries?.data ? (
              <>
                <SeriesChart series={bilantSeries.data} workItem={bilant!} />
                <div className="mt-2">
                  <SeriesLegend source="A" bilant={isBilantSeries(bilantSeries.data)} series={bilantSeries.data} />
                </div>
              </>
            ) : (
              <div role="status" className="py-8 text-[15px]">
                <p className="font-[560]">{bilant ? "Seria bilanțului pentru grafic nu e publicată încă." : "Bilanțul pe acest post nu e calculat încă."}</p>
                <p className="mt-1 max-w-[70ch] text-muted-foreground">
                  Bilanțul compară energia ieșită din post cu suma contoarelor clienților de sub el. Lipsa peste normal arată
                  unde se pierd bani.{" "}
                  {bilant
                    ? "Cifrele și cauza de mai jos vin deja din bilanț; graficul apare când firul bilanțului publică seria."
                    : `Până vine bilanțul, pierderea afișată e estimată din contoarele semnalate de modelul A${posts.lossCost ? ` (kWh pe zi × scor × 30 de zile × ${fmtDec(posts.lossCost.value, 2)} lei/kWh)` : ""}.`}
                </p>
              </div>
            )}
          </div>
        </section>

        <section aria-labelledby="sum-title">
          <h2 id="sum-title" className="text-[20px] font-[620]">
            Pe scurt
          </h2>
          <dl className="mt-2 grid grid-cols-[minmax(0,15rem)_minmax(0,1fr)] gap-x-6 [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-2 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-2 [&>dt]:text-muted-foreground">
            <dt>Pierderi pe lună</dt>
            <dd>
              {post.loss_lei_month != null ? `${approxLei(post.loss_lei_month)}, ${status.label}` : "necunoscute"}
              {post.derived ? <span className="block text-[14px] text-muted-foreground">estimat din contoarele semnalate de A</span> : null}
            </dd>
            <dt>Contoare semnalate</dt>
            <dd>{fmtInt(post.meters_flagged ?? 0)}</dd>
            <dt>Tensiunea maximă</dt>
            <dd>{post.voltage_p90_pu != null ? `${fmtDec(post.voltage_p90_pu, 2)} față de limita de 1,10` : "–"}</dd>
          </dl>
        </section>

        <div className="border-b border-rule">
          <Disclosure title="Cauza probabilă" hint="explicația bilanțului și factorii">
            {bilant ? (
              <>
                <p className="max-w-[72ch] text-[16.5px]">
                  {post.diagnosis && !/cauza probabilă/i.test(bilant.explanation.summary_ro) ? `${sentence(post.diagnosis)} ` : ""}
                  {clampPercentRo(bilant.explanation.summary_ro)}
                </p>
                <ul className="mt-3 space-y-1.5 text-[15.5px]">
                  {bilant.explanation.top_factors.map((f) => (
                    <li key={f.feature} className="flex justify-between gap-6 border-t border-rule pt-1.5">
                      <span>{factorLabelRo(f.label_ro)}</span>
                      <span className="font-[600] tabular-nums">
                        {f.contribution >= 0 ? "+" : "−"}
                        {fmtScore(Math.abs(f.contribution))}
                      </span>
                    </li>
                  ))}
                </ul>
                {bilantDecision ? (
                  <p className="mt-3 text-[15px]">
                    <span translate="no" className="code-id">{bilantDecision.rule_id}</span>{" "}
                    <span className="text-muted-foreground">{ruleRo(bilantDecision.rule_id) ?? ""}</span>: {bilantDecision.reason_ro}
                  </p>
                ) : null}
              </>
            ) : (
              <p className="max-w-[72ch] text-[16px] text-muted-foreground">
                Fără bilanț, nu putem separa pierderea normală de rețea de furt, contoare defecte sau clienți trecuți la postul greșit.
                Contoarele de mai jos sunt semnalate independent de modelul A.
              </p>
            )}
          </Disclosure>

          <Disclosure title="Contoarele de pe post" hint={meterRows.length ? `${meterRows.length} semnalate de modelul A` : "niciunul semnalat"}>
            {meterRows.length ? (
              <ul className="divide-y divide-rule border-y border-rule">
                {meterRows.map((w) => {
                  const d = decisions[w.work_item_id];
                  const fusion = bilantFusion(w);
                  const kwh = (w.extra as Record<string, unknown> | undefined)?.estimated_kwh_lost_per_day;
                  return (
                    <li key={w.work_item_id} className="grid grid-cols-[36px_minmax(0,1.2fr)_minmax(0,1fr)_110px_minmax(0,1fr)] items-center gap-x-4 py-2.5 text-[15px]">
                      <span className="block size-9" dangerouslySetInnerHTML={{ __html: markerSvg({ source: "A", kind: markerKind(d?.decision) }) }} />
                      <Link href={`/lucrari/${encodeURIComponent(w.work_item_id)}`} translate="no" className="code-id underline decoration-rule underline-offset-4 hover:decoration-ink">
                        {w.asset_id}
                      </Link>
                      <span className="text-muted-foreground">{predictionLabelRo(w.prediction.label)}</span>
                      <span className="text-right tabular-nums">
                        <b className="font-[620]">{scoreText(w.prediction.score)}</b>
                        {typeof kwh === "number" ? <span className="block text-[13.5px] text-muted-foreground">{fmtDec(kwh, 1)} kWh/zi</span> : null}
                      </span>
                      <span>
                        {d ? DECISION_LABEL_RO[d.decision] : "fără decizie"}
                        {fusion ? <span className="block text-[13.5px] font-[560] text-ink">confirmat de bilanț: {fmtScore(fusion.a_score)} → {fmtScore(fusion.combined_score)}</span> : null}
                      </span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-[15px] text-muted-foreground">Niciun contor de sub acest post nu e semnalat de modelul A.</p>
            )}
          </Disclosure>

          {cItem ? (
            <Disclosure title="Tensiunea la prânz" hint="sursa C: graficul și decizia">
              <p className="max-w-[72ch] text-[16px]">{clampPercentRo(cItem.explanation.summary_ro)}</p>
              {cDecision ? (
                <p className="mt-2 text-[15px]">
                  Decizia: <b className="font-[600]">{DECISION_LABEL_RO[cDecision.decision]}</b>, <span translate="no" className="code-id">{cDecision.rule_id}</span>.
                </p>
              ) : null}
              {cSeries?.data ? (
                <div className="mt-3 border-y border-rule bg-panel px-3 pt-2 pb-3">
                  <SeriesChart series={cSeries.data} workItem={cItem} />
                  <SeriesLegend source="C" />
                </div>
              ) : null}
              <Link href={`/lucrari/${encodeURIComponent(cItem.work_item_id)}`} className="mt-3 inline-block text-[15px] font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink">
                Deschide lucrarea de tensiune
              </Link>
            </Disclosure>
          ) : null}

          {options.length && cItem ? (
            <Disclosure title="Scara de soluții" hint="pentru tensiune, de la cea mai ieftină">
              <RemedyLadder
                options={options}
                decision={cDecision ?? null}
                recommended={cItem.recommended_action}
                p90Before={ladderBaseP90(cItem, cChoice)}
                choice={cChoice ?? null}
              />
            </Disclosure>
          ) : null}

          <Disclosure title="Cifrele exacte" hint="lei, kWh, tensiune, culoarea de pe hartă">
            <dl className="grid grid-cols-[minmax(0,15rem)_minmax(0,1fr)] gap-x-6 text-[15.5px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-1.5 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-1.5 [&>dt]:text-muted-foreground">
              <dt>Pierderi pe lună</dt>
              <dd>{post.loss_lei_month != null ? `${fmtInt(post.loss_lei_month)} lei` : "necunoscute"}</dd>
              <dt>Lipsă pe zi</dt>
              <dd>
                {lossKwhDay == null
                  ? "–"
                  : lossKwhDay >= 0
                    ? `${fmtDec(lossKwhDay, 1)} kWh peste pierderea normală`
                    : `fără lipsă; clienții arată cu ${fmtDec(-lossKwhDay, 1)} kWh mai mult`}
              </dd>
              <dt>Tensiune maximă P90</dt>
              <dd>{post.voltage_p90_pu != null ? `${fmtDec(post.voltage_p90_pu, 3).replace(/0$/, "")} pu (limita 1,10)` : "–"}</dd>
              <dt>Culoarea pe hartă</dt>
              <dd>
                {status.label}; praguri de afișare: {fmtInt(posts.thresholds.yellow)} și {fmtInt(posts.thresholds.red)} lei pe lună
              </dd>
            </dl>
          </Disclosure>
        </div>

        <p className="text-[13.5px] text-muted-foreground">
          Postul e unitatea comună: contoarele (A), bilanțul și tensiunea (C) se întâlnesc aici.{" "}
          {posts.derived
            ? "Până vine bilanțul, posturile sunt derivate din lucrările planului (contoarele A pe post și posturile C)."
            : `Datele: ${posts.detail ?? "API"}.`}
        </p>
      </div>
    </AppShell>
  );
}
