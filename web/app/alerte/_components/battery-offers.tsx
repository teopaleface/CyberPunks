import Link from "next/link";
import type { RemedyChoice } from "@/lib/data/remedies";
import { fmtDec, fmtInt, fmtLei } from "@/lib/format";
import { DemoStamp } from "./parts";

/**
 * Ofertele de baterii pentru PPC Energie, din scara de soluții a agentului (treapta 4): doar posturile
 * unde bateria ajută tensiunea. Ordonate după efect (P90 după soluție), apoi după venit.
 */
export function BatteryOffers({ remedies, scenario }: { remedies: RemedyChoice[]; scenario: string }) {
  const rows = remedies
    .filter((r) => r.battery && (r.battery.customers_targeted ?? 0) > 0)
    .toSorted((a, b) => a.p90_after_pu - b.p90_after_pu || (b.battery?.revenue_lei ?? 0) - (a.battery?.revenue_lei ?? 0));
  if (!rows.length) return null;
  const totals = rows.reduce(
    (t, r) => ({
      customers: t.customers + (r.battery?.customers_targeted ?? 0),
      kwh: t.kwh + (r.battery?.battery_kwh_total ?? 0),
      revenue: t.revenue + (r.battery?.revenue_lei ?? 0),
    }),
    { customers: 0, kwh: 0, revenue: 0 },
  );
  return (
    <section aria-labelledby="battery-title" className="border-t border-rule">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-2 px-7 pt-5 pb-3">
        <div>
          <h2 id="battery-title" className="text-[20px] font-[650]">
            Oferte de baterii pentru PPC Energie <span className="text-[16px] font-[500] text-muted-foreground">{rows.length}</span>
          </h2>
          <p className="mt-1 max-w-[86ch] text-[15px] text-muted-foreground">
            Posturile unde o baterie la prosumatori coboară tensiunea de la prânz. Lista merge la PPC Energie (magazinele PPC și
            Flanco); în total {fmtInt(totals.customers)} clienți, {fmtInt(totals.kwh)} kWh de baterii, venit estimat {fmtLei(totals.revenue)}.
          </p>
        </div>
        <DemoStamp />
      </div>
      <div className="overflow-x-auto px-7 pb-6">
        <table className="w-full min-w-[880px] border-collapse text-[15px]">
          <thead>
            <tr className="border-y border-rule text-left text-[13.5px] text-muted-foreground">
              <th className="py-2 pr-4 font-[500]">Postul</th>
              <th className="py-2 pr-4 text-right font-[500]">Clienți vizați</th>
              <th className="py-2 pr-4 text-right font-[500]">Baterii</th>
              <th className="py-2 pr-4 text-right font-[500]">Tensiunea P90</th>
              <th className="py-2 pr-4 text-right font-[500]">Venit estimat</th>
              <th className="py-2 pr-4 text-right font-[500]">Recuperare pentru client</th>
              <th className="py-2 font-[500]">Combinația aleasă</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.work_item_id} className="border-b border-rule align-top">
                <td className="py-2.5 pr-4">
                  <Link href={`/posturi/${encodeURIComponent(r.post_id)}?scenariu=${encodeURIComponent(scenario)}`} className="code-id underline decoration-rule underline-offset-4 hover:decoration-ink" translate="no">
                    {r.post_id}
                  </Link>
                  <span className="block text-[13.5px] text-muted-foreground">{(r.label ?? "").replace(/^PT-\d+,\s*/, "").replace(/\s*\(sintetic\)$/, "")}</span>
                </td>
                <td className="py-2.5 pr-4 text-right tabular-nums">{fmtInt(r.battery?.customers_targeted ?? 0)}</td>
                <td className="py-2.5 pr-4 text-right tabular-nums">{fmtInt(r.battery?.battery_kwh_total ?? 0)} kWh</td>
                <td className="py-2.5 pr-4 text-right tabular-nums">
                  {fmtDec(r.p90_before_pu, 3)} → <b className="font-[620]">{fmtDec(r.p90_after_pu, 3)}</b>
                </td>
                <td className="py-2.5 pr-4 text-right tabular-nums">{fmtLei(r.battery?.revenue_lei ?? 0)}</td>
                <td className="py-2.5 pr-4 text-right tabular-nums">{r.battery?.payback_years != null ? `${fmtDec(r.battery.payback_years, 1)} ani` : "–"}</td>
                <td className="py-2.5 text-[14px] text-muted-foreground">{r.chosen.length} trepte, {fmtLei(r.cost_lei)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-2 text-[13.5px] text-muted-foreground">
          Efectul pe tensiune e cel al combinației alese de agent, calculat cu modelul de rețea al firului C; rata de acceptare a ofertei e o ipoteză din config.
        </p>
      </div>
    </section>
  );
}
