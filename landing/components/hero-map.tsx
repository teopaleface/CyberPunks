import type { CSSProperties } from "react";
import type { HeroMapData, ItemState, Source } from "@/lib/data";

const SRC: Record<Source, string> = { A: "#3b82f0", B: "#b84fc0", C: "#c4880a" };

/** pașii secvenței din hero, în ms (aceiași cu legenda Perceive → Act de sub hartă) */
export const HERO_STEPS = { perceive: 400, estimate: 1100, decide: 1900, act: 2500 } as const;

type Vars = CSSProperties & Record<`--${string}`, string | number>;

/**
 * Harta din hero: România din puncte, zona Rețele Electrice mai aprinsă, lucrările zilei demo
 * pe aceeași grilă (culoarea sursei), traseele echipelor în alb și o lupă peste București și Ilfov.
 * Randată pe server; animația e doar CSS (globals.css), oprită de prefers-reduced-motion.
 */
export function HeroMap({ map }: { map: HeroMapData }) {
  const { width, height, pitch, lens } = map;
  const labels: { x: number; y: number; t: string }[] = [
    { x: 0.105, y: 0.33, t: "Banat" },
    { x: 0.585, y: 0.985, t: "Muntenia Sud" },
    { x: 0.9, y: 0.6, t: "Dobrogea" },
  ];
  return (
    <svg
      viewBox={`0 0 ${width} ${height.toFixed(0)}`}
      className="block h-auto w-full overflow-visible"
      role="img"
      aria-labelledby="hero-map-title hero-map-desc"
    >
      <title id="hero-map-title">Planul agentului pentru ziua din scenariul demo</title>
      <desc id="hero-map-desc">
        Harta României din puncte. Zona Rețele Electrice (Banat, Muntenia Sud, Dobrogea) e mai luminoasă. Punctele colorate
        sunt lucrările zilei: albastru contoare și bilanț pe post, violet furtună, chihlimbar tensiune. Liniile albe sunt
        traseele echipelor. Lupa mărește Bucureștiul și Ilfovul.
      </desc>
      <defs>
        {lens && (
          <clipPath id="lens-clip">
            <circle cx={lens.cx} cy={lens.cy} r={lens.r - 1} />
          </clipPath>
        )}
        <radialGradient id="lens-fill" cx="50%" cy="45%" r="60%">
          <stop offset="0%" stopColor="#0a2238" />
          <stop offset="100%" stopColor="#04182b" />
        </radialGradient>
        <pattern id="lens-grid" width="11" height="11" patternUnits="userSpaceOnUse">
          <circle cx="5.5" cy="5.5" r="0.9" fill="#1b3a57" />
        </pattern>
      </defs>

      {/* România din puncte: restul țării stins, zona Rețele Electrice aprinsă */}
      <g className="hero-base" fill="none" strokeLinecap="round" strokeDasharray={`0 ${pitch}`}>
        <path d={map.restDots} stroke="#1c3a58" strokeWidth={2.8} />
        <path d={map.reDots} stroke="#3a6f9f" strokeWidth={3.6} />
      </g>

      <g className="max-sm:hidden" fill="#8197ac" fontSize={15} fontWeight={500} letterSpacing="0.01em">
        {labels.map((l) => (
          <text key={l.t} x={l.x * width} y={l.y * height} textAnchor="middle" className="hero-dim" style={{ "--delay": "300ms" } as Vars}>
            {l.t}
          </text>
        ))}
      </g>

      {/* lucrările zilei, pe grilă: o celulă aprinsă = una sau mai multe lucrări */}
      <g>
        {map.cells.map((c) => (
          <circle
            key={`${c.x}-${c.y}`}
            cx={c.x}
            cy={c.y}
            r={c.n > 20 ? 4.6 : 3.8}
            fill={SRC[c.src]}
            className="hero-cell"
            style={{ "--order": c.order } as Vars}
          />
        ))}
        {map.cells
          .filter((c) => c.human && c.src === "B")
          .map((c) => (
            <circle
              key={`h-${c.x}-${c.y}`}
              cx={c.x}
              cy={c.y}
              r={8.5}
              fill="none"
              stroke="#fa4616"
              strokeWidth={1.8}
              className="hero-ring"
              style={{ "--delay": `${HERO_STEPS.decide}ms` } as Vars}
            />
          ))}
      </g>

      {/* traseele care se văd la scara țării (echipele trimise din timp în Banat) */}
      <g fill="none" stroke="#eef3f8" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        {map.routes.map((r, i) => (
          <path key={r.crew} d={r.d} pathLength={1} className="hero-route" style={{ "--delay": `${HERO_STEPS.act + i * 120}ms` } as Vars} />
        ))}
      </g>
      <g fill="#eef3f8">
        {map.depots.map((d) => (
          <rect key={`${d.x}-${d.y}`} x={d.x - 3.5} y={d.y - 3.5} width={7} height={7} rx={1.5} className="hero-dim" style={{ "--delay": `${HERO_STEPS.act}ms` } as Vars} />
        ))}
      </g>

      {lens && <Lens lens={lens} />}
    </svg>
  );
}

