import Link from "next/link";
import type { ReactNode } from "react";
import { BarChart3, ChevronRight, Database, ScrollText, Layers } from "lucide-react";
import { cn } from "cn";
import { Card, Dot, Gauge, KV, Pill, SOURCE_TONE, btn, type Tone } from "@/components/ds";
import type { AuditRecord, Decision, ModelReport, Notification, Series, Source, WorkItem } from "@/lib/contracts";
import type { RemedyChoice } from "@/lib/data/remedies";
import { DECISION_LABEL_RO, auditActionRo, clampPercentRo, outcomeRo, ruleRo } from "@/lib/data/labels";
import { fmtMoment, fmtPercent, fmtScore, sentence } from "@/lib/format";
import { TAG_CHIPS, intervalText, metricRows, pctText, type StopInfo, type Tag } from "@/lib/item-data";

/** Tot ce trebuie unei pagini de lucrare, adunat o dată. */
export interface ItemCtx {
  w: WorkItem;
  decision: Decision | null;
  audit: AuditRecord[];
  invalid: boolean;
  scenario: string;
  series: Series | null;
  report: ModelReport | null;
  remedy: RemedyChoice | null;
  stop: StopInfo | null;
  notifications: Notification[];
}

export interface CardDef {
  key: string;
  tags: Tag[];
  /** Clase de lățime pe grila de 12 coloane. */
  span: string;
  node: ReactNode;
}

export const SPAN = { c3: "lg:col-span-3", c4: "lg:col-span-4", c5: "lg:col-span-5", c6: "lg:col-span-6", c7: "lg:col-span-7", c8: "lg:col-span-8", c12: "lg:col-span-12" } as const;

/** Adresa lucrării, cu scenariul și filtrul. */
export function itemHref(id: string, scenario: string, tag?: Tag | null) {
  const q = new URLSearchParams({ scenariu: scenario });
  if (tag) q.set("vedere", tag);
  return `/lucrari/${encodeURIComponent(id)}?${q.toString()}`;
}

/** Filtrele din capul paginii: link-uri (adresa păstrează alegerea), doar cele care au carduri. */
export function ItemChips({ id, scenario, active, tags }: { id: string; scenario: string; active: Tag | null; tags: Set<Tag> }) {
  const base = "inline-flex h-9 items-center gap-2 rounded-full border px-4 text-[14.5px] font-[520] whitespace-nowrap transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring";
  const off = "border-rule text-ink hover:border-ink-soft hover:bg-surface-2";
  const on = "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]";
  return (
    <nav aria-label="Filtrează cardurile" className="flex flex-wrap gap-2.5">
      <Link href={itemHref(id, scenario)} scroll={false} replace aria-current={!active ? "true" : undefined} className={cn(base, !active ? on : off)}>
        Toate
      </Link>
      {TAG_CHIPS.filter((c) => tags.has(c.id)).map((c) => (
        <Link key={c.id} href={itemHref(id, scenario, c.id)} scroll={false} replace aria-current={active === c.id ? "true" : undefined} className={cn(base, active === c.id ? on : off)}>
          {active !== c.id ? <Dot tone={c.tone} /> : null}
          {c.label}
        </Link>
      ))}
    </nav>
  );
}

export function CardGrid({ cards }: { cards: CardDef[] }) {
  return (
    <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-12">
      {cards.map((c) => (
        <div key={c.key} className={cn("flex min-w-0 [&>*]:w-full", c.span)}>
          {c.node}
        </div>
      ))}
    </div>
  );
}

/** Tonul pastilei deciziei. */
export const DECISION_TONE: Record<Decision["decision"], Tone> = {
  assigned: "green",
  human_review: "orange",
  notify: "blue",
  remote_action: "violet",
  deferred: "grey",
  rejected_invalid: "red",
};

