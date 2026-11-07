"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { cn } from "cn";
import type { WorkItem } from "@/lib/contracts";
import { DECISION_LABEL_RO } from "@/lib/data/labels";
import type { PostSummary } from "@/lib/data/types";
import { fmtDec, fmtInt, hhmm, minutesOfPlanDay, plural } from "@/lib/format";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { loadWorkItemDetail } from "@/lib/data/actions";
import { RE_BOUNDS, isSlim, itemTitle, type PlanScreenData } from "@/lib/plan-screen";
import type { LocatorGeo } from "@/lib/server/geo";
import { Feeders } from "./feeders";
import type { Bounds, MapItem, MapPost } from "./plan-map";
import { AlertsPanel, QueuePanel, WorkItemPeek } from "./rail";

// MapLibre e greu (~800 KB): se încarcă doar în browser, după restul ecranului.
const PlanMap = dynamic(() => import("./plan-map").then((m) => m.PlanMap), {
  ssr: false,
  loading: () => <div className="absolute inset-0 animate-pulse bg-canvas" aria-hidden="true" />,
});

const ALL = "toata_zona";

function shortDepot(label: string): string {
  return label
    .replace(/^Bază operativă\s*/i, "Depot ")
    .replace(/\s*\(simulată\)/i, "")
    .replace(/^Baza București /, "Depot ");
}

// în modul de prezentare, încadrarea lasă loc butoanelor de regiune și hărții mici (subtitrarea are banda ei)
const SCENE_MAP_PADDING = { top: 76, bottom: 64, left: 56, right: 330 };

export interface PostsInfo {
  posts: PostSummary[];
  derived: boolean;
  lossCostNote: string | null;
  /** Pragurile de culoare, în lei pe lună (config/planner.yaml). */
  thresholds: { yellow: number; red: number };
}