function Lens({ lens }: { lens: NonNullable<HeroMapData["lens"]> }) {
  const { cx, cy, r, anchor } = lens;
  // linia de la București la marginea lupei
  const dx = cx - anchor.x;
  const dy = cy - anchor.y;
  const len = Math.hypot(dx, dy);
  const ex = cx - (dx / len) * r;
  const ey = cy - (dy / len) * r;
  const itemStyle = (s: ItemState): { r: number; opacity: number } =>
    s === "route" ? { r: 5, opacity: 1 } : s === "human" ? { r: 3.6, opacity: 1 } : { r: 2.6, opacity: 0.42 };
  return (
    <g>
      <g className="hero-dim" style={{ "--delay": "700ms" } as Vars}>
        <circle cx={anchor.x} cy={anchor.y} r={9} fill="none" stroke="#a9bccd" strokeWidth={1.4} />
        <line x1={anchor.x + (dx / len) * 9} y1={anchor.y + (dy / len) * 9} x2={ex} y2={ey} stroke="#4a7aa6" strokeWidth={1.3} />
        <circle cx={cx} cy={cy} r={r} fill="url(#lens-fill)" stroke="#4a7aa6" strokeWidth={1.4} />
        <circle cx={cx} cy={cy} r={r} fill="url(#lens-grid)" />
        <text x={cx} y={cy - r - 14} textAnchor="middle" fill="#a9bccd" fontSize={15} fontWeight={500} className="max-sm:hidden">
          București și Ilfov
        </text>
      </g>
      <g clipPath="url(#lens-clip)">
        {lens.items.map((it, i) => {
          const st = itemStyle(it.state);
          const fading = it.state !== "route" && it.state !== "human";
          return (
            <circle
              key={i}
              cx={it.x}
              cy={it.y}
              r={st.r}
              fill={SRC[it.src]}
              opacity={st.opacity}
              stroke={it.state === "route" ? "#eef3f8" : undefined}
              strokeWidth={it.state === "route" ? 1.6 : undefined}
              className={fading ? "hero-demote" : "hero-cell"}
              style={(fading ? {} : { "--order": 0.55 }) as Vars}
            />
          );
        })}
        {lens.items
          .filter((it) => it.state === "human")
          .map((it, i) => (
            <circle
              key={`h${i}`}
              cx={it.x}
              cy={it.y}
              r={7.5}
              fill="none"
              stroke="#fa4616"
              strokeWidth={1.6}
              className="hero-ring"
              style={{ "--delay": `${HERO_STEPS.decide + (i % 6) * 60}ms` } as Vars}
            />
          ))}
        <g fill="none" stroke="#eef3f8" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" opacity={0.9}>
          {lens.routes.map((rt, i) => (
            <path key={rt.crew} d={rt.d} pathLength={1} className="hero-route" style={{ "--delay": `${HERO_STEPS.act + i * 140}ms` } as Vars} />
          ))}
        </g>
        <g fill="#eef3f8">
          {lens.depots.map((d) => (
            <rect key={`${d.x}-${d.y}`} x={d.x - 4.5} y={d.y - 4.5} width={9} height={9} rx={2} className="hero-dim" style={{ "--delay": `${HERO_STEPS.act}ms` } as Vars} />
          ))}
        </g>
      </g>
    </g>
  );
}
