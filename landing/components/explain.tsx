import type { Stories } from "@/lib/data";
import { df, nf, pf } from "@/lib/format";

/**
 * Explicabilitatea: o oprire reală din traseele zilei demo, urmărită de la predicție (modelul, versiunea,
 * intervalul) la factorii care au contat, cazurile asemănătoare, regula cu pragul ei, acțiune și jurnal.
 */
const LABELS: Record<string, string> = { faulty: "Faulty meter", tamper: "Tampered meter", normal: "Normal meter" };
const OUTCOMES: Record<string, string> = {
  goluri_comunicatie: "communication gaps",
  manipulare_confirmata: "confirmed tampering",
  citiri_negative: "negative readings",
};

export function Explain({ explain }: { explain: Stories["explain"] }) {
  return (
    <section aria-labelledby="explain-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[980px] text-center">
        <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ppc-blue sm:text-[1.35rem]">Explainability</p>
        <h2 id="explain-title" className="reveal t-section mt-3 text-balance">
          Every decision has a reason.
        </h2>
        <p className="reveal t-intro mx-auto mt-6 max-w-[42rem] text-balance text-ink-3">
          Each stop on a route traces back to the prediction, the model version and the rule that put it there.
        </p>
      </div>

      {explain ? (
        <div className="reveal mx-auto mt-16 max-w-[880px] rounded-[28px] border border-hairline bg-tile p-7 sm:mt-24 sm:p-10">
          <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-hairline pb-6">
            <h3 className="text-[1.35rem] font-semibold tracking-[-0.015em] text-ink">{explain.meter}</h3>
            <p className="text-[0.95rem] text-ink-3">{explain.place}, synthetic</p>
          </div>
          <ol className="divide-y divide-hairline">
            <Row label="Prediction">
              <span className="text-ink">
                {LABELS[explain.label] ?? explain.label}, {pf(explain.score)}
              </span>
              {explain.low !== null && explain.high !== null && (
                <span className="text-ink-3">
                  {" "}
                  (interval {pf(explain.low)}–{pf(explain.high)})
                </span>
              )}
              <span className="mt-1 block text-[0.88rem] text-ink-3">Model {explain.model}</span>
            </Row>
            <Row label="Why">
              <ul className="grid gap-3">
                {explain.factors.map((f) => {
                  const max = explain.factors[0]?.contribution || 1;
                  return (
                    <li key={f.label}>
                      <span className="block text-[0.98rem] text-ink-2">{f.label}</span>
                      <span className="mt-1.5 block h-1.5 rounded-full bg-night-2">
                        <span className="block h-full rounded-full bg-src-a" style={{ width: `${Math.max(4, (f.contribution / max) * 100)}%` }} />
                      </span>
                    </li>
                  );
                })}
              </ul>
              <span className="mt-3 block text-[0.84rem] text-ink-3">Bar length: each factor’s share of the score (SHAP).</span>
            </Row>
            {explain.similar && (
              <Row label="Like">
                <span className="text-ink-2">
                  The closest past cases were {OUTCOMES[explain.similar.outcome] ?? explain.similar.outcome.replaceAll("_", " ")}.
                </span>
              </Row>
            )}
            <Row label="Rule">
              <span className="text-ink-2">
                A visit pays off when the expected value beats its cost:{" "}
                <span className="num text-ink">
                  {nf(explain.value)} lei vs {nf(explain.cost)} lei
                </span>
                {explain.actionCost !== null && explain.travelCost !== null && explain.km !== null && (
                  <span className="text-ink-3">
                    {" "}
                    ({nf(explain.actionCost)} lei for the check, {nf(explain.travelCost)} lei for {df(explain.km, 1)} km)
                  </span>
                )}
                .
              </span>
              <span className="mt-1 block text-[0.88rem] text-ink-3">Rule {explain.rule}</span>
            </Row>
            {explain.crew && (
              <Row label="Action">
                <span className="text-ink">
                  Crew {explain.crew}
                  {explain.stop !== null ? `, stop ${explain.stop}` : ""}
                  {explain.eta ? `, arrives ${explain.eta}` : ""}.
                </span>
              </Row>
            )}
            <Row label="Logged">
              <span className="font-mono text-[0.86rem] break-all text-ink-3">audit {explain.auditId}</span>
            </Row>
          </ol>
        </div>
      ) : (
        <p className="mt-16 text-center text-ink-3">The decision log for the demo day isn’t generated yet.</p>
      )}
    </section>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <li className="grid gap-2 py-5 sm:grid-cols-[8rem_minmax(0,1fr)] sm:gap-6">
      <span className="text-[0.95rem] font-medium text-ink-3">{label}</span>
      <div className="text-[1.02rem] leading-relaxed">{children}</div>
    </li>
  );
}
