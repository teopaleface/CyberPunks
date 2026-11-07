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
  /** Eticheta stă vizibilă când harta e apropiată (opririle din trasee). */
  pinned: boolean;
  /** Marker cu literă (DOM); celelalte lucrări sunt puncte într-un strat al hărții. */
  prominent: boolean;
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

export interface MapPost {
  id: string;
  lat: number;
  lon: number;
  color: string;
  title: string;
  sub: string;
  /** 0–1, mărimea cercului (pierderea relativă). */
  weight: number;
}

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

const LAYER_COLORS = {
  light: { A: "#2c6fd9", B: "#a23c9e", C: "#d99100", att: "#d4430f", panel: "#f2f3f1", ink: "#13202a", verde: "#2f8f5b", galben: "#d9a400", rosu: "#c8321e", gri: "#9aa4a9" },
  dark: { A: "#3b82f0", B: "#b84fc0", C: "#c4880a", att: "#ff6a3d", panel: "#0f1d2b", ink: "#e9eef2", verde: "#4fb57a", galben: "#e0b52a", rosu: "#ff6b5e", gri: "#5d6f81" },
} as const;

function postsGeoJSON(posts: MapPost[]) {
  return {
    type: "FeatureCollection" as const,
    features: posts.map((p) => ({
      type: "Feature" as const,
      properties: { id: p.id, color: p.color, title: p.title, sub: p.sub, weight: p.weight },
      geometry: { type: "Point" as const, coordinates: [p.lon, p.lat] },
    })),
  };
}

function itemsGeoJSON(items: MapItem[]) {
  return {
    type: "FeatureCollection" as const,
    features: items
      .filter((i) => !i.prominent)
      .map((i) => ({
        type: "Feature" as const,
        properties: { id: i.id, source: i.source, kind: i.kind, title: i.title, sub: i.sub ?? "" },
        geometry: { type: "Point" as const, coordinates: [i.lon, i.lat] },
      })),
  };
}

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

/** Textele din date intră în HTML-ul markerilor și al popup-urilor: le escapăm. */
export function esc(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c] as string);
}

function labelHtml(item: MapItem): string {
  const sub = item.sub ? `<span class="s${item.attention ? " att" : ""}">${esc(item.sub)}</span>` : "";
  return `<div class="lab"><span class="t">${esc(item.title)}</span>${sub}</div>`;
}

