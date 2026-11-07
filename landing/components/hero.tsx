import type { CSSProperties } from "react";
import type { HeroMapData } from "@/lib/data";
import { HERO_STEPS, HeroMap } from "./hero-map";
import { formatDateRo, nDe, nf } from "@/lib/format";

export const REPO_URL = "https://github.com/teopaleface/CyberPunks";

type Vars = CSSProperties & Record<`--${string}`, string | number>;

const STEPS = [
  { name: "Perceive", ro: "citește contoarele, vremea, posturile", at: HERO_STEPS.perceive },
  { name: "Estimate", ro: "modelele dau scoruri cu interval", at: HERO_STEPS.estimate },
  { name: "Decide", ro: "reguli cu praguri; la nesiguranță, un om", at: HERO_STEPS.decide },
  { name: "Act", ro: "trasee, ordine de lucru, alerte", at: HERO_STEPS.act },
];

export function Hero({ map }: { map: HeroMapData }) {
  const p = map.plan;
  return (
    <section id="top" aria-labelledby="hero-title" className="relative isolate overflow-hidden">
      <Horizon />
      <div className="mx-auto grid max-w-[1440px] gap-x-6 gap-y-12 px-5 pt-10 pb-24 sm:px-8 lg:min-h-[calc(100dvh-4rem)] lg:grid-cols-12 lg:grid-rows-[1fr_auto_1fr] lg:pt-6 lg:pb-28 xl:px-12 2xl:max-w-[1680px]">
        <div className="lg:col-span-5 lg:col-start-1 lg:row-start-2">
          <h1
            id="hero-title"
            className="hero-rise text-[clamp(2.9rem,4.9vw,5.3rem)] leading-[0.95] font-semibold tracking-[-0.045em] text-balance"
          >
            <span className="block lg:whitespace-nowrap">Tomorrow’s crews,</span>
            <span className="block lg:whitespace-nowrap">planned tonight.</span>
          </h1>
          <p className="hero-rise mt-7 max-w-[34rem] text-[clamp(1.075rem,1.25vw,1.3rem)] leading-relaxed text-ink-2" style={{ "--delay": "120ms" } as Vars}>
            Daybreak decide în fiecare seară unde merg mâine echipele de teren Rețele Electrice: ce contor se verifică, ce post
            pierde energie, unde lovește furtuna, unde urcă tensiunea. Fiecare decizie are o explicație, iar ce nu e sigur
            ajunge la un om.
          </p>
          <div className="hero-rise mt-9 flex flex-wrap items-center gap-3" style={{ "--delay": "220ms" } as Vars}>
            <a
              href="#demo"
              className="inline-flex h-12 items-center rounded-lg bg-ppc-energy px-6 text-[1.02rem] font-semibold text-white transition-[background-color,transform] duration-150 ease-out hover:bg-[#2b52f0] active:scale-[0.97]"
            >
              Vezi demo-ul
            </a>
            <a
              href={REPO_URL}
              className="inline-flex h-12 items-center gap-2.5 rounded-lg border border-rule-strong px-5 text-[1.02rem] font-medium text-ink transition-[border-color,background-color,transform] duration-150 ease-out hover:border-ink-3 hover:bg-night-3 active:scale-[0.97]"
            >
              <GitHubMark />
              Codul pe GitHub
            </a>
          </div>
        </div>

        <ol
          className="hero-rise grid max-w-[40rem] grid-cols-2 gap-x-6 gap-y-6 self-start sm:grid-cols-4 lg:col-span-5 lg:col-start-1 lg:row-start-3 lg:mt-4 max-lg:order-last"
          aria-label="Pașii agentului"
          style={{ "--delay": "320ms" } as Vars}
        >
            {STEPS.map((s, i) => (
              <li key={s.name} className="min-w-0">
                <div className="relative h-px bg-rule">
                  <span className="hero-step-bar absolute inset-0 bg-ppc-blue" style={{ "--delay": `${s.at}ms` } as Vars} />
                </div>
                <p className="hero-step mt-3 text-[0.95rem] font-semibold tracking-[-0.01em]" style={{ "--delay": `${s.at}ms` } as Vars}>
                  <span className="num text-ink-3">{i + 1}</span> {s.name}
                </p>
                <p className="mt-1 text-[0.86rem] leading-snug text-ink-3">{s.ro}</p>
              </li>
            ))}
        </ol>

        <figure className="relative lg:col-span-7 lg:col-start-6 lg:row-span-3 lg:row-start-1 lg:-mr-4 lg:self-center xl:-mr-8">
          <HeroMap map={map} />
          <figcaption className="mt-5">
            {p ? (
              <p className="max-w-[48rem] text-[0.86rem] leading-relaxed text-ink-3">
                Planul real al agentului pentru {formatDateRo(p.date)}, ziua din scenariul demo:{" "}
                <span className="text-ink-2">
                  <Dot c="#3b82f0" /> {nDe(p.bySource.A)} lucrări la contoare și posturi, <Dot c="#b84fc0" /> {nDe(p.bySource.B)} zone cu
                  risc de furtună, <Dot c="#c4880a" /> {nDe(p.bySource.C)} posturi cu tensiune mare
                </span>
                . {nDe(p.assigned)} lucrări au intrat în traseele a {nf(p.crews)} echipe, {nf(p.remote)} se verifică întâi de la distanță,{" "}
                <span className="text-ppc-orange-soft">{nf(p.human)} așteaptă decizia unui om</span>. Contoarele, posturile, echipele și
                bazele sunt sintetice, puse pe harta reală; vremea zilei e reală.
              </p>
            ) : (
              <p className="text-[0.86rem] text-ink-3">Planul demo nu e generat încă (în lucru).</p>
            )}
          </figcaption>
        </figure>
      </div>
    </section>
  );
}

