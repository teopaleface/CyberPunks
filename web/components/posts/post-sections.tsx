"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Chips } from "@/components/ds/chips";
import type { Tone } from "@/components/ds";
import { cn } from "cn";
import type { PostSection } from "@/lib/posts-view";

export interface SectionDef {
  id: Exclude<PostSection, "toate">;
  /** Ce card(uri) arată fiecare filă; „stare” e vizibil mereu la „Toate” și la fila Bilanț. */
  node: ReactNode;
  className?: string;
  /** Filele la care apare cardul (pe lângă „Toate”). */
  also?: Exclude<PostSection, "toate">[];
}

const CHIPS: { id: PostSection; label: string; tone?: Tone }[] = [
  { id: "toate", label: "Toate" },
  { id: "bilant", label: "Bilanț", tone: "blue" },
  { id: "contoare", label: "Contoare", tone: "violet" },
  { id: "tensiune", label: "Tensiune", tone: "amber" },
  { id: "cauze", label: "Cauze", tone: "blue" },
  { id: "remediere", label: "Remediere", tone: "violet" },
  { id: "lucrari", label: "Lucrări", tone: "amber" },
  { id: "jurnal", label: "Jurnal", tone: "blue" },
];

/** Filtrele paginii postului: ascund cardurile (fără să le scoată din pagină), iar alegerea stă în URL. */
export function PostSections({ sections, stare, initial }: { sections: SectionDef[]; stare: ReactNode; initial: PostSection }) {
  const [section, setSection] = useState<PostSection>(initial);
  const choose = (s: PostSection) => {
    setSection(s);
    const url = new URL(window.location.href);
    if (s === "toate") url.searchParams.delete("sectiune");
    else url.searchParams.set("sectiune", s);
    window.history.replaceState(window.history.state, "", url);
  };
  // „Analizează” (#cauze): arată cardul Cauze, chiar dacă o filă îl ascunde, apoi derulează la el
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      const a = e.target instanceof Element ? e.target.closest('a[href="#cauze"]') : null;
      if (!a) return;
      e.preventDefault();
      setSection("cauze");
      const url = new URL(window.location.href);
      url.searchParams.set("sectiune", "cauze");
      window.history.replaceState(window.history.state, "", url);
      window.setTimeout(() => document.getElementById("cauze")?.scrollIntoView({ block: "start" }), 0);
    };
    document.addEventListener("click", onClick);
    return () => document.removeEventListener("click", onClick);
  }, []);
  return (
    <>
      <Chips label="Părți ale paginii" items={CHIPS} value={section} onChange={choose} className="mt-5" />
      <div className="mt-5 grid grid-cols-[minmax(0,1fr)] gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.35fr)_minmax(0,1fr)]">
        <div className={cn("contents", section !== "toate" && section !== "bilant" && "hidden")}>{stare}</div>
        {sections.map((s) => {
          const show = section === "toate" || section === s.id || s.also?.includes(section as never);
          return (
            <div key={s.id} className={cn("min-w-0", s.className, !show && "hidden")}>
              {s.node}
            </div>
          );
        })}
      </div>
    </>
  );
}
