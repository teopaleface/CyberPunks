import type { Stories } from "@/lib/data";
import { nf } from "@/lib/format";

/**
 * Scara de soluții pentru tensiune (sursa C): cel mai ieftin pas întâi, efectul fiecăruia calculat
 * fizic. Exemplul e postul real din planul demo cu tensiunea cea mai mare rezolvată fără investiție
 * (outputs/demo/plans/demo-vara/remedies.json). Tensiunea în volți = pu × 230 V; limita 1,10 pu = 253 V.
 */
const V = (pu: number) => Math.round(pu * 230);

export function Ladder({ ladder }: { ladder: Stories["ladder"] }) {
  return (
    <section aria-labelledby="ladder-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[1180px]">
        <div className="mx-auto max-w-[980px] text-center">
          <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-src-c-ink sm:text-[1.35rem]">When the sun is too much</p>
          <h2 id="ladder-title" className="reveal t-section mt-3 text-balance">
            Cheapest fix first.
          </h2>
          <p className="reveal t-intro mx-auto mt-6 max-w-[42rem] text-balance text-ink-3">
            When rooftop solar pushes a substation past 253 V, Daybreak tries the cheap fixes first and checks each one against the physics of
            the grid before it spends real money.
          </p>
        </div>

        {ladder ? (
          <div className="reveal mx-auto mt-16 grid max-w-[1080px] gap-5 sm:mt-24 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
            <div className="flex flex-col justify-between rounded-[28px] border border-hairline bg-tile p-7 sm:p-10">
              <div>
                <p className="text-[1rem] font-semibold text-ink-2">{ladder.label}, demo day</p>
                <p className="mt-1 text-[0.9rem] text-ink-3">Highest voltage of the day, 90th percentile</p>
              </div>
              <div className="mt-10 flex items-end gap-6">
                <div>
                  <p className="text-[0.85rem] text-ink-3">Before</p>
                  <p className="num text-[clamp(2.8rem,5vw,4rem)] leading-none font-semibold tracking-[-0.04em] text-ink-3 line-through decoration-2">
                    {V(ladder.before)} V
                  </p>
                </div>
                <div>
                  <p className="text-[0.85rem] text-src-c-ink">After</p>
                  <p className="num text-[clamp(2.8rem,5vw,4rem)] leading-none font-semibold tracking-[-0.04em] text-ink">{V(ladder.after)} V</p>
                </div>
              </div>
              <Gauge before={ladder.before} after={ladder.after} />
              <p className="mt-8 text-[0.95rem] leading-relaxed text-ink-3">
                <span className="text-ink">Chosen: the cheapest mix that gets under the limit, {nf(ladder.cost)} lei.</span>
                {ladder.battery && (
                  <>
                    {" "}
                    The battery offer reaches {nf(ladder.battery.customers)} prosumers and could earn PPC Energie {nf(ladder.battery.revenue)} lei; the
                    batteries charge at noon and give the energy back in the 18:00–22:00 evening peak.
                  </>
                )}
              </p>
            </div>

            <ol className="rounded-[28px] border border-hairline bg-tile p-3 sm:p-4">
              {ladder.steps.map((s, i) => (
                <li
                  key={s.action}
                  className={`flex items-center gap-4 rounded-[20px] px-4 py-4 sm:px-5 ${s.chosen ? "bg-tile-2" : ""}`}
                >
                  <span className="num w-5 shrink-0 text-[0.95rem] text-ink-3">{i + 1}</span>
                  <span className="min-w-0 flex-1">
                    <span className={`block text-[1.02rem] leading-snug ${s.chosen ? "text-ink" : "text-ink-2"}`}>{s.label}</span>
                    <span className="mt-0.5 block text-[0.86rem] text-ink-3">
                      {nf(s.cost)} lei{s.needsCrew ? ", needs a crew" : ""}. Alone: {V(s.aloneAfter)} V{V(s.aloneAfter) > 253 ? ", not enough" : ""}.
                    </span>
                  </span>
                  {s.chosen ? (
                    <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-src-c/15 px-3 py-1 text-[0.82rem] font-medium text-src-c-ink">
                      <Check />
                      Chosen
                    </span>
                  ) : (
                    <span className="shrink-0 text-[0.82rem] text-ink-3">Skipped</span>
                  )}
                </li>
              ))}
            </ol>
          </div>
        ) : (
          <p className="mt-16 text-center text-ink-3">The remedy ladder for the demo day isn’t generated yet.</p>
        )}
      </div>
    </section>
  );
}

/** Bara de tensiune: 230 V la stânga, limita de 253 V marcată, înainte (gri) și după (chihlimbar). */
function Gauge({ before, after }: { before: number; after: number }) {
  const lo = 1.0;
  const hi = Math.max(1.2, before + 0.01);
  const x = (pu: number) => `${((pu - lo) / (hi - lo)) * 100}%`;
  return (
    <div className="mt-10" aria-hidden>
      <div className="relative h-2 rounded-full bg-night-2">
        <div className="absolute inset-y-0 left-0 rounded-full bg-ink-3/40" style={{ width: x(before) }} />
        <div className="absolute inset-y-0 left-0 rounded-full bg-src-c" style={{ width: x(after) }} />
        <div className="absolute -top-2 -bottom-2 w-[2px] rounded bg-ppc-orange" style={{ left: x(1.1) }} />
      </div>
      <div className="relative mt-3 h-4 text-[0.78rem] text-ink-3">
        <span className="absolute left-0">230 V</span>
        <span className="absolute -translate-x-1/2 text-ppc-orange-soft" style={{ left: x(1.1) }}>
          limit 253 V
        </span>
      </div>
    </div>
  );
}

function Check() {
  return (
    <svg aria-hidden viewBox="0 0 12 12" className="size-3" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M2.5 6.4 5 8.8l4.5-5.6" />
    </svg>
  );
}
