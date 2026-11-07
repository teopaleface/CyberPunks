import { REPO_URL } from "./site-header";

/** Echipa: un final scurt, cu răsăritul complet în spate. */
export function Team() {
  return (
    <section id="team" aria-labelledby="team-title" className="relative isolate overflow-hidden px-5 pt-28 pb-36 text-center sm:px-8 sm:pt-40 sm:pb-48">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-[75%]"
        style={{
          background:
            "radial-gradient(60% 60% at 50% 100%, rgba(250,70,22,0.40) 0%, rgba(255,150,110,0.18) 25%, rgba(0,163,224,0.14) 50%, rgba(22,63,232,0.08) 65%, rgba(0,15,30,0) 85%)",
        }}
      />
      <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ink-2 sm:text-[1.35rem]">CyberPunks</p>
      <h2 id="team-title" className="reveal t-section mx-auto mt-3 max-w-[14ch] text-balance">
        Made in 24 hours.
      </h2>
      <p className="reveal t-intro mx-auto mt-6 max-w-[34rem] text-balance text-ink-3">
        Teo, Tudor and Eden, at SmartHack XI in Bucharest, November 7–8, 2026. Built for the dispatchers of Rețele Electrice.
      </p>
      <div className="reveal mt-10 flex flex-wrap items-center justify-center gap-x-7 gap-y-4">
        <a
          href={REPO_URL}
          className="inline-flex h-11 items-center rounded-full bg-ppc-energy px-6 text-[1.06rem] font-medium text-white transition-[background-color,transform] duration-150 ease-out hover:bg-ppc-energy-hover active:scale-[0.97]"
        >
          Read the code
        </a>
        <a href="#top" className="text-[1.06rem] text-ppc-blue hover:underline">
          Back to the top ›
        </a>
      </div>
    </section>
  );
}
