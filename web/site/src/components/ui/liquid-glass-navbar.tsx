import { animate, motion, useMotionValue, useSpring, useTransform } from "motion/react"
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import type { NavItem } from "@/lib/site"

interface LiquidNavbarProps {
  items: NavItem[]
  logo: React.ReactNode
  cta?: React.ReactNode
  /** id of the active item, or null when none is in view */
  activeId: string | null
  onNavigate: (href: string) => void
  className?: string
}

/**
 * Liquid glass navbar, in the spirit of 21st.dev/@gughigug/liquid-glass-navbar:
 * a glass bar whose active marker is a drop of liquid. When it moves, a
 * fast "head" and a slow "tail" drop are pulled apart and joined by a goo
 * filter, so the drop stretches, splits into droplets and merges back with
 * a ripple. Hover shows a faint meniscus under the pointer.
 * The options never change from page to page; only the marker moves.
 */
export function LiquidNavbar({ items, logo, cta, activeId, onNavigate, className }: LiquidNavbarProps) {
  const trackRef = useRef<HTMLDivElement>(null)
  const itemRefs = useRef<(HTMLAnchorElement | null)[]>([])
  const [hover, setHover] = useState<number | null>(null)
  const [rects, setRects] = useState<{ x: number; w: number }[]>([])

  const activeIndex = items.findIndex((i) => i.id === activeId)

  const measure = useCallback(() => {
    setRects(
      itemRefs.current.map((el) => (el ? { x: el.offsetLeft, w: el.offsetWidth } : { x: 0, w: 0 }))
    )
  }, [])

  useLayoutEffect(() => {
    measure()
    const ro = new ResizeObserver(measure)
    if (trackRef.current) ro.observe(trackRef.current)
    window.addEventListener("resize", measure)
    document.fonts?.ready.then(measure)
    return () => {
      ro.disconnect()
      window.removeEventListener("resize", measure)
    }
  }, [measure])

  // Raw target, then two springs: a quick head and a lazy tail.
  const tx = useMotionValue(0)
  const tw = useMotionValue(0)
  const headX = useSpring(tx, { stiffness: 520, damping: 34, mass: 0.6 })
  const headW = useSpring(tw, { stiffness: 520, damping: 34, mass: 0.6 })
  const tailX = useSpring(tx, { stiffness: 140, damping: 18, mass: 1 })
  const tailW = useSpring(tw, { stiffness: 140, damping: 18, mass: 1 })
  const visible = useSpring(0, { stiffness: 300, damping: 30 })
  const dropScale = useTransform(visible, [0, 1], [0.2, 1])

  // Middle droplet sits between head and tail; it is what visibly "splits".
  const midX = useTransform<number, number>([headX, tailX], ([h, t]) => (h + t) / 2)
  const midW = useTransform<number, number>([headW, tailW], ([h, t]) => Math.min(h, t) * 0.55)
  const midOffset = useTransform<number, number>([headW, tailW, midW], ([h, t, m]) => (h + t) / 4 - m / 2)

  const ripple = useMotionValue(0)
  const rippleOpacity = useTransform(ripple, [0, 0.15, 1], [0, 0.55, 0])
  const rippleScale = useTransform(ripple, [0, 1], [0.6, 1.6])
  const lastIndex = useRef<number>(-1)

  useEffect(() => {
    const r = rects[activeIndex]
    if (!r) {
      visible.set(0)
      return
    }
    const first = lastIndex.current === -1
    if (first) {
      // Appear in place, no travel.
      tx.jump(r.x)
      tw.jump(r.w)
      headX.jump(r.x)
      headW.jump(r.w)
      tailX.jump(r.x)
      tailW.jump(r.w)
    } else {
      tx.set(r.x)
      tw.set(r.w)
    }
    visible.set(1)
    if (lastIndex.current !== activeIndex) {
      const t = setTimeout(() => {
        ripple.set(0)
        animate(ripple, 1, { duration: 0.9, ease: [0.22, 1, 0.36, 1] })
      }, first ? 0 : 260)
      lastIndex.current = activeIndex
      return () => clearTimeout(t)
    }
  }, [activeIndex, rects, tx, tw, headX, headW, tailX, tailW, visible, ripple])

  const hoverRect = hover !== null ? rects[hover] : null

  return (
    <nav
      aria-label="Main navigation"
      className={cn(
        "relative flex items-center gap-1 rounded-full p-1.5 pl-4",
        "bg-white/[0.06] backdrop-blur-2xl backdrop-saturate-150",
        "shadow-[inset_0_1px_0_rgba(255,255,255,.28),inset_0_-1px_0_rgba(255,255,255,.06),0_10px_40px_-12px_rgba(0,0,0,.9)]",
        "ring-1 ring-white/10",
        className
      )}
    >
      {/* goo filter: blur, then sharpen alpha so nearby blobs fuse */}
      <svg aria-hidden className="absolute h-0 w-0">
        <defs>
          <filter id="nav-goo">
            <feGaussianBlur in="SourceGraphic" stdDeviation="7" result="blur" />
            <feColorMatrix
              in="blur"
              mode="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9"
              result="goo"
            />
            <feComposite in="SourceGraphic" in2="goo" operator="atop" />
          </filter>
        </defs>
      </svg>

      <div className="mr-2 shrink-0">{logo}</div>

      <div ref={trackRef} className="relative flex items-center" onMouseLeave={() => setHover(null)}>
        {/* hover meniscus */}
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 rounded-full bg-white/[0.07]"
          animate={{
            x: hoverRect?.x ?? 0,
            width: hoverRect?.w ?? 0,
            opacity: hoverRect && hover !== activeIndex ? 1 : 0,
          }}
          transition={{ type: "spring", stiffness: 400, damping: 32 }}
        />

        {/* the drop */}
        <motion.div
          aria-hidden
          className="pointer-events-none absolute inset-y-0 left-0 right-0"
          style={{ filter: "url(#nav-goo)", opacity: visible }}
        >
          <motion.span
            className="absolute inset-y-0 rounded-full bg-[var(--ember)]"
            style={{ x: tailX, width: tailW, scale: dropScale, opacity: 0.55 }}
          />
          <motion.span
            className="absolute top-1/2 h-3 -translate-y-1/2 rounded-full bg-[var(--ember)]"
            style={{ x: midX, width: midW, marginLeft: midOffset, opacity: 0.55 }}
          />
          <motion.span
            className="absolute inset-y-0 rounded-full bg-[var(--ember)]"
            style={{ x: headX, width: headW, scale: dropScale, opacity: 0.55 }}
          />
        </motion.div>

        {/* glass highlight riding on the drop */}
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 rounded-full shadow-[inset_0_1px_0_rgba(255,255,255,.75),inset_0_-6px_14px_rgba(255,197,2,.35)]"
          style={{ x: headX, width: headW, opacity: visible, scale: dropScale }}
        />
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 rounded-full ring-2 ring-[var(--ember-soft)]"
          style={{ x: headX, width: headW, opacity: rippleOpacity, scale: rippleScale }}
        />

        {items.map((item, i) => {
          const Icon = item.icon
          const active = i === activeIndex
          return (
            <a
              key={item.id}
              ref={(el) => {
                itemRefs.current[i] = el
              }}
              href={item.href}
              aria-current={active ? "location" : undefined}
              onMouseEnter={() => setHover(i)}
              onFocus={() => setHover(i)}
              onClick={(e) => {
                e.preventDefault()
                onNavigate(item.href)
              }}
              className={cn(
                "group/item relative z-10 flex h-10 items-center gap-2 rounded-full px-3 text-sm transition-colors duration-300 md:px-4",
                active ? "text-white" : "text-white/70 hover:text-white"
              )}
            >
              <Icon
                aria-hidden
                className={cn(
                  "hidden size-4 shrink-0 sm:block transition-transform duration-500 ease-[var(--ease-out)]",
                  "group-hover/item:-rotate-12 group-hover/item:scale-110",
                  active && "text-white"
                )}
              />
              <span>{item.label}</span>
            </a>
          )
        })}
      </div>

      {cta && <div className="ml-1 shrink-0">{cta}</div>}
    </nav>
  )
}
