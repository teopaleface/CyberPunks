import Link from "next/link";
import { Activity, CalendarDays, ChartColumn, Clock, ClipboardList, Cpu, MapPin, TrendingUp, Wrench } from "lucide-react";
import { ReviewActions } from "@/components/detail/review-actions";
import { Card, Pill, btn } from "@/components/ds";
import { ruleRo } from "@/lib/data/labels";
import { factorLabelRo } from "@/lib/data/labels";
import { fmtDec, fmtKm, fmtLei, fmtScore, fmtTime, sentence } from "@/lib/format";
import { isBilantPost } from "@/lib/extras";
import { intervalText, ruleCost, seriesSentence } from "@/lib/item-data";
import { isBilantSeries } from "@/lib/series-utils";
import { MiniChart } from "./mini-chart";
import { DataCard, DecisionPill, Headline, ModelCard, ScoresCard, SimilarCard, SPAN, TrailCard, type CardDef, type ItemCtx } from "./parts";


/** Pictograma unui factor, după numele lui. */
function factorIcon(feature: string) {
  if (/zero|gap|missing|lips|negative|count|days/.test(feature)) return CalendarDays;
  if (/peak|ratio|max|z_mean|excess|share/.test(feature)) return ChartColumn;
  if (/vcorr|neigh|corr/.test(feature)) return Activity;
  return TrendingUp;
}

function ConsumptionCard({ ctx }: { ctx: ItemCtx }) {
  const { w, series } = ctx;
  const bilant = isBilantPost(w);
  const s = seriesSentence(series);
  const p = w.prediction;
  const interval = intervalText(p.interval_low, p.interval_high);
  const headline = bilant
    ? p.point_estimate != null
      ? `Lipsesc ${fmtDec(p.point_estimate, 0)} kWh pe zi peste normal.`
      : "Bilanțul postului arată pierderi peste normal."
    : s.headline;
  const detail = bilant
    ? (series?.points.length ? `Bilanț pe ${series.points.length} zile, ieșit din post față de suma clienților.` : null)
    : [interval ? `Scor de defect ${fmtScore(p.score) === "1,00" ? "peste 0,99" : fmtScore(p.score)}, interval ${interval}` : null, s.detail].filter(Boolean).join(". ") || null;
  const bil = series ? isBilantSeries(series) : false;
  return (
    <Card title={bilant ? "Bilanț" : "Consum"} icon={TrendingUp} iconTone="blue" className="w-full">
      <Headline>{headline}</Headline>
      {detail ? <p className="mt-1.5 text-[15px] text-ink-soft">{detail}</p> : null}
      <div className="mt-3">
        {series ? (
          <MiniChart
            points={series.points}
            unit={series.unit}
            color="var(--src-a)"
            label={series.title_ro}
            height={bil ? 200 : 180}
          />
        ) : (
          <p className="py-8 text-center text-[15px] text-ink-soft">Seria pentru grafic nu e disponibilă.</p>
        )}
      </div>
      {series ? <p className="mt-1 text-[13px] text-ink-soft">{series.synthetic ? "Date sintetice. " : ""}Linia continuă e valoarea, cea întreruptă e ce ar fi fost normal{bil ? " (suma clienților)" : ""}.</p> : null}
    </Card>
  );
}

