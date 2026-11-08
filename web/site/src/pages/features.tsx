import { useEffect, useState } from "react"
import { BalanceExplorer, DiagnosisBars } from "@/components/balance-explorer"
import { Block, NextStep, PageShell } from "@/components/page"
import { Reveal } from "@/components/reveal"
import { DB, DIAGNOSIS_RO, PLAN_DATE_RO, SYNTHETIC_NOTE } from "@/data/daybreak"
import { TO_CONFIRM, EvalTable, agentGain } from "@/sections/demo"
import { ActVisual, DecideVisual, EstimateVisual, PerceiveVisual, STEPS } from "@/sections/how-it-works"
import { PlanFigures } from "@/sections/plan"
import { cn, fmt } from "@/lib/utils"

/* ======================= Tomorrow's plan ======================= */

export function PlanPage() {
  return (
    <PageShell
      title="Tomorrow's plan"
      lead={`From ${fmt(DB.summary.items_in)} possible jobs, the agent selects crew visits, remote checks and cases for human review. This demo plan is for ${PLAN_DATE_RO}.`}
    >
      <Block title="Plan totals" intro={SYNTHETIC_NOTE}>
        <div data-ui className="rounded-2xl bg-surface p-[clamp(24px,3vw,44px)]">
          <PlanFigures />
        </div>
      </Block>
      <Block title="Agent decisions" intro="Each job gets one decision and records the rule behind it.">
        <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
          <DecideVisual />
        </div>
      </Block>
      <Block title="Crews" intro={`${DB.summary.crews_used} crews, limited by their skills and shifts. OR-Tools calculates their routes.`}>
        <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
          <ActVisual />
        </div>
      </Block>
      <NextStep text={`${fmt(DB.summary.human_review)} cases need a dispatcher. Inspect the evidence and assign a crew in the console.`} label="Review cases" to="/app/coada" />
    </PageShell>
  )
}

/* ======================= Bilanț ======================= */

const INPUTS = [
  { t: "Transformer energy meter", d: "Energy leaving the transformer at 15-minute intervals." },
  { t: "Customer meters", d: "Consumption and generation every 15 minutes, plus voltage where available." },
  { t: "Customer-to-transformer mapping", d: "Which transformer supplies each customer." },
  { t: "Weather", d: "Temperature and sunlight help explain normal consumption." },
  { t: "Energy price", d: "Converts energy loss from kWh to lei." },
]

