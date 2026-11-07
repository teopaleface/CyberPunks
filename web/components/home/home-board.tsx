"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import { Chips } from "@/components/ds/chips";
import { cn } from "cn";
import { ITEMS, type HomeFilter } from "./filters";

/** Ce secțiuni arată fiecare filtru. */
const SHOW: Record<HomeFilter, string[]> = {
  toate: ["kpis", "map", "crews", "question", "gantt"],
  lucrari: ["kpis", "question"],
  echipe: ["crews", "gantt"],
  trasee: ["crews", "gantt"],
  posturi: ["map"],
  alerte: ["alerts", "question"],
  vreme: ["question"],
  tensiune: ["question"],
};

/** Unde duce linkul de sub filtru (pagina cu toate detaliile). */
const MORE: Partial<Record<HomeFilter, { href: string; label: string }>> = {
  lucrari: { href: "/lucrari", label: "Vezi toate lucrările" },
  echipe: { href: "/harta", label: "Vezi traseele pe hartă" },
  trasee: { href: "/harta", label: "Vezi traseele pe hartă" },
  posturi: { href: "/posturi", label: "Vezi toate posturile" },
  alerte: { href: "/alerte", label: "Vezi toate alertele" },
  vreme: { href: "/harta", label: "Vezi zonele de furtună pe hartă" },
  tensiune: { href: "/lucrari", label: "Vezi lucrările de tensiune" },
};

export function HomeBoard({
  initial,
  suffix,
  kpis,
  map,
  crews,
  question,
  gantt,
  alerts,
}: {
  initial: HomeFilter;
  /** `?scenariu=…` pentru linkuri. */
  suffix: string;
  kpis: ReactNode;
  map: ReactNode;
  crews: ReactNode;
  question: { bodies: { default: ReactNode; storm: ReactNode | null; voltage: ReactNode | null }; rest: ReactNode };
  gantt: ReactNode;
  alerts: ReactNode;
}) {
  const [filter, setFilter] = useState<HomeFilter>(initial);
  const all = filter === "toate";
  const shown = new Set(SHOW[filter]);
  const body = filter === "vreme" ? (question.bodies.storm ?? question.bodies.default) : filter === "tensiune" ? (question.bodies.voltage ?? question.bodies.default) : question.bodies.default;
  const more = MORE[filter];

  const pick = (id: HomeFilter) => {
    setFilter(id);
    const url = new URL(window.location.href);
    if (id === "toate") url.searchParams.delete("filtru");
    else url.searchParams.set("filtru", id);
    window.history.replaceState(null, "", url);
  };

  return (
    <>
      <Chips
        label="Ce arăt pe ecran"
        items={ITEMS}
        value={filter}
        onChange={pick}
        className="mt-5 max-md:hidden"
      />
      <div role="group" aria-label="Ce arăt pe ecran" className="mt-4 hidden gap-2 overflow-x-auto pb-1 max-md:flex">
        {ITEMS.map((i) => (
          <button
            key={i.id}
            type="button"
            aria-pressed={filter === i.id}
            onClick={() => pick(i.id)}
            className={cn(
              "h-9 shrink-0 rounded-full border px-4 text-[14px] whitespace-nowrap",
              filter === i.id ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-[#2a3a52] text-ink",
            )}
          >
            {i.label}
          </button>
        ))}
      </div>

      {shown.has("kpis") ? <div className="mt-5">{kpis}</div> : null}
      {shown.has("alerts") ? <div className="mt-5">{alerts}</div> : null}

      <div
        className={cn(
          "mt-5 grid gap-5",
          all ? "lg:grid-cols-[minmax(0,1fr)_minmax(0,0.9fr)_minmax(0,1fr)]" : "lg:grid-cols-2",
        )}
      >
        {shown.has("map") ? <div className={cn("min-w-0", all && "lg:col-start-1 lg:row-start-1")}>{map}</div> : null}
        {shown.has("crews") ? <div className={cn("min-w-0", all && "lg:col-start-2 lg:row-start-1")}>{crews}</div> : null}
        {shown.has("question") ? (
          <div className={cn("min-w-0", all && "lg:col-start-3 lg:row-span-2 lg:row-start-1", !all && "lg:col-span-2 lg:mx-auto lg:w-full lg:max-w-[520px]")}>
            <section className="@container flex h-full flex-col rounded-[14px] border border-rule bg-panel">
              {body}
              {question.rest}
            </section>
          </div>
        ) : null}
        {shown.has("gantt") ? <div className={cn("min-w-0", all && "lg:col-span-2 lg:col-start-1 lg:row-start-2", !all && "lg:col-span-2")}>{gantt}</div> : null}
      </div>

      {more ? (
        <p className="mt-5">
          <Link href={`${more.href}${suffix}`} className="inline-flex items-center gap-2 text-[15px] font-[560] text-[#8db8ff] hover:underline focus-visible:outline-2 focus-visible:outline-ring">
            {more.label}
            <ArrowRight aria-hidden="true" size={17} />
          </Link>
        </p>
      ) : null}
    </>
  );
}
