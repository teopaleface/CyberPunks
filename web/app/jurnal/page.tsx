import { DownloadIcon } from "lucide-react";
import { connection } from "next/server";
import { Suspense } from "react";
import { LogoMark } from "@/components/brand/logo";
import { AppShell } from "@/components/shell/app-shell";
import { RunAgentButton } from "@/components/shell/run-agent";
import { Button } from "@/components/ui/button";
import { getAudit } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { sentence } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { actionOptions, buildRows } from "./_components/build-rows";
import { JournalTable } from "./_components/journal-table";
import { JournalSummary } from "./_components/summary";

type SearchParams = Promise<Record<string, string | string[] | undefined>>;

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
      <section className="border-b border-rule bg-panel">
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3 px-7 pt-5 pb-4">
          <div className="min-w-0">
            <h1 className="text-[26px] leading-tight font-[650] tracking-[-0.005em]">Jurnalul deciziilor</h1>
            <p className="mt-1 max-w-[90ch] text-[16px] text-muted-foreground">
              Fiecare rând leagă o decizie, a agentului sau a omului, de predicția, versiunea modelului, regula și pragurile care au
              produs-o.
            </p>
          </div>
          {rows.length ? (
            <Button asChild variant="outline" size="panel" className="rounded-[4px] border-input bg-panel">
              <a href={`/jurnal/descarca?scenariu=${encodeURIComponent(scenario)}`} download={`jurnal-${scenario}.jsonl`}>
                <DownloadIcon data-icon="inline-start" aria-hidden="true" />
                Descarcă jurnalul (JSONL)
              </a>
            </Button>
          ) : null}
        </div>
      </section>

      {rows.length ? (
        <>
          <JournalSummary rows={rows} />
          <JournalTable rows={rows} options={actionOptions(rows)} scenario={scenario} />
        </>
      ) : (
        <div className="mx-auto max-w-[720px] px-7 py-20">
          <h2 className="text-[24px] font-[650]">Jurnalul e gol pentru „{scenarioLabel}”</h2>
          <p className="mt-3 text-[16.5px] leading-relaxed text-muted-foreground">
            Rulează agentul ca să apară primele decizii. Fiecare decizie, a agentului sau a ta, intră aici împreună cu predicția,
            regula și pragurile care au produs-o.
          </p>
          <div className="mt-5">
            <RunAgentButton scenario={scenario} scenarioLabel={scenarioLabel} />
          </div>
        </div>
      )}

      <p className="px-7 pt-4 pb-8 text-[13.5px] text-muted-foreground">
        Jurnalul vine din: {SOURCE_LABEL_RO[audit.source]}
        {audit.degradedReason ? `. ${sentence(audit.degradedReason)}` : "."}
        {audit.parseErrors?.length ? ` ${audit.parseErrors.length} rânduri n-au putut fi citite și lipsesc din tabel.` : ""}
      </p>
    </AppShell>
  );
}

/** Aceleași înălțimi ca ecranul real, ca nimic să nu sară când vin datele. */
function JournalSkeleton() {
  return (
    <div className="flex min-h-dvh flex-col" aria-busy="true" aria-label="Se încarcă jurnalul deciziilor">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-panel px-7">
        <LogoMark size={26} />
        <span className="text-[21px] font-[650]">Tura de mâine</span>
      </div>
      <div className="h-[98px] shrink-0 border-b border-rule bg-panel" />
      <div className="h-[88px] shrink-0 border-b border-rule bg-canvas" />
      <div className="flex-1 animate-pulse bg-panel" />
    </div>
  );
}
