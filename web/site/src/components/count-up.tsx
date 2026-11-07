import { animate, useInView } from "motion/react"
import { useEffect, useRef, useState } from "react"
import { useReduced } from "@/lib/motion"
import { fmt } from "@/lib/utils"

/**
 * A number that counts up from 0 each time it comes into view. The final
 * value sits invisibly in the same cell, so the width never jumps while
 * the digits change.
 */
export function CountUp({
  value,
  duration = 1.8,
  once = false,
  className,
  onProgress,
}: {
  value: number
  duration?: number
  /** count only the first time it comes into view (for content that remounts anyway) */
  once?: boolean
  className?: string
  /** called with 0..1 as the count runs (1 when it is done or motion is reduced) */
  onProgress?: (p: number) => void
}) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { amount: 0.6, once })
  const reduce = useReduced()
  const [n, setN] = useState(reduce ? value : 0)

  useEffect(() => {
    if (reduce) return setN(value)
    if (!inView) {
      setN(0)
      return
    }
    const c = animate(0, value, { duration, ease: [0.16, 1, 0.3, 1], onUpdate: (v) => setN(v) })
    return () => c.stop()
  }, [inView, value, duration, reduce])

  const progressRef = useRef(onProgress)
  progressRef.current = onProgress
  useEffect(() => {
    progressRef.current?.(value ? Math.min(1, Math.max(0, n / value)) : 1)
  }, [n, value])

  return (
    <span ref={ref} className={`tabular inline-grid ${className ?? ""}`}>
      <span aria-hidden className="invisible [grid-area:1/1]">
        {fmt(value)}
      </span>
      <span aria-hidden className="text-right [grid-area:1/1]">
        {fmt(Math.round(n))}
      </span>
      <span className="sr-only">{fmt(value)}</span>
    </span>
  )
}