export function DecisionPill({ decision, size }: { decision: Decision | null; size?: "sm" | "md" | "lg" }) {
  if (!decision) return <Pill size={size}>Fără decizie în plan</Pill>;
  const text = decision.decision === "human_review" ? "Necesită decizia umană" : sentence(DECISION_LABEL_RO[decision.decision]).replace(/\.$/, "");
  return (
    <Pill tone={DECISION_TONE[decision.decision]} size={size}>
      {text}
    </Pill>
  );
}

/** Linie de titlu mare într-un card, ca în design. */
export function Headline({ children, className }: { children: ReactNode; className?: string }) {
  return <p className={cn("text-[22px] leading-tight font-[700] tracking-[-0.015em]", className)}>{children}</p>;
}

/** Rând de cifră cu etichetă mică deasupra (Model, Valoare așteptată). */
export function Stat({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <div className="min-w-0">
      <p className="text-[14px] text-ink-soft">{label}</p>
      <p className="mt-0.5 text-[24px] leading-tight font-[700] tracking-[-0.02em] tabular-nums">{children}</p>
    </div>
  );
}

/** Cardul „Model”: versiunea, indicatorul cu scorul și intervalul. */
export function ModelCard({ ctx, className }: { ctx: ItemCtx; className?: string }) {
  const p = ctx.w.prediction;
  const interval = intervalText(p.interval_low, p.interval_high);
  return (
    <Card title="Model" icon={Layers} iconTone={SOURCE_TONE[ctx.w.source]} className={className}>
      <Headline className="font-[650] break-all"><span translate="no">{p.model_version}</span></Headline>
      <div className="mt-2 flex justify-center">
        <Gauge value={p.score} tone={ctx.w.source === "C" ? "amber" : "violet"} label={<span className={pctText(p.score).length > 4 ? "text-[24px]" : ""}>{pctText(p.score)}</span>} sub={interval ? `interval ${interval}` : undefined} size={210} />
      </div>
    </Card>
  );
}

/** „Cazuri similare”: fiecare rând se deschide și arată nota cazului. */
export function SimilarCard({ w, className }: { w: WorkItem; className?: string }) {
  const cases = w.explanation.similar_cases ?? [];
  return (
    <Card title="Cazuri similare" icon={Layers} iconTone="violet" className={className}>
      {cases.length ? (
        <ul className="space-y-2">
          {cases.map((c) => (
            <li key={c.case_id}>
              <details className="group rounded-[10px] border border-rule bg-surface-2">
                <summary className="flex min-h-11 cursor-pointer list-none items-center gap-3 rounded-[10px] px-3.5 py-2 text-[15px] focus-visible:outline-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
                  <span translate="no" className="min-w-0 flex-1 truncate font-[560]" title={c.case_id}>{c.case_id}</span>
                  <span className="shrink-0 text-ink-soft tabular-nums">{fmtScore(c.similarity)}</span>
                  <ChevronRight aria-hidden="true" size={18} className="shrink-0 text-ink-soft transition-transform group-open:rotate-90" />
                </summary>
                <p className="border-t border-rule px-3.5 py-2.5 text-[14px] text-ink-soft">
                  <span className="font-[600] text-ink">{sentence(outcomeRo(c.outcome))}</span>
                  {c.note_ro ? ` ${clampPercentRo(c.note_ro)}` : ""}
                </p>
              </details>
            </li>
          ))}
        </ul>
      ) : (
        <p className="py-6 text-center text-[16px] text-ink-soft">Fără cazuri similare</p>
      )}
    </Card>
  );
}

