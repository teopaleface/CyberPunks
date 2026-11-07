import { cookies } from "next/headers";
import { connection } from "next/server";
import { Suspense } from "react";
import { Wordmark } from "@/components/brand/logo";
import { redirect } from "next/navigation";
import { Briefing } from "@/components/plan/briefing";
import { AppShell } from "@/components/shell/app-shell";
import { toBriefing } from "@/lib/briefing";
import { toPlanScreenData } from "@/lib/plan-screen";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { DEFAULT_SCENARIO } from "@/lib/data";
import { RunAgentButton } from "@/components/shell/run-agent";

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
  const [{ info, view }, params] = await Promise.all([loadShellInfo(scenario), searchParams]);

  // adresele vechi ale hărții (?lucrare=, ?harta=, ?zona=) duc la harta mare, cu tot cu selecție
  if (["lucrare", "harta", "zona"].some((k) => typeof params[k] === "string")) {
    const q = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (typeof v === "string") q.set(k, v);
    redirect(`/harta?${q.toString()}`);
  }

  // fixture-urile țin locul doar scenariului implicit; alt scenariu fără plan primește o stare goală cinstită
  if (!view.data || (view.source === "fixtures" && scenario !== DEFAULT_SCENARIO)) {
    const label = info.scenarios.find((s) => s.id === scenario)?.label ?? scenario;
    return (
      <AppShell info={info}>
        <div className="mx-auto max-w-[680px] px-7 py-20">
          <h1 className="text-[30px] font-[620]">Nu există încă un plan pentru „{label}”</h1>
          <p className="mt-3 text-[18px] leading-relaxed text-muted-foreground">
            Agentul n-a rulat încă pentru acest scenariu{view.degradedReason ? ` (${view.degradedReason})` : ""}. Pornește-l acum sau
            alege alt scenariu din antet.
          </p>
          <div className="mt-6">
            <RunAgentButton scenario={scenario} scenarioLabel={label} />
          </div>
        </div>
      </AppShell>
    );
  }

  const data = toPlanScreenData(view.data);
  const briefing = toBriefing(data);
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
    <AppShell info={info}>
      <Briefing key={`${scenario}:${data.planId}`} data={data} briefing={briefing} generatedAt={view.data.plan.generated_at} approval={approval} />
    </AppShell>
  );
}

/** Aceeași așezare ca briefingul, ca nimic să nu sară când vin datele. */
function PlanSkeleton() {
  return (
    <div role="status" className="flex min-h-dvh flex-col" aria-busy="true" aria-label="Se încarcă planul de mâine…">
      <div className="flex h-16 shrink-0 items-center gap-3 border-b border-rule bg-panel px-7">
        <Wordmark />
      </div>
      <div className="mx-auto w-full max-w-[1776px] px-[72px] pt-12 max-[1500px]:px-10">
        <div className="h-5 w-80 animate-pulse rounded-[3px] bg-muted motion-reduce:animate-none" />
        <div className="mt-4 h-[110px] w-[min(880px,70%)] animate-pulse rounded-[4px] bg-muted motion-reduce:animate-none" />
        <div className="mt-8 h-12 w-64 rounded-[4px] bg-muted" />
        <div className="mt-14 grid grid-cols-3 gap-14 max-[1500px]:grid-cols-2">
          <div className="h-[300px] rounded-[6px] bg-panel" />
          <div className="h-[300px] rounded-[6px] bg-panel/60" />
          <div className="h-[400px] rounded-[6px] bg-panel/60" />
        </div>
      </div>
    </div>
  );
}
