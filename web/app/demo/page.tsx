import type { Metadata } from "next";
import { connection } from "next/server";
import { Suspense } from "react";
import { DemoStage } from "@/components/demo/demo-stage";
import { getPosts } from "@/lib/data/posts";
import { toPlanScreenData } from "@/lib/plan-screen";
import { loadLocatorGeo } from "@/lib/server/geo";
import { loadPlanView, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Prezentare" };

export default function DemoPage({ searchParams }: PageProps<"/demo">) {
  return (
    <Suspense fallback={<div className="dark h-dvh bg-canvas" aria-busy="true" />}>
      <Demo searchParams={searchParams} />
    </Suspense>
  );
}

async function Demo({ searchParams }: { searchParams: PageProps<"/demo">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [view, geo, params, posts] = await Promise.all([
    loadPlanView(scenario),
    loadLocatorGeo(),
    searchParams,
    getPosts(scenario).catch(() => null),
  ]);
  if (!view.data) {
    return (
      <div className="dark grid h-dvh place-items-center bg-canvas text-ink">
        <p className="max-w-[560px] text-center text-[18px]">
          Nu există încă un plan pentru „{scenario}”. Rulează agentul din consolă, apoi revino aici.
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
      geo={geo}
      generatedAt={view.data.plan.generated_at}
      postsInfo={posts ? { posts: posts.data, derived: posts.derived, lossCostNote: posts.lossCost?.note ?? null } : undefined}
      initialScene={scene}
      auto={params.auto === "1"}
    />
  );
}
