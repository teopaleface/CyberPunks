import { CircleAlert, Gauge as GaugeIcon, Waypoints } from "lucide-react";
import { Card, Dot, KV, Pill, SOURCE_TONE, type Tone } from "@/components/ds";
import { fmtDateLong, fmtDec, fmtLei, fmtTime } from "@/lib/format";
import { roundPct } from "@/lib/human";
import { ruleRo } from "@/lib/data/labels";
import type { OrderStop, OrderView } from "@/lib/orders-view";

/** Coloana din dreapta (cărți închise); nu se tipărește. */
export function OrderSide({ order, planDate, selected }: { order: OrderView; planDate: string; selected: OrderStop | null }) {
  const depot = order.depot?.label_ro.replace(/\s*\(simulată\)/i, "") ?? "—";
  const interval = order.departAt && order.returnAt ? `${fmtTime(order.departAt)} – ${fmtTime(order.returnAt)}` : "—";
  return (
    <div className="space-y-5">
      <Card title="Detalii lucrare" icon={CircleAlert} iconTone="blue" bodyClassName="pt-1">
        <KV k="Echipa" v={<span translate="no">{order.crewId}</span>} />
        <KV k="Data" v={`${fmtDateLong(planDate)} (sintetic)`} />
        <KV k="Baza" v={depot} />
        <KV k="Interval total" v={interval} />
        <KV k="Distanță" v={`${fmtDec(order.totalKm, 1)} km`} />
        <KV k="Opriri" v={order.stops.length} />
      </Card>
      {selected ? (
        <Card title="Activul vizat" icon={GaugeIcon} iconTone="blue" bodyClassName="pt-1">
          <KV k="Activ" v={<span translate="no">{selected.assetId}</span>} />
          <KV k="Localitate" v={selected.place || "—"} />
          {selected.predictionLabel ? (
            <KV k="Stare" v={<Pill tone="violet">{selected.predictionLabel}{selected.score != null ? ` ${roundPct(selected.score)}` : ""}</Pill>} />
          ) : null}
          {selected.ruleId ? <KV k="Regulă" v={<span title={ruleRo(selected.ruleId) ?? undefined} translate="no">{selected.ruleId}</span>} /> : null}
          {selected.costLei != null ? <KV k="Cost" v={<Pill tone="amber">{fmtLei(selected.costLei)}</Pill>} /> : null}
        </Card>
      ) : null}
      <Card title="Traseu (sinteză)" icon={Waypoints} iconTone="blue" bodyClassName="pt-1">
        <ol>
          {order.stops.map((s) => {
            const tone: Tone = s.source ? SOURCE_TONE[s.source] : "grey";
            return (
              <li key={s.workItemId} className="flex items-center gap-3 border-b border-rule py-2.5 text-[15.5px] last:border-b-0">
                <Dot tone={tone} className="size-3.5" />
                <span className="min-w-0 flex-1 truncate font-[560]" translate="no">{s.assetId}</span>
                <span className="font-[600] tabular-nums">{fmtTime(s.eta)}</span>
              </li>
            );
          })}
          <li className="flex items-center gap-3 py-2.5 text-[15.5px]">
            <Dot tone="grey" className="size-3.5" />
            <span className="flex-1 font-[560]">întoarcere</span>
            <span className="font-[600] tabular-nums">{order.returnAt ? fmtTime(order.returnAt) : "—"}</span>
          </li>
        </ol>
      </Card>
    </div>
  );
}
