import { ChevronDown } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { useState } from "react"
import { BILANT_NOTE, DB, DIAGNOSIS_RO, type Case, type Decision } from "@/data/daybreak"
import { cn, fmt, lei } from "@/lib/utils"

const ease = [0.22, 1, 0.36, 1] as const

export const DECISION_TONE: Record<Decision, string> = {
  assigned: "text-ember-soft",
  remote_action: "text-white",
  human_review: "text-ember",
  deferred: "text-white/65",
  notify: "text-white/85",
}

const CLASS_ORDER = ["normal", "contor_client", "furt_inainte_contor", "pierdere_tehnica", "client_post_gresit", "contor_bilant_setat"]

/** How sure the model is of each cause: the six classes as bars. */
export function DiagnosisBars({ c }: { c: Case }) {
  return (
    <ul className="space-y-2.5" aria-label="Probabilitatea fiecărei cauze">
      {CLASS_ORDER.map((k) => {
        const v = c.proba[k] ?? 0
        const top = k === c.diagnosis
        return (
          <li key={k} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1">
            <span className={cn("truncate text-[15px]", top ? "font-medium text-white" : "text-white/75")}>{DIAGNOSIS_RO[k]}</span>
            <span className="tabular text-right text-sm text-white/80">{fmt(v * 100)}%</span>
            <span className="col-span-2 h-1.5 overflow-hidden rounded-full bg-white/10">
              <motion.span
                className={cn("block h-full rounded-full", top ? "bg-ember" : "bg-white/45")}
                initial={false}
                animate={{ width: `${Math.max(v * 100, 0.5)}%` }}
                transition={{ duration: 0.3, ease }}
              />
            </span>
          </li>
        )
      })}
    </ul>
  )
}

/** What pushed the model toward its answer, with signed contributions. */
export function Factors({ c }: { c: Case }) {
  const max = Math.max(...c.factors.map((f) => Math.abs(f.contribution)), 0.01)
  return (
    <ul className="space-y-3">
      {c.factors.map((f) => (
        <li key={f.label}>
          <div className="flex items-baseline justify-between gap-4">
            <span className="text-[15px] text-white/90">{f.label}</span>
            <span className={cn("tabular shrink-0 text-sm", f.contribution >= 0 ? "text-ember-soft" : "text-white/65")}>
              {f.contribution >= 0 ? "+" : "−"}
              {fmt(Math.abs(f.contribution), 2)}
            </span>
          </div>
          <span className="mt-1.5 block h-1 rounded-full bg-white/10">
            <span
              className={cn("block h-full rounded-full", f.contribution >= 0 ? "bg-ember/80" : "bg-white/40")}
              style={{ width: `${(Math.abs(f.contribution) / max) * 100}%` }}
            />
          </span>
        </li>
      ))}
    </ul>
  )
}