function Dot({ c }: { c: string }) {
  return <span aria-hidden className="mr-0.5 inline-block size-2 translate-y-[-1px] rounded-full align-middle" style={{ background: c }} />;
}

/** Zorii: un arc de orizont în culorile PPC, cu soarele portocaliu în mijloc. Decor, ascuns cititoarelor. */
function Horizon() {
  return (
    <div aria-hidden className="hero-horizon pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-[46vh] min-h-[300px] overflow-hidden">
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(120% 90% at 50% 100%, rgba(22,63,232,0.30) 0%, rgba(0,163,224,0.10) 38%, rgba(0,15,30,0) 70%)",
        }}
      />
      <div
        className="absolute top-[78%] left-1/2 h-[220vh] w-[230vw] -translate-x-1/2 rounded-[50%] bg-night"
        style={{
          boxShadow:
            "0 -1px 0 0 rgba(0,163,224,0.85), 0 -6px 26px -4px rgba(0,163,224,0.55), 0 -30px 120px -10px rgba(22,63,232,0.55)",
        }}
      />
      <div
        className="absolute top-[78%] left-1/2 h-[90px] w-[min(56vw,880px)] -translate-x-1/2 -translate-y-1/2"
        style={{ background: "radial-gradient(50% 50% at 50% 50%, rgba(250,70,22,0.55) 0%, rgba(250,70,22,0.18) 40%, rgba(250,70,22,0) 72%)" }}
      />
      <div
        className="absolute top-[78%] left-1/2 h-[2px] w-[min(34vw,520px)] -translate-x-1/2 -translate-y-1/2 rounded-full"
        style={{ background: "linear-gradient(90deg, rgba(250,70,22,0), #fa4616 30%, #ffb08f 50%, #fa4616 70%, rgba(250,70,22,0))" }}
      />
    </div>
  );
}

function GitHubMark() {
  return (
    <svg aria-hidden viewBox="0 0 16 16" className="size-[18px]" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}
