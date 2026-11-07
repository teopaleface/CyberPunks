"use client";

import { englishText } from "@/lib/english";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import type { Alert, Decision, WorkItem } from "@/lib/contracts";
import { requestAssistantAction } from "@/lib/operations/assistant-intent";
import { scoreText } from "@/lib/human";
import { alertOutcomeRo, clampPercentRo, factorLabelRo, ACTION_RO, CONFIDENCE_RO, DECISION_LABEL_RO, outcomeRo, predictionLabelRo, ruleRo } from "@/lib/data/labels";
import type { ReviewDecision } from "@/lib/data/types";
import { fmtDec, fmtInt, fmtLei, fmtScore, fmtTime, sentence } from "@/lib/format";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { isSlim, itemPlace, itemTitle } from "@/lib/plan-screen";
import { ScoreScale } from "./score-scale";

function Marker({ w, decision, selected = false }: { w: WorkItem; decision?: Decision | null; selected?: boolean }) {
  return (
    <span
      className="block size-9 shrink-0"
      dangerouslySetInnerHTML={{ __html: markerSvg({ source: w.source, kind: markerKind(decision?.decision), selected }) }}
    />
  );
}


// --------------------------------------------------------------------------------------------
// „Nu sunt sigur”: ce n-a putut decide agentul singur
// --------------------------------------------------------------------------------------------
export function QueuePanel({
  queue,
  itemsById,
  scenario,
  onSelect,
  recovered,
}: {
  queue: Decision[];
  itemsById: Record<string, WorkItem>;
  scenario: string;
  onSelect: (id: string) => void;
  recovered?: { count: number; lei: number };
}) {
  const first = queue[0];
  const w = first ? itemsById[first.work_item_id] : undefined;

  const act = (decision: ReviewDecision) => {
    if (!first) return;
    requestAssistantAction("review_work_item", {work_item_id:first.work_item_id,decision,note:""},scenario);
  };

  return (
    <section aria-labelledby="q-title" className="border-b border-rule px-7 py-3.5">
      <div className="flex items-center gap-2.5">
        <h2 id="q-title" className="text-[20px] font-[650] tracking-[-0.005em]">

          Needs review
        </h2>
        {queue.length ? (
          <span className="inline-grid h-6 min-w-6 place-items-center rounded-full bg-att px-1.5 text-[14px] font-[700] text-on-att">
            {queue.length}
          </span>
        ) : null}
        <span className="ml-auto truncate text-[14px] text-muted-foreground">
          {recovered && recovered.count > 0 ? (
            <>

              confirmed by a person: <b className="font-[620] text-ink tabular-nums">{recovered.count}</b>, about{" "}
              <b className="font-[620] text-ink tabular-nums">{fmtLei(recovered.lei)}</b>  recovered
            </>
          ) : first ? (
            `regula ${first.rule_id}`
          ) : null}
        </span>
      </div>
      {!first || !w ? (
        <p className="mt-2 text-[15px] text-muted-foreground">

          No cases are awaiting human review.
        </p>
      ) : (
        <div className="mt-2.5 grid grid-cols-[36px_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-2.5">
          <button type="button" onClick={() => onSelect(w.work_item_id)} aria-label={`Show ${w.work_item_id} on the map`} className="rounded-full">
            <Marker w={w} decision={first} />
          </button>
          <div className="min-w-0">
            <div className="code-id truncate text-[16px]" translate="no">{w.work_item_id}</div>
            <div className="truncate text-[14.5px] text-muted-foreground">
              {itemTitle(w)}, {itemPlace(w)}
            </div>
          </div>
          <div className="flex items-center gap-3">
            <ScoreScale score={w.prediction.score} low={w.prediction.interval_low} high={w.prediction.interval_high} threshold={0.5} width={110} tone="att" />
            <span className="num-wide text-[32px]">{scoreText(w.prediction.score)}</span>
          </div>
          <p className="col-span-2 col-start-2 text-[15.5px] font-[540] text-pretty">
            {w.prediction.abstain_reason ? sentence(w.prediction.abstain_reason) : sentence(first.reason_ro)}{" "}
            <span className="font-[400] whitespace-nowrap text-muted-foreground">Your decision is required.</span>
          </p>
          <div className="col-span-2 col-start-2 flex flex-wrap items-center gap-2.5">
            <Button size="panel" onClick={() => act("approve")}>
              Approve
            </Button>
            <Button size="panel" variant="outline" onClick={() => act("reject")}>
              Reject
            </Button>
            <Button size="panel" variant="outline" onClick={() => act("defer")}>
              Defer
            </Button>
            <span className="ml-auto text-[14px] text-muted-foreground tabular-nums [@media(max-height:950px)]:hidden">
              interval {fmtScore(w.prediction.interval_low ?? w.prediction.score)}–{fmtScore(w.prediction.interval_high ?? w.prediction.score)},{" "}
              {CONFIDENCE_RO[w.prediction.confidence]}
            </span>
          </div>
          {queue.length > 1 ? (
            <Link
              href={`/coada?scenariu=${encodeURIComponent(scenario)}`}
              className="col-span-2 col-start-2 text-[15px] font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink"
            >

              Another {queue.length - 1} {queue.length - 1 === 1 ? "work item awaits" : "work items await"}  human review
            </Link>
          ) : null}
        </div>
      )}
    </section>
  );
}

