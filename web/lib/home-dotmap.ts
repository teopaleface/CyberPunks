/**
 * Harta de puncte a României, din conturul real al județelor (public/geo/ro-judete.json):
 * o grilă hexagonală, iar punctul se păstrează dacă cade într-un județ. Culoarea vine din regiunea județului.
 * Calculul e pur (testabil); `getRomaniaDots` îl face o singură dată pe server și ține rezultatul în memorie.
 */
import { readFile } from "node:fs/promises";
import path from "node:path";

export type DotRegion = "muntenia_sud" | "dobrogea" | "banat" | "other";

export interface Dot {
  x: number;
  y: number;
  region: DotRegion;
}

export interface DotMap {
  width: number;
  height: number;
  /** Distanța dintre puncte, în unitățile hărții. */
  pitch: number;
  dots: Dot[];
}

type Ring = [number, number][];
interface Feature {
  properties: { name?: string; re_region?: string | null };
  geometry: { type: "Polygon"; coordinates: Ring[] } | { type: "MultiPolygon"; coordinates: Ring[][] };
}
export interface GeoJson {
  features: Feature[];
}

export function inRing(lon: number, lat: number, ring: Ring): boolean {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

/** Poligon cu găuri: în inelul exterior și în niciun inel interior. */
export function inPolygon(lon: number, lat: number, rings: Ring[]): boolean {
  if (!rings.length || !inRing(lon, lat, rings[0])) return false;
  for (let i = 1; i < rings.length; i++) if (inRing(lon, lat, rings[i])) return false;
  return true;
}

const REGIONS = new Set(["muntenia_sud", "dobrogea", "banat"]);

export function computeDots(geo: GeoJson, lonStep = 0.18): DotMap {
  const polys = geo.features.flatMap((f) => {
    const region = (REGIONS.has(f.properties.re_region ?? "") ? f.properties.re_region : "other") as DotRegion;
    const list = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
    return list.map((rings) => {
      let w = 180, e = -180, s = 90, n = -90;
      for (const [lon, lat] of rings[0]) {
        w = Math.min(w, lon);
        e = Math.max(e, lon);
        s = Math.min(s, lat);
        n = Math.max(n, lat);
      }
      return { rings, region, bbox: [w, s, e, n] as const };
    });
  });
  let w = 180, e = -180, s = 90, n = -90;
  for (const p of polys) {
    w = Math.min(w, p.bbox[0]);
    s = Math.min(s, p.bbox[1]);
    e = Math.max(e, p.bbox[2]);
    n = Math.max(n, p.bbox[3]);
  }
  if (!polys.length) return { width: 0, height: 0, pitch: 1, dots: [] };

  // pe hartă 1° de longitudine = cos(46°) din 1° de latitudine; rândurile hexagonale stau la 0,866 din pas
  const k = 100;
  const colW = lonStep * 0.7 * k;
  const rowH = colW * 0.866;
  const latStep = rowH / k;
  const dots: Dot[] = [];
  for (let row = 0; n - row * latStep >= s; row++) {
    const lat = n - row * latStep;
    const shift = row % 2 ? lonStep / 2 : 0;
    for (let lon = w + shift; lon <= e; lon += lonStep) {
      const hit = polys.find((p) => lon >= p.bbox[0] && lon <= p.bbox[2] && lat >= p.bbox[1] && lat <= p.bbox[3] && inPolygon(lon, lat, p.rings));
      if (hit) dots.push({ x: round1((lon - w) * 0.7 * k), y: round1(row * rowH), region: hit.region });
    }
  }
  return { width: Math.round((e - w) * 0.7 * k + colW), height: Math.round((n - s) * k + rowH), pitch: colW, dots };
}

const round1 = (v: number) => Math.round(v * 10) / 10;

let cached: Promise<DotMap> | null = null;

export function getRomaniaDots(): Promise<DotMap> {
  cached ??= readFile(path.join(process.cwd(), "public/geo/ro-judete.json"), "utf8").then((t) => computeDots(JSON.parse(t) as GeoJson));
  return cached;
}
