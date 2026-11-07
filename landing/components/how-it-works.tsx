import type { CSSProperties } from "react";
import type { CityMapData, Source } from "@/lib/data";
import { nf } from "@/lib/format";
import { Scrolly } from "./scrolly";

const SRC: Record<Source, string> = { A: "#3b82f0", B: "#b84fc0", C: "#c4880a" };
type Vars = CSSProperties & Record<`--${string}`, string | number>;

/**
 * „How it works”: harta Bucureștiului și a Ilfovului stă fixă, iar cei patru pași ai agentului trec
 * pe lângă ea. Fiecare pas schimbă harta (styles în globals.css, `.city`): lucrările apar, primesc
 * scoruri, cele mai multe merg la verificare de la distanță, iar echipele primesc trasee.
 */
export function HowItWorks({ city }: { city: CityMapData | null }) {
  const c = city?.counts;
  const steps = [
    {
      name: "Perceive.",
      lead: "It reads the grid every evening.",
      body: "Smart-meter readings, each substation’s own meter, tomorrow’s weather forecast, and the crews and depots available.",
      chip: c ? `${nf(c.items)} work items across three regions` : null,
    },
    {
      name: "Estimate.",
      lead: "Trained models score every risk.",
      body: "A broken or tampered meter, energy lost at a substation, outages from tomorrow’s storm, voltage above 253 V at noon. Every score comes with an interval, not just a number.",
      chip: null,
    },
    {
      name: "Decide.",
      lead: "Rules weigh value against cost.",
      body: "Cheap remote checks come first. Crews go where an hour of work recovers the most. When a model isn’t sure, the case goes to a person.",
      chip: c ? `${nf(c.remote)} checked remotely, ${nf(c.human)} sent to a person` : null,
    },
    {
      name: "Act.",
      lead: "Routes, work orders, alerts.",
      body: "OR-Tools builds the routes, every crew gets a printable work order, and each decision is logged with the prediction behind it.",
      chip: c ? `${nf(c.route)} stops on ${nf(c.crews)} crew routes, ${nf(Math.round(c.km))} km` : null,
    },
  ];

  return (
    <section id="how" aria-labelledby="how-title" className="relative px-5 pb-16 sm:px-8 sm:pb-24">
      <div className="mx-auto max-w-[1180px]">
        <div className="mx-auto max-w-[980px] text-center">
          <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ppc-blue sm:text-[1.35rem]">How it works</p>
          <h2 id="how-title" className="reveal t-section mt-3 text-balance">
            Perceive. Estimate. Decide. Act.
          </h2>
        </div>

        <Scrolly className="mt-16 grid gap-10 sm:mt-24 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16">
          <div className="relative z-0">
            {steps.map((s, i) => (
              <article
                key={s.name}
                data-scrolly-step={i + 1}
                className="city-step flex min-h-[62vh] flex-col justify-start pt-8 pb-10 lg:min-h-[78vh] lg:justify-center lg:py-10"
              >
                <h3 className="t-title text-ink">
                  <span className="num mr-3 text-ink-3">{i + 1}</span>
                  {s.name}
                </h3>
                <p className="mt-4 max-w-[30rem] text-[clamp(1.1rem,1.4vw,1.3rem)] leading-[1.45] text-ink-3">
                  <span className="text-ink">{s.lead}</span> {s.body}
                </p>
                {s.chip && (
                  <p className="mt-6 inline-flex w-fit items-center rounded-full border border-hairline-strong bg-tile px-4 py-1.5 text-[0.92rem] text-ink-2">
                    {s.chip}
                  </p>
                )}
              </article>
            ))}
          </div>

          <div className="max-lg:sticky max-lg:top-[52px] max-lg:z-20 max-lg:order-first max-lg:-mx-5 max-lg:bg-night max-lg:px-5 max-lg:pt-3 max-lg:pb-2 max-sm:[&_figcaption]:hidden">
            <div className="lg:sticky lg:top-[calc(52px+8vh)]">
              <CityFigure city={city} />
            </div>
          </div>
        </Scrolly>
      </div>
    </section>
  );
}

function CityFigure({ city }: { city: CityMapData | null }) {
  if (!city) {
    return (
      <div className="grid aspect-[4/3] place-items-center rounded-[32px] border border-hairline bg-tile text-ink-3">
        The demo plan isn’t generated yet.
      </div>
    );
  }
  return (
    <figure className="overflow-hidden rounded-[32px] border border-hairline bg-[radial-gradient(120%_90%_at_50%_0%,#0b2440_0%,#04172a_60%)] p-3 sm:p-5">
      <svg viewBox={`0 0 ${city.width} ${city.height.toFixed(0)}`} className="block h-auto w-full" role="img" aria-labelledby="city-title">
        <title id="city-title">
          Bucharest and Ilfov on the demo day: work items as dots, the people-review cases circled in orange, crew routes in white.
        </title>
        <path d={city.dots} fill="none" stroke="#1d3b5a" strokeWidth={3.4} strokeLinecap="round" strokeDasharray={`0 ${city.pitch}`} />
        <g>
          {city.items.map((it, i) => (
            <circle
              key={i}
              cx={it.x}
              cy={it.y}
              r={4.2}
              fill={SRC[it.src]}
              data-state={it.state}
              className="ci"
              style={{ "--s": (0.55 + it.score * 1.15).toFixed(2), "--d": `${(i % 40) * 12}ms` } as Vars}
            />
          ))}
        </g>
        <g fill="none" stroke="#fa4616" strokeWidth={2.2}>
          {city.items
            .filter((it) => it.state === "human")
            .map((it, i) => (
              <circle key={i} cx={it.x} cy={it.y} r={11} className="cring" />
            ))}
        </g>
        <g fill="none" stroke="#f5f7fa" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round">
          {city.routes.map((r, i) => (
            <path key={r.crew} d={r.d} pathLength={1} className="croute" style={{ "--d": `${i * 160}ms` } as Vars} />
          ))}
        </g>
        <g fill="#f5f7fa">
          {city.depots.map((d) => (
            <rect key={`${d.x}-${d.y}`} x={d.x - 7} y={d.y - 7} width={14} height={14} rx={3} className="cdepot" />
          ))}
        </g>
      </svg>
      <figcaption className="flex flex-wrap items-center gap-x-5 gap-y-2 px-2 pt-3 pb-1 text-[0.82rem] text-ink-3">
        <Legend color="#3b82f0" label="Meters and substation losses" />
        <Legend color="#c4880a" label="Voltage" />
        <Legend ring label="Sent to a person" />
        <span className="inline-flex items-center gap-2">
          <span aria-hidden className="h-[2px] w-4 rounded bg-ink" />
          Crew route
        </span>
      </figcaption>
    </figure>
  );
}

function Legend({ color, label, ring }: { color?: string; label: string; ring?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden
        className="size-2.5 rounded-full"
        style={ring ? { boxShadow: "inset 0 0 0 1.5px #fa4616" } : { background: color }}
      />
      {label}
    </span>
  );
}
