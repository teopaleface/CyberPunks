import { readFile } from "node:fs/promises";
import path from "node:path";
import { connection } from "next/server";
import { Suspense } from "react";
import { AppShell } from "@/components/shell/app-shell";
import type { Source } from "@/lib/contracts";
import { REPO_ROOT, getMetrics } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { SOURCE_ORDER } from "@/lib/sources";
import { ErrorAnalysis } from "./_components/error-analysis";
import { ModelColumn } from "./_components/model-column";
import { PlannerSection } from "./_components/planner-section";

export default function ModelsPage({ searchParams }: PageProps<"/modele">) {
  return (
    <Suspense fallback={<div className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Se încarcă modelele" />}>
      <Models searchParams={searchParams} />
    </Suspense>
  );
}

/** reports/<X>/error_analysis.md din repo, dacă există (scris de scriptul de analiză al modelului). */
async function readErrorAnalysis(source: Source): Promise<string | null> {
  try {
    const text = await readFile(path.join(REPO_ROOT, "reports", source, "error_analysis.md"), "utf8");
    return text.trim() ? text : null;
  } catch {
    return null;
  }
}

async function Models({ searchParams }: { searchParams: PageProps<"/modele">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info }, metrics, ...analyses] = await Promise.all([loadShellInfo(scenario), getMetrics(), ...SOURCE_ORDER.map(readErrorAnalysis)]);
  const bundle = metrics.data;
  const analysisBy = Object.fromEntries(SOURCE_ORDER.map((s, i) => [s, analyses[i]])) as Record<Source, string | null>;
  const published = SOURCE_ORDER.filter((s) => bundle[s]);

  return (
    <AppShell info={info}>
      <div className="mx-auto max-w-[1760px] px-7 pt-7 pb-16">
        <h1 className="text-[30px] leading-tight font-[650]">Modelele</h1>
        <p className="mt-2 max-w-[92ch] text-[16.5px] leading-relaxed">
          Trei modele antrenate de echipă. Fiecare e evaluat pe un set de test separat, pe care nu l-a văzut la antrenare, și comparat cu un baseline
          simplu. Orice cifră de pe pagină vine dintr-un script pe care îl poți rula din nou: comanda stă lângă fiecare raport.
        </p>
        <p className="mt-1.5 text-[14px] text-muted-foreground">
          {published.length === 3
            ? "Toate cele trei rapoarte sunt publicate"
            : published.length
              ? `Publicate: ${published.join(", ")}`
              : "Niciun raport publicat încă"}
          . Rapoartele vin din: {SOURCE_LABEL_RO[metrics.source]}
          {metrics.degradedReason ? `. ${metrics.degradedReason}` : ""}.
        </p>

        <div className="mt-7 grid grid-cols-1 gap-y-10 xl:grid-cols-3 xl:gap-x-0 xl:divide-x xl:divide-rule">
          {SOURCE_ORDER.map((s, i) => (
            <div key={s} className={i === 0 ? "min-w-0 xl:pr-9" : i === 2 ? "min-w-0 xl:pl-9" : "min-w-0 xl:px-9"}>
              <ModelColumn source={s} report={bundle[s]} hasAnalysis={Boolean(analysisBy[s])} />
            </div>
          ))}
        </div>

        <section aria-labelledby="erori-title" className="mt-12 border-t border-rule pt-6">
          <h2 id="erori-title" className="text-[24px] font-[650]">
            Unde greșește modelul
          </h2>
          <p className="mt-1.5 max-w-[92ch] text-[15.5px] leading-relaxed text-muted-foreground">
            Analiza erorilor pe setul de test: unde scade calitatea și ce cazuri scapă. Textul vine neschimbat din raportul fiecărui model.
          </p>
          {SOURCE_ORDER.some((s) => analysisBy[s]) ? (
            <div className="mt-5 space-y-8">
              {SOURCE_ORDER.map((s) => {
                const md = analysisBy[s];
                return md ? <ErrorAnalysis key={s} source={s} md={md} /> : null;
              })}
              {SOURCE_ORDER.some((s) => !analysisBy[s]) ? (
                <p className="text-[14.5px] text-muted-foreground">
                  Încă nepublicate:{" "}
                  {SOURCE_ORDER.filter((s) => !analysisBy[s])
                    .map((s) => `reports/${s}/error_analysis.md`)
                    .join(", ")}
                  .
                </p>
              ) : null}
            </div>
          ) : (
            <p className="mt-4 text-[15px] text-muted-foreground">
              Nicio analiză a erorilor nu e publicată încă. Fișierele așteptate: <span className="dense">reports/&lt;A|B|C&gt;/error_analysis.md</span>.
            </p>
          )}
        </section>

        <PlannerSection planner={bundle.planner} />
      </div>
    </AppShell>
  );
}