// --------------------------------------------------------------------------------------------
// Alerte
// --------------------------------------------------------------------------------------------
const SEVERITY_ORDER = { critical: 0, warning: 1, info: 2 } as const;
const SEVERITY_RO = { critical: "critical", warning: "warning", info: "information" } as const;

function SeverityIcon({ severity }: { severity: Alert["severity"] }) {
  if (severity === "info") {
    return (
      <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" className="shrink-0">
        <circle cx="10" cy="10" r="8.5" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth="1.6" />
        <rect x="9.1" y="8.5" width="1.8" height="6" style={{ fill: "var(--ink)" }} />
        <rect x="9.1" y="5.2" width="1.8" height="1.8" style={{ fill: "var(--ink)" }} />
      </svg>
    );
  }
  return (
    <svg width="22" height="20" viewBox="0 0 22 20" aria-hidden="true" className="shrink-0">
      <path d="M11 1.5 L21 18.5 H1 Z" style={{ fill: severity === "critical" ? "var(--destructive)" : "var(--att)" }} />
      <rect x="10" y="7" width="2" height="6" fill="#fff" />
      <rect x="10" y="14.5" width="2" height="2" fill="#fff" />
    </svg>
  );
}

export function AlertsPanel({
  alerts,
  decisions,
  onSelect,
}: {
  alerts: Alert[];
  decisions: Record<string, Decision>;
  onSelect: (id: string) => void;
}) {
  if (!alerts.length) return null;
  const sorted = alerts.toSorted((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  const shown = sorted.slice(0, 1);
  return (
    <section aria-label="Alerts" className="border-b border-rule px-7 py-3 [@media(max-height:950px)]:hidden">
      <ul className="space-y-3">
        {shown.map((a) => {
          const outcome = alertOutcomeRo(a.work_item_ids, decisions);
          return (
          <li key={a.alert_id}>
            <div className="flex items-center gap-2.5">
              <SeverityIcon severity={a.severity} />
              <h3 className="min-w-0 truncate text-[17px] font-[620]">{englishText(a.title_ro)}</h3>
              <span className="sr-only">, {SEVERITY_RO[a.severity]}</span>
              {a.work_item_ids?.[0] ? (
                <button
                  type="button"
                  onClick={() => onSelect(a.work_item_ids![0])}
                  className="code-id ml-auto text-[14px] text-muted-foreground underline decoration-rule underline-offset-4 hover:text-ink"
                >
                  {a.work_item_ids[0]}
                </button>
              ) : null}
            </div>
            {outcome ? (
              // numărătoarea din decizii stă în față: textul alertei poate promite mai mult decât face planul
              <p className="mt-0.5 line-clamp-1 pl-[32px] text-[15px]" title={englishText(a.body_ro)}>
                <span className="text-muted-foreground">Agent decisions: </span>
                {outcome}
              </p>
            ) : (
              <p className="mt-0.5 line-clamp-1 pl-[32px] text-[15px]" title={englishText(a.body_ro)}>
                {englishText(a.body_ro)}
              </p>
            )}
          </li>
          );
        })}
      </ul>
      {sorted.length > shown.length ? (
        <Link href="/alerte" className="mt-1.5 inline-block pl-[32px] text-[14.5px] font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink">
          {sorted.length - shown.length === 1 ? "One more alert" : `Another ${sorted.length - shown.length} alerte`}, under Alerts and messages
        </Link>
      ) : null}
    </section>
  );
}

// --------------------------------------------------------------------------------------------
// Detaliul lucrării selectate: scor, de ce, caz similar, regula, urmărirea până la predicție
// --------------------------------------------------------------------------------------------
function costOf(d: Decision | null | undefined): { cost: number; label: string } | null {
  const t = d?.threshold ?? {};
  if (typeof t.cost_lei === "number") return { cost: t.cost_lei, label: "cost" };
  if (typeof t.visit_cost_lei === "number") return { cost: t.visit_cost_lei, label: "visit cost" };
  if (typeof t.preposition_cost_lei === "number") return { cost: t.preposition_cost_lei, label: "crew prepositioning cost" };
  if (typeof t.tap_change_visit_cost_lei === "number") return { cost: t.tap_change_visit_cost_lei, label: "tap adjustment cost" };
  return null;
}

function pointEstimate(w: WorkItem): string | null {
  const p = w.prediction;
  if (p.point_estimate == null) return null;
  const unit = p.point_unit ?? "";
  const iv = p.point_interval;
  if (w.source === "C") {
    return `Estimated maximum voltage: ${fmtDec(p.point_estimate, 3).replace(/0$/, "")} pu${iv ? ` (P10–P90: ${fmtDec(iv[0], 3).replace(/0$/, "")}–${fmtDec(iv[1], 3).replace(/0$/, "")})` : ""}; the limit is 1.10 pu.`;
  }
  if (w.source === "B") {
    return `Estimate: ${fmtInt(p.point_estimate)} customers without power at peak${iv ? ` (P10–P90: ${fmtInt(iv[0])}–${fmtInt(iv[1])})` : ""}.`;
  }
  return `${fmtDec(p.point_estimate, 2)} ${unit}`.trim();
}

export function WorkItemPeek({
  w,
  decision,
  crewInfo,
  scenario,
  highlight = false,
  detailError = null,
  onRetry,
}: {
  highlight?: boolean;
  detailError?: string | null;
  onRetry?: () => void;
  w: WorkItem | null;
  decision: Decision | null;
  crewInfo: { crewId: string; seq: number; start: string; end: string } | null;
  scenario: string;
}) {
  if (!w) {
    return (
      <section className="flex flex-1 items-center px-7 py-6 text-[15px] text-muted-foreground">

        Select a work item on the map or timeline to review the decision.
      </section>
    );
  }
  const p = w.prediction;
  const slim = isSlim(w);
  const maxContribution = Math.max(0.0001, ...w.explanation.top_factors.map((f) => Math.abs(f.contribution)));
  const cost = costOf(decision);
  const ev = w.impact.expected_value_lei;
  const scaleMax = Math.max(ev, cost?.cost ?? 0) * 1.08 || 1;
  const est = pointEstimate(w);
  const scoreMin = typeof decision?.threshold?.score_min === "number" ? decision.threshold.score_min : null;
  const ruleText = ruleRo(decision?.rule_id);
  return (
    <section aria-labelledby="peek-title" className={"min-h-0 flex-1 overflow-y-auto px-7 pt-3.5 pb-5" + (highlight ? " spot" : "")}>
      <div className="grid grid-cols-[36px_minmax(0,1fr)_auto] items-center gap-x-3">
        <Marker w={w} decision={decision} selected />
        <div className="min-w-0">
          <h2 id="peek-title" className="truncate text-[18px] font-[600]">
            {itemTitle(w)}
          </h2>
          <p className="truncate text-[14.5px] text-muted-foreground">
            {itemPlace(w)}, {predictionLabelRo(p.label)}
          </p>
        </div>
        <div className="text-right text-[14px] leading-tight text-muted-foreground">
          {crewInfo ? (
            <>
              <b className="font-[560] text-ink">
                {crewInfo.crewId}, stop {crewInfo.seq}
              </b>
              <br />
              {crewInfo.start}–{crewInfo.end}
            </>
          ) : decision ? (
            <b className="font-[560] text-ink">{DECISION_LABEL_RO[decision.decision]}</b>
          ) : (
            "No decision"
          )}
        </div>
      </div>

      <dl className="mt-2.5 grid grid-cols-[104px_minmax(0,1fr)] gap-x-4 text-[15px] [&>dd]:border-t [&>dd]:border-rule [&>dd]:py-2 [&>dt]:border-t [&>dt]:border-rule [&>dt]:py-2.5 [&>dt]:text-[14px] [&>dt]:text-muted-foreground">
        <dt>Score</dt>
        <dd>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span className="num-wide text-[38px]">{scoreText(p.score)}</span>
            <ScoreScale score={p.score} low={p.interval_low} high={p.interval_high} threshold={scoreMin} width={128} />
            <span className="text-[14px] leading-[1.3] whitespace-nowrap text-muted-foreground">
              {p.interval_low != null && p.interval_high != null ? (
                <>
                  interval {fmtScore(p.interval_low)}–{fmtScore(p.interval_high)}
                  <br />
                </>
              ) : null}
              {CONFIDENCE_RO[p.confidence]}
              {scoreMin != null ? `, threshold ${fmtScore(scoreMin)}` : ""}
            </span>
            {w.impact.safety_flag ? (
              <span className="ml-auto flex items-center gap-1.5 text-[14px] font-[560] whitespace-nowrap">
                <svg width="16" height="18" viewBox="0 0 16 18" aria-hidden="true">
                  <path d="M8 1 L15 3.5 V8.5 C15 12.8 12 15.8 8 17 C4 15.8 1 12.8 1 8.5 V3.5 Z" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth="1.6" />
                  <path d="M8.8 4.5 L5.5 9.6 H8 L7.2 13.5 L10.5 8.4 H8 Z" style={{ fill: "var(--ink)" }} />
                </svg>

                Safety flag
              </span>
            ) : null}
          </div>
          {est ? <p className="mt-1 text-[14.5px]">{englishText(est)}</p> : null}
        </dd>

        <dt>Reason</dt>
        <dd className="space-y-1.5" aria-busy={slim && !detailError}>
          {slim && detailError ? (
            <div role="alert" className="text-[14.5px]">
              <p>Could not load details: {englishText(detailError)}</p>
              {onRetry ? (
                <button type="button" onClick={onRetry} className="mt-1 font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink">

                  Retry
                </button>
              ) : null}
            </div>
          ) : null}
          {slim && !detailError
            ? [0, 1, 2].map((i) => (
                <div key={i} className="grid grid-cols-[minmax(0,1fr)_140px_48px] items-center gap-x-3 max-[1600px]:grid-cols-[minmax(0,1fr)_64px_44px]" aria-hidden="true">
                  <span className="h-3.5 animate-pulse rounded-[2px] bg-muted" style={{ width: `${78 - i * 14}%` }} />
                  <span className="h-2.5 animate-pulse bg-muted" />
                  <span className="h-3.5 animate-pulse rounded-[2px] bg-muted" />
                </div>
              ))
            : null}
          {w.explanation.top_factors.slice(0, 4).map((f) => (
            <div key={f.feature} className="grid grid-cols-[minmax(0,1fr)_140px_48px] items-center gap-x-3 max-[1600px]:grid-cols-[minmax(0,1fr)_64px_44px]">
              <span>{factorLabelRo(f.label_ro)}</span>
              <span className="relative h-2.5 bg-muted" aria-hidden="true">
                <i
                  className="absolute inset-y-0 left-0 bg-ink"
                  style={{ width: `${((Math.abs(f.contribution) / maxContribution) * 100).toFixed(1)}%`, opacity: f.contribution < 0 ? 0.45 : 1 }}
                />
              </span>
              <span className="text-right font-[600] tabular-nums">
                {f.contribution >= 0 ? "+" : "−"}
                {fmtScore(Math.abs(f.contribution))}
              </span>
            </div>
          ))}
          <p className="text-[14px] text-muted-foreground">{clampPercentRo(w.explanation.summary_ro)}</p>
        </dd>

        {w.explanation.similar_cases?.length ? (
          <>
            <dt>Similar case</dt>
            <dd>
              {w.explanation.similar_cases.slice(0, 2).map((c) => (
                <div key={c.case_id}>
                  <span translate="no" className="code-id">{c.case_id}</span>, {outcomeRo(c.outcome)}, similarity {fmtScore(c.similarity)}
                </div>
              ))}
            </dd>
          </>
        ) : null}

        {decision ? (
          <>
            <dt>Rule</dt>
            <dd>
              <div className="flex flex-wrap items-center gap-x-3.5 gap-y-1">
                <span translate="no" className="code-id">{decision.rule_id}</span>
                {ruleText ? <span className="text-muted-foreground">{ruleText}</span> : null}
              </div>
              {cost ? (
                <svg width="100%" height="34" className="mt-1.5 block" aria-hidden="true">
                  <rect x="0" y="3" height="10" width={`${((ev / scaleMax) * 72).toFixed(1)}%`} style={{ fill: "var(--ink)" }} />
                  <text x={`${((ev / scaleMax) * 72 + 1.5).toFixed(1)}%`} y="12" fontSize="13" style={{ fill: "var(--ink)" }}>

                    expected value {fmtLei(ev)}
                  </text>
                  <rect x="0" y="20" height="10" width={`${((cost.cost / scaleMax) * 72).toFixed(1)}%`} style={{ fill: "var(--input)" }} />
                  <text x={`${((cost.cost / scaleMax) * 72 + 1.5).toFixed(1)}%`} y="29" fontSize="13" style={{ fill: "var(--muted-foreground)" }}>
                    {cost.label} {fmtLei(cost.cost)}
                  </text>
                </svg>
              ) : null}
              <p className="mt-1">{englishText(decision.reason_ro)}</p>
              <p className="text-[14px] text-muted-foreground">Model recommendation: {ACTION_RO[w.recommended_action]}.</p>
            </dd>
          </>
        ) : null}

        <dt>Traceability</dt>
        <dd className="text-[14px] text-muted-foreground">

          <details>
            <summary className="cursor-pointer underline underline-offset-4">IDs and model version</summary>
            <p className="mt-2 break-all">Work item <span translate="no">{w.work_item_id}</span></p>
          Prediction <b className="dense font-[560] text-ink">{p.prediction_id.slice(0, 8)}…</b>, model{" "}
          <b className="dense font-[560] text-ink">{p.model_version}</b>
          {decision ? (
            <>

              , decision <b className="dense font-[560] text-ink">{decision.audit_id.slice(0, 8)}…</b>
            </>
          ) : null}
          </details>
          <span className="mt-1 block">
            {w.data_quality.synthetic ? "Synthetic asset" : "Real data"}
            {w.data_quality.data_sources.length ? `, sources: ${w.data_quality.data_sources.map(englishText).join(", ")}` : ""}
            {w.created_at ? `; estimated at ${fmtTime(w.created_at)}` : ""}.
          </span>
          <Link
            href={`/lucrari/${encodeURIComponent(w.work_item_id)}?scenariu=${encodeURIComponent(scenario)}`}
            className="mt-1.5 inline-block text-[15px] font-[600] text-ink underline decoration-rule underline-offset-4 hover:decoration-ink"
          >

            Open work item
          </Link>
        </dd>
      </dl>
    </section>
  );
}
