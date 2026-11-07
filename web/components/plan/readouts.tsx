import type { PlanSummary } from "@/lib/contracts";
import { fmtDateLong, fmtDec, fmtInt, fmtMoment } from "@/lib/format";

/**
 * Rândul de sub antet: ziua planului și cifrele zilei, ca afișajele unui panou de dispecerat
 * (cifre late, despărțite doar de linii subțiri; „la om” e portocaliu pentru că așteaptă o decizie).
 */
export function Readouts({
  summary,
  planDate,
  shift,
  generatedAt,
  crewsTotal,
}: {
  summary: PlanSummary;
  planDate: string;
  shift: { start: string; end: string } | null;
  generatedAt: string;
  crewsTotal: number;
}) {
  const cells: { value: React.ReactNode; label: React.ReactNode; attention?: boolean }[] = [
    {
      value: fmtInt(summary.items_in),
      label: (
        <>
          <b>lucrări intrate</b>
          <br />
          {fmtInt(summary.items_valid)} valide, {fmtInt(summary.items_invalid)} în carantină
        </>
      ),
    },
    {
      value: fmtInt(summary.assigned),
      label: (
        <>
          <b>în trasee</b>
          <br />
          {fmtInt(summary.crews_used)} din {fmtInt(crewsTotal)} echipe
        </>
      ),
    },
    {
      value: fmtInt(summary.human_review),
      attention: summary.human_review > 0,
      label: (
        <>
          <b>la om</b>
          <br />
          decide dispecerul
        </>
      ),
    },
    {
      value: fmtInt(summary.notifications + summary.remote_actions),
      label: (
        <>
          <b>fără echipă</b>
          <br />
          {fmtInt(summary.notifications)} mesaje, {fmtInt(summary.remote_actions)} la distanță
        </>
      ),
    },
    {
      value: (
        <>
          {fmtInt(summary.expected_value_lei)}
          <small>lei</small>
        </>
      ),
      label: (
        <>
          <b>valoare</b>
          <br />
          așteptată
        </>
      ),
    },
    {
      value: (
        <>
          {fmtDec(summary.total_km, 1)}
          <small>km</small>
        </>
      ),
      label: (
        <>
          <b>de parcurs</b>
          <br />
          pe trasee
        </>
      ),
    },
  ];
  return (
    <section aria-label="Cifrele zilei" className="flex h-[88px] shrink-0 border-b border-rule bg-canvas">
      <div className="flex shrink-0 flex-col justify-center border-r border-rule bg-panel pr-7 pl-7">
        <h1 className="text-[21px] leading-tight font-[650] tracking-[-0.005em] whitespace-nowrap">
          {fmtDateLong(planDate)}
        </h1>
        <p className="text-[14px] leading-snug whitespace-nowrap text-muted-foreground">
          {shift ? `tura ${shift.start}–${shift.end}` : "tura de zi"}
          <br />
          plan generat {fmtMoment(generatedAt)}
        </p>
      </div>
      <dl className="flex min-w-0 flex-1">
        {cells.map((c, i) => (
          <div key={i} className="flex min-w-0 flex-auto items-center gap-3 border-l border-rule px-5 first:border-l-0 min-[1700px]:px-6">
            <dd
              className={
                "num-wide order-1 text-[clamp(28px,2.1vw,40px)] whitespace-nowrap [&_small]:ml-1.5 [&_small]:text-[0.46em] [&_small]:font-[520] [&_small]:tracking-normal [&_small]:text-muted-foreground " +
                (c.attention ? "text-att" : "")
              }
            >
              {c.value}
            </dd>
            <dt className="order-2 text-[14px] leading-[1.3] whitespace-nowrap text-muted-foreground [&_b]:font-[560] [&_b]:text-ink">
              {c.label}
            </dt>
          </div>
        ))}
      </dl>
    </section>
  );
}
