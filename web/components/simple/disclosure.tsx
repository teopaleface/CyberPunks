"use client";

import { useId, useState, type ReactNode } from "react";
import { cn } from "cn";

/**
 * Secțiune care se deschide la cerere („Detalii tehnice”, „Detaliile zilei”): primul nivel rămâne simplu,
 * cifrele și termenii tehnici sunt la un click. Înălțimea se deschide cu grid-template-rows (0fr → 1fr),
 * 200 ms, ease-out puternic; fără mișcare când sistemul cere mișcare redusă.
 */
export function Disclosure({
  title,
  hint,
  defaultOpen = false,
  className,
  children,
}: {
  title: ReactNode;
  /** O frază scurtă lângă titlu: ce găsești înăuntru. */
  hint?: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const id = useId();
  return (
    <section className={cn("border-t border-rule", className)}>
      <h2 className="m-0">
        <button
          type="button"
          aria-expanded={open}
          aria-controls={id}
          onClick={() => setOpen((v) => !v)}
          className="group flex w-full items-start gap-3 py-4 text-left transition-colors duration-150 hover:text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            aria-hidden="true"
            className={cn("mt-1.5 shrink-0 transition-transform duration-200 ease-[cubic-bezier(0.23,1,0.32,1)] motion-reduce:transition-none", open && "rotate-90")}
          >
            <path d="M5 2.5 9.5 7 5 11.5" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className="text-[17px] leading-snug font-[620]">{title}</span>
            {hint ? <span className="text-[14px] leading-relaxed text-muted-foreground">{hint}</span> : null}
          </span>
        </button>
      </h2>
      <div
        id={id}
        className={cn(
          "grid transition-[grid-template-rows,opacity] duration-200 ease-[cubic-bezier(0.23,1,0.32,1)] motion-reduce:transition-none",
          open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
        // închis: conținutul nu e focalizabil și nu e citit
        inert={!open}
      >
        <div className="min-h-0 overflow-hidden">
          <div className="pb-6">{children}</div>
        </div>
      </div>
    </section>
  );
}
