import type { PlanSummary } from "@/lib/contracts";
import { fmtInt, plural } from "@/lib/format";

/** Cele trei cifre principale; restul rezumatului rămâne în detaliile planului. */
export function KpiRow({ s }: { s: PlanSummary }) {
  const figures = [
    { value: fmtInt(s.assigned), label: "Lucrări propuse în trasee" },
    { value: fmtInt(s.human_review), label: "Cazuri care cer decizia ta" },
    { value: fmtInt(Math.round(s.expected_value_lei)), unit: "lei", label: "Valoarea așteptată a planului" },
  ];
  return (
    <dl aria-label="Rezumatul planului" className="grid gap-5 rounded-2xl border border-rule bg-panel p-6 sm:grid-cols-3 sm:gap-6">
      {figures.map((f) => (
        <div key={f.label} className="min-w-0">
          <dt className="text-[14px] leading-relaxed text-ink-soft">{f.label}</dt>
          <dd className="mt-2 text-[32px] leading-tight font-[650] tracking-[-0.03em] tabular-nums sm:text-[36px]">
            {f.value}
            {f.unit ? <span className="ml-2 text-[18px] font-[450] text-ink-soft">{f.unit}</span> : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function PlanFigures({ s }: { s: PlanSummary }) {
  return (
    <dl aria-label="Alte cifre ale planului" className="grid gap-5 rounded-2xl border border-rule bg-panel p-6 sm:grid-cols-3">
      {[
        { value: plural(s.items_in, "lucrare primită", "lucrări primite"), label: "Date analizate de agent" },
        { value: plural(s.remote_actions, "verificare la distanță", "verificări la distanță"), label: "Fără deplasarea unei echipe" },
        { value: `${fmtInt(Math.round(s.total_km))} km`, label: "Distanța totală a traseelor" },
      ].map((f) => (
        <div key={f.label} className="min-w-0">
          <dt className="text-[14px] text-ink-soft">{f.label}</dt>
          <dd className="mt-2 text-[18px] font-[550] tabular-nums">{f.value}</dd>
        </div>
      ))}
    </dl>
  );
}
