import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import { connection } from "next/server";
import { Suspense } from "react";
import { PageTitle } from "@/components/ds";
import { Disclosure } from "@/components/simple/disclosure";
import { AppShell } from "@/components/shell/app-shell";
import { RunAgentButton } from "@/components/shell/run-agent";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { fmtMoment, sentence } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { AlertList } from "./_components/alert-list";
import { MessageList } from "./_components/message-list";
import { AlertsBoard } from "./_components/board";
import { getRemedies } from "@/lib/data/remedies";

const WRAP = "mx-auto w-full max-w-[1440px] px-8 pt-7 pb-14 max-md:px-4";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function AlertsPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<AlertsSkeleton />}>
      <Alerts searchParams={searchParams} />
    </Suspense>
  );
}

async function Alerts({ searchParams }: { searchParams: SearchParams }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, remedies] = await Promise.all([loadShellInfo(scenario), getRemedies(scenario).catch(() => null)]);
  const data = view.data;
  const scenarioLabel = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;

  return (
    <AppShell info={info}>
      <div className={WRAP}>
        <PageTitle title="Alerts and messages" subtitle="Operational alerts and delivery status." />

        {data ? (
          <>
            <AlertsBoard
              alerts={data.plan.alerts ?? []}
              notifications={data.plan.notifications ?? []}
              workItemsById={data.workItemsById}
              decisionsByWorkItemId={data.decisionsByWorkItemId}
              remedies={remedies?.data ?? []}
              scenario={scenario}
            />
            <Disclosure title="All alerts and messages" hint="Full list with linked work items" className="mt-8">
              <div className="overflow-hidden rounded-[18px] border border-rule bg-panel">
                <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.12fr)_minmax(0,1fr)]">
                  <div className="min-w-0 xl:border-r xl:border-rule">
                    <AlertList
                      alerts={data.plan.alerts ?? []}
                      workItemsById={data.workItemsById}
                      decisionsByWorkItemId={data.decisionsByWorkItemId}
                      scenario={scenario}
                    />
                  </div>
                  <MessageList
                    notifications={data.plan.notifications ?? []}
                    workItemsById={data.workItemsById}
                    decisionsByWorkItemId={data.decisionsByWorkItemId}
                    scenario={scenario}
                  />
                </div>
              </div>
              <p className="mt-3 text-[13.5px] text-muted-foreground">Plan generated {fmtMoment(data.plan.generated_at)}.</p>
            </Disclosure>
          </>
        ) : (
          <div className="mt-6 max-w-[720px] rounded-[18px] border border-rule bg-panel p-8">
            <h2 className="text-[24px] font-[650]">No plan yet for &quot;{englishText(scenarioLabel)}&quot;</h2>
            <p className="mt-3 text-[16.5px] leading-relaxed text-ink-soft">
              Run the agent to prepare alerts and messages, or select another scenario in the menu.
            </p>
            <div className="mt-5">
              <RunAgentButton scenario={scenario} scenarioLabel={englishText(scenarioLabel)} />
            </div>
          </div>
        )}

        <p className="pt-4 text-[13.5px] text-muted-foreground">
          Plan source: {englishText(SOURCE_LABEL_RO[view.source])}
          {view.degradedReason ? `. ${englishText(sentence(view.degradedReason))}` : "."}
        </p>
      </div>
    </AppShell>
  );
}

function AlertsSkeleton() {
  return (
    <div role="status" className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Loading alerts and messages…">
      <div className="h-16 border-b border-rule bg-panel" />
      <div className={WRAP}>
        <div className="h-[72px]" />
        <div className="mt-5 grid grid-cols-1 gap-5 lg:grid-cols-2">
          <div className="h-[300px] animate-pulse rounded-[18px] bg-panel" />
          <div className="h-[300px] animate-pulse rounded-[18px] bg-panel" />
        </div>
      </div>
    </div>
  );
}
