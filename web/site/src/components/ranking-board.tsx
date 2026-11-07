import { Clock, Loader2, Users, X } from "lucide-react"
import { animate, motion, useMotionValue, useTransform } from "motion/react"
import { useEffect } from "react"
import { Link } from "react-router-dom"
import { SourceIcon } from "@/components/ui/animated-icons"
import { DB, SOURCES, type QueueRow } from "@/data/daybreak"
import { useApprovals, type Verdict } from "@/lib/approvals"
import { cn, fmt, lei } from "@/lib/utils"

/** All the cases the agent was not sure about and sent to a person. */
export const QUEUE: QueueRow[] = DB.items
  .filter((i) => i.decision === "human_review")
  .sort((a, b) => b.impact.expectedValueLei - a.impact.expectedValueLei)
  .map((i) => ({
    id: i.id,
    source: i.source,
    label: i.label,
    score: i.prediction.score ?? 0,
    low: i.prediction.low,
    high: i.prediction.high,
    reason: i.reason,
    expectedValueLei: i.impact.expectedValueLei,
  }))
export const QUEUE_TOTAL = QUEUE.reduce((s, q) => s + q.expectedValueLei, 0)

function Counter({ value }: { value: number }) {
  const mv = useMotionValue(value)
  const text = useTransform(mv, (v) => fmt(v))
  useEffect(() => {
    const c = animate(mv, value, { duration: 0.6, ease: [0.22, 1, 0.36, 1] })
    return c.stop
  }, [mv, value])
  return <motion.span className="tabular">{text}</motion.span>
}

export function useApprovedValue() {
  const { approved } = useApprovals()
  return QUEUE.filter((q) => approved.has(q.id)).reduce((s, q) => s + q.expectedValueLei, 0)
}

/** The source's icon in its colour, plus its name. */
export function SourceTag({ s }: { s: keyof typeof SOURCES }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-white/85">
      <SourceIcon s={s} size={20} accent={SOURCES[s].color} className="shrink-0 text-white/75" />
      {SOURCES[s].name}
    </span>
  )
}

/** Value approved by a person, and where the queue stands. */
export function ApprovedCounter() {
  const { approved, deferred, rejected, persisted, status } = useApprovals()
  const total = useApprovedValue()
  const yes = QUEUE.filter((q) => approved.has(q.id)).length
  const later = QUEUE.filter((q) => deferred.has(q.id)).length
  const no = QUEUE.filter((q) => rejected.has(q.id)).length
  return (
    <div className="rounded-2xl bg-surface p-[clamp(20px,2.4vw,32px)]">
      <div className="text-[clamp(2.4rem,min(4.6vw,7.5vh),4.2rem)] leading-none font-semibold tracking-[-0.03em]">
        {status === "loading" ? (
          <span className="inline-block h-[0.9em] w-48 animate-pulse rounded-2xl bg-white/10 align-middle" aria-label="Se încarcă" />
        ) : (
          <>
            <Counter value={total} /> <span className="text-[0.45em]">lei</span>
          </>
        )}
      </div>
      <p className="mt-2 text-white/80">valoare așteptată, aprobată de tine</p>
      <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className="h-full rounded-full bg-ember"
          animate={{ width: `${(total / QUEUE_TOTAL) * 100}%` }}
          transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      <p className="tabular mt-3 text-sm text-white/70">
        {yes} aprobate, {later} amânate, {no} respinse, {QUEUE.length - yes - later - no} așteaptă
      </p>
      <p className="mt-4 text-sm text-white/60">{persisted ? "Deciziile se salvează în contul tău." : "Intră în cont ca să păstrezi deciziile."}</p>
    </div>
  )
}

const VERDICTS = [
  { v: "approved", label: "Echipaj", done: "Echipaj", icon: Users, on: "bg-ok text-black", text: "text-ok" },
  { v: "deferred", label: "Amână", done: "Amânat", icon: Clock, on: "bg-amber text-black", text: "text-amber" },
  { v: "rejected", label: "Respinge", done: "Respins", icon: X, on: "bg-magenta text-black", text: "text-magenta" },
] as const

export const VERDICT_TEXT: Record<Verdict, { done: string; text: string }> = {
  approved: { done: "Aprobat", text: "text-ok" },
  deferred: { done: "Amânat", text: "text-amber" },
  rejected: { done: "Respins", text: "text-magenta" },
}

