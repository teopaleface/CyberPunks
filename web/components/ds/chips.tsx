"use client";

import { cn } from "cn";
import { Dot, type Tone } from "./index";

/** Filtrul ales are contur alb; punctele surselor își păstrează culoarea. */
export function Chips<T extends string>({
  items,
  value,
  onChange,
  label,
  className,
}: {
  items: { id: T; label: string; tone?: Tone; count?: number }[];
  value: T;
  onChange: (id: T) => void;
  label: string;
  className?: string;
}) {
  return (
    <div role="group" aria-label={label} className={cn("flex flex-wrap gap-2.5", className)}>
      {items.map((it) => {
        const on = it.id === value;
        return (
          <button
            key={it.id}
            type="button"
            aria-pressed={on}
            onClick={() => onChange(it.id)}
            className={cn(
              "inline-flex min-h-10 items-center gap-2 rounded-full border px-4 py-1.5 text-[15px] font-[550] whitespace-nowrap transition-colors duration-150",
              on ? "border-ink bg-surface-2 text-ink" : "border-input text-ink-soft hover:border-ink-soft hover:bg-surface-2 hover:text-ink",
            )}
          >
            {it.tone ? <Dot tone={it.tone} /> : null}
            {it.label}
            {typeof it.count === "number" ? <span className="text-ink-soft tabular-nums">({it.count})</span> : null}
          </button>
        );
      })}
    </div>
  );
}
