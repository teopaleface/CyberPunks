import { motion, type HTMLMotionProps } from "motion/react"
import { useReduced } from "@/lib/motion"
import type { ElementType, ReactNode } from "react"

// motion.create must not run per render, or the element remounts.
const cache = new Map<ElementType, ElementType>()
function motionFor(tag: ElementType): ElementType {
  if (!cache.has(tag)) cache.set(tag, motion.create(tag as never) as ElementType)
  return cache.get(tag)!
}

type RevealProps = {
  children: ReactNode
  /** Seconds. Use 0, 0.08, 0.16… to stagger top to bottom. */
  delay?: number
  /** Distance the element travels down into place. */
  y?: number
  as?: ElementType
  className?: string
} & Omit<HTMLMotionProps<"div">, "children">

/**
 * Fade-in from top to bottom on scroll: the element starts a little
 * above its place and settles down into it, once, as it enters.
 */
export function Reveal({
  children,
  delay = 0,
  y = 16,
  as = "div",
  className,
  ...rest
}: RevealProps) {
  const reduce = useReduced()
  const MotionTag = motionFor(as)
  return (
    <MotionTag
      className={className}
      initial={{ opacity: 0, y: reduce ? 0 : -y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "0px 0px -8% 0px" }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
      {...rest}
    >
      {children}
    </MotionTag>
  )
}
