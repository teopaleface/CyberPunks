import { englishText } from "@/lib/english";
import { CalendarDays, CheckSquare, Coins, Flag, Gauge as GaugeIcon, MapPin, MessageSquare, PenLine, TriangleAlert, Warehouse, Wrench } from "lucide-react";
import Link from "next/link";
import { Fragment } from "react";
import { fmtDateLong, fmtLei, fmtTime } from "@/lib/format";
import { roundPct } from "@/lib/human";
import { buildChecklist, type OrderStop, type OrderView } from "@/lib/orders-view";

const BORDER: Record<string, string> = {
  A: "border-[#3986fc] bg-[#eef5ff] text-[#1d5fcf]",
  B: "border-[#ad5fd6] bg-[#f7eefc] text-[#8a3fb3]",
  C: "border-[#e59b15] bg-[#fff6e6] text-[#a8680a]",
};
const NEUTRAL = "border-slate-300 bg-slate-50 text-slate-600";

/** Foaia printabilă: fundal alb, text închis. Tot ce e în ea apare la tipărire. */
export function OrderPaper({ order, planDate, selected, scenario }: { order: OrderView; planDate: string; selected: OrderStop | null; scenario: string }) {
  const checks = buildChecklist(order);
  const q = (stop: string) => `?echipa=${encodeURIComponent(order.crewId)}&oprire=${encodeURIComponent(stop)}&scenariu=${encodeURIComponent(scenario)}`;
  const depotName = (order.depot ? englishText(order.depot.label_ro.replace(/\s*\(simulată\)/i, "")) : undefined) ?? "Unknown depot";
  return (
    <article id="order-paper" aria-label={`Work order ${order.crewId}`} className="rounded-[16px] bg-white p-7 text-[#0b1322] [color-scheme:light] max-md:p-4">
      <header className="flex items-center gap-5 border-b-2 border-slate-300 pb-4">
        <p className="text-[28px] font-[750] tracking-[-0.02em]" translate="no">Daybreak</p>
        <span aria-hidden="true" className="h-8 w-px bg-slate-300" />
        <p className="flex-1 text-[26px] font-[700] tracking-[-0.015em]">Work order</p>
        <p className="flex items-center gap-2 text-[17px] text-slate-700">
          <Wrench aria-hidden="true" size={22} strokeWidth={1.6} />  Field work
        </p>
      </header>

      <div className="grid grid-cols-3 gap-4 border-b-2 border-slate-300 py-4 max-md:grid-cols-1">
        <p className="flex items-center gap-3">
          <CalendarDays aria-hidden="true" size={34} strokeWidth={1.4} className="shrink-0 text-slate-700" />
          <span>
            <b className="block text-[24px] leading-tight" translate="no">{order.crewId}</b>
            <span className="text-[16px] text-slate-700">{fmtDateLong(planDate)}  (synthetic)</span>
          </span>
        </p>
        <p className="flex items-center gap-3 md:border-l md:border-slate-300 md:pl-5">
          <MapPin aria-hidden="true" size={30} strokeWidth={1.4} className="shrink-0 text-slate-700" />
          <b className="text-[19px] leading-tight">{depotName}</b>
        </p>
        <p className="flex items-center gap-3 md:border-l md:border-slate-300 md:pl-5">
          <Warehouse aria-hidden="true" size={30} strokeWidth={1.4} className="shrink-0 text-slate-700" />
          <span>
            <b className="block text-[19px] leading-tight">Departure from depot</b>
            <span className="text-[16px] text-slate-700">{order.departAt ? `at ${fmtTime(order.departAt)}` : "Unknown time"}</span>
          </span>
        </p>
      </div>

      <ol aria-label="Route" className="flex flex-wrap items-center gap-x-3 gap-y-3 py-4">
        {order.stops.map((s) => (
          <Fragment key={s.workItemId}>
            <li>
              <Link
                href={q(s.workItemId)}
                scroll={false}
                aria-current={selected?.workItemId === s.workItemId ? "true" : undefined}
                className={`flex min-w-[116px] flex-col items-center rounded-[10px] border-2 px-3 py-1.5 aria-[current=true]:ring-2 aria-[current=true]:ring-slate-900 ${BORDER[s.source ?? ""] ?? NEUTRAL}`}
              >
                <span className="flex items-center gap-1.5 text-[16px] font-[650]"><MapPin aria-hidden="true" size={16} /><span translate="no">{s.assetId}</span></span>
                <span className="text-[17px] font-[700] text-[#0b1322] tabular-nums">{fmtTime(s.eta)}</span>
              </Link>
            </li>
            <li aria-hidden="true" className="text-[22px] text-slate-700">→</li>
          </Fragment>
        ))}
        <li className="flex min-w-[116px] flex-col items-center rounded-[10px] border-2 border-slate-300 bg-slate-50 px-3 py-1.5">
          <span className="flex items-center gap-1.5 text-[16px] font-[650] text-slate-700"><Flag aria-hidden="true" size={16} />  return</span>
          <span className="text-[17px] font-[700] tabular-nums">{order.returnAt ? fmtTime(order.returnAt) : "—"}</span>
        </li>
      </ol>

      {selected ? (
        <div className="flex flex-wrap items-center gap-x-6 gap-y-3 rounded-[10px] border-2 border-slate-300 px-5 py-3">
          <p className="flex items-center gap-3">
            <GaugeIcon aria-hidden="true" size={34} strokeWidth={1.4} />
            <span><span className="block text-[14px] text-slate-700">Asset</span><b className="text-[22px] leading-tight whitespace-nowrap" translate="no">{selected.assetId}</b></span>
          </p>
          <p className="flex flex-1 items-center gap-2 text-[17px] font-[600]"><MapPin aria-hidden="true" size={20} />{selected.place}</p>
          <p className="flex items-center gap-2 text-[17px]">
            <TriangleAlert aria-hidden="true" size={22} className="text-[#d33b2c]" />
            {selected.predictionLabel ? <span className="rounded-full bg-[#efe3fb] px-3 py-0.5 font-[650] whitespace-nowrap text-[#6b2d98]">{selected.predictionLabel}{selected.score != null ? ` ${roundPct(selected.score)}` : ""}</span> : null}
          </p>
          <p className="text-[17px] font-[650] whitespace-nowrap" translate="no">{selected.ruleId ?? ""}</p>
          {selected.costLei != null ? (
            <p className="flex items-center gap-2">
              <Coins aria-hidden="true" size={28} strokeWidth={1.4} />
              <span><span className="block text-[14px] text-slate-700">Cost</span><b className="rounded-full bg-[#fbe9b8] px-3 py-0.5 text-[17px] whitespace-nowrap">{fmtLei(selected.costLei)}</b></span>
            </p>
          ) : <span />}
        </div>
      ) : null}

      <section aria-labelledby="verif" className="mt-4 rounded-[10px] border-2 border-slate-300 px-5 py-3">
        <h3 id="verif" className="flex items-center gap-2.5 text-[19px] font-[700]">
          <CheckSquare aria-hidden="true" size={24} strokeWidth={1.5} />  Checks <span className="text-[16px] font-[400] text-slate-700">(complete during the visit)</span>
        </h3>
        <ul className="mt-2 grid grid-cols-2 gap-x-8 gap-y-1.5 max-md:grid-cols-1">
          {checks.map((c) => (
            <li key={c.id}>
              <label className="flex cursor-pointer items-center gap-3 text-[16px]">
                <input type="checkbox" className="size-5 shrink-0 accent-[#0b46f5]" />
                {c.text}
              </label>
            </li>
          ))}
        </ul>
      </section>

      <div className="mt-4 grid grid-cols-2 gap-4 max-md:grid-cols-1">
        <section aria-labelledby="note" className="rounded-[10px] border-2 border-slate-300 px-5 pt-3 pb-5">
          <h3 id="note" className="flex items-center gap-2.5 text-[19px] font-[700]"><MessageSquare aria-hidden="true" size={22} strokeWidth={1.5} /> Note</h3>
          <div aria-hidden="true" className="mt-9 space-y-6">
            <div className="border-b border-slate-500" /><div className="border-b border-slate-500" /><div className="border-b border-slate-500" />
          </div>
        </section>
        <section aria-labelledby="semn" className="rounded-[10px] border-2 border-slate-300 px-5 pt-3 pb-4">
          <h3 id="semn" className="flex items-center gap-2.5 text-[19px] font-[700]"><PenLine aria-hidden="true" size={22} strokeWidth={1.5} />  Signature</h3>
          <div className="mt-14 grid grid-cols-2 gap-5 text-[14px] text-slate-700">
            <p className="border-t border-slate-500 pt-1">Name (capital letters)</p>
            <p className="border-t border-slate-500 pt-1">Signature</p>
          </div>
        </section>
      </div>
    </article>
  );
}
