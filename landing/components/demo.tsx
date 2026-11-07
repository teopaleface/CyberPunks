import { REPO_URL } from "./site-header";

/**
 * Demo: consola dispecerului (web/, portul 3710) și modul de prezentare (/demo), plus locul filmului
 * de 30 de secunde al firului de prezentare. Filmul se leagă când există; nu intră în repo.
 */
const CONSOLE_URL = "http://localhost:3710";

export function Demo() {
  return (
    <section id="demo" aria-labelledby="demo-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[1180px]">
        <div className="mx-auto max-w-[980px] text-center">
          <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ppc-blue sm:text-[1.35rem]">Demo</p>
          <h2 id="demo-title" className="reveal t-section mt-3 text-balance">
            See it run.
          </h2>
          <p className="reveal t-intro mx-auto mt-6 max-w-[40rem] text-balance text-ink-3">
            The dispatcher console runs on your machine, with the real plan for the demo day and every decision explained.
          </p>
        </div>

        <div className="reveal mx-auto mt-16 max-w-[980px] sm:mt-20">
          <div className="relative grid aspect-video place-items-center overflow-hidden rounded-[28px] border border-hairline bg-[radial-gradient(80%_70%_at_50%_100%,rgba(250,70,22,0.22)_0%,rgba(22,63,232,0.16)_40%,rgba(4,23,42,1)_75%)]">
            <div className="text-center">
              <span aria-hidden className="mx-auto grid size-16 place-items-center rounded-full border border-hairline-strong bg-night/50 backdrop-blur">
                <svg viewBox="0 0 16 16" className="ml-0.5 size-5 text-ink-2" fill="currentColor">
                  <path d="M4 2.8v10.4c0 .6.6.9 1.1.6l8.2-5.2a.7.7 0 0 0 0-1.2L5.1 2.2C4.6 1.9 4 2.2 4 2.8Z" />
                </svg>
              </span>
              <p className="mt-5 text-[1.1rem] font-semibold text-ink">The 30-second film</p>
              <p className="mt-1 text-[0.95rem] text-ink-3">Coming with the final presentation</p>
            </div>
          </div>
        </div>

        <ul className="mx-auto mt-5 grid max-w-[980px] gap-5 md:grid-cols-2">
          <li className="reveal">
            <a href={CONSOLE_URL} className="group block h-full rounded-[28px] border border-hairline bg-tile p-7 transition-colors duration-200 hover:bg-tile-2 sm:p-9">
              <p className="t-title text-ink">Dispatcher console</p>
              <p className="mt-3 text-[1.02rem] leading-relaxed text-ink-3">
                Tomorrow’s plan on the map, the crews’ day, the “not sure” queue and the reason behind every decision.
              </p>
              <p className="mt-6 font-mono text-[0.84rem] text-ink-2">make api &amp;&amp; make web-demo</p>
              <p className="mt-4 inline-flex items-center gap-1 text-[1rem] text-ppc-blue group-hover:underline">Open localhost:3710 ›</p>
            </a>
          </li>
          <li className="reveal">
            <a href={`${CONSOLE_URL}/demo`} className="group block h-full rounded-[28px] border border-hairline bg-tile p-7 transition-colors duration-200 hover:bg-tile-2 sm:p-9">
              <p className="t-title text-ink">Presentation mode</p>
              <p className="mt-3 text-[1.02rem] leading-relaxed text-ink-3">
                Five scenes on a night map: the plan, the cases for a person, why the agent decided, the crew before the storm, the crews’ day.
              </p>
              <p className="mt-6 font-mono text-[0.84rem] text-ink-2">← → or 1–5 to change scenes</p>
              <p className="mt-4 inline-flex items-center gap-1 text-[1rem] text-ppc-blue group-hover:underline">Open localhost:3710/demo ›</p>
            </a>
          </li>
        </ul>
        <p className="mt-8 text-center text-[0.92rem] text-ink-3">
          Setup and every step, timed from a clean clone:{" "}
          <a href={`${REPO_URL}/blob/main/docs/REPRODUCERE.md`} className="text-ppc-blue hover:underline">
            docs/REPRODUCERE.md
          </a>
        </p>
      </div>
    </section>
  );
}
