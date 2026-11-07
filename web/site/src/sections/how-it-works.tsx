import { AnimatePresence, motion, useMotionValueEvent, useScroll, useTransform } from "motion/react"
import { useRef, useState, type ReactNode } from "react"
import { Reveal } from "@/components/reveal"
import { SourceIcon } from "@/components/ui/animated-icons"
import { useSnap } from "@/components/section-snap"
import { DB, DECISION_RO, SOURCES, type Decision, type SourceKey } from "@/data/daybreak"
import { cn, fmt } from "@/lib/utils"

const ease = [0.22, 1, 0.36, 1] as const
const S = DB.summary

/* ---------- visuals, one per step (also used on the feature pages) ---------- */

const INPUTS = [
  { t: "Consumul contoarelor", d: "Peste 2 milioane de contoare care trimit la 15 minute, plus contorul fiecărui post." },
  { t: "Vremea", d: "Prognoza pe zone: vânt, ploaie, radiație solară. Zilele și vremea sunt reale." },
  { t: "Rețeaua", d: "Posturile, clienții de sub ele, echipele și bazele lor (sintetice, pe harta reală)." },
]

export function PerceiveVisual() {
  return (
    <div className="flex h-full flex-col justify-center gap-7">
      <dl className="tabular grid grid-cols-3 gap-4">
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_in)}</dd>
          <dt className="mt-2 text-sm text-white/70">lucrări intrate</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_valid)}</dd>
          <dt className="mt-2 text-sm text-white/70">valide</dt>
        </div>
        <div>
          <dd className="text-[clamp(1.8rem,3vw,2.8rem)] leading-none font-semibold">{fmt(S.items_invalid)}</dd>
          <dt className="mt-2 text-sm text-white/70">în carantină</dt>
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
    what: "Probabilitatea ca un contor să fie defect sau manipulat.",
    metric: `ROC AUC ${fmt(DB.models.A.rocAuc, 2)} pe gospodării nevăzute, față de ${fmt(DB.models.A.iforestRocAuc, 2)} la o detecție de anomalii simplă`,
  },
  B: {
    what: "Probabilitatea de avarii într-o zonă mâine și câți clienți rămân fără curent.",
    metric: `ROC AUC ${fmt(DB.models.B.roc_auc, 2)}, testat pe perioade ulterioare antrenării`,
  },
  C: {
    what: "Tensiunea maximă pe fiecare post, oră cu oră, cu interval P10–P90.",
    metric: `Eroare medie ${fmt(DB.models.C.mae_vmax_pu, 4)} pu, testat pe rețele nevăzute`,
  },
  bilant: {
    what: "Pierderea normală a fiecărui post și cauza a ce lipsește peste ea.",
    metric: `Cauza ghicită în ${fmt(DB.models.bilant.diagnosisAccuracy * 100)}% din cazuri, pe ${fmt(DB.models.bilant.testPosts)} de posturi`,
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
              <div className="text-sm text-white/60">lucrări</div>
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
      <ul className="space-y-3" aria-label="Deciziile agentului">
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
      <ul className="space-y-2" aria-label="Traseele echipelor">
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
                {r.stops === 1 ? "1 oprire" : `${r.stops} opriri`}, {fmt(r.km, 1)} km
              </span>
            </li>
          )
        })}
      </ul>
      <dl className="tabular grid grid-cols-3 gap-4">
        <div>
          <dd className="text-2xl font-semibold">{fmt(S.total_km, 1)} km</dd>
          <dt className="text-sm text-white/65">pentru {S.crews_used} echipe</dt>
        </div>
        <div>
          <dd className="text-2xl font-semibold">{fmt(S.notifications)}</dd>
          <dt className="text-sm text-white/65">notificări</dt>
        </div>
        <div>
          <dd className="text-2xl font-semibold">{fmt(DB.alerts.length)}</dd>
          <dt className="text-sm text-white/65">alerte la dispecerat</dt>
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
    title: "Percepe",
    body: "Citește contoarele, vremea și rețeaua. Ce intră greșit (o coordonată în afara țării, un scor imposibil) stă în carantină, nu în plan.",
    visual: <PerceiveVisual />,
  },
  {
    title: "Estimează",
    body: "Trei modele antrenate de noi dau probabilități, nu verdicte: contoare, furtună, tensiune. Bilanțul pe post se adaugă la contoare.",
    visual: <EstimateVisual />,
  },
  {
    title: "Decide",
    body: "Reguli scrise în cod, nu un LLM: valoarea trebuie să bată costul, iar ce nu e sigur merge la un om. Fiecare decizie are o regulă și un motiv.",
    visual: <DecideVisual />,
  },
  {
    title: "Acționează",
    body: "Împarte lucrările pe echipele limitate, face traseele, ordinele de lucru, alertele și notificările, și scrie totul în jurnal.",
    visual: <ActVisual />,
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
  const [active, setActive] = useState(0)
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] })
  const fill = useTransform(scrollYProgress, [0, 1], ["0%", "100%"])
  useMotionValueEvent(scrollYProgress, "change", (p) => {
    setActive(Math.max(0, Math.min(STEPS.length - 1, Math.round(p * (STEPS.length - 1)))))
  })

  const go = (i: number) => {
    if (snap) snap.goToStep("cum", i)
    else if (ref.current) window.scrollTo({ top: ref.current.offsetTop + i * window.innerHeight, behavior: "smooth" })
  }

  return (
    <section
      ref={ref}
      id="cum"
      data-snap
      data-snap-steps={STEPS.length}
      aria-label="Cum funcționează"
      className="relative"
      style={{ height: `${STEPS.length * 100}svh` }}
    >
      <div className="sticky top-0 flex h-[100svh] flex-col justify-center py-[clamp(84px,11vh,120px)]">
        <div className="container-page grid gap-10 lg:grid-cols-12">
          <div className="lg:col-span-5">
            <Reveal>
              <h2 className="h-section">Cum funcționează</h2>
            </Reveal>
            <div className="mt-[clamp(20px,4vh,40px)] flex">
              <div aria-hidden className="relative mr-6 w-0.5 shrink-0 rounded-full bg-white/10">
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
                              className="block max-w-[46ch] overflow-hidden pt-1.5 text-white/85"
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
