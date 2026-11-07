import { Reveal } from "@/components/reveal"
import { SourceTag } from "@/components/ranking-board"
import { Screen } from "@/components/section-snap"
import { DB, PLAN_DATE_RO, SOURCES, SYNTHETIC_NOTE, type SourceKey } from "@/data/daybreak"
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

/** The day's plan in numbers, straight from the agent's run. */
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
    <Screen id="plan" label="Tomorrow's plan">
      <div className="container-page grid gap-10 lg:grid-cols-12 lg:items-center">
        <div className="lg:col-span-5">
          <Reveal>
            <h2 className="h-section">Plan for {PLAN_DATE_RO}</h2>
          </Reveal>
          <Reveal delay={0.06}>
            <p className="mt-5 max-w-[44ch] text-foreground/90 lg:text-lg">
              An actual agent run for a historical summer day. Expected plan value:
            </p>
            <p className="mt-2 break-all text-xs text-muted-foreground">Fixed demo snapshot · {DB.planId} · generated {DB.generatedAt}. A new console run may differ.</p>
          </Reveal>
          <Reveal delay={0.1}>
            <p className="tabular mt-4 text-[clamp(2.8rem,min(6vw,10vh),5.6rem)] leading-none font-semibold tracking-[-0.035em]">
              {fmt(S.expected_value_lei)} <span className="text-[0.4em] text-foreground/80">lei</span>
            </p>
          </Reveal>
          <Reveal delay={0.14} className="mt-8 space-y-2">
            {(["A", "B", "C"] as SourceKey[]).map((s) => (
              <div key={s} className="flex items-center justify-between gap-6">
                <SourceTag s={s} />
                <span className="tabular text-foreground/85">
                  {fmt(DB.perSource[s]?.total ?? 0)} jobs, {SOURCES[s].long.toLowerCase()}
                </span>
              </div>
            ))}
          </Reveal>
        </div>
        <Reveal delay={0.08} className="lg:col-span-7">
          <div data-ui className="rounded-2xl bg-surface p-[clamp(24px,3vw,44px)]">
            <PlanFigures />
            <p className="mt-8 text-sm text-foreground/60">{SYNTHETIC_NOTE}</p>
          </div>
        </Reveal>
      </div>
    </Screen>
  )
}
