import { AlertTriangle, ShieldAlert } from "lucide-react"
import type { ReactNode } from "react"
import { useApprovals } from "@/lib/approvals"
import { DECISION_TONE } from "@/components/balance-explorer"
import { CrewPicker } from "@/components/crew-picker"
import { CrewStatusPanel } from "@/components/crew-status"
import { SourceTag, VerdictButtons } from "@/components/ranking-board"
import { SeriesChart } from "@/components/series-chart"
import type { Item } from "@/data/daybreak"
import { cn, fmt, lei } from "@/lib/utils"

const CONFIDENCE_RO: Record<string, string> = { high: "încredere mare", medium: "încredere medie", low: "încredere scăzută" }
const OUTCOME_RO: Record<string, string> = {
  avarii: "Avarii",
  avarii_extinse: "Avarii extinse",
  fara_avarii: "Fără avarii",
  furt: "Furt confirmat",
  normal: "Normal",
}
const ACTION_RO: Record<string, string> = {
  human_review: "decide un om",
  preposition_crew: "echipă trimisă din timp în zonă",
  inspect_on_site: "verificare la fața locului",
  remote_reading: "citire de la distanță",
  adjust_tap: "schimbarea prizei transformatorului",
  grid_inspection: "inspecția rețelei",
  phase_rebalance: "reechilibrarea fazelor",
  no_action: "nicio acțiune",
  export_limit: "limitarea injecției în rețea",
  notify_customers: "mesaj către clienți",
}

export function Panel({ title, children, className }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={cn("rounded-2xl bg-surface p-[clamp(18px,2vw,28px)]", className)}>
      {title && <h2 className="mb-4 font-sans text-lg font-semibold tracking-[-0.01em]">{title}</h2>}
      {children}
    </section>
  )
}

/** Score on a 0–1 scale, with its interval and, when there is one, the threshold. */
export function ScoreScale({ score, low, high }: { score: number; low: number | null; high: number | null }) {
  return (
    <div>
      <div className="relative h-3 rounded-full bg-foreground/10">
        {low !== null && high !== null && (
          <span className="absolute inset-y-0 rounded-full bg-foreground/25" style={{ left: `${low * 100}%`, width: `${Math.max(1, (high - low) * 100)}%` }} />
        )}
        <span className="absolute top-1/2 size-4 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ember ring-4 ring-black" style={{ left: `${score * 100}%` }} />
      </div>
      <div className="tabular mt-2 flex justify-between text-sm text-foreground/60">
        <span>0</span>
        <span>
          {fmt(score, 2)}
          {low !== null && high !== null ? ` (interval ${fmt(low, 2)}–${fmt(high, 2)})` : ""}
        </span>
        <span>1</span>
      </div>
    </div>
  )
}

const THRESHOLD_RO: Record<string, string> = {
  score: "scorul modelului",
  expected_value_lei: "valoarea așteptată",
  cost_lei: "costul acțiunii",
  action_cost_lei: "costul acțiunii",
  min_net_value_lei: "valoarea netă minimă",
  lei_per_work_hour: "lei pe oră de lucru",
  net_value_lei: "valoarea netă",
  travel_cost_lei: "costul drumului",
  travel_km_est: "km estimați",
  human_review_min_ev_lei: "valoarea de la care decide un om",
  min_score: "scorul minim",
  overvoltage_limit_pu: "limita de tensiune (pu)",
  vmax_p90_pu: "tensiunea maximă P90 (pu)",
  preposition_cost_lei: "costul turei în zonă",
  alert_min_score: "scorul minim pentru alertă",
  preposition_min_score: "scorul minim pentru echipă în zonă",
  p90_before_pu: "tensiunea P90 înainte (pu)",
  p90_after_pu: "tensiunea P90 după (pu)",
  remedy_cost_lei: "costul soluției",
  remedy_steps: "pași de soluție",
  remedy_options_checked: "soluții verificate",
  planned_notice_working_days: "zile de anunț pentru întrerupere",
  arrive_before_start_min: "minute înainte de furtună",
  post_excess_loss_lei_month: "pierderea peste normal, pe lună",
  max_crews_per_region: "echipe maxime pe regiune",
  visit_cost_lei: "costul vizitei",
  breakeven_score: "scorul de la care merită",
  fusion_a_score: "scorul contorului (A)",
  fusion_combined_score: "scorul combinat cu bilanțul",
  fusion_post_loss_lei_month: "pierderea postului, pe lună",
  visit_min_score: "scorul minim pentru vizită",
  remote_min_score: "scorul minim pentru citire",
  tap_cost_lei: "costul schimbării prizei",
  measurement_cost_lei: "costul măsurătorilor",
  participation_rate: "rata de participare",
}

