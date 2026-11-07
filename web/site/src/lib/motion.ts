import { useReducedMotion } from "motion/react"

/**
 * Whether the site obeys the OS "reduce motion" setting.
 * Off for the hackathon demo: on Windows with "Animation effects" turned
 * off, the browser reports reduced motion and every animation (beam,
 * reveals, smooth scroll) would stop. Turn on for a public launch.
 */
export const HONOR_REDUCED_MOTION = false

export function prefersReducedMotion(): boolean {
  if (!HONOR_REDUCED_MOTION || typeof window === "undefined") return false
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

export function useReduced(): boolean {
  const os = useReducedMotion()
  return HONOR_REDUCED_MOTION && !!os
}
