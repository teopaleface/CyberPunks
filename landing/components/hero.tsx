import type { CSSProperties } from "react";
import type { HeroMapData } from "@/lib/data";
import { formatDate, nf } from "@/lib/format";
import { MapPlane } from "./map-plane";
import { REPO_URL } from "./site-header";

type Vars = CSSProperties & Record<`--${string}`, string | number>;

/**
 * Hero în stilul paginilor de produs Apple: numele produsului, o frază mare, o propoziție, două
 * acțiuni; dedesubt, imaginea produsului: harta înclinată ca un peisaj, cu răsăritul PPC în spate.
 */
export function Hero({ map }: { map: HeroMapData }) {
  const p = map.plan;
  return (
    <section id="top" aria-labelledby="hero-title" className="relative isolate overflow-hidden text-center">
      <div className="flex min-h-[calc(100svh-52px)] flex-col">
        <div className="mx-auto max-w-[1180px] px-5 pt-[clamp(2.5rem,7vh,6rem)] sm:px-8">
          <p className="hero-rise text-[1.3rem] font-semibold tracking-[-0.02em] text-ink-2 sm:text-[1.5rem]">Daybreak</p>
          <h1 id="hero-title" className="t-hero hero-rise mx-auto mt-2 max-w-[13ch] text-balance" style={{ "--delay": "80ms" } as Vars}>
            Tomorrow’s crews, planned tonight.
          </h1>
          <p className="t-intro hero-rise mx-auto mt-5 max-w-[36rem] text-balance text-ink-3" style={{ "--delay": "160ms" } as Vars}>
            An AI agent that decides, every evening, where the Rețele Electrice field crews go the next morning.
          </p>
          <div className="hero-rise mt-8 flex flex-wrap items-center justify-center gap-x-7 gap-y-4" style={{ "--delay": "240ms" } as Vars}>
            <a
              href="#demo"
              className="inline-flex h-11 items-center rounded-full bg-ppc-energy px-6 text-[1.06rem] font-medium text-white transition-[background-color,transform] duration-150 ease-out hover:bg-ppc-energy-hover active:scale-[0.97]"
            >
              Watch the demo
            </a>
            <a href={REPO_URL} className="group inline-flex items-center gap-1 text-[1.06rem] text-ppc-blue hover:underline">
              Read the code
              <Chevron />
            </a>
          </div>
        </div>

        {/* imaginea produsului: harta înclinată ca un peisaj, răsăritul în spatele orizontului */}
        <div className="relative mt-2 min-h-[clamp(240px,36vw,500px)] flex-1" style={{ perspective: "1100px", perspectiveOrigin: "50% 0%" }}>
          <Sunrise />
          <div
            className="absolute inset-x-0 top-0 bottom-[13%] flex items-end justify-center [@media(max-height:960px)_and_(min-width:1024px)]:bottom-[19%]"
            style={{ maskImage: "linear-gradient(to top, black 62%, transparent 100%)", WebkitMaskImage: "linear-gradient(to top, black 62%, transparent 100%)" }}
          >
            <div className="hero-plane w-[min(1080px,132vw)] shrink-0 2xl:w-[1240px]" style={{ transform: "rotateX(61deg)", transformOrigin: "50% 100%" }}>
              <MapPlane map={map} />
            </div>
          </div>
        </div>
      </div>

      {p && (
        <p
          className="hero-fade mx-auto max-w-[40rem] px-5 pt-6 pb-24 text-[0.82rem] leading-relaxed text-ink-3 sm:pb-32"
          style={{ "--delay": "1600ms" } as Vars}
        >
          The agent’s actual plan for {formatDate(p.date)}, the demo day: {nf(p.itemsIn)} work items in, {nf(p.assigned)} on the routes of{" "}
          {nf(p.crews)} crews, {nf(p.remote)} checked remotely first, {nf(p.human)} sent to a person. Meters, substations, crews and depots are
          synthetic, placed on the real map; the weather is real.
        </p>
      )}
    </section>
  );
}

/** Răsăritul: soarele portocaliu pe orizont, cerul albastru deasupra. Decor, ascuns cititoarelor de ecran. */
function Sunrise() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10">
      <div
        className="hero-sun absolute top-[-30%] left-1/2 h-[80%] w-[min(1500px,160vw)]"
        style={{
          transform: "translate(-50%, 0)",
          background:
            "radial-gradient(42% 46% at 50% 50%, rgba(250,70,22,0.55) 0%, rgba(255,140,90,0.28) 22%, rgba(0,163,224,0.20) 48%, rgba(22,63,232,0.10) 66%, rgba(0,15,30,0) 80%)",
        }}
      />
      <div
        className="hero-sun absolute top-[10%] left-1/2 h-[2px] w-[min(760px,80vw)] rounded-full"
        style={{
          transform: "translate(-50%, 0)",
          background: "linear-gradient(90deg, rgba(250,70,22,0), rgba(255,176,143,0.95) 50%, rgba(250,70,22,0))",
          boxShadow: "0 0 24px 4px rgba(250,70,22,0.45)",
        }}
      />
    </div>
  );
}

function Chevron() {
  return (
    <svg
      aria-hidden
      viewBox="0 0 8 14"
      className="mt-[2px] h-[0.72em] w-auto transition-transform duration-200 ease-out group-hover:translate-x-0.5"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M1.5 1.5 6.5 7l-5 5.5" />
    </svg>
  );
}
