import { Check, Loader2 } from "lucide-react"
import { DB, SKILL_RO, type Crew, type Item } from "@/data/daybreak"
import { useApprovals } from "@/lib/approvals"
import { cn, fmt } from "@/lib/utils"

const ROUTE = new Map(DB.routes.map((r) => [r.crew, r]))

/** Where each base is (city centres, enough for a distance). */
const DEPOT_AT: Record<string, [number, number]> = {
  "D-BUC-V": [44.43, 26.0],
  "D-BUC-E": [44.43, 26.17],
  "D-CTA": [44.17, 28.63],
  "D-TM": [45.75, 21.23],
  "D-ARD": [46.18, 21.31],
  "D-RES": [45.3, 21.89],
  "D-DEV": [45.88, 22.9],
}

/** Straight-line distance in km. */
function km([a, b]: [number, number], [c, d]: [number, number]) {
  const r = Math.PI / 180
  const x = (d - b) * r * Math.cos(((a + c) / 2) * r)
  const y = (c - a) * r
  return Math.sqrt(x * x + y * y) * 6371
}

/** What a crew is doing tomorrow, from the agent's plan. */
export function crewStatus(c: Crew) {
  const r = ROUTE.get(c.id)
  if (!r) return { busy: false, text: `Liber toată tura (${DB.shift.start}–${DB.shift.end})` }
  const stops = r.stops === 1 ? "1 oprire" : `${r.stops} opriri`
  return {
    busy: true,
    text: r.back ? `Ocupat ${r.depart}–${r.back}, ${stops}, ${fmt(r.km, 1)} km` : `În zonă de la ${r.depart}, ${stops}`,
  }
}

/**
 * After a person approves a case, they pick who goes. Every crew is listed with
 * its base, its skills and what it already does tomorrow; crews that have the
 * skill the work needs come first, free ones before busy ones.
 */
export function CrewPicker({ item }: { item: Item }) {
  const { crews: assigned, assign, saving } = useApprovals()
  const need = item.effort?.crew_skill
  const chosen = assigned.get(item.id)
  const extra = new Map<string, number>()
  assigned.forEach((crew, id) => id !== item.id && extra.set(crew, (extra.get(crew) ?? 0) + 1))

  const rows = DB.crews
    .map((c) => ({
      c,
      s: crewStatus(c),
      fits: !need || c.skills.includes(need),
      dist: DEPOT_AT[c.depot] ? km(DEPOT_AT[c.depot], [item.lat, item.lng]) : 9999,
    }))
    // the right skill first, then the closest base (in 60 km bands), then free before busy
    .sort(
      (a, b) =>
        Number(b.fits) - Number(a.fits) ||
        Math.floor(a.dist / 60) - Math.floor(b.dist / 60) ||
        Number(a.s.busy) - Number(b.s.busy) ||
        a.dist - b.dist
    )
  const recommended = rows.find((r) => r.fits)?.c.id

  return (
    <div className="mt-6">
      <h3 className="font-sans text-base font-semibold">Alege echipajul</h3>
      {need && <p className="mt-1 text-sm text-white/65">Lucrarea cere {SKILL_RO[need] ?? need}.</p>}
      <ul role="radiogroup" aria-label="Echipaje" className="mt-3 grid gap-2 sm:grid-cols-2 2xl:grid-cols-3">
        {rows.map(({ c, s, fits, dist }) => {
          const on = chosen === c.id
          const mine = extra.get(c.id) ?? 0
          return (
            <li key={c.id}>
              <button
                type="button"
                role="radio"
                aria-checked={on}
                disabled={saving === item.id}
                onClick={() => assign(item.id, c.id)}
                className={cn(
                  "relative w-full cursor-pointer rounded-2xl p-3.5 text-left transition-[background-color,box-shadow,opacity] duration-150 disabled:cursor-wait",
                  on ? "bg-surface-2 ring-2 ring-[rgb(24,65,232)] ring-inset" : "bg-white/[0.04] hover:bg-white/[0.08]",
                  !fits && !on && "opacity-55"
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold">{c.id}</span>
                  {on ? (
                    <span className="inline-flex items-center gap-1 text-sm font-medium text-[rgb(110,150,255)]">
                      {saving === item.id ? <Loader2 className="size-4 animate-spin" aria-hidden /> : <Check className="size-4" aria-hidden />}
                      Alocat
                    </span>
                  ) : c.id === recommended ? (
                    <span className="text-sm font-medium text-amber">Recomandat</span>
                  ) : null}
                </div>
                <div className="mt-0.5 text-sm text-white/70">
                  {c.depotRo}, la ~{fmt(dist)} km, {c.size} oameni, {c.skills.map((k) => SKILL_RO[k] ?? k).join(" și ")}
                </div>
                <div className="mt-2 flex items-center gap-2 text-sm">
                  <span className={cn("size-2 shrink-0 rounded-full", s.busy ? "bg-amber" : "bg-ok")} aria-hidden />
                  <span className="text-white/85">{s.text}</span>
                </div>
                {mine > 0 && <div className="mt-1 text-sm text-white/60">+{mine} alocate de tine</div>}
                {!fits && <div className="mt-1 text-sm text-white/55">Nu are {SKILL_RO[need!] ?? need}</div>}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