export function PlanMap({
  items,
  routes,
  depots,
  bounds,
  selectedId,
  onSelect,
  posts = [],
  mode = "items",
  onPostClick,
  theme = "light",
  className,
}: {
  items: MapItem[];
  routes: MapRoute[];
  depots: MapDepot[];
  bounds: Bounds;
  selectedId: string | null;
  onSelect: (id: string) => void;
  posts?: MapPost[];
  mode?: "items" | "posts";
  onPostClick?: (id: string) => void;
  theme?: "light" | "dark";
  className?: string;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MLMap | null>(null);
  const markersRef = useRef(new Map<string, { marker: MLMarker; el: HTMLDivElement; item: MapItem }>());
  const depotMarkersRef = useRef<MLMarker[]>([]);
  const onSelectRef = useRef(onSelect);
  const onPostRef = useRef(onPostClick);
  const [ready, setReady] = useState(false);
  const [failed, setFailed] = useState(false);
  const latest = useRef({ items, routes, depots, bounds, selectedId, posts, mode });

  useEffect(() => {
    onSelectRef.current = onSelect;
    onPostRef.current = onPostClick;
  });
  useEffect(() => {
    latest.current = { items, routes, depots, bounds, selectedId, posts, mode };
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
        m.on("load", () => {
          quiet(m, theme);
          m.addSource("routes", { type: "geojson", data: routesGeoJSON(latest.current.routes) });
          const bg = PALETTE[theme].bg;
          const ink = theme === "light" ? "#13202a" : "#e9eef2";
          m.addLayer({ id: "r-case", type: "line", source: "routes", paint: { "line-color": bg, "line-width": 6.5 }, layout: { "line-cap": "round", "line-join": "round" } });
          m.addLayer({ id: "r-out", type: "line", source: "routes", filter: ["!", ["get", "ret"]], paint: { "line-color": ink, "line-width": 2.4 }, layout: { "line-cap": "round" } });
          m.addLayer({ id: "r-ret", type: "line", source: "routes", filter: ["get", "ret"], paint: { "line-color": ink, "line-width": 1.8, "line-dasharray": [2, 1.6] } });
          const C = LAYER_COLORS[theme];
          const srcColor = ["match", ["get", "source"], "A", C.A, "B", C.B, C.C] as unknown as string;
          m.addSource("items", { type: "geojson", data: itemsGeoJSON(latest.current.items) });
          m.addLayer({
            id: "items-quiet",
            type: "circle",
            source: "items",
            filter: ["!=", ["get", "kind"], "human"],
            paint: {
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 2.2, 9, 3.4, 12, 5, 14, 6.5],
              "circle-color": ["case", ["==", ["get", "kind"], "pending"], C.panel, srcColor] as unknown as string,
              "circle-stroke-color": ["case", ["==", ["get", "kind"], "pending"], srcColor, C.panel] as unknown as string,
              "circle-stroke-width": ["case", ["==", ["get", "kind"], "pending"], 1.6, 1] as unknown as number,
              "circle-opacity": 0.92,
            },
          });
          m.addLayer({
            id: "items-human",
            type: "circle",
            source: "items",
            filter: ["==", ["get", "kind"], "human"],
            paint: {
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, 3.4, 9, 4.6, 12, 6.5, 14, 8],
              "circle-color": srcColor,
              "circle-stroke-color": C.att,
              "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 6, 1.6, 12, 2.6] as unknown as number,
            },
          });
          m.addSource("posts", { type: "geojson", data: postsGeoJSON(latest.current.posts) });
          m.addLayer({
            id: "posts",
            type: "circle",
            source: "posts",
            layout: { visibility: latest.current.mode === "posts" ? "visible" : "none" },
            paint: {
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 6, ["+", 3, ["*", 4, ["get", "weight"]]], 11, ["+", 6, ["*", 9, ["get", "weight"]]], 14, ["+", 9, ["*", 12, ["get", "weight"]]]] as unknown as number,
              "circle-color": ["match", ["get", "color"], "verde", C.verde, "galben", C.galben, "roșu", C.rosu, C.gri] as unknown as string,
              "circle-stroke-color": C.panel,
              "circle-stroke-width": 1.4,
              "circle-opacity": 0.9,
            },
          });
          const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 10, className: "plan-pop", maxWidth: "320px" });
          m.on("mouseenter", "posts", (e) => {
            m.getCanvas().style.cursor = "pointer";
            const f = e.features?.[0];
            if (!f) return;
            const pr = f.properties as { title: string; sub: string };
            popup
              .setLngLat((f.geometry as unknown as { coordinates: [number, number] }).coordinates)
              .setHTML(`<span class="t">${esc(pr.title)}</span><span class="s">${esc(pr.sub)}</span>`)
              .addTo(m);
          });
          m.on("mouseleave", "posts", () => {
            m.getCanvas().style.cursor = "";
            popup.remove();
          });
          m.on("click", "posts", (e) => {
            const id = e.features?.[0]?.properties?.id;
            if (typeof id === "string") onPostRef.current?.(id);
          });
          for (const layer of ["items-quiet", "items-human"]) {
            m.on("mouseenter", layer, (e) => {
              m.getCanvas().style.cursor = "pointer";
              const f = e.features?.[0];
              if (!f) return;
              const pr = f.properties as { title: string; sub: string; kind: string };
              popup
                .setLngLat((f.geometry as unknown as { coordinates: [number, number] }).coordinates)
                .setHTML(`<span class="t">${esc(pr.title)}</span>${pr.sub ? `<span class="s${pr.kind === "human" ? " att" : ""}">${esc(pr.sub)}</span>` : ""}`)
                .addTo(m);
            });
            m.on("mouseleave", layer, () => {
              m.getCanvas().style.cursor = "";
              popup.remove();
            });
            m.on("click", layer, (e) => {
              const id = e.features?.[0]?.properties?.id;
              if (typeof id === "string") onSelectRef.current(id);
            });
          }
          const zoomAttrs = () => {
            const z = m.getZoom();
            containerRef.current?.toggleAttribute("data-far", z < 8.2);
            containerRef.current?.toggleAttribute("data-near", z >= 11.4);
          };
          m.on("zoom", zoomAttrs);
          zoomAttrs();
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
      (map.getSource("items") as { setData?: (d: unknown) => void } | undefined)?.setData?.(itemsGeoJSON(items));

      depotMarkersRef.current.forEach((m) => m.remove());
      depotMarkersRef.current = depots.map((d) => {
        const el = document.createElement("div");
        el.className = "mk depot";
        el.innerHTML = depotSvg() + `<div class="lab"><span class="t">${esc(d.label)}</span></div>`;
        return new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([d.lon, d.lat]).addTo(map);
      });

      markersRef.current.forEach((m) => m.marker.remove());
      markersRef.current.clear();
      const sel = latest.current.selectedId;
      for (const item of items) {
        if (!item.prominent && item.id !== sel) continue;
        const el = document.createElement("div");
        el.className = "mk item";
        el.dataset.pinned = item.pinned ? "1" : "0";
        el.setAttribute("role", "button");
        el.setAttribute("tabindex", "0");
        el.setAttribute("aria-label", `${item.title}${item.sub ? `, ${item.sub}` : ""}`); // atributul nu interpretează HTML
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

  // selecția: doar markerii afectați se redesenează; lucrarea selectată primește marker cu literă
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    let cancelled = false;
    const selItem = items.find((i) => i.id === selectedId);
    // markerii temporari ai selecțiilor vechi (lucrări fără traseu) dispar
    markersRef.current.forEach(({ marker, item }, id) => {
      if (!item.prominent && id !== selectedId) {
        marker.remove();
        markersRef.current.delete(id);
      }
    });
    if (selItem && !markersRef.current.has(selItem.id)) {
      (async () => {
        const maplibregl = await import("maplibre-gl");
        if (cancelled) return;
        const el = document.createElement("div");
        el.className = "mk item";
        el.dataset.pinned = "0";
        el.dataset.selected = "1";
        el.innerHTML = markerSvg({ source: selItem.source, kind: selItem.kind, selected: true }) + labelHtml(selItem);
        el.style.zIndex = "5";
        const marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([selItem.lon, selItem.lat]).addTo(map);
        markersRef.current.set(selItem.id, { marker, el, item: selItem });
      })();
    }
    markersRef.current.forEach(({ el, item }, id) => {
      const sel = id === selectedId;
      if (el.dataset.selected === (sel ? "1" : "0")) return;
      el.dataset.selected = sel ? "1" : "0";
      el.innerHTML = markerSvg({ source: item.source, kind: item.kind, selected: sel }) + labelHtml(item);
      el.style.zIndex = sel ? "5" : "";
    });
    return () => {
      cancelled = true;
    };
  }, [ready, selectedId, items]);

  // modul hărții: lucrări sau posturi
  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    (map.getSource("posts") as { setData?: (d: unknown) => void } | undefined)?.setData?.(postsGeoJSON(posts));
    const showPosts = mode === "posts";
    for (const id of ["items-quiet", "items-human"]) if (map.getLayer(id)) map.setLayoutProperty(id, "visibility", showPosts ? "none" : "visible");
    if (map.getLayer("posts")) map.setLayoutProperty("posts", "visibility", showPosts ? "visible" : "none");
    containerRef.current?.toggleAttribute("data-posts", showPosts);
  }, [ready, mode, posts]);

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
