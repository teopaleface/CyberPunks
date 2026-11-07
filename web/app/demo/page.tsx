import { requireConsole } from "@/lib/server/operations";
import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { DemoStage } from "@/components/demo/demo-stage";
import { toPlanScreenData } from "@/lib/plan-screen";
import { loadPlanView, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Presentation" };

export default function DemoPage({ searchParams }: PageProps<"/demo">) {
  return (
    <Suspense fallback={<div role="status" className="dark h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Loading presentation…</span>
      </div>}>
      <Demo searchParams={searchParams} />
    </Suspense>
  );
}

async function Demo({ searchParams }: { searchParams: PageProps<"/demo">["searchParams"] }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [view, params] = await Promise.all([loadPlanView(scenario), searchParams]);
  if (!view.data) {
    return (
      <div className="dark grid h-dvh place-items-center bg-canvas text-ink">
        <p className="max-w-[560px] text-center text-[18px]">
          No plan yet for &quot;{scenario}&quot;. Run the agent from the console, then return here.
        </p>
      </div>
    );
  }
  // lucrările arătate în scene vin întregi, ca înregistrarea să nu prindă încărcări
  const slim = toPlanScreenData(view.data);
  const decisions = view.data.plan.decisions;
  const human = decisions.find((d) => d.decision === "human_review")?.work_item_id;
  const top = decisions
    .filter((d) => d.decision === "assigned" && d.rank != null)
    .toSorted((a, b) => (a.rank ?? 99) - (b.rank ?? 99))[0]?.work_item_id;
  const storms = decisions.filter((d) => d.work_item_id.startsWith("B-") && (d.decision === "assigned" || d.decision === "human_review"));
  const storm = (storms.find((d) => slim.regionOf[d.work_item_id] === "banat") ?? storms[0])?.work_item_id;
  const full = [slim.defaultSelected, human, top, storm].filter((x): x is string => Boolean(x));
  const data = toPlanScreenData(view.data, full);
  const scene = Number(typeof params.scena === "string" ? params.scena : "1") || 1;
  return (
    <DemoStage
      data={data}
      initialScene={scene}
      auto={params.auto === "1"}
    />
  );
}
