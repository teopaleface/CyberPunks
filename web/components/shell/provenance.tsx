"use client";

import { useId } from "react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
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
 * (agentul în direct, ultimul plan salvat sau datele de test). Motivul apare la trecerea cu mouse-ul.
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
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          className="flex w-full flex-col items-start gap-1 rounded-[10px] border border-[#2a3a52] px-3 py-2.5 text-left text-[13.5px] hover:bg-[#0f1a2b]"
        >
          <span className="flex items-center gap-2 font-[560]">
            <SyntheticGlyph size={14} />
            {allSynthetic || totalItems === 0 ? "Date sintetice" : `Date sintetice: ${syntheticItems} din ${totalItems}`}
          </span>
          <span className="flex items-center gap-2 text-ink-soft">
            <span className={`size-2 rounded-full ${DOT[source]}`} aria-hidden="true" />
            {PROVENANCE_SHORT_RO[source]}
          </span>
        </button>
      </TooltipTrigger>
      <TooltipContent side="right" align="end" className="max-w-[360px] text-[14px] leading-snug">
        <p>
          Contoarele, posturile de transformare, bazele și echipele sunt sintetice, puse pe harta reală. Vremea și
          rețelele de test vin din surse publice, citate la fiecare lucrare.
        </p>
        <p className="mt-2">
          Planul vine din: <b>{SOURCE_LABEL_RO[source]}</b>
          {detail ? <span className="block opacity-80">{detail}</span> : null}
        </p>
        {degradedReason ? <p className="mt-2">{degradedReason}</p> : null}
      </TooltipContent>
    </Tooltip>
  );
}
