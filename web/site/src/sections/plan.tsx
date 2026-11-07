import { useState } from "react"
import { CountUp } from "@/components/count-up"
import { Reveal } from "@/components/reveal"
import { Screen } from "@/components/section-snap"
import { DB, PLAN_DATE_RO } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

const S = DB.summary

export const PLAN_FIGURES = [
  { n: fmt(S.items_in), t: "lucrări intrate din cele trei surse" },
  { n: fmt(S.remote_actions), t: "verificări de la distanță, fără deplasare" },
  { n: fmt(S.assigned), t: "lucrări trimise la echipe" },
  { n: fmt(S.human_review), t: "cazuri pe care decide un om" },
  { n: `${fmt(S.total_km, 0)} km`, t: `de drum pentru ${S.crews_used} echipe` },
  { n: fmt(S.notifications), t: "notificări pentru echipe și clienți" },
]

/** The day's plan in numbers, straight from the agent's run (used on /plan). */
export function PlanFigures() {
  return (
    <dl className="tabular grid grid-cols-2 gap-x-8 gap-y-7 md:grid-cols-3">
      {PLAN_FIGURES.map((f) => (
        <div key={f.t}>
          <dd className="text-[clamp(1.8rem,min(3.2vw,5.4vh),3rem)] leading-none font-semibold tracking-[-0.02em]">{f.n}</dd>
          <dt className="mt-2 max-w-[22ch] text-white/75">{f.t}</dt>
        </div>
      ))}
    </dl>
  )
}

/** Lime the saved sum turns into as it counts up. */
const LIME = "#a3e635"

/** One number for the day: the sum the plan saves, and how few jobs needed a crew. */
export function Plan() {
  const [p, setP] = useState(0)
  const color = `color-mix(in oklab, ${LIME} ${Math.round(p * 100)}%, #ffffff)`
  return (
    <Screen id="plan" label={`Planul pentru ${PLAN_DATE_RO}`}>
      <div className="container-page flex flex-col items-center text-center">
        <Reveal>
          <p className="leading-none font-semibold tracking-[-0.045em]" style={{ color }}>
            <CountUp
              value={Math.round(S.expected_value_lei)}
              onProgress={setP}
              className="text-[clamp(4.5rem,min(15vw,26vh),13rem)]"
            />
            <span className="ml-[0.25em] text-[clamp(1.6rem,min(4vw,7vh),3.4rem)] tracking-[-0.02em] opacity-80">lei economisiți</span>
          </p>
        </Reveal>
        <Reveal delay={0.12}>
          <p className="mt-[clamp(16px,3vh,32px)] text-[clamp(1rem,1.3vw,1.2rem)] text-white/70">
            Doar {fmt(S.assigned)} din {fmt(S.items_in)} de lucrări aveau de fapt nevoie de echipe pe teren.
          </p>
        </Reveal>
      </div>
    </Screen>
  )
}