function ShapCard({ ctx }: { ctx: ItemCtx }) {
  const top = ctx.w.explanation.top_factors
    .filter((f) => Math.abs(f.contribution) > 0)
    .toSorted((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 3);
  return (
    <Card title="SHAP" icon={Cpu} iconTone="violet" className="w-full">
      <Headline>Ce a cântărit cel mai mult.</Headline>
      <ul className="mt-3 divide-y divide-rule border-t border-rule">
        {top.map((f) => {
          const Icon = factorIcon(f.feature);
          return (
            <li key={f.feature} className="flex items-start gap-3 py-3">
              <Icon aria-hidden="true" size={22} strokeWidth={1.6} className="mt-0.5 shrink-0 text-violet" />
              <span className="min-w-0 flex-1 text-[16px] leading-snug">{factorLabelRo(f.label_ro)}</span>
              <span className="shrink-0 text-[14.5px] font-[600] text-ink-soft tabular-nums" title="contribuția la scor (SHAP, log-odds)">
                {f.contribution >= 0 ? "+" : "−"}
                {fmtDec(Math.abs(f.contribution), 2)}
              </span>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}

function RuleCard({ ctx }: { ctx: ItemCtx }) {
  const { w, decision, stop, scenario } = ctx;
  if (!decision) {
    return (
      <Card title="Regula" icon={Wrench} iconTone="blue" className="w-full">
        <p className="text-[16px] text-ink-soft">Lucrarea nu are încă o decizie în planul curent.</p>
      </Card>
    );
  }
  const cost = ruleCost(decision.threshold);
  const ev = decision.threshold?.expected_value_lei ?? w.impact.expected_value_lei;
  return (
    <Card title={<span translate="no">{decision.rule_id}</span>} icon={Wrench} iconTone="blue" className="w-full">
      {cost != null ? (
        <Headline>
          {fmtLei(ev)} {ev > cost ? ">" : "<"} {fmtLei(cost)}
        </Headline>
      ) : (
        <Headline>{fmtLei(ev)}</Headline>
      )}
      <p className="mt-1.5 text-[15px] text-ink-soft">
        {cost != null ? "Valoarea așteptată față de costul acțiunii. " : "Valoarea așteptată. "}
        {ruleRo(decision.rule_id) ? sentence(ruleRo(decision.rule_id) as string) : ""}
      </p>
      {stop ? <p className="mt-1 text-[15px]">Deplasare: {fmtKm(stop.travel_km)}.</p> : null}
      <div className="mt-4 flex flex-wrap gap-3">
        {decision.decision === "human_review" ? (
          <div className="w-full">
            <ReviewActions workItemId={w.work_item_id} scenario={scenario} />
          </div>
        ) : (
          <Link href={`/harta?lucrare=${encodeURIComponent(w.work_item_id)}&scenariu=${encodeURIComponent(scenario)}`} className={btn("outline")}>
            <MapPin aria-hidden="true" size={18} />
            Vezi pe hartă
          </Link>
        )}
      </div>
    </Card>
  );
}

function TeamCard({ ctx }: { ctx: ItemCtx }) {
  const { decision, stop } = ctx;
  const auditId = decision?.audit_id;
  return (
    <Card title={stop?.crew_id ? <span translate="no">{stop.crew_id}</span> : "Echipa"} icon={MapPin} iconTone="blue" className="w-full">
      {stop ? (
        <>
          <Headline>Oprirea {stop.seq}</Headline>
          <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-[15px]">
            <span className="flex items-center gap-2"><Clock aria-hidden="true" size={20} className="text-ink-soft" />Sosire: <b className="font-[650] tabular-nums">{fmtTime(stop.eta)}</b></span>
            {auditId ? <span className="flex items-center gap-2"><ClipboardList aria-hidden="true" size={20} className="text-ink-soft" />Audit: <b translate="no" className="font-[650]" title={auditId}>{auditId.slice(0, 8)}…</b></span> : null}
          </div>
          <div className="mt-4"><Pill tone="green" size="lg" className="w-full justify-center">În traseu</Pill></div>
        </>
      ) : (
        <>
          <Headline>Fără echipă în traseu</Headline>
          <p className="mt-2 line-clamp-4 text-[15px] text-ink-soft">{decision ? sentence(decision.reason_ro) : "Lucrarea nu e în niciun traseu."}</p>
          {auditId ? <p className="mt-3 flex items-center gap-2 text-[15px]"><ClipboardList aria-hidden="true" size={20} className="text-ink-soft" />Audit: <b translate="no" className="font-[650]" title={auditId}>{auditId.slice(0, 8)}…</b></p> : null}
          <div className="mt-3"><DecisionPill decision={decision} size="lg" /></div>
        </>
      )}
    </Card>
  );
}

/** Lucrare A: contor sau post (bilanț). */
export function layoutA(ctx: ItemCtx): CardDef[] {
  const bilant = isBilantPost(ctx.w);
  const cards: CardDef[] = [
    { key: "consum", tags: ["predictii"], span: SPAN.c5, node: <ConsumptionCard ctx={ctx} /> },
    { key: "model", tags: ["predictii"], span: SPAN.c3, node: <ModelCard ctx={ctx} /> },
    { key: "shap", tags: ["predictii"], span: SPAN.c4, node: <ShapCard ctx={ctx} /> },
    { key: "regula", tags: ["reguli", "recomandari"], span: SPAN.c4, node: <RuleCard ctx={ctx} /> },
    { key: "echipa", tags: ["rute", "harti"], span: SPAN.c4, node: <TeamCard ctx={ctx} /> },
    { key: "similare", tags: ["predictii"], span: SPAN.c4, node: <SimilarCard w={ctx.w} className="w-full" /> },
    { key: "date", tags: ["predictii"], span: SPAN.c4, node: <DataCard w={ctx.w} className="w-full" /> },
  ];
  if (!bilant) cards.push({ key: "scoruri", tags: ["scoruri"], span: SPAN.c4, node: <ScoresCard source="A" report={ctx.report} className="w-full" /> });
  cards.push({ key: "urme", tags: ["urme", "reguli"], span: SPAN.c4, node: <TrailCard ctx={ctx} className="w-full" /> });
  return cards;
}

