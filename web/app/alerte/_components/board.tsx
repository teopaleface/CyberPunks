import { englishText } from "@/lib/english";
import {
  BoltIcon,
  ChartColumnIcon,
  CircleUserRoundIcon,
  ClockIcon,
  CloudLightningIcon,
  CoinsIcon,
  FileTextIcon,
  GiftIcon,
  MapPinIcon,
  MessageSquareIcon,
  UsersIcon,
  ZapIcon,
} from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { Card, Pill, btn, type Tone } from "@/components/ds";
import { ChipGrid, type GridCard } from "@/components/misc/chip-grid";
import { DetailDialog } from "@/components/misc/detail-dialog";
import type { Alert, Decision, Notification, WorkItem } from "@/lib/contracts";
import { DECISION_LABEL_RO } from "@/lib/data/labels";
import type { RemedyChoice } from "@/lib/data/remedies";
import { fmtInt, fmtLei, fmtTime } from "@/lib/format";
import { CopyMessage } from "./copy-message";
import { BatteryOffers } from "./battery-offers";
import { itemPlace, itemTitle } from "@/lib/plan-screen";

/** Limita de supratensiune, în volți: 1,10 pu × 230 V. */
const LIMIT_PU = 1.1;
const volts = (pu: number) => Math.round(pu * 230);

interface Props {
  alerts: Alert[];
  notifications: Notification[];
  workItemsById: Record<string, WorkItem>;
  decisionsByWorkItemId: Record<string, Decision>;
  remedies: RemedyChoice[];
  scenario: string;
}

/** Ce așteaptă decizia, pe scurt: contorul, postul cu locul lui, zona. */
function pendingTitle(w: WorkItem): string {
  if (w.asset_type === "meter") return `Meter ${w.asset_id}`;
  if (w.asset_type === "transformer_post") return itemPlace(w);
  return englishText(itemTitle(w));
}

const q = (s: string) => `?scenariu=${encodeURIComponent(s)}`;
const lucrare = (id: string, s: string) => `/lucrari/${encodeURIComponent(id)}${q(s)}`;

function DraftPill({ size = "md" }: { size?: "sm" | "md" }) {
  return (
    <Pill tone="violet" icon={FileTextIcon} size={size}>
      Unsent draft
    </Pill>
  );
}

function Stat({ icon: Icon, tone, value, label }: { icon: typeof ZapIcon; tone: Tone; value: ReactNode; label: string }) {
  const color = { blue: "text-[#8db8ff]", violet: "text-[#d6a8f0]", amber: "text-[#f5c66b]", green: "text-[#7ee2a0]", orange: "text-[#ffa27c]", red: "text-[#ff9b9b]", grey: "text-ink-soft" }[tone];
  return (
    <div className="flex min-w-0 items-center gap-3 border-l border-rule pl-4 first:border-l-0 first:pl-0">
      <Icon size={28} strokeWidth={1.6} aria-hidden="true" className={`shrink-0 ${color}`} />
      <div className="min-w-0">
        <p className="text-[24px] leading-tight font-[700] tracking-[-0.02em] whitespace-nowrap tabular-nums">{value}</p>
        <p className="text-[14.5px] text-ink-soft">{label}</p>
      </div>
    </div>
  );
}

function Eyebrow({ icon: Icon, tone, children }: { icon: typeof ZapIcon; tone: Tone; children: ReactNode }) {
  const color = { blue: "text-[#6fa6ff]", violet: "text-[#c58bf0]", amber: "text-[#f5c66b]", green: "text-[#7ee2a0]", orange: "text-[#ffa27c]", red: "text-[#ff9b9b]", grey: "text-ink-soft" }[tone];
  return (
    <p className="flex items-center gap-3 text-[16px] text-ink-soft">
      <Icon size={22} strokeWidth={1.7} aria-hidden="true" className={color} />
      {children}
    </p>
  );
}