/** „Detalii date”: lipsa, sursele, problemele de intrare, sintetic. */
export function DataCard({ w, className }: { w: WorkItem; className?: string }) {
  const q = w.data_quality;
  const pill = (t: ReactNode) => <span className="inline-block min-w-16 rounded-full bg-surface-2 px-3 py-1 text-center text-[14px] ring-1 ring-[#2a3a52]">{t}</span>;
  return (
    <Card title="Detalii date" icon={Database} iconTone="blue" className={className}>
      <KV k="Lipsă date" v={pill(fmtPercent(q.missing_ratio, 1))} />
      <KV k="Surse" v={pill(q.data_sources.length)} />
      <KV k="Probleme de intrare" v={pill(q.input_issues?.length ? q.input_issues.length : "niciuna")} />
      <KV k="Date sintetice" v={pill(q.synthetic ? "da" : "nu")} />
      <details className="group mt-2 text-[14px] text-ink-soft">
        <summary className="cursor-pointer list-none rounded-[6px] py-1 underline decoration-rule underline-offset-4 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring [&::-webkit-details-marker]:hidden">
          Arată sursele și problemele
        </summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          {q.data_sources.map((s) => <li key={s}>{s}</li>)}
          {q.input_issues?.map((s) => <li key={s} className="text-att-ink">{s}</li>)}
        </ul>
      </details>
    </Card>
  );
}

/** „Scoruri”: modelul față de baza lui, din rapoartele de evaluare. */
export function ScoresCard({ source, report, className }: { source: Source; report: ModelReport | null; className?: string }) {
  const rows = metricRows(source, report);
  const tone = SOURCE_TONE[source];
  return (
    <Card title="Scoruri" icon={BarChart3} iconTone="blue" className={className}>
      {rows.length ? (
        <>
          <table className="w-full text-[15px]">
            <thead>
              <tr className="text-[14px] text-ink-soft">
                <th scope="col" className="pb-2 text-left font-[500]">Metrica</th>
                <th scope="col" className="pb-2 text-center font-[500]">Acest model</th>
                <th scope="col" className="pb-2 text-center font-[500]">Bază</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key} className="border-t border-rule">
                  <th scope="row" className="py-2 pr-2 text-left font-[450]">{r.label}</th>
                  <td className="py-1.5 text-center"><Pill tone={tone} className="tabular-nums">{r.model}</Pill></td>
                  <td className="py-1.5 text-center">{r.base ? <Pill tone="grey" className="tabular-nums">{r.base}</Pill> : <span className="text-ink-soft">–</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {report?.baseline_id ? <p className="mt-2 text-[13px] text-ink-soft">Bază: {report.baseline_id}.</p> : null}
        </>
      ) : (
        <p className="py-6 text-center text-[16px] text-ink-soft">Raportul de evaluare nu e disponibil.</p>
      )}
    </Card>
  );
}

/** „Urme de decizie”: regula în cuvinte, motivul și înregistrările din jurnal. */
export function TrailCard({ ctx, className }: { ctx: ItemCtx; className?: string }) {
  const { decision, audit } = ctx;
  const recent = audit.toSorted((a, b) => b.ts.localeCompare(a.ts)).slice(0, 3);
  return (
    <Card title="Urme de decizie" icon={ScrollText} iconTone="amber" className={className}>
      {decision ? (
        <>
          <Headline className="text-[19px]">{sentence(ruleRo(decision.rule_id) ?? DECISION_LABEL_RO[decision.decision])}</Headline>
          <p className="mt-1 text-[14px] text-ink-soft" translate="no">{decision.rule_id}</p>
          <p className="mt-3 line-clamp-6 text-[15px] text-ink-soft">{sentence(clampPercentRo(decision.reason_ro))}</p>
        </>
      ) : (
        <p className="text-[16px] text-ink-soft">Lucrarea nu are încă o decizie în planul curent.</p>
      )}
      {recent.length ? (
        <ol className="mt-3 space-y-1.5 border-t border-rule pt-3 text-[14px]">
          {recent.map((a) => (
            <li key={a.audit_id}>
              <span className="font-[600]">{a.actor === "human" ? "Om" : "Agent"}</span>, {fmtMoment(a.ts)}: {auditActionRo(a.action)}
              {a.note && a.note !== decision?.reason_ro ? <span className="line-clamp-2 block text-ink-soft">„{a.note}”</span> : null}
            </li>
          ))}
        </ol>
      ) : null}
    </Card>
  );
}

export { btn };
