import { CircleCheck, ClipboardCheck, Clock, LogOut, ScanSearch, Truck, Wrench } from "lucide-react"
import { DB } from "@/data/daybreak"
import { useApprovals } from "@/lib/approvals"
import { PHASE_RO, statusAt, useSimClock, type CrewPhase, type CrewStatus } from "@/lib/crew-status"
import { cn } from "@/lib/utils"

const PHASE_ICON: Record<CrewPhase, typeof Truck> = {
  programata: Clock,
  tranzit: Truck,
  diagnosticare: ScanSearch,
  lucru: Wrench,
  finalizare: ClipboardCheck,
  retragere: LogOut,
  incheiata: CircleCheck,
}

const PHASE_TONE: Record<CrewPhase, string> = {
  programata: "text-foreground/60",
  tranzit: "text-[#6b8cff]",
  diagnosticare: "text-amber",
  lucru: "text-amber",
  finalizare: "text-ok",
  retragere: "text-magenta",
  incheiata: "text-ok",
}

/** The crew's status for an item, or the crew a person picked in "Decide un om" (not yet routed). */
export function useCrewStatus(id: string): CrewStatus | null {
  const { now } = useSimClock()
  const { decisions, crews } = useApprovals()
  const s = statusAt(id, now)
  if (s) return s
  const picked = decisions.get(id) === "approved" ? crews.get(id) : undefined
  if (!picked) return null
  return { crew: picked, phase: "programata", seq: 0, stops: 0, arrive: "", leave: "", note: "Alocată de tine; intră în traseul echipei la următoarea rulare." }
}

export function PhaseIcon({ phase, className }: { phase: CrewPhase; className?: string }) {
  const Icon = PHASE_ICON[phase]
  return <Icon className={cn("size-[18px] shrink-0", PHASE_TONE[phase], `cs-${phase}`, className)} aria-hidden />
}

/** One table cell: icon, phase and crew. */
export function CrewStatusCell({ id }: { id: string }) {
  const s = useCrewStatus(id)
  if (!s) return <span className="text-foreground/35">Fără echipaj</span>
  return (
    <span className="flex items-center gap-2.5" title={s.note}>
      <PhaseIcon phase={s.phase} />
      <span>
        <span className={cn("block font-medium", PHASE_TONE[s.phase])}>{PHASE_RO[s.phase]}</span>
        <span className="block text-sm text-foreground/55">{s.crew}</span>
      </span>
    </span>
  )
}

const ORDER: CrewPhase[] = ["tranzit", "diagnosticare", "lucru", "finalizare", "retragere"]

/** Near the top of an item page: where its crew is now, as five steps. */
export function CrewStatusPanel({ id }: { id: string }) {
  const s = useCrewStatus(id)
  const { label } = useSimClock()
  if (!s) return null
  const crew = DB.crews.find((c) => c.id === s.crew)
  const at = s.phase === "incheiata" ? ORDER.length : ORDER.indexOf(s.phase)
  return (
    <section aria-label="Statusul echipajului" className="rounded-2xl bg-surface p-5 md:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className="grid size-12 place-items-center rounded-2xl bg-foreground/[0.06]">
            <PhaseIcon phase={s.phase} className="size-6" />
          </span>
          <div>
            <div className="text-xl font-semibold">
              <span className={PHASE_TONE[s.phase]}>{PHASE_RO[s.phase]}</span>, echipa {s.crew}
            </div>
            <div className="text-foreground/75">{s.note}</div>
          </div>
        </div>
        <div className="tabular text-right text-sm text-foreground/60">
          <div>Ora {label}, simulare pe tura de mâine</div>
          {s.seq > 0 && (
            <div>
              Oprirea {s.seq} din {s.stops}
              {crew ? `, baza ${crew.depotRo}` : ""}
            </div>
          )}
        </div>
      </div>
      <ol className="mt-5 grid grid-cols-5 gap-2" aria-label="Etapele echipajului la această lucrare">
        {ORDER.map((p, i) => {
          const done = i < at
          const on = i === at
          return (
            <li key={p} aria-current={on ? "step" : undefined}>
              <span className={cn("block h-1.5 rounded-full", done ? "bg-foreground/45" : on ? "bg-amber" : "bg-foreground/10")} />
              <span className={cn("mt-2 flex items-center gap-1.5 text-sm", on ? "font-medium text-foreground" : done ? "text-foreground/60" : "text-foreground/40")}>
                <PhaseIcon phase={p} className={cn("size-4", !on && "text-current [animation:none]")} />
                {PHASE_RO[p]}
              </span>
            </li>
          )
        })}
      </ol>
    </section>
  )
}
