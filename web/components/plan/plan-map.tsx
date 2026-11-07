"use client";

import "maplibre-gl/dist/maplibre-gl.css";
import type { Map as MLMap, Marker as MLMarker, StyleSpecification } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import type { Source } from "@/lib/contracts";
import { depotSvg, markerSvg, type MarkerKind } from "@/lib/marker-svg";

export interface MapItem {
  id: string;
  source: Source;
  lat: number;
  lon: number;
  kind: MarkerKind;
  title: string;
  sub?: string;
  /** Eticheta stă mereu vizibilă (lucrări din trasee și cele care așteaptă un om). */
  pinned: boolean;
  attention?: boolean;
}

export interface MapRoute {
  crewId: string;
  /** [lon, lat]: bază → opriri → bază. */
  path: [number, number][];
}

export interface MapDepot {
  id: string;
  label: string;
  lat: number;
  lon: number;
}

export type Bounds = [number, number, number, number];

const WORKER_URL = "/maplibre/maplibre-gl-worker.mjs";

const STYLE_URL = {
  light: "https://tiles.openfreemap.org/styles/positron",
  dark: "https://tiles.openfreemap.org/styles/dark",
} as const;

// --------------------------------------------------------------------------------------------
// Arce: traseele arată ordinea opririlor, nu drumul exact (planificatorul nu dă geometria drumului).
// --------------------------------------------------------------------------------------------
const mercX = (lon: number) => (lon + 180) / 360;
const mercY = (lat: number) => {
  const r = (lat * Math.PI) / 180;
  return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2;
};
const invLon = (x: number) => x * 360 - 180;
const invLat = (y: number) => (Math.atan(Math.sinh(Math.PI * (1 - 2 * y))) * 180) / Math.PI;

export function arc(a: [number, number], b: [number, number], bend = 0.2, n = 32): [number, number][] {
  const ax = mercX(a[0]), ay = mercY(a[1]), bx = mercX(b[0]), by = mercY(b[1]);
  const dx = bx - ax, dy = by - ay;
  const cx = (ax + bx) / 2 - dy * bend, cy = (ay + by) / 2 + dx * bend;
  const out: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const t = i / n, u = 1 - t;
    out.push([
      +invLon(u * u * ax + 2 * u * t * cx + t * t * bx).toFixed(5),
      +invLat(u * u * ay + 2 * u * t * cy + t * t * by).toFixed(5),
    ]);
  }
  return out;
}

// --------------------------------------------------------------------------------------------
// Harta de fundal liniștită: totul gri, culoarea rămâne pentru trasee și markeri.
// --------------------------------------------------------------------------------------------
const PALETTE = {
  light: { bg: "#e4e7e6", water: "#cdd5d8", waterLine: "#c3cdd1", build: "#dadedd", green: "#dfe3e2", land: "#dce0df", road: "#f6f7f5", casing: "#d3d8d8", rail: "#d2d7d7", admin: "#a9b1b3", city: "#3e4952", text: "#6a747c" },
  dark: { bg: "#0a1521", water: "#0d2133", waterLine: "#13304a", build: "#101e2c", green: "#0c1a27", land: "#0c1926", road: "#1b2c3e", casing: "#14243a", rail: "#16263a", admin: "#3a4f66", city: "#c9d3dc", text: "#7f91a3" },
} as const;

const HIDE_SYMBOLS = /highway|road|shield|poi|airport|aeroway|label_other|village|town|water_name_line|waterway|housenum|transit|rail|park/;