function thresholdRows(t: Record<string, number | string | null>) {
  return Object.entries(t)
    .filter(([k, v]) => v !== null && v !== "" && typeof v !== "boolean" && THRESHOLD_RO[k])
    .slice(0, 8)
    .map(([k, v]) => {
      const isLei = k.includes("lei")
      const val = typeof v === "number" ? (isLei ? lei(v) : fmt(v, v < 10 ? (k.endsWith("_pu") ? 3 : 2) : 0)) : String(v)
      return { k: THRESHOLD_RO[k], v: val }
    })
}

/** Everything about one work item, from the model's guess to the decision and its trace. */
export function ItemDetail({ item }: { item: Item }) {
  const p = item.prediction
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <SourceTag s={item.source} />
        {item.decision && (
          <span className={cn("font-medium", DECISION_TONE[item.decision])}>
            {item.decisionRo}
            {item.crew ? `, echipa ${item.crew}` : ""}
          </span>
        )}
        {item.impact.safety && (
          <span className="inline-flex items-center gap-1.5 text-bad">
            <ShieldAlert className="size-4" aria-hidden /> Risc de siguranță
          </span>
        )}
        {item.quality.synthetic && <span className="text-sm text-foreground/60">Date sintetice</span>}
      </div>

      <CrewStatusPanel id={item.id} />

      {item.summary && <p className="max-w-[72ch] text-lg text-foreground/90">{item.summary}</p>}

      <div className="grid gap-6 xl:grid-cols-12">
        <Panel title="Ce prezice modelul" className="xl:col-span-5">
          {p.score !== null && <ScoreScale score={p.score} low={p.low} high={p.high} />}
          <dl className="mt-5 space-y-3">
            {p.point !== null && (
              <div>
                <dt className="text-sm text-foreground/60">Estimare</dt>
                <dd className="tabular text-xl font-semibold">
                  {fmt(p.point, p.point < 10 ? 3 : 0)}{" "}
                  <span className="text-base font-normal text-foreground/75">{p.pointUnit}</span>
                </dd>
                {p.pointInterval && (
                  <dd className="tabular text-sm text-foreground/60">
                    interval {fmt(p.pointInterval[0], p.pointInterval[0] < 10 ? 3 : 0)}–{fmt(p.pointInterval[1], p.pointInterval[1] < 10 ? 3 : 0)}
                  </dd>
                )}
              </div>
            )}
            {p.confidence && (
              <div>
                <dt className="text-sm text-foreground/60">Încredere</dt>
                <dd>{CONFIDENCE_RO[p.confidence] ?? p.confidence}</dd>
              </div>
            )}
            {p.abstain && (
              <div className="flex gap-2 rounded-2xl bg-ember/12 p-3">
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-ember" aria-hidden />
                <div>
                  <dt className="font-medium">Modelul nu e sigur</dt>
                  <dd className="text-foreground/85">{p.abstainReason}</dd>
                </div>
              </div>
            )}
          </dl>
        </Panel>

        <Panel title="De ce" className="xl:col-span-7">
          {item.factors.length ? (
            <ul className="space-y-3">
              {item.factors.map((f) => {
                const max = Math.max(...item.factors.map((x) => Math.abs(x.contribution)), 0.01)
                return (
                  <li key={f.label} className="grid grid-cols-[minmax(0,1fr)_minmax(80px,30%)_3.5rem] items-center gap-3">
                    <span className="text-[15px] text-foreground/90">{f.label}</span>
                    <span className="relative h-2 rounded-full bg-foreground/[0.06]">
                      <span className="absolute inset-y-0 left-1/2 w-px bg-foreground/25" />
                      <span
                        className={cn("absolute inset-y-0 rounded-full", f.contribution >= 0 ? "left-1/2 bg-ember" : "right-1/2 bg-foreground/50")}
                        style={{ width: `${(Math.abs(f.contribution) / max) * 50}%` }}
                      />
                    </span>
                    <span className={cn("tabular text-right text-sm", f.contribution >= 0 ? "text-ember-soft" : "text-foreground/65")}>
                      {f.contribution >= 0 ? "+" : "−"}
                      {fmt(Math.abs(f.contribution), 2)}
                    </span>
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="text-foreground/75">Modelul nu a dat factori pentru această lucrare.</p>
          )}
          <p className="mt-4 text-sm text-foreground/55">Spre dreapta împinge spre problemă, spre stânga o face mai puțin probabilă.</p>
        </Panel>
      </div>

      {item.series && (
        <Panel>
          <SeriesChart series={item.series} source={item.source} />
        </Panel>
      )}

      <div className="grid gap-6 xl:grid-cols-12">
        <Panel title="Decizia agentului" className="xl:col-span-7">
          {item.reason && <p className="text-foreground/90">{item.reason}</p>}
          <dl className="tabular mt-5 grid gap-x-8 gap-y-3 sm:grid-cols-2">
            <div>
              <dt className="text-sm text-foreground/60">Regula</dt>
              <dd className="font-medium">{item.rule ?? "fără regulă"}</dd>
            </div>
            {item.action && (
              <div>
                <dt className="text-sm text-foreground/60">Acțiunea recomandată</dt>
                <dd>{ACTION_RO[item.action] ?? item.action.replaceAll("_", " ")}</dd>
              </div>
            )}
            {thresholdRows(item.threshold).map((r) => (
              <div key={r.k}>
                <dt className="text-sm text-foreground/60">{r.k}</dt>
                <dd>{r.v}</dd>
              </div>
            ))}
          </dl>
        </Panel>
        <Panel title="Ce e în joc" className="xl:col-span-5">
          <dl className="tabular space-y-3">
            <div>
              <dt className="text-sm text-foreground/60">Valoarea așteptată</dt>
              <dd className="text-2xl font-semibold">{lei(item.impact.expectedValueLei)}</dd>
            </div>
            <div>
              <dt className="text-sm text-foreground/60">Dacă problema e reală</dt>
              <dd>{lei(item.impact.valueIfTrueLei)}</dd>
            </div>
            <div>
              <dt className="text-sm text-foreground/60">Clienți afectați</dt>
              <dd>{fmt(item.impact.customers)}</dd>
            </div>
            {item.effort && (
              <div>
                <dt className="text-sm text-foreground/60">Efort</dt>
                <dd>
                  {item.effort.duration_min} min, {item.effort.crew_size} oameni
                  {item.effort.requires_planned_outage ? ", cere întrerupere planificată" : ""}
                </dd>
              </div>
            )}
          </dl>
        </Panel>
      </div>

      {item.similar.length > 0 && (
        <Panel title="Cazuri asemănătoare din trecut">
          <ul className="space-y-3">
            {item.similar.map((c) => (
              <li key={c.id} className="grid gap-1 sm:grid-cols-[1fr_auto] sm:gap-6">
                <div>
                  <div className="font-medium">{OUTCOME_RO[c.outcome] ?? c.outcome}</div>
                  <div className="text-foreground/75">{c.note}</div>
                </div>
                <div className="tabular text-sm text-foreground/65 sm:text-right">asemănare {fmt(c.similarity, 2)}</div>
              </li>
            ))}
          </ul>
        </Panel>
      )}

        <Panel title="Urmărire">
          <dl className="space-y-2.5 text-[15px]">
            <div className="flex flex-wrap justify-between gap-x-4">
              <dt className="text-foreground/60">Lucrarea</dt>
              <dd className="break-all">{item.id}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-x-4">
              <dt className="text-foreground/60">Predicția</dt>
              <dd className="break-all">{p.id}</dd>
            </div>
            <div className="flex flex-wrap justify-between gap-x-4">
              <dt className="text-foreground/60">Modelul</dt>
              <dd>{p.model}</dd>
            </div>
            {item.auditId && (
              <div className="flex flex-wrap justify-between gap-x-4">
                <dt className="text-foreground/60">Rândul din jurnal</dt>
                <dd className="break-all">{item.auditId}</dd>
              </div>
            )}
          </dl>
        </Panel>

        {item.decision === "human_review" && <HumanDecision item={item} />}
    </div>
  )
}

/** The three choices a person has when the agent could not decide alone; approving opens the crew picker. */
function HumanDecision({ item }: { item: Item }) {
  const { decisions, crews } = useApprovals()
  const v = decisions.get(item.id)
  const crew = crews.get(item.id)
  return (
    <section
      aria-label="Decizia ta"
      className="rounded-2xl bg-[linear-gradient(135deg,rgba(255,197,2,0.12),rgba(255,92,255,0.08))] p-[clamp(18px,2vw,28px)]"
    >
      <h2 className="font-sans text-lg font-semibold tracking-[-0.01em]">Agentul nu a decis singur. Decide tu</h2>
      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-4">
        <VerdictButtons id={item.id} label={item.label} size="lg" />
        {v && (
          <p role="status" className="text-foreground/80">
            {v === "approved"
              ? crew
                ? `Aprobat: merge echipajul ${crew}.`
                : "Aprobat: alege echipajul care merge."
              : v === "deferred"
                ? "Amânat: rămâne în coadă; agentul îl aduce din nou la următoarea rulare."
                : "Respins: alerta e ignorată pentru mâine; agentul o reevaluează la următoarea rulare."}
          </p>
        )}
      </div>
      {v === "approved" && <CrewPicker item={item} />}
    </section>
  )
}
