"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowUpRight, Play, UserRound } from "lucide-react";

/** O singură navigare pentru ecrane, în stânga. Antetul păstrează doar comenzile generale. */
export function TopTabs() {
  const scenario = useSearchParams().get("scenariu");
  const q = scenario ? `?scenariu=${encodeURIComponent(scenario)}` : "";
  return (
    <div className="flex min-w-0 flex-1 items-center gap-4 max-md:hidden">
      <span className="text-[14px] text-muted-foreground">Consola dispecerului</span>
      <nav aria-label="Comenzi generale" className="ml-auto flex items-center gap-2">
        <a href="/" className="flex min-h-10 items-center gap-1.5 rounded-full px-3 text-[14px] text-ink-soft hover:bg-surface-2 hover:text-ink">
          Vezi site-ul
          <ArrowUpRight aria-hidden="true" size={15} />
        </a>
        <Link href={`/rulare${q}`} className="flex min-h-10 items-center gap-2 rounded-full border border-rule px-4 text-[14px] text-ink hover:border-ink-soft hover:bg-surface-2">
          <Play aria-hidden="true" size={15} />
          Rulare agent
        </Link>
        <a href="/intra" aria-label="Contul meu" className="grid size-10 place-items-center rounded-full border border-rule text-ink-soft hover:bg-surface-2 hover:text-ink">
          <UserRound aria-hidden="true" size={18} />
        </a>
      </nav>
    </div>
  );
}
