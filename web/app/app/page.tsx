import { englishText } from "@/lib/english";
import { ArrowRight } from "lucide-react";
import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { Suspense } from "react";
import { Card, PageTitle, Pill } from "@/components/ds";
import { AlertBanner } from "@/components/home/alert-banner";
import { ApproveButton } from "@/components/home/approve-button";
import { CrewsCard, GanttCard, QuestionBody, RomaniaCard, SelectedMeter } from "@/components/home/cards";
import { HOME_FILTERS, type HomeFilter } from "@/components/home/filters";
import { HomeBoard } from "@/components/home/home-board";
import { KpiRow, PlanFigures } from "@/components/home/kpis";
import { AppShell } from "@/components/shell/app-shell";
import { RunAgentButton } from "@/components/shell/run-agent";
import { toBriefing, crewLines } from "@/lib/briefing";
import type { Alert, WorkItem } from "@/lib/contracts";
import { DEFAULT_SCENARIO } from "@/lib/data";
import { fmtDateLong } from "@/lib/format";
import { getRomaniaDots } from "@/lib/home-dotmap";
import { toPlanScreenData } from "@/lib/plan-screen";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";

export default function PlanPage({ searchParams }: PageProps<"/app">) {
  return (
    <Suspense fallback={<PlanSkeleton />}>
      <Plan searchParams={searchParams} />
    </Suspense>
  );
}

/** Avertizarea cea mai importantă: furtuna cu probabilitatea cea mai mare, altfel prima alertă critică. */
function topAlert(alerts: Alert[]): { id: string; lead: string; text: string } | null {
  const prob = (a: Alert) => Number(/Probabilitate de avarii (\d+)%/.exec(a.body_ro)?.[1] ?? 0);
  const storms = alerts.filter((a) => /^Risc de avarii/i.test(a.title_ro)).sort((a, b) => prob(b) - prob(a));
  const clean = (t: string) => t.replace(/\s*\([^()]*(nesigur|decide)[^()]*\)/i, "").replace(/\.$/, "");
  if (storms[0]) {
    const a = storms[0];
    const win = /fereastra (\d{1,2}:\d{2})\s*[-–]\s*(\d{1,2}:\d{2})/.exec(a.body_ro);
    return { id: a.alert_id, lead: "Storm warning", text: `${englishText(clean(a.title_ro))}${win ? `, ${win[1]}–${win[2]}` : ""}.` };
  }
  const crit = alerts.find((a) => a.severity === "critical");
  return crit ? { id: crit.alert_id, lead: "Warning", text: `${englishText(clean(crit.title_ro))}.` } : null;
}

