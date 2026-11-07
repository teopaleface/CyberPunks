import Link from "next/link";
import type { ReactNode } from "react";
import { Wordmark } from "@/components/brand/logo";
import type { ShellInfo } from "@/lib/server/queries";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";
import { SearchButton } from "./search";
import { MobileBottomNav, MobileTabs, SideNav } from "./side-nav";
import { TopTabs } from "./top-tabs";

/**
 * Cadrul consolei (designul „Noapte”, app-01): sus numele și filele, în stânga meniul cu ecranele,
 * jos în meniu scenariul și proveniența datelor. Pe telefon, meniul devine bara de jos (app-14).
 * `fit`: pagina ocupă exact ecranul (harta mare).
 */
export function AppShell({ info, fit = false, children }: { info: ShellInfo; fit?: boolean; children: ReactNode }) {
  return (
    <div className={fit ? "flex h-dvh min-h-[640px] flex-col overflow-hidden" : "flex min-h-dvh flex-col"}>
      <a href="#continut" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-[8px] focus:bg-panel focus:px-3 focus:py-2">
        Sari la conținut
      </a>
      <header className="sticky top-0 z-30 flex h-[60px] shrink-0 items-center border-b border-[#152133] bg-canvas/95 backdrop-blur">
        <div className="flex h-full w-[256px] shrink-0 items-center border-r border-[#152133] px-7 max-md:w-auto max-md:border-r-0 max-md:px-4">
          <Link href={`/?scenariu=${encodeURIComponent(info.scenario)}`} aria-label="Daybreak, planul de mâine" className="rounded-[6px]">
            <Wordmark />
          </Link>
        </div>
        <div className="flex min-w-0 flex-1 items-center gap-4 px-5 max-md:px-3">
          <TopTabs />
          <span className="flex-1" />
          <SearchButton index={info.search} />
        </div>
      </header>
      <div className={fit ? "flex min-h-0 flex-1" : "flex flex-1"}>
        <aside className="sticky top-[60px] flex h-[calc(100dvh-60px)] w-[256px] shrink-0 flex-col justify-between gap-6 overflow-y-auto border-r border-[#152133] px-3.5 py-5 max-md:hidden">
          <SideNav counts={{ review: info.counts.review, alerts: info.counts.alerts + info.counts.notifications }} />
          <div className="space-y-3 px-1">
            <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
            <Provenance {...info.provenance} />
          </div>
        </aside>
        <main id="continut" tabIndex={-1} className={(fit ? "flex min-h-0 min-w-0 flex-1 flex-col" : "min-w-0 flex-1 max-md:pb-20") + " outline-none"}>
          <div className="md:hidden">
            <MobileTabs />
          </div>
          {children}
        </main>
      </div>
      <MobileBottomNav />
    </div>
  );
}
