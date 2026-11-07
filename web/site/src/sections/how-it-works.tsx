import { motion } from "motion/react"
import { useState, type ReactNode } from "react"
import { CountUp } from "@/components/count-up"
import { DecideFlow } from "@/components/decide-flow"
import { SHIFT, crewDay, hhmm } from "@/lib/crew-status"
import { Reveal } from "@/components/reveal"
import { SourceIcon } from "@/components/ui/animated-icons"
import { DB, SOURCES, type SourceKey } from "@/data/daybreak"
import { cn, fmt } from "@/lib/utils"

const ease = [0.22, 1, 0.36, 1] as const
const S = DB.summary

/* ---------- visuals, one per step (also used on the feature pages) ---------- */

const INPUTS = [
  { t: "Meter readings", d: "PPC's workshop described over 2 million smart meters reporting every 15 minutes. Demo readings are synthetic." },
  { t: "Weather", d: "Public Open-Meteo forecasts for wind, rain and solar radiation. The storm model uses historical Open-Meteo weather and EAGLE-I outages." },
  { t: "Grid", d: "Transformers, connected customers, crews and depots are synthetic, on a real map." },
]

export function PerceiveVisual({ compact = false }: { compact?: boolean }) {
  if (compact) return (
    <div className="flex flex-col items-center py-5 text-center">
      <CountUp value={S.items_valid} className="text-[clamp(4rem,9vw,8rem)] leading-none font-semibold tracking-[-0.04em]" />
      <p className="mt-4 text-lg text-foreground/80">validated jobs</p>
      <details className="mt-6 w-full text-left">
        <summary className="cursor-pointer py-2 text-sm text-foreground/75">Data inputs and validation</summary>
        <p className="mt-3 text-sm text-foreground/70">{fmt(S.items_in)} incoming jobs; {fmt(S.items_invalid)} quarantined.</p>
        <dl className="mt-4 space-y-4">{INPUTS.map((x) => <div key={x.t}><dt className="font-medium">{x.t}</dt><dd className="text-sm text-foreground/75">{x.d}</dd></div>)}</dl>
      </details>
    </div>
  )
  return (
    <div className="flex h-full flex-col justify-center gap-7">
      <dl className="tabular grid grid-cols-3 gap-4">
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_in)}</dd>
          <dt className="mt-2 text-sm text-foreground/70">incoming jobs</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_valid)}</dd>
          <dt className="mt-2 text-sm text-foreground/70">valid</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_invalid)}</dd>
          <dt className="mt-2 text-sm text-foreground/70">quarantined</dt>
        </div>
      </dl>
      <ul className="space-y-4">
        {INPUTS.map((x) => (
          <li key={x.t}>
            <div className="font-medium">{x.t}</div>
            <div className="text-foreground/75">{x.d}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export const MODEL_LINES: Record<SourceKey | "bilant", { what: string; metric: string }> = {
  A: {
    what: "Probability that a meter is faulty or tampered with.",
    metric: `ROC AUC ${fmt(DB.models.A.rocAuc, 2)} on unseen households, versus ${fmt(DB.models.A.iforestRocAuc, 2)} for a simple anomaly detector`,
  },
  B: {
    what: "Probability of outages tomorrow and estimated customers affected.",
    metric: `ROC AUC ${fmt(DB.models.B.roc_auc, 2)}, tested on periods after the training data`,
  },
  C: {
    what: "Hourly peak voltage at each transformer, with a P10–P90 interval.",
    metric: `Mean error ${fmt(DB.models.C.mae_vmax_pu, 4)} pu, tested on unseen grids`,
  },
  bilant: {
    what: "Normal loss at each transformer and the likely cause of any excess.",
    metric: `Correct cause in ${fmt(DB.models.bilant.diagnosisAccuracy * 100)}% of cases across ${fmt(DB.models.bilant.testPosts)} transformers`,
  },
}

export function EstimateVisual() {
  const counts = DB.perSource
  return (
    <div className="flex h-full flex-col justify-center">
      <ul className="space-y-5">
        {(["A", "B", "C"] as SourceKey[]).map((s) => (
          <li key={s} className="grid grid-cols-[auto_1fr_auto] items-start gap-x-5">
            <span className="grid size-14 place-items-center rounded-2xl bg-foreground/[0.05]">
              <SourceIcon s={s} size={36} accent={`var(--source-${s.toLowerCase()})`} className="text-foreground/85" />
            </span>
            <div>
              <div className="font-medium">{SOURCES[s].name}</div>
              <p className="mt-0.5 text-foreground/85">{MODEL_LINES[s].what}</p>
              <p className="mt-0.5 text-sm text-foreground/60">{MODEL_LINES[s].metric}</p>
            </div>
            <div className="tabular text-right">
              <div className="text-2xl font-semibold">{fmt(counts[s]?.total ?? 0)}</div>
              <div className="text-sm text-foreground/60">jobs</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function DecideVisual() {
  return <DecideFlow />
}

export function ActVisual({ compact = false }: { compact?: boolean }) {
  const routes = compact ? DB.routes.slice(0, 4) : DB.routes
  const hours = Array.from({ length: Math.floor((SHIFT.end - SHIFT.start) / 120) + 1 }, (_, i) => SHIFT.start + i * 120)
  const x = (m: number) => `${((Math.min(Math.max(m, SHIFT.start), SHIFT.end) - SHIFT.start) / (SHIFT.end - SHIFT.start)) * 100}%`
  const width = (a: number, b: number) => `${Math.max(0, (Math.min(b, SHIFT.end) - Math.max(a, SHIFT.start)) / (SHIFT.end - SHIFT.start)) * 100}%`
  return (
    <div className="flex flex-col gap-5">
      <div className="grid grid-cols-[5rem_1fr] gap-3 sm:grid-cols-[7rem_1fr] sm:gap-5">
        <span />
        <div className="tabular relative h-5 text-xs text-foreground/60">
          {hours.map((m, i) => <span key={m} className={`absolute ${i === 0 ? "" : i === hours.length - 1 ? "-translate-x-full" : "-translate-x-1/2"}`} style={{ left: x(m) }}>{hhmm(m)}</span>)}
        </div>
      </div>
      <ul className="grid gap-5" aria-label="Planned crew day, with estimated work windows">
        {routes.map((r, i) => {
          const day = crewDay(r.crew)
          if (!day) return null
          return (
            <li key={r.crew} className="grid grid-cols-[5rem_1fr] items-center gap-3 sm:grid-cols-[7rem_1fr] sm:gap-5">
              <span className="text-sm font-medium">{r.crew}<span className="block text-xs font-normal text-foreground/60">{r.stops} {r.stops === 1 ? "stop" : "stops"}</span></span>
              <div>
                <span className="relative block h-7">
                  {hours.map((m) => <span key={m} aria-hidden className="absolute inset-y-0 w-px bg-foreground/10" style={{ left: x(m) }} />)}
                  <motion.span aria-hidden className="absolute top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-amber/45" style={{ left: x(day.depart), width: width(day.depart, day.back), transformOrigin: "left" }} initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: i * 0.04, duration: 0.4, ease }} />
                  {day.stops.map((stop, j) => (
                    <span key={j} title={`Planned arrival ${hhmm(stop.arrive)}; estimated departure ${hhmm(stop.leave)}`} className="absolute inset-y-0 rounded-sm bg-amber" style={{ left: x(stop.arrive), width: `max(3px, ${width(stop.arrive, stop.leave)})` }} />
                  ))}
                </span>
                <p className="tabular mt-1 text-xs text-foreground/70">{day.open ? `From ${hhmm(day.depart)}, on call` : `${hhmm(day.depart)}–${hhmm(day.back)}`} · {fmt(r.km, 1)} km</p>
              </div>
            </li>
          )
        })}
      </ul>
      <p className="text-xs leading-relaxed text-foreground/65">Lines show the route window; blocks show estimated on-site time from planned arrivals.{compact && DB.routes.length > routes.length ? ` ${routes.length} of ${DB.routes.length} crews shown; all routes are on the plan page.` : ""}</p>
    </div>
  )
}

/* ---------- the steps ---------- */

export interface Step {
  title: string
  body: string
  visual: ReactNode
}

export const STEPS: Step[] = [
  {
    title: "Perceive",
    body: "Reads meter, weather and grid data. Invalid coordinates and impossible scores are quarantined before planning.",
    visual: <PerceiveVisual compact />,
  },
  {
    title: "Estimate",
    body: "Our trained models estimate meter faults, storm outages and voltage. Transformer energy balance adds evidence to meter alerts.",
    visual: <EstimateVisual />,
  },
  {
    title: "Decide",
    body: "Code applies the rules. Expected value must exceed cost; uncertain cases go to a person. Each decision records its rule and reason.",
    visual: <DecideVisual />,
  },
  {
    title: "Act",
    body: "Assigns work within crew capacity, plans routes, creates work orders and notifications, and records each action in the audit log.",
    visual: <ActVisual compact />,
  },
]

/** Read all four steps at once; select one to inspect its output. */
export function HowItWorks() {
  const [active, setActive] = useState(0)
  return (
    <section id="cum" aria-label="How it works" className="relative py-[clamp(84px,11vh,120px)]">
      <div className="container-page grid items-start gap-10 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <Reveal><h2 className="h-section">How it works</h2></Reveal>
          <p className="mt-5 text-foreground/70">Select a step to inspect its output.</p>
          <ol className="mt-6 space-y-2">
            {STEPS.map((step, i) => (
              <li key={step.title}>
                <button
                  type="button"
                  onClick={() => setActive(i)}
                  aria-pressed={i === active}
                  aria-controls="agent-step-output"
                  className={cn("w-full cursor-pointer rounded-2xl p-4 text-left transition-colors", i === active ? "bg-surface-2" : "hover:bg-surface")}
                >
                  <span className={cn("block font-display text-lg font-semibold", i === active ? "text-accent-ink" : "text-foreground")}>{step.title}</span>
                  <span className="mt-2 block text-foreground/85">{step.body}</span>
                </button>
              </li>
            ))}
          </ol>
        </div>
        <Reveal delay={0.1} className="lg:col-span-7">
          <div id="agent-step-output" data-ui className="rounded-2xl bg-surface p-[clamp(20px,3vw,40px)]" aria-label={`${STEPS[active].title} output`}>
            <h3 className="mb-6 font-sans text-lg font-semibold">{STEPS[active].title}</h3>
            {STEPS[active].visual}
          </div>
        </Reveal>
      </div>
    </section>
  )
}
