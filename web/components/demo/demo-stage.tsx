"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { LogoMark } from "@/components/brand/logo";
import { PlanScreen, type PostsInfo } from "@/components/plan/plan-screen";
import { Readouts } from "@/components/plan/readouts";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { fmtDateLong } from "@/lib/format";
import type { PlanScreenData } from "@/lib/plan-screen";
import type { LocatorGeo } from "@/lib/server/geo";

interface Scene {
  title: string;
  text: string;
  region?: string;
  selected?: string | null;
  spotlight?: "queue" | "peek" | "feeders" | "map" | null;
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
    const human = decisions.find((d) => d.decision === "human_review");
    const ranked = decisions.filter((d) => d.decision === "assigned" && d.rank != null).toSorted((a, b) => (a.rank ?? 99) - (b.rank ?? 99));
    const top = ranked[0];
    const storm = decisions
      .filter((d) => d.work_item_id.startsWith("B-") && (d.decision === "assigned" || d.decision === "human_review"))
      .toSorted((a, b) => (data.regionOf[a.work_item_id] === "banat" ? -1 : 0) - (data.regionOf[b.work_item_id] === "banat" ? -1 : 0))[0];
    const stormRegion = storm ? (data.regionOf[storm.work_item_id] ?? undefined) : undefined;
    return [
      { title: "Planul de mâine", text: "Unde merg echipele mâine și de ce, din trei modele antrenate de noi: contoare, furtună, tensiune.", region: data.defaultRegion, selected: data.defaultSelected, spotlight: null },
      { title: "Nu sunt sigur: decide un om", text: "Ce nu poate decide singur, agentul trimite la dispecer, cu motivul în cuvinte simple.", selected: human?.work_item_id ?? data.defaultSelected, spotlight: "queue" },
      { title: "De ce a decis agentul așa", text: "Scorul, intervalul, factorii, cazul asemănător și regula, până la predicția și versiunea modelului.", selected: top?.work_item_id ?? data.defaultSelected, spotlight: "peek" },
      { title: "Echipa ajunge înainte de furtună", text: "Unde vine furtuna, echipa e trimisă din timp, înainte de fereastra de risc.", region: stormRegion, selected: storm?.work_item_id ?? null, spotlight: "map" },
      { title: "Ziua echipelor", text: "Traseele devin ordine de lucru; dispecerul aprobă lista pentru mâine.", spotlight: "feeders" },
    ];
  }, [data]);

  const [index, setIndex] = useState(() => Math.min(Math.max(initialScene - 1, 0), 4));
  const go = useCallback((i: number) => setIndex(((i % scenes.length) + scenes.length) % scenes.length), [scenes.length]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLElement && /input|textarea|select/i.test(e.target.tagName)) return;
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
    if (!auto) return;
    const t = window.setInterval(() => setIndex((i) => (i + 1) % scenes.length), 7000);
    return () => window.clearInterval(t);
  }, [auto, scenes.length]);

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("scena", String(index + 1));
    window.history.replaceState(window.history.state, "", url);
  }, [index]);

  const scene = scenes[index];
  const sceneProp = useMemo(() => ({ region: scene.region, selected: scene.selected, spotlight: scene.spotlight }), [scene]);

  return (
    <div className="dark flex h-dvh min-h-[720px] flex-col overflow-hidden bg-canvas text-ink">
      <header className="flex h-16 shrink-0 items-center gap-6 border-b border-rule bg-panel px-7">
        <span className="flex items-center gap-2.5">
          <LogoMark size={26} />
          <span className="text-[21px] font-[650] tracking-[-0.005em]">Tura de mâine</span>
        </span>
        <span className="h-7 w-px bg-rule" aria-hidden="true" />
        <span className="text-[17px] text-muted-foreground">Consola dispecerului Rețele Electrice, planul pentru {fmtDateLong(data.planDate).toLowerCase()}</span>
        <span className="flex-1" />
        <span className="flex items-center gap-2 rounded-[4px] border border-ink px-3 py-1.5 text-[15px] font-[520]">
          <SyntheticGlyph /> Date sintetice pe hartă reală
        </span>
        <nav aria-label="Scenele prezentării" className="flex items-center gap-1.5">
          {scenes.map((s, i) => (
            <button
              key={s.title}
              type="button"
              onClick={() => go(i)}
              aria-current={i === index ? "step" : undefined}
              aria-label={`Scena ${i + 1}: ${s.title}`}
              className={"h-2.5 rounded-full transition-all duration-300 " + (i === index ? "w-7 bg-ink" : "w-2.5 bg-idle hover:bg-ink-soft")}
            />
          ))}
        </nav>
      </header>
      <Readouts summary={data.summary} planDate={data.planDate} shift={data.shift} generatedAt={generatedAt} crewsTotal={data.crews.length} />
      <div className="relative flex min-h-0 flex-1 flex-col">
        <PlanScreen data={data} geo={geo} initialSelected={scenes[index].selected ?? data.defaultSelected} postsInfo={postsInfo} theme="dark" scene={sceneProp} />
        <div
          key={index}
          className="pointer-events-none absolute bottom-[326px] left-4 z-20 w-[min(720px,52%)] animate-in fade-in slide-in-from-bottom-2 rounded-[6px] border border-rule bg-panel/95 px-5 py-3.5 duration-500"
          role="status"
          aria-live="polite"
        >
          <p className="text-[13px] tracking-[0.01em] text-muted-foreground tabular-nums">
            Scena {index + 1} din {scenes.length}
          </p>
          <p className="text-[22px] leading-tight font-[650]">{scene.title}</p>
          <p className="mt-1 text-[16px] leading-snug text-ink-soft">{scene.text}</p>
        </div>
      </div>
    </div>
  );
}
