import type { ReactNode } from "react";
import { Wordmark } from "@/components/brand/logo";
import type { ShellInfo } from "@/lib/server/queries";
import { MobileMenu } from "./mobile-menu";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";
import { SearchButton } from "./search";
import { MobileBottomNav, SideNav } from "./side-nav";
import { TopTabs } from "./top-tabs";

/**
 * Cadrul consolei păstrează identitatea landingului. Meniul grupează sarcinile,
 * iar scenariul și proveniența datelor rămân vizibile. Pe telefon, toate ecranele sunt în meniu.
 * `fit`: pagina ocupă exact ecranul (harta mare).
 */
export function AppShell({ info, fit = false, children }: { info: ShellInfo; fit?: boolean; children: ReactNode }) {
  return (
    <div className={fit ? "flex h-dvh min-h-[640px] flex-col overflow-hidden" : "flex min-h-dvh flex-col"}>
      <a href="#continut" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-[8px] focus:bg-panel focus:px-3 focus:py-2">
        Sari la conținut
      </a>
      <header className="sticky top-0 z-30 flex h-[72px] shrink-0 items-center border-b border-rule bg-canvas/90 backdrop-blur-xl">
        <div className="flex h-full w-[248px] shrink-0 items-center px-7 max-md:w-auto max-md:px-4">
          {/* prima pagină e site-ul de prezentare (static): o încărcare completă, nu navigare Next */}
          <a href="/" aria-label="Daybreak, prima pagină" className="rounded-[6px]">
            <Wordmark />
          </a>
        </div>
        <div className="flex min-w-0 flex-1 items-center justify-end gap-4 px-5 max-md:px-3">
          <TopTabs />
          <SearchButton index={info.search} />
          <MobileMenu info={info} />
        </div>
      </header>
      <div className={fit ? "flex min-h-0 flex-1" : "flex flex-1"}>
        <aside className="sticky top-[72px] flex h-[calc(100dvh-72px)] w-[248px] shrink-0 flex-col justify-between gap-8 overflow-y-auto border-r border-rule px-4 py-7 max-md:hidden">
          <SideNav counts={{ review: info.counts.review, alerts: info.counts.alerts + info.counts.notifications }} />
          <div className="space-y-3 border-t border-rule px-1 pt-5">
            <p className="px-2 text-[13px] text-muted-foreground">Planul afișat</p>
            <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
            <Provenance {...info.provenance} />
          </div>
        </aside>
        <main id="continut" tabIndex={-1} className={(fit ? "flex min-h-0 min-w-0 flex-1 flex-col" : "min-w-0 flex-1 max-md:pb-20") + " outline-none"}>
          {children}
        </main>
      </div>
      <MobileBottomNav />
    </div>
  );
}
