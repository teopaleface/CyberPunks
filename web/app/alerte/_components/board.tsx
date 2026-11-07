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
  SendIcon,
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
  if (w.asset_type === "meter") return `Contor ${w.asset_id}`;
  if (w.asset_type === "transformer_post") return itemPlace(w);
  return itemTitle(w);
}

const q = (s: string) => `?scenariu=${encodeURIComponent(s)}`;
const lucrare = (id: string, s: string) => `/lucrari/${encodeURIComponent(id)}${q(s)}`;

function DraftPill({ size = "md" }: { size?: "sm" | "md" }) {
  return (
    <Pill tone="violet" icon={FileTextIcon} size={size}>
      Ne trimis – ciornă
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
            Alertă meteorologică
          </Eyebrow>
          <h2 className="text-[26px] leading-tight font-[700] tracking-[-0.02em]">{storm.title_ro}</h2>
          {window ? (
            <p className="flex items-center gap-3 text-[28px] leading-none font-[700] tracking-[-0.02em] tabular-nums">
              <ClockIcon size={28} aria-hidden="true" />
              <span>
                <span className="sr-only">Fereastra de risc: </span>
                {window}
              </span>
            </p>
          ) : null}
          <p className="max-w-[60ch] text-[16px] leading-relaxed text-ink-soft">{storm.body_ro}</p>
          <div className="mt-auto flex flex-col gap-3 pt-1">
            <div>
              {waiting ? (
                <Pill tone="orange" icon={CircleUserRoundIcon} size="lg">
                  Decizie umană: în așteptare
                </Pill>
              ) : stormDecision ? (
                <Pill tone="green" size="lg">
                  Decizia: {DECISION_LABEL_RO[stormDecision.decision]}
                </Pill>
              ) : null}
            </div>
            <div className="flex flex-wrap gap-3">
              <Link href={lucrare(stormId, scenario)} className={btn("primary")}>
                Vezi lucrarea
              </Link>
              {waiting ? (
                <Link href={`/coada${q(scenario)}`} className={btn("danger")}>
                  Deschide De decis
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
              Mesaj de grup țintit
            </Eyebrow>
            <DraftPill />
          </div>
          <h2 className="text-[26px] leading-tight font-[700] tracking-[-0.02em]">
            Către prosumatorii de la <span translate="no">{msg.asset_id}</span>
          </h2>
          <p className="text-[16px] leading-relaxed text-ink-soft">{msg.message_ro}</p>
          <div className="mt-auto flex flex-wrap items-center gap-x-5 gap-y-3 pt-1">
            <span className="flex items-center gap-2.5 text-[17px] font-[600]">
              <MapPinIcon size={20} aria-hidden="true" className="text-[#8db8ff]" />
              <span translate="no">{msg.asset_id}</span>
            </span>
            {p90 !== null ? (
              <>
                <Stat icon={ZapIcon} tone="amber" value={`${p90} V`} label="P90 actual" />
                <Stat icon={BoltIcon} tone="blue" value={`> ${limit} V`} label="Limita" />
              </>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <button type="button" disabled aria-describedby="demo-nota" className={btn("primary")}>
              <SendIcon size={18} aria-hidden="true" />
              Trimite mesajul
            </button>
            <p id="demo-nota" className="text-[14.5px] text-ink-soft">
              În demo nu se trimite nimic.
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
              Oferte baterii
            </Eyebrow>
            <DraftPill />
          </div>
          <h2 className="text-[26px] leading-tight font-[700] tracking-[-0.02em]">PPC Energie: oferte de baterii</h2>
          <p className="text-[16px] text-ink-soft">
            Pentru prosumatorii din {offers.length === 1 ? "1 post" : `${fmtInt(offers.length)} posturi`} unde bateria coboară tensiunea de la prânz.
          </p>
          <div className="grid grid-cols-1 gap-4 pt-1 sm:grid-cols-3">
            <Stat icon={UsersIcon} tone="blue" value={fmtInt(tot.c)} label="prosumatori" />
            <Stat icon={ChartColumnIcon} tone="green" value={`${fmtInt(tot.kwh)} kWh`} label="baterii în total" />
            <Stat icon={CoinsIcon} tone="amber" value={fmtLei(tot.lei)} label="venit estimat" />
          </div>
          <div className="mt-auto flex flex-wrap gap-3 pt-2">
            <Link href={`/posturi/${encodeURIComponent(top.post_id)}${q(scenario)}`} className={btn("primary")}>
              Vezi postul <span translate="no">{top.post_id}</span>
            </Link>
            <DetailDialog
              trigger="Detalii"
              triggerClassName={btn("outline")}
              title="Oferte de baterii pentru PPC Energie"
              description="Posturile unde o baterie la prosumatori coboară tensiunea, cu efectul pe P90 și venitul estimat."
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
    statusRows.push({ key: "al", icon: BoltIcon, tone: "blue", text: storm.title_ro, pill: <Pill tone="blue" size="sm">Alertă în consolă</Pill> });
  }
  for (const [aud, label] of [["echipa", "Mesaj către echipă"], ["prosumatori", "Mesaj către prosumatori"], ["clienti_zona", "Mesaj către clienții din zonă"]] as const) {
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
            {count > 1 ? <span className="text-ink-soft"> și încă {fmtInt(count - 1)}</span> : null}
          </>
        ),
        pill: <DraftPill size="sm" />,
      });
    }
  }
  if (offers.length) {
    statusRows.push({ key: "of", icon: GiftIcon, tone: "amber", text: "Oferte baterii – PPC Energie", pill: <DraftPill size="sm" /> });
  }
  if (statusRows.length) {
    cards.push({
      id: "trimiteri",
      tags: ["trimiteri", "mesaje"],
      span: "lg:col-span-3",
      node: (
        <Card title="Starea trimiterilor" icon={FileTextIcon} className="rounded-[18px]">
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
          <p className="mt-3 text-[14px] text-ink-soft">Consola nu trimite mesaje în demo; alertele rămân în consolă, la dispecerat.</p>
        </Card>
      ),
    });
  }

  if (msgRemedy && p90 !== null) {
    const over = p90 - limit;
    cards.push({
      id: "indicatori",
      tags: ["mesaje", "alerte"],
      span: "lg:col-span-2",
      node: (
        <Card title={<><span translate="no">{msgRemedy.post_id}</span>: indicatori</>} icon={MapPinIcon} className="rounded-[18px]">
          <dl className="flex flex-col gap-2.5">
            {[
              ["Tensiunea P90 actuală", `${p90} V`, "blue" as Tone],
              ["Limita de tensiune", `${limit} V`, "violet" as Tone],
              ["Depășire", over > 0 ? `+${over} V` : `${over} V`, "amber" as Tone],
            ].map(([k, v, tone]) => (
              <div key={k as string} className="flex items-center justify-between gap-3 border-b border-rule pb-2.5 last:border-b-0 last:pb-0">
                <dt className="text-[16px]">{k}</dt>
                <dd>
                  <Pill tone={tone as Tone} size="lg" className="min-w-[96px] justify-center tabular-nums">
                    {v}
                  </Pill>
                </dd>
              </div>
            ))}
          </dl>
        </Card>
      ),
    });
  }

  if (offers.length) {
    cards.push({
      id: "venit",
      tags: ["oferte"],
      span: "lg:col-span-2",
      node: (
        <Card title="Venit estimat" icon={ChartColumnIcon} className="rounded-[18px]">
          <p className="text-[40px] leading-tight font-[700] tracking-[-0.02em] tabular-nums">{fmtLei(tot.lei)}</p>
          <p className="mt-2 text-[16px] leading-relaxed text-ink-soft">
            Din oferte de baterii: {fmtInt(tot.c)} prosumatori vizați, {fmtInt(tot.kwh)} kWh de baterii, în {offers.length === 1 ? "1 post" : `${fmtInt(offers.length)} posturi`}. Venitul e suma estimărilor
            din scara de soluții; rata de acceptare e o ipoteză din config.
          </p>
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
          title="Decizii necesare"
          icon={CircleUserRoundIcon}
          iconTone="orange"
          className="rounded-[18px]"
          action={
            <Link href={`/coada${q(scenario)}`} className="text-[14.5px] font-[600] text-[#8db8ff] underline decoration-rule underline-offset-4 hover:decoration-current">
              Toate ({fmtInt(pending.length)})
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
                    În așteptare
                  </Pill>
                </li>
              );
            })}
          </ul>
          {pending.length > PENDING_SHOWN ? <p className="mt-2 text-[14px] text-ink-soft">Încă {fmtInt(pending.length - PENDING_SHOWN)} în coadă.</p> : null}
        </Card>
      ),
    });
  }

  return (
    <ChipGrid
      label="Filtrează cardurile"
      chips={[
        { id: "alerte", label: "Alerte", tone: "blue" },
        { id: "mesaje", label: "Mesaje", tone: "violet" },
        { id: "oferte", label: "Oferte", tone: "amber" },
        { id: "decizii", label: "Decizii umane", tone: "orange" },
        { id: "trimiteri", label: "Trimiteri", tone: "blue" },
      ]}
      cards={cards}
    />
  );
}
