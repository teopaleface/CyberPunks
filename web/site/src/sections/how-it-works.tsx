import { motion } from "motion/react"
import { useState, type ReactNode } from "react"
import { Reveal } from "@/components/reveal"
import { SourceIcon } from "@/components/ui/animated-icons"
import { DB, DECISION_RO, SOURCES, type Decision, type SourceKey } from "@/data/daybreak"
import { cn, fmt } from "@/lib/utils"

const ease = [0.22, 1, 0.36, 1] as const
const S = DB.summary

/* ---------- visuals, one per step (also used on the feature pages) ---------- */

const INPUTS = [
  { t: "Meter readings", d: "PPC's workshop described over 2 million smart meters reporting every 15 minutes. Demo readings are synthetic." },
  { t: "Weather", d: "Public Open-Meteo forecasts for wind, rain and solar radiation. The storm model uses historical Open-Meteo weather and EAGLE-I outages." },
  { t: "Grid", d: "Transformers, connected customers, crews and depots are synthetic, on a real map." },
]

export function PerceiveVisual() {
  return (
    <div className="flex h-full flex-col justify-center gap-7">
      <dl className="tabular grid grid-cols-3 gap-4">
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_in)}</dd>
          <dt className="mt-2 text-sm text-white/70">incoming jobs</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_valid)}</dd>
          <dt className="mt-2 text-sm text-white/70">valid</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_invalid)}</dd>
          <dt className="mt-2 text-sm text-white/70">quarantined</dt>
        </div>
      </dl>
      <ul className="space-y-4">
        {INPUTS.map((x) => (
          <li key={x.t}>
            <div className="font-medium">{x.t}</div>
            <div className="text-white/75">{x.d}</div>
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
            <span className="grid size-14 place-items-center rounded-2xl bg-white/[0.05]" style={{ color: SOURCES[s].color }}>
              <SourceIcon s={s} size={36} accent={SOURCES[s].color} className="text-white/85" />
            </span>
            <div>
              <div className="font-medium">{SOURCES[s].name}</div>
              <p className="mt-0.5 text-white/85">{MODEL_LINES[s].what}</p>
              <p className="mt-0.5 text-sm text-white/60">{MODEL_LINES[s].metric}</p>
            </div>
            <div className="tabular text-right">
              <div className="text-2xl font-semibold">{fmt(counts[s]?.total ?? 0)}</div>
              <div className="text-sm text-white/60">jobs</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

const DECISION_ORDER: Decision[] = ["remote_action", "deferred", "assigned", "human_review", "notify"]

export function DecideVisual() {
  const max = Math.max(...DECISION_ORDER.map((d) => DB.decisionCounts[d] ?? 0))
  return (
    <div className="flex h-full flex-col justify-center gap-6">
      <ul className="space-y-3" aria-label="Agent decisions">
        {DECISION_ORDER.map((d, i) => {
          const n = DB.decisionCounts[d] ?? 0
          return (
            <li key={d} className="grid grid-cols-[11rem_1fr_3.5rem] items-center gap-4">
              <span className={cn("text-[15px]", d === "human_review" ? "font-medium text-ember" : "text-white/85")}>{DECISION_RO[d]}</span>
              <span className="h-2 overflow-hidden rounded-full bg-white/10">
                <motion.span
                  className={cn("block h-full rounded-full", d === "human_review" ? "bg-ember" : "bg-white/70")}
                  initial={{ width: 0 }}
                  animate={{ width: `${(n / max) * 100}%` }}
                  transition={{ delay: i * 0.05, duration: 0.4, ease }}
                />
              </span>
              <span className="tabular text-right font-medium">{fmt(n)}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

const toMin = (t: string) => {
  const [h, m] = t.split(":").map(Number)
  return h * 60 + m
}

export function ActVisual() {
  const start = 8 * 60,
    end = 17 * 60
  return (
    <div className="flex h-full flex-col justify-center gap-5">
      <ul className="space-y-2" aria-label="Crew routes">
        {DB.routes.map((r, i) => {
          const a = Math.max(0, (toMin(r.depart) - start) / (end - start))
          const b = Math.min(1, (toMin(r.back || "17:00") - start) / (end - start))
          const src = (Object.keys(r.sources)[0] as SourceKey) ?? "A"
          return (
            <li key={r.crew} className="grid grid-cols-[4.5rem_1fr_7rem] items-center gap-3 text-sm">
              <span className="font-medium">{r.crew}</span>
              <span className="relative h-5 rounded-[4px] bg-white/[0.06]">
                <motion.span
                  className="absolute inset-y-0 rounded-[4px]"
                  style={{ left: `${a * 100}%`, background: SOURCES[src].color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${(b - a) * 100}%` }}
                  transition={{ delay: i * 0.04, duration: 0.4, ease }}
                />
              </span>
              <span className="tabular text-right text-white/75">
                {r.stops === 1 ? "1 stop" : `${r.stops} stops`}, {fmt(r.km, 1)} km
              </span>
            </li>
          )
        })}
      </ul>
      <dl className="tabular grid grid-cols-3 gap-4">
        <div>
          <dd className="text-2xl font-semibold">{fmt(S.total_km, 1)} km</dd>
          <dt className="text-sm text-white/65">for {S.crews_used} crews</dt>
        </div>
        <div>
          <dd className="text-2xl font-semibold">{fmt(S.notifications)}</dd>
          <dt className="text-sm text-white/65">notifications</dt>
        </div>
        <div>
          <dd className="text-2xl font-semibold">{fmt(DB.alerts.length)}</dd>
          <dt className="text-sm text-white/65">dispatcher alerts</dt>
        </div>
      </dl>
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
    visual: <PerceiveVisual />,
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
    visual: <ActVisual />,
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
          <p className="mt-5 text-white/70">Select a step to inspect its output.</p>
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
                  <span className={cn("block font-display text-lg font-semibold", i === active ? "text-ember" : "text-white")}>{step.title}</span>
                  <span className="mt-2 block text-white/85">{step.body}</span>
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
