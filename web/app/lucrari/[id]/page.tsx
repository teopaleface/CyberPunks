import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { RemedyLadder } from "@/components/detail/remedy-ladder";
import { ReviewActions } from "@/components/detail/review-actions";
import { SeriesChart, SeriesLegend } from "@/components/detail/series-chart";
import { isBilantSeries } from "@/lib/series-utils";
import { ScoreScale } from "@/components/plan/score-scale";
import { Disclosure } from "@/components/simple/disclosure";
import { VerdictBlock, shortTitle } from "@/components/simple/verdict-block";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { AppShell } from "@/components/shell/app-shell";
import type { AuditRecord, Decision, WorkItem } from "@/lib/contracts";
import { getSeries, getWorkItem } from "@/lib/data";
import { getRemedies } from "@/lib/data/remedies";
import { auditActionRo, clampPercentRo, factorLabelRo,
  ACTION_RO,
  CONFIDENCE_RO,
  DECISION_LABEL_RO,
  SKILL_RO,
  SOURCE_LABEL_RO,
  outcomeRo,
  ruleRo,
  thresholdLabelRo,
  thresholdValueRo,
} from "@/lib/data/labels";
import { BILANT_LABEL, bilantFusion, isBilantPost, ladderBaseP90, ladderChoice, remedyOptions } from "@/lib/extras";
import { fmtDayMonth, fmtDec, fmtDuration, fmtInt, fmtLei, fmtMoment, fmtPercent, fmtScore, fmtTime, isWholeDay, plural, sentence } from "@/lib/format";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { itemPlace } from "@/lib/plan-screen";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { SOURCES } from "@/lib/sources";
import { scoreText } from "@/lib/human";
import { verdictRo } from "@/lib/verdict";

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default function WorkItemPage({ params, searchParams }: PageProps<"/lucrari/[id]">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Se încarcă lucrarea…</span>
      </div>}>
      <Detail params={params} searchParams={searchParams} />
    </Suspense>
  );
}

/** Seturile de date externe pe care au fost antrenate sau validate modelele (din sursele citate). */
const EXTERNAL = /SGCC|London|Londra|EAGLE|SimBench|PVGIS|Open-Meteo|ENTSO/i;

