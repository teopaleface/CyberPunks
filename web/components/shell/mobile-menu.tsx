"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";
import { ExternalLink, Menu } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import type { ShellInfo } from "@/lib/server/queries";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";

/** Meniul de pe telefon: filele de sus, scenariul și proveniența datelor (pe desktop stau în antet și în meniul din stânga). */
export function MobileMenu({ info }: { info: ShellInfo }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const q = scenario ? `?scenariu=${encodeURIComponent(scenario)}` : "";
  const links = [
    { href: `/app${q}`, label: "Consola", on: !pathname.startsWith("/modele") && !pathname.startsWith("/rulare") },
    { href: `/modele${q}`, label: "Rezultate", on: pathname.startsWith("/modele") },
    { href: `/rulare${q}`, label: "Rulează", on: pathname.startsWith("/rulare") },
  ];
  const item = "flex h-12 items-center gap-2 rounded-[10px] px-3 text-[16px] hover:bg-[#0f1a2b] focus-visible:outline-2 focus-visible:outline-ring";
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button type="button" aria-label="Meniu: secțiuni, scenariu și proveniența datelor" className="grid size-10 place-items-center rounded-[10px] border border-[#2a3a52] text-ink hover:bg-[#0f1a2b] md:hidden">
          <Menu aria-hidden="true" size={20} strokeWidth={1.8} />
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[88%] max-w-[360px] gap-5 border-rule bg-panel p-5 text-ink">
        <SheetTitle>Meniu</SheetTitle>
        <SheetDescription className="sr-only">Secțiunile consolei, scenariul și proveniența datelor.</SheetDescription>
        <nav aria-label="Secțiunile" className="flex flex-col gap-1">
          {links.map((l) => (
            <Link key={l.label} href={l.href} onClick={() => setOpen(false)} aria-current={l.on ? "page" : undefined} className={`${item} ${l.on ? "bg-[#1b2434] font-[600]" : "text-ink-soft"}`}>
              {l.label}
            </Link>
          ))}
          <Link href={`/demo${q}`} target="_blank" className={`${item} text-ink-soft`}>
            Vezi demo
            <ExternalLink aria-hidden="true" size={16} strokeWidth={1.8} />
            <span className="sr-only">(se deschide într-o filă nouă)</span>
          </Link>
        </nav>
        <div className="space-y-3">
          <p className="text-[13px] text-ink-soft">Scenariul</p>
          <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
          <Provenance {...info.provenance} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
