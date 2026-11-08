import { englishText } from "@/lib/english";
import Link from "next/link";
import { Check, ClipboardCheck, Layers, Map as MapIcon, Sparkles, TriangleAlert, Zap, Cpu, SlidersHorizontal, FileText } from "lucide-react";
import { ReviewActions } from "@/components/detail/review-actions";
import { Card, Pill, btn } from "@/components/ds";
import { fmtDec, fmtLei } from "@/lib/format";
import { confidenceWord } from "@/lib/human";
import { ladderBaseP90, ladderChoice, remedyOptions } from "@/lib/extras";
import { CONTRIBUTION_RO, customerMessage, localityOf, pctText, puToVolts, voltageContributions } from "@/lib/item-data";
import { stepRo, verdictRo } from "@/lib/verdict";
import { MiniChart } from "./mini-chart";
import { DecisionPill, Headline, ScoresCard, SPAN, Stat, TrailCard, type CardDef, type ItemCtx } from "./parts";

const pu3 = (v: number) => `${fmtDec(v, 3)} pu`;

function derive(ctx: ItemCtx) {
  const { w, decision, remedy } = ctx;
  const chosen = ladderChoice(w, remedy);
  const options = remedyOptions(w);
  const before = ladderBaseP90(w, remedy);
  const after = remedy?.p90_after_pu ?? decision?.threshold?.p90_after_pu ?? null;
  const cost = remedy?.cost_lei ?? decision?.threshold?.remedy_cost_lei ?? null;
  const limitPu = ctx.series?.thresholds?.limita_tensiune_pu ?? decision?.threshold?.overvoltage_limit_pu ?? 1.1;
  return { chosen, options, before, after, cost, limitPu };
}

function StateCard({ ctx }: { ctx: ItemCtx }) {
  const { w, decision, scenario } = ctx;
  const p = w.prediction;
  return (
    <Card title="Substation status" icon={ClipboardCheck} iconTone="blue" className="w-full">
      <Headline className="text-[24px]"><span translate="no">{w.asset_id}</span> {localityOf(w)}</Headline>
      <p className="mt-1 text-[15.5px] text-ink-soft">Risk of exceeding the voltage limit.</p>
      <div className="mt-4 grid grid-cols-2 gap-4">
        <div>
          <Stat label="Model">{pctText(p.score)}</Stat>
          <Pill size="sm" tone="grey" className="mt-1.5">{confidenceWord(p.confidence, p.score)}</Pill>
        </div>
        <Stat label="Expected value">{fmtLei(w.impact.expected_value_lei)}</Stat>
      </div>
      <div className="mt-4"><DecisionPill decision={decision} /></div>
      <div className="mt-4 flex flex-wrap gap-3">
        {decision?.decision === "human_review" ? (
          <div className="w-full"><ReviewActions workItemId={w.work_item_id} scenario={scenario} /></div>
        ) : (
          <>
            {decision?.decision === "assigned" && decision.crew_id ? (
              <Link href={`/ordine/${encodeURIComponent(decision.crew_id)}?scenariu=${encodeURIComponent(scenario)}`} className={btn("primary")}>
                <FileText aria-hidden="true" size={18} />  Work order
              </Link>
            ) : null}
            <Link href={`/harta?lucrare=${encodeURIComponent(w.work_item_id)}&scenariu=${encodeURIComponent(scenario)}`} className={btn("outline")}>
              <MapIcon aria-hidden="true" size={18} />  View on map
            </Link>
          </>
        )}
      </div>
    </Card>
  );
}

function VoltageCard({ ctx }: { ctx: ItemCtx }) {
  const { series } = ctx;
  const { chosen, before, after, limitPu } = derive(ctx);
  const volts = (v?: number | null) => (typeof v === "number" ? Math.round(v * 230 * 10) / 10 : null);
  const points = (series?.points ?? []).map((p) => ({ t: String(p.t), value: volts(p.value), expected: volts(p.expected), low: volts(p.low), high: volts(p.high) }));
  const limitV = puToVolts(limitPu);
  return (
    <Card title="P10–P90 voltage" icon={Zap} iconTone="blue" action={<Pill tone="amber">Limit: {limitV} V</Pill>} className="w-full">
      <p className="text-[16px] font-[600]">
        {before != null ? (
          <>
            P90: {pu3(before)} ({puToVolts(before)} V){after != null && chosen.length ? <> → {pu3(after)} ({puToVolts(after)} V)</> : null}
          </>
        ) : (
          "P90 unavailable"
        )}
      </p>
      <div className="mt-2">
        {points.length ? (
          <MiniChart points={points} unit="V" color="var(--violet)" hours limit={limitV} limitLabel={`Limit ${limitV} V`} height={210} label={englishText(series?.title_ro ?? "Hourly voltage")} />
        ) : (
          <p className="py-10 text-center text-[15px] text-ink-soft">Voltage data is unavailable.</p>
        )}
      </div>
      <p className="mt-1 text-[13px] text-ink-soft">The line is P50; the band is P10–P90. 1 pu = 230 V.{series?.synthetic ? " Synthetic data." : ""}</p>
    </Card>
  );
}

