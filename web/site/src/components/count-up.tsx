import { animate, motion, useInView, useMotionValue, useTransform } from "motion/react"
import { useEffect, useRef } from "react"
import { useReduced } from "@/lib/motion"
import { fmt } from "@/lib/utils"

/** Adapted from design: reserve the final width and expose only the final number to assistive tech. */
export function CountUp({ value, className = "", tint = false }: { value: number; className?: string; tint?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { amount: 0.6, once: true })
  const reduce = useReduced()
  const count = useMotionValue(0)
  const display = useTransform(count, (n) => fmt(Math.round(n)))
  const color = useTransform(count, (n) => `color-mix(in oklab, var(--countup-ink) ${Math.round(value ? Math.min(1, Math.max(0, n / value)) * 100 : 100)}%, var(--foreground))`)

  useEffect(() => {
    if (!inView || reduce) return
    const controls = animate(count, value, { duration: 1.8, ease: [0.16, 1, 0.3, 1] })
    return () => controls.stop()
  }, [count, inView, reduce, value])

  return (
    <span ref={ref} className={`tabular inline-grid ${className}`}>
      <span aria-hidden className="invisible [grid-area:1/1]">{fmt(value)}</span>
      {reduce ? (
        <span aria-hidden className="text-right [grid-area:1/1]" style={tint ? { color: "var(--countup-ink)" } : undefined}>{fmt(value)}</span>
      ) : (
        <motion.span aria-hidden className="text-right [grid-area:1/1]" style={tint ? { color } : undefined}>{display}</motion.span>
      )}
      <span className="sr-only">{fmt(value)}</span>
    </span>
  )
}