export function BilantPage() {
  const m = DB.modelCards.bilant
  return (
    <PageShell
      title="Energy balance at each transformer"
      lead="Subtract customer readings from the energy leaving a transformer. The model estimates normal loss and the likely cause of any excess. The agent selects an action."
    >
      <Block title="Select a transformer" intro="Eight synthetic transformers from the agent run, covering each cause and the largest losses.">
        <BalanceExplorer full />
      </Block>

      <Block title="Previous model results against baselines" intro="Historical held-out test data for the previous balance model. The active FeederBW model has a separate evaluation with synthetic fault labels.">
        <dl className="tabular grid gap-6 md:grid-cols-3">
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">
              {fmt(m.metrics.normal_mae_kwh_day, 1)} <span className="text-lg text-foreground/70">kWh/day</span>
            </dd>
            <dt className="mt-2 text-foreground/80">normal-loss error, versus {fmt(m.baseline.normal_mae_kwh_day, 1)} for the physical formula</dt>
          </div>
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">{fmt(m.metrics.diagnoza_macro_f1, 2)}</dd>
            <dt className="mt-2 text-foreground/80">cause classification F1, versus {fmt(m.baseline.diagnoza_macro_f1, 2)} for the rule table</dt>
          </div>
          <div data-ui className="rounded-2xl bg-surface p-6">
            <dd className="text-4xl font-semibold">{fmt(m.metrics.diagnoza_abstain_rate * 100)}%</dd>
            <dt className="mt-2 text-foreground/80">of transformers receive an uncertain result instead of a cause</dt>
          </div>
        </dl>
      </Block>

      <Block title="Required inputs">
        <dl className="grid gap-x-12 gap-y-8 md:grid-cols-2 lg:grid-cols-3">
          {INPUTS.map((x) => (
            <div key={x.t}>
              <dt className="font-semibold">{x.t}</dt>
              <dd className="mt-1 text-foreground/80">{x.d}</dd>
            </div>
          ))}
        </dl>
      </Block>

      <Block title="Needs validation with PPC">
        <ul className="max-w-[70ch] space-y-4">
          {TO_CONFIRM.map((c) => (
            <li key={c} className="flex gap-3">
              <span aria-hidden className="mt-2.5 size-2 shrink-0 rounded-full bg-ember" />
              <span className="text-foreground/90">{c}</span>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Inspect each transformer and trace its decision to the model." label="View transformers" to="/app/posturi" />
    </PageShell>
  )
}

/* ======================= Diagnostic ======================= */

const DIAGNOSES = [
  { key: "contor_client", sees: "A meter is stuck, has a shifted clock or reports negative readings", team: "Metering crew, after a remote reading" },
  { key: "furt_inainte_contor", sees: "A constant energy gap appears suddenly, while the meters look normal", team: "Inspection crew" },
  { key: "pierdere_tehnica", sees: "Loss rises under load and the phases are unbalanced", team: "Grid crew" },
  { key: "client_post_gresit", sees: "A meter follows the pattern of customers on another transformer", team: "Correct the mapping without a site visit" },
  { key: "contor_bilant_setat", sees: "The transformer meter reads twice the expected energy", team: "Metering crew" },
]

export function DiagnosticPage() {
  const [active, setActive] = useState(0)
  const f1 = DB.modelCards.bilant.metrics

  useEffect(() => {
    const els = DIAGNOSES.map((_, i) => document.getElementById(`cauza-${i}`)).filter(Boolean) as HTMLElement[]
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(Number(e.target.id.split("-")[1]))),
      { rootMargin: "-45% 0px -50% 0px" }
    )
    els.forEach((el) => io.observe(el))
    return () => io.disconnect()
  }, [])

  const jump = (i: number) => {
    const el = document.getElementById(`cauza-${i}`)
    if (!el) return
    el.scrollIntoView({ behavior: "auto" })
  }

  return (
    <PageShell
      title="Where the energy goes"
      lead="Loss patterns provide evidence of a cause. The agent uses that evidence to select a crew visit, a remote check or a data correction."
    >
      <div className="container-page mt-[clamp(64px,10vh,120px)] grid gap-12 lg:grid-cols-12">
        <aside className="hidden lg:col-span-3 lg:block">
          <nav aria-label="Causes" className="sticky top-32">
            <ul className="space-y-1">
              {DIAGNOSES.map((d, i) => (
                <li key={d.key}>
                  <button
                    type="button"
                    onClick={() => jump(i)}
                    aria-current={active === i ? "true" : undefined}
                    className={cn(
                      "relative w-full cursor-pointer rounded-2xl py-2.5 pr-3 pl-5 text-left transition-colors duration-150",
                      active === i ? "bg-surface text-foreground" : "text-foreground/70 hover:text-foreground"
                    )}
                  >
                    {active === i && <span aria-hidden className="absolute inset-y-3 left-0 w-1 rounded-full bg-ember" />}
                    {DIAGNOSIS_RO[d.key]}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </aside>
        <div className="space-y-[clamp(64px,10vh,120px)] lg:col-span-9">
          {DIAGNOSES.map((d, i) => {
            const example = DB.cases.find((c) => c.diagnosis === d.key)
            const n = DB.posts.filter((p) => p.diagnosis === d.key).length
            return (
              <section key={d.key} id={`cauza-${i}`} className="scroll-mt-32">
                <Reveal>
                  <h2 className="text-[clamp(1.6rem,2.6vw,2.4rem)] leading-tight font-semibold">{DIAGNOSIS_RO[d.key]}</h2>
                </Reveal>
                <Reveal delay={0.06} data-ui className="mt-6 grid gap-8 rounded-2xl bg-surface p-[clamp(20px,3vw,36px)] md:grid-cols-2">
                  <dl className="space-y-5">
                    <div>
                      <dt className="text-sm text-foreground/60">Observed pattern</dt>
                      <dd className="mt-1">{d.sees}</dd>
                    </div>
                    <div>
                      <dt className="text-sm text-foreground/60">Who acts</dt>
                      <dd className="mt-1 font-medium">{d.team}</dd>
                    </div>
                    <div className="tabular flex gap-10">
                      <div>
                        <dd className="text-2xl font-semibold">{n}</dd>
                        <dt className="text-sm text-foreground/60">transformers in the plan</dt>
                      </div>
                      <div>
                        <dd className="text-2xl font-semibold">{fmt(f1[`diagnoza_f1_${d.key}`] ?? 0, 2)}</dd>
                        <dt className="text-sm text-foreground/60">Previous model test F1</dt>
                      </div>
                    </div>
                  </dl>
                  {example ? (
                    <figure>
                      <figcaption className="mb-3 text-sm text-foreground/70">{example.label}: model evidence</figcaption>
                      <DiagnosisBars c={example} />
                    </figure>
                  ) : (
                    <p className="text-foreground/70">No transformer in this plan has this cause.</p>
                  )}
                </Reveal>
              </section>
            )
          })}
        </div>
      </div>

      <Block title="What energy balance adds" intro="Transformer energy balance adds an independent check to meter-level fraud detection.">
        <ul className="grid gap-x-12 gap-y-6 md:grid-cols-2">
          {[
            ["Independent evidence", "A suspicious meter on a transformer with excess loss provides corroborating evidence for review."],
            ["Loss expressed in lei", "Expected recoverable value helps prioritise crew visits."],
            ["Issues beyond the meter", "Theft upstream of the meter, cable losses and unbalanced phases."],
            ["Cost to the distributor", "The distributor pays for losses above the allowance recognised by ANRE."],
          ].map(([t, d]) => (
            <li key={t}>
              <h3 className="font-sans font-semibold">{t}</h3>
              <p className="mt-1 text-foreground/80">{d}</p>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Inspect the evidence and planned action for each transformer." label="Open energy balance" to="/app/posturi" />
    </PageShell>
  )
}

/* ======================= Agent ======================= */

const VISUALS = [<PerceiveVisual key="p" />, <EstimateVisual key="e" />, <DecideVisual key="d" />, <ActVisual key="a" />]

export function AgentPage() {
  const { gain } = agentGain()
  return (
    <PageShell
      title="How the agent plans the day"
      lead="The models estimate risk. Code applies planning rules. Uncertain cases go to a dispatcher before a crew visit."
    >
      {STEPS.map((s, i) => (
        <Block key={s.title} title={s.title} intro={s.body}>
          <div data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]">
            {VISUALS[i]}
          </div>
        </Block>
      ))}

      <Block title={`${gain}% more net value than the best simple strategy`} intro="The same days and crews, with different decision strategies. Synthetic data with known outcomes.">
        <div className="rounded-2xl bg-surface p-[clamp(20px,3vw,36px)]">
          <EvalTable />
        </div>
      </Block>

      <Block title="Planning safeguards">
        <ul className="grid gap-x-12 gap-y-6 md:grid-cols-2">
          {[
            ["Remote checks first", "Re-read meters and event logs remotely before sending a crew."],
            ["Within crew capacity", "Assignments respect each crew's skills, shift and capacity, prioritised by value."],
            ["Human review for uncertainty", "Low scores, unfamiliar areas and full regional capacity require dispatcher review with a recorded reason."],
            ["Traceable decisions", "Each decision links to its prediction, model version and rule."],
          ].map(([t, d]) => (
            <li key={t}>
              <h3 className="font-sans font-semibold">{t}</h3>
              <p className="mt-1 text-foreground/80">{d}</p>
            </li>
          ))}
        </ul>
      </Block>

      <NextStep text="Inspect the full audit log and human review queue." label="Open audit log" to="/app/jurnal" />
    </PageShell>
  )
}