function LadderCard({ ctx }: { ctx: ItemCtx }) {
  const { chosen, options, cost } = derive(ctx);
  const rows = chosen.map((a) => ({ a, o: options.find((x) => x.action === a) }));
  return (
    <Card title="Remedies considered" icon={Layers} iconTone="blue" className="w-full">
      {rows.length ? (
        <>
          <ul className="space-y-2.5">
            {rows.map(({ a, o }) => (
              <li key={a} className="flex items-center gap-3 rounded-[10px] border border-rule bg-surface-2 px-3.5 py-2.5">
                <span className="grid size-6 shrink-0 place-items-center rounded-[6px] bg-ok text-white"><Check aria-hidden="true" size={16} strokeWidth={3} /></span>
                <span className="min-w-0 flex-1 text-[15.5px] leading-snug font-[550]">
                  {stepRo(a).charAt(0).toLocaleUpperCase("ro-RO") + stepRo(a).slice(1)}
                  {a === "offer_battery" && ctx.remedy?.battery?.revenue_lei ? (
                    <span className="block text-[13px] font-[400] text-ink-soft">Estimated revenue: {fmtLei(ctx.remedy.battery.revenue_lei)}</span>
                  ) : null}
                </span>
                {o ? <Pill tone="grey" className="tabular-nums">{fmtLei(o.cost_lei)}</Pill> : null}
              </li>
            ))}
          </ul>
          <div className="mt-4 flex items-center justify-between border-t border-rule pt-3">
            <span className="text-[18px] font-[650]">Total</span>
            {cost != null ? <Pill tone="green" size="lg" className="text-[20px] font-[700] tabular-nums">{fmtLei(cost)}</Pill> : null}
          </div>
        </>
      ) : (
        <p className="py-8 text-center text-[16px] text-ink-soft">The agent has not chosen a remedy combination yet.</p>
      )}
    </Card>
  );
}

function ContributionsCard({ ctx }: { ctx: ItemCtx }) {
  const rows = voltageContributions(ctx.w);
  const shown = rows.slice(0, 5);
  const rest = rows.slice(5);
  const row = (r: { key: string; pu: number }) => (
    <tr key={r.key} className="border-t border-rule">
      <th scope="row" className="py-2 pr-2 text-left font-[450]">{CONTRIBUTION_RO[r.key] ?? r.key}</th>
      <td className="py-2 text-right tabular-nums">{r.pu >= 0 ? "+" : "−"}{fmtDec(Math.abs(r.pu), 4)}</td>
      <td className="py-2 pl-3 text-right tabular-nums">{r.pu >= 0 ? "+" : "−"}{fmtDec(Math.abs(r.pu) * 230, 1)}</td>
    </tr>
  );
  return (
    <Card title="Voltage contributions" icon={SlidersHorizontal} iconTone="violet" className="w-full">
      {rows.length ? (
        <>
          <table className="w-full text-[15px]">
            <thead>
              <tr className="text-[14px] text-ink-soft">
                <th scope="col" className="pb-2 text-left font-[500]">Factor</th>
                <th scope="col" className="pb-2 text-right font-[500]">[pu]</th>
                <th scope="col" className="pb-2 text-right font-[500]">[V]</th>
              </tr>
            </thead>
            <tbody>{shown.map(row)}</tbody>
          </table>
          {rest.length ? (
            <details className="mt-1 text-[14px] text-ink-soft">
              <summary className="cursor-pointer list-none py-1 underline decoration-rule underline-offset-4 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">Another {rest.length}  minor factors</summary>
              <table className="w-full text-[15px] text-ink"><tbody>{rest.map(row)}</tbody></table>
            </details>
          ) : null}
        </>
      ) : (
        <p className="py-6 text-center text-[16px] text-ink-soft">Contributions are unavailable.</p>
      )}
    </Card>
  );
}

