import { connection } from "next/server";
import { Suspense } from "react";
import { LogoMark } from "@/components/brand/logo";
import { PlanScreen } from "@/components/plan/plan-screen";
import { Readouts } from "@/components/plan/readouts";
import { AppShell } from "@/components/shell/app-shell";
import { toPlanScreenData } from "@/lib/plan-screen";
import { getPosts } from "@/lib/data/posts";
import { loadLocatorGeo } from "@/lib/server/geo";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";

export default function PlanPage({ searchParams }: PageProps<"/">) {
  return (
    <Suspense fallback={<PlanSkeleton />}>
      <Plan searchParams={searchParams} />
    </Suspense>
  );
}

async function Plan({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, geo, params, posts] = await Promise.all([
    loadShellInfo(scenario),
    loadLocatorGeo(),
    searchParams,
    getPosts(scenario).catch(() => null),
  ]);

  if (!view.data) {
    return (
      <AppShell info={info}>
        <div className="mx-auto max-w-[640px] px-7 py-20">
          <h1 className="text-[26px] font-[650]">Nu există încă un plan pentru „{scenario}”</h1>
          <p className="mt-3 text-[16px] leading-relaxed text-muted-foreground">
            {view.degradedReason ?? "Agentul n-a rulat încă pentru acest scenariu."} Apasă „Rulează agentul” ca să-l
            calculeze acum, sau alege alt scenariu din antet.
          </p>
        </div>
      </AppShell>
    );
  }

  const data = toPlanScreenData(view.data);
  const requested = typeof params.lucrare === "string" ? params.lucrare : null;
  const initialSelected = requested && data.items.some((w) => w.work_item_id === requested) ? requested : data.defaultSelected;

  return (
    <AppShell info={info} fit>
      <Readouts
        summary={data.summary}
        planDate={data.planDate}
        shift={data.shift}
        generatedAt={view.data.plan.generated_at}
        crewsTotal={data.crews.length}
      />
      <PlanScreen
        data={data}
        geo={geo}
        initialSelected={initialSelected}
        postsInfo={posts ? { posts: posts.data, derived: posts.derived, lossCostNote: posts.lossCost?.note ?? null } : undefined}
      />
    </AppShell>
  );
}

/** Aceleași înălțimi ca ecranul real, ca nimic să nu sară când vin datele. */
function PlanSkeleton() {
  return (
    <div className="flex h-dvh min-h-[720px] flex-col overflow-hidden" aria-busy="true" aria-label="Se încarcă planul de mâine">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-panel px-7">
        <LogoMark size={26} />
        <span className="text-[21px] font-[650]">Tura de mâine</span>
      </div>
      <div className="h-[92px] shrink-0 border-b border-rule bg-panel/60" />
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_clamp(460px,38vw,732px)]">
        <div className="animate-pulse border-r border-rule bg-canvas" />
        <div className="bg-panel" />
      </div>
      <div className="h-[300px] shrink-0 border-t border-rule bg-panel" />
    </div>
  );
}