async function Plan({ searchParams }: { searchParams: PageProps<"/app">["searchParams"] }) {
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
          <h1 className="text-[30px] font-[620]">No plan yet for &quot;{englishText(label)}&quot;</h1>
          <p className="mt-3 text-[18px] leading-relaxed text-muted-foreground">
            The agent has not run for this scenario yet{view.degradedReason ? ` (${englishText(view.degradedReason)})` : ""}. Run the agent or select another scenario in the menu.
          </p>
          <div className="mt-6">
            <RunAgentButton scenario={scenario} scenarioLabel={englishText(label)} />
          </div>
        </div>
      </AppShell>
    );
  }

  const data = toPlanScreenData(view.data);
  const briefing = toBriefing(data);
  const lines = crewLines(data);
  const dots = await getRomaniaDots();

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

  // cazul de decis: primul din coadă; pentru filtrele „Vreme” și „Tensiune”, primul de tipul lor
  const queueItems = Object.values(data.decisions)
    .filter((d) => d.decision === "human_review")
    .map((d) => data.items.find((w) => w.work_item_id === d.work_item_id))
    .filter((w): w is WorkItem => Boolean(w));
  const first = briefing.next?.item ?? null;
  const storm = queueItems.find((w) => w.source === "B") ?? null;
  const voltage = queueItems.find((w) => w.source === "C") ?? null;

  // contorul A cu scorul cel mai mare dintre cele aflate într-un traseu
  const routed = new Set(data.routes.flatMap((r) => r.stops.map((s) => s.work_item_id)));
  const meter =
    data.items
      .filter((w) => w.source === "A" && w.asset_type === "meter" && routed.has(w.work_item_id))
      .sort((a, b) => b.prediction.score - a.prediction.score)[0] ?? null;

  const rawFilter = typeof params.filtru === "string" ? params.filtru : "toate";
  const initial = (HOME_FILTERS as string[]).includes(rawFilter) ? (rawFilter as HomeFilter) : "toate";
  const banner = topAlert(data.alerts);
  const dateLong = fmtDateLong(data.planDate);
  const suffix = `?scenariu=${encodeURIComponent(scenario)}`;

  const alerts = (
    <Card title="Alerts">
      <ul className="divide-y divide-rule">
        {data.alerts.slice(0, 6).map((a) => (
          <li key={a.alert_id} className="flex items-center gap-3 py-2.5 text-[15px]">
            <Pill size="sm" tone={a.severity === "critical" ? "red" : a.severity === "warning" ? "amber" : "grey"}>
              {a.severity === "critical" ? "Critical" : a.severity === "warning" ? "Warning" : "Info"}
            </Pill>
            <span className="min-w-0 flex-1">{englishText(a.title_ro)}</span>
          </li>
        ))}
        {data.alerts.length === 0 ? <li className="py-2 text-ink-soft">No alerts.</li> : null}
      </ul>
    </Card>
  );

  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1440px] px-8 pt-7 pb-14 max-md:px-4">
        {banner ? <AlertBanner key={banner.id} id={`${scenario}:${banner.id}`} lead={banner.lead} text={banner.text} /> : null}
        <PageTitle title="Plan" subtitle={`${dateLong}.${info.provenance.syntheticItems ? " Includes synthetic data." : ""}`} />
        <HomeBoard
          key={`${scenario}:${data.planId}`}
          initial={initial}
          suffix={suffix}
          kpis={<KpiRow s={data.summary} />}
          figures={<PlanFigures s={data.summary} />}
          plan={
            <>
              <h2 className="text-[23px] leading-[1.3] font-[550] tracking-[-0.02em]">Crew assignments</h2>
              <p className="mt-3 text-[15px] leading-relaxed text-ink-soft">
                {data.routes.filter((r) => r.stops.length > 0).length} crew routes ready. Approval covers crew assignments only; review cases separately.
              </p>
              <div className="mt-5 flex flex-wrap gap-3">
                <Link href={`/harta${suffix}`} className="inline-flex min-h-11 items-center gap-2 rounded-[10px] border border-rule bg-surface-2 px-4 py-2.5 text-[14px] text-ink hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring">
                  Review routes
                  <ArrowRight aria-hidden="true" size={16} />
                </Link>
              </div>
              <div className="mt-5 border-t border-rule pt-5">
                <ApproveButton scenario={scenario} planId={data.planId} approvedAt={approval?.at ?? null} approvedLocal={approval?.local ?? false} />
              </div>

            </>
          }
          map={<RomaniaCard map={dots} scenario={scenario} />}
          crews={<CrewsCard lines={lines} approved={Boolean(approval)} scenario={scenario} />}
          gantt={<GanttCard data={data} dateLabel={dateLong.charAt(0).toLowerCase() + dateLong.slice(1)} />}
          alerts={alerts}
          meter={meter ? <SelectedMeter item={meter} scenario={scenario} /> : null}
          question={{
            default: <QuestionBody item={first} scenario={scenario} reason={briefing.next?.what ? englishText(briefing.next.what) : undefined} />,
            storm: <QuestionBody item={storm} scenario={scenario} emptyText="No storm cases need your decision." />,
            voltage: <QuestionBody item={voltage} scenario={scenario} emptyText="No voltage cases need your decision." />,
          }}
        />
      </div>
    </AppShell>
  );
}

/** Aceeași așezare ca ecranul, ca nimic să nu sară când vin datele. */
function PlanSkeleton() {
  return (
    <div role="status" className="flex min-h-dvh flex-col" aria-busy="true" aria-label="Loading tomorrow's plan…">
      <div className="h-16 shrink-0 border-b border-rule bg-panel" />
      <div className="mx-auto w-full max-w-[1440px] px-8 pt-7 max-md:px-4">
        <div className="h-[58px] animate-pulse rounded-[14px] bg-panel motion-reduce:animate-none" />
        <div className="mt-6 h-9 w-72 max-w-full animate-pulse rounded-[6px] bg-muted motion-reduce:animate-none" />
        <div className="mt-4 h-5 w-full max-w-xl rounded-[6px] bg-muted" />
        <div className="mt-7 grid gap-5 rounded-2xl border border-rule bg-panel p-6 sm:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="h-16 rounded-lg bg-muted" />
          ))}
        </div>
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="h-[360px] rounded-2xl border border-rule bg-panel" />
          <div className="h-[360px] rounded-2xl border border-rule bg-panel" />
        </div>
        <div className="mt-7 h-24 rounded-2xl border border-rule bg-panel" />
      </div>
    </div>
  );
}
