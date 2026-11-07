import { Reveal } from "@/components/reveal"
import { CountUp } from "@/components/count-up"
import { Screen } from "@/components/section-snap"
import { DB, PLAN_DATE_RO, SYNTHETIC_NOTE } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

const S = DB.summary

export const PLAN_FIGURES = [
  { n: fmt(S.items_in), t: "jobs across the three sources" },
  { n: fmt(S.remote_actions), t: "remote checks without a site visit" },
  { n: fmt(S.assigned), t: "jobs assigned to crews" },
  { n: fmt(S.human_review), t: "cases for human review" },
  { n: `${fmt(S.total_km, 0)} km`, t: `travelled by ${S.crews_used} crews` },
  { n: fmt(S.notifications), t: "crew and customer notifications" },
]

/** Full totals stay on /plan; the landing highlights one expected value. */
export function PlanFigures() {
  return (
    <dl className="tabular grid grid-cols-2 gap-x-8 gap-y-7 md:grid-cols-3">
      {PLAN_FIGURES.map((f) => (
        <div key={f.t}>
          <dd className="text-[clamp(1.8rem,min(3.2vw,5.4vh),3rem)] leading-none font-semibold tracking-[-0.02em]">{f.n}</dd>
          <dt className="mt-2 max-w-[22ch] text-foreground/75">{f.t}</dt>
        </div>
      ))}
    </dl>
  )
}

export function Plan() {
  return (
    <Screen id="plan" label={`Plan for ${PLAN_DATE_RO}`}>
      <div className="container-page flex flex-col items-center text-center">
        <Reveal>
          <h2 className="font-sans text-lg font-medium text-foreground/80">Expected plan value</h2>
          <p className="mt-5 leading-none font-semibold tracking-[-0.045em]">
            <CountUp value={Math.round(S.expected_value_lei)} tint className="text-[clamp(3.5rem,14vw,12rem)]" />
            <span className="ml-[0.25em] text-[clamp(1.5rem,4vw,3.4rem)] tracking-[-0.02em] text-foreground/80">RON</span>
          </p>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-7 text-lg text-foreground/80">
            {fmt(S.assigned)} of {fmt(S.items_in)} jobs assigned to {fmt(S.crews_used)} field crews.
          </p>
          <p className="mx-auto mt-3 max-w-[70ch] text-sm text-foreground/65">{SYNTHETIC_NOTE}</p>
          <p className="mx-auto mt-2 max-w-[70ch] break-words text-xs text-foreground/60">Fixed demo snapshot · {DB.planId} · generated {DB.generatedAt}. A new console run may differ.</p>
          <a href="/plan" className="mt-6 inline-flex min-h-11 items-center rounded-full border border-foreground/20 px-5 text-sm hover:bg-surface-2">View plan details</a>
        </Reveal>
      </div>
    </Screen>
  )
}
