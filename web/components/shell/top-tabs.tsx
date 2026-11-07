"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { cn } from "cn";

/** Filele de sus (design app-01): consola, rezultatele modelelor, rularea agentului, prezentarea. */
export function TopTabs() {
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const q = scenario ? `?scenariu=${encodeURIComponent(scenario)}` : "";
  const tabs = [
    { href: `/app${q}`, label: "Consola", match: !pathname.startsWith("/modele") && !pathname.startsWith("/rulare") },
    { href: `/modele${q}`, label: "Rezultate", match: pathname.startsWith("/modele") },
    { href: `/rulare${q}`, label: "Rulează", match: pathname.startsWith("/rulare") },
  ];
  return (
    <nav aria-label="Secțiunile" className="flex items-center gap-1.5 max-md:hidden">
      {tabs.map((t) => (
        <Link
          key={t.label}
          href={t.href}
          aria-current={t.match ? "page" : undefined}
          className={cn(
            "rounded-[10px] px-4 py-2 text-[15px] transition-colors duration-150",
            t.match ? "border border-[#2a3a52] bg-[#1b2230] font-[560] text-ink" : "text-ink-soft hover:text-ink",
          )}
        >
          {t.label}
        </Link>
      ))}
      <Link href={`/demo${q}`} target="_blank" className="flex items-center gap-2 rounded-[10px] px-4 py-2 text-[15px] text-ink-soft hover:text-ink">
        Vezi demo
        <ExternalLink aria-hidden="true" size={16} strokeWidth={1.8} />
        <span className="sr-only">(se deschide într-o filă nouă)</span>
      </Link>
    </nav>
  );
}
