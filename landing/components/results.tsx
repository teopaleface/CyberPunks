import type { AgentEval, ModelResult } from "@/lib/data";
import { nf, pf } from "@/lib/format";

/**
 * Rezultatul agentului, ca o cifră de keynote, apoi comparația cu strategiile simple și comenzile
 * care refac fiecare cifră. Totul din reports/planner/agent_eval.json și reports/<sursă>/metrics.json.
 */
export function Results({ agent, models }: { agent: AgentEval | null; models: Partial<Record<ModelResult["key"], ModelResult>> }) {
  const max = agent ? Math.max(...agent.strategies.map((s) => s.perDay)) : 1;
  const a = agent?.strategies.find((s) => s.key === "agent");
  const best = agent?.strategies.find((s) => s.label === agent.bestSimple);
  const commands = [
    { what: "Meters", cmd: models.A?.reproduce },
    { what: "Substation balance", cmd: models.bilant?.reproduce },
    { what: "Storms", cmd: models.B?.reproduce },
    { what: "Voltage", cmd: models.C?.reproduce },
    { what: "The agent", cmd: agent?.reproduce },
  ].filter((c): c is { what: string; cmd: string } => !!c.cmd);

  return (
    <section id="results" aria-labelledby="results-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[1180px] text-center">
        <h2 id="results-title" className="sr-only">
          Results
        </h2>
        {agent && a && best ? (
          <>
            <p className="reveal sunrise-text t-big-number num pb-3">+{Math.round(agent.uplift * 100)}%</p>
            <p className="reveal t-section mx-auto mt-2 max-w-[16ch] text-balance">more value. Same crews.</p>
            <p className="reveal t-intro mx-auto mt-6 max-w-[42rem] text-balance text-ink-3">
              Net value per day against the best simple strategy, {best.label.toLowerCase()}, over a {nf(agent.days)}-day simulation where the
              truth is known.
              <a href="#note-7" className="ml-0.5 align-super text-[0.6em] hover:text-ink" aria-label="Source 7">
                7
              </a>
            </p>

            <figure className="reveal mx-auto mt-16 max-w-[880px] rounded-[28px] border border-hairline bg-tile p-7 text-left sm:mt-20 sm:p-10">
              <figcaption className="text-[1rem] font-semibold text-ink-2">Net value per day, in lei</figcaption>
              <ul className="mt-6 grid gap-4">
                {agent.strategies.map((s) => (
                  <li key={s.key} className="grid grid-cols-[minmax(0,11rem)_minmax(0,1fr)_auto] items-center gap-4 text-[0.95rem]">
                    <span className={s.key === "agent" ? "font-semibold text-ink" : "text-ink-3"}>{s.label}</span>
                    <span className="h-2.5 rounded-full bg-night-2">
                      <span
                        className="block h-full rounded-full"
                        style={{
                          width: `${Math.max(2, (s.perDay / max) * 100)}%`,
                          background: s.key === "agent" ? "linear-gradient(90deg, #00a3e0, #ffb08f, #fa4616)" : "#3a5370",
                        }}
                      />
                    </span>
                    <span className={`num w-[4.5rem] text-right ${s.key === "agent" ? "text-ink" : "text-ink-3"}`}>{nf(s.perDay)}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-8 border-t border-hairline pt-5 text-[0.92rem] leading-relaxed text-ink-3">
                Also {nf(a.kmPerDay)} km a day instead of {nf(best.kmPerDay)}, and {pf(a.urgentMissed)} of urgent cases missed instead of{" "}
                {pf(best.urgentMissed)}. Synthetic world, scores calibrated by construction.
              </p>
            </figure>
          </>
        ) : (
          <p className="text-ink-3">The agent evaluation is in progress.</p>
        )}

        <div className="mx-auto mt-28 max-w-[880px] text-left sm:mt-36">
          <h3 className="reveal t-title text-center text-balance">Every number here comes from a script.</h3>
          <p className="reveal mx-auto mt-4 max-w-[36rem] text-center text-[1.08rem] leading-relaxed text-ink-3">
            Clone the repository and run the evaluation yourself. Each model is scored on data it never saw, next to the simple method it has to
            beat.
          </p>
          <div className="reveal mt-10 overflow-x-auto rounded-[22px] border border-hairline bg-night-2 p-6 font-mono text-[0.84rem] leading-[1.9] text-ink-2">
            <p className="text-ink-3"># setup, lint and the tests</p>
            <p>uv sync &amp;&amp; make check</p>
            {commands.map((c) => (
              <div key={c.what}>
                <p className="mt-3 text-ink-3"># {c.what}</p>
                <p className="whitespace-pre">{c.cmd}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
