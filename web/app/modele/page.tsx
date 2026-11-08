import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import { readText } from "@/lib/server/read-file";
import path from "node:path";
import { connection } from "next/server";
import { Suspense } from "react";
import { PageTitle } from "@/components/ds";
import { Disclosure } from "@/components/simple/disclosure";
import { AppShell } from "@/components/shell/app-shell";
import type { Source } from "@/lib/contracts";
import { REPO_ROOT, getMetrics } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { sentence } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { SOURCE_ORDER } from "@/lib/sources";
import { ModelsBoard } from "./_components/board";
import { BalanceEvaluation } from "./_components/balance-evaluation";
import { ModelColumn } from "./_components/model-column";
import { PlannerSection } from "./_components/planner-section";

const WRAP = "mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4";

export default function ModelsPage({ searchParams }: PageProps<"/modele">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Loading models…</span>
      </div>}>
      <Models searchParams={searchParams} />
    </Suspense>
  );
}

/** reports/<X>/error_analysis.md din repo, dacă există (scris de scriptul de analiză al modelului). */
async function readErrorAnalysis(source: Source): Promise<string | null> {
  try {
    const text = await readText(path.join(REPO_ROOT, "reports", source, "error_analysis.md"));
    return text.trim() ? text : null;
  } catch {
    return null;
  }
}

async function Models({ searchParams }: { searchParams: PageProps<"/modele">["searchParams"] }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info }, metrics, ...analyses] = await Promise.all([loadShellInfo(scenario), getMetrics(), ...SOURCE_ORDER.map(readErrorAnalysis)]);
  const bundle = metrics.data;
  const analysisBy = Object.fromEntries(SOURCE_ORDER.map((s, i) => [s, analyses[i]])) as Record<Source, string | null>;
  const published = SOURCE_ORDER.filter((s) => bundle[s]);

  return (
    <AppShell info={info}>
      <div className={WRAP}>
        <PageTitle
          title="Model evaluation"
          subtitle="Measured performance against simple rules on the same test data."
        />
        <ModelsBoard bundle={bundle} planner={bundle.planner} analysisBy={analysisBy} />
        <BalanceEvaluation report={bundle.bilant ?? null} />

        <p className="mt-5 text-[13.5px] text-muted-foreground">
          {published.length === 3 && bundle.bilant
            ? "All four model reports published"
            : published.length
              ? `Published: ${published.join(", ")}`
              : "No reports published yet"}
          . Report source: {englishText(SOURCE_LABEL_RO[metrics.source])}
          {metrics.degradedReason ? `. ${englishText(sentence(metrics.degradedReason)).replace(/\.$/, "")}` : ""}.
        </p>

        <div className="mt-6">
          <Disclosure title="Model details" hint="Test data, baseline, metrics and sources">
            <div className="grid grid-cols-1 gap-y-10 xl:grid-cols-3 xl:gap-x-0 xl:divide-x xl:divide-rule">
              {SOURCE_ORDER.map((s, i) => (
                <div key={s} className={i === 0 ? "min-w-0 xl:pr-9" : i === 2 ? "min-w-0 xl:pl-9" : "min-w-0 xl:px-9"}>
                  <ModelColumn source={s} report={bundle[s]} hasAnalysis={Boolean(analysisBy[s])} />
                </div>
              ))}
            </div>
          </Disclosure>
          <Disclosure title="Agent evaluation details" hint="Strategies, robustness and assumptions">
            <PlannerSection planner={bundle.planner} />
          </Disclosure>
        </div>
      </div>
    </AppShell>
  );
}
