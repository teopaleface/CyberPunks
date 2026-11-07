"use client";

import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, useTransition } from "react";
import { cn } from "cn";
import type { WorkItem } from "@/lib/contracts";
import { DECISION_LABEL_RO } from "@/lib/data/labels";
import type { PostSummary } from "@/lib/data/types";
import { fmtDec, fmtInt, hhmm, minutesOfDay } from "@/lib/format";
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
    .replace(/^Bază operativă\s*/i, "Baza ")
    .replace(/\s*\(simulată\)/i, "")
    .replace(/^Baza București /, "Baza ");
}

export interface PostsInfo {
  posts: PostSummary[];
  derived: boolean;
  lossCostNote: string | null;
}

export function PlanScreen({
  data,
  geo,
  initialSelected,
  postsInfo,
  approval,
  theme = "light",
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
        const start = minutesOfDay(s.eta);
        m.set(s.work_item_id, { crewId: r.crew_id, seq: s.seq, start, end: start + s.duration_min });
      }
    }
    return m;
  }, [data.routes]);

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

  const bounds: Bounds = useMemo(() => {
    if (region === ALL) return RE_BOUNDS;
    return data.regions.find((r) => r.id === region)?.bounds ?? RE_BOUNDS;
  }, [region, data.regions]);

  const mapItems: MapItem[] = useMemo(
    () =>
      data.items.map((w) => {
        const d = data.decisions[w.work_item_id];
        const kind = markerKind(d?.decision);
        const stop = stopInfo.get(w.work_item_id);
        let sub: string | undefined;
        if (stop) sub = `${stop.crewId}, ${hhmm(stop.start)}`;
        else if (d) sub = DECISION_LABEL_RO[d.decision];
        else sub = "fără decizie";
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
      if (p.loss_lei_month != null) parts.push(`${fmtInt(p.loss_lei_month)} lei pe lună pierduți${p.derived ? " (estimat din A)" : ""}`);
      if (p.meters_flagged) parts.push(`${p.meters_flagged} ${p.meters_flagged === 1 ? "contor semnalat" : "contoare semnalate"}`);
      if (p.voltage_p90_pu != null) parts.push(`tensiune P90 ${fmtDec(p.voltage_p90_pu, 3).replace(/0$/, "")} pu`);
      if (p.diagnosis) parts.push(p.diagnosis);
      return {
        id: p.post_id,
        lat: p.lat,
        lon: p.lon,
        color: p.color ?? "necunoscut",
        title: p.label && p.label !== p.post_id ? `${p.post_id}, ${p.label.replace(`${p.post_id}, `, "")}` : p.post_id,
        sub: parts.join("; ") || "fără semnale",
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
  const [, startDetail] = useTransition();
  const selectedBase = selected ? itemsById[selected] : undefined;
  const needsDetail = Boolean(selected && selectedBase && isSlim(selectedBase) && !details[selected]);
  useEffect(() => {
    if (!needsDetail || !selected) return;
    let cancelled = false;
    startDetail(async () => {
      const r = await loadWorkItemDetail(selected, data.scenario);
      if (!cancelled && r.ok) setDetails((d) => ({ ...d, [selected]: r.workItem }));
    });
    return () => {
      cancelled = true;
    };
  }, [needsDetail, selected, data.scenario]);
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
          />
          <div className="absolute top-4 left-4 flex flex-col items-start gap-2">
            <RegionChips regions={data.regions} region={region} onChange={setRegion} totalItems={data.items.length} />
            {mapPosts.length ? <ModeSwitch mode={mode} onChange={setMode} posts={mapPosts.length} /> : null}
          </div>
          {scene ? null : mode === "posts" ? (
            <PostsLegend derived={postsInfo?.derived ?? false} note={postsInfo?.lossCostNote ?? null} />
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
        <aside className="flex min-h-0 flex-col bg-panel" aria-label="Decizii care cer atenție">
          <div className={cn(spotlight === "queue" && "spot spot-att")}>
            <QueuePanel queue={queue} itemsById={itemsById} scenario={data.scenario} onSelect={select} recovered={data.recovered} />
          </div>
          <AlertsPanel alerts={data.alerts} onSelect={select} />
          <WorkItemPeek
            highlight={spotlight === "peek"}
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
  const chips = [{ id: ALL, label: "Toată zona", count: totalItems }, ...regions.map((r) => ({ id: r.id, label: r.label, count: r.itemCount }))];
  return (
    <div role="group" aria-label="Zona arătată pe hartă" className="flex overflow-hidden rounded-[4px] border border-rule bg-panel text-[14.5px]">
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
    [markerSvg({ source: "A", r: 9 }), "Contoare"],
    [markerSvg({ source: "B", r: 9 }), "Furtună"],
    [markerSvg({ source: "C", r: 9 }), "Tensiune"],
    [markerSvg({ source: "A", kind: "human", r: 9 }), "Decide un om"],
    [markerSvg({ source: "C", kind: "remote", r: 9 }), "Fără echipă"],
    [markerSvg({ source: "B", kind: "pending", r: 9 }), "Amânată"],
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
        ordinea opririlor, nu drumul
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
  const label = region === ALL ? "Toată zona Rețele Electrice" : `Harta arată: ${data.regions.find((r) => r.id === region)?.label ?? region}`;
  const items = Object.values(itemsById);
  return (
    <div className="absolute top-4 right-4 w-[292px] rounded-[4px] border border-rule bg-panel/95 max-[1500px]:hidden">
      <div className="flex items-baseline justify-between border-b border-rule px-3 pt-2 pb-1.5 text-[14px]">
        <b className="font-[600]">Zona Rețele Electrice</b>
        <span className="text-muted-foreground">{label.replace("Harta arată: ", "")}</span>
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
    <div role="group" aria-label="Ce arată harta" className="flex overflow-hidden rounded-[4px] border border-rule bg-panel text-[14px]">
      {btn("items", "Lucrările de mâine")}
      {btn("posts", `Posturile (${posts})`)}
    </div>
  );
}

function PostsLegend({ derived, note }: { derived: boolean; note: string | null }) {
  const dot = (color: string) => <span className="inline-block size-3.5 rounded-full border border-panel" style={{ background: color }} aria-hidden="true" />;
  return (
    <div className="absolute bottom-7 left-4 max-w-[760px] rounded-[4px] border border-rule bg-panel/95 px-3 py-2 text-[13.5px]">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
        <b className="font-[600]">Lei pierduți pe lună</b>
        <span className="flex items-center gap-1.5">{dot("#2f8f5b")}sub 150</span>
        <span className="flex items-center gap-1.5">{dot("#d9a400")}150–600</span>
        <span className="flex items-center gap-1.5">{dot("#c8321e")}peste 600</span>
        <span className="flex items-center gap-1.5">{dot("#9aa4a9")}necunoscut</span>
        <span className="text-muted-foreground">cercul mai mare, pierdere mai mare; clic pe un post pentru pagina lui</span>
      </div>
      <p className="mt-1 text-[12.5px] text-muted-foreground">
        {derived
          ? "Estimat din contoarele semnalate de modelul A (kWh pe zi × scor), până vine bilanțul pe post. "
          : "Din bilanțul pe post. "}
        Simulare pe date publice, gândită pentru datele PPC.{note ? ` Prețul energiei pierdute: ${note.split(/[:;(]/)[0].trim().toLowerCase() === "proxy" ? "proxy din prețul PZU OPCOM" : note.split(";")[0]}.` : ""}
      </p>
    </div>
  );
}
