import { requireConsole } from "@/lib/server/operations";
import { englishText } from "@/lib/english";
import type { Metadata } from "next";
import { cookies } from "next/headers";
import { connection } from "next/server";
import { Suspense } from "react";
import { Wordmark } from "@/components/brand/logo";
import { PlanScreen } from "@/components/plan/plan-screen";
import { Readouts } from "@/components/plan/readouts";
import { AppShell } from "@/components/shell/app-shell";
import { toPlanScreenData } from "@/lib/plan-screen";
import { getPosts } from "@/lib/data/posts";
import { loadLocatorGeo } from "@/lib/server/geo";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { DEFAULT_SCENARIO } from "@/lib/data";
import { RunAgentButton } from "@/components/shell/run-agent";

export const metadata: Metadata = { title: "Map and timeline" };

export default function MapPage({ searchParams }: PageProps<"/harta">) {
  return (
    <Suspense fallback={<PlanSkeleton />}>
      <Plan searchParams={searchParams} />
    </Suspense>
  );
}

async function Plan({ searchParams }: { searchParams: PageProps<"/harta">["searchParams"] }) {
  await requireConsole();
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info, view }, geo, params, posts] = await Promise.all([
    loadShellInfo(scenario),
    loadLocatorGeo(),
    searchParams,
    getPosts(scenario).catch(() => null),
  ]);

  // fixture-urile țin locul doar scenariului implicit; alt scenariu fără plan primește o stare goală cinstită
  if (!view.data || (view.source === "fixtures" && scenario !== DEFAULT_SCENARIO)) {
    const label = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;
    return (
      <AppShell info={info}>
        <div className="mx-auto max-w-[680px] px-7 py-20">
          <h1 className="text-[26px] font-[650]">No plan yet for &quot;{englishText(label)}&quot;</h1>
          <p className="mt-3 text-[16px] leading-relaxed text-muted-foreground">
            The agent has not run for this scenario yet{view.degradedReason ? ` (${englishText(view.degradedReason)})` : ""}. Run the agent or select another scenario in the menu.
          </p>
          <div className="mt-6">
            <RunAgentButton scenario={scenario} scenarioLabel={englishText(label)} />
          </div>
        </div>
      </AppShell>
    );
  }

  const requested = typeof params.lucrare === "string" ? params.lucrare : null;
  const slimData = toPlanScreenData(view.data);
  const initialSelected =
    requested && slimData.items.some((w) => w.work_item_id === requested) ? requested : slimData.defaultSelected;
  // lucrarea selectată la început vine întreagă (fără așteptare); restul se încarcă la cerere
  const data = initialSelected ? toPlanScreenData(view.data, [initialSelected]) : slimData;
  // aprobarea listei: din jurnal (API) sau, dacă API-ul n-o are încă, din cookie-ul acestui browser
  const fromAudit = view.data.audit.find(
    (a) =>
      a.actor === "human" &&
      /plan/i.test(a.action) &&
      /aprob|approv/i.test(a.action) &&
      Date.parse(a.ts) >= Date.parse(view.data!.plan.generated_at),
  );
  const cookie = (await cookies()).get(`aprobat_${scenario}`)?.value;
  const [cookiePlan, cookieAt] = cookie ? cookie.split("|") : [];
  const approval = fromAudit
    ? { at: fromAudit.ts, local: false }
    : cookiePlan === data.planId && cookieAt
      ? { at: cookieAt, local: true }
      : null;

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
        key={`${scenario}:${data.planId}`}
        data={data}
        geo={geo}
        initialSelected={initialSelected}
        postsInfo={posts ? { posts: posts.data, derived: posts.derived, lossCostNote: posts.lossCost?.note ?? null, thresholds: posts.thresholds } : undefined}
        approval={approval}
        initialRegion={typeof params.zona === "string" ? params.zona : null}
        initialMode={params.harta === "posturi" ? "posts" : "items"}
      />
    </AppShell>
  );
}

/** Aceleași înălțimi ca ecranul real, ca nimic să nu sară când vin datele. */
function PlanSkeleton() {
  return (
    <div role="status" className="flex h-dvh min-h-[720px] flex-col overflow-hidden" aria-busy="true" aria-label="Loading tomorrow's plan…">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-panel px-7">
        <Wordmark />
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
