import type { ReactNode } from "react";
import { Wordmark } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/theme/theme-toggle";
import type { ShellInfo } from "@/lib/server/queries";
import { currentUser, toMembership } from "@/lib/server/accounts";
import { mayReadConsole } from "@/lib/operations/policy";
import { DEFAULT_SCENARIO } from "@/lib/data";
import { AccountControls } from "./account-controls";
import { AgentDock } from "./agent-dock";
import { MobileMenu } from "./mobile-menu";
import { Provenance } from "./provenance";
import { ScenarioSwitch } from "./scenario-switch";
import { MobileBottomNav, SideNav } from "./side-nav";

/** Desktop navigation lives in the sidebar; mobile has a compact brand and menu bar. */
export async function AppShell({ info, scenario, fit = false, children }: { info?: ShellInfo; scenario?: string; fit?: boolean; children: ReactNode }) {
  const user = await currentUser();
  const consoleAllowed = Boolean(user && mayReadConsole(user));
  // Never serialize global scenario metadata or counts into a restricted role's client props.
  const consoleInfo = consoleAllowed ? info : undefined;
  const account = user ? { id: user.id, email: user.email, name: user.full_name, membership: toMembership(user) } : null;
  return (
    <div className={fit ? "flex h-dvh min-h-[640px] flex-col overflow-hidden" : "flex min-h-dvh flex-col"}>
      <a href="#continut" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-panel focus:px-3 focus:py-2">
        Skip to content
      </a>
      <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-rule bg-canvas/90 px-4 backdrop-blur-xl md:hidden">
        <a href="/" aria-label="Daybreak home" className="rounded-md"><Wordmark /></a>
        <MobileMenu info={consoleInfo} consoleAllowed={consoleAllowed} account={account} />
      </header>
      <div className={fit ? "flex min-h-0 flex-1" : "flex flex-1"}>
        <aside className="sticky top-0 flex h-dvh w-[248px] shrink-0 flex-col justify-between gap-8 overflow-y-auto border-r border-rule px-4 py-6 max-md:hidden">
          <div className="space-y-7">
            <a href="/" aria-label="Daybreak home" className="inline-flex min-h-10 items-center rounded-md px-3"><Wordmark /></a>
            <SideNav consoleAllowed={consoleAllowed} role={account?.membership.role} counts={consoleInfo ? { review: consoleInfo.counts.review, alerts: consoleInfo.counts.alerts + consoleInfo.counts.notifications } : undefined} />
          </div>
          <div className="space-y-3 border-t border-rule px-1 pt-5">
            <ThemeToggle />
            {consoleInfo ? <>
              <ScenarioSwitch scenario={consoleInfo.scenario} scenarios={consoleInfo.scenarios} />
              <Provenance {...consoleInfo.provenance} />
            </> : null}
            {account ? <AccountControls name={account.name || account.email} /> : <a href="/intra" className="block px-3 py-2 text-ink-soft">Sign in</a>}
          </div>
        </aside>
        <main id="continut" tabIndex={-1} className={(fit ? "flex min-h-0 min-w-0 flex-1 flex-col" : "min-w-0 flex-1 max-md:pb-20") + " outline-none"}>
          {children}
        </main>
      </div>
      <MobileBottomNav consoleAllowed={consoleAllowed} role={account?.membership.role} />
      {account ? <AgentDock account={account} scenario={consoleInfo?.scenario ?? scenario ?? DEFAULT_SCENARIO} /> : null}
    </div>
  );
}