export function PlanScreen({
  data,
  geo,
  initialSelected,
  postsInfo,
  approval,
  theme = "dark",
  scene,
  initialRegion,
  initialMode = "items",
}: {
  initialRegion?: string | null;
  initialMode?: "items" | "posts";
  data: PlanScreenData;
  geo: LocatorGeo | null;
  initialSelected: string | null;
  postsInfo?: PostsInfo;
  approval?: { at: string; local: boolean } | null;
  theme?: "light" | "dark";
  /** Modul de prezentare comandă regiunea, selecția și ce se evidențiază. */
  scene?: { region?: string; selected?: string | null; spotlight?: "queue" | "peek" | "feeders" | "map" | null };
}) {
  const router = useRouter();
  const [mode, setModeState] = useState<"items" | "posts">(initialMode);
  const itemsById = useMemo(() => Object.fromEntries(data.items.map((w) => [w.work_item_id, w])) as Record<string, WorkItem>, [data.items]);
  const stopInfo = useMemo(() => {
    const m = new Map<string, { crewId: string; seq: number; start: number; end: number }>();
    for (const r of data.routes) {
      for (const s of r.stops) {
        const start = minutesOfPlanDay(s.eta, data.planDate);
        m.set(s.work_item_id, { crewId: r.crew_id, seq: s.seq, start, end: start + s.duration_min });
      }
    }
    return m;
  }, [data.routes, data.planDate]);

  const [selected, setSelected] = useState<string | null>(initialSelected);
  const [region, setRegionState] = useState<string>(() => {
    if (initialRegion && (initialRegion === ALL || data.regions.some((r) => r.id === initialRegion))) return initialRegion;
    const r = initialSelected ? data.regionOf[initialSelected] : null;
    return r ?? data.defaultRegion;
  });
  // starea hărții stă și în adresă (?zona=, ?harta=posturi), ca o vedere să poată fi trimisă mai departe
  const syncUrl = useCallback((key: string, value: string | null) => {
    if (scene) return; // în modul de prezentare adresa ține scena
    const url = new URL(window.location.href);
    if (value) url.searchParams.set(key, value);
    else url.searchParams.delete(key);
    window.history.replaceState(window.history.state, "", url);
  }, [scene]);
  const setRegion = useCallback(
    (next: string) => {
      setRegionState(next);
      syncUrl("zona", next);
    },
    [syncUrl],
  );
  const setMode = useCallback(
    (m: "items" | "posts") => {
      setModeState(m);
      syncUrl("harta", m === "posts" ? "posturi" : null);
    },
    [syncUrl],
  );

  // scenele din modul de prezentare (ajustare de stare în timpul randării, fără efecte)
  const [prevScene, setPrevScene] = useState(scene);
  if (scene !== prevScene) {
    setPrevScene(scene);
    if (scene?.region) setRegionState(scene.region);
    if (scene?.selected !== undefined) setSelected(scene.selected);
  }
  const spotlight = scene?.spotlight ?? null;

  const select = useCallback(
    (id: string) => {
      setSelected(id);
      const r = data.regionOf[id];
      if (region !== ALL && r && r !== region) setRegion(r);
      if (!scene) {
        const url = new URL(window.location.href);
        url.searchParams.set("lucrare", id);
        window.history.replaceState(window.history.state, "", url);
      }
    },
    [data.regionOf, region, setRegion, scene],
  );

  // în prezentare, încadrarea cuprinde și lucrarea scenei (de exemplu un caz „Nu sunt sigur” din afara traseelor)
  const sceneItem = scene?.selected ? itemsById[scene.selected] : undefined;
  const bounds: Bounds = useMemo(() => {
    const base = region === ALL ? RE_BOUNDS : (data.regions.find((r) => r.id === region)?.bounds ?? RE_BOUNDS);
    if (!sceneItem || region === ALL) return base;
    const { lon, lat } = sceneItem.location;
    const m = 0.08; // ~8 km de margine în jurul lucrării
    return [Math.min(base[0], lon - m), Math.min(base[1], lat - m), Math.max(base[2], lon + m), Math.max(base[3], lat + m)];
  }, [region, data.regions, sceneItem]);

  const mapItems: MapItem[] = useMemo(
    () =>
      data.items.map((w) => {
        const d = data.decisions[w.work_item_id];
        const kind = markerKind(d?.decision);
        const stop = stopInfo.get(w.work_item_id);
        let sub: string | undefined;
        if (stop) sub = `${stop.crewId}, ${hhmm(stop.start)}`;
        else if (d) sub = DECISION_LABEL_RO[d.decision];
        else sub = "No decision";
        return {
          id: w.work_item_id,
          source: w.source,
          lat: w.location.lat,
          lon: w.location.lon,
          kind,
          title: w.asset_type === "meter" ? w.asset_id : itemTitle(w),
          sub,
          pinned: Boolean(stop),
          prominent: Boolean(stop),
          attention: kind === "human",
        };
      }),
    [data.items, data.decisions, stopInfo],
  );
  const mapRoutes = useMemo(() => data.routes.map((r) => ({ crewId: r.crew_id, path: r.path })), [data.routes]);
  const mapDepots = useMemo(
    () => data.depots.map((d) => ({ id: d.depot_id, label: shortDepot(d.label_ro), lat: d.lat, lon: d.lon })),
    [data.depots],
  );

  const mapPosts: MapPost[] = useMemo(() => {
    const list = postsInfo?.posts ?? [];
    const maxLoss = Math.max(1, ...list.map((p) => p.loss_lei_month ?? 0));
    return list.map((p) => {
      const parts: string[] = [];
      if (p.loss_lei_month != null) parts.push(`${fmtInt(p.loss_lei_month)} RON lost per month${p.derived ? " (estimated from model A)" : ""}`);
      if (p.meters_flagged) parts.push(plural(p.meters_flagged, "flagged meter", "flagged meters"));
      if (p.voltage_p90_pu != null) parts.push(`P90 voltage ${fmtDec(p.voltage_p90_pu, 3).replace(/0$/, "")} pu`);
      if (p.diagnosis) parts.push(p.diagnosis);
      return {
        id: p.post_id,
        lat: p.lat,
        lon: p.lon,
        color: p.color ?? "necunoscut",
        title: p.label && p.label !== p.post_id ? `${p.post_id}, ${p.label.replace(`${p.post_id}, `, "")}` : p.post_id,
        sub: parts.join("; ") || "No signals",
        weight: Math.sqrt((p.loss_lei_month ?? 0) / maxLoss),
      };
    });
  }, [postsInfo]);

  const queue = useMemo(
    () => Object.values(data.decisions).filter((d) => d.decision === "human_review"),
    [data.decisions],
  );
  // detaliile lucrării selectate (factori, cazuri similare) se încarcă la cerere și rămân în cache
  const [details, setDetails] = useState<Record<string, WorkItem>>({});
  const [detailErrors, setDetailErrors] = useState<Record<string, string>>({});
  const [retry, setRetry] = useState(0);
  const [, startDetail] = useTransition();
  const selectedBase = selected ? itemsById[selected] : undefined;
  const needsDetail = Boolean(selected && selectedBase && isSlim(selectedBase) && !details[selected] && !detailErrors[selected]);
  useEffect(() => {
    if (!needsDetail || !selected) return;
    let cancelled = false;
    startDetail(async () => {
      try {
        const r = await loadWorkItemDetail(selected, data.scenario);
        if (cancelled) return;
        if (r.ok) setDetails((d) => ({ ...d, [selected]: r.workItem }));
        else setDetailErrors((e) => ({ ...e, [selected]: r.error }));
      } catch {
        if (!cancelled) setDetailErrors((e) => ({ ...e, [selected]: "Could not load details. The server did not respond." }));
      }
    });
    return () => {
      cancelled = true;
    };
  }, [needsDetail, selected, data.scenario, retry]);
  const retryDetail = useCallback((id: string) => {
    setDetailErrors((e) => {
      const next = { ...e };
      delete next[id];
      return next;
    });
    setRetry((n) => n + 1);
  }, []);
  const selItem = selected ? (details[selected] ?? itemsById[selected] ?? null) : null;
  const selStop = selected ? stopInfo.get(selected) : undefined;

  return (
    <>
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_clamp(460px,38vw,732px)]">
        <div className={cn("relative min-h-0 overflow-hidden border-r border-rule", spotlight === "map" && "spot")}>
          <PlanMap
            className="absolute inset-0"
            items={mapItems}
            routes={mapRoutes}
            depots={mapDepots}
            bounds={bounds}
            selectedId={selected}
            onSelect={select}
            posts={mapPosts}
            mode={mode}
            onPostClick={(id) => router.push(`/posturi/${encodeURIComponent(id)}`)}
            theme={theme}
            padding={scene ? SCENE_MAP_PADDING : undefined}
          />
          <div className="absolute top-4 left-4 flex flex-col items-start gap-2">
            <RegionChips regions={data.regions} region={region} onChange={setRegion} totalItems={data.items.length} />
            {mapPosts.length ? <ModeSwitch mode={mode} onChange={setMode} posts={mapPosts.length} /> : null}
          </div>
          {scene ? null : mode === "posts" ? (
            <PostsLegend derived={postsInfo?.derived ?? false} note={postsInfo?.lossCostNote ?? null} thresholds={postsInfo?.thresholds ?? { yellow: 200, red: 600 }} />
          ) : (
            <Legend />
          )}
          {geo ? (
            <Locator
              geo={geo}
              data={data}
              region={region}
              bounds={bounds}
              onRegion={setRegion}
              itemsById={itemsById}
            />
          ) : null}
        </div>
        <aside className="flex min-h-0 flex-col bg-panel" aria-label="Decisions needing attention">
          <div className={cn(spotlight === "queue" && "spot spot-att")}>
            <QueuePanel queue={queue} itemsById={itemsById} scenario={data.scenario} onSelect={select} recovered={data.recovered} />
          </div>
          <AlertsPanel alerts={data.alerts} decisions={data.decisions} onSelect={select} />
          <WorkItemPeek
            highlight={spotlight === "peek"}
            detailError={selected ? (detailErrors[selected] ?? null) : null}
            onRetry={selected ? () => retryDetail(selected) : undefined}
            w={selItem}
            decision={selected ? (data.decisions[selected] ?? null) : null}
            crewInfo={selStop ? { crewId: selStop.crewId, seq: selStop.seq, start: hhmm(selStop.start), end: hhmm(selStop.end) } : null}
            scenario={data.scenario}
          />
        </aside>
      </div>
      <Feeders
        highlight={spotlight === "feeders"}
        routes={data.routes}
        itemsById={itemsById}
        decisions={data.decisions}
        depots={data.depots}
        crews={data.crews}
        shift={data.shift}
        quarantine={data.quarantine}
        selectedId={selected}
        onSelect={select}
        scenario={data.scenario}
        planId={data.planId}
        planDate={data.planDate}
        approval={approval ?? null}
      />
    </>
  );
}

