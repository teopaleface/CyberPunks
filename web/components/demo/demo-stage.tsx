"use client";

import { Coins, Layers, Map as MapIcon, MapPin, Route as RouteIcon, UserRound, Waypoints } from "lucide-react";
import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Wordmark } from "@/components/brand/logo";
import { Card, Dot, Gauge, Kpi, Pill, SOURCE_TONE, type Tone } from "@/components/ds";
import type { Bounds, MapItem, MapRoute } from "@/components/plan/plan-map";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { ACTION_RO, DECISION_LABEL_RO, predictionLabelRo } from "@/lib/data/labels";
import { fmtDateLong, fmtDec, fmtInt, fmtLei, fmtTime } from "@/lib/format";
import { roundPct } from "@/lib/human";
import { markerKind, markerSvg } from "@/lib/marker-svg";
import { itemPlace, itemTitle, RE_BOUNDS, type PlanScreenData } from "@/lib/plan-screen";

// MapLibre e greu: se încarcă doar în browser
const PlanMap = dynamic(() => import("@/components/plan/plan-map").then((m) => m.PlanMap), {
  ssr: false,
  loading: () => <div className="absolute inset-0 animate-pulse bg-canvas" aria-hidden="true" />,
});

const ALL = "toata_zona";
const MAP_PADDING = { top: 36, bottom: 36, left: 36, right: 36 };

interface Scene {
  title: string;
  /** Titlul mare, când diferă de „titlu.”. */
  headline?: string;
  text: string;
  /** Regiunea de pe hartă și din filtre (ALL = toată zona). */
  region: string;
  /** Lucrarea scenei: cardul din dreapta și echipa din cronologie. */
  item: string | null;
}

function shortDepot(label: string): string {
  return label.replace(/^Bază operativă\s*/i, "Baza ").replace(/\s*\(simulată\)/i, "").replace(/^Baza București /, "Baza ");
}

/**
 * Modul de prezentare pentru înregistrări: scena pe tot ecranul (cifre, hartă, lucrarea scenei, cronologia echipei),
 * fără navigare, cu scene comandate din tastatură (← →, cifrele 1–5), din adresă (?scena=2) sau automat (?auto=1).
 */
