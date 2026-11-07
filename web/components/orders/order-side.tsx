import { englishText } from "@/lib/english";
import { CircleAlert, Gauge as GaugeIcon, Waypoints } from "lucide-react";
import { Card, Dot, KV, Pill, SOURCE_TONE, type Tone } from "@/components/ds";
import { fmtDateLong, fmtDec, fmtLei, fmtTime } from "@/lib/format";
import { roundPct } from "@/lib/human";
import { ruleRo } from "@/lib/data/labels";
import type { OrderStop, OrderView } from "@/lib/orders-view";

/** Coloana din dreapta (cărți închise); nu se tipărește. */
export function OrderSide({ order, planDate, selected }: { order: OrderView; planDate: string; selected: OrderStop | null }) {
  const depot = (order.depot ? englishText(order.depot.label_ro.replace(/\s*\(simulată\)/i, "")) : undefined) ?? "—";
  const interval = order.departAt && order.returnAt ? `${fmtTime(order.departAt)} – ${fmtTime(order.returnAt)}` : "—";
  return (
    <div className="space-y-5">
      <Card title="Work details" icon={CircleAlert} iconTone="blue" bodyClassName="pt-1">
        <KV k="Crew" v={<span translate="no">{order.crewId}</span>} />
        <KV k="Date" v={`${fmtDateLong(planDate)} (synthetic)`} />
        <KV k="Depot" v={depot} />
        <KV k="Total time" v={interval} />
        <KV k="Distance" v={`${fmtDec(order.totalKm, 1)} km`} />
        <KV k="Stops" v={order.stops.length} />
      </Card>
      {selected ? (
        <Card title="Target asset" icon={GaugeIcon} iconTone="blue" bodyClassName="pt-1">
          <KV k="Asset" v={<span translate="no">{selected.assetId}</span>} />
          <KV k="Locality" v={selected.place || "—"} />
          {selected.predictionLabel ? (
            <KV k="Status" v={<Pill tone="violet">{selected.predictionLabel}{selected.score != null ? ` ${roundPct(selected.score)}` : ""}</Pill>} />
          ) : null}
          {selected.ruleId ? <KV k="Rule" v={<span title={ruleRo(selected.ruleId) ?? undefined} translate="no">{selected.ruleId}</span>} /> : null}
          {selected.costLei != null ? <KV k="Cost" v={<Pill tone="amber">{fmtLei(selected.costLei)}</Pill>} /> : null}
        </Card>
      ) : null}
      <Card title="Route summary" icon={Waypoints} iconTone="blue" bodyClassName="pt-1">
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
            <span className="flex-1 font-[560]">return</span>
            <span className="font-[600] tabular-nums">{order.returnAt ? fmtTime(order.returnAt) : "—"}</span>
          </li>
        </ol>
      </Card>
    </div>
  );
}