function RegionChips({
  regions,
  region,
  onChange,
  totalItems,
}: {
  regions: PlanScreenData["regions"];
  region: string;
  onChange: (id: string) => void;
  totalItems: number;
}) {
  const chips = [{ id: ALL, label: "All areas", count: totalItems }, ...regions.map((r) => ({ id: r.id, label: r.label, count: r.itemCount }))];
  return (
    <div role="group" aria-label="Area shown on the map" className="flex overflow-hidden rounded-[4px] border border-rule bg-panel text-[14.5px]">
      {chips.map((c) => (
        <button
          key={c.id}
          type="button"
          aria-pressed={region === c.id}
          onClick={() => onChange(c.id)}
          className={cn(
            "flex h-10 items-center gap-2 border-l border-rule px-3.5 whitespace-nowrap transition-colors duration-150 first:border-l-0",
            region === c.id ? "bg-ink font-[600] text-panel" : "font-[500] text-ink hover:bg-muted",
          )}
        >
          {c.label}
          <span className={cn("tabular-nums", region === c.id ? "text-panel/75" : "text-muted-foreground")}>{c.count}</span>
        </button>
      ))}
    </div>
  );
}

function Legend() {
  const sm = (html: string) => (
    <span
      className="block size-[22px] shrink-0 [&>svg]:block"
      dangerouslySetInnerHTML={{ __html: html.replace('width="36" height="36"', 'width="22" height="22"').replace('viewBox="0 0 36 36"', 'viewBox="5 5 26 26"') }}
    />
  );
  const items: [string, string][] = [
    [markerSvg({ source: "A", r: 9 }), "Meters"],
    [markerSvg({ source: "B", r: 9 }), "Storm"],
    [markerSvg({ source: "C", r: 9 }), "Voltage"],
    [markerSvg({ source: "A", kind: "human", r: 9 }), "Human review"],
    [markerSvg({ source: "C", kind: "remote", r: 9 }), "No crew"],
    [markerSvg({ source: "B", kind: "pending", r: 9 }), "Deferred"],
  ];
  return (
    <div className="absolute bottom-7 left-4 flex items-center gap-4 rounded-[4px] border border-rule bg-panel/95 px-3 py-1.5 text-[13.5px] max-[1500px]:gap-2.5 max-[1500px]:text-[13px]">
      {items.map(([html, label]) => (
        <span key={label} className="flex items-center gap-1.5 whitespace-nowrap">
          {sm(html)}
          {label}
        </span>
      ))}
      <span className="flex items-center gap-1.5 whitespace-nowrap text-muted-foreground max-[1500px]:hidden">
        <svg width="22" height="10" viewBox="0 0 26 12" aria-hidden="true">
          <path d="M1 9 Q13 0 25 9" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth="2.2" />
        </svg>

        Stop order, not road directions
      </span>
    </div>
  );
}

