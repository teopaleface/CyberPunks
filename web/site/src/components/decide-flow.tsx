import { DB, DECISION_RO, type Decision } from "@/data/daybreak"
import { useReduced } from "@/lib/motion"
import { fmt } from "@/lib/utils"

/** The human branch sits in the middle, where the eye lands. */
const ORDER: Decision[] = ["remote_action", "deferred", "human_review", "assigned", "notify"]

const W = 390
const H = 400
const SRC_X = 40
const SRC_TOP = 40
const SRC_H = 320
const END_X = 372
/** the widest a band may be where it reaches its decision */
const END_W = 26

/**
 * The jobs stream out of one source and split into the agent's five
 * decisions; the band's width is the share of jobs. The branch that goes
 * to a person is the one in amber.
 */
export function DecideFlow() {
  const reduce = useReduced()
  const counts = ORDER.map((d) => DB.decisionCounts[d] ?? 0)
  const total = counts.reduce((a, b) => a + b, 0)
  const widths = counts.map((n) => (n / (total || 1)) * SRC_H)
  const scale = widths.some(Boolean) ? SRC_H / widths.reduce((a, b) => a + b, 0) : 1
  const lanes = ORDER.map((d, i) => {
    const w = widths[i] * scale
    const ys = SRC_TOP + widths.slice(0, i).reduce((sum, width) => sum + width * scale, 0) + w / 2
    const yt = SRC_TOP + (i * SRC_H) / (ORDER.length - 1)
    const path = `M ${SRC_X} ${ys} C ${SRC_X + 170} ${ys}, ${END_X - 170} ${yt}, ${END_X} ${yt}`
    // the band narrows into its decision, so wide bands never cover their neighbours
    const tw = Math.min(w, END_W)
    const band =
      `M ${SRC_X} ${ys - w / 2} C ${SRC_X + 170} ${ys - w / 2}, ${END_X - 170} ${yt - tw / 2}, ${END_X} ${yt - tw / 2} ` +
      `L ${END_X} ${yt + tw / 2} C ${END_X - 170} ${yt + tw / 2}, ${SRC_X + 170} ${ys + w / 2}, ${SRC_X} ${ys + w / 2} Z`
    const human = d === "human_review"
    const dots = counts[i] ? Math.max(2, Math.round((counts[i] / total) * 16)) : 0
    return { d, n: counts[i], w, tw, ys, yt, path, band, human, dots }
  })

  return (
    <div data-decision-flow>
      <p className="mb-4 text-sm font-medium text-foreground/80">{fmt(total)} jobs, grouped by decision</p>
      <div className="grid grid-cols-[minmax(56px,0.7fr)_minmax(0,1fr)] items-center gap-4">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="h-[300px] w-full" aria-hidden>
          <rect x={SRC_X - 16} y={SRC_TOP} width={16} height={SRC_H} rx={4} className="fill-foreground/85" />
          {lanes.map((l) => <path key={l.d} d={l.band} className={l.human ? "fill-amber/50" : "fill-foreground/[0.12]"} />)}
          {!reduce && lanes.map((l) => Array.from({ length: l.dots }, (_, k) => (
            <circle key={`${l.d}-${k}`} r={l.human ? 5 : 3} className={l.human ? "fill-amber" : "fill-foreground/70"} opacity={0}>
              <animateMotion dur="2.6s" begin={`${(k * 2.6) / l.dots}s`} repeatCount="indefinite" path={l.path} />
              <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.12;0.85;1" dur="2.6s" begin={`${(k * 2.6) / l.dots}s`} repeatCount="indefinite" />
            </circle>
          )))}
          {lanes.map((l) => (
            <rect key={`${l.d}-end`} x={END_X} y={l.yt - Math.max(l.tw, 12) / 2} width={6} height={Math.max(l.tw, 12)} rx={3} className={l.human ? "fill-amber" : "fill-foreground/60"} />
          ))}
        </svg>
        <ul aria-label="Agent decisions" className="grid h-[300px] grid-rows-5">
          {lanes.map((l) => (
            <li key={l.d} className={`flex items-center justify-between gap-2 text-sm sm:text-base ${l.human ? "font-semibold text-accent-ink" : "text-foreground/85"}`}>
              <span>{DECISION_RO[l.d]}</span><span className="tabular shrink-0">{fmt(l.n)}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
