import { AnimatePresence, motion } from "motion/react"
import { useEffect, useId, useMemo, useRef, useState } from "react"
import { SOURCES, type Series, type SourceKey } from "@/data/daybreak"
import { fmt } from "@/lib/utils"

const THRESHOLD_RO: Record<string, string> = {
  limita_tensiune_pu: "limita de tensiune",
  limita_calitate_95_pu: "limita de calitate (95%)",
  rafala_inceput_furtuna_kmh: "începe furtuna",
  rafala_periculoasa_kmh: "rafală periculoasă",
}

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [w, setW] = useState(640)
  useEffect(() => {
    if (!ref.current) return
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width))
    ro.observe(ref.current)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

const label = (t: string, hourly: boolean) => {
  const d = new Date(t)
  return hourly
    ? `${String(d.getHours()).padStart(2, "0")}:00`
    : new Intl.DateTimeFormat("ro-RO", { day: "numeric", month: "short" }).format(d)
}

/**
 * One series from the agent's run: the model's band (P10–P90) as a soft
 * field, the expected value dashed, the measured value as the line, the
 * thresholds that matter and the moments the agent marked.
 */
export function SeriesChart({ series, source, height = 260 }: { series: Series; source: SourceKey; height?: number }) {
  const [ref, width] = useWidth<HTMLDivElement>()
  const gid = useId().replace(/:/g, "")
  const [hover, setHover] = useState<number | null>(null)
  const color = SOURCES[source].color
  const pad = { l: 44, r: 12, t: 14, b: 26 }
  const pts = series.points
  const hourly = pts.length > 1 && new Date(pts[1][0]).getTime() - new Date(pts[0][0]).getTime() < 86_400_000

  const g = useMemo(() => {
    const vals = pts.flatMap((p) => [p[1], p[2], p[3], p[4]]).filter((v): v is number => v !== null)
    const th = Object.values(series.thresholds)
    let min = Math.min(...vals, ...th),
      max = Math.max(...vals, ...th)
    const span = max - min || 1
    min -= span * 0.08
    max += span * 0.08
    const x = (i: number) => pad.l + (i / Math.max(1, pts.length - 1)) * (width - pad.l - pad.r)
    const y = (v: number) => pad.t + (1 - (v - min) / (max - min)) * (height - pad.t - pad.b)
    const path = (k: 1 | 2) => {
      let d = ""
      let pen = false
      pts.forEach((p, i) => {
        const v = p[k]
        if (v === null) {
          pen = false
          return
        }
        d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`
        pen = true
      })
      return d
    }
    const banded = pts.map((p, i) => [i, p[3], p[4]] as const).filter((b) => b[1] !== null && b[2] !== null)
    const band = banded.length
      ? banded.map(([i, , hi], j) => `${j ? "L" : "M"}${x(i).toFixed(1)},${y(hi as number).toFixed(1)}`).join("") +
        [...banded].reverse().map(([i, lo]) => `L${x(i).toFixed(1)},${y(lo as number).toFixed(1)}`).join("") +
        "Z"
      : ""
    const ticks = Array.from({ length: 4 }, (_, k) => min + ((max - min) * (k + 0.5)) / 4)
    return { x, y, value: path(1), expected: path(2), band, ticks }
  }, [pts, series.thresholds, width, height, pad.l, pad.r, pad.t, pad.b])

  const onMove = (e: React.PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const rel = (e.clientX - rect.left - pad.l) / (rect.width - pad.l - pad.r)
    setHover(Math.max(0, Math.min(pts.length - 1, Math.round(rel * (pts.length - 1)))))
  }

  const h = hover !== null ? pts[hover] : null
  const digits = series.unit === "pu" ? 3 : 1
  const xTicks = [0, Math.floor((pts.length - 1) / 3), Math.floor(((pts.length - 1) * 2) / 3), pts.length - 1]
  const annIdx = series.annotations.map((a) => ({ ...a, i: pts.findIndex((p) => p[0] === a.t) })).filter((a) => a.i >= 0)

  return (
    <figure>
      <figcaption className="mb-3 flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
        <span className="font-medium">{series.title}</span>
        <span className="flex flex-wrap gap-x-4 text-sm text-foreground/70">
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 rounded-full" style={{ background: color }} aria-hidden /> măsurat
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-4 border-t border-dashed border-foreground/70" aria-hidden /> așteptat
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-4 rounded-[3px]" style={{ background: `${color}40` }} aria-hidden /> interval P10–P90
          </span>
        </span>
      </figcaption>
      <div ref={ref} className="relative">
        <svg
          width={width}
          height={height}
          className="block touch-none"
          onPointerMove={onMove}
          onPointerLeave={() => setHover(null)}
          role="img"
          aria-label={series.title}
        >
          <defs>
            <linearGradient id={`band-${gid}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.38" />
              <stop offset="100%" stopColor={color} stopOpacity="0.08" />
            </linearGradient>
            <linearGradient id={`line-${gid}`} x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor={color} stopOpacity="0.55" />
              <stop offset="100%" stopColor={color} stopOpacity="1" />
            </linearGradient>
          </defs>
          {g.ticks.map((t) => (
            <g key={t}>
              <line x1={pad.l} x2={width - pad.r} y1={g.y(t)} y2={g.y(t)} stroke="rgba(255,255,255,.06)" />
              <text x={pad.l - 8} y={g.y(t) + 4} textAnchor="end" fontSize={11} fill="rgba(255,255,255,.55)">
                {fmt(t, digits)}
              </text>
            </g>
          ))}
          {g.band && <motion.path initial={false} animate={{ d: g.band }} transition={{ duration: 0.3 }} fill={`url(#band-${gid})`} />}
          {Object.entries(series.thresholds).map(([k, v]) => (
            <g key={k}>
              <line x1={pad.l} x2={width - pad.r} y1={g.y(v)} y2={g.y(v)} stroke="var(--ember)" strokeOpacity={0.75} strokeDasharray="6 5" />
              <text x={width - pad.r - 4} y={g.y(v) - 6} textAnchor="end" fontSize={11} fill="var(--ember-soft)">
                {THRESHOLD_RO[k] ?? k} {fmt(v, digits)}
              </text>
            </g>
          ))}
          {annIdx.map((a) => (
            <line key={a.t} x1={g.x(a.i)} x2={g.x(a.i)} y1={pad.t} y2={height - pad.b} stroke="rgba(255,255,255,.35)" strokeDasharray="2 4" />
          ))}
          {g.expected && <path d={g.expected} fill="none" stroke="rgba(255,255,255,.65)" strokeWidth={1.5} strokeDasharray="4 5" />}
          {g.value && (
            <motion.path
              d={g.value}
              fill="none"
              stroke={`url(#line-${gid})`}
              strokeWidth={2.5}
              strokeLinejoin="round"
              initial={{ pathLength: 0 }}
              whileInView={{ pathLength: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            />
          )}
          {xTicks.map((i) => (
            <text
              key={i}
              x={g.x(i)}
              y={height - 6}
              fontSize={11}
              fill="rgba(255,255,255,.55)"
              textAnchor={i === 0 ? "start" : i === pts.length - 1 ? "end" : "middle"}
            >
              {label(pts[i][0], hourly)}
            </text>
          ))}
          {h && hover !== null && (
            <g>
              <line x1={g.x(hover)} x2={g.x(hover)} y1={pad.t} y2={height - pad.b} stroke="rgba(255,255,255,.3)" />
              {h[1] !== null && <circle cx={g.x(hover)} cy={g.y(h[1])} r={4.5} fill={color} stroke="#000" strokeWidth={1.5} />}
              {h[2] !== null && <circle cx={g.x(hover)} cy={g.y(h[2])} r={3.5} fill="#fff" />}
            </g>
          )}
        </svg>
        <AnimatePresence>
          {h && hover !== null && (
            <motion.div
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="pointer-events-none absolute top-1 z-10 w-52 rounded-2xl bg-surface-2 p-3 text-sm shadow-[0_12px_40px_-8px_rgba(0,0,0,.9)]"
              style={{ left: Math.min(Math.max(g.x(hover) - 104, 0), width - 208) }}
            >
              <div className="mb-1 font-medium">{label(h[0], hourly)}</div>
              {h[1] !== null && (
                <div className="tabular flex justify-between">
                  <span className="text-foreground/75">Măsurat</span>
                  <span>
                    {fmt(h[1], digits)} {series.unit}
                  </span>
                </div>
              )}
              {h[2] !== null && (
                <div className="tabular flex justify-between">
                  <span className="text-foreground/75">Așteptat</span>
                  <span>
                    {fmt(h[2], digits)} {series.unit}
                  </span>
                </div>
              )}
              {h[3] !== null && h[4] !== null && (
                <div className="tabular flex justify-between text-foreground/70">
                  <span>Interval</span>
                  <span>
                    {fmt(h[3], digits)}–{fmt(h[4], digits)}
                  </span>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {annIdx.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm text-foreground/70">
          {annIdx.map((a) => (
            <li key={a.t}>
              {label(a.t, hourly)}: {a.label}
            </li>
          ))}
        </ul>
      )}
    </figure>
  )
}
