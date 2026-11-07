"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Wordmark } from "@/components/brand/logo";
import { Briefing } from "@/components/plan/briefing";
import { PlanScreen, type PostsInfo } from "@/components/plan/plan-screen";
import { Readouts } from "@/components/plan/readouts";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { toBriefing } from "@/lib/briefing";
import { fmtDateLong } from "@/lib/format";
import type { PlanScreenData } from "@/lib/plan-screen";
import type { LocatorGeo } from "@/lib/server/geo";

interface Scene {
  title: string;
  text: string;
  /** „briefing”: primul ecran simplu; „map”: harta mare, cu linia de timp și detaliile lucrării. */
  view: "briefing" | "map";
  region?: string;
  selected?: string | null;
  spotlight?: "queue" | "peek" | "feeders" | "map" | null;
  /** Ce se evidențiază pe briefing. */
  spot?: "case" | null;
}

/**
 * Modul de prezentare pentru înregistrări: consola în tema închisă (harta de noapte), fără navigare,
 * cu scene comandate din tastatură (← →, cifrele 1–5), din adresă (?scena=2) sau automat (?auto=1).
 */
export function DemoStage({
  data,
  geo,
  postsInfo,
  generatedAt,
  initialScene,
  auto,
}: {
  data: PlanScreenData;
  geo: LocatorGeo | null;
  postsInfo?: PostsInfo;
  generatedAt: string;
  initialScene: number;
  auto: boolean;
}) {
  const scenes: Scene[] = useMemo(() => {
    const decisions = Object.values(data.decisions);
    const ranked = decisions.filter((d) => d.decision === "assigned" && d.rank != null).toSorted((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
    const top = ranked[0];
    const storm = decisions
      .filter((d) => d.work_item_id.startsWith("B-") && (d.decision === "assigned" || d.decision === "human_review"))
      .toSorted((a, b) => (data.regionOf[a.work_item_id] === "banat" ? -1 : 0) - (data.regionOf[b.work_item_id] === "banat" ? -1 : 0))[0];
    const stormRegion = storm ? (data.regionOf[storm.work_item_id] ?? undefined) : undefined;
    return [
      {
        title: "Planul de mâine",
        text: "Unde merg echipele mâine și de ce, din trei modele antrenate de noi: contoare, furtună, tensiune.",
        view: "briefing",
        spot: null,
      },
      {
        title: "Nu sunt sigur: decide un om",
        text: "Ce nu poate decide singur, agentul trimite la dispecer, cu motivul în cuvinte simple.",
        view: "briefing",
        spot: "case",
      },
      {
        title: "De ce a decis agentul așa",
        text: "Scorul, intervalul, factorii, cazul asemănător și regula, până la predicția și versiunea modelului.",
        view: "map",
        selected: top?.work_item_id ?? data.defaultSelected,
        region: (top ? data.regionOf[top.work_item_id] : null) ?? data.defaultRegion,
        spotlight: "peek",
      },
      {
        title: "Echipa ajunge înainte de furtună",
        text: "Unde vine furtuna, echipa e trimisă din timp, înainte de fereastra de risc.",
        view: "map",
        region: stormRegion,
        selected: storm?.work_item_id ?? null,
        spotlight: "map",
      },
      {
        title: "Ziua echipelor",
        text: "Traseele devin ordine de lucru; dispecerul aprobă lista pentru mâine.",
        view: "map",
        region: data.defaultRegion,
        selected: data.defaultSelected,
        spotlight: "feeders",
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
      if (el && (/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/i.test(el.tagName) || el.closest('[role="button"]'))) return;
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
  const sceneProp = useMemo(() => ({ region: scene.region, selected: scene.selected, spotlight: scene.spotlight }), [scene]);
  const briefing = useMemo(() => toBriefing(data), [data]);

  return (
    <div className="dark flex h-dvh min-h-[720px] flex-col overflow-hidden bg-canvas text-ink [color-scheme:dark]">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b border-rule bg-panel px-7">
        <Wordmark />
        <span className="h-7 w-px bg-rule" aria-hidden="true" />
        <span className="text-[17px] text-muted-foreground">Consola dispecerului Rețele Electrice, planul pentru {fmtDateLong(data.planDate).toLowerCase()}</span>
        <span className="flex-1" />
        <span className="flex items-center gap-2 rounded-[4px] border border-ink px-3 py-1.5 text-[15px] font-[520]">
          <SyntheticGlyph /> Date sintetice pe hartă reală
        </span>
        <nav aria-label="Scenele prezentării" className="flex items-center">
          {scenes.map((s, i) => (
            <button
              key={s.title}
              type="button"
              onClick={() => go(i)}
              aria-current={i === index ? "step" : undefined}
              aria-label={`Scena ${i + 1}: ${s.title}`}
              className="group grid h-9 place-items-center rounded-[4px] px-1"
            >
              {/* punctul se vede mic; ținta de clic e tot butonul */}
              <span
                aria-hidden="true"
                className={
                  "block h-2.5 rounded-full transition-[width,background-color] duration-300 " +
                  (i === index ? "w-7 bg-ink" : "w-2.5 bg-idle group-hover:bg-ink-soft")
                }
              />
            </button>
          ))}
        </nav>
      </header>
      {/* subtitrarea scenei: o bandă opacă a ei, nu peste hartă (se citește și pe proiector) */}
      <section aria-hidden="true" className="flex shrink-0 items-baseline gap-6 border-b border-rule bg-panel px-7 py-4">
        <p className="shrink-0 text-[15px] text-muted-foreground tabular-nums">
          Scena {index + 1} din {scenes.length}
        </p>
        <p key={index} className="animate-in fade-in duration-300 motion-reduce:animate-none">
          <b className="text-[24px] leading-tight font-[620]">{scene.title}.</b>{" "}
          <span className="text-[19px] text-ink-soft">{scene.text}</span>
        </p>
      </section>
      {/* regiunea anunțată rămâne montată */}
      <p role="status" className="sr-only">
        Scena {index + 1} din {scenes.length}: {scene.title}. {scene.text}
      </p>
      {scene.view === "briefing" ? (
        <div className="min-h-0 flex-1 overflow-y-auto">
          <Briefing data={data} briefing={briefing} generatedAt={generatedAt} approval={null} theme="dark" spot={scene.spot ?? null} compact />
        </div>
      ) : (
        <>
          <Readouts summary={data.summary} planDate={data.planDate} shift={data.shift} generatedAt={generatedAt} crewsTotal={data.crews.length} />
          <div className="relative flex min-h-0 flex-1 flex-col">
            <PlanScreen key={data.planId} data={data} geo={geo} initialSelected={scenes[index].selected ?? data.defaultSelected} postsInfo={postsInfo} theme="dark" scene={sceneProp} />
          </div>
        </>
      )}
    </div>
  );
}
