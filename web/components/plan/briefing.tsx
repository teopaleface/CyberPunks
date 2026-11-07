"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState, useTransition } from "react";
import { toast } from "sonner";
import { cn } from "cn";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { submitReview } from "@/lib/data/actions";
import { alertOutcomeRo } from "@/lib/data/labels";
import type { ReviewDecision } from "@/lib/data/types";
import type { Briefing as BriefingModel, CrewGroup } from "@/lib/briefing";
import { fmtDateLong, fmtDec, fmtInt, fmtLei, fmtMoment, hhmm, minutesOfPlanDay, plural } from "@/lib/format";
import { markerKind } from "@/lib/marker-svg";
import type { PlanScreenData } from "@/lib/plan-screen";
import { itemTitle } from "@/lib/plan-screen";
import { SOURCES } from "@/lib/sources";
import { ApproveList } from "./approve-list";
import { PlanMap, type MapItem } from "./plan-map";

const REVIEW_DONE: Record<ReviewDecision, string> = { approve: "Ai aprobat", reject: "Ai respins", defer: "Ai amânat" };
// harta mică are loc doar pentru trasee: margini egale, fără butoane de regiune
const THUMB_PADDING = { top: 36, bottom: 36, left: 36, right: 36 };

/**
 * Primul ecran, ca un briefing: fraza zilei și o singură acțiune, cel mult trei cifre, următorul caz de decis,
 * echipele pe scurt (lista întreagă într-o fereastră) și o hartă mică doar cu traseele. Restul, la un click.
 */
export function Briefing({
  data,
  briefing: b,
  generatedAt,
  approval,
  theme = "light",
  spot = null,
  compact = false,
}: {
  data: PlanScreenData;
  briefing: BriefingModel;
  generatedAt: string;
  approval: { at: string; local: boolean } | null;
  theme?: "light" | "dark";
  /** În prezentare: ce se evidențiază (cazul de decis). */
  spot?: "case" | null;
  /** Mai puțin spațiu sus (prezentarea are deja o bandă cu subtitrarea). */
  compact?: boolean;
}) {
  const critical = data.alerts.filter((a) => a.severity === "critical").length;
  const shift = data.shift ? `tura ${data.shift.start}–${data.shift.end}` : "tura de zi";
  return (
    <div className={cn("mx-auto w-full max-w-[1776px] px-[72px] pb-16 max-[1500px]:px-10", compact ? "pt-8" : "pt-12")}>
      <section aria-labelledby="ziua" className="grid grid-cols-[minmax(0,1fr)_auto] items-end gap-x-16 gap-y-8 max-[1300px]:grid-cols-1">
        <div>
          <p className="text-[18px] text-muted-foreground">
            {fmtDateLong(data.planDate)}, {shift}
          </p>
          <h1 id="ziua" className="mt-3 max-w-[24ch] text-[46px] leading-[1.14] font-[620] tracking-[-0.02em] text-balance max-[1500px]:text-[40px]">
            {b.sentence}
          </h1>
          {b.subline ? <p className="mt-3 text-[21px] text-ink-soft">{b.subline}</p> : null}
          <div className="mt-8 flex flex-wrap items-center gap-x-7 gap-y-3">
            {b.queueCount ? (
              <Button asChild size="panel" className="h-auto px-6 py-3.5 text-[18px] font-[600] active:scale-[0.98]">
                <Link href={`/coada?scenariu=${encodeURIComponent(data.scenario)}`}>Vezi {b.queueCount === 1 ? "cazul" : `cele ${plural(b.queueCount, "caz", "cazuri")}`}</Link>
              </Button>
            ) : (
              <CrewsDialog groups={b.groups} crewsUsed={b.crewsUsed} crewsTotal={b.crewsTotal} primary />
            )}
            <DayDetails data={data} generatedAt={generatedAt} />
            {critical ? (
              <Link
                href={`/alerte?scenariu=${encodeURIComponent(data.scenario)}`}
                className="text-[17px] text-att-ink underline decoration-att/40 underline-offset-[5px] hover:decoration-att"
              >
                {plural(critical, "alertă critică", "alerte critice")}
              </Link>
            ) : null}
          </div>
        </div>
        <dl className="grid grid-cols-3 gap-x-10 pb-2">
          {b.numbers.map((n) => (
            <div key={n.label} className="flex flex-col-reverse">
              <dt className="mt-1 text-[17px] text-muted-foreground">{n.label}</dt>
              <dd className={cn("num-wide text-[56px] leading-none max-[1500px]:text-[46px]", n.attention && "text-att")}>
                {n.approx ? <span className="mr-2 align-middle font-sans text-[18px] font-[500] tracking-normal text-muted-foreground">circa</span> : null}
                {n.value}
              </dd>
            </div>
          ))}
        </dl>
      </section>

      {/* sub 1700 px, harta trece pe rândul ei, pe toată lățimea: cazul și echipele au loc să respire */}
      <div className={cn("grid grid-cols-2 gap-x-14 gap-y-12 min-[1700px]:grid-cols-[minmax(0,560px)_minmax(0,1fr)_minmax(0,560px)]", compact ? "mt-10" : "mt-14")}>
        <NextCase briefing={b} scenario={data.scenario} highlight={spot === "case"} />
        <CrewsSummary briefing={b} data={data} approval={approval} />
        <MapCard data={data} theme={theme} />
      </div>
    </div>
  );
}

