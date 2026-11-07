import { cn } from "cn";
import type { Alert, Decision, WorkItem } from "@/lib/contracts";
import { fmtInt, fmtMoment, fmtTime, plural } from "@/lib/format";
import { CountPill, DemoStamp, SEVERITY_ORDER, SEVERITY_RO, SeverityIcon, WorkItemRef, type Severity } from "./parts";

const CHANNEL_RO: Record<Alert["channel"], string> = {
  dispecerat: "către dispecerat",
  echipa: "către echipă",
  clienti: "către clienți",
};

const TONE: Record<Severity, string> = {
  critical: "text-destructive",
  warning: "text-att-ink",
  info: "text-ink",
};

const BAR: Record<Severity, string | null> = {
  critical: "shadow-[inset_3px_0_0_var(--destructive)] bg-[color-mix(in_oklab,var(--destructive)_5%,var(--panel))]",
  warning: "shadow-[inset_3px_0_0_var(--att)]",
  info: null,
};

const COUNT_RO: Record<Severity, [string, string]> = {
  critical: ["critică", "critice"],
  warning: ["avertisment", "avertismente"],
  info: ["informare", "informări"],
};

function safeTime(iso: string, fn: (s: string) => string): string {
  try {
    return fn(iso);
  } catch {
    return iso;
  }
}

/** Câte lucrări legate se arată întregi; restul stau sub „Încă N lucrări”. */
const SHOW_LINKED = 3;

/** Lucrările legate de o alertă. O alertă poate strânge sute de lucrări, așa că primele trei se văd întregi, restul la cerere. */
function LinkedItems({
  ids,
  workItemsById,
  decisionsByWorkItemId,
  scenario,
}: {
  ids: string[];
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  scenario: string;
}) {
  const first = ids.slice(0, SHOW_LINKED);
  const rest = ids.slice(SHOW_LINKED);
  return (
    <div className="mt-2.5">
      <ul className="flex flex-col gap-1.5" aria-label="Lucrările legate de alertă">
        {first.map((id) => (
          <li key={id} className="min-w-0">
            <WorkItemRef id={id} workItem={workItemsById[id]} decision={decisionsByWorkItemId[id]} scenario={scenario} />
          </li>
        ))}
      </ul>
      {rest.length ? (
        <details className="group mt-2">
          <summary className="inline-flex cursor-pointer list-none items-center gap-1.5 rounded-[4px] text-[15px] font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink [&::-webkit-details-marker]:hidden">
            <span className="group-open:hidden">Încă {plural(rest.length, "lucrare", "lucrări")}</span>
            <span className="hidden group-open:inline">Ascunde cele {fmtInt(rest.length)}</span>
          </summary>
          <ul className="mt-2 flex flex-wrap gap-x-5 gap-y-1" aria-label="Celelalte lucrări legate de alertă">
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

/** Alertele planului, cele mai grave primele. Gravitatea se vede din formă, cuvânt și culoare, niciodată doar din culoare. */
export function AlertList({
  alerts,
  workItemsById,
  decisionsByWorkItemId,
  scenario,
}: {
  alerts: Alert[];
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  scenario: string;
}) {
  const sorted = alerts.toSorted((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  const counts = (["critical", "warning", "info"] as const)
    .map((s) => ({ s, n: alerts.filter((a) => a.severity === s).length }))
    .filter((c) => c.n > 0);

  return (
    <section aria-labelledby="alerte-titlu" className="min-w-0">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 px-7 pt-6 pb-3">
        <div>
          <h2 id="alerte-titlu" className="flex items-center gap-2.5 text-[21px] font-[650] tracking-[-0.005em]">
            Alerte <CountPill n={alerts.length} />
          </h2>
          <p className="mt-0.5 text-[15px] text-muted-foreground">Pentru dispecerat și echipe, cele mai grave primele.</p>
        </div>
        {counts.length ? (
          <ul aria-label="Alerte după gravitate" className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[15px]">
            {counts.map(({ s, n }) => (
              <li key={s} className="flex items-center gap-2">
                <SeverityIcon severity={s} size={18} />
                <span className={cn("font-[600] tabular-nums", TONE[s])}>{plural(n, ...COUNT_RO[s])}</span>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      {sorted.length ? (
        <ol className="divide-y divide-rule border-y border-rule bg-panel">
          {sorted.map((a) => {
            const ids = a.work_item_ids ?? [];
            return (
              <li key={a.alert_id} className={cn("grid grid-cols-[152px_minmax(0,1fr)] gap-x-5 py-4 pr-7 pl-7", BAR[a.severity])}>
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
                  <h3 className="text-[18px] leading-snug font-[620]">{a.title_ro}</h3>
                  <p className="mt-1 max-w-[82ch] text-[16px] leading-relaxed">{a.body_ro}</p>
                  {ids.length ? (
                    <LinkedItems
                      ids={ids}
                      workItemsById={workItemsById}
                      decisionsByWorkItemId={decisionsByWorkItemId}
                      scenario={scenario}
                    />
                  ) : null}
                  {a.channel === "clienti" ? (
                    <div className="mt-2.5">
                      <DemoStamp />
                    </div>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      ) : (
        <div className="border-y border-rule bg-panel px-7 py-10">
          <p className="text-[17px] font-[600]">Nicio alertă pentru planul acesta.</p>
          <p className="mt-1 max-w-[70ch] text-[15.5px] text-muted-foreground">
            Alertele apar când agentul vede un risc pentru oameni, o furtună care se apropie sau o sursă de date care lipsește.
          </p>
        </div>
      )}
    </section>
  );
}