export function DemoStage({
  data,
  initialScene,
  auto,
}: {
  data: PlanScreenData;
  initialScene: number;
  auto: boolean;
}) {
  const scenes: Scene[] = useMemo(() => {
    const decisions = Object.values(data.decisions);
    const ranked = decisions.filter((d) => d.decision === "assigned" && d.rank != null).toSorted((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
    const top = ranked[0];
    const human = decisions.find((d) => d.decision === "human_review");
    const storm = decisions
      .filter((d) => d.work_item_id.startsWith("B-") && (d.decision === "assigned" || d.decision === "human_review"))
      .toSorted((a, b) => (data.regionOf[a.work_item_id] === "banat" ? -1 : 0) - (data.regionOf[b.work_item_id] === "banat" ? -1 : 0))[0];
    return [
      {
        title: "Planul de mâine",
        headline: "Planul de mâine. Unde merg echipele și de ce.",
        text: "Unde merg echipele mâine și de ce, din trei modele antrenate de noi: contoare, furtună, tensiune.",
        region: ALL,
        item: data.defaultSelected,
      },
      {
        title: "Nu sunt sigur: decide un om",
        text: "Ce nu poate decide singur, agentul trimite la dispecer, cu motivul în cuvinte simple.",
        region: ALL,
        item: human?.work_item_id ?? data.defaultSelected,
      },
      {
        title: "De ce a decis agentul așa",
        text: "Scorul, intervalul, factorii, cazul asemănător și regula, până la predicția și versiunea modelului.",
        region: (top ? data.regionOf[top.work_item_id] : null) ?? data.defaultRegion,
        item: top?.work_item_id ?? data.defaultSelected,
      },
      {
        title: "Echipa ajunge înainte de furtună",
        text: "Unde vine furtuna, echipa e trimisă din timp, înainte de fereastra de risc.",
        region: (storm ? data.regionOf[storm.work_item_id] : null) ?? data.defaultRegion,
        item: storm?.work_item_id ?? null,
      },
      {
        title: "Ziua echipelor",
        text: "Traseele devin ordine de lucru; dispecerul aprobă lista pentru mâine.",
        region: data.defaultRegion,
        item: data.defaultSelected,
      },
    ];
  }, [data]);

  const [index, setIndex] = useState(() => Math.min(Math.max(initialScene - 1, 0), 4));
  const [autoOn, setAutoOn] = useState(auto);
  const go = useCallback((i: number) => setIndex(((i % scenes.length) + scenes.length) % scenes.length), [scenes.length]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented) return;
      const el = e.target instanceof HTMLElement ? e.target : null;
      if (el && (/^(INPUT|TEXTAREA|SELECT)$/i.test(el.tagName) || el.isContentEditable)) return;
      // pe butoane și linkuri, Space și Enter le apasă pe ele; săgețile și cifrele schimbă scena
      if (el && (e.key === " " || e.key === "Enter") && (/^(BUTTON|A)$/i.test(el.tagName) || el.closest('[role="button"]'))) return;
      setAutoOn(false); // orice tastă oprește derularea automată
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        setIndex((i) => (i + 1) % scenes.length);
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        setIndex((i) => (i - 1 + scenes.length) % scenes.length);
      } else if (/^[1-9]$/.test(e.key) && Number(e.key) <= scenes.length) {
        setIndex(Number(e.key) - 1);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [scenes.length]);

  useEffect(() => {
    if (!autoOn) return;
    const t = window.setInterval(() => setIndex((i) => (i + 1) % scenes.length), 7000);
    return () => window.clearInterval(t);
  }, [autoOn, scenes.length]);

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("scena", String(index + 1));
    window.history.replaceState(window.history.state, "", url);
  }, [index]);

  const scene = scenes[index];
  const itemsById = useMemo(() => Object.fromEntries(data.items.map((w) => [w.work_item_id, w])), [data.items]);
  const item = scene.item ? (itemsById[scene.item] ?? null) : null;
  const decision = scene.item ? (data.decisions[scene.item] ?? null) : null;

  // echipa scenei: a lucrării; fără ea (decide un om), prima din regiunea scenei
  const route = useMemo(() => {
    const own = decision?.crew_id ? data.routes.find((r) => r.crew_id === decision.crew_id) : undefined;
    if (own) return own;
    const depotRegion = new Map(data.depots.map((d) => [d.depot_id, d.region ?? null]));
    const region = scene.region === ALL ? data.defaultRegion : scene.region;
    return data.routes.find((r) => depotRegion.get(r.depot_id) === region && r.stops.length > 0) ?? data.routes.find((r) => r.stops.length > 0) ?? null;
  }, [data.routes, data.depots, data.defaultRegion, decision, scene.region]);

  const bounds: Bounds = useMemo(() => {
    const base = scene.region === ALL ? RE_BOUNDS : (data.regions.find((r) => r.id === scene.region)?.bounds ?? RE_BOUNDS);
    if (!item || scene.region === ALL) return base;
    const m = 0.08;
    return [Math.min(base[0], item.location.lon - m), Math.min(base[1], item.location.lat - m), Math.max(base[2], item.location.lon + m), Math.max(base[3], item.location.lat + m)];
  }, [scene.region, data.regions, item]);

  const stopInfo = useMemo(() => {
    const m = new Map<string, { crewId: string; eta: string }>();
    for (const r of data.routes) for (const s of r.stops) m.set(s.work_item_id, { crewId: r.crew_id, eta: s.eta });
    return m;
  }, [data.routes]);
  const mapItems: MapItem[] = useMemo(
    () =>
      data.items.map((w) => {
        const d = data.decisions[w.work_item_id];
        const kind = markerKind(d?.decision);
        const stop = stopInfo.get(w.work_item_id);
        return {
          id: w.work_item_id,
          source: w.source,
          lat: w.location.lat,
          lon: w.location.lon,
          kind,
          title: w.asset_type === "meter" ? w.asset_id : itemTitle(w),
          sub: stop ? `${stop.crewId}, ${fmtTime(stop.eta)}` : d ? DECISION_LABEL_RO[d.decision] : "fără decizie",
          pinned: Boolean(stop),
          prominent: Boolean(stop),
          attention: kind === "human",
        };
      }),
    [data.items, data.decisions, stopInfo],
  );
  const mapRoutes: MapRoute[] = useMemo(() => data.routes.map((r) => ({ crewId: r.crew_id, path: r.path })), [data.routes]);
  const mapDepots = useMemo(() => data.depots.map((d) => ({ id: d.depot_id, label: shortDepot(d.label_ro), lat: d.lat, lon: d.lon })), [data.depots]);
  const noop = useCallback(() => {}, []);

  const s = data.summary;
  const human = decision?.decision === "human_review";
  const score = item?.prediction.score ?? null;
  const sm = (html: string) => (
    <span className="block size-[22px] shrink-0 [&>svg]:block" dangerouslySetInnerHTML={{ __html: html.replace('width="36" height="36"', 'width="22" height="22"').replace('viewBox="0 0 36 36"', 'viewBox="5 5 26 26"') }} />
  );
  const legend: [string, string][] = [
    [markerSvg({ source: "A", r: 9 }), "Contoare"],
    [markerSvg({ source: "B", r: 9 }), "Furtună"],
    [markerSvg({ source: "C", r: 9 }), "Tensiune"],
    [markerSvg({ source: "A", kind: "human", r: 9 }), "Decide un om"],
  ];
  const regionChips = [{ id: ALL, label: "Toate regiunile" }, ...data.regions.map((r) => ({ id: r.id, label: r.label }))];
  const planned = decision?.decision === "assigned";
  const stopOf = route?.stops ?? [];

  return (
    <div className="dark flex min-h-dvh flex-col bg-canvas text-ink [color-scheme:dark] lg:h-dvh lg:overflow-hidden">
      <header className="flex h-[60px] shrink-0 items-center gap-6 border-b border-[#152133] px-7 max-md:px-4">
        <Wordmark />
        <span className="text-[16px] text-muted-foreground max-md:hidden">Prezentare, planul pentru {fmtDateLong(data.planDate).toLowerCase()}</span>
        <span className="flex-1" />
        <span className="flex items-center gap-2 rounded-full border border-[#2a3a52] px-3 py-1 text-[14px] font-[520] max-md:hidden">
          <SyntheticGlyph /> Date sintetice pe hartă reală
        </span>
        <nav aria-label="Scenele prezentării" className="flex items-center">
          {scenes.map((sc, i) => (
            <button
              key={sc.title}
              type="button"
              onClick={() => go(i)}
              aria-current={i === index ? "step" : undefined}
              aria-label={`Scena ${i + 1}: ${sc.title}`}
              className="group grid h-9 place-items-center rounded-[4px] px-1 focus-visible:outline-2 focus-visible:outline-ring"
            >
              <span aria-hidden="true" className={"block h-2.5 rounded-full transition-[width,background-color] duration-300 " + (i === index ? "w-7 bg-ink" : "w-2.5 bg-idle group-hover:bg-ink-soft")} />
            </button>
          ))}
        </nav>
      </header>
      {/* regiunea anunțată rămâne montată */}
      <p role="status" className="sr-only">
        Scena {index + 1} din {scenes.length}: {scene.title}. {scene.text}
      </p>

      <div className="mx-auto flex min-h-0 w-full max-w-[1760px] flex-1 flex-col gap-3 px-6 pt-4 pb-4 max-md:px-4">
        <div className="grid grid-cols-6 gap-4 max-xl:grid-cols-3 max-md:grid-cols-2">
          <Kpi icon={Layers} tone="blue" value={fmtInt(s.items_in)} label="primite" />
          <Kpi icon={Waypoints} tone="violet" value={fmtInt(s.assigned)} label="în trasee" />
          <Kpi icon={MapPin} tone="amber" value={fmtInt(s.remote_actions)} label="la distanță" />
          <Kpi icon={UserRound} tone="blue" value={fmtInt(s.human_review)} label="la om" />
          <Kpi icon={Coins} tone="violet" value={fmtLei(s.expected_value_lei)} />
          <Kpi icon={RouteIcon} tone="amber" value={fmtDec(s.total_km, 0)} unit="km" />
        </div>

        <div aria-hidden="true" key={index} className="animate-in fade-in duration-300 motion-reduce:animate-none">
          <h1 className="text-[40px] leading-[1.1] font-[750] tracking-[-0.025em] max-md:text-[28px]">{scene.headline ?? `${scene.title}.`}</h1>
          <p className="mt-1 max-w-[110ch] text-[17px] text-ink-soft">{scene.text}</p>
        </div>

        <div aria-hidden="true" className="flex flex-wrap gap-2.5">
          {regionChips.map((c) => {
            const on = c.id === scene.region;
            return (
              <span key={c.id} className={"inline-flex h-9 items-center rounded-full border px-4 text-[14.5px] font-[520] " + (on ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-[#2a3a52] text-ink")}>
                {c.label}
              </span>
            );
          })}
        </div>

        <div className="grid min-h-[460px] flex-1 lg:min-h-0 grid-cols-[minmax(0,1.55fr)_minmax(380px,1fr)] gap-4 max-lg:grid-cols-1">
          <Card
            title="România: regiuni și trasee"
            icon={MapIcon}
            iconTone="violet"
            className="relative flex min-h-[420px] flex-col"
            bodyClassName="relative flex-1 p-0 pt-3"
            action={
              <span className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[13.5px] text-ink-soft max-md:hidden">
                {legend.map(([html, label]) => (
                  <span key={label} className="flex items-center gap-1.5 whitespace-nowrap">
                    {sm(html)}
                    {label}
                  </span>
                ))}
              </span>
            }
          >
            <div className="absolute inset-x-0 top-[3.25rem] bottom-0 overflow-hidden rounded-b-[14px]">
              <PlanMap className="absolute inset-0" items={mapItems} routes={mapRoutes} depots={mapDepots} bounds={bounds} selectedId={scene.item} onSelect={noop} theme="dark" padding={MAP_PADDING} />
            </div>
          </Card>

          <div className="flex min-w-0 flex-col gap-4 lg:min-h-0 lg:overflow-y-auto">
            {item ? (
              <Card
                title={itemTitle(item) === item.asset_id ? itemPlace(item) : itemTitle(item)}
                icon={MapPin}
                iconTone="blue"
                action={<Pill tone="green">Date sintetice</Pill>}
              >
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 max-sm:grid-cols-1">
                  <div className="flex flex-col items-center gap-1">
                    <p className="flex items-center gap-2 text-[16px] font-[600]">
                      {human ? <UserRound aria-hidden="true" size={20} className="text-att-ink" /> : <Waypoints aria-hidden="true" size={20} className="text-ok-ink" />}
                      {decision ? DECISION_LABEL_RO[decision.decision] : "Fără decizie"}
                    </p>
                    {score != null ? <Gauge value={score} label={<span className="text-[26px] whitespace-nowrap">{roundPct(score)}</span>} sub={predictionLabelRo(item.prediction.label)} tone={human ? "violet" : "blue"} size={150} /> : null}
                  </div>
                  <span aria-hidden="true" className="h-24 w-px bg-rule max-sm:hidden" />
                  <ul className="space-y-2 text-[16px]">
                    <li className="flex items-center gap-3"><Layers aria-hidden="true" size={19} className="text-violet" />{fmtInt(s.items_in)} primite</li>
                    <li className="flex items-center gap-3"><Waypoints aria-hidden="true" size={19} className="text-violet" />{fmtInt(s.assigned)} în trasee</li>
                    <li className="flex items-center gap-3"><RouteIcon aria-hidden="true" size={19} className="text-violet" />{fmtDec(s.total_km, 0)} km</li>
                    <li className="flex items-center gap-3"><Coins aria-hidden="true" size={19} className="text-violet" />{fmtLei(s.expected_value_lei)}</li>
                  </ul>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-3 max-sm:grid-cols-1">
                  <span className="flex h-11 items-center justify-center gap-2 rounded-[10px] bg-[#0b2a18] text-[15.5px] font-[600] text-ok-ink">
                    {planned ? `Echipa ${decision?.crew_id ?? ""}${stopInfo.get(scene.item ?? "") ? `, ${fmtTime(stopInfo.get(scene.item ?? "")?.eta ?? "")}` : ""}` : human ? "Fără echipă trimisă" : (ACTION_RO[item.recommended_action] ?? "").replace(/^./, (c) => c.toUpperCase())}
                  </span>
                  <span className={"flex h-11 items-center justify-center gap-2 rounded-[10px] text-[15.5px] font-[600] " + (human ? "bg-att text-white" : "bg-[#0f2547] text-[#8db8ff]")}>
                    {human ? "Necesită o persoană" : decision ? DECISION_LABEL_RO[decision.decision] : "—"}
                  </span>
                </div>
              </Card>
            ) : null}

            {route ? (
              <Card title={`Cronologia traseului – ${route.crew_id}`} icon={Waypoints} iconTone="violet" bodyClassName="pt-1" className="shrink-0">
                <ol>
                  <TimelineRow time={route.depart_at ? fmtTime(route.depart_at) : "—"} label={`Plecare – ${route.depot ? shortDepot(route.depot.label_ro) : route.depot_id}`} dot="filled" badge={<Pill tone="violet" size="sm"><span translate="no">{route.crew_id}</span></Pill>} />
                  {stopOf.map((st) => {
                    const w = itemsById[st.work_item_id];
                    return (
                      <TimelineRow
                        key={st.work_item_id}
                        time={fmtTime(st.eta)}
                        label={
                          <>
                            <span translate="no">{w?.asset_id ?? st.work_item_id}</span> – {w ? (ACTION_RO[w.recommended_action] ?? "intervenție") : "intervenție"}
                          </>
                        }
                        dot={st.work_item_id === scene.item ? "current" : "empty"}
                        tone={w ? SOURCE_TONE[w.source] : undefined}
                      />
                    );
                  })}
                  <TimelineRow time={route.return_at ? fmtTime(route.return_at) : "—"} label={`Întoarcere – ${route.depot ? shortDepot(route.depot.label_ro) : route.depot_id}`} dot="empty" last />
                </ol>
              </Card>
            ) : null}
          </div>
        </div>

        <nav aria-label="Paginile prezentării" className="flex justify-center gap-3 pt-1">
          {scenes.map((sc, i) => (
            <button
              key={sc.title}
              type="button"
              onClick={() => go(i)}
              aria-current={i === index ? "step" : undefined}
              aria-label={`Scena ${i + 1}: ${sc.title}`}
              className={"grid size-10 place-items-center rounded-full border text-[15px] font-[600] transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring " + (i === index ? "border-action bg-action text-white" : "border-[#2a3a52] bg-panel text-ink hover:border-[#3d5170]")}
            >
              {i + 1}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );
}

function TimelineRow({ time, label, dot, tone, badge, last }: { time: string; label: React.ReactNode; dot: "filled" | "current" | "empty"; tone?: Tone; badge?: React.ReactNode; last?: boolean }) {
  return (
    <li className={"flex items-center gap-4 py-2 text-[15.5px] " + (last ? "" : "border-b border-rule")}>
      <span
        aria-hidden="true"
        className={"size-3.5 shrink-0 rounded-full border-2 " + (dot === "empty" ? "border-ink-soft bg-transparent" : "border-[#2a63c9] bg-src-a")}
      />
      <span className="w-14 shrink-0 font-[620] tabular-nums">{time}</span>
      <span className="flex min-w-0 flex-1 items-center gap-2">
        {tone ? <Dot tone={tone} /> : null}
        <span className="min-w-0 truncate">{label}</span>
      </span>
      {badge}
    </li>
  );
}