// ------------------------------------------------------------------ următorul caz
function NextCase({ briefing: b, scenario, highlight = false }: { briefing: BriefingModel; scenario: string; highlight?: boolean }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [acting, setActing] = useState<ReviewDecision | null>(null);
  const next = b.next;
  if (!next) {
    return (
      <section aria-labelledby="caz" className="self-start rounded-[6px] border border-rule bg-panel px-7 py-6">
        <h2 id="caz" className="text-[22px] font-[620]">
          Nimic de decis
        </h2>
        <p className="mt-2 text-[18px] text-ink-soft">Agentul a decis singur toate lucrările de mâine.</p>
      </section>
    );
  }
  const act = (decision: ReviewDecision) => {
    setActing(decision);
    startTransition(async () => {
      const result = await submitReview(next.decision.work_item_id, decision, "", scenario);
      setActing(null);
      if (result.ok) {
        toast.success(`${REVIEW_DONE[decision]}: ${next.place}`, { description: "Decizia ta a intrat în jurnal, iar planul se recalculează." });
        router.refresh();
      } else {
        toast.error("Decizia nu s-a salvat", { description: result.error });
      }
    });
  };
  const meta = SOURCES[next.item.source];
  return (
    <section aria-labelledby="caz" className={cn("self-start rounded-[6px] border border-rule bg-panel px-7 py-6", highlight && "spot")}>
      <p className="flex items-center gap-2.5 text-[16px] font-[600] text-att-ink">
        <span className="size-3 rounded-full" style={{ background: `var(--src-${next.item.source.toLowerCase()})` }} aria-hidden="true" />
        Următorul caz de decis
        <span className="sr-only">, {meta.name}</span>
      </p>
      <h2 id="caz" className="mt-3 text-[28px] leading-tight font-[620]">
        {next.place}
      </h2>
      <p className="mt-2 max-w-[40ch] text-[19px] leading-[1.45] text-ink-soft">{next.what}</p>
      <div className="mt-6 flex flex-wrap gap-2.5">
        <Button size="panel" onClick={() => act("approve")} disabled={pending} aria-describedby="caz" className="active:scale-[0.98]">
          {acting === "approve" ? "Se trimite…" : "Aprobă"}
        </Button>
        <Button size="panel" variant="outline" onClick={() => act("reject")} disabled={pending} aria-describedby="caz" className="active:scale-[0.98]">
          {acting === "reject" ? "Se trimite…" : "Respinge"}
        </Button>
        <Button size="panel" variant="outline" onClick={() => act("defer")} disabled={pending} aria-describedby="caz" className="active:scale-[0.98]">
          {acting === "defer" ? "Se trimite…" : "Amână"}
        </Button>
      </div>
      <p className="mt-5 flex flex-wrap gap-x-6 gap-y-2 text-[16.5px]">
        <Link
          href={`/lucrari/${encodeURIComponent(next.decision.work_item_id)}?scenariu=${encodeURIComponent(scenario)}`}
          className="underline decoration-rule underline-offset-4 hover:decoration-ink"
        >
          De ce nu e sigur
        </Link>
        {b.queueCount > 1 ? (
          <Link href={`/coada?scenariu=${encodeURIComponent(scenario)}`} className="underline decoration-rule underline-offset-4 hover:decoration-ink">
            Încă {plural(b.queueCount - 1, "caz", "cazuri")}
          </Link>
        ) : null}
      </p>
    </section>
  );
}

