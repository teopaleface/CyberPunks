import Link from "next/link";
import type { ReactNode } from "react";
import { Wordmark } from "@/components/brand/logo";
import type { ShellInfo } from "@/lib/server/queries";
import { NavTabs } from "./nav-tabs";
import { Provenance } from "./provenance";
import { RunAgentButton } from "./run-agent";
import { ScenarioSwitch } from "./scenario-switch";

/**
 * Cadrul fiecărui ecran: antetul (semn, ecrane, scenariu, proveniență, „Rulează agentul”) și conținutul.
 * `fit`: ecranul ocupă exact fereastra (planul, pe proiector); altfel pagina curge normal.
 */
export function AppShell({ info, fit = false, children }: { info: ShellInfo; fit?: boolean; children: ReactNode }) {
  const scenarioLabel = info.scenarios.find((s) => s.id === info.scenario)?.label ?? info.scenario;
  return (
    <div className={fit ? "flex h-dvh min-h-[720px] flex-col overflow-hidden" : "flex min-h-dvh flex-col"}>
      <a
        href="#continut"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-panel focus:px-3 focus:py-2"
      >
        Sari la conținut
      </a>
      <header className="flex h-16 shrink-0 items-center gap-6 border-b border-rule bg-panel pr-7 pl-7">
        <Link href="/" aria-label="Tura de mâine, planul de mâine" className="rounded-[4px]">
          <Wordmark />
        </Link>
        <span className="h-7 w-px bg-rule" aria-hidden="true" />
        <NavTabs review={info.counts.review} alerts={info.counts.alerts + info.counts.notifications} />
        <span className="flex-1" />
        <ScenarioSwitch scenario={info.scenario} scenarios={info.scenarios} />
        <Provenance {...info.provenance} />
        <RunAgentButton scenario={info.scenario} scenarioLabel={scenarioLabel} />
      </header>
      <div id="continut" className={fit ? "flex min-h-0 flex-1 flex-col" : "flex-1"}>
        {children}
      </div>
    </div>
  );
}
