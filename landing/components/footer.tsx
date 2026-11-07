import { REPO_URL } from "./site-header";

/**
 * Notele (sursele cifrelor publice și ce e sintetic), apoi subsolul cu mențiunea obligatorie:
 * proiect CyberPunks pentru SmartHack XI 2026, tema PPC, nu un produs oficial PPC.
 */
const NOTES: { id: number; text: React.ReactNode }[] = [
  {
    id: 1,
    text: (
      <>
        Rețele Electrice, development plan 2026–2035 (public consultation), tables 2.1–2.3: 3,180,331 customers on December 31, 2024 (Muntenia
        1,506,549; Banat 967,682; Dobrogea 706,100).{" "}
        <a className="underline decoration-ink-3/50 underline-offset-2 hover:text-ink" href="https://www.reteleelectrice.ro/wp-content/uploads/plan-dezvoltare-re-consultare.pdf">
          reteleelectrice.ro
        </a>
      </>
    ),
  },
  { id: 2, text: <>ANRE, prosumer statistics on August 31, 2026: 385,791 prosumers with 4,281.86 MW installed; Ilfov ranks first among counties (21,647).</> },
  { id: 3, text: <>Rețele Electrice, development plan 2024–2033: grid losses (own technological consumption) in Muntenia of 8.66% in 2023, down from 10.78% in 2018.</> },
  { id: 4, text: <>ANRE, report on distribution service quality in 2024: Rețele Electrice paid about 85% of the automatic compensation for outages paid nationally.</> },
  { id: 5, text: <>PPC, “24h to Power PPC”, the SmartHack XI 2026 theme document (November 7, 2026), translated from Romanian.</> },
  {
    id: 7,
    text: (
      <>
        Agent evaluation: 30 simulated days in a synthetic world where the true problems are known, against four simple strategies on the same
        crews (<code className="text-ink-2">reports/planner/agent_eval.json</code>, <code className="text-ink-2">uv run python -m cyberpunks.planner.evaluate --days 30 --seed 7 --meters 120</code>).
        Model figures come from <code className="text-ink-2">reports/&lt;model&gt;/metrics.json</code>, each on its own held-out test set.
      </>
    ),
  },
  {
    id: 6,
    text: (
      <>
        Demo day: the plan the agent produced for July 8, 2025, from the snapshot in the repository (<code className="text-ink-2">outputs/demo</code>).
        Meters, substations, crews and depots are synthetic, placed on the real map; the weather is real. County outlines: Natural Earth (public domain).
      </>
    ),
  },
];

export function Footer() {
  return (
    <footer className="border-t border-hairline px-5 pt-14 pb-16 sm:px-8">
      <div className="mx-auto max-w-[1180px]">
        <ol className="grid max-w-[60rem] gap-3 text-[0.8rem] leading-relaxed text-ink-3">
          {[...NOTES].sort((x, y) => x.id - y.id).map((n) => (
            <li key={n.id} id={`note-${n.id}`} className="scroll-mt-24">
              <span className="num mr-2">{n.id}.</span>
              {n.text}
            </li>
          ))}
        </ol>
        <div className="mt-12 flex flex-col gap-4 border-t border-hairline pt-6 text-[0.8rem] text-ink-3 sm:flex-row sm:items-center sm:justify-between">
          <p>A CyberPunks project for SmartHack XI 2026, PPC track. Not an official PPC product.</p>
          <a href={REPO_URL} className="hover:text-ink">
            github.com/teopaleface/CyberPunks
          </a>
        </div>
      </div>
    </footer>
  );
}