function MessageCard({ ctx }: { ctx: ItemCtx }) {
  const msg = customerMessage(ctx.w, ctx.notifications);
  const note = ctx.notifications.find((n) => n.work_item_id === ctx.w.work_item_id && n.message_ro === msg);
  return (
    <Card
      title="Customer message draft"
      icon={TriangleAlert}
      iconTone="amber"
      className="w-full"
    >
      {msg ? (
        <>
          <Pill tone="grey" size="sm">Draft · Not sent</Pill><details className="mt-3 text-[14px]"><summary className="cursor-pointer py-2 font-medium">Read the proposed message</summary><p className="mt-2 whitespace-pre-wrap leading-relaxed text-ink-soft">{englishText(msg)}</p></details>
          <p className="mt-3 text-[14px] text-ink-soft">
            {note ? `To ${note.audience === "prosumatori" ? "solar customers" : note.audience === "echipa" ? "crew" : "customers in the area"}` : "Preview"}
            {note?.demo_only ? ", demo: nothing is sent externally" : ""}.
          </p>
        </>
      ) : (
        <p className="py-6 text-[16px] text-ink-soft">No customer messages for this work item.</p>
      )}
    </Card>
  );
}

function RecommendCard({ ctx }: { ctx: ItemCtx }) {
  const { chosen, before, after, cost, limitPu } = derive(ctx);
  const verdict = verdictRo(ctx.w, ctx.decision, { chosen, costLei: cost });
  const limitV = puToVolts(limitPu);
  const title = chosen.length
    ? `Apply ${chosen.map(stepRo).join(" + ")}${cost != null ? ` (total cost ${fmtLei(cost)})` : ""}.`
    : verdict.headline;
  const sub =
    chosen.length && before != null && after != null
      ? `Reduces peak voltage from ${puToVolts(before)} V to ${puToVolts(after)} V (P90), ${after <= limitPu ? "below" : "above"} limit of ${limitV} V.`
      : verdict.detail ?? null;
  return (
    <Card title="Recommendation" icon={Layers} iconTone="blue" className="w-full">
      <div className="flex flex-wrap items-center gap-4 rounded-[12px] border border-rule bg-surface-2 p-4">
        <div className="min-w-0 flex-1 basis-72">
          <Headline>{title}</Headline>
          {sub ? <p className="mt-1.5 text-[15.5px] text-ink-soft">{sub}</p> : null}
        </div>
        <Pill tone="green" size="lg" icon={Sparkles}>Agent recommendation</Pill>
      </div>
    </Card>
  );
}

function VoltageModelCard({ ctx }: { ctx: ItemCtx }) {
  const p = ctx.w.prediction;
  return (
    <Card title="Model" icon={Cpu} iconTone="blue" className="w-full">
      <Headline className="text-[20px]">Risk of exceeding the voltage limit</Headline>
      <p className="mt-0.5 text-[13.5px] text-ink-soft" translate="no">{p.model_version}</p>
      <div className="mt-3 grid grid-cols-2 gap-4 rounded-[12px] border border-rule bg-surface-2 p-3.5">
        <div>
          <p className="text-[14px] text-ink-soft">Score</p>
          <Pill tone="violet" size="lg" className="mt-1 text-[20px] font-[700]">{pctText(p.score)}</Pill>
        </div>
        <div>
          <p className="text-[14px] text-ink-soft">Expected value</p>
          <Pill tone="amber" size="lg" className="mt-1 text-[20px] font-[700] tabular-nums">{fmtLei(ctx.w.impact.expected_value_lei)}</Pill>
        </div>
      </div>
    </Card>
  );
}

/** Lucrare C: tensiune pe post. */
export function layoutC(ctx: ItemCtx): CardDef[] {
  return [
    { key: "stare", tags: ["predictii", "recomandari"], span: SPAN.c4, node: <StateCard ctx={ctx} /> },
    { key: "tensiune", tags: ["tensiune", "predictii"], span: SPAN.c4, node: <VoltageCard ctx={ctx} /> },
    { key: "scara", tags: ["recomandari", "tensiune"], span: SPAN.c4, node: <LadderCard ctx={ctx} /> },
    { key: "contributii", tags: ["tensiune", "predictii"], span: SPAN.c4, node: <ContributionsCard ctx={ctx} /> },
    { key: "alerte", tags: ["recomandari"], span: SPAN.c4, node: <MessageCard ctx={ctx} /> },
    { key: "scoruri", tags: ["scoruri"], span: SPAN.c4, node: <ScoresCard source="C" report={ctx.report} className="w-full" /> },
    { key: "recomandare", tags: ["recomandari"], span: SPAN.c8, node: <RecommendCard ctx={ctx} /> },
    { key: "model", tags: ["predictii"], span: SPAN.c4, node: <VoltageModelCard ctx={ctx} /> },
    { key: "urme", tags: ["urme", "reguli"], span: SPAN.c12, node: <TrailCard ctx={ctx} className="w-full" /> },
  ];
}

