import { DB, DECISION_RO, type Decision } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

/** The human branch sits in the middle, where the eye lands. */
const ORDER: Decision[] = ["remote_action", "deferred", "human_review", "assigned", "notify"]

const W = 640
const H = 400
const SRC_X = 40
const SRC_TOP = 64
const SRC_H = 280
const END_X = 372
const MIN_W = 7
/** the widest a band may be where it reaches its decision */
const END_W = 26

/**
 * The jobs stream out of one source and split into the agent's five
 * decisions; the band's width is the share of jobs. The branch that goes
 * to a person is the one in amber.
 */
export function DecideFlow() {
  const counts = ORDER.map((d) => DB.decisionCounts[d] ?? 0)
  const total = counts.reduce((a, b) => a + b, 0) || 1
  const widths = counts.map((n) => Math.max(MIN_W, (n / total) * SRC_H))
  const scale = SRC_H / widths.reduce((a, b) => a + b, 0)
  let y = SRC_TOP
  const lanes = ORDER.map((d, i) => {
    const w = widths[i] * scale
    const ys = y + w / 2
    y += w
    const yt = SRC_TOP + (i * SRC_H) / (ORDER.length - 1)
    const path = `M ${SRC_X} ${ys} C ${SRC_X + 170} ${ys}, ${END_X - 170} ${yt}, ${END_X} ${yt}`
    // the band narrows into its decision, so wide bands never cover their neighbours
    const tw = Math.min(w, END_W)
    const band =
      `M ${SRC_X} ${ys - w / 2} C ${SRC_X + 170} ${ys - w / 2}, ${END_X - 170} ${yt - tw / 2}, ${END_X} ${yt - tw / 2} ` +
      `L ${END_X} ${yt + tw / 2} C ${END_X - 170} ${yt + tw / 2}, ${SRC_X + 170} ${ys + w / 2}, ${SRC_X} ${ys + w / 2} Z`
    const human = d === "human_review"
    const dots = Math.max(2, Math.round((counts[i] / total) * 16))
    return { d, n: counts[i], w, tw, ys, yt, path, band, human, dots }
  })

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="h-full w-full" role="img" aria-label="Cum împarte agentul lucrările pe decizii">
      <text x={SRC_X - 16} y={SRC_TOP - 22} className="fill-white text-[17px] font-semibold">
        {fmt(DB.summary.items_in)} lucrări
      </text>
      <rect x={SRC_X - 16} y={SRC_TOP} width={16} height={SRC_H} rx={4} className="fill-white/85" />

      {lanes.map((l) => (
        <path key={l.d} d={l.band} className={l.human ? "fill-amber/50" : "fill-white/[0.09]"} />
      ))}

      {lanes.map((l) =>
        Array.from({ length: l.dots }, (_, k) => (
          <circle key={`${l.d}-${k}`} r={l.human ? 5 : 3} className={l.human ? "fill-amber" : "fill-white/70"} opacity={0}>
            <animateMotion dur={l.human ? "2.2s" : "2.6s"} begin={`${(k * (l.human ? 2.2 : 2.6)) / l.dots}s`} repeatCount="indefinite" path={l.path} />
            <animate
              attributeName="opacity"
              values="0;1;1;0"
              keyTimes="0;0.12;0.85;1"
              dur={l.human ? "2.2s" : "2.6s"}
              begin={`${(k * (l.human ? 2.2 : 2.6)) / l.dots}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))
      )}

      {lanes.map((l) => (
        <g key={`${l.d}-label`}>
          <rect x={END_X} y={l.yt - Math.max(l.tw, 12) / 2} width={6} height={Math.max(l.tw, 12)} rx={3} className={l.human ? "fill-amber" : "fill-white/60"} />
          <text x={END_X + 22} y={l.yt + 6} className={l.human ? "fill-amber text-[19px] font-semibold" : "fill-white/85 text-[17px]"}>
            {DECISION_RO[l.d]}
          </text>
          <text x={W - 8} y={l.yt + 6} textAnchor="end" className={l.human ? "fill-amber text-[19px] font-semibold" : "fill-white/70 text-[17px]"} style={{ fontVariantNumeric: "tabular-nums" }}>
            {fmt(l.n)}
          </text>
        </g>
      ))}
    </svg>
  )
}
