import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import { BookOpenIcon } from "lucide-react";
import { connection } from "next/server";
import { Suspense } from "react";
import { PageTitle } from "@/components/ds";
import { AppShell } from "@/components/shell/app-shell";
import { RunAgentButton } from "@/components/shell/run-agent";
import { getAudit } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { sentence } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { actionOptions, buildRows } from "./_components/build-rows";
import { JournalTable } from "./_components/journal-table";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

const WRAP = "mx-auto w-full max-w-[1440px] px-8 pt-7 pb-14 max-md:px-4";

export default function JournalPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<JournalSkeleton />}>
      <Journal searchParams={searchParams} />
    </Suspense>
  );
}

async function Journal({ searchParams }: { searchParams: SearchParams }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, audit] = await Promise.all([loadShellInfo(scenario), getAudit(scenario)]);
  const rows = buildRows(audit.data, view.data?.workItemsById ?? {});
  const scenarioLabel = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;

  return (
    <AppShell info={info}>
      <div className={WRAP}>
        <PageTitle
          icon={BookOpenIcon}
          title="Decision history"
          subtitle="Decisions and actions with their supporting rules and evidence."
        />
        <div className="mt-6">
          {rows.length ? (
            <JournalTable rows={rows} options={actionOptions(rows)} scenario={scenario} />
          ) : (
            <div className="max-w-[720px] rounded-[18px] border border-rule bg-panel p-8">
              <h2 className="text-[24px] font-[650]">No history for &quot;{englishText(scenarioLabel)}&quot;</h2>
              <p className="mt-3 text-[16.5px] leading-relaxed text-ink-soft">
                Run the agent to record its first decisions and supporting evidence.
              </p>
              <div className="mt-5">
                <RunAgentButton scenario={scenario} scenarioLabel={englishText(scenarioLabel)} />
              </div>
            </div>
          )}
        </div>
        <p className="pt-4 text-[13.5px] text-muted-foreground">
          History source: {englishText(SOURCE_LABEL_RO[audit.source])}
          {audit.degradedReason ? `. ${englishText(sentence(audit.degradedReason))}` : "."}
          {audit.parseErrors?.length ? ` ${audit.parseErrors.length} rows could not be read and are missing from the table.` : ""}
        </p>
      </div>
    </AppShell>
  );
}

/** Aceleași înălțimi ca ecranul real, ca nimic să nu sară când vin datele. */
function JournalSkeleton() {
  return (
    <div role="status" className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Loading decision history…">
      <div className="h-16 border-b border-rule bg-panel" />
      <div className={WRAP}>
        <div className="h-[72px]" />
        <div className="mt-6 h-[110px] animate-pulse rounded-[18px] bg-panel" />
        <div className="mt-5 h-[520px] animate-pulse rounded-[18px] bg-panel" />
      </div>
    </div>
  );
}
