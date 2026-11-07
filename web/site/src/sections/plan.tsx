import { useState } from "react"
import { CountUp } from "@/components/count-up"
import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { DB, PLAN_DATE_RO } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

const S = DB.summary

export const PLAN_FIGURES = [
  { n: fmt(S.items_in), t: "jobs received from three sources" },
  { n: fmt(S.remote_actions), t: "remote checks without travel" },
  { n: fmt(S.assigned), t: "jobs assigned to crews" },
  { n: fmt(S.human_review), t: "cases for human review" },
  { n: `${fmt(S.total_km, 0)} km`, t: `of travel for ${S.crews_used} crews` },
  { n: fmt(S.notifications), t: "crew and customer notifications" },
]

/** The day's plan in numbers, straight from the agent's run (used on /plan). */
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

/** Theme-aware accent for the expected-value counter. */
const COUNTER_INK = "var(--countup-ink)"

/** Expected value of the simulated plan and its crew assignments. */
export function Plan() {
  const [p, setP] = useState(0)
  const color = `color-mix(in oklab, ${COUNTER_INK} ${Math.round(p * 100)}%, var(--foreground))`
  return (
    <Screen id="plan" label={`Plan for ${PLAN_DATE_RO}`}>
      <div className="container-page flex flex-col items-center text-center">
        <Reveal>
          <p className="leading-none font-semibold tracking-[-0.045em]" style={{ color }}>
            <CountUp
              value={Math.round(S.expected_value_lei)}
              onProgress={setP}
              className="text-[clamp(4.5rem,min(15vw,26vh),13rem)]"
            />
            <span className="ml-[0.25em] text-[clamp(1.6rem,min(4vw,7vh),3.4rem)] tracking-[-0.02em] opacity-80">RON expected value</span>
          </p>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-[clamp(16px,3vh,32px)] text-[clamp(1rem,1.3vw,1.2rem)] text-foreground/70">
            The demo plan assigns {fmt(S.assigned)} of {fmt(S.items_in)} jobs to field crews. Expected value is simulated, not measured savings.
          </p>
        </Reveal>
      </div>
    </Screen>
  )
}