export function CasePicker({
  value,
  onChange,
  cases = DB.cases,
  dense = false,
}: {
  value: string
  onChange: (id: string) => void
  cases?: Case[]
  dense?: boolean
}) {
  return (
    <ul className="flex flex-col gap-1.5" aria-label="Posturi de transformare">
      {cases.map((c) => {
        const active = c.id === value
        return (
          <li key={c.id}>
            <button
              type="button"
              onClick={() => onChange(c.id)}
              aria-pressed={active}
              className={cn(
                "relative flex w-full cursor-pointer items-center gap-4 rounded-2xl text-left transition-[background-color,transform] duration-200 active:scale-[0.99]",
                dense ? "px-4 py-2.5" : "px-5 py-3",
                active ? "bg-surface-2" : "hover:bg-surface"
              )}
            >
              {active && (
                <motion.span
                  layoutId={`case-beam-${dense ? "d" : "n"}`}
                  transition={{ duration: 0.25, ease }}
                  className="absolute inset-y-3 left-0 w-1 rounded-full bg-ember"
                />
              )}
              <span className="min-w-0 flex-1">
                <span className="block truncate font-medium">{c.label.replace(" (sintetic)", "")}</span>
                <span className="block truncate text-sm text-white/65">{c.diagnosisRo}</span>
              </span>
              <span className="tabular shrink-0 text-right font-medium">
                {c.lossLeiMonth ? lei(c.lossLeiMonth) : "0 lei"}
                <span className="block text-xs font-normal text-white/60">pe lună</span>
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

const SKILL_RO: Record<string, string> = {
  metering: "echipa de contoare",
  lv_grid: "echipa de rețea (joasă tensiune)",
  mv_grid: "echipa de rețea (medie tensiune)",
}

const ITEMS_BY_ID = new Map(DB.items.map((i) => [i.id, i]))

/** What happens because of the model's conclusion, in one sentence and three numbers. */
export function outcomeOf(c: Case) {
  const it = ITEMS_BY_ID.get(c.id)
  const t = (it?.threshold ?? {}) as Record<string, number | undefined>
  const cost = t.cost_lei ?? t.action_cost_lei ?? null
  const value = t.expected_value_lei ?? c.expectedValueLei
  const net = t.net_value_lei ?? (cost !== null && value ? value - cost : null)
  const team = it?.effort ? SKILL_RO[it.effort.crew_skill] ?? "o echipă" : "o echipă"
  switch (c.decision) {
    case "assigned":
      return {
        title: `Trimitem echipa ${c.crew} mâine`,
        body: `Merge ${team}${it?.effort ? `, ${it.effort.crew_size} oameni, ${it.effort.duration_min} min` : ""}.`,
        cost,
        value,
        net,
      }
    case "remote_action":
      return {
        title: "Verificăm de la distanță, fără deplasare",
        body:
          cost !== null && cost <= 10
            ? `Recitim contoarele și jurnalul lor de evenimente. Trimitem ${team} doar dacă se confirmă.`
            : `Întâi o verificare de la distanță; dacă se confirmă, merge ${team}.`,
        cost: cost !== null && cost <= 10 ? cost : 2,
        value,
        net: value ? value - (cost !== null && cost <= 10 ? cost : 2) : null,
      }
    case "deferred":
      return {
        title: "Amânat, nu merită încă o deplasare",
        body: "Rămâne pe listă; agentul îl reevaluează mâine, cu datele noi.",
        cost,
        value,
        net: null,
      }
    case "human_review":
      return { title: "Decide un om", body: "Modelul nu e destul de sigur; cazul ajunge la dispecer.", cost, value, net: null }
    default:
      return { title: c.decisionRo, body: "", cost, value, net }
  }
}

/** One case: the cause, what it costs, and what we do about it. The reasons open on demand. */
export function CaseDetail({ c, full = false }: { c: Case; full?: boolean }) {
  const [why, setWhy] = useState(false)
  const o = outcomeOf(c)
  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={c.id}
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 6 }}
        transition={{ duration: 0.2, ease }}
      >
        <div className="flex flex-wrap items-start justify-between gap-x-8 gap-y-2">
          <div>
            <h3 className="font-sans text-[clamp(1.25rem,1.8vw,1.6rem)] font-semibold tracking-[-0.015em]">{c.diagnosisRo}</h3>
            <p className="mt-1 text-white/70">{c.label}</p>
          </div>
          <div className="tabular text-right">
            <div className="text-[clamp(1.8rem,2.8vw,2.6rem)] leading-none font-semibold text-amber">{fmt(c.score * 100)}%</div>
            <div className="mt-1 text-sm text-white/65">cât de sigur e modelul</div>
          </div>
        </div>

        <p className="mt-4 text-[17px] text-white/90">
          {c.lossLeiMonth ? (
            <>
              Se pierd <span className="tabular font-semibold text-white">{lei(c.lossLeiMonth)}</span> pe lună peste pierderea normală
              {c.excessKwhDay !== null ? (
                <>
                  , adică <span className="tabular font-semibold text-white">{fmt(c.excessKwhDay, 1)} kWh</span> pe zi
                </>
              ) : null}
              .
            </>
          ) : (
            "Nu se pierd bani: e o eroare de măsură, care blochează bilanțul până se corectează."
          )}
        </p>

        <div className="mt-5 rounded-2xl bg-[linear-gradient(135deg,rgba(255,197,2,0.14),rgba(255,92,255,0.06))] p-4 lg:p-5">
          <p className={cn("text-lg font-semibold", DECISION_TONE[c.decision])}>{o.title}</p>
          {o.body && <p className="mt-1 text-white/85">{o.body}</p>}
          <dl className="tabular mt-4 grid grid-cols-3 gap-4">
            <div>
              <dd className="text-xl font-semibold">{o.cost !== null ? lei(o.cost) : "fără"}</dd>
              <dt className="text-sm text-white/65">costul acțiunii</dt>
            </div>
            <div>
              <dd className="text-xl font-semibold">{o.value ? lei(o.value) : "fără"}</dd>
              <dt className="text-sm text-white/65">valoarea așteptată</dt>
            </div>
            <div>
              <dd className="text-xl font-semibold text-amber">{o.net !== null ? lei(o.net) : "nu încă"}</dd>
              <dt className="text-sm text-white/65">câștig net</dt>
            </div>
          </dl>
        </div>

        <button
          type="button"
          onClick={() => setWhy((w) => !w)}
          aria-expanded={why}
          className="group mt-4 inline-flex cursor-pointer items-center gap-2 text-white/80 transition-colors duration-150 hover:text-white"
        >
          <ChevronDown className={cn("size-4 transition-transform duration-200", why && "rotate-180")} aria-hidden />
          {why ? "Ascunde motivele" : "De ce crede modelul asta?"}
        </button>
        <AnimatePresence initial={false}>
          {why && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25, ease }}
              className="overflow-hidden"
            >
              <div className="grid gap-8 pt-4 md:grid-cols-2">
                <div>
                  <h4 className="mb-3 font-sans text-sm font-medium text-white/70">Factorii</h4>
                  <Factors c={c} />
                </div>
                <div>
                  <h4 className="mb-3 font-sans text-sm font-medium text-white/70">Toate cauzele posibile</h4>
                  <DiagnosisBars c={c} />
                </div>
              </div>
              {full && c.reason && <p className="mt-4 text-white/80">{c.reason}</p>}
              {full && (
                <p className="mt-2 text-sm text-white/55">
                  Regula {c.rule}, modelul {c.model}
                </p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </AnimatePresence>
  )
}

/** Picker + the selected case, the live balance. */
export function BalanceExplorer({ compact = false, full = false }: { compact?: boolean; full?: boolean }) {
  const [id, setId] = useState(DB.cases[0].id)
  const c = DB.cases.find((x) => x.id === id)!
  return (
    <div>
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="lg:col-span-4">
          <CasePicker value={id} onChange={setId} dense={compact} />
        </div>
        <div data-ui className="self-start rounded-2xl bg-surface p-5 lg:col-span-8 lg:p-6">
          <CaseDetail c={c} full={full} />
        </div>
      </div>
      <p className="mt-3 text-sm text-white/55">{BILANT_NOTE}. Posturi și contoare sintetice.</p>
    </div>
  )
}