// ------------------------------------------------------------------ echipele
function groupSentence(g: CrewGroup): string {
  const n = plural(g.crews.length, "echipă", "echipe");
  return `${n}${g.region ? ` în ${g.region}` : ""}${g.summary ? `, ${g.summary}` : ""}`;
}

function CrewsSummary({ briefing: b, data, approval }: { briefing: BriefingModel; data: PlanScreenData; approval: { at: string; local: boolean } | null }) {
  return (
    <section aria-labelledby="echipe">
      <h2 id="echipe" className="text-[22px] font-[620]">
        Echipele de mâine
      </h2>
      <p className="mt-3 text-[28px] leading-tight font-[600]">
        {plural(b.crewsUsed, "echipă", "echipe")} pe teren
        <span className="text-[19px] font-[400] text-muted-foreground"> din {fmtInt(b.crewsTotal)}</span>
      </p>
      <ul className="mt-4 space-y-2.5 text-[18px] text-ink-soft">
        {b.groups.map((g) => (
          <li key={g.label} className="flex items-baseline gap-3">
            <span className="mt-[7px] size-2.5 shrink-0 self-start rounded-full" style={{ background: g.storm ? "var(--src-b)" : "var(--ink)" }} aria-hidden="true" />
            {groupSentence(g)}
          </li>
        ))}
      </ul>
      <div className="mt-7 flex flex-wrap items-center gap-3">
        <CrewsDialog groups={b.groups} crewsUsed={b.crewsUsed} crewsTotal={b.crewsTotal} />
        <ApproveList key={data.planId} scenario={data.scenario} planId={data.planId} approvedAt={approval?.at ?? null} approvedLocal={approval?.local ?? false} />
      </div>
    </section>
  );
}

