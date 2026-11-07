import { useReducedMotion } from "motion/react"

/** Respect the operating system's reduced-motion preference throughout the site. */
export const HONOR_REDUCED_MOTION = true

export function prefersReducedMotion(): boolean {
  if (!HONOR_REDUCED_MOTION || typeof window === "undefined") return false
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

export function useReduced(): boolean {
  const os = useReducedMotion()
  return HONOR_REDUCED_MOTION && !!os
}
