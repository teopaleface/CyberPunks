import type { PlanSummary } from "@/lib/contracts";
import { fmtInt, plural } from "@/lib/format";

/** Cele trei cifre principale; restul rezumatului rămâne în detaliile planului. */
export function KpiRow({ s }: { s: PlanSummary }) {
  const figures = [
    { value: fmtInt(s.assigned), label: "Work items on routes" },
    { value: fmtInt(s.human_review), label: "Cases awaiting your decision" },
    { value: fmtInt(Math.round(s.expected_value_lei)), unit: "RON", label: "Expected plan value" },
  ];
  return (
    <dl aria-label="Plan summary" className="grid gap-5 rounded-2xl border border-rule bg-panel p-6 sm:grid-cols-3 sm:gap-6">
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
    <dl aria-label="Other plan figures" className="grid gap-5 rounded-2xl border border-rule bg-panel p-6 sm:grid-cols-3">
      {[
        { value: plural(s.items_in, "work item received", "work items received"), label: "Data reviewed by the agent" },
        { value: plural(s.remote_actions, "remote check", "remote checks"), label: "No crew visit" },
        { value: `${fmtInt(Math.round(s.total_km))} km`, label: "Total route distance" },
      ].map((f) => (
        <div key={f.label} className="min-w-0">
          <dt className="text-[14px] text-ink-soft">{f.label}</dt>
          <dd className="mt-2 text-[18px] font-[550] tabular-nums">{f.value}</dd>
        </div>
      ))}
    </dl>
  );
}
