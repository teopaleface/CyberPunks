"use client";

import { useId } from "react";
import { englishText } from "@/lib/english";
import { Popover } from "radix-ui";
import { PROVENANCE_SHORT_RO, SOURCE_LABEL_RO } from "@/lib/data/labels";
import type { DataSource } from "@/lib/data/types";

/** Pătratul hașurat: semnul „date sintetice”, același în toată consola. */
export function SyntheticGlyph({ size = 16 }: { size?: number }) {
  // un id propriu pe fiecare semn: cu un id comun, un semn ascuns (display: none) lua hașura tuturor
  const id = `syn-hatch-${useId().replace(/[^a-zA-Z0-9_-]/g, "")}`;
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" className="shrink-0">
      <defs>
        <pattern id={id} width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="1.6" height="4" fill="currentColor" />
        </pattern>
      </defs>
      <rect x=".5" y=".5" width="15" height="15" fill={`url(#${id})`} stroke="currentColor" />
    </svg>
  );
}

const DOT: Record<DataSource, string> = {
  api: "bg-ok",
  demo: "bg-idle",
  fixtures: "bg-src-c",
};

/**
 * Transparența datelor, mereu vizibilă: ce e sintetic și de unde vine planul afișat
 * (agentul în direct, ultimul plan salvat sau datele de test). Explicația se deschide la clic sau la atingere.
 */
export function Provenance({
  source,
  degradedReason,
  detail,
  syntheticItems,
  totalItems,
}: {
  source: DataSource;
  degradedReason?: string;
  detail?: string;
  syntheticItems: number;
  totalItems: number;
}) {
  const allSynthetic = totalItems > 0 && syntheticItems === totalItems;
  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <button
          type="button"
          aria-haspopup="dialog"
          className="flex w-full flex-col items-start gap-1 rounded-[10px] border border-rule px-3 py-2.5 text-left text-[13.5px] hover:bg-surface-2"
        >
          <span className="flex items-center gap-2 font-[560]">
            <SyntheticGlyph size={14} />
            {totalItems === 0 ? "No plan loaded" : allSynthetic ? "Synthetic data" : syntheticItems > 0 ? "Includes synthetic data" : "Data sources"}
          </span>
          <span className="flex items-center gap-2 text-ink-soft">
            <span className={`size-2 rounded-full ${DOT[source]}`} aria-hidden="true" />
            {PROVENANCE_SHORT_RO[source]}
          </span>
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          side="right"
          align="end"
          sideOffset={8}
          collisionPadding={12}
          className="z-[60] max-w-[360px] rounded-[10px] border border-rule bg-panel p-3.5 text-[14px] leading-snug text-ink shadow-lg outline-hidden"
        >
        <p>
          Meters, substations, depots and crews are synthetic, placed on a real map. Weather and test networks use public sources cited on each work item.
        </p>
        <p className="mt-2">
          Plan source: <b>{SOURCE_LABEL_RO[source]}</b>
          {detail ? <span className="block opacity-80">{englishText(detail)}</span> : null}
        </p>
        {degradedReason ? <p className="mt-2">{englishText(degradedReason)}</p> : null}
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}
