import { AnimatePresence, motion, useMotionValueEvent, useScroll, useTransform } from "motion/react"
import { useEffect, useRef, useState, type ReactNode } from "react"
import { Reveal } from "@/components/reveal"
import { SourceIcon } from "@/components/ui/animated-icons"
import { useSnap } from "@/components/section-snap"
import { CountUp } from "@/components/count-up"
import { DecideFlow } from "@/components/decide-flow"
import { DB, DECISION_RO, SOURCES, type Decision, type SourceKey } from "@/data/daybreak"
import { SHIFT, crewDay, hhmm } from "@/lib/crew-status"
import { cn, fmt } from "@/lib/utils"
import { useReduced } from "@/lib/motion"

const ease = [0.22, 1, 0.36, 1] as const
const S = DB.summary

/* ---------- visuals, one per step (also used on the feature pages) ---------- */

export function PerceiveVisual() {
  return (
    <div className="flex h-full flex-col items-center justify-center text-center">
      <CountUp value={S.items_valid} once className="text-[clamp(4rem,9vw,8rem)] leading-none font-semibold tracking-[-0.04em]" />
      <p className="mt-4 text-[clamp(1.1rem,1.6vw,1.4rem)] text-foreground/80">validated jobs</p>
    </div>
  )
}

export const MODEL_LINES: Record<SourceKey | "bilant", { what: string; metric: string }> = {
  A: {
    what: "Probability of a faulty or tampered meter.",
    metric: `ROC AUC ${fmt(DB.models.A.rocAuc, 2)} on unseen households, versus ${fmt(DB.models.A.iforestRocAuc, 2)} for a simple anomaly detector`,
  },
  B: {
    what: "Tomorrow's outage risk and the number of customers affected.",
    metric: `ROC AUC ${fmt(DB.models.B.roc_auc, 2)}, tested on periods after training`,
  },
  C: {
    what: "Hourly maximum voltage at each transformer, with a P10–P90 interval.",
    metric: `Mean error ${fmt(DB.models.C.mae_vmax_pu, 4)} pu, tested on unseen grids`,
  },
  bilant: {
    what: "Normal loss at each transformer and the cause of any excess loss.",
    metric: `Cause predicted in ${fmt(DB.models.bilant.diagnosisAccuracy * 100)}% of cases, across ${fmt(DB.models.bilant.testPosts)} transformers`,
  },
}