function Locator({
  geo,
  data,
  region,
  bounds,
  onRegion,
  itemsById,
}: {
  geo: LocatorGeo;
  data: PlanScreenData;
  region: string;
  bounds: Bounds;
  onRegion: (id: string) => void;
  itemsById: Record<string, WorkItem>;
}) {
  const [w, s, e, n] = geo.bounds;
  const px = (lon: number) => ((lon - w) / (e - w)) * geo.width;
  const py = (lat: number) => ((n - lat) / (n - s)) * geo.height;
  const label = region === ALL ? "All Rețele Electrice areas" : `Map shows: ${data.regions.find((r) => r.id === region)?.label ?? region}`;
  const items = Object.values(itemsById);
  return (
    <div className="absolute top-4 right-4 w-[292px] rounded-[4px] border border-rule bg-panel/95 max-[1500px]:hidden">
      <div className="flex items-baseline justify-between border-b border-rule px-3 pt-2 pb-1.5 text-[14px]">
        <b className="font-[600]">Rețele Electrice area</b>
        <span className="text-muted-foreground">{label.replace("Map shows: ", "")}</span>
      </div>
      <svg width="100%" viewBox={`-6 -6 ${geo.width + 12} ${geo.height + 12}`} role="group" aria-label={label} className="block">
        {geo.counties.map((c) => (
          <path
            key={c.name}
            d={c.d}
            onClick={c.region ? () => onRegion(c.region!) : undefined}
            className={c.region ? "cursor-pointer" : undefined}
            style={{
              fill: c.region ? (c.region === region ? "color-mix(in oklab, var(--ink) 16%, var(--panel))" : "var(--muted)") : "var(--panel)",
              stroke: "var(--rule)",
              strokeWidth: 0.6,
            }}
          >
            <title>{c.region ? `${c.name}, ${data.regions.find((r) => r.id === c.region)?.label ?? ""}` : c.name}</title>
          </path>
        ))}
        {region !== ALL ? (
          <rect
            x={px(bounds[0])}
            y={py(bounds[3])}
            width={Math.max(3, px(bounds[2]) - px(bounds[0]))}
            height={Math.max(3, py(bounds[1]) - py(bounds[3]))}
            fill="none"
            style={{ stroke: "var(--ink)" }}
            strokeWidth={1.4}
          />
        ) : null}
        {data.depots.map((d) => (
          <rect key={d.depot_id} x={px(d.lon) - 2} y={py(d.lat) - 5} width={4} height={10} style={{ fill: "var(--ink)" }} />
        ))}
        {items.map((it) => (
          <circle
            key={it.work_item_id}
            cx={px(it.location.lon)}
            cy={py(it.location.lat)}
            r={it.source === "B" ? 4.5 : 3}
            style={{ fill: `var(--src-${it.source.toLowerCase()})`, stroke: "var(--panel)" }}
            strokeWidth={1}
          />
        ))}
      </svg>
      <div className="flex gap-3 border-t border-rule px-3 py-1.5 text-[13px] text-muted-foreground">
        {data.regions.map((r) => (
          <button key={r.id} type="button" onClick={() => onRegion(r.id)} className={cn("underline-offset-4 hover:text-ink hover:underline", r.id === region && "font-[600] text-ink")}>
            {r.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function ModeSwitch({ mode, onChange, posts }: { mode: "items" | "posts"; onChange: (m: "items" | "posts") => void; posts: number }) {
  const btn = (m: "items" | "posts", label: string) => (
    <button
      type="button"
      aria-pressed={mode === m}
      onClick={() => onChange(m)}
      className={cn(
        "flex h-9 items-center gap-2 border-l border-rule px-3 whitespace-nowrap transition-colors duration-150 first:border-l-0",
        mode === m ? "bg-ink font-[600] text-panel" : "font-[500] text-ink hover:bg-muted",
      )}
    >
      {label}
    </button>
  );
  return (
    <div role="group" aria-label="Map content" className="flex overflow-hidden rounded-[4px] border border-rule bg-panel text-[14px]">
      {btn("items", "Tomorrow's work items")}
      {btn("posts", `Substations (${fmtInt(posts)})`)}
    </div>
  );
}

function PostsLegend({ derived, note, thresholds }: { derived: boolean; note: string | null; thresholds: { yellow: number; red: number } }) {
  const dot = (color: string) => <span className="inline-block size-3.5 rounded-full border border-panel" style={{ background: color }} aria-hidden="true" />;
  return (
    <div className="absolute bottom-7 left-4 max-w-[760px] rounded-[4px] border border-rule bg-panel/95 px-3 py-2 text-[13.5px]">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <b className="font-[600]">RON lost per month</b>
        <span className="flex items-center gap-1.5">{dot("#2f8f5b")}below {fmtInt(thresholds.yellow)}</span>
        <span className="flex items-center gap-1.5">
          {dot("#d9a400")}
          {fmtInt(thresholds.yellow)}–{fmtInt(thresholds.red)}
        </span>
        <span className="flex items-center gap-1.5">{dot("#c8321e")}above {fmtInt(thresholds.red)}</span>
        <span className="flex items-center gap-1.5">{dot("#9aa4a9")}necunoscut</span>
        <span className="text-muted-foreground">Larger circles mean greater losses. Select a substation for details.</span>
        <Link href="/posturi" className="font-[560] underline decoration-rule underline-offset-4 hover:decoration-ink">

          Substation list
        </Link>
      </div>
      <p className="mt-1 text-[12.5px] text-muted-foreground">
        {derived
          ? "Estimated from meters flagged by model A (daily kWh × score), pending the substation energy balance. "
          : "From the substation energy balance. "}

        Simulation using public data, designed for PPC data.{note ? ` Lost energy price: ${note.split(/[:;(]/)[0].trim().toLowerCase() === "proxy" ? "proxy from the OPCOM day-ahead price" : note.split(";")[0]}.` : ""}
      </p>
    </div>
  );
}
