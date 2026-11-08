"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useState } from "react";
import { Menu } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import type { ShellInfo } from "@/lib/server/queries";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";
import { availableNav, navigationHref } from "./side-nav";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import type { WorkspaceAccount } from "@/lib/operations/types";
import { AccountControls } from "./account-controls";

/** Pe telefon, meniul include aceleași ecrane și setări ca meniul lateral. */
export function MobileMenu({ info, consoleAllowed = false, account }: { info?: ShellInfo; consoleAllowed?: boolean; account: WorkspaceAccount | null }) {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();
  const scenario = useSearchParams().get("scenariu");
  const links = [
    ...availableNav(consoleAllowed, account?.membership.role).map((n) => ({ href: navigationHref(n.href, scenario), label: n.label, on: n.match(pathname) })),
  ];
  const item = "flex h-12 items-center gap-2 rounded-[10px] px-3 text-[16px] hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-ring";
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <button type="button" aria-label="Open navigation" className="grid size-11 place-items-center rounded-full border border-rule text-ink hover:bg-surface-2 md:hidden">
          <Menu aria-hidden="true" size={20} strokeWidth={1.8} />
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="w-[88%] max-w-[360px] gap-5 overflow-y-auto border-rule bg-panel p-5 text-ink">
        <SheetTitle>Menu</SheetTitle>
        <SheetDescription className="sr-only">Workspace navigation, scenario and data sources.</SheetDescription>
        <nav aria-label="Workspace navigation" className="flex flex-col gap-1">
          {links.map((l) => (
            <Link key={l.label} href={l.href} onClick={() => setOpen(false)} aria-current={l.on ? "page" : undefined} className={`${item} ${l.on ? "bg-action/10 font-semibold text-action" : "text-ink-soft"}`}>
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="space-y-3">
          <ThemeToggle />
          {consoleAllowed && info ? <>
            <p className="text-[13px] text-ink-soft">Scenario</p>
            <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
            <Provenance {...info.provenance} />
          </> : null}
          {account ? <AccountControls name={account.name || account.email} /> : <a href="/intra" className={item}>Sign in</a>}
        </div>
      </SheetContent>
    </Sheet>
  );
}
