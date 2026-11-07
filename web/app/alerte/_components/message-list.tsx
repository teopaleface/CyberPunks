import { englishText } from "@/lib/english";
import type { Decision, Notification, WorkItem } from "@/lib/contracts";
import { fmtMoment, plural } from "@/lib/format";
import { itemPlace, itemTitle } from "@/lib/plan-screen";
import { CountPill, DemoStamp, WorkItemRef } from "./parts";

type Audience = Notification["audience"];

const GROUPS: { audience: Audience; title: string }[] = [
  { audience: "echipa", title: "Crews" },
  { audience: "prosumatori", title: "Prosumers" },
  { audience: "clienti_zona", title: "Local customers" },
];

const SUMMARY_RO: Record<Audience, [string, string]> = {
  echipa: ["to a crew", "to crews"],
  prosumatori: ["to prosumers", "to prosumers"],
  clienti_zona: ["to local customers", "to local customers"],
};

function safeMoment(iso: string): string {
  try {
    return fmtMoment(iso);
  } catch {
    return iso;
  }
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Localitatea, cu diacriticele din eticheta locului („PT-1269, Afumați (sintetic)” → „Afumați, Ilfov”). */
function placeOf(w: WorkItem): string {
  const label = w.location.label?.trim() ?? "";
  const rest = label
    .replace(new RegExp(`^(Contor\\s+)?${escapeRe(w.asset_id)},?\\s*`), "")
    .replace(/\s*\(sintetic\)\s*$/i, "")
    .trim();
  const county = w.location.county ?? "";
  if (!rest || w.asset_type === "zone") return itemPlace(w);
  return county && !rest.includes(county) ? `${rest}, ${county}` : rest;
}

/** Cui îi e scris mesajul, în cuvinte: echipa din plan, prosumatorii unui post, clienții unei zone. */
function recipient(n: Notification, w: WorkItem | undefined, d: Decision | undefined): string {
  if (n.audience === "echipa") {
    if (d?.crew_id) return `To crew ${d.crew_id}`;
    return `To the crew sent to ${w ? itemTitle(w) : n.asset_id}`;
  }
  if (n.audience === "prosumatori") return `To prosumers at ${n.asset_id}${w ? `, ${placeOf(w)}` : ""}`;
  return `To customers in ${w ? placeOf(w) : n.asset_id}`;
}

/** Câte mesaje se văd din fiecare grup; mesajele către prosumatori seamănă mult între ele. */
const SHOW_PER_GROUP = 3;

/** Un mesaj, ca o previzualizare: cui, textul întreg, când ar pleca, lucrarea din spate și eticheta de demo. */
function MessageItem({
  n,
  workItemsById,
  decisionsByWorkItemId,
  scenario,
}: {
  n: Notification;
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  scenario: string;
}) {
  const wid = n.work_item_id ?? null;
  const w = wid ? workItemsById[wid] : undefined;
  const d = wid ? decisionsByWorkItemId[wid] : undefined;
  const toCustomers = n.audience !== "echipa";
  return (
    <li className="px-7 py-4">
      <div className="flex max-w-[780px] items-start justify-between gap-4">
        <p className="pt-0.5 text-[16px] leading-snug font-[620]">{englishText(recipient(n, w, d))}</p>
        {n.demo_only !== false || toCustomers ? <DemoStamp /> : null}
      </div>
      <blockquote className="mt-2 max-w-[780px] rounded-[4px] border border-rule bg-popover px-4 py-3 text-[16px] leading-relaxed">
        {englishText(n.message_ro)}
      </blockquote>
      <div className="mt-2.5 flex flex-wrap items-center gap-x-6 gap-y-2 text-[14.5px] text-muted-foreground">
        <span>
          Scheduled for{" "}
          <time dateTime={n.scheduled_for} className="text-ink">
            {safeMoment(n.scheduled_for)}
          </time>
        </span>
        {wid ? (
          <WorkItemRef id={wid} workItem={w} decision={d} scenario={scenario} />
        ) : (
          <span>
            Asset <span translate="no" className="code-id text-ink">{n.asset_id}</span>
          </span>
        )}
      </div>
    </li>
  );
}

/** Mesajele pregătite de agent, pe destinatari. Doar demo: fiecare poartă eticheta „Demo, nu s-a trimis”. */
export function MessageList({
  notifications,
  workItemsById,
  decisionsByWorkItemId,
  scenario,
}: {
  notifications: Notification[];
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  scenario: string;
}) {
  const groups = GROUPS.map((g) => ({
    ...g,
    items: notifications
      .filter((n) => n.audience === g.audience)
      .toSorted((a, b) => a.scheduled_for.localeCompare(b.scheduled_for)),
  })).filter((g) => g.items.length > 0);
  const known = new Set(GROUPS.map((g) => g.audience));
  const other = notifications.filter((n) => !known.has(n.audience));
  if (other.length) groups.push({ audience: other[0].audience, title: "Other recipients", items: other });

  const summary = groups
    .filter((g) => known.has(g.audience))
    .map((g) => {
      const [one, many] = SUMMARY_RO[g.audience];
      return `${g.items.length} ${g.items.length === 1 ? one : many}`;
    })
    .join(", ");

  return (
    <section aria-labelledby="mesaje-titlu" className="min-w-0">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2 px-7 pt-6 pb-3">
        <div>
          <h2 id="mesaje-titlu" className="flex items-center gap-2.5 text-[21px] font-[650] tracking-[-0.005em]">
            Messages <CountPill n={notifications.length} />
          </h2>
          <p className="mt-0.5 text-[15px] text-muted-foreground">Prepared by the agent. No messages are sent in demo mode.</p>
        </div>
        {summary ? <p className="text-[15px] text-muted-foreground">{summary}</p> : null}
      </div>

      {groups.length ? (
        <div className="border-t border-rule">
          {groups.map((g) => (
            <section key={g.title} aria-label={`${g.title}, ${plural(g.items.length, "message", "messages")}`}>
              <h3 className="flex items-center gap-2 border-b border-rule bg-canvas px-7 py-2 text-[15.5px] font-[620]">
                {g.title}
                <span className="font-[500] text-muted-foreground tabular-nums">{g.items.length}</span>
              </h3>
              <ul className="divide-y divide-rule border-b border-rule bg-panel">
                {g.items.slice(0, SHOW_PER_GROUP).map((n) => (
                  <MessageItem key={n.notification_id} n={n} workItemsById={workItemsById} decisionsByWorkItemId={decisionsByWorkItemId} scenario={scenario} />
                ))}
              </ul>
              {g.items.length > SHOW_PER_GROUP ? (
                <details className="group border-b border-rule bg-panel">
                  <summary className="flex cursor-pointer list-none items-center gap-2 px-7 py-3 text-[15px] font-[600] hover:bg-muted [&::-webkit-details-marker]:hidden">
                    <span className="underline decoration-rule underline-offset-4 group-open:hidden">
                      Another {plural(g.items.length - SHOW_PER_GROUP, "message", "messages")} {SUMMARY_RO[g.audience]?.[1] ?? ""}
                    </span>
                    <span className="hidden underline decoration-rule underline-offset-4 group-open:inline">Hide additional messages</span>
                  </summary>
                  <ul className="divide-y divide-rule border-t border-rule">
                    {g.items.slice(SHOW_PER_GROUP).map((n) => (
                      <MessageItem key={n.notification_id} n={n} workItemsById={workItemsById} decisionsByWorkItemId={decisionsByWorkItemId} scenario={scenario} />
                    ))}
                  </ul>
                </details>
              ) : null}
            </section>
          ))}
        </div>
      ) : (
        <div className="border-y border-rule bg-panel px-7 py-10">
          <p className="text-[17px] font-[600]">No messages prepared.</p>
          <p className="mt-1 max-w-[70ch] text-[15.5px] text-muted-foreground">
            Messages appear when the agent assigns a crew or proposes a remote action.
          </p>
        </div>
      )}
    </section>
  );
}
