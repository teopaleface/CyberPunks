import type { ReactNode } from "react"

/**
 * A reading section with enough space to clear the shared navigation.
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
      aria-label={label}
      className={`relative flex flex-col justify-center py-[clamp(84px,11vh,120px)] ${className}`}
    >
      {children}
    </section>
  )
}
