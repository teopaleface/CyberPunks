/**
 * Geometria hărții din hero: județele României (Natural Earth 1:10m, domeniu public) desenate
 * ca o rețea de puncte. Totul se calculează la build, pe server: browserul primește doar
 * câteva căi SVG scurte (un rând de puncte = o linie cu `stroke-dasharray="0 pas"`).
 */

export type Ring = [number, number][];
export type Geometry = { type: "Polygon"; coordinates: Ring[] } | { type: "MultiPolygon"; coordinates: Ring[][] };
export interface CountyFeature {
  properties: { name: string; iso: string; re_region: string | null };
  geometry: Geometry;
}

export interface Projection {
  width: number;
  height: number;
  x: (lon: number) => number;
  y: (lat: number) => number;
}

/** Proiecție echirectangulară cu scara longitudinii corectată la latitudinea medie. */
export function makeProjection(bounds: [number, number, number, number], width: number): Projection {
  const [w, s, e, n] = bounds;
  const k = Math.cos((((s + n) / 2) * Math.PI) / 180);
  const height = (width * (n - s)) / ((e - w) * k);
  return {
    width,
    height,
    x: (lon) => ((lon - w) / (e - w)) * width,
    y: (lat) => ((n - lat) / (n - s)) * height,
  };
}

function polygonsOf(g: Geometry): Ring[][] {
  return g.type === "Polygon" ? [g.coordinates] : g.coordinates;
}

/**
 * Intervalele [x1, x2) din interiorul poligoanelor pe linia orizontală y (regula par-impar,
 * deci găurile se respectă). Coordonatele sunt deja proiectate.
 */
function scanline(rings: Ring[], y: number): [number, number][] {
  const xs: number[] = [];
  for (const ring of rings) {
    for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      const [xi, yi] = ring[i];
      const [xj, yj] = ring[j];
      if (yi > y !== yj > y) xs.push(xi + ((y - yi) / (yj - yi)) * (xj - xi));
    }
  }
  xs.sort((a, b) => a - b);
  const spans: [number, number][] = [];
  for (let i = 0; i + 1 < xs.length; i += 2) spans.push([xs[i], xs[i + 1]]);
  return spans;
}

/**
 * Rândurile de puncte pentru un grup de județe, ca o singură cale SVG: „M x y H x2” pe fiecare
 * rând. Cu `stroke-dasharray="0 pitch"` și capete rotunde, fiecare rând devine un șir de puncte
 * aliniate pe aceeași grilă (capetele se rotunjesc la multipli de `pitch`, deci județele vecine
 * nu dublează punctele de la graniță).
 */
export function dotRowsPath(features: CountyFeature[], proj: Projection, pitch: number): { d: string; dots: number } {
  const projected = features.map((f) =>
    polygonsOf(f.geometry).map((poly) => poly.map((ring) => ring.map(([lon, lat]) => [proj.x(lon), proj.y(lat)] as [number, number]))),
  );
  let d = "";
  let dots = 0;
  for (let y = pitch / 2; y < proj.height; y += pitch) {
    for (const polys of projected) {
      for (const rings of polys) {
        for (const [x1, x2] of scanline(rings, y)) {
          const xs = Math.ceil(x1 / pitch - 0.5) * pitch + pitch / 2;
          const xe = Math.ceil(x2 / pitch - 0.5) * pitch - pitch / 2;
          if (xe < xs - 0.01) continue;
          const n = Math.round((xe - xs) / pitch) + 1;
          dots += n;
          d += `M${xs.toFixed(1)} ${y.toFixed(1)}H${(xe + 0.01).toFixed(2)}`;
        }
      }
    }
  }
  return { d, dots };
}

/** Conturul județelor (pentru o linie subțire în jurul zonei Rețele Electrice). */
export function outlinePath(features: CountyFeature[], proj: Projection): string {
  return features
    .map((f) =>
      polygonsOf(f.geometry)
        .map((poly) => poly.map((ring) => `M${ring.map(([lon, lat]) => `${proj.x(lon).toFixed(1)},${proj.y(lat).toFixed(1)}`).join("L")}Z`).join(""))
        .join(""),
    )
    .join("");
}

/** Centrul celulei de grilă în care cade un punct (ca lucrările să stea pe aceeași rețea). */
export function snap(v: number, pitch: number): number {
  return Math.floor(v / pitch) * pitch + pitch / 2;
}
