import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { cache } from "react";
import { RE_BOUNDS } from "@/lib/plan-screen";

/**
 * Harta mică a zonei Rețele Electrice, desenată ca SVG din conturul județelor
 * (Natural Earth, domeniu public, web/public/geo/ro-judete.json). Calculată pe server, ca browserul
 * să primească doar căile SVG.
 */
export interface LocatorGeo {
  width: number;
  height: number;
  /** [vest, sud, est, nord] */
  bounds: [number, number, number, number];
  counties: { name: string; region: string | null; d: string }[];
}

type Ring = [number, number][];
type Geometry = { type: "Polygon"; coordinates: Ring[] } | { type: "MultiPolygon"; coordinates: Ring[][] };

export const loadLocatorGeo = cache(async (): Promise<LocatorGeo | null> => {
  try {
    const file = path.join(process.cwd(), "public", "geo", "ro-judete.json");
    const json = JSON.parse(await readFile(file, "utf8")) as {
      features: { properties: { name: string; re_region: string | null }; geometry: Geometry }[];
    };
    const [w, s, e, n] = RE_BOUNDS;
    const k = Math.cos((((s + n) / 2) * Math.PI) / 180);
    const width = 320;
    const height = Math.round((width * (n - s)) / ((e - w) * k));
    const px = (lon: number) => (((lon - w) / (e - w)) * width).toFixed(1);
    const py = (lat: number) => (((n - lat) / (n - s)) * height).toFixed(1);
    const ringPath = (ring: Ring) => `M${ring.map(([lon, lat]) => `${px(lon)},${py(lat)}`).join("L")}Z`;
    const counties = json.features.map((f) => {
      const polys = f.geometry.type === "Polygon" ? [f.geometry.coordinates] : f.geometry.coordinates;
      return { name: f.properties.name, region: f.properties.re_region, d: polys.map((p) => p.map(ringPath).join("")).join("") };
    });
    return { width, height, bounds: RE_BOUNDS, counties };
  } catch {
    return null;
  }
});
