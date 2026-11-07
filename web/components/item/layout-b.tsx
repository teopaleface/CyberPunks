import { CalendarDays, ClipboardCheck, Clock, Cpu, Droplet, Layers, MapPin, Truck, UserRound, Users, Wind, Zap } from "lucide-react";
import { ReviewActions } from "@/components/detail/review-actions";
import { Card, Gauge, Pill } from "@/components/ds";
import { fmtDayMonth, fmtDec, fmtInt, fmtLei, fmtTime, plural } from "@/lib/format";
import { confidenceWord } from "@/lib/human";
import { localityOf, maxGust, pctText, windowHours } from "@/lib/item-data";
import { Headline, DecisionPill, ScoresCard, SPAN, TrailCard, type CardDef, type ItemCtx } from "./parts";
import { Sparkline } from "./sparkline";

const win = (ctx: ItemCtx) => {
  const t = ctx.w.time_window;
  return t ? { text: `${fmtTime(t.start)} – ${fmtTime(t.end)}`, hours: windowHours(t.start, t.end) } : null;
};

function PillRow({ icon: Icon, label, children }: { icon: typeof Zap; label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3.5 py-2.5">
      <Icon aria-hidden="true" size={20} strokeWidth={1.7} className="shrink-0 text-ink-soft" />
      <span className="min-w-0 flex-1 text-[15.5px]">{label}</span>
      {children}
    </div>
  );
}

function WorkCard({ ctx }: { ctx: ItemCtx }) {
  const { w, decision, scenario } = ctx;
  return (
    <Card title="Lucrare" icon={ClipboardCheck} iconTone="blue" className="w-full">
      <Headline className="text-[24px]">{localityOf(w)}: furtună.</Headline>
      <p className="mt-1 text-[15.5px] text-ink-soft">Lucrare (sintetică) generată de model.</p>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[14px] text-ink-soft"><Layers aria-hidden="true" size={16} />Model</p>
          <p className="mt-0.5 text-[18px] font-[700] break-all" translate="no">{w.prediction.model_version}</p>
        </div>
        <div>
          <p className="text-[14px] text-ink-soft">Valoare estimată</p>
          <p className="mt-0.5 text-[20px] font-[700] tabular-nums">{fmtLei(w.impact.expected_value_lei)}</p>
        </div>
      </div>
      <div className="mt-4"><DecisionPill decision={decision} /></div>
      {decision?.decision === "human_review" ? (
        <div className="mt-4"><ReviewActions workItemId={w.work_item_id} scenario={scenario} /></div>
      ) : null}
    </Card>
  );
}

function ConfidenceCard({ ctx }: { ctx: ItemCtx }) {
  const p = ctx.w.prediction;
  const review = ctx.decision?.decision === "human_review";
  return (
    <Card title="Încredere risc" icon={Layers} iconTone="violet" className="w-full">
      <div className="flex flex-col items-center">
        <Gauge value={p.score} label={<span className={pctText(p.score).length > 4 ? "text-[24px]" : ""}>{pctText(p.score)}</span>} sub={confidenceWord(p.confidence, p.score).replace("mică", "scăzută")} size={220} />
        <div className="mt-3">
          {review ? <Pill tone="orange" size="lg" icon={UserRound}>Necesită revizuire</Pill> : <DecisionPill decision={ctx.decision} size="lg" />}
        </div>
      </div>
    </Card>
  );
}

function AlgoCard({ ctx }: { ctx: ItemCtx }) {
  const { w } = ctx;
  return (
    <Card title="Model" icon={Zap} iconTone="blue" className="w-full">
      <div className="space-y-2.5">
        <PillRow icon={Cpu} label="Algoritm"><Pill tone="violet" className="break-all" ><span translate="no">{w.prediction.model_version}</span></Pill></PillRow>
        <PillRow icon={Zap} label="Risc"><Pill tone="blue" className="tabular-nums">{pctText(w.prediction.score)}</Pill></PillRow>
        <PillRow icon={Layers} label="Valoare estimată"><Pill tone="amber" className="tabular-nums">{fmtLei(w.impact.expected_value_lei)}</Pill></PillRow>
      </div>
    </Card>
  );
}