async function Detail({ params, searchParams }: Pick<PageProps<"/lucrari/[id]">, "params" | "searchParams">) {
  await connection();
  const id = safeDecode((await params).id);
  const scenario = await resolveScenario(searchParams);
  const [{ info }, result, series, remedies] = await Promise.all([
    loadShellInfo(scenario),
    getWorkItem(id, scenario),
    getSeries(id, scenario),
    id.startsWith("C-") ? getRemedies(scenario).catch(() => null) : Promise.resolve(null),
  ]);
  const detail = result.data;

  if (!detail) {
    return (
      <AppShell info={info}>
        <div className="mx-auto max-w-[680px] px-7 py-20">
          <Link href="/" className="text-[15px] underline decoration-rule underline-offset-4">
            Înapoi la planul de mâine
          </Link>
          <h1 className="mt-6 text-[26px] font-[650]">Lucrarea {id} nu există în scenariul „{scenario}”</h1>
          <p className="mt-3 text-[16px] text-muted-foreground">
            Poate a fost respinsă la intrare sau vine din alt scenariu. Verifică jurnalul deciziilor sau alege alt scenariu din antet.
          </p>
        </div>
      </AppShell>
    );
  }

  const { workItem: w, decision, audit, invalid } = detail;
  const meta = SOURCES[w.source];
  const p = w.prediction;
  const options = w.source === "C" ? remedyOptions(w) : [];
  // la tensiune, agentul alege o combinație de trepte; antetul o arată pe ea, nu doar tipul deciziei
  const chosenCombo = w.source === "C" ? ladderChoice(w, remedies?.data.find((r) => r.work_item_id === w.work_item_id)) : [];
  const choice = remedies?.data.find((r) => r.work_item_id === w.work_item_id);
  const verdict = verdictRo(w, decision, { chosen: chosenCombo, costLei: choice?.cost_lei ?? null });
  const fusion = bilantFusion(w);
  // confirmarea vine din pragurile deciziei (fusion_confirmed); altfel din nota bilanțului
  const fusionConfirmed =
    typeof decision?.threshold?.fusion_confirmed === "boolean"
      ? (decision.threshold.fusion_confirmed as boolean)
      : fusion && /nu confirmă/i.test(fusion.note_ro)
        ? false
        : null;
  const summary = clampPercentRo(w.explanation.summary_ro);
  const summaryShort = summary.length <= 220;
  const chartTitle = series.data?.title_ro ?? "Ce vede modelul";
  const external = w.data_quality.data_sources.filter((s) => EXTERNAL.test(s));
  const scoreMin = typeof decision?.threshold?.score_min === "number" ? decision.threshold.score_min : null;

  return (
    <AppShell info={info}>
      {/* antetul, subțire: înapoi, codul lucrării, locul */}
      <section className="border-b border-rule bg-panel">
        <div className="mx-auto flex max-w-[1100px] flex-wrap items-center gap-x-5 gap-y-2 px-7 py-3.5">
          <Link href={`/?scenariu=${encodeURIComponent(scenario)}`} className="text-[15px] text-muted-foreground underline decoration-rule underline-offset-4 hover:text-ink">
            Planul de mâine
          </Link>
          <span className="h-5 w-px bg-rule" aria-hidden="true" />
          <span className="size-7 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source: w.source, kind: markerKind(decision?.decision) }) }} />
          <span className="code-id text-[15px]" translate="no">{w.work_item_id}</span>
          <span className="text-[15px] text-muted-foreground">{itemPlace(w)}</span>
        </div>
      </section>

      <div className="mx-auto max-w-[1100px] space-y-10 px-7 pt-10 pb-20 text-[18px] leading-[1.5]">
        <VerdictBlock verdict={verdict}>
          {invalid ? (
            <span className="inline-block rounded-[4px] border border-att px-3 py-1.5 text-[16px] font-[600] text-att-ink">Respinsă la intrare: date greșite</span>
          ) : decision && chosenCombo.length > 1 ? null : decision ? (
            <span
              className={
                "inline-block rounded-[4px] px-3 py-1.5 text-[16px] font-[600] " +
                (decision.decision === "human_review" ? "bg-att text-on-att" : "bg-ink text-panel")
              }
            >
              {sentence(DECISION_LABEL_RO[decision.decision]).replace(/\.$/, "")}
              {decision.crew_id ? `, ${decision.crew_id}` : ""}
            </span>
          ) : (
            <span className="inline-block rounded-[4px] border border-rule px-3 py-1.5 text-[16px]">Fără decizie în plan</span>
          )}
          {decision?.decision === "human_review" ? (
            <div aria-labelledby="hr-title" role="group" className="max-w-[640px] border-l-[3px] border-att bg-att-surface px-5 py-4">
              <h2 id="hr-title" className="text-[20px] font-[620] text-att-ink">
                Nu sunt sigur: decide tu
              </h2>
              <p className="mt-1 mb-3 text-[16px]">{p.abstain_reason ? sentence(p.abstain_reason) : decision.reason_ro}</p>
              <ReviewActions workItemId={w.work_item_id} scenario={scenario} />
            </div>
          ) : null}
        </VerdictBlock>

        {/* graficul principal */}
        <section aria-labelledby="chart-title">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 id="chart-title" title={chartTitle} className="text-[20px] font-[620]">
              {shortTitle(chartTitle)}
            </h2>
            {series.data ? (
              <span className="flex items-center gap-2 text-[14px] text-muted-foreground">
                {series.data.synthetic ? (
                  <>
                    <SyntheticGlyph size={14} /> Date sintetice
                  </>
                ) : (
                  "Date reale"
                )}
                {series.source === "fixtures" ? ", exemplu de test" : series.source === "demo" ? ", ultimul plan salvat" : ""}
              </span>
            ) : null}
          </div>
          <div className="mt-3 border-y border-rule bg-panel px-4 pt-3 pb-4">
            {series.data ? (
              <>
                <SeriesChart series={series.data} workItem={w} />
                <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
                  <SeriesLegend source={series.data.source} bilant={isBilantSeries(series.data)} series={series.data} />
                  {series.data.annotations?.length ? (
                    <span className="text-[14px] text-muted-foreground">
                      {series.data.annotations.map((a) => `${isWholeDay(String(a.t)) ? fmtDayMonth(String(a.t)) : fmtTime(String(a.t))}: ${clampPercentRo(a.label_ro)}`).join("; ")}
                    </span>
                  ) : null}
                </div>
              </>
            ) : (
              <p className="py-10 text-center text-[15px] text-muted-foreground">
                Seria pentru grafic nu e disponibilă ({series.degradedReason ?? "sursa n-a trimis-o"}). Explicația de mai jos vine direct din model.
              </p>
            )}
          </div>
        </section>

        {summaryShort ? (
          <section aria-labelledby="mean-title">
            <h2 id="mean-title" className="text-[20px] font-[620]">
              Ce înseamnă
            </h2>
            <p className="mt-1.5 max-w-[72ch]">{summary}</p>
          </section>
        ) : null}

        {/* tot restul, la un click */}
        <div className="border-b border-rule">
          {options.length ? (
            <Disclosure title="Scara de soluții" hint="de la cea mai ieftină la cea mai scumpă">
              <p className="mb-3 max-w-[72ch] text-[15px] text-muted-foreground">
                Punctul arată P90 al tensiunii maxime după soluție; linia portocalie e limita.
              </p>
              <RemedyLadder
                options={options}
                decision={decision}
                recommended={w.recommended_action}
                p90Before={ladderBaseP90(w, choice)}
                choice={choice ?? null}
              />
            </Disclosure>
          ) : null}

          {fusion ? (
            <Disclosure
              title={`Verificat cu bilanțul postului ${fusion.post_id}`}
              hint={fusionConfirmed === true ? "bilanțul confirmă" : fusionConfirmed === false ? "bilanțul nu confirmă; scorul rămâne al modelului A" : "a doua sursă, independentă"}
            >
              <p className="max-w-[72ch] text-[16px]">{fusion.note_ro}</p>
              <p className="mt-2 text-[15.5px]">
                Scorul contorului: {fmtScore(fusion.a_score)} → {fmtScore(fusion.combined_score)} după confirmare. La post lipsesc{" "}
                {fmtDec(fusion.post_excess_loss_kwh_day, 1)} kWh pe zi peste normal ({fmtLei(fusion.post_excess_loss_lei_month)} pe lună).
              </p>
              <p className="mt-2 text-[13.5px] text-muted-foreground">{BILANT_LABEL}</p>
            </Disclosure>
          ) : null}

          <Disclosure title="De ce a ieșit așa" hint="factorii modelului și cazuri asemănătoare">
            <div className="space-y-8 text-[16px]">
              {!summaryShort ? <p className="max-w-[72ch] text-[17px]">{summary}</p> : null}
              <div>
                <h3 className="text-[17px] font-[620]">Ce a cântărit modelul</h3>
                <Factors w={w} />
              </div>
              {w.explanation.similar_cases?.length ? (
                <div>
                  <h3 className="text-[17px] font-[620]">Cazuri asemănătoare din istoric</h3>
                  <ul className="mt-3 divide-y divide-rule border-y border-rule">
                    {w.explanation.similar_cases.map((c) => (
                      <li key={c.case_id} className="grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_160px] items-center gap-4 py-2.5 text-[15px]">
                        <span translate="no" className="code-id">{c.case_id}</span>
                        <span>
                          {outcomeRo(c.outcome)}
                          {c.note_ro ? <span className="block text-[14px] text-muted-foreground">{c.note_ro}</span> : null}
                        </span>
                        <span className="flex items-center gap-2">
                          <span className="relative h-2 flex-1 bg-muted" aria-hidden="true">
                            <i className="absolute inset-y-0 left-0 bg-ink" style={{ width: `${(c.similarity * 100).toFixed(0)}%` }} />
                          </span>
                          <span className="w-10 text-right tabular-nums">{fmtScore(c.similarity)}</span>
                        </span>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-1.5 text-[13.5px] text-muted-foreground">Similaritatea compară factorii acestei lucrări cu ai cazurilor din setul de antrenare.</p>
                </div>
              ) : null}
            </div>
          </Disclosure>

          <Disclosure title="Detalii tehnice" hint="regula, pragurile, valoare și cost, încrederea">
            <div className="space-y-8 text-[16px]">
              <span className="flex w-fit items-center gap-2 rounded-[4px] border border-rule px-2.5 py-1 text-[14px]">
                <span className="size-2.5 rounded-full" style={{ background: meta.color }} aria-hidden="true" />
                {meta.letter} {meta.name}: {meta.problem}
              </span>
              <DecisionBlock w={w} decision={decision} />
              <div>
                <h3 className="text-[17px] font-[620]">Încrederea modelului</h3>
                <div className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2">
                  <span className="num-wide text-[44px]">{scoreText(p.score)}</span>
                  <ScoreScale score={p.score} low={p.interval_low} high={p.interval_high} threshold={scoreMin} width={180} tone={decision?.decision === "human_review" ? "att" : "ink"} />
                  <span className="text-[14.5px] leading-snug text-muted-foreground">
                    {p.interval_low != null && p.interval_high != null ? `interval ${fmtScore(p.interval_low)}–${fmtScore(p.interval_high)}` : "fără interval"}
                    <br />
                    {CONFIDENCE_RO[p.confidence]}
                    {scoreMin != null ? `, pragul regulii ${fmtScore(scoreMin)}` : ""}
                  </span>
                </div>
                <p className="mt-2 text-[14.5px] text-muted-foreground">
                  Scorul e o probabilitate calibrată ca problema să fie reală.
                  {p.abstain ? " Modelul a spus singur „nu sunt sigur”, așa că agentul nu trimite echipa fără un om." : ""}
                </p>
              </div>
            </div>
          </Disclosure>

          <Disclosure title="Datele de intrare" hint="sintetice sau reale, surse, probleme găsite">
            <ul className="space-y-1.5 text-[15.5px]">
              <li className="flex items-center gap-2">
                {w.data_quality.synthetic ? (
                  <>
                    <SyntheticGlyph size={14} /> Activ sintetic, pus pe harta reală
                  </>
                ) : (
                  "Date reale"
                )}
              </li>
              {external.length ? <li>Model validat pe date externe: {external.join(", ")}</li> : null}
              <li>Date lipsă: {fmtPercent(w.data_quality.missing_ratio, 1)}</li>
              <li>Surse: {w.data_quality.data_sources.join(", ")}</li>
              {w.data_quality.input_issues?.length ? (
                <li>
                  Probleme găsite la intrare și cum au fost tratate:
                  <ul className="mt-1 list-disc pl-5 text-[14.5px]">
                    {w.data_quality.input_issues.map((i) => (
                      <li key={i}>{i}</li>
                    ))}
                  </ul>
                </li>
              ) : (
                <li className="text-muted-foreground">Nicio problemă găsită la intrare.</li>
              )}
            </ul>
            <p className="mt-3 text-[13.5px] text-muted-foreground">
              Datele vin din: {SOURCE_LABEL_RO[result.source]}
              {result.degradedReason ? `. ${result.degradedReason}` : ""}.
            </p>
          </Disclosure>

          <Disclosure title="Urmărirea până la model" hint="ID-uri, model, jurnalul deciziei">
            <dl className="grid grid-cols-[150px_minmax(0,1fr)] gap-x-4 text-[15px] [&_dd]:border-t [&_dd]:border-rule [&_dd]:py-1.5 [&_dt]:border-t [&_dt]:border-rule [&_dt]:py-1.5 [&_dt]:text-muted-foreground">
              <dt>ID predicție</dt>
              <dd className="dense font-[560] break-all">{p.prediction_id}</dd>
              <dt>Model</dt>
              <dd className="dense font-[560]">{p.model_id}</dd>
              <dt>Versiune</dt>
              <dd className="dense font-[560]">{p.model_version}</dd>
              <dt>Estimat la</dt>
              <dd>{fmtMoment(w.created_at)}</dd>
              {decision ? (
                <>
                  <dt>ID decizie</dt>
                  <dd className="dense font-[560] break-all">{decision.audit_id}</dd>
                </>
              ) : null}
            </dl>
            <AuditTrail audit={audit} />
          </Disclosure>
        </div>

        {isBilantPost(w) && !fusion ? <p className="text-[13.5px] text-muted-foreground">{BILANT_LABEL}</p> : null}
      </div>
    </AppShell>
  );
}

function Factors({ w }: { w: WorkItem }) {
  const max = Math.max(0.0001, ...w.explanation.top_factors.map((f) => Math.abs(f.contribution)));
  return (
    <div className="mt-4 space-y-2.5">
      {w.explanation.top_factors.map((f) => (
        <div key={f.feature} className="grid grid-cols-[minmax(0,1fr)_minmax(140px,240px)_56px] items-center gap-x-4 text-[16px]">
          <span>
            {factorLabelRo(f.label_ro)}
            <span className="dense ml-2 text-[13px] text-muted-foreground">{f.feature}</span>
          </span>
          <span className="relative h-3 bg-muted" aria-hidden="true">
            <i
              className="absolute inset-y-0 left-0"
              style={{ width: `${((Math.abs(f.contribution) / max) * 100).toFixed(1)}%`, background: f.contribution >= 0 ? "var(--ink)" : "var(--idle)" }}
            />
          </span>
          <span className="text-right font-[620] tabular-nums">
            {f.contribution >= 0 ? "+" : "−"}
            {fmtScore(Math.abs(f.contribution))}
          </span>
        </div>
      ))}
      <p className="text-[13.5px] text-muted-foreground">
        Contribuția fiecărui factor la scor (valori SHAP din modelul antrenat). Barele închise ridică scorul, cele deschise îl coboară.
      </p>
    </div>
  );
}

function DecisionBlock({ w, decision }: { w: WorkItem; decision: Decision | null }) {
  if (!decision) {
    return (
      <section>
        <h3 className="text-[17px] font-[620]">Decizia agentului</h3>
        <p className="mt-2 text-[15px] text-muted-foreground">Lucrarea nu are încă o decizie în planul curent.</p>
      </section>
    );
  }
  const t = decision.threshold ?? {};
  const costKeys = ["cost_lei", "visit_cost_lei", "preposition_cost_lei", "tap_cost_lei", "tap_change_visit_cost_lei", "chosen_cost_lei"];
  const costKey = costKeys.find((k) => typeof t[k] === "number");
  const cost = costKey ? (t[costKey] as number) : null;
  const ev = w.impact.expected_value_lei;
  const max = Math.max(ev, cost ?? 0) || 1;
  const rule = ruleRo(decision.rule_id);

  return (
    <section aria-labelledby="dec-title">
      <h3 id="dec-title" className="text-[17px] font-[620]">
        Decizia agentului
      </h3>
      <p className="mt-1.5 text-[16.5px] leading-relaxed">{decision.reason_ro.charAt(0).toLocaleUpperCase("ro-RO") + decision.reason_ro.slice(1)}</p>
      <div className="mt-3 flex flex-wrap items-baseline gap-x-3">
        <span translate="no" className="code-id text-[16px]">{decision.rule_id}</span>
        <span className="text-[15px] text-muted-foreground">
          {[rule, decision.rank ? `locul ${decision.rank} în prioritate` : null].filter(Boolean).join(", ")}
        </span>
      </div>
      {Object.keys(t).length ? (
        <dl className="mt-2 grid grid-cols-[minmax(0,1fr)_auto] gap-x-6 text-[15px] [&_dd]:border-t [&_dd]:border-rule [&_dd]:py-1.5 [&_dd]:text-right [&_dd]:tabular-nums [&_dt]:border-t [&_dt]:border-rule [&_dt]:py-1.5 [&_dt]:text-muted-foreground">
          {Object.entries(t).map(([k, v]) => (
            <div key={k} className="contents">
              <dt title={k}>{thresholdLabelRo(k)}</dt>
              <dd>{thresholdValueRo(k, v)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {cost != null ? (
        <div className="mt-4 space-y-1.5 text-[14.5px]">
          <div className="flex items-center gap-3">
            <span className="h-3 bg-ink" style={{ width: `${((ev / max) * 70).toFixed(1)}%` }} aria-hidden="true" />
            <span className="whitespace-nowrap">valoare așteptată {fmtLei(ev)}</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="h-3 bg-input" style={{ width: `${((cost / max) * 70).toFixed(1)}%` }} aria-hidden="true" />
            <span className="whitespace-nowrap text-muted-foreground">cost {fmtLei(cost)}</span>
          </div>
          <p className="text-muted-foreground">
            Valoarea așteptată = scorul × {fmtLei(w.impact.value_if_true_lei)} (cât se câștigă dacă problema e reală). Ipotezele: config/economics.yaml, cheia „
            {w.impact.assumptions_ref ?? "–"}”.
          </p>
        </div>
      ) : null}
      <dl className="mt-4 grid grid-cols-[150px_minmax(0,1fr)] gap-x-4 text-[15px] [&_dd]:py-1 [&_dt]:py-1 [&_dt]:text-muted-foreground">
        <dt>Recomandarea modelului</dt>
        <dd>{ACTION_RO[w.recommended_action]}</dd>
        <dt>Efort</dt>
        <dd>
          {fmtDuration(w.effort.duration_min)}
          {w.effort.crew_size != null ? `, ${plural(w.effort.crew_size, "om", "oameni")}` : ""}, {SKILL_RO[w.effort.crew_skill]}
          {w.effort.requires_planned_outage ? ", cere întrerupere planificată" : ""}
        </dd>
        <dt>Clienți afectați</dt>
        <dd>{fmtInt(w.impact.customers_affected ?? 0)}</dd>
        <dt>Urgență</dt>
        <dd>în {plural(Math.round(w.impact.urgency_hours), "oră", "ore")}{w.impact.safety_flag ? ", cu risc pentru oameni" : ""}</dd>
      </dl>
    </section>
  );
}

function AuditTrail({ audit }: { audit: AuditRecord[] }) {
  if (!audit.length) return null;
  const sorted = audit.toSorted((a, b) => a.ts.localeCompare(b.ts));
  return (
    <ol className="mt-3 space-y-2 border-l-2 border-rule pl-4">
      {sorted.map((a) => (
        <li key={a.audit_id} className="text-[14.5px]">
          <span className="font-[600]">{a.actor === "human" ? "Om" : "Agent"}</span>, {fmtMoment(a.ts)}:{" "}
          {auditActionRo(a.action)}
          {a.rule_id ? <span className="dense text-muted-foreground"> ({a.rule_id})</span> : null}
          {a.note ? <span className="block text-muted-foreground">„{a.note}”</span> : null}
        </li>
      ))}
    </ol>
  );
}
