import type { Stories } from "@/lib/data";
import { formatDate, nf, pf } from "@/lib/format";
import { HoldToApprove } from "./hold-to-approve";

/**
 * Omul în buclă: un caz real din coada „Nu sunt sigur” a zilei demo, cu ce îi trebuie omului ca să
 * decidă. Textul e compus în engleză din câmpurile structurate ale lucrării (scor, fereastră, factori),
 * nu tradus din textul românesc al planificatorului.
 */
export function HumanLoop({ human, date }: { human: Stories["human"]; date: string | null }) {
  return (
    <section aria-labelledby="human-title" className="relative isolate overflow-hidden px-5 py-28 sm:px-8 sm:py-40">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-1/2 -z-10 h-[70%] -translate-y-1/2"
        style={{ background: "radial-gradient(45% 50% at 50% 55%, rgba(250,70,22,0.16) 0%, rgba(22,63,232,0.10) 45%, rgba(0,15,30,0) 75%)" }}
      />
      <div className="mx-auto max-w-[980px] text-center">
        <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ppc-orange-soft sm:text-[1.35rem]">Human in the loop</p>
        <h2 id="human-title" className="reveal t-section mt-3 text-balance">
          Not sure? It asks you.
        </h2>
        <p className="reveal t-intro mx-auto mt-6 max-w-[40rem] text-balance text-ink-3">
          Low confidence, missing data or a region with no crews left: the case goes to a person, with everything needed to decide.
        </p>
      </div>

      {human ? (
        <div className="reveal mx-auto mt-16 max-w-[560px] sm:mt-20">
          <article className="rounded-[28px] border border-hairline-strong bg-tile/80 p-7 shadow-[0_40px_120px_-40px_rgba(0,0,0,0.8)] backdrop-blur-xl sm:p-9">
            <p className="inline-flex items-center gap-2 rounded-full bg-ppc-orange/12 px-3 py-1 text-[0.85rem] font-medium text-ppc-orange-soft">
              <span aria-hidden className="size-2 rounded-full bg-ppc-orange" />
              Needs a person
            </p>
            <h3 className="mt-5 text-[clamp(1.5rem,2.4vw,1.9rem)] leading-tight font-semibold tracking-[-0.02em] text-ink">{human.title}</h3>
            <p className="mt-2 text-[0.98rem] text-ink-3">
              {human.place}
              {human.window ? `, storm expected ${human.window}` : ""}
            </p>
            <p className="mt-6 text-[1.05rem] leading-relaxed text-ink-2">
              The storm model gives a {pf(human.score)} chance of outages, but its confidence is low.
              {human.customers ? ` If it hits, about ${nf(human.customers)} customers lose power (median estimate).` : ""}
            </p>
            {human.factors.length > 0 && (
              <ul className="mt-5 grid gap-2 text-[0.95rem] text-ink-3">
                {human.factors.map((f) => (
                  <li key={f} className="flex gap-2.5">
                    <span aria-hidden className="mt-[0.6em] size-1 shrink-0 rounded-full bg-ink-3" />
                    {f}
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-6 border-t border-hairline pt-5 text-[0.92rem] text-ink-3">
              Expected value <span className="num text-ink">{nf(human.value)} lei</span>, model {human.model}
            </p>
            <div className="mt-6">
              <HoldToApprove />
            </div>
          </article>
          <p className="mt-6 text-center text-[0.9rem] leading-relaxed text-ink-3">
            {date ? `On ${formatDate(date)}` : "On the demo day"}, {nf(human.queue.total)} cases went to a person: {nf(human.queue.abstain)} where a model
            abstained, {nf(human.queue.cap)} over a region’s crew cap, {nf(human.queue.low)} with low confidence. Nothing is sent from this page.
          </p>
        </div>
      ) : (
        <p className="mt-16 text-center text-ink-3">The review queue for the demo day isn’t generated yet.</p>
      )}
    </section>
  );
}