function WindowCard({ ctx }: { ctx: ItemCtx }) {
  const t = win(ctx);
  return (
    <Card title="Fereastră furtună" icon={CalendarDays} iconTone="blue" className="w-full">
      {t ? (
        <>
          <Headline className="text-[30px] tabular-nums">{t.text}</Headline>
          <p className="mt-4 flex items-center gap-2.5 text-[15px] text-ink-soft"><Clock aria-hidden="true" size={20} />Durată <Pill tone="grey">{plural(t.hours, "oră", "ore")}</Pill></p>
        </>
      ) : (
        <p className="py-6 text-[16px] text-ink-soft">Modelul nu a dat o fereastră pentru furtună.</p>
      )}
    </Card>
  );
}

function GustCard({ ctx }: { ctx: ItemCtx }) {
  const g = maxGust(ctx.series);
  const values = (ctx.series?.points ?? []).map((p) => p.value).filter((v): v is number => typeof v === "number");
  return (
    <Card title="Rafale (vânt)" icon={Wind} iconTone="blue" className="w-full">
      {g ? (
        <>
          <Headline className="text-[30px]">{fmtDec(g.value, 0)} km/h</Headline>
          <p className="mt-1 text-[14.5px] text-ink-soft">Rafala maximă din serie, {fmtDayMonth(g.t.slice(0, 10))}, {fmtTime(g.t)}.</p>
          <div className="mt-3"><Sparkline values={values} label="Rafalele de vânt, oră cu oră" /></div>
        </>
      ) : (
        <p className="py-6 text-[16px] text-ink-soft">Seria de rafale nu e disponibilă.</p>
      )}
    </Card>
  );
}

function RainCard({ ctx }: { ctx: ItemCtx }) {
  const { w } = ctx;
  const rain = w.explanation.top_factors.find((f) => f.feature === "precip_48h" && typeof f.value === "number");
  const p90 = w.prediction.point_interval?.[1];
  return rain ? (
    <Card title="Ploaie" icon={Droplet} iconTone="blue" className="w-full">
      <Headline className="text-[30px]">{fmtDec(rain.value as number, 0)} mm</Headline>
      <p className="mt-1 text-[14.5px] text-ink-soft">Cumul în ultimele 48 de ore.</p>
    </Card>
  ) : (
    <Card title="Clienți fără curent (P90)" icon={Droplet} iconTone="blue" className="w-full">
      <Headline className="text-[30px]">{p90 != null ? fmtInt(p90) : "–"}</Headline>
      <p className="mt-1 text-[14.5px] text-ink-soft">Scenariul pesimist, dacă se produce avaria.</p>
    </Card>
  );
}

function CustomersCard({ ctx }: { ctx: ItemCtx }) {
  const p = ctx.w.prediction;
  const n = p.point_estimate ?? ctx.w.impact.customers_affected;
  return (
    <Card title="Clienți" icon={Users} iconTone="blue" className="w-full">
      <Headline className="text-[30px]">{n != null ? `${fmtInt(n)} clienți` : "–"}</Headline>
      <p className="mt-1 text-[14.5px] text-ink-soft">Impact estimat (P50).</p>
      {p.point_interval ? <p className="mt-2 text-[14.5px] text-ink-soft">Interval P10–P90: {fmtInt(p.point_interval[0])}–{fmtInt(p.point_interval[1])}</p> : null}
    </Card>
  );
}