export function EstimateVisual() {
  const counts = DB.perSource
  return (
    <div className="flex h-full flex-col justify-center">
      <ul className="space-y-5">
        {(["A", "B", "C"] as SourceKey[]).map((s) => (
          <li key={s} className="grid grid-cols-[auto_1fr_auto] items-start gap-x-5">
            <span className="grid size-14 place-items-center rounded-2xl bg-foreground/[0.05]" style={{ color: SOURCES[s].color }}>
              <SourceIcon s={s} size={36} accent={SOURCES[s].color} className="text-foreground/85" />
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
              <span className={cn("text-[15px]", d === "human_review" ? "font-medium text-ember" : "text-foreground/85")}>{DECISION_RO[d]}</span>
              <span className="h-2 overflow-hidden rounded-full bg-foreground/10">
                <motion.span
                  className={cn("block h-full rounded-full", d === "human_review" ? "bg-ember" : "bg-foreground/70")}
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

/** On the landing page: one crew per kind of day (a full city round, a short one, a storm). */
const LANDING_CREWS = ["E-BV-1", "E-BE-1", "E-BV-3", "E-TM-1"]

const HOURS = (() => {
  const out: number[] = []
  for (let h = Math.ceil(SHIFT.start / 60); h * 60 <= SHIFT.end; h += 2) out.push(h * 60)
  return out
})()

/**
 * The crews' day on one time axis: the thin line is the crew on the road,
 * each solid block is a stop where it works.
 */
export function ActVisual({ compact = false }: { compact?: boolean }) {
  const routes = compact ? DB.routes.filter((r) => LANDING_CREWS.includes(r.crew)) : DB.routes
  const x = (m: number) => `${((Math.min(Math.max(m, SHIFT.start), SHIFT.end) - SHIFT.start) / (SHIFT.end - SHIFT.start)) * 100}%`
  const w = (a: number, b: number) => `${((Math.min(b, SHIFT.end) - Math.max(a, SHIFT.start)) / (SHIFT.end - SHIFT.start)) * 100}%`
  return (
    <div className="flex h-full flex-col justify-center gap-5">
      <div className="grid grid-cols-[7.5rem_1fr_7.5rem] gap-x-4">
        <span />
        <div className="tabular relative h-5 text-sm text-foreground/55">
          {HOURS.map((m) => (
            <span key={m} className="absolute -translate-x-1/2" style={{ left: x(m) }}>
              {hhmm(m)}
            </span>
          ))}
        </div>
        <span />
      </div>
      <ul className={cn("grid", compact ? "gap-5" : "gap-3")} aria-label="Crew day by hour">
        {routes.map((r, i) => {
          const day = crewDay(r.crew)
          const crew = DB.crews.find((c) => c.id === r.crew)
          return (
            <li key={r.crew} className="grid grid-cols-[7.5rem_1fr_7.5rem] items-center gap-x-4">
              <span>
                <span className="block font-medium">{r.crew}</span>
                <span className="block truncate text-sm text-foreground/55">{crew?.depotRo}</span>
              </span>
              <span className={cn("relative block", compact ? "h-8" : "h-6")}>
                {HOURS.map((m) => (
                  <span key={m} aria-hidden className="absolute inset-y-0 w-px bg-foreground/[0.07]" style={{ left: x(m) }} />
                ))}
                <motion.span
                  aria-hidden
                  className="absolute top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-amber/45"
                  style={{ left: x(day.depart), width: w(day.depart, day.back), transformOrigin: "left" }}
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ delay: i * 0.06, duration: 0.5, ease }}
                />
                {day.stops.map((st, j) => (
                  <motion.span
                    key={j}
                    title={`${hhmm(st.arrive)}–${hhmm(st.leave)}`}
                    className="absolute inset-y-0 rounded-[4px] bg-amber"
                    style={{ left: x(st.arrive), width: `max(3px, ${w(st.arrive, st.leave)})` }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.25 + i * 0.06 + j * 0.03, duration: 0.25 }}
                  />
                ))}
              </span>
              <span className="tabular text-right text-sm">
                <span className="block text-foreground/85">
                  {day.open ? `${hhmm(day.depart)}, in the area` : `${hhmm(day.depart)}–${hhmm(day.back)}`}
                </span>
                <span className="block text-foreground/55">
                  {r.stops === 1 ? "1 stop" : `${r.stops} stops`}, {fmt(r.km, 1)} km
                </span>
              </span>
            </li>
          )
        })}
      </ul>
      <p className="flex flex-wrap items-center gap-x-6 gap-y-2 pl-[calc(7.5rem+1rem)] text-sm text-foreground/60">
        <span className="flex items-center gap-2">
          <span aria-hidden className="h-0.5 w-6 rounded-full bg-amber/45" /> travelling
        </span>
        <span className="flex items-center gap-2">
          <span aria-hidden className="h-3 w-3 rounded-[3px] bg-amber" /> on site
        </span>
        {compact && (
          <span>
            {DB.routes.length - routes.length} more crews in the console
          </span>
        )}
      </p>
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
    body: "Reads meters, weather and grid data. Invalid coordinates or impossible scores are quarantined before planning.",
    visual: <PerceiveVisual />,
  },
  {
    title: "Estimate",
    body: "Three models trained by our team estimate probabilities for meters, storms and voltage. Transformer energy balance adds another check.",
    visual: <EstimateVisual />,
  },
  {
    title: "Decide",
    body: "Rules in code require expected value to exceed cost and send uncertain cases to a dispatcher. Every decision records its rule and reason.",
    visual: <DecideFlow />,
  },
  {
    title: "Act",
    body: "Assigns jobs within crew capacity, creates routes, work orders, alerts and notifications, and records every action in the audit log.",
    visual: <ActVisual compact />,
  },
]

/**
 * One pinned screen per stage: the section is as tall as its stages, the
 * content stays in place, and each scroll step (the landing page snaps one
 * stage at a time) moves to the next stage.
 */
export function HowItWorks() {
  const ref = useRef<HTMLElement>(null)
  const snap = useSnap()
  const reduce = useReduced()
  const [wide, setWide] = useState(() => window.innerWidth >= 1024 && window.innerHeight >= 700)
  const pinned = wide && !reduce
  useEffect(() => {
    const resize = () => setWide(window.innerWidth >= 1024 && window.innerHeight >= 700)
    window.addEventListener("resize", resize)
    return () => window.removeEventListener("resize", resize)
  }, [])
  const [active, setActive] = useState(0)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] })
  const fill = useTransform(scrollYProgress, [0, 1], ["0%", "100%"])
  useMotionValueEvent(scrollYProgress, "change", (p) => {
    if (pinned) setActive(Math.max(0, Math.min(STEPS.length - 1, Math.round(p * (STEPS.length - 1)))))
  })

  const go = (i: number) => {
    if (!pinned) return setActive(i)
    if (snap) snap.goToStep("cum", i)
    else if (ref.current) window.scrollTo({ top: ref.current.offsetTop + i * window.innerHeight, behavior: "smooth" })
  }

  return (
    <section
      ref={ref}
      id="cum"
      data-snap
      data-snap-steps={pinned ? STEPS.length : undefined}
      aria-label="How it works"
      className="relative"
      style={pinned ? { height: `${STEPS.length * 100}svh` } : undefined}
    >
      <div className={cn("flex flex-col justify-center py-[clamp(84px,11vh,120px)]", pinned ? "sticky top-0 h-[100svh]" : "min-h-[100svh]")}>
        <div className="container-page grid gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <Reveal>
              <h2 className="h-section">How it works</h2>
            </Reveal>
            <div className="mt-[clamp(20px,4vh,40px)] flex">
              <div aria-hidden className="relative mr-6 w-0.5 shrink-0 rounded-full bg-foreground/10">
                <motion.div className="absolute top-0 left-0 w-0.5 rounded-full bg-ember" style={{ height: fill }} />
              </div>
              <ol className="flex flex-1 flex-col">
                {STEPS.map((st, i) => {
                  const on = i === active
                  return (
                    <li key={st.title}>
                      <button type="button" onClick={() => go(i)} aria-current={on ? "step" : undefined} className="group w-full cursor-pointer py-2.5 text-left">
                        <span
                          className={cn(
                            "block font-display text-[clamp(1.15rem,1.7vw,1.5rem)] font-semibold tracking-[-0.015em] transition-opacity duration-200",
                            on ? "opacity-100" : "opacity-40 group-hover:opacity-75"
                          )}
                        >
                          {st.title}
                        </span>
                        <AnimatePresence initial={false}>
                          {on && (
                            <motion.span
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              transition={{ duration: 0.25, ease }}
                              className="block max-w-[46ch] overflow-hidden pt-1.5 text-foreground/85"
                            >
                              {st.body}
                            </motion.span>
                          )}
                        </AnimatePresence>
                      </button>
                    </li>
                  )
                })}
              </ol>
            </div>
          </div>
          <Reveal delay={0.1} className="lg:col-span-7">
            <div
              data-ui
              className="relative h-[clamp(400px,58vh,540px)] overflow-hidden rounded-2xl p-[clamp(20px,3vw,40px)]"
              style={{ background: "radial-gradient(120% 80% at 85% 0%, rgba(255,197,2,0.12), transparent 60%), var(--surface)" }}
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={active}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.25, ease }}
                  className="relative h-full"
                >
                  {STEPS[active].visual}
                </motion.div>
              </AnimatePresence>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  )
}