/** Approve, postpone or reject one case. Choosing the current verdict again takes it back. */
export function VerdictButtons({ id, label, size = "sm" }: { id: string; label: string; size?: "sm" | "lg" }) {
  const { decisions, decide, saving, status } = useApprovals()
  const current = decisions.get(id)
  const busy = saving === id || saving === "*" || status === "loading"
  return (
    <div className={cn("flex shrink-0", size === "lg" ? "flex-wrap gap-3" : "gap-2")}>
      {VERDICTS.map(({ v, label: verb, done, icon: Icon, on }) => {
        const active = current === v
        return (
          <button
            key={v}
            type="button"
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              decide(id, v)
            }}
            disabled={busy}
            aria-pressed={active}
            aria-label={size === "lg" ? undefined : active ? `Retrage: ${done.toLowerCase()}, ${label}` : `${verb}: ${label}`}
            title={verb}
            className={cn(
              "inline-flex cursor-pointer items-center justify-center gap-2 rounded-full transition-[background-color,transform] duration-150 active:scale-90 disabled:cursor-wait disabled:opacity-60",
              size === "lg" ? "h-12 px-6 font-semibold" : "size-11",
              active ? on : "bg-white/[0.08] text-white/80 hover:bg-white/15 hover:text-white"
            )}
          >
            {busy && active ? <Loader2 className="size-5 animate-spin" aria-hidden /> : <Icon className="size-5" aria-hidden />}
            {size === "lg" && (active ? done : verb)}
          </button>
        )
      })}
    </div>
  )
}

/** One case in the queue, as drawn: icon, place and value on top; the three choices and the risk below. */
export function QueueCard({ q, selected, to, onSelect }: { q: QueueRow; selected?: boolean; to?: string; onSelect?: () => void }) {
  const { decisions, crews } = useApprovals()
  const v = decisions.get(q.id)
  const crew = crews.get(q.id)
  const body = (
    <div className="flex items-start gap-3">
      <span
        className="grid size-14 shrink-0 place-items-center rounded-xl bg-white/[0.05]"
        title={SOURCES[q.source].name}
      >
        <SourceIcon s={q.source} size={34} accent={SOURCES[q.source].color} className="text-white/80" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-medium leading-snug">{q.label}</span>
        {v ? (
          <span className={cn("mt-0.5 block text-sm font-medium", VERDICT_TEXT[v].text)}>
            {VERDICT_TEXT[v].done}
            {v === "approved" && crew ? `, ${crew}` : ""}
          </span>
        ) : (
          <span className="mt-0.5 block text-sm text-white/55">{SOURCES[q.source].name}</span>
        )}
      </span>
      <span className="tabular shrink-0 text-right text-xl font-semibold">{lei(q.expectedValueLei)}</span>
    </div>
  )
  return (
    <div
      className={cn(
        "rounded-2xl p-3.5 transition-[background-color,box-shadow,opacity] duration-200",
        selected ? "bg-surface-2 ring-2 ring-[rgb(24,65,232)] ring-inset" : "bg-surface hover:bg-surface-2",
        v === "rejected" && !selected && "opacity-60"
      )}
    >
      {to ? (
        <Link to={to} onClick={onSelect} className="block" aria-current={selected ? "true" : undefined}>
          {body}
        </Link>
      ) : (
        <button type="button" onClick={onSelect} className="block w-full cursor-pointer text-left" aria-pressed={selected}>
          {body}
        </button>
      )}
      <div className="mt-3 flex items-center justify-between gap-3">
        <VerdictButtons id={q.id} label={q.label} />
        <span className="tabular text-lg font-medium text-white/85">Risc {fmt(q.score * 100)}%</span>
      </div>
    </div>
  )
}

/** The queue as cards; each opens its case. Used on the landing page and the plan page. */
export function QueueTable({ limit }: { limit?: number; showReason?: boolean }) {
  const { error, status, retry } = useApprovals()
  const rows = limit ? QUEUE.slice(0, limit) : QUEUE

  if (status === "error") {
    return (
      <div className="rounded-2xl bg-surface p-6" role="alert">
        <p className="font-medium">{error}</p>
        <button type="button" onClick={retry} className="mt-3 cursor-pointer underline underline-offset-4 hover:text-ember-soft">
          Încearcă din nou
        </button>
      </div>
    )
  }
  if (rows.length === 0) {
    return (
      <div className="rounded-2xl bg-surface p-6">
        <p className="font-medium">Agentul a decis singur tot planul de mâine.</p>
        <p className="mt-1 text-white/75">Nimic nu așteaptă un om.</p>
      </div>
    )
  }
  return (
    <div>
      <ul className="grid gap-2 md:grid-cols-2" aria-label="Cazuri care așteaptă un om">
        {rows.map((q) => (
          <li key={q.id}>
            <QueueCard q={q} to={`/app/coada/${q.id}`} />
          </li>
        ))}
      </ul>
      {error && (
        <p className="mt-3 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
