import { motion, useAnimate, useInView } from "motion/react"
import { useReduced } from "@/lib/motion"
import { useCallback, useEffect, useId, useRef } from "react"
import { cn } from "@/lib/utils"

/**
 * The product's word, drawn as SVG so the glass can bend it. The team has no
 * graphic mark yet (the sun logos were rejected), so the word is the mark.
 */
export function DaybreakMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 300 64" className={className} aria-hidden>
      <text
        x="150"
        y="46"
        textAnchor="middle"
        fill="#fff"
        fontFamily="Unbounded, Geist, sans-serif"
        fontWeight="700"
        fontSize="44"
        letterSpacing="-1.5"
      >
        Daybreak
      </text>
    </svg>
  )
}

/**
 * Liquid glass logo reveal, after 21st.dev/@shepovalovdenis/liquid-glass-logo-reveal:
 * a droplet falls, lands, and spreads into a glass tile. Inside the tile the
 * mark is magnified and bent at the rim (SVG displacement) with a little
 * colour dispersion, like real glass; then the glass lets go and the mark
 * stays lit. Plays once when it enters the screen; click to replay.
 * Built with SVG filters and Motion instead of WebGL.
 */
export function LiquidGlassLogoReveal({ className }: { className?: string }) {
  const [scope, animate] = useAnimate()
  const inView = useInView(scope, { once: true, amount: 0.6 })
  const reduce = useReduced()
  const fid = useId().replace(/:/g, "")
  const running = useRef(false)

  const play = useCallback(async () => {
    if (running.current) return
    running.current = true
    const e = [0.22, 1, 0.36, 1] as const
    if (reduce) {
      await animate(".mark", { opacity: 1, scale: 1 }, { duration: 0.3 })
      running.current = false
      return
    }
    animate(".mark", { opacity: 0.25, scale: 0.94 }, { duration: 0.2 })
    animate(".tile", { scale: 0, opacity: 0, borderRadius: "50%" }, { duration: 0 })
    animate(".splash", { scale: 0.2, opacity: 0 }, { duration: 0 })
    // fall
    await animate(
      ".drop",
      { y: ["-260%", "0%"], scaleY: [1.5, 1.15], scaleX: [0.7, 0.9], opacity: [0, 1] },
      { duration: 0.55, ease: [0.55, 0, 1, 0.45] }
    )
    // splash: drop flattens, ring runs out, glass spreads
    animate(".drop", { scaleY: 0.3, scaleX: 2.2, opacity: 0 }, { duration: 0.28, ease: e })
    animate(".splash", { scale: [0.2, 2.4], opacity: [0.9, 0] }, { duration: 1.1, ease: e })
    await animate(
      ".tile",
      { scale: [0.15, 1.08, 1], opacity: [0.6, 1, 1], borderRadius: ["50%", "30%", "28%"] },
      { duration: 0.9, ease: e }
    )
    animate(".mark", { opacity: 1, scale: 1 }, { duration: 0.6, ease: e })
    // bend settles
    await animate(".lens", { scale: [1.18, 1.06] }, { duration: 1.2, ease: e })
    await new Promise((r) => setTimeout(r, 900))
    // glass lets go
    await animate(".tile", { opacity: 0, scale: 1.12 }, { duration: 1, ease: e })
    running.current = false
  }, [animate, reduce])

  useEffect(() => {
    if (inView) play()
  }, [inView, play])

  return (
    <button
      ref={scope}
      type="button"
      onClick={play}
      aria-label="Replay logo animation"
      className={cn("group relative grid aspect-square cursor-pointer place-items-center outline-none", className)}
    >
      <svg aria-hidden className="absolute h-0 w-0">
        <defs>
          {/* Rim refraction: a radial field pushes pixels outward near the edge. */}
          <filter id={`bend-${fid}`} x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.012" numOctaves="2" seed="4" result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale="18" xChannelSelector="R" yChannelSelector="G" />
          </filter>
        </defs>
      </svg>

      {/* light behind, so the glass has something to bend */}
      <div aria-hidden className="absolute inset-[18%] rounded-full bg-ember/30 blur-[60px] transition-opacity duration-700 group-hover:opacity-100" />
      <div aria-hidden className="absolute top-0 left-1/2 h-1/2 w-[3px] -translate-x-1/2 bg-[linear-gradient(to_bottom,transparent,rgba(255,197,2,.9))] blur-[1px]" />

      {/* the mark */}
      <motion.div className="mark relative w-[62%]" initial={{ opacity: 0.25, scale: 0.94 }}>
        <DaybreakMark className="w-full drop-shadow-[0_0_28px_rgba(255,197,2,.65)]" />
      </motion.div>

      {/* falling drop */}
      <motion.span
        aria-hidden
        className="drop absolute top-1/2 left-1/2 -mt-[4%] -ml-[4%] size-[8%] rounded-full bg-[radial-gradient(circle_at_35%_30%,#fff,rgba(255,197,2,.9)_40%,rgba(255,197,2,.6))] shadow-[0_0_30px_rgba(255,197,2,.9)]"
        initial={{ opacity: 0 }}
      />
      {/* splash ring */}
      <motion.span
        aria-hidden
        className="splash absolute size-[40%] rounded-full ring-2 ring-white/70"
        initial={{ opacity: 0 }}
      />

      {/* glass tile: bent, magnified copy of the mark with dispersion */}
      <motion.div
        aria-hidden
        className="tile absolute grid size-[64%] place-items-center overflow-hidden bg-white/[0.06] backdrop-blur-[2px] shadow-[inset_0_2px_0_rgba(255,255,255,.7),inset_0_-14px_30px_rgba(255,92,255,.25),inset_0_0_0_1px_rgba(255,255,255,.18),0_30px_80px_-20px_rgba(255,197,2,.55)]"
        initial={{ opacity: 0, scale: 0 }}
      >
        <motion.div className="lens relative w-[90%]" style={{ filter: `url(#bend-${fid})` }}>
          <DaybreakMark className="absolute inset-0 w-full translate-x-[2px] opacity-60 mix-blend-screen [filter:sepia(1)_saturate(6)_hue-rotate(-30deg)]" />
          <DaybreakMark className="absolute inset-0 w-full -translate-x-[2px] opacity-50 mix-blend-screen [filter:sepia(1)_saturate(4)_hue-rotate(160deg)]" />
          <DaybreakMark className="relative w-full" />
        </motion.div>
        {/* specular sweep */}
        <span className="pointer-events-none absolute -top-1/4 -left-1/4 h-1/2 w-[150%] rotate-[-18deg] bg-white/10 blur-xl" />
      </motion.div>
    </button>
  )
}
