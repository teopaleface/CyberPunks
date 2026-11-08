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
          <b>work items received</b>
          <br />
          <span className="sec">{fmtInt(summary.items_valid)}  valid, {fmtInt(summary.items_invalid)}  quarantined</span>
        </>
      ),
    },
    {
      value: fmtInt(summary.assigned),
      label: (
        <>
          <b>Assigned</b>
          <br />
          <span className="sec">{fmtInt(summary.crews_used)}  of {fmtInt(crewsTotal)} echipe</span>
        </>
      ),
    },
    {
      value: fmtInt(summary.human_review),
      attention: summary.human_review > 0,
      label: (
        <>
          <b>Human review</b>
          <br />
          <span className="sec">dispatcher decides</span>
        </>
      ),
    },
    {
      value: fmtInt(summary.notifications + summary.remote_actions),
      label: (
        <>
          <b>no crew</b>
          <br />
          <span className="sec">{fmtInt(summary.notifications)}  messages, {fmtInt(summary.remote_actions)}  Remote</span>
        </>
      ),
    },
    {
      value: (
        <>
          {fmtInt(summary.expected_value_lei)}
          <small>RON</small>
        </>
      ),
      label: (
        <>
          <b>value</b>
          <br />
          <span className="sec">expected</span>
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
          <b>to travel</b>
          <br />
          <span className="sec">on routes</span>
        </>
      ),
    },
  ];
  return (
    <section aria-label="Daily figures" className="flex h-[88px] shrink-0 border-b border-rule bg-canvas [@media(max-height:950px)]:h-[76px]">
      <div className="flex shrink-0 flex-col justify-center border-r border-rule bg-panel pr-7 pl-7 max-[1600px]:pr-5 max-[1600px]:pl-5">
        <h1 className="text-[21px] leading-tight font-[650] tracking-[-0.005em] whitespace-nowrap max-[1600px]:text-[18px]">
          {fmtDateLong(planDate)}
        </h1>
        <p className="text-[14px] leading-snug whitespace-nowrap text-muted-foreground max-[1600px]:text-[13px]">
          {shift ? `shift ${shift.start}–${shift.end}` : "day shift"}
          <br />

          plan generated {fmtMoment(generatedAt)}
        </p>
      </div>
      <dl className="@container flex min-w-0 flex-1">
        {cells.map((c, i) => (
          <div key={i} className="flex min-w-0 flex-auto items-center gap-3 border-l border-rule px-5 first:border-l-0 @min-[1300px]:px-6 @max-[1240px]:flex-col @max-[1240px]:items-start @max-[1240px]:justify-center @max-[1240px]:gap-1 @max-[1240px]:px-4">
            <dt className="order-2 text-[14px] leading-[1.3] whitespace-nowrap text-muted-foreground [&_b]:font-[560] [&_b]:text-ink @max-[1240px]:text-[13px] @max-[1240px]:[&_br]:hidden @max-[1240px]:[&_b]:mr-1 @max-[1000px]:[&_.sec]:hidden">
              {c.label}
            </dt>
            <dd
              className={
                "num-wide order-1 text-[clamp(22px,2.4cqw,38px)] whitespace-nowrap @max-[1240px]:text-[clamp(20px,2.6cqw,30px)] [&_small]:ml-1.5 [&_small]:text-[0.46em] [&_small]:font-[520] [&_small]:tracking-normal [&_small]:text-muted-foreground " +
                (c.attention ? "text-att" : "")
              }
            >
              {c.value}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
