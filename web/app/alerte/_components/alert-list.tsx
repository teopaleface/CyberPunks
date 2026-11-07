import { englishText } from "@/lib/english";
import { cn } from "cn";
import type { Alert, Decision, WorkItem } from "@/lib/contracts";
import { alertOutcomeRo } from "@/lib/data/labels";
import { fmtInt, fmtMoment, fmtTime, plural } from "@/lib/format";
import { CountPill, DemoStamp, SEVERITY_RO, SeverityIcon, WorkItemRef, type Severity } from "./parts";

const CHANNEL_RO: Record<Alert["channel"], string> = {
  dispecerat: "to dispatcher",
  echipa: "to crew",
  clienti: "to customers",
};

const TONE: Record<Severity, string> = {
  critical: "text-destructive",
  warning: "text-att-ink",
  info: "text-ink",
};

/** Bara din stânga: roșu pentru critic, portocaliu pentru avertisment; informarea rămâne gri. */
const BAR: Record<Severity, string | null> = {
  critical: "shadow-[inset_3px_0_0_var(--destructive)]",
  warning: "shadow-[inset_3px_0_0_var(--att)]",
  info: null,
};

const GROUPS: { severity: Severity; title: string; count: [string, string] }[] = [
  { severity: "critical", title: "Critical", count: ["critical alert", "critical alerts"] },
  { severity: "warning", title: "Warnings", count: ["warning", "warnings"] },
  { severity: "info", title: "Information", count: ["information alert", "information alerts"] },
];

/** Câte alerte se văd din fiecare grup; restul stau sub „Încă N”. */
const SHOW_PER_GROUP = 4;
/** Câte lucrări legate se arată întregi; restul stau sub „Încă N lucrări”. */
const SHOW_LINKED = 3;

function safeTime(iso: string, fn: (s: string) => string): string {
  try {
    return fn(iso);
  } catch {
    return iso;
  }
}

interface Lookups {
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  scenario: string;
}

