import { useEffect, useState } from "react"
import { DB } from "@/data/daybreak"

/**
 * Where a crew is relative to one work item, on tomorrow's shift.
 * The plan only has arrival times, so the phases are simulated from them:
 * the crew travels, diagnoses, works, wraps up and leaves each stop.
 */
export type CrewPhase = "programata" | "tranzit" | "diagnosticare" | "lucru" | "finalizare" | "retragere" | "incheiata"

export const PHASE_RO: Record<CrewPhase, string> = {
  programata: "Scheduled",
  tranzit: "In transit",
  diagnosticare: "Diagnosing",
  lucru: "Working",
  finalizare: "Finishing",
  retragere: "Leaving",
  incheiata: "Completed",
}

export interface CrewStatus {
  crew: string
  phase: CrewPhase
  /** 1-based position of this item in the crew's route */
  seq: number
  stops: number
  arrive: string
  leave: string
  /** what the phase means, in one short sentence */
  note: string
}

const toMin = (t: string) => {
  const [h, m] = t.split(":").map(Number)
  return h * 60 + m
}
const hhmm = (m: number) => `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(Math.round(m) % 60).padStart(2, "0")}`
/** travel time for a leg, at about 35 km/h in town, never under 5 minutes */
const travel = (km: number) => Math.max(5, Math.round((km / 35) * 60))

const SHIFT_START = toMin(DB.shift.start)
const SHIFT_END = toMin(DB.shift.end)

interface Window {
  crew: string
  seq: number
  stops: number
  depart: number
  /** when the crew can leave for this stop: the previous stop's end, or the depart time */
  setOff: number
  arrive: number
  leave: number
  /** when the crew is clear of the site: next arrival, or back at the depot */
  clear: number
  last: boolean
}

const WINDOWS = new Map<string, Window>()
for (const r of DB.routes) {
  const stops = DB.routeStops.filter((s) => s.crew === r.crew).sort((a, b) => a.seq - b.seq)
  const depart = toMin(r.depart)
  const back = r.back ? toMin(r.back) : SHIFT_END + 60
  stops.forEach((s, i) => {
    const arrive = toMin(s.eta)
    const next = stops[i + 1]
    const leave = next ? toMin(next.eta) - travel(next.km) : r.back ? back - 15 : back
    const prev = i > 0 ? WINDOWS.get(stops[i - 1].id) : undefined
    WINDOWS.set(s.id, {
      crew: r.crew,
      seq: s.seq,
      stops: stops.length,
      depart,
      setOff: prev ? prev.leave : depart,
      arrive,
      leave: Math.max(arrive + 5, leave),
      clear: next ? toMin(next.eta) : back,
      last: !next,
    })
  })
}

export function statusAt(id: string, now: number): CrewStatus | null {
  const w = WINDOWS.get(id)
  if (!w) return null
  const dur = w.leave - w.arrive
  const diagEnd = w.arrive + Math.max(5, Math.round(dur * 0.25))
  const finStart = w.leave - Math.max(5, Math.round(dur * 0.15))
  let phase: CrewPhase
  let note: string
  if (now < w.setOff) {
    phase = "programata"
    note = w.seq === 1 ? `Crew leaves the depot at ${hhmm(w.depart)}.` : `Crew is at an earlier job; expected arrival ${hhmm(w.arrive)}.`
  } else if (now < w.arrive) {
    phase = "tranzit"
    note = `Travelling; expected arrival ${hhmm(w.arrive)}.`
  } else if (now < diagEnd) {
    phase = "diagnosticare"
    note = `Arrived at ${hhmm(w.arrive)} and is investigating the cause.`
  } else if (now < finStart) {
    phase = "lucru"
    note = `Working; expected finish ${hhmm(w.leave)}.`
  } else if (now < w.leave) {
    phase = "finalizare"
    note = `Checks and closes the job by ${hhmm(w.leave)}.`
  } else if (now < w.clear) {
    phase = "retragere"
    note = w.last ? "Returning to the depot." : "Travelling to the next stop."
  } else {
    phase = "incheiata"
    note = `Job closed at ${hhmm(w.leave)}.`
  }
  return { crew: w.crew, phase, seq: w.seq, stops: w.stops, arrive: hhmm(w.arrive), leave: hhmm(w.leave), note }
}

/**
 * The simulated clock: today's time of day laid over tomorrow's shift, so the
 * statuses move during a demo. Outside the shift it wraps around inside it.
 */
function simNow() {
  const d = new Date()
  const m = d.getHours() * 60 + d.getMinutes()
  const len = SHIFT_END + 60 - SHIFT_START
  return m >= SHIFT_START && m < SHIFT_START + len ? m : SHIFT_START + (((m - SHIFT_START) % len) + len) % len
}

export function useSimClock() {
  const [now, setNow] = useState(simNow)
  useEffect(() => {
    const t = window.setInterval(() => setNow(simNow()), 20_000)
    return () => window.clearInterval(t)
  }, [])
  return { now, label: hhmm(now) }
}

export const SHIFT = { start: SHIFT_START, end: SHIFT_END }
export { hhmm }

/** One crew's day: when it leaves, when it is back, and its time on site at each stop. */
export function crewDay(crew: string) {
  const r = DB.routes.find((x) => x.crew === crew)!
  const stops = DB.routeStops
    .filter((s) => s.crew === crew)
    .sort((a, b) => a.seq - b.seq)
    .map((s) => WINDOWS.get(s.id)!)
    .map((w) => ({ arrive: w.arrive, leave: Math.min(w.leave, r.back ? toMin(r.back) : SHIFT_END) }))
  return { depart: toMin(r.depart), back: r.back ? toMin(r.back) : SHIFT_END, open: !r.back, stops }
}
