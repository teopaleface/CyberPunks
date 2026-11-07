import { cn } from "@/lib/utils"
import { useReduced } from "@/lib/motion"
import type { SourceKey } from "@/data/daybreak"

/**
 * Small animated icons for the three sources, in the spirit of
 * 21st.dev/@dev.yadhakim/animated-weather-icons: each one is a tiny scene.
 * A: a meter whose needle sweeps; B: a storm cloud with falling rain and a
 * lightning flash; C: a sun whose rays turn, over a solar panel.
 * Drawn on a 48 grid. The moves are CSS keyframes (index.css, `ic-*`) with
 * `transform-box: view-box`, so every part turns around its own point.
 */

interface IconProps {
  size?: number
  accent?: string
  className?: string
}

function useStill() {
  return useReduced() ? "ic-still" : ""
}

export function MeterIcon({ size = 40, accent = "currentColor", className }: IconProps) {
  const still = useStill()
  return (
    <svg viewBox="0 0 48 48" width={size} height={size} className={cn(still, className)} aria-hidden fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round">
      <rect x="7" y="9" width="34" height="30" rx="6" />
      <path d="M13 29a11 11 0 0 1 22 0" opacity={0.45} />
      <line className="ic-needle" x1="24" y1="29" x2="24" y2="19.5" stroke={accent} strokeWidth={2.8} />
      <circle cx="24" cy="29" r="2.2" fill={accent} stroke="none" />
      <circle className="ic-blink" cx="35" cy="15" r="1.8" fill={accent} stroke="none" />
      <path d="M16 34.5h16" opacity={0.45} />
    </svg>
  )
}

export function StormIcon({ size = 40, accent = "currentColor", className }: IconProps) {
  const still = useStill()
  return (
    <svg viewBox="0 0 48 48" width={size} height={size} className={cn(still, className)} aria-hidden fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
      <g className="ic-drift">
        <path d="M13 27h22a7 7 0 0 0 0-14 10 10 0 0 0-19-1.5A7.8 7.8 0 0 0 13 27Z" />
      </g>
      <path className="ic-bolt" d="M26 26l-5 8h6l-4 8" stroke={accent} strokeWidth={2.8} />
      <line className="ic-drop ic-drop-1" x1="15" y1="31" x2="14" y2="34.5" opacity={0.8} />
      <line className="ic-drop ic-drop-2" x1="33" y1="31" x2="32" y2="34.5" opacity={0.8} />
    </svg>
  )
}

export function SunPanelIcon({ size = 40, accent = "currentColor", className }: IconProps) {
  const still = useStill()
  return (
    <svg viewBox="0 0 48 48" width={size} height={size} className={cn(still, className)} aria-hidden fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
      <g className="ic-rays" stroke={accent}>
        {Array.from({ length: 8 }, (_, i) => {
          const a = (i * Math.PI) / 4
          return <line key={i} x1={17 + Math.cos(a) * 8.5} y1={15 + Math.sin(a) * 8.5} x2={17 + Math.cos(a) * 11.5} y2={15 + Math.sin(a) * 11.5} />
        })}
      </g>
      <circle className="ic-pulse" cx="17" cy="15" r="5.2" fill={accent} stroke="none" />
      <path d="M21 41l4-13h17l-4 13Z" />
      <path d="M23.5 34.5h16.5M30.5 28l-3.5 13M36 28l-3.5 13" opacity={0.5} />
    </svg>
  )
}

const BY_SOURCE = { A: MeterIcon, B: StormIcon, C: SunPanelIcon } as const

export function SourceIcon({ s, ...rest }: IconProps & { s: SourceKey }) {
  const Icon = BY_SOURCE[s]
  return <Icon {...rest} />
}
