import Lenis from "lenis"
import { createContext, useContext, useEffect, useState, type ReactNode } from "react"
import { useReduced } from "@/lib/motion"

const LenisContext = createContext<Lenis | null>(null)
export const useLenis = () => useContext(LenisContext)

/**
 * Smooth wheel scrolling for the reading pages. The landing page turns it
 * off (`enabled={false}`) because it moves screen by screen instead.
 */
export function SmoothScroll({ children, enabled = true }: { children: ReactNode; enabled?: boolean }) {
  const reduce = useReduced()
  const [lenis, setLenis] = useState<Lenis | null>(null)

  useEffect(() => {
    if (!enabled || reduce) return
    const instance = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
    })
    setLenis(instance)
    let raf = 0
    const loop = (time: number) => {
      instance.raf(time)
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => {
      cancelAnimationFrame(raf)
      instance.destroy()
      setLenis(null)
    }
  }, [enabled, reduce])

  return <LenisContext.Provider value={lenis}>{children}</LenisContext.Provider>
}
