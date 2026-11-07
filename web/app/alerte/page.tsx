import { connection } from "next/server";
import { Suspense } from "react";
import { Wordmark } from "@/components/brand/logo";
import { AppShell } from "@/components/shell/app-shell";
import { RunAgentButton } from "@/components/shell/run-agent";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { fmtMoment, sentence } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { AlertList } from "./_components/alert-list";
import { MessageList } from "./_components/message-list";
import { BatteryOffers } from "./_components/battery-offers";
import { getRemedies } from "@/lib/data/remedies";
import { DemoStamp } from "./_components/parts";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

export default function AlertsPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<AlertsSkeleton />}>
      <Alerts searchParams={searchParams} />
    </Suspense>
  );
}

async function Alerts({ searchParams }: { searchParams: SearchParams }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, remedies] = await Promise.all([loadShellInfo(scenario), getRemedies(scenario).catch(() => null)]);
  const data = view.data;
  const scenarioLabel = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;

  return (
    <AppShell info={info}>
      <section className="border-b border-rule bg-panel">
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3 px-7 pt-5 pb-4">
          <div className="min-w-0">
            <h1 className="text-[26px] leading-tight font-[650] tracking-[-0.005em]">Alerte și mesaje</h1>
            <p className="mt-1 text-[16px] leading-[1.75] text-muted-foreground">
              Alertele ajung la dispecerat și la echipe. Mesajele către clienți sunt doar pentru demo: consola nu le trimite niciodată,
              iar fiecare poartă eticheta{" "}
              <span className="align-[1px]">
                <DemoStamp />
              </span>
            </p>
          </div>
          {data ? <p className="text-[14.5px] text-muted-foreground">Plan generat {fmtMoment(data.plan.generated_at)}</p> : null}
        </div>
      </section>

      {data ? (
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
      ) : (
        <div className="mx-auto max-w-[720px] px-7 py-20">
          <h2 className="text-[24px] font-[650]">Nu există încă un plan pentru „{scenarioLabel}”</h2>
          <p className="mt-3 text-[16.5px] leading-relaxed text-muted-foreground">
            Alertele și mesajele vin din planul agentului. Rulează agentul ca să le pregătească, sau alege alt scenariu din antet.
          </p>
          <div className="mt-5">
            <RunAgentButton scenario={scenario} scenarioLabel={scenarioLabel} />
          </div>
        </div>
      )}

      {data && remedies ? <BatteryOffers remedies={remedies.data} scenario={scenario} /> : null}

      <p className="px-7 pt-4 pb-8 text-[13.5px] text-muted-foreground">
        Planul vine din: {SOURCE_LABEL_RO[view.source]}
        {view.degradedReason ? `. ${sentence(view.degradedReason)}` : "."}
      </p>
    </AppShell>
  );
}

function AlertsSkeleton() {
  return (
    <div role="status" className="flex min-h-dvh flex-col" aria-busy="true" aria-label="Se încarcă alertele și mesajele…">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-panel px-7">
        <Wordmark />
      </div>
      <div className="h-[98px] shrink-0 border-b border-rule bg-panel" />
      <div className="grid flex-1 grid-cols-[minmax(0,1.12fr)_minmax(0,1fr)]">
        <div className="animate-pulse border-r border-rule bg-canvas" />
        <div className="bg-canvas" />
      </div>
    </div>
  );
}
