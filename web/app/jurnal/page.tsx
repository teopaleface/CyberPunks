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

const WRAP = "mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4";

export default function JournalPage({ searchParams }: { searchParams: SearchParams }) {
  return (
    <Suspense fallback={<JournalSkeleton />}>
      <Journal searchParams={searchParams} />
    </Suspense>
  );
}

async function Journal({ searchParams }: { searchParams: SearchParams }) {
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
          title="Jurnalul deciziilor"
          subtitle="Istoricul deciziilor modelului, al oamenilor și al acțiunilor aplicate, cu trasabilitate către lucrări, reguli și versiuni de model."
        />
        <div className="mt-6">
          {rows.length ? (
            <JournalTable rows={rows} options={actionOptions(rows)} scenario={scenario} />
          ) : (
            <div className="max-w-[720px] rounded-[18px] border border-rule bg-panel p-8">
              <h2 className="text-[24px] font-[650]">Jurnalul e gol pentru „{scenarioLabel}”</h2>
              <p className="mt-3 text-[16.5px] leading-relaxed text-ink-soft">
                Rulează agentul ca să apară primele decizii. Fiecare decizie, a agentului sau a ta, intră aici împreună cu predicția,
                regula și pragurile care au produs-o.
              </p>
              <div className="mt-5">
                <RunAgentButton scenario={scenario} scenarioLabel={scenarioLabel} />
              </div>
            </div>
          )}
        </div>
        <p className="pt-4 text-[13.5px] text-muted-foreground">
          Jurnalul vine din: {SOURCE_LABEL_RO[audit.source]}
          {audit.degradedReason ? `. ${sentence(audit.degradedReason)}` : "."}
          {audit.parseErrors?.length ? ` ${audit.parseErrors.length} rânduri n-au putut fi citite și lipsesc din tabel.` : ""}
        </p>
      </div>
    </AppShell>
  );
}

/** Aceleași înălțimi ca ecranul real, ca nimic să nu sară când vin datele. */
function JournalSkeleton() {
  return (
    <div role="status" className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Se încarcă jurnalul deciziilor…">
      <div className="h-16 border-b border-rule bg-panel" />
      <div className={WRAP}>
        <div className="h-[72px]" />
        <div className="mt-6 h-[110px] animate-pulse rounded-[18px] bg-panel" />
        <div className="mt-5 h-[520px] animate-pulse rounded-[18px] bg-panel" />
      </div>
    </div>
  );
}
