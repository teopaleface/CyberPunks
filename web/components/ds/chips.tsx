"use client";

import { cn } from "cn";
import { Dot, type Tone } from "./index";

/** Filtrele din capul paginii: „Toate” alb când e ales, celelalte cu punctul culorii lor. */
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
              "inline-flex h-9 items-center gap-2 rounded-full border px-4 text-[14.5px] font-[520] whitespace-nowrap transition-colors duration-150",
              on ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-[#2a3a52] text-ink hover:border-[#3d5170] hover:bg-[#0f1a2b]",
            )}
          >
            {it.tone && !on ? <Dot tone={it.tone} /> : null}
            {it.label}
            {typeof it.count === "number" ? <span className={on ? "text-[#0b1322]/70" : "text-ink-soft"}>({it.count})</span> : null}
          </button>
        );
      })}
    </div>
  );
}