function quiet(map: MLMap, theme: "light" | "dark") {
  const P = PALETTE[theme];
  const style = map.getStyle() as StyleSpecification;
  for (const l of style.layers ?? []) {
    const id = l.id;
    try {
      if (l.type === "background") map.setPaintProperty(id, "background-color", P.bg);
      else if (l.type === "fill") {
        if (/water/.test(id)) map.setPaintProperty(id, "fill-color", P.water);
        else if (/building/.test(id)) map.setPaintProperty(id, "fill-color", P.build);
        else if (/park|wood|landcover|landuse|grass|ice|glacier|forest/.test(id)) map.setPaintProperty(id, "fill-color", P.green);
        else map.setPaintProperty(id, "fill-color", P.land);
      } else if (l.type === "line") {
        if (/water/.test(id)) map.setPaintProperty(id, "line-color", P.waterLine);
        else if (/boundary|admin/.test(id)) map.setPaintProperty(id, "line-color", P.admin);
        else if (/rail/.test(id)) map.setPaintProperty(id, "line-color", P.rail);
        else if (/casing/.test(id)) map.setPaintProperty(id, "line-color", P.casing);
        else map.setPaintProperty(id, "line-color", P.road);
      } else if (l.type === "symbol") {
        if (HIDE_SYMBOLS.test(id)) {
          map.setLayoutProperty(id, "visibility", "none");
          continue;
        }
        if (map.getLayoutProperty(id, "text-field") !== undefined) map.setLayoutProperty(id, "text-field", ["get", "name"]);
        map.setPaintProperty(id, "text-color", /city|capital|state|country/.test(id) ? P.city : P.text);
        map.setPaintProperty(id, "text-halo-color", P.bg);
        map.setPaintProperty(id, "text-halo-width", 1.4);
      }
    } catch {
      // stratul nu are proprietatea: rămâne cum e
    }
  }
}

function routesGeoJSON(routes: MapRoute[]) {
  const features = routes.flatMap((r) =>
    r.path.slice(0, -1).map((p, i) => ({
      type: "Feature" as const,
      properties: { crew: r.crewId, ret: i === r.path.length - 2 },
      geometry: { type: "LineString" as const, coordinates: arc(p, r.path[i + 1]) },
    })),
  );
  return { type: "FeatureCollection" as const, features };
}

function labelHtml(item: MapItem): string {
  const sub = item.sub ? `<span class="s${item.attention ? " att" : ""}">${item.sub}</span>` : "";
  return `<div class="lab"><span class="t">${item.title}</span>${sub}</div>`;
}

