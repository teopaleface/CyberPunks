import { useEffect, useRef, type ReactNode } from "react"
import { prefersReducedMotion } from "@/lib/motion"
import { cn } from "@/lib/utils"

interface TiltedGridProps {
  tiles: ReactNode[]
  /** px per second */
  speed?: number
  tileWidth?: number
  gap?: number
  className?: string
  children?: ReactNode
}

/**
 * A curved, endlessly streaming row of tiles that bends toward the viewer
 * at the edges and fades out (in the spirit of 21st.dev/@ruixen.ui/tilted-grid-hero).
 * Tiles are positioned every frame from a single offset, so the curve is
 * exact at any width. Slows down on hover, pauses off screen and under
 * reduced motion.
 */
export function TiltedGrid({ tiles, speed = 72, tileWidth = 380, gap = 28, className, children }: TiltedGridProps) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const tileRefs = useRef<(HTMLDivElement | null)[]>([])
  const hoverRef = useRef(false)

  // Enough copies to always cover the strip.
  const loop = [...tiles, ...tiles, ...tiles]

  useEffect(() => {
    const wrap = wrapRef.current
    if (!wrap) return
    const reduce = prefersReducedMotion()
    const step = tileWidth + gap
    const total = step * loop.length
    let offset = 0
    let raf = 0
    let last = performance.now()
    let visible = true
    let current = speed

    const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting))
    io.observe(wrap)

    const frame = (now: number) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      const target = reduce ? 0 : hoverRef.current ? speed * 0.15 : speed
      current += (target - current) * 0.06
      if (visible) {
        offset = (offset + current * dt) % total
        const w = wrap.clientWidth
        const cx = w / 2
        tileRefs.current.forEach((el, i) => {
          if (!el) return
          let x = i * step - offset
          // wrap into [-step, total - step)
          x = ((x % total) + total) % total - step * Math.floor(loop.length / 3)
          const center = x + tileWidth / 2
          const n = (center - cx) / (w / 2 + tileWidth * 0.2) // -1 … 1 across the strip
          const a = Math.abs(n)
          const rot = -n * 42
          const z = a * a * 220
          const opacity = a < 0.82 ? 1 : Math.max(0, 1 - (a - 0.82) / 0.32)
          el.style.transform = `translate3d(${x}px,0,${z}px) rotateY(${rot}deg)`
          el.style.opacity = String(opacity)
          el.style.display = opacity <= 0.01 ? "none" : ""
        })
      }
      raf = requestAnimationFrame(frame)
    }
    raf = requestAnimationFrame(frame)
    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
    }
  }, [speed, tileWidth, gap, loop.length])

  return (
    <div className={cn("relative overflow-clip [contain:paint]", className)}>
      <div
        ref={wrapRef}
        className="relative h-full w-full overflow-hidden [perspective:1100px] [perspective-origin:50%_50%]"
        onMouseEnter={() => (hoverRef.current = true)}
        onMouseLeave={() => (hoverRef.current = false)}
      >
        <div className="absolute inset-0 [transform-style:preserve-3d]">
          {loop.map((t, i) => (
            <div
              key={i}
              ref={(el) => {
                tileRefs.current[i] = el
              }}
              aria-hidden={i >= tiles.length}
              className="absolute top-1/2 left-0 -translate-y-1/2 will-change-transform [backface-visibility:hidden]"
              style={{ width: tileWidth }}
            >
              {t}
            </div>
          ))}
        </div>
      </div>
      {children}
    </div>
  )
}
