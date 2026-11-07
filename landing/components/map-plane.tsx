import type { CSSProperties } from "react";
import type { HeroMapData, Source } from "@/lib/data";

const SRC: Record<Source, string> = { A: "#3b82f0", B: "#b84fc0", C: "#c4880a" };
type Vars = CSSProperties & Record<`--${string}`, string | number>;

/**
 * Harta din hero, ca un peisaj înclinat în zori: România din puncte, zona Rețele Electrice mai
 * aprinsă, lucrările zilei demo ca lumini pe grilă (culoarea sursei), cu un halou estompat.
 * Fără etichete: e imaginea produsului, detaliile vin mai jos în pagină.
 */
export function MapPlane({ map }: { map: HeroMapData }) {
  const { width, height, pitch } = map;
  return (
    <svg viewBox={`0 0 ${width} ${height.toFixed(0)}`} className="block h-auto w-full overflow-visible" aria-hidden>
      <defs>
        <filter id="plane-glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="7" />
        </filter>
      </defs>
      <g fill="none" strokeLinecap="round" strokeDasharray={`0 ${pitch}`}>
        <path d={map.restDots} stroke="#1e3d5c" strokeWidth={2.9} />
        <path d={map.reDots} stroke="#4b86bd" strokeWidth={3.7} />
      </g>
      {/* haloul luminilor, apoi luminile */}
      <g filter="url(#plane-glow)" opacity={0.9}>
        {map.cells.map((c) => (
          <circle key={`g-${c.x}-${c.y}`} cx={c.x} cy={c.y} r={c.n > 20 ? 11 : 8} fill={SRC[c.src]} className="hero-cell" style={{ "--order": c.order } as Vars} />
        ))}
      </g>
      <g>
        {map.cells.map((c) => (
          <circle key={`${c.x}-${c.y}`} cx={c.x} cy={c.y} r={c.n > 20 ? 4.8 : 4} fill={SRC[c.src]} className="hero-cell" style={{ "--order": c.order } as Vars} />
        ))}
      </g>
      <g fill="none" stroke="#f5f7fa" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
        {map.routes.map((r, i) => (
          <path key={r.crew} d={r.d} pathLength={1} className="hero-route" style={{ "--delay": `${2700 + i * 140}ms` } as Vars} />
        ))}
      </g>
    </svg>
  );
}