export function PlanMap({
  items,
  routes,
  depots,
  bounds,
  selectedId,
  onSelect,
  theme = "light",
  className,
}: {
  items: MapItem[];
  routes: MapRoute[];
  depots: MapDepot[];
  bounds: Bounds;
  selectedId: string | null;
  onSelect: (id: string) => void;
  theme?: "light" | "dark";
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const markersRef = useRef(new Map<string, { marker: MLMarker; el: HTMLDivElement; item: MapItem }>());
  const depotMarkersRef = useRef<MLMarker[]>([]);
  const onSelectRef = useRef(onSelect);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const latest = useRef({ items, routes, depots, bounds, selectedId });

  useEffect(() => {
    onSelectRef.current = onSelect;
  });
  useEffect(() => {
    latest.current = { items, routes, depots, bounds, selectedId };
  });

  // creează harta o singură dată
  useEffect(() => {
    let cancelled = false;
    let map: MLMap | null = null;
    const markers = markersRef.current;
    (async () => {
      try {
        const maplibregl = await import("maplibre-gl");
        if (cancelled || !containerRef.current) return;
        // worker-ul servit static (vezi scripts/copy-maplibre-worker.ts)
        if (maplibregl.getWorkerUrl() !== WORKER_URL) maplibregl.setWorkerUrl(WORKER_URL);
        const b = latest.current.bounds;
        const m = new maplibregl.Map({
          container: containerRef.current,
          style: STYLE_URL[theme],
          bounds: [
            [b[0], b[1]],
            [b[2], b[3]],
          ],
          fitBoundsOptions: { padding: { top: 76, bottom: 64, left: 56, right: 330 } },
          attributionControl: false,
          fadeDuration: 0,
          dragRotate: false,
          pitchWithRotate: false,
          cooperativeGestures: false,
          canvasContextAttributes: { preserveDrawingBuffer: true },
        });
        map = m;
        m.addControl(new maplibregl.AttributionControl({ compact: false }), "bottom-right");
        m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
        m.touchZoomRotate.disableRotation();
        mapRef.current = m;
        m.on("error", (e) => {
          // dalele lipsă nu opresc harta; doar stilul lipsă e o problemă reală
          if (!m.isStyleLoaded() && String(e?.error?.message ?? "").includes("style")) setFailed(true);
        });
        m.on("zoom", () => {
          containerRef.current?.toggleAttribute("data-far", m.getZoom() < 8.2);
        });
        m.on("load", () => {
          quiet(m, theme);
          m.addSource("routes", { type: "geojson", data: routesGeoJSON(latest.current.routes) });
          const bg = PALETTE[theme].bg;
          const ink = theme === "light" ? "#13202a" : "#e9eef2";
          m.addLayer({ id: "r-case", type: "line", source: "routes", paint: { "line-color": bg, "line-width": 6.5 }, layout: { "line-cap": "round", "line-join": "round" } });
          m.addLayer({ id: "r-out", type: "line", source: "routes", filter: ["!", ["get", "ret"]], paint: { "line-color": ink, "line-width": 2.4 }, layout: { "line-cap": "round" } });
          m.addLayer({ id: "r-ret", type: "line", source: "routes", filter: ["get", "ret"], paint: { "line-color": ink, "line-width": 1.8, "line-dasharray": [2, 1.6] } });
          containerRef.current?.toggleAttribute("data-far", m.getZoom() < 8.2);
          setReady(true);
        });
      } catch {
        if (!cancelled) setFailed(true);
      }
    })();
    return () => {
      cancelled = true;
      markers.forEach((m) => m.marker.remove());
      markers.clear();
      depotMarkersRef.current.forEach((m) => m.remove());
      depotMarkersRef.current = [];
      map?.remove();
      mapRef.current = null;
    };
    // tema schimbă stilul de bază: harta se recreează
  }, [theme]);

  // markerii și traseele, la fiecare plan nou
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    let cancelled = false;
    (async () => {
      const maplibregl = await import("maplibre-gl");
      if (cancelled) return;
      (map.getSource("routes") as { setData?: (d: unknown) => void } | undefined)?.setData?.(routesGeoJSON(routes));

      depotMarkersRef.current.forEach((m) => m.remove());
      depotMarkersRef.current = depots.map((d) => {
        const el = document.createElement("div");
        el.className = "mk depot";
        el.innerHTML = depotSvg() + `<div class="lab"><span class="t">${d.label}</span></div>`;
        return new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([d.lon, d.lat]).addTo(map);
      });

      markersRef.current.forEach((m) => m.marker.remove());
      markersRef.current.clear();
      for (const item of items) {
        const el = document.createElement("div");
        el.className = "mk item";
        el.dataset.pinned = item.pinned ? "1" : "0";
        el.setAttribute("role", "button");
        el.setAttribute("tabindex", "0");
        el.setAttribute("aria-label", `${item.title}${item.sub ? `, ${item.sub}` : ""}`);
        el.innerHTML = markerSvg({ source: item.source, kind: item.kind, selected: item.id === latest.current.selectedId }) + labelHtml(item);
        el.addEventListener("click", (e) => {
          e.stopPropagation();
          onSelectRef.current(item.id);
        });
        el.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            onSelectRef.current(item.id);
          }
        });
        const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([item.lon, item.lat]).addTo(map);
        markersRef.current.set(item.id, { marker, el, item });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, items, routes, depots]);

  // selecția: doar markerii afectați se redesenează
  useEffect(() => {
    if (!ready) return;
    markersRef.current.forEach(({ el, item }, id) => {
      const sel = id === selectedId;
      if (el.dataset.selected === (sel ? "1" : "0")) return;
      el.dataset.selected = sel ? "1" : "0";
      el.innerHTML = markerSvg({ source: item.source, kind: item.kind, selected: sel }) + labelHtml(item);
      el.style.zIndex = sel ? "5" : "";
    });
  }, [ready, selectedId, items]);

  // vederea (regiunea aleasă)
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    map.fitBounds(
      [
        [bounds[0], bounds[1]],
        [bounds[2], bounds[3]],
      ],
      { padding: { top: 76, bottom: 64, left: 56, right: 330 }, duration: reduce ? 0 : 800, maxZoom: 13.2 },
    );
  }, [ready, bounds]);

  return (
    <div className={className}>
      <div ref={containerRef} className="plan-map h-full w-full" aria-label="Harta planului" role="region" />
      {failed ? (
        <div className="absolute inset-0 grid place-items-center bg-canvas/80 p-8 text-center text-[15px]">
          <p>
            Harta nu s-a putut încărca (dalele OpenFreeMap nu răspund). Planul e întreg în linia de timp și în lista din
            dreapta.
          </p>
        </div>
      ) : null}
    </div>
  );
}
