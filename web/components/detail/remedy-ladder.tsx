import type { Decision, RecommendedAction } from "@/lib/contracts";
import { ACTION_RO, CONFIDENCE_RO } from "@/lib/data/labels";
import type { RemedyOption } from "@/lib/extras";
import { fmtDec, fmtDuration, fmtInt, fmtLei, fmtPercent } from "@/lib/format";

/**
 * Scara de soluții pentru tensiune (C): treptele de la ieftin la scump, cu P90 după fiecare.
 * Agentul alege cea mai ieftină treaptă (sau combinație) care aduce P90 sub limită și spune de ce
 * una mai ieftină nu ajunge.
 */
export function RemedyLadder({
  options,
  decision,
  recommended,
  limit = 1.1,
  p90Before,
}: {
  options: RemedyOption[];
  decision: Decision | null;
  recommended: RecommendedAction;
  limit?: number;
  p90Before: number | null;
}) {
  const sorted = options.toSorted((a, b) => a.cost_lei - b.cost_lei);
  // treapta aleasă: cea din decizie (R-REMEDY-LADDER, `threshold.chosen_cost_lei` dacă există), altfel acțiunea recomandată
  const chosenCost = typeof decision?.threshold?.chosen_cost_lei === "number" ? decision.threshold.chosen_cost_lei : null;
  const chosen =
    (chosenCost != null ? sorted.find((o) => Math.abs(o.cost_lei - chosenCost) < 0.5) : undefined) ??
    sorted.find((o) => o.action === recommended) ??
    sorted.find((o) => o.p90_after_pu < limit) ??
    null;
  const cheaperFailing = chosen ? sorted.filter((o) => o.cost_lei < chosen.cost_lei) : [];
  const allVals = [limit, ...(p90Before != null ? [p90Before] : []), ...sorted.map((o) => o.p90_after_pu)];
  const vMin = Math.min(...allVals) - 0.01;
  const vMax = Math.max(...allVals) + 0.01;
  const X = (v: number) => `${(((v - vMin) / (vMax - vMin)) * 100).toFixed(2)}%`;

  return (
    <div>
      <ol className="divide-y divide-rule border-y border-rule">
        {sorted.map((o, i) => {
          const isChosen = chosen === o;
          const ok = o.p90_after_pu < limit;
          return (
            <li
              key={`${o.action}-${i}`}
              className={
                "grid grid-cols-[28px_minmax(0,1.3fr)_minmax(0,1fr)_110px] items-center gap-x-4 py-3 " +
                (isChosen ? "bg-[color-mix(in_oklab,var(--src-c)_12%,var(--panel))]" : "")
              }
            >
              <span
                className={
                  "grid size-7 place-items-center rounded-full border text-[13.5px] font-[650] " +
                  (isChosen ? "border-ink bg-ink text-panel" : "border-input")
                }
                aria-hidden="true"
              >
                {i + 1}
              </span>
              <div className="min-w-0">
                <div className="flex flex-wrap items-baseline gap-x-2">
                  <span className="text-[16px] font-[620]">{ACTION_RO[o.action] ?? o.action}</span>
                  {isChosen ? <span className="text-[13.5px] font-[600] text-src-c-ink">aleasă de agent</span> : null}
                </div>
                <p className="text-[14px] text-muted-foreground">{o.note_ro}</p>
                <p className="text-[13.5px] text-muted-foreground">
                  {o.needs_crew ? `cere echipă, ${fmtDuration(o.duration_min)}` : "fără echipă"}, {CONFIDENCE_RO[o.confidence]}
                  {o.participation_rate != null ? `, participare ${fmtPercent(o.participation_rate)} (ipoteză)` : ""}
                  {o.inverter_trips_avoided != null ? `, ${fmtInt(o.inverter_trips_avoided)} opriri de invertoare evitate` : ""}
                </p>
                {o.message_preview_ro ? (
                  <blockquote className="mt-1.5 border-l-2 border-rule pl-3 text-[14px]">
                    „{o.message_preview_ro}”
                    <span className="block text-[12.5px] text-muted-foreground">mesaj de grup pe post, fără date personale, demo: nu se trimite</span>
                  </blockquote>
                ) : null}
                {o.customers_targeted != null || o.battery_kwh_total != null ? (
                  <p className="mt-1 text-[13.5px]">
                    {o.customers_targeted != null ? `${fmtInt(o.customers_targeted)} clienți vizați` : ""}
                    {o.battery_kwh_total != null ? `, ${fmtDec(o.battery_kwh_total, 0)} kWh de baterii` : ""}
                    {o.revenue_lei != null ? `, venit estimat ${fmtLei(o.revenue_lei)}` : ""}
                    {o.payback_years != null ? `, recuperare în ${fmtDec(o.payback_years, 1)} ani` : ""}
                  </p>
                ) : null}
              </div>
              {/* P90 după soluție față de limită */}
              <div className="relative h-8" aria-label={`P90 după: ${fmtDec(o.p90_after_pu, 3)} pu`}>
                <span className="absolute top-1/2 h-px w-full bg-rule" />
                <span className="absolute top-0 bottom-0 w-[2px] bg-att" style={{ left: X(limit) }} title="limita 1,10 pu" />
                {p90Before != null ? (
                  <span className="absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full border border-ink bg-panel" style={{ left: X(p90Before) }} title="P90 fără soluție" />
                ) : null}
                <span
                  className={"absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full " + (ok ? "bg-ink" : "bg-att")}
                  style={{ left: X(o.p90_after_pu) }}
                />
                <span className="absolute -bottom-1 text-[12px] whitespace-nowrap text-muted-foreground tabular-nums" style={{ left: X(o.p90_after_pu), transform: "translateX(-50%)" }}>
                  {fmtDec(o.p90_after_pu, 3)}
                </span>
              </div>
              <div className="text-right">
                <div className="text-[16px] font-[620] tabular-nums">{o.cost_lei === 0 ? "0 lei" : fmtLei(o.cost_lei)}</div>
                <div className={"text-[13px] " + (ok ? "text-muted-foreground" : "text-att-ink")}>{ok ? "sub limită" : "nu ajunge"}</div>
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-3 text-[15px]">
        {chosen ? (
          <>
            Agentul alege <b className="font-[620]">{ACTION_RO[chosen.action] ?? chosen.action}</b> ({fmtLei(chosen.cost_lei)}), cea mai ieftină treaptă care
            aduce P90 sub {fmtDec(limit, 2)} pu.
            {cheaperFailing.length
              ? ` Treptele mai ieftine (${cheaperFailing.map((o) => ACTION_RO[o.action] ?? o.action).join(", ")}) lasă P90 peste limită.`
              : ""}
          </>
        ) : (
          "Nicio treaptă nu aduce P90 sub limită singură; decizia merge la un om."
        )}
      </p>
      <p className="mt-1 text-[13.5px] text-muted-foreground">
        Efectul fiecărei trepte e calculat cu modelul de rețea al firului C, nu ghicit. Punctul gol arată P90 fără nicio soluție.
      </p>
    </div>
  );
}
