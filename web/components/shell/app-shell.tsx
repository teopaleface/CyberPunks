import type { ReactNode } from "react";
import { UserRound } from "lucide-react";
import { Wordmark } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import type { ShellInfo } from "@/lib/server/queries";
import { MobileMenu } from "./mobile-menu";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";
import { MobileBottomNav, SideNav } from "./side-nav";

/** Desktop navigation lives in the sidebar; mobile has a compact brand and menu bar. */
export function AppShell({ info, fit = false, children }: { info: ShellInfo; fit?: boolean; children: ReactNode }) {
  return (
    <div className={fit ? "flex h-dvh min-h-[640px] flex-col overflow-hidden" : "flex min-h-dvh flex-col"}>
      <a href="#continut" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-panel focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-rule bg-canvas/90 px-4 backdrop-blur-xl md:hidden">
        <a href="/" aria-label="Daybreak home" className="rounded-md"><Wordmark /></a>
        <MobileMenu info={info} />
      </header>
      <div className={fit ? "flex min-h-0 flex-1" : "flex flex-1"}>
        <aside className="sticky top-0 flex h-dvh w-[248px] shrink-0 flex-col justify-between gap-8 overflow-y-auto border-r border-rule px-4 py-6 max-md:hidden">
          <div className="space-y-7">
            <a href="/" aria-label="Daybreak home" className="inline-flex min-h-10 items-center rounded-md px-3"><Wordmark /></a>
            <SideNav counts={{ review: info.counts.review, alerts: info.counts.alerts + info.counts.notifications }} />
          </div>
          <div className="space-y-3 border-t border-rule px-1 pt-5">
            <ThemeToggle />
            <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
            <Provenance {...info.provenance} />
            <a href="/intra" className="flex min-h-11 items-center gap-3 rounded-xl px-3 text-[15px] text-ink-soft hover:bg-surface-2 hover:text-ink">
              <UserRound aria-hidden="true" size={20} strokeWidth={1.6} />
              Account
            </a>
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
