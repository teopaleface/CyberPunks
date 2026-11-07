import { Check, ChevronDown } from "lucide-react"
import { AnimatePresence, motion } from "motion/react"
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react"
import { cn } from "@/lib/utils"

export interface Option<T extends string> {
  value: T
  label: string
}

/**
 * A select in the site's theme: a dark button and a dark list, the current
 * option marked, keyboard support (arrows, Home/End, Enter, Escape) and
 * closing on a click outside. Replaces the browser's grey native menus.
 */
export function ThemedSelect<T extends string>({
  value,
  onChange,
  options,
  label,
  className,
  disabled,
}: {
  value: T
  onChange: (v: T) => void
  options: Option<T>[]
  /** visible label, shown before the button */
  label?: string
  className?: string
  disabled?: boolean
}) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(() => Math.max(0, options.findIndex((o) => o.value === value)))
  const wrap = useRef<HTMLDivElement>(null)
  const btn = useRef<HTMLButtonElement>(null)
  const listId = useId()
  const labelId = useId()
  const current = options.find((o) => o.value === value) ?? options[0]

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (!wrap.current?.contains(e.target as Node)) setOpen(false)
    }
    window.addEventListener("mousedown", onDown)
    return () => window.removeEventListener("mousedown", onDown)
  }, [open])

  useEffect(() => {
    if (open) setActive(Math.max(0, options.findIndex((o) => o.value === value)))
  }, [open, options, value])

  const choose = (i: number) => {
    onChange(options[i].value)
    setOpen(false)
    btn.current?.focus()
  }

  const onKey = (e: KeyboardEvent) => {
    if (disabled) return
    if (!open && (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "Enter" || e.key === " ")) {
      e.preventDefault()
      setOpen(true)
      return
    }
    if (!open) return
    if (e.key === "Escape") {
      e.preventDefault()
      setOpen(false)
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      setActive((a) => Math.min(options.length - 1, a + 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setActive((a) => Math.max(0, a - 1))
    } else if (e.key === "Home") {
      e.preventDefault()
      setActive(0)
    } else if (e.key === "End") {
      e.preventDefault()
      setActive(options.length - 1)
    } else if (e.key === "Enter" || e.key === " ") {
      e.preventDefault()
      choose(active)
    } else if (e.key === "Tab") setOpen(false)
  }

  return (
    <div ref={wrap} className={cn("relative inline-flex items-center gap-2", className)}>
      {label && (
        <span id={labelId} className="text-white/80">
          {label}
        </span>
      )}
      <button
        ref={btn}
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-labelledby={label ? `${labelId} ${listId}-v` : undefined}
        onClick={() => setOpen((o) => !o)}
        onKeyDown={onKey}
        className={cn(
          "inline-flex h-10 min-w-36 cursor-pointer items-center justify-between gap-3 rounded-xl bg-surface-2 px-3.5 text-left text-white transition-colors duration-150",
          "hover:bg-white/[0.1] focus-visible:ring-2 focus-visible:ring-[rgb(24,65,232)] focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-60",
          open && "bg-white/[0.1]"
        )}
      >
        <span id={`${listId}-v`}>{current?.label}</span>
        <ChevronDown className={cn("size-4 text-white/60 transition-transform duration-200", open && "rotate-180")} aria-hidden />
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul
            id={listId}
            role="listbox"
            aria-activedescendant={`${listId}-${active}`}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.12 }}
            className="absolute top-[calc(100%+6px)] right-0 z-[1000] min-w-full overflow-hidden rounded-xl bg-[#1b1b1f] p-1 shadow-[0_16px_40px_-8px_rgba(0,0,0,.9)] ring-1 ring-white/10"
          >
            {options.map((o, i) => {
              const sel = o.value === value
              return (
                <li
                  key={o.value}
                  id={`${listId}-${i}`}
                  role="option"
                  aria-selected={sel}
                  onMouseEnter={() => setActive(i)}
                  onMouseDown={(e) => {
                    e.preventDefault()
                    choose(i)
                  }}
                  className={cn(
                    "flex cursor-pointer items-center justify-between gap-6 rounded-lg px-3 py-2 whitespace-nowrap",
                    i === active ? "bg-white/[0.08] text-white" : "text-white/80"
                  )}
                >
                  {o.label}
                  {sel && <Check className="size-4 text-amber" aria-hidden />}
                </li>
              )
            })}
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  )
}
