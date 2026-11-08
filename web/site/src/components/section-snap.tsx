import { createContext, useCallback, useContext, useEffect, useMemo, useRef, type ReactNode } from "react"
import { prefersReducedMotion } from "@/lib/motion"

/**
 * Full-page section scroller for the landing page.
 * Every element marked `data-snap` is one screen. A wheel gesture, a swipe,
 * or the arrow / page keys move exactly one stop, with an eased scroll, so
 * the screen always holds one section, centred, with the same space above
 * and below. A section taller than the screen (short laptops) gets extra
 * stops so it can still be read whole.
 * Turned off on narrow or very short screens, where normal scrolling is
 * kinder.
 */

interface SnapApi {
  goTo: (id: string) => void
  /** Go to stage i of a pinned section (data-snap-steps). */
  goToStep: (id: string, i: number) => void
  next: () => void
}

const SnapContext = createContext<SnapApi | null>(null)
export const useSnap = () => useContext(SnapContext)

const DURATION = 950
const GESTURE_GAP = 240 // ms of quiet that ends one wheel gesture
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2)

function enabledFor(w: number, h: number) {
  return w >= 768 && h >= 500 && !prefersReducedMotion() && window.matchMedia("(hover: hover) and (pointer: fine)").matches
}

export function SectionSnap({ children }: { children: ReactNode }) {
  const animating = useRef(false)
  const raf = useRef(0)

  const stops = useCallback(() => {
    const vh = window.innerHeight
    const list: { y: number; id: string }[] = []
    document.querySelectorAll<HTMLElement>("[data-snap]").forEach((el) => {
      const top = el.getBoundingClientRect().top + window.scrollY
      const h = el.offsetHeight
      const steps = Number(el.dataset.snapSteps || 0)
      if (steps > 1) {
        // A pinned section: one stop per stage, one screen apart.
        for (let i = 0; i < steps; i++) list.push({ y: Math.round(top + i * vh), id: el.id })
      } else if (h <= vh * 1.25) {
        // One screen (or barely more): one stop. Centre it; if it is a little
        // taller, align its top so the heading is never cut.
        list.push({ y: Math.round(h <= vh + 2 ? top + (h - vh) / 2 : top), id: el.id })
      } else {
        const last = top + h - vh
        for (let y = top; y < last; y += vh * 0.8) list.push({ y: Math.round(y), id: el.id })
        list.push({ y: Math.round(last), id: el.id })
      }
    })
    const max = document.documentElement.scrollHeight - vh
    const clamped = list.map((s) => ({ ...s, y: Math.max(0, Math.min(max, s.y)) })).sort((a, b) => a.y - b.y)
    // Two stops closer than a third of a screen feel like one step that did nothing: keep the first.
    return clamped.filter((s, i) => i === 0 || s.y - clamped[i - 1].y > vh * 0.33)
  }, [])

  const nearest = useCallback(() => {
    const s = stops()
    let best = 0
    s.forEach((p, i) => {
      if (Math.abs(p.y - window.scrollY) < Math.abs(s[best].y - window.scrollY)) best = i
    })
    return { s, i: best }
  }, [stops])

  const animateTo = useCallback((y: number) => {
    cancelAnimationFrame(raf.current)
    animating.current = false
    const from = window.scrollY
    const dist = y - from
    if (Math.abs(dist) < 1) return
    if (prefersReducedMotion()) {
      window.scrollTo(0, y)
      return
    }
    animating.current = true
    const start = performance.now()
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / DURATION)
      window.scrollTo(0, from + dist * easeInOut(t))
      if (t < 1) raf.current = requestAnimationFrame(step)
      else animating.current = false
    }
    raf.current = requestAnimationFrame(step)
  }, [])

  const move = useCallback(
    (dir: 1 | -1) => {
      const { s, i } = nearest()
      // If we sit between stops (after a resize), first settle on the closest one.
      if (!s.length) return
      const atStop = Math.abs(s[i].y - window.scrollY) < 4
      const target = atStop ? Math.max(0, Math.min(s.length - 1, i + dir)) : i
      animateTo(s[target].y)
    },
    [nearest, animateTo]
  )

  const goTo = useCallback(
    (id: string) => {
      const s = stops().find((p) => p.id === id)
      if (s) animateTo(s.y)
    },
    [stops, animateTo]
  )

  useEffect(() => {
    let active = enabledFor(window.innerWidth, window.innerHeight)
    let lastWheel = 0
    let gestureUsed = false

    const onWheel = (e: WheelEvent) => {
      if (!active || e.ctrlKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) return
      // Let inner scrollable areas (a long table, a map) keep their wheel.
      const t = e.target
      if (t instanceof Element && t.closest("[data-snap-ignore], [data-lenis-prevent], input, textarea, select, [role=dialog], .leaflet-container")) return
      e.preventDefault()
      const now = performance.now()
      const gap = now - lastWheel
      lastWheel = now
      if (gap > GESTURE_GAP) gestureUsed = false
      if (animating.current || gestureUsed || Math.abs(e.deltaY) < 3) return
      gestureUsed = true
      move(e.deltaY > 0 ? 1 : -1)
    }

    const onKey = (e: KeyboardEvent) => {
      if (!active || e.altKey || e.ctrlKey || e.metaKey) return
      const el = document.activeElement as HTMLElement | null
      if (el && (el.isContentEditable || el.closest("[data-snap-ignore], [role=dialog], [role=listbox], [role=slider]") || /^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(el.tagName))) return
      const down = ["ArrowDown", "PageDown"].includes(e.key) || (e.key === " " && !e.shiftKey && el?.tagName !== "BUTTON")
      const up = ["ArrowUp", "PageUp"].includes(e.key) || (e.key === " " && e.shiftKey)
      if (down || up) {
        e.preventDefault()
        if (!animating.current) move(down ? 1 : -1)
      } else if (e.key === "Home" || e.key === "End") {
        e.preventDefault()
        const s = stops()
        if (s.length) animateTo(e.key === "Home" ? s[0].y : s[s.length - 1].y)
      }
    }

    let resizeTimer = 0
    const onResize = () => {
      cancelAnimationFrame(raf.current)
      animating.current = false
      active = enabledFor(window.innerWidth, window.innerHeight)
      window.clearTimeout(resizeTimer)
      resizeTimer = window.setTimeout(() => {
        if (!active) return
        const { s, i } = nearest()
        if (s.length) window.scrollTo(0, s[i].y)
      }, 150)
    }

    const preference = window.matchMedia("(prefers-reduced-motion: reduce)")
    preference.addEventListener("change", onResize)
    window.addEventListener("wheel", onWheel, { passive: false })
    window.addEventListener("keydown", onKey)
    window.addEventListener("resize", onResize)
    return () => {
      preference.removeEventListener("change", onResize)
      animating.current = false
      cancelAnimationFrame(raf.current)
      window.clearTimeout(resizeTimer)
      window.removeEventListener("wheel", onWheel)
      window.removeEventListener("keydown", onKey)
      window.removeEventListener("resize", onResize)
    }
  }, [move, nearest, stops, animateTo])

  const goToStep = useCallback(
    (id: string, i: number) => {
      const el = document.getElementById(id)
      if (!el) return
      const top = el.getBoundingClientRect().top + window.scrollY
      animateTo(Math.round(top + i * window.innerHeight))
    },
    [animateTo]
  )

  const api = useMemo<SnapApi>(() => ({ goTo, goToStep, next: () => move(1) }), [goTo, goToStep, move])

  return <SnapContext.Provider value={api}>{children}</SnapContext.Provider>
}

/**
 * One landing screen: exactly the height of the viewport, content centred
 * with equal padding above and below (the padding clears the navbar).
 */
export function Screen({
  id,
  className = "",
  children,
  label,
}: {
  id: string
  className?: string
  children: ReactNode
  label?: string
}) {
  return (
    <section
      id={id}
      data-snap
      aria-label={label}
      className={`relative flex min-h-[100svh] flex-col justify-center py-[clamp(84px,11vh,120px)] ${className}`}
    >
      {children}
    </section>
  )
}