function CrewsDialog({ groups, crewsUsed, crewsTotal, primary = false }: { groups: CrewGroup[]; crewsUsed: number; crewsTotal: number; primary?: boolean }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button size="panel" variant={primary ? "default" : "outline"} className="active:scale-[0.98]">
          Vezi echipele
        </Button>
      </DialogTrigger>
      <DialogContent className="max-h-[86vh] overflow-y-auto rounded-[8px] bg-panel p-8 sm:max-w-[760px]">
        <DialogHeader>
          <DialogTitle className="text-[26px] font-[620]">Echipele de mâine</DialogTitle>
          <DialogDescription className="text-[17px]">
            {plural(crewsUsed, "echipă", "echipe")} pe teren din {fmtInt(crewsTotal)}. Ora de plecare și de întoarcere la bază.
          </DialogDescription>
        </DialogHeader>
        <div className="mt-2 space-y-8">
          {groups.map((g) => (
            <section key={g.label}>
              <h3 className="text-[17px] font-[600] text-muted-foreground">{g.label}</h3>
              <ul className="mt-2 divide-y divide-rule border-y border-rule">
                {g.crews.map((c) => (
                  <li key={c.crewId} className="grid grid-cols-[96px_minmax(0,1fr)_auto] items-baseline gap-x-5 py-3.5 text-[17.5px]">
                    <b className="font-[620]" translate="no">
                      {c.crewId}
                    </b>
                    <span className="text-ink-soft">
                      {c.base}, {c.storm ? "o zonă de furtună" : plural(c.stops, "oprire", "opriri")}
                      {c.km != null ? <span className="text-muted-foreground">, {fmtDec(c.km, 0)} km</span> : null}
                    </span>
                    <span className="text-right tabular-nums">
                      {c.storm && c.until ? `${c.depart ?? "–"}–${c.until}` : `${c.depart ?? "–"}–${c.back ?? "–"}`}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
        <p className="mt-4 text-[16.5px]">
          <Link href="/harta" className="underline decoration-rule underline-offset-4 hover:decoration-ink">
            Vezi traseele și linia de timp pe hartă
          </Link>
        </p>
      </DialogContent>
    </Dialog>
  );
}

// ------------------------------------------------------------------ detaliile zilei
function DayDetails({ data, generatedAt }: { data: PlanScreenData; generatedAt: string }) {
  const s = data.summary;
  const rows: [string, string][] = [
    ["Lucrări intrate", `${fmtInt(s.items_in ?? 0)}${s.items_invalid ? `, ${fmtInt(s.items_invalid)} respinse la intrare` : ", toate valide"}`],
    ["În trasee", `${plural(s.assigned ?? 0, "lucrare", "lucrări")}, ${plural(s.crews_used ?? 0, "echipă", "echipe")} din ${fmtInt(data.crews.length)}`],
    ["Decide un om", plural(s.human_review ?? 0, "caz", "cazuri")],
    ["Verificate de la distanță", plural(s.remote_actions ?? 0, "lucrare", "lucrări")],
    ["Mesaje către clienți", plural(s.notifications ?? 0, "mesaj", "mesaje")],
    ["Amânate", plural(s.deferred ?? 0, "lucrare", "lucrări")],
    ["Valoare așteptată", fmtLei(s.expected_value_lei ?? 0)],
    ["De parcurs", `${fmtDec(s.total_km ?? 0, 1)} km`],
    ["Plan generat", fmtMoment(generatedAt)],
  ];
  const alerts = data.alerts.filter((a) => a.severity !== "info").slice(0, 4);
  return (
    <Sheet>
      <SheetTrigger asChild>
        <button type="button" className="text-[17px] text-ink-soft underline decoration-rule underline-offset-[5px] hover:text-ink hover:decoration-ink">
          Detaliile zilei
        </button>
      </SheetTrigger>
      <SheetContent
        side="right"
        className="gap-0 overflow-y-auto bg-panel p-0 duration-[240ms] ease-[cubic-bezier(0.32,0.72,0,1)] data-[side=right]:w-[min(560px,92vw)] data-[side=right]:sm:max-w-[560px]"
      >
        <SheetHeader className="px-8 pt-8 pb-4">
          <SheetTitle className="text-[26px] font-[620]">Detaliile zilei</SheetTitle>
          <SheetDescription className="text-[16.5px]">Toate cifrele planului de mâine. Datele sunt sintetice, pe hartă reală.</SheetDescription>
        </SheetHeader>
        <dl className="mx-8 grid grid-cols-[220px_minmax(0,1fr)] border-t border-rule text-[17px] [&_dd]:border-b [&_dd]:border-rule [&_dd]:py-3 [&_dt]:border-b [&_dt]:border-rule [&_dt]:py-3 [&_dt]:text-muted-foreground">
          {rows.map(([k, v]) => (
            <div key={k} className="contents">
              <dt>{k}</dt>
              <dd className="tabular-nums">{v}</dd>
            </div>
          ))}
        </dl>
        {alerts.length ? (
          <section aria-labelledby="alerte-zi" className="mx-8 mt-8 mb-8">
            <h3 id="alerte-zi" className="text-[18px] font-[620]">
              Alertele zilei
            </h3>
            <ul className="mt-2 space-y-3 text-[16.5px]">
              {alerts.map((a) => {
                const outcome = alertOutcomeRo(a.work_item_ids, data.decisions);
                return (
                  <li key={a.alert_id}>
                    <b className="font-[600]">{a.title_ro}</b>
                    {outcome ? <span className="block text-muted-foreground">Ce a decis agentul: {outcome}</span> : null}
                  </li>
                );
              })}
            </ul>
            <Link href={`/alerte?scenariu=${encodeURIComponent(data.scenario)}`} className="mt-4 inline-block text-[16.5px] underline decoration-rule underline-offset-4 hover:decoration-ink">
              Toate alertele și mesajele
            </Link>
          </section>
        ) : null}
      </SheetContent>
    </Sheet>
  );
}

// ------------------------------------------------------------------ harta mică
function MapCard({ data, theme = "dark" }: { data: PlanScreenData; theme?: "light" | "dark" }) {
  const router = useRouter();
  const region = data.regions.find((r) => r.id === data.defaultRegion);
  const items: MapItem[] = useMemo(() => {
    const byId = new Map(data.items.map((w) => [w.work_item_id, w]));
    return data.routes.flatMap((r) =>
        r.stops
          .filter((st) => (st.workItem ?? byId.get(st.work_item_id)) && st.lat != null && st.lon != null)
          .map((st) => {
            const w = (st.workItem ?? byId.get(st.work_item_id))!;
            return {
              id: w.work_item_id,
              source: w.source,
              lat: st.lat!,
              lon: st.lon!,
              kind: markerKind(data.decisions[w.work_item_id]?.decision),
              title: w.asset_type === "meter" ? w.asset_id : itemTitle(w),
              sub: st.eta ? `${r.crew_id}, ${hhmm(minutesOfPlanDay(st.eta, data.planDate))}` : r.crew_id,
              pinned: false,
              prominent: true,
            };
          }),
    );
  }, [data.items, data.routes, data.decisions, data.planDate]);
  const routes = useMemo(() => data.routes.map((r) => ({ crewId: r.crew_id, path: r.path })), [data.routes]);
  const depots = useMemo(
    () => data.depots.map((d) => ({ id: d.depot_id, label: d.label_ro.replace(/^Bază operativă\s*/i, "").replace(/\s*\(simulată\)/, ""), lat: d.lat, lon: d.lon })),
    [data.depots],
  );
  const outside = data.routes.filter((r) => data.depots.find((d) => d.depot_id === r.depot_id)?.region !== data.defaultRegion).length;
  return (
    <section aria-labelledby="harta" className="col-span-2 min-w-0 min-[1700px]:col-span-1">
      <h2 id="harta" className="text-[22px] font-[620]">
        Harta
      </h2>
      <div className="relative mt-3 h-[400px] overflow-hidden rounded-[6px] border border-rule">
        <PlanMap
          className="absolute inset-0"
          items={items}
          routes={routes}
          depots={depots}
          bounds={region?.bounds ?? [25.7, 43.85, 26.6, 44.75]}
          selectedId={null}
          onSelect={(id) => router.push(`/lucrari/${encodeURIComponent(id)}?scenariu=${encodeURIComponent(data.scenario)}`)}
          padding={THUMB_PADDING}
          theme={theme}
        />
      </div>
      <p className="mt-3 text-[16.5px] leading-snug text-ink-soft">
        {region ? `Doar traseele din ${region.label}.` : "Doar traseele."}
        {outside ? ` ${plural(outside, "echipă e", "echipe sunt")} în alte regiuni.` : ""} Restul lucrărilor apar pe harta mare.
      </p>
      <Link href={`/harta?scenariu=${encodeURIComponent(data.scenario)}`} className="mt-2 inline-block text-[17px] underline decoration-rule underline-offset-[5px] hover:decoration-ink">
        Deschide harta mare
      </Link>
    </section>
  );
}