function CrewCard({ ctx }: { ctx: ItemCtx }) {
  const { w, decision, stop } = ctx;
  const t = win(ctx);
  const crew = stop?.crew_id ?? decision?.crew_id ?? null;
  const status =
    decision?.decision === "assigned" && stop ? <Pill tone="green" size="lg">Echipa ajunge la {fmtTime(stop.eta)}</Pill>
    : decision?.decision === "human_review" ? <Pill tone="orange" size="lg" icon={UserRound}>În așteptarea aprobării umane</Pill>
    : <DecisionPill decision={decision} size="lg" />;
  const cell = (Icon: typeof Zap, k: string, v: React.ReactNode) => (
    <div className="flex items-center gap-2.5">
      <Icon aria-hidden="true" size={22} className="shrink-0 text-ink-soft" />
      <div><p className="text-[13.5px] text-ink-soft">{k}</p><p className="text-[16px] font-[650]">{v}</p></div>
    </div>
  );
  return (
    <Card title="Prepoziționare echipă" icon={Truck} iconTone="blue" className="w-full">
      <Headline className="text-[26px]">{crew ? <span translate="no">{crew}</span> : "Echipă nealocată încă"}</Headline>
      <p className="mt-1 text-[15.5px] text-ink-soft">Propunere de prepoziționare înainte de fereastra furtunii.</p>
      <div className="mt-4 flex flex-wrap items-center gap-x-8 gap-y-4">
        {status}
        {cell(MapPin, "Locație", localityOf(w))}
        {crew ? cell(Users, "Echipă", <span translate="no">{crew}</span>) : null}
        {t ? cell(CalendarDays, "Fereastră", <span className="tabular-nums">{t.text}</span>) : null}
      </div>
    </Card>
  );
}

function ImpactCard({ ctx }: { ctx: ItemCtx }) {
  const { w, decision } = ctx;
  const p = w.prediction;
  const n = p.point_estimate ?? w.impact.customers_affected;
  const cost = decision?.threshold?.preposition_cost_lei;
  return (
    <Card title="Impact estimat" icon={Layers} iconTone="blue" className="w-full">
      <div className="space-y-2.5">
        <PillRow icon={Users} label="Clienți (P50)"><Pill tone="blue" className="tabular-nums">{n != null ? fmtInt(n) : "–"}</Pill></PillRow>
        <PillRow icon={Layers} label="Valoare estimată"><Pill tone="amber" className="tabular-nums">{fmtLei(w.impact.expected_value_lei)}</Pill></PillRow>
        {typeof cost === "number" ? <PillRow icon={Truck} label="Cost echipă trimisă"><Pill tone="grey" className="tabular-nums">{fmtLei(cost)}</Pill></PillRow> : null}
      </div>
    </Card>
  );
}

/** Lucrare B: furtună peste o zonă. */
export function layoutB(ctx: ItemCtx): CardDef[] {
  return [
    { key: "lucrare", tags: ["recomandari"], span: SPAN.c5, node: <WorkCard ctx={ctx} /> },
    { key: "incredere", tags: ["predictii"], span: SPAN.c3, node: <ConfidenceCard ctx={ctx} /> },
    { key: "model", tags: ["predictii"], span: SPAN.c4, node: <AlgoCard ctx={ctx} /> },
    { key: "fereastra", tags: ["predictii"], span: SPAN.c3, node: <WindowCard ctx={ctx} /> },
    { key: "rafale", tags: ["predictii"], span: SPAN.c3, node: <GustCard ctx={ctx} /> },
    { key: "ploaie", tags: ["predictii"], span: SPAN.c3, node: <RainCard ctx={ctx} /> },
    { key: "clienti", tags: ["predictii"], span: SPAN.c3, node: <CustomersCard ctx={ctx} /> },
    { key: "echipa", tags: ["rute", "harti"], span: SPAN.c7, node: <CrewCard ctx={ctx} /> },
    { key: "impact", tags: ["recomandari"], span: SPAN.c5, node: <ImpactCard ctx={ctx} /> },
    { key: "scoruri", tags: ["scoruri"], span: SPAN.c6, node: <ScoresCard source="B" report={ctx.report} className="w-full" /> },
    { key: "urme", tags: ["urme", "reguli"], span: SPAN.c6, node: <TrailCard ctx={ctx} className="w-full" /> },
  ];
}
