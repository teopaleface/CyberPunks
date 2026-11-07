import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { ReviewActions } from "@/components/detail/review-actions";
import { ScoreScale } from "@/components/plan/score-scale";
import { AppShell } from "@/components/shell/app-shell";
import type { AuditRecord, Decision, WorkItem } from "@/lib/contracts";
import { getAudit } from "@/lib/data";
import { factorLabelRo, CONFIDENCE_RO, DECISION_LABEL_RO, SOURCE_LABEL_RO, predictionLabelRo, ruleRo } from "@/lib/data/labels";
import { fmtLei, fmtMoment, fmtScore, plural, sentence } from "@/lib/format";
import { markerSvg } from "@/lib/marker-svg";
import { itemPlace, itemTitle } from "@/lib/plan-screen";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { SOURCES, sourceOf } from "@/lib/sources";

export default function QueuePage({ searchParams }: PageProps<"/coada">) {
  return (
    <Suspense fallback={<div className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Se încarcă lucrările care așteaptă un om" />}>
      <Queue searchParams={searchParams} />
    </Suspense>
  );
}

/** Ce a decis omul (AuditRecord.action pentru actor „human”). */
const HUMAN_ACTION_RO: Record<string, string> = {
  review_approve: "Aprobată",
  review_reject: "Respinsă",
  review_defer: "Amânată",
};

/** Nota din jurnal are forma „cine: ce a scris” (sau doar „cine”), așa cum o scrie API-ul. */
function splitNote(note: string | null | undefined): { who: string | null; text: string | null } {
  const n = note?.trim();
  if (!n) return { who: null, text: null };
  const m = /^([^:\n]{1,100}):\s([\s\S]*)$/.exec(n);
  if (m) return { who: m[1].trim(), text: m[2].trim() || null };
  return n.includes(" ") ? { who: null, text: n } : { who: n, text: null };
}

function linkTo(id: string, scenario: string) {
  return `/lucrari/${encodeURIComponent(id)}?scenariu=${encodeURIComponent(scenario)}`;
}

interface Waiting {
  decision: Decision;
  w: WorkItem | null;
}

async function Queue({ searchParams }: { searchParams: PageProps<"/coada">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const { info, view } = await loadShellInfo(scenario);
  const plan = view.data;
  const auditResult = plan ? null : await getAudit(scenario);
  const audit: AuditRecord[] = plan ? plan.audit : (auditResult?.data ?? []);

  const waiting: Waiting[] = (plan?.plan.decisions ?? [])
    .filter((d) => d.decision === "human_review")
    .map((decision) => ({ decision, w: plan?.workItemsById[decision.work_item_id] ?? null }))
    .sort(
      (a, b) =>
        Number(Boolean(b.w?.impact.safety_flag)) - Number(Boolean(a.w?.impact.safety_flag)) ||
        (b.w?.impact.expected_value_lei ?? 0) - (a.w?.impact.expected_value_lei ?? 0),
    );
  const decided = audit.filter((a) => a.actor === "human").toSorted((a, b) => b.ts.localeCompare(a.ts));

  return (
    <AppShell info={info}>
      <div className="mx-auto max-w-[1760px] px-7 pt-7 pb-16">
        <div className="flex items-center gap-3">
          <h1 className="text-[30px] leading-tight font-[650]">Nu sunt sigur</h1>
          {waiting.length ? (
            <span className="inline-grid h-8 min-w-8 place-items-center rounded-full bg-att px-2.5 text-[17px] font-[700] text-white tabular-nums">
              {waiting.length}
              <span className="sr-only"> {waiting.length === 1 ? "lucrare așteaptă" : "lucrări așteaptă"} un om</span>
            </span>
          ) : null}
        </div>
        <p className="mt-2 max-w-[96ch] text-[16.5px] leading-relaxed">
          Aici trimite agentul ce nu poate decide singur: modelul s-a abținut, intervalul de încredere trece de pragul regulii, datele de intrare
          au probleme, sau e un risc pentru oameni și nu e nicio echipă liberă. Decide un om. Decizia intră în jurnal cu actorul „om”, iar planul
          se recalculează.
        </p>

        {waiting.length > 1 ? <Summary waiting={waiting} /> : null}

        {!plan ? (
          <div className="mt-8 border-y border-rule bg-panel px-5 py-6">
            <p className="text-[18px] font-[620]">Nu există încă un plan pentru „{scenario}”.</p>
            <p className="mt-1.5 text-[15.5px] text-muted-foreground">
              {view.degradedReason ?? "Agentul n-a rulat încă pentru acest scenariu."} Apasă „Rulează agentul” din antet ca să-l calculeze acum.
            </p>
          </div>
        ) : waiting.length ? (
          <section aria-labelledby="wait-title" className="mt-7">
            <h2 id="wait-title" className="sr-only">
              Lucrări care așteaptă un om
            </h2>
            <ul className="border-y border-rule">
              {waiting.map((x) => (
                <WaitingRow key={x.decision.work_item_id} item={x} scenario={scenario} />
              ))}
            </ul>
          </section>
        ) : (
          <div className="mt-8 border-y border-rule bg-panel px-5 py-7">
            <p className="text-[20px] font-[620]">Agentul a decis singur tot ce a primit. Nimic nu așteaptă un om acum.</p>
            <Link
              href={`/?scenariu=${encodeURIComponent(scenario)}`}
              className="mt-3 inline-block text-[16px] font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink"
            >
              Înapoi la planul de mâine
            </Link>
          </div>
        )}

        <section aria-labelledby="done-title" className="mt-12">
          <div className="flex flex-wrap items-baseline justify-between gap-x-4">
            <h2 id="done-title" className="text-[22px] font-[650]">
              Decise de oameni
            </h2>
            {decided.length ? <span className="text-[14.5px] text-muted-foreground">{plural(decided.length, "decizie", "decizii")}, cele mai noi primele</span> : null}
          </div>
          {decided.length ? (
            <ol className="mt-3 border-y border-rule">
              {decided.map((a) => (
                <DecidedRow key={a.audit_id} a={a} scenario={scenario} />
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-[15.5px] text-muted-foreground">
              Niciun om n-a decis încă în planul curent. Când aprobi, respingi sau amâni o lucrare, decizia apare aici, cu ora și nota ta.
            </p>
          )}
        </section>

        <p className="mt-10 text-[13.5px] text-muted-foreground">
          Datele vin din: {SOURCE_LABEL_RO[view.source]}
          {view.degradedReason ? `. ${view.degradedReason}` : ""}
          {auditResult?.degradedReason ? `. Jurnal: ${auditResult.degradedReason}` : ""}.
        </p>
      </div>
    </AppShell>
  );
}

/** Pe scurt, pentru proiector: câte lucrări din fiecare sursă și din ce motive. */
function Summary({ waiting }: { waiting: Waiting[] }) {
  const bySource = new Map<string, number>();
  const byRule = new Map<string, number>();
  for (const { decision, w } of waiting) {
    const s = w?.source ?? sourceOf(decision.work_item_id);
    if (s) bySource.set(s, (bySource.get(s) ?? 0) + 1);
    byRule.set(decision.rule_id, (byRule.get(decision.rule_id) ?? 0) + 1);
  }
  const sources = (["A", "B", "C"] as const).filter((s) => bySource.get(s));
  const rules = [...byRule.entries()].sort((a, b) => b[1] - a[1]);
  return (
    <div className="mt-5 flex flex-wrap items-center gap-x-8 gap-y-2 text-[15px]">
      <span className="flex flex-wrap items-center gap-x-4 gap-y-1">
        {sources.map((s) => (
          <span key={s} className="flex items-center gap-1.5">
            <span className="size-6 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source: s }, 24) }} />
            {SOURCES[s].name} <b className="font-[650] tabular-nums">{bySource.get(s)}</b>
          </span>
        ))}
      </span>
      <span className="h-5 w-px bg-rule" aria-hidden="true" />
      <span className="text-muted-foreground">
        {rules.map(([rule, n], i) => (
          <span key={rule}>
            {i ? "; " : "Motive: "}
            {ruleRo(rule) ?? rule} <b className="font-[650] text-ink tabular-nums">{n}</b>
          </span>
        ))}
      </span>
    </div>
  );
}

function WaitingRow({ item: { decision, w }, scenario }: { item: Waiting; scenario: string }) {
  const id = decision.work_item_id;
  const source = w?.source ?? sourceOf(id);
  const p = w?.prediction;
  const scoreMin = typeof decision.threshold?.score_min === "number" ? decision.threshold.score_min : null;
  const reason = p?.abstain_reason ? sentence(p.abstain_reason) : sentence(decision.reason_ro);
  const factors = w?.explanation.top_factors.slice(0, 2) ?? [];
  const maxF = Math.max(0.0001, ...factors.map((f) => Math.abs(f.contribution)));
  const rule = ruleRo(decision.rule_id);

  return (
    <li className="grid grid-cols-1 gap-x-10 gap-y-5 border-t border-rule py-6 first:border-t-0 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)_minmax(400px,0.95fr)]">
      {/* ce e și de ce a ajuns aici */}
      <div className="min-w-0">
        <div className="flex items-center gap-3">
          {source ? (
            <span className="size-9 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source, kind: "human" }) }} />
          ) : null}
          <div className="min-w-0">
            <Link href={linkTo(id, scenario)} className="code-id block truncate text-[19px] underline decoration-rule underline-offset-4 hover:decoration-ink">
              {id}
            </Link>
            {w ? (
              <p className="truncate text-[15px] text-muted-foreground">
                {itemTitle(w)}, {itemPlace(w)}: {predictionLabelRo(w.prediction.label)}
              </p>
            ) : (
              <p className="text-[15px] text-muted-foreground">Lucrarea nu e în lista primită; decizia se poate lua oricum.</p>
            )}
          </div>
        </div>
        <p className="mt-3 text-[17.5px] leading-snug font-[580]">{reason}</p>
        <p className="mt-1.5 text-[14.5px] text-muted-foreground">
          <span className="code-id text-ink">{decision.rule_id}</span>
          {rule ? `: ${rule}` : ""}
        </p>
        {w?.impact.safety_flag ? (
          <p className="mt-2 flex items-center gap-2 text-[15px] font-[600]">
            <svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true">
              <path d="M8 1 L15 3.5 V8.5 C15 12.8 12 15.8 8 17 C4 15.8 1 12.8 1 8.5 V3.5 Z" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth="1.6" />
              <path d="M8.8 4.5 L5.5 9.6 H8 L7.2 13.5 L10.5 8.4 H8 Z" style={{ fill: "var(--ink)" }} />
            </svg>
            Risc pentru oameni
          </p>
        ) : null}
      </div>

      {/* scorul, factorii, valoarea */}
      <div className="min-w-0">
        {p ? (
          <>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5">
              <span className="num-wide text-[40px] leading-none">{fmtScore(p.score)}</span>
              <ScoreScale score={p.score} low={p.interval_low} high={p.interval_high} threshold={scoreMin} width={190} tone="att" />
              <span className="text-[14.5px] leading-snug text-muted-foreground">
                {p.interval_low != null && p.interval_high != null ? `interval ${fmtScore(p.interval_low)}–${fmtScore(p.interval_high)}` : "fără interval"}
                <br />
                {CONFIDENCE_RO[p.confidence]}
                {scoreMin != null ? `, pragul regulii ${fmtScore(scoreMin)}` : ""}
              </span>
            </div>
            {factors.length ? (
              <div className="mt-4 space-y-2">
                {factors.map((f) => (
                  <div key={f.feature} className="grid grid-cols-[minmax(0,1fr)_120px_52px] items-center gap-x-3 text-[15px]">
                    <span className="min-w-0">{factorLabelRo(f.label_ro)}</span>
                    <span className="relative h-2.5 bg-muted" aria-hidden="true">
                      <i
                        className="absolute inset-y-0 left-0"
                        style={{ width: `${((Math.abs(f.contribution) / maxF) * 100).toFixed(1)}%`, background: f.contribution >= 0 ? "var(--ink)" : "var(--idle)" }}
                      />
                    </span>
                    <span className="text-right font-[620] tabular-nums">
                      {f.contribution >= 0 ? "+" : "−"}
                      {fmtScore(Math.abs(f.contribution))}
                    </span>
                  </div>
                ))}
              </div>
            ) : null}
            <Value w={w} abstained={Boolean(p.abstain)} />
          </>
        ) : (
          <p className="text-[15px] text-muted-foreground">Fără predicție pentru această lucrare.</p>
        )}
      </div>

      {/* decizia omului */}
      <div className="min-w-0 border-l-[3px] border-att bg-att-surface px-5 py-4">
        <p className="mb-2 text-[16px] font-[650] text-att-ink">Decide tu</p>
        <ReviewActions workItemId={id} scenario={scenario} />
      </div>
    </li>
  );
}

/** Valoarea în joc. Când modelul se abține, valoarea așteptată e 0: arătăm cât valorează dacă problema e reală. */
function Value({ w, abstained }: { w: WorkItem | null; abstained: boolean }) {
  if (!w) return null;
  const ev = w.impact.expected_value_lei;
  const ifTrue = w.impact.value_if_true_lei;
  const lei = (n: number) => (n === 0 ? "0 lei" : fmtLei(n));
  if (ev > 0 || !abstained) {
    return (
      <p className="mt-4 text-[15.5px]">
        Valoare așteptată <b className="font-[650] tabular-nums">{lei(ev)}</b>
        {ifTrue > 0 ? <span className="text-muted-foreground">; {lei(ifTrue)} dacă problema e reală</span> : null}
      </p>
    );
  }
  return (
    <p className="mt-4 text-[15.5px]">
      {ifTrue > 0 ? (
        <>
          În joc <b className="font-[650] tabular-nums">{lei(ifTrue)}</b>
          <span className="text-muted-foreground"> dacă problema e reală. Agentul nu calculează valoarea așteptată când modelul se abține.</span>
        </>
      ) : (
        <span className="text-muted-foreground">Agentul nu calculează valoarea așteptată când modelul se abține.</span>
      )}
    </p>
  );
}

function DecidedRow({ a, scenario }: { a: AuditRecord; scenario: string }) {
  const { who, text } = splitNote(a.note);
  const label = HUMAN_ACTION_RO[a.action] ?? sentence((DECISION_LABEL_RO as Record<string, string>)[a.action] ?? a.action.replaceAll("_", " ")).replace(/\.$/, "");
  const source = a.work_item_id ? sourceOf(a.work_item_id) : null;
  return (
    <li className="grid grid-cols-[220px_150px_minmax(0,1fr)] items-baseline gap-x-6 border-t border-rule py-3 text-[15.5px] first:border-t-0">
      <span className="text-muted-foreground tabular-nums">{fmtMoment(a.ts)}</span>
      <span className="font-[650]">
        {label}
        {who ? <span className="block text-[14px] font-[450] text-muted-foreground">de {who}</span> : null}
      </span>
      <span className="min-w-0">
        {a.work_item_id ? (
          <span className="flex items-center gap-2">
            {source ? <span className="size-6 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source }, 24) }} /> : null}
            <Link href={linkTo(a.work_item_id, scenario)} className="code-id truncate underline decoration-rule underline-offset-4 hover:decoration-ink">
              {a.work_item_id}
            </Link>
            {a.rule_id ? <span className="dense text-[13.5px] text-muted-foreground">venită din {a.rule_id}</span> : null}
          </span>
        ) : null}
        {text ? <span className="mt-0.5 block text-muted-foreground">„{text}”</span> : null}
      </span>
    </li>
  );
}