/** Lucrările legate de o alertă. O alertă poate strânge sute de lucrări, așa că primele trei se văd întregi, restul la cerere. */
function LinkedItems({ ids, workItemsById, decisionsByWorkItemId, scenario }: { ids: string[] } & Lookups) {
  const first = ids.slice(0, SHOW_LINKED);
  const rest = ids.slice(SHOW_LINKED);
  return (
    <div className="mt-2.5">
      <ul className="flex flex-col gap-1.5" aria-label="Work items linked to this alert">
        {first.map((id) => (
          <li key={id} className="min-w-0">
            <WorkItemRef id={id} workItem={workItemsById[id]} decision={decisionsByWorkItemId[id]} scenario={scenario} />
          </li>
        ))}
      </ul>
      {rest.length ? (
        <details className="group mt-2">
          <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 rounded-[4px] text-[15px] font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink [&::-webkit-details-marker]:hidden">
            <span className="group-open:hidden">Another {plural(rest.length, "work item", "work items")}</span>
            <span className="hidden group-open:inline">Hide {fmtInt(rest.length)}</span>
          </summary>
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1" aria-label="Other work items linked to this alert">
            {rest.map((id) => (
              <li key={id}>
                <WorkItemRef id={id} decision={decisionsByWorkItemId[id]} scenario={scenario} />
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}

function AlertItem({ a, ...lookups }: { a: Alert } & Lookups) {
  const ids = a.work_item_ids ?? [];
  const outcome = alertOutcomeRo(ids, lookups.decisionsByWorkItemId);
  return (
    <li className={cn("grid grid-cols-[152px_minmax(0,1fr)] gap-x-5 py-4 pr-7 pl-7", BAR[a.severity])}>
      <div className="text-[14.5px] leading-snug">
        <span className={cn("flex items-center gap-2 text-[16px] font-[650]", TONE[a.severity])}>
          <SeverityIcon severity={a.severity} />
          {SEVERITY_RO[a.severity]}
        </span>
        <span className="mt-1.5 block text-muted-foreground">
          <time dateTime={a.created_at} title={safeTime(a.created_at, fmtMoment)} className="tabular-nums">
            {safeTime(a.created_at, fmtTime)}
          </time>
          , {CHANNEL_RO[a.channel] ?? a.channel}
        </span>
      </div>
      <div className="min-w-0">
        <h4 className="text-[18px] leading-snug font-[620]">{englishText(a.title_ro)}</h4>
        <p className="mt-1 max-w-[82ch] text-[16px] leading-relaxed">{englishText(a.body_ro)}</p>
        {outcome ? (
          <p className="mt-1 text-[15px]">
            <span className="text-muted-foreground">Agent decision: </span>
            {englishText(outcome)}
          </p>
        ) : null}
        {ids.length ? <LinkedItems ids={ids} {...lookups} /> : null}
        {a.channel === "clienti" ? (
          <div className="mt-2.5">
            <DemoStamp />
          </div>
        ) : null}
      </div>
    </li>
  );
}

/** Alertele planului, pe gravitate, cele mai grave primele. Gravitatea se vede din formă, cuvânt și culoare, niciodată doar din culoare. */
export function AlertList({ alerts, ...lookups }: { alerts: Alert[] } & Lookups) {
  const groups = GROUPS.map((g) => ({ ...g, items: alerts.filter((a) => a.severity === g.severity) })).filter((g) => g.items.length);

  return (
    <section aria-labelledby="alerte-titlu" className="min-w-0">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 px-7 pt-6 pb-3">
        <div>
          <h2 id="alerte-titlu" className="flex items-center gap-2.5 text-[21px] font-[650] tracking-[-0.005em]">
            Alerts <CountPill n={alerts.length} />
          </h2>
          <p className="mt-0.5 text-[15px] text-muted-foreground">Highest severity first.</p>
        </div>
        {groups.length ? (
          <ul aria-label="Alerts by severity" className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[15px]">
            {groups.map((g) => (
              <li key={g.severity} className="flex items-center gap-2">
                <SeverityIcon severity={g.severity} size={18} />
                <span className={cn("font-[600] tabular-nums", TONE[g.severity])}>{plural(g.items.length, ...g.count)}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {groups.length ? (
        <div className="border-t border-rule">
          {groups.map((g) => (
            <section key={g.severity} aria-label={`${g.title}, ${plural(g.items.length, ...g.count)}`}>
              <h3 className="flex items-center gap-2 border-b border-rule bg-canvas px-7 py-2 text-[15.5px] font-[620]">
                <SeverityIcon severity={g.severity} size={16} />
                {g.title}
                <span className="font-[500] text-muted-foreground tabular-nums">{g.items.length}</span>
              </h3>
              <ol className="divide-y divide-rule border-b border-rule bg-panel">
                {g.items.slice(0, SHOW_PER_GROUP).map((a) => (
                  <AlertItem key={a.alert_id} a={a} {...lookups} />
                ))}
              </ol>
              {g.items.length > SHOW_PER_GROUP ? (
                <details className="group border-b border-rule bg-panel">
                  <summary className="flex cursor-pointer list-none items-center px-7 py-3 text-[15px] font-[600] hover:bg-muted [&::-webkit-details-marker]:hidden">
                    <span className="underline decoration-rule underline-offset-4 group-open:hidden">
                      Another {plural(g.items.length - SHOW_PER_GROUP, ...g.count)}
                    </span>
                    <span className="hidden underline decoration-rule underline-offset-4 group-open:inline">Hide additional alerts</span>
                  </summary>
                  <ol className="divide-y divide-rule border-t border-rule">
                    {g.items.slice(SHOW_PER_GROUP).map((a) => (
                      <AlertItem key={a.alert_id} a={a} {...lookups} />
                    ))}
                  </ol>
                </details>
              ) : null}
            </section>
          ))}
        </div>
      ) : (
        <div className="border-y border-rule bg-panel px-7 py-10">
          <p className="text-[17px] font-[600]">No alerts for this plan.</p>
          <p className="mt-1 max-w-[70ch] text-[15.5px] text-muted-foreground">
            Alerts appear for safety risks, approaching storms or unavailable data.
          </p>
        </div>
      )}
    </section>
  );
}
