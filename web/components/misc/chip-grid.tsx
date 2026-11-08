"use client";

import { useState, type ReactNode } from "react";
import { cn } from "cn";
import { Chips } from "@/components/ds/chips";
import type { Tone } from "@/components/ds";

export interface GridCard {
  id: string;
  /** Filtrele în care apare cardul (în afară de „Toate”). */
  tags: string[];
  /** Clasele de lățime în grilă, de exemplu `lg:col-span-3`. */
  span: string;
  /** Optional width when a filter narrows the grid. */
  filteredSpan?: string;
  node: ReactNode;
}

/** Filtrele-pastilă de sus și grila de carduri pe care o filtrează. Cardurile se fac pe server. */
export function ChipGrid({
  chips,
  cards,
  label,
  columns = "lg:grid-cols-6",
}: {
  chips: { id: string; label: string; tone?: Tone }[];
  cards: GridCard[];
  label: string;
  columns?: string;
}) {
  const [value, setValue] = useState("all");
  const shown = value === "all" ? cards : cards.filter((c) => c.tags.includes(value));
  return (
    <>
      <Chips label={label} items={[{ id: "all", label: "All" }, ...chips]} value={value} onChange={setValue} className="mt-5" />
      <p role="status" className="sr-only">
        {shown.length} cards shown
      </p>
      <div className={cn("mt-5 grid grid-cols-1 items-start gap-5", columns)}>
        {shown.length ? (
          shown.map((c) => (
            <div key={c.id} className={cn("flex min-w-0 flex-col [&>*]:flex-1", shown.length === 1 ? "col-span-full" : value === "all" ? c.span : c.filteredSpan ?? c.span)}>
              {c.node}
            </div>
          ))
        ) : (
          <p className="text-[16px] text-ink-soft col-span-full">No results for this filter and scenario.</p>
        )}
      </div>
    </>
  );
}
