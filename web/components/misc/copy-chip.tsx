"use client";

import { CheckIcon, CopyIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { cn } from "cn";

/** Text scurt într-un chenar, cu buton de copiere (versiunea modelului, ID-uri). */
export function CopyChip({ text, label, className }: { text: string; label: string; className?: string }) {
  const [done, setDone] = useState(false);
  const [failed, setFailed] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setFailed(false);
    } catch {
      setDone(false);
      setFailed(true);
    }
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      setDone(false);
      setFailed(false);
    }, 1800);
  };
  return (
    <span className={cn("inline-flex max-w-full items-center gap-2 rounded-[8px] border border-rule bg-surface-2 py-1 pr-1 pl-2.5 text-[14px]", className)}>
      <span translate="no" className="min-w-0 truncate tabular-nums" title={text}>
        {text}
      </span>
      <button
        type="button"
        onClick={copy}
        aria-label={done ? `${label}: copied` : label}
        className="inline-grid size-7 shrink-0 place-items-center rounded-[6px] text-ink-soft transition-colors duration-150 hover:bg-accent hover:text-ink focus-visible:outline-2 focus-visible:outline-ring"
      >
        {done ? <CheckIcon size={15} aria-hidden="true" className="text-ok-ink" /> : <CopyIcon size={15} aria-hidden="true" />}
      </button>
      <span role="status" className="sr-only">
        {done ? "Copied." : failed ? "Copy failed." : ""}
      </span>
    </span>
  );
}
