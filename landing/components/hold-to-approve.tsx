"use client";

import { useEffect, useRef, useState } from "react";

const HOLD_MS = 1200;

/**
 * „Ține apăsat ca să aprobi”: aprobarea unui om nu se dă dintr-un clic scăpat. Umplerea merge liniar
 * cât ții apăsat (mouse, deget, Space sau Enter) și se retrage repede dacă dai drumul. Pe pagină nu se
 * trimite nimic: e o demonstrație, iar „Undo” readuce cazul în coadă.
 */
export function HoldToApprove() {
  const [state, setState] = useState<"idle" | "holding" | "approved" | "skipped">("idle");
  const timer = useRef<number | null>(null);

  const stop = () => {
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = null;
    setState((s) => (s === "holding" ? "idle" : s));
  };
  const start = () => {
    if (state !== "idle") return;
    setState("holding");
    timer.current = window.setTimeout(() => {
      timer.current = null;
      setState("approved");
    }, HOLD_MS);
  };
  useEffect(() => () => stop(), []);

  if (state === "approved" || state === "skipped") {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3" role="status">
        <p className="flex items-center gap-2 text-[1rem] text-ink">
          <span aria-hidden className={`grid size-6 place-items-center rounded-full ${state === "approved" ? "bg-ppc-blue text-night" : "bg-tile-2 text-ink-2"}`}>
            {state === "approved" ? "✓" : "–"}
          </span>
          {state === "approved" ? "Approved. Logged as a human decision." : "Skipped. The case stays in the queue."}
        </p>
        <button
          type="button"
          onClick={() => setState("idle")}
          className="rounded-full px-3 py-1.5 text-[0.92rem] text-ppc-blue transition-colors hover:bg-tile-2"
        >
          Undo
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        type="button"
        aria-label="Hold to approve"
        data-holding={state === "holding" ? "" : undefined}
        onPointerDown={(e) => {
          e.currentTarget.setPointerCapture(e.pointerId);
          start();
        }}
        onPointerUp={stop}
        onPointerCancel={stop}
        onKeyDown={(e) => {
          if ((e.key === " " || e.key === "Enter") && !e.repeat) {
            e.preventDefault();
            start();
          }
        }}
        onKeyUp={(e) => {
          if (e.key === " " || e.key === "Enter") stop();
        }}
        onContextMenu={(e) => e.preventDefault()}
        className="group relative h-12 touch-none overflow-hidden rounded-full bg-tile-2 px-6 text-[1.02rem] font-medium text-ink transition-transform duration-150 ease-out select-none active:scale-[0.97]"
      >
        <span>Hold to approve</span>
        <span
          aria-hidden
          className="absolute inset-0 flex items-center justify-center bg-ppc-blue text-night [clip-path:inset(0_100%_0_0)] transition-[clip-path] duration-200 ease-out group-data-[holding]:[clip-path:inset(0_0_0_0)] group-data-[holding]:duration-[1200ms] group-data-[holding]:ease-linear"
        >
          Hold to approve
        </span>
      </button>
      <button
        type="button"
        onClick={() => setState("skipped")}
        className="h-12 rounded-full px-5 text-[1.02rem] text-ink-2 transition-colors duration-150 hover:bg-tile-2 hover:text-ink"
      >
        Skip
      </button>
    </div>
  );
}
