/**
 * Markerul unei lucrări, ca șir SVG: îl folosesc și harta (elemente DOM pentru MapLibre), și componentele React.
 * Culorile vin din variabilele temei, prin `style` (atributele SVG nu înțeleg `var()`).
 * Litera sursei e mereu desenată, ca identitatea să nu depindă doar de culoare.
 */
import type { DecisionType, Source } from "@/lib/contracts";

export type MarkerKind = "assigned" | "human" | "remote" | "pending" | "invalid";

export function markerKind(decision: DecisionType | null | undefined): MarkerKind {
  switch (decision) {
    case "assigned":
      return "assigned";
    case "human_review":
      return "human";
    case "remote_action":
    case "notify":
      return "remote";
    case "rejected_invalid":
      return "invalid";
    default:
      return "pending"; // amânată sau fără decizie
  }
}

const COLOR: Record<Source, string> = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" };
const ON: Record<Source, string> = { A: "#fff", B: "#fff", C: "var(--ink)" };
const OUTLINE: Record<Source, boolean> = { A: false, B: false, C: true };

export interface MarkerOpts {
  source: Source;
  kind?: MarkerKind;
  selected?: boolean;
  /** Raza discului, în px. */
  r?: number;
}

/** SVG pătrat de 36×36 (centrul la 18,18). */
export function markerSvg({ source, kind = "assigned", selected = false, r = 10 }: MarkerOpts, size = 36): string {
  const c = 18;
  const col = COLOR[source];
  let p = "";
  if (selected) p += `<circle cx="${c}" cy="${c}" r="${r + 6.5}" style="fill:none;stroke:var(--ink)" stroke-width="2.2"/>`;
  if (kind === "human") {
    p += `<circle cx="${c}" cy="${c}" r="${r + 5.5}" style="fill:var(--panel);stroke:var(--att)" stroke-width="3.2"/>`;
  }
  let letter = ON[source];
  if (kind === "pending" || kind === "invalid") {
    p += `<circle cx="${c}" cy="${c}" r="${r}" style="fill:var(--panel);stroke:${col}" stroke-width="2.6" stroke-dasharray="3.4 2.3"/>`;
    if (OUTLINE[source]) p += `<circle cx="${c}" cy="${c}" r="${r + 2}" style="fill:none;stroke:var(--ink)" stroke-width=".8"/>`;
    letter = OUTLINE[source] ? "var(--ink)" : col;
  } else if (kind === "remote") {
    p += `<circle cx="${c}" cy="${c}" r="${r}" style="fill:var(--panel);stroke:${col}" stroke-width="3"/>`;
    letter = OUTLINE[source] ? "var(--ink)" : col;
  } else {
    p += `<circle cx="${c}" cy="${c}" r="${r + 1.6}" style="fill:var(--panel)"/>`;
    p += `<circle cx="${c}" cy="${c}" r="${r}" style="fill:${col}${OUTLINE[source] ? ";stroke:var(--ink)" : ""}"${OUTLINE[source] ? ' stroke-width="1.5"' : ""}/>`;
  }
  const fs = r > 9 ? 13 : 11.5;
  p += `<text x="${c}" y="${c + fs * 0.36}" text-anchor="middle" font-size="${fs}" font-weight="700" style="fill:${letter};font-family:var(--font-sans)">${source}</text>`;
  return `<svg width="${size}" height="${size}" viewBox="0 0 36 36" aria-hidden="true" style="overflow:visible">${p}</svg>`;
}

/** Baza operativă: bara groasă din schema monofilară. */
export function depotSvg(size = 36): string {
  return `<svg width="${size}" height="${size}" viewBox="0 0 36 36" aria-hidden="true"><rect x="14.5" y="7" width="7" height="22" style="fill:var(--ink);stroke:var(--panel)" stroke-width="1.5"/></svg>`;
}
