"use client";

import { ArrowRight, ChevronDown, SlidersHorizontal } from "lucide-react";
import Link from "next/link";
import { useState, type ReactNode } from "react";
import { cn } from "cn";
import { ITEMS, type HomeFilter } from "./filters";

/** Filtrele se aplică detaliilor; propunerea și decizia următoare rămân vizibile. */
const SHOW: Record<HomeFilter, string[]> = {
  toate: ["figures", "map", "crews", "gantt", "meter", "alerts"],
  lucrari: ["figures", "question", "meter"],
  echipe: ["crews", "gantt"],
  trasee: ["crews", "gantt"],
  posturi: ["map"],
  alerte: ["alerts", "question"],
  vreme: ["question"],
  tensiune: ["question"],
};

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
  plan,
  figures,
  map,
  crews,
  question,
  meter,
  gantt,
  alerts,
}: {
  initial: HomeFilter;
  suffix: string;
  kpis: ReactNode;
  plan: ReactNode;
  figures: ReactNode;
  map: ReactNode;
  crews: ReactNode;
  question: { default: ReactNode; storm: ReactNode; voltage: ReactNode };
  meter: ReactNode;
  gantt: ReactNode;
  alerts: ReactNode;
}) {
  const [filter, setFilter] = useState<HomeFilter>(initial);
  const shown = new Set(SHOW[filter]);
  const body = filter === "vreme" ? question.storm : filter === "tensiune" ? question.voltage : question.default;
  const more = MORE[filter];

  const pick = (id: HomeFilter) => {
    setFilter(id);
    const url = new URL(window.location.href);
    if (id === "toate") url.searchParams.delete("filtru");
    else url.searchParams.set("filtru", id);
    window.history.replaceState(null, "", url);
  };

  return (
    <div className="flex flex-col">
      <div className="order-1 mt-6 grid items-start gap-6 md:order-2 xl:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)]">
        <section aria-label="Următoarea decizie" className="@container min-w-0 rounded-2xl border border-rule bg-panel p-6 sm:p-7">
          {question.default}
        </section>
        <section aria-label="Planul propus" className="@container min-w-0 rounded-2xl border border-rule bg-panel p-6 sm:p-7 xl:order-first">
          {plan}
        </section>
      </div>

      <div className="order-2 mt-7 md:order-1">{kpis}</div>

      <details id="detalii-plan" open={initial !== "toate"} className="group order-3 mt-7 scroll-mt-24 rounded-2xl border border-rule bg-panel">
        <summary className="flex cursor-pointer list-none items-center gap-3 rounded-2xl p-5 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ring sm:p-6 [&::-webkit-details-marker]:hidden">
          <SlidersHorizontal aria-hidden="true" size={20} className="shrink-0 text-ink-soft" />
          <span className="min-w-0 flex-1">
            <span className="block text-[17px] font-[550]">Detalii despre plan</span>
            <span className="mt-1 block text-[14px] leading-relaxed text-ink-soft">Lucrări, echipe, trasee, posturi și alerte. Filtrează ce vrei să verifici.</span>
          </span>
          <ChevronDown aria-hidden="true" size={20} className="shrink-0 text-ink-soft transition-transform group-open:rotate-180" />
        </summary>
        <div className="border-t border-rule p-5 sm:p-6">
          <div role="group" aria-label="Filtrează detaliile planului" className="flex flex-wrap gap-2">
            {ITEMS.map((i) => (
              <button
                key={i.id}
                type="button"
                aria-pressed={filter === i.id}
                onClick={() => pick(i.id)}
                className={cn(
                  "min-h-10 rounded-lg border px-4 py-2 text-[14px] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring",
                  filter === i.id ? "border-[#ffc502] bg-[#ffc502] text-black" : "border-rule bg-surface-2 text-ink-soft hover:bg-white/10 hover:text-ink",
                )}
              >
                {i.label}
              </button>
            ))}
          </div>

          <div className="mt-6 grid items-start gap-5 lg:grid-cols-2">
            {shown.has("figures") ? <div className="min-w-0 lg:col-span-2">{figures}</div> : null}
            {shown.has("map") ? <div className="min-w-0">{map}</div> : null}
            {shown.has("crews") ? <div className="min-w-0">{crews}</div> : null}
            {shown.has("alerts") ? <div className="min-w-0 lg:col-span-2">{alerts}</div> : null}
            {shown.has("question") ? <section aria-label="Caz de verificat" className="@container min-w-0 rounded-2xl border border-rule bg-panel p-6">{body}</section> : null}
            {shown.has("meter") && meter ? <div className="min-w-0">{meter}</div> : null}
            {shown.has("gantt") ? <div className="min-w-0 lg:col-span-2">{gantt}</div> : null}
          </div>

          {more ? (
            <Link href={`${more.href}${suffix}`} className="mt-6 inline-flex min-h-10 items-center gap-2 rounded-lg border border-rule bg-surface-2 px-4 py-2 text-[14px] text-ink hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
              {more.label}
              <ArrowRight aria-hidden="true" size={16} />
            </Link>
          ) : null}
        </div>
      </details>
    </div>
  );
}
