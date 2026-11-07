import { useEffect, useRef } from "react"
import { useReduced } from "@/lib/motion"
import { cn } from "@/lib/utils"

interface HalftoneWordmarkProps {
  word: string
  className?: string
  /** Fraction of the letters hidden below the bottom edge. */
  crop?: number
  /** Ink colour at rest and when stirred. */
  rest?: [number, number, number]
  hot?: [number, number, number]
}

const REST: [number, number, number] = [235, 235, 238]
const HOT: [number, number, number] = [255,197,2]

interface Dot {
  hx: number
  hy: number
  x: number
  y: number
  vx: number
  vy: number
  r: number
  heat: number
}

/**
 * Halftone wordmark, after 21st.dev/@kedhareswer/halftone-wordmark-footer:
 * an enormous word cropped by the bottom edge, printed in halftone dots.
 * Dots part around the pointer on springs and warm from white to orange as
 * they move; a click sends a shock ring through the letters.
 */
export function HalftoneWordmark({
  word,
  className,
  crop = -0.24,
  rest = REST,
  hot = HOT,
}: HalftoneWordmarkProps) {
  const reduce = useReduced()
  const wrapRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const wrap = wrapRef.current
    const canvas = canvasRef.current
    if (!wrap || !canvas) return
    const ctx = canvas.getContext("2d")!

    let dots: Dot[] = []
    let W = 0,
      H = 0,
      dpr = 1,
      step = 8
    let raf = 0
    let visible = false
    const pointer = { x: -9999, y: -9999, active: false }
    const shocks: { x: number; y: number; r: number; life: number }[] = []

    const build = async () => {
      try {
        await document.fonts.load(`800 100px Unbounded`)
      } catch {
        /* fall back to whatever is loaded */
      }
      W = wrap.clientWidth
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      step = Math.max(5, Math.round(W / 170))

      // Fit the word to the width, then crop its foot.
      const off = document.createElement("canvas")
      const octx = off.getContext("2d")!
      let size = 100
      octx.font = `800 ${size}px Unbounded, sans-serif`
      const m = octx.measureText(word)
      size = (size * (W * 0.98)) / m.width
      const capH = size * 0.74
      H = Math.round(capH * (1 - crop) + step * 2)

      off.width = W
      off.height = H
      octx.font = `800 ${size}px Unbounded, sans-serif`
      octx.textBaseline = "alphabetic"
      octx.textAlign = "center"
      octx.fillStyle = "#fff"
      octx.fillText(word, W / 2, step + capH)
      const data = octx.getImageData(0, 0, W, H).data

      dots = []
      for (let y = step / 2; y < H; y += step) {
        for (let x = step / 2; x < W; x += step) {
          // coverage over the cell
          let a = 0,
            n = 0
          for (let oy = -step / 3; oy <= step / 3; oy += step / 3)
            for (let ox = -step / 3; ox <= step / 3; ox += step / 3) {
              const px = Math.round(x + ox),
                py = Math.round(y + oy)
              if (px >= 0 && py >= 0 && px < W && py < H) {
                a += data[(py * W + px) * 4 + 3]
                n++
              }
            }
          const cov = a / (n * 255)
          if (cov > 0.05) {
            // halftone: fade toward the bottom crop, like ink running out
            const fade = 0.55 + 0.45 * (1 - y / H)
            dots.push({ hx: x, hy: y, x, y, vx: 0, vy: 0, r: (step / 2) * Math.pow(cov, 0.6) * fade, heat: 0 })
          }
        }
      }
      canvas.width = W * dpr
      canvas.height = H * dpr
      canvas.style.height = `${H}px`
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      draw()
    }

    const draw = () => {
      ctx.clearRect(0, 0, W, H)
      for (const d of dots) {
        const t = Math.min(1, d.heat)
        const r = Math.round(rest[0] + (hot[0] - rest[0]) * t)
        const g = Math.round(rest[1] + (hot[1] - rest[1]) * t)
        const b = Math.round(rest[2] + (hot[2] - rest[2]) * t)
        ctx.fillStyle = `rgb(${r},${g},${b})`
        ctx.beginPath()
        ctx.arc(d.x, d.y, d.r * (1 + t * 0.25), 0, Math.PI * 2)
        ctx.fill()
      }
    }

    const tick = () => {
      raf = requestAnimationFrame(tick)
      if (!visible || reduce) return
      const R = Math.max(90, W * 0.08)
      for (const s of shocks) {
        s.r += W * 0.012
        s.life -= 0.016
      }
      for (let i = shocks.length - 1; i >= 0; i--) if (shocks[i].life <= 0) shocks.splice(i, 1)

      let moving = false
      for (const d of dots) {
        // pointer pushes dots away
        if (pointer.active) {
          const dx = d.x - pointer.x,
            dy = d.y - pointer.y
          const dist2 = dx * dx + dy * dy
          if (dist2 < R * R) {
            const dist = Math.sqrt(dist2) || 1
            const f = (1 - dist / R) * 2.2
            d.vx += (dx / dist) * f
            d.vy += (dy / dist) * f
          }
        }
        for (const s of shocks) {
          const dx = d.hx - s.x,
            dy = d.hy - s.y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const band = Math.abs(dist - s.r)
          if (band < 40) {
            const f = (1 - band / 40) * 3.2 * s.life
            d.vx += (dx / dist) * f
            d.vy += (dy / dist) * f
          }
        }
        // spring home
        d.vx += (d.hx - d.x) * 0.06
        d.vy += (d.hy - d.y) * 0.06
        d.vx *= 0.82
        d.vy *= 0.82
        d.x += d.vx
        d.y += d.vy
        const off = Math.hypot(d.x - d.hx, d.y - d.hy)
        d.heat += (Math.min(1, off / 18) - d.heat) * 0.12
        if (off > 0.2 || d.heat > 0.01) moving = true
      }
      if (moving || pointer.active || shocks.length) draw()
    }

    const local = (e: PointerEvent) => {
      const r = canvas.getBoundingClientRect()
      return { x: e.clientX - r.left, y: e.clientY - r.top }
    }
    const onMove = (e: PointerEvent) => {
      const p = local(e)
      pointer.x = p.x
      pointer.y = p.y
      pointer.active = true
    }
    const onLeave = () => {
      pointer.active = false
      pointer.x = pointer.y = -9999
    }
    const onDown = (e: PointerEvent) => {
      const p = local(e)
      shocks.push({ x: p.x, y: p.y, r: 0, life: 1 })
    }

    const io = new IntersectionObserver(([e]) => (visible = e.isIntersecting))
    io.observe(canvas)
    canvas.addEventListener("pointermove", onMove)
    canvas.addEventListener("pointerleave", onLeave)
    canvas.addEventListener("pointerdown", onDown)
    let lastW = 0
    const ro = new ResizeObserver(() => {
      if (Math.abs(wrap.clientWidth - lastW) > 4) {
        lastW = wrap.clientWidth
        build()
      }
    })
    ro.observe(wrap)
    if (!reduce) raf = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
      ro.disconnect()
      canvas.removeEventListener("pointermove", onMove)
      canvas.removeEventListener("pointerleave", onLeave)
      canvas.removeEventListener("pointerdown", onDown)
    }
  }, [word, crop, rest, hot, reduce])

  return (
    <div ref={wrapRef} className={cn("relative w-full", className)}>
      <canvas ref={canvasRef} className="block w-full cursor-crosshair touch-none" role="img" aria-label={word} />
    </div>
  )
}