export function AlertsBoard({ alerts, notifications, workItemsById, decisionsByWorkItemId, remedies, scenario }: Props) {
  const isHuman = (id: string) => decisionsByWorkItemId[id]?.decision === "human_review";

  // Alerta de furtună din B: cea care așteaptă un om, altfel prima.
  const storms = alerts.filter((a) => (a.work_item_ids ?? []).length === 1 && a.work_item_ids?.[0]?.startsWith("B-"));
  const storm = storms.find((a) => isHuman(a.work_item_ids![0])) ?? storms[0] ?? null;
  const stormId = storm?.work_item_ids?.[0] ?? null;
  const stormItem = stormId ? workItemsById[stormId] : undefined;
  const stormDecision = stormId ? decisionsByWorkItemId[stormId] : undefined;
  const window = stormItem?.time_window ? `${fmtTime(stormItem.time_window.start)} – ${fmtTime(stormItem.time_window.end)}` : null;

  // Mesajul către prosumatori: primul care are cifre de tensiune pentru postul lui.
  const remedyOf = (n: Notification) => remedies.find((r) => r.work_item_id === n.work_item_id || r.post_id === n.asset_id);
  const prosumers = notifications.filter((n) => n.audience === "prosumatori");
  const msg = prosumers.find((n) => remedyOf(n)) ?? prosumers[0] ?? null;
  const msgRemedy = msg ? remedyOf(msg) : undefined;
  const p90 = msgRemedy ? volts(msgRemedy.p90_before_pu) : null;
  const limit = volts(LIMIT_PU);

  // Ofertele de baterii, din scara de soluții.
  const offers = remedies
    .filter((r) => r.battery && (r.battery.customers_targeted ?? 0) > 0)
    .toSorted((a, b) => a.p90_after_pu - b.p90_after_pu || (b.battery?.revenue_lei ?? 0) - (a.battery?.revenue_lei ?? 0));
  const tot = offers.reduce(
    (t, r) => ({ c: t.c + (r.battery?.customers_targeted ?? 0), kwh: t.kwh + (r.battery?.battery_kwh_total ?? 0), lei: t.lei + (r.battery?.revenue_lei ?? 0) }),
    { c: 0, kwh: 0, lei: 0 },
  );

  // Deciziile care așteaptă un om, legate de alerte.
  const pending = [...new Set(alerts.flatMap((a) => a.work_item_ids ?? []))].filter(isHuman);
  const PENDING_SHOWN = 4;

  const cards: GridCard[] = [];

  if (storm && stormId) {
    const waiting = isHuman(stormId);
    cards.push({
      id: "furtuna",
      tags: ["alerte", ...(waiting ? ["decizii"] : [])],
      span: "lg:col-span-3",
      node: (
        <Card className="rounded-[18px]" bodyClassName="flex h-full flex-col gap-3 p-5">
          <Eyebrow icon={CloudLightningIcon} tone="blue">
            Weather alert
          </Eyebrow>
          <h2 className="text-[26px] leading-tight font-[700] tracking-[-0.02em]">{englishText(storm.title_ro)}</h2>
          {window ? (
            <p className="flex items-center gap-3 text-[28px] leading-none font-[700] tracking-[-0.02em] tabular-nums">
              <ClockIcon size={28} aria-hidden="true" />
              <span>
                <span className="sr-only">Risk window: </span>
                {window}
              </span>
            </p>
          ) : null}
          <p className="max-w-[60ch] text-[16px] leading-relaxed text-ink-soft">{englishText(storm.body_ro)}</p>
          <div className="mt-auto flex flex-col gap-3 pt-1">
            <div>
              {waiting ? (
                <Pill tone="orange" icon={CircleUserRoundIcon} size="lg">
                  Human decision pending
                </Pill>
              ) : stormDecision ? (
                <Pill tone="green" size="lg">
                  Decision: {DECISION_LABEL_RO[stormDecision.decision]}
                </Pill>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href={lucrare(stormId, scenario)} className={btn("primary")}>
                View work item
              </Link>
              {waiting ? (
                <Link href={`/coada${q(scenario)}`} className={btn("danger")}>
                  Open review queue
                </Link>
              ) : null}
            </div>
          </div>
        </Card>
      ),
    });
  }

  if (msg) {
    cards.push({
      id: "mesaj",
      tags: ["mesaje", "trimiteri"],
      span: "lg:col-span-3",
      node: (
        <Card className="rounded-[18px]" bodyClassName="flex h-full flex-col gap-3 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <Eyebrow icon={MessageSquareIcon} tone="violet">
              Targeted group message
            </Eyebrow>
            <DraftPill />
          </div>
          <h2 className="text-[26px] leading-tight font-[700] tracking-[-0.02em]">
            To prosumers at <span translate="no">{msg.asset_id}</span>
          </h2>
          <p className="text-[16px] leading-relaxed text-ink-soft">{englishText(msg.message_ro)}</p>
          <div className="mt-auto flex flex-wrap items-center gap-x-5 gap-y-3 pt-1">
            <span className="flex items-center gap-2.5 text-[17px] font-[600]">
              <MapPinIcon size={20} aria-hidden="true" className="text-[#8db8ff]" />
              <span translate="no">{msg.asset_id}</span>
            </span>
            {p90 !== null ? (
              <>
                <Stat icon={ZapIcon} tone="amber" value={`${p90} V`} label="Current P90" />
                <Stat icon={BoltIcon} tone="blue" value={`${limit} V`} label="Limit" />
                <Stat icon={ZapIcon} tone="amber" value={`${p90 > limit ? "+" : ""}${p90 - limit} V`} label="Above limit" />
              </>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <CopyMessage text={englishText(msg.message_ro)} noteId="demo-nota" />
            <p id="demo-nota" className="text-[14.5px] text-ink-soft">
              Demo messages are not sent.
            </p>
          </div>
        </Card>
      ),
    });
  }

  if (offers.length) {
    const top = offers[0];
    cards.push({
      id: "oferte",
      tags: ["oferte", "trimiteri"],
      span: "lg:col-span-3",
      node: (
        <Card className="rounded-[18px]" bodyClassName="flex h-full flex-col gap-3 p-5">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <Eyebrow icon={GiftIcon} tone="amber">
              Battery offers
            </Eyebrow>
            <DraftPill />
          </div>
          <p className="text-[16px] text-ink-soft">
            For prosumers at {offers.length === 1 ? "1 substation" : `${fmtInt(offers.length)} substations`} where batteries reduce midday voltage.
          </p>
          <div className="grid grid-cols-1 gap-4 pt-1 sm:grid-cols-3">
            <Stat icon={UsersIcon} tone="blue" value={fmtInt(tot.c)} label="prosumers" />
            <Stat icon={ChartColumnIcon} tone="green" value={`${fmtInt(tot.kwh)} kWh`} label="batteries in total" />
            <Stat icon={CoinsIcon} tone="amber" value={fmtLei(tot.lei)} label="estimated revenue" />
          </div>
          <p className="text-[13px] leading-relaxed text-ink-soft">Revenue sums remedy estimates. Offer acceptance is a configured assumption.</p>
          <div className="mt-auto flex flex-wrap gap-3 pt-2">
            <Link href={`/posturi/${encodeURIComponent(top.post_id)}${q(scenario)}`} className={btn("primary")}>
              View substation <span translate="no">{top.post_id}</span>
            </Link>
            <DetailDialog
              trigger="Details"
              triggerClassName={btn("outline")}
              title="Battery offers for PPC Energie"
              description="Substations where batteries reduce voltage, with P90 effect and estimated revenue."
            >
              <BatteryOffers remedies={remedies} scenario={scenario} bare />
            </DetailDialog>
          </div>
        </Card>
      ),
    });
  }

  // Starea trimiterilor: un rând din fiecare fel, cu numărul total.
  const firstOf = (aud: Notification["audience"]) => notifications.find((n) => n.audience === aud);
  const statusRows: { key: string; icon: typeof ZapIcon; tone: Tone; text: ReactNode; pill: ReactNode }[] = [];
  if (storm) {
    statusRows.push({ key: "al", icon: BoltIcon, tone: "blue", text: englishText(storm.title_ro), pill: <Pill tone="blue" size="sm">Console alert</Pill> });
  }
  for (const [aud, label] of [["echipa", "Crew message"], ["prosumatori", "Prosumer message"], ["clienti_zona", "Message to local customers"]] as const) {
    const n = firstOf(aud);
    const count = notifications.filter((x) => x.audience === aud).length;
    if (n) {
      statusRows.push({
        key: aud,
        icon: MessageSquareIcon,
        tone: "violet",
        text: (
          <>
            {label}: <span translate="no">{n.asset_id}</span>
            {count > 1 ? <span className="text-ink-soft"> and another {fmtInt(count - 1)}</span> : null}
          </>
        ),
        pill: <DraftPill size="sm" />,
      });
    }
  }
  if (offers.length) {
    statusRows.push({ key: "of", icon: GiftIcon, tone: "amber", text: "Battery offers · PPC Energie", pill: <DraftPill size="sm" /> });
  }
  if (statusRows.length) {
    cards.push({
      id: "trimiteri",
      tags: ["trimiteri", "mesaje"],
      span: "lg:col-span-3",
      node: (
        <Card title="Delivery status" icon={FileTextIcon} className="rounded-[18px]">
          <ul className="flex flex-col gap-2.5">
            {statusRows.map((r) => (
              <li key={r.key} className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 rounded-[12px] border border-rule bg-surface-2 px-4 py-3">
                <span className="flex min-w-0 items-center gap-3 text-[16px]">
                  <r.icon size={22} strokeWidth={1.7} aria-hidden="true" className="shrink-0 text-ink-soft" />
                  <span className="min-w-0">{r.text}</span>
                </span>
                {r.pill}
              </li>
            ))}
          </ul>
          <p className="mt-3 text-[14px] text-ink-soft">Demo messages are not sent. Alerts stay in the dispatcher console.</p>
        </Card>
      ),
    });
  }

  if (pending.length) {
    cards.push({
      id: "decizii",
      tags: ["decizii"],
      span: "lg:col-span-2",
      node: (
        <Card
          title="Decisions needed"
          icon={CircleUserRoundIcon}
          iconTone="orange"
          className="rounded-[18px]"
          action={
            <Link href={`/coada${q(scenario)}`} className="text-[14.5px] font-[600] text-[#8db8ff] underline decoration-rule underline-offset-4 hover:decoration-current">
              All ({fmtInt(pending.length)})
            </Link>
          }
        >
          <ul className="flex flex-col">
            {pending.slice(0, PENDING_SHOWN).map((id) => {
              const w = workItemsById[id];
              return (
                <li key={id} className="flex items-center justify-between gap-3 border-b border-rule py-2.5 first:pt-0 last:border-b-0">
                  <Link href={lucrare(id, scenario)} className="min-w-0 truncate text-[16px] hover:underline" title={id}>
                    {w ? pendingTitle(w) : <span translate="no">{id}</span>}
                  </Link>
                  <Pill tone="amber" size="sm" icon={ClockIcon}>
                    Pending
                  </Pill>
                </li>
              );
            })}
          </ul>
          {pending.length > PENDING_SHOWN ? <p className="mt-2 text-[14px] text-ink-soft">Another {fmtInt(pending.length - PENDING_SHOWN)} in the queue.</p> : null}
        </Card>
      ),
    });
  }

  return (
    <ChipGrid
      label="Filter cards"
      chips={[
        { id: "alerte", label: "Alerts", tone: "blue" },
        { id: "mesaje", label: "Messages", tone: "violet" },
        { id: "oferte", label: "Offers", tone: "amber" },
        { id: "decizii", label: "Human decisions", tone: "orange" },
        { id: "trimiteri", label: "Deliveries", tone: "blue" },
      ]}
      cards={cards}
    />
  );
}
