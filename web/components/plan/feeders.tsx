"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Decision, WorkItem } from "@/lib/contracts";
import type { Crew, Depot, ResolvedRoute } from "@/lib/data/types";
import { fmtDec, fmtInt, hhmm, hhmmDay, parseHHMM } from "@/lib/format";
import { markerSvg } from "@/lib/marker-svg";
import { crewTimeline, timelineRange, workItemWindow, type CrewTimeline } from "@/lib/plan-derive";
import type { QuarantineEntry } from "@/lib/plan-screen";
import { ApproveList } from "./approve-list";

/**
 * Linia de timp a echipelor, desenată ca o schemă monofilară: fiecare bază e o bară groasă, fiecare echipă
 * o plecare din bară. Drumul e o linie subțire, lucrul un bloc gros în culoarea sursei. Fereastra în care
 * contează lucrarea (furtuna, soarele de la prânz) stă în spatele rândului.
 */

const ROW_H = 60;
const AXIS_H = 34;
const LEFT = 300;
const RIGHT_PAD = 28;
const SRC_FILL = { A: "var(--src-a)", B: "var(--src-b)", C: "var(--src-c)" } as const;

function placeName(w: WorkItem, short = false): string {
  if (w.asset_type === "meter") return short ? w.asset_id.replace(/^MTR-/, "") : w.asset_id;
  const z = w.location.zone_id.split("-").slice(1).join(" ");
  const local = z ? z.charAt(0) + z.slice(1).toLowerCase() : "";
  return w.asset_type === "zone" ? `Zona ${local || w.asset_id}` : `${w.asset_id}${local ? `, ${local}` : ""}`;
}

export function Feeders({
  routes,
  itemsById,
  decisions,
  depots,
  crews,
  shift,
  quarantine,
  selectedId,
  onSelect,
  scenario,
  planId,
  planDate,
  approval,
  highlight = false,
}: {
  highlight?: boolean;
  planDate: string;
  scenario: string;
  planId: string;
  approval: { at: string; local: boolean } | null;
  routes: ResolvedRoute[];
  itemsById: Record<string, WorkItem>;
  decisions: Record<string, Decision>;
  depots: Depot[];
  crews: Crew[];
  shift: { start: string; end: string } | null;
  quarantine: QuarantineEntry[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(1600);
  const selectedCyRef = useRef<number | null>(null);
  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.max(900, Math.round(entry.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const model = useMemo(() => {
    const timelines = routes.map((r) => ({ route: r, tl: crewTimeline(r, shift?.start ?? "08:00", planDate) }));
    // axa acoperă tura și orele echipelor; ferestrele mai lungi se taie la margine
    const windows: { start: number; end: number }[] = timelines.map(({ tl }) => ({ start: tl.depart, end: tl.back }));
    const range = timelineRange(shift, windows);
    // grupăm echipele pe baze, în ordinea bazelor din config
    const order = new Map(depots.map((d, i) => [d.depot_id, i]));
    const groups = new Map<string, { route: ResolvedRoute; tl: CrewTimeline }[]>();
    for (const t of timelines.toSorted(
      (a, b) => (order.get(a.route.depot_id) ?? 99) - (order.get(b.route.depot_id) ?? 99) || a.tl.depart - b.tl.depart,
    )) {
      const g = groups.get(t.route.depot_id) ?? [];
      g.push(t);
      groups.set(t.route.depot_id, g);
    }
    return { range, groups: [...groups.entries()] };
  }, [routes, shift, depots, planDate]);

  const { range, groups } = model;
  const x = (m: number) => +(LEFT + ((m - range.start) / (range.end - range.start)) * (width - LEFT - RIGHT_PAD)).toFixed(1);
  const rows = groups.reduce((n, [, g]) => n + g.length, 0);
  const height = AXIS_H + rows * ROW_H + groups.length * 22 + 8;
  const s0 = parseHHMM(shift?.start ?? "08:00");
  const s1 = parseHHMM(shift?.end ?? "16:00");

  const used = new Set(routes.map((r) => r.crew_id));
  const free = crews.filter((c) => !used.has(c.crew_id));
  const depotName = (id: string) =>
    depots.find((d) => d.depot_id === id)?.label_ro.replace(/^Bază operativă\s*/i, "").replace(/\s*\(simulată\)/, "") ?? id;
  const freeByDepot = new Map<string, string[]>();
  for (const c of free) freeByDepot.set(c.depot_id, [...(freeByDepot.get(c.depot_id) ?? []), c.crew_id]);

  // pozițiile rândurilor, calculate o dată (fără variabile modificate în timpul randării)
  const layout: { depotId: string; top: number; busTop: number; busBottom: number; rows: { route: ResolvedRoute; tl: CrewTimeline; cy: number }[] }[] = [];
  {
    let cursor = AXIS_H;
    for (const [depotId, g] of groups) {
      const top = cursor;
      cursor += 22;
      const rowsOut = g.map(({ route, tl }) => {
        const cy = cursor + ROW_H / 2 - 4;
        cursor += ROW_H;
        return { route, tl, cy };
      });
      layout.push({ depotId, top, busTop: top + 26, busBottom: cursor - 18, rows: rowsOut });
    }
  }
  const hours: number[] = [];
  for (let h = Math.ceil(range.start / 60) * 60; h <= range.end; h += 60) hours.push(h);

  // rândul echipei care are lucrarea selectată (pentru derulare)
  const selectedCy = selectedId
    ? (layout.flatMap((g) => g.rows).find((r) => r.route.stops.some((st) => st.work_item_id === selectedId))?.cy ?? null)
    : null;

  // când lucrarea selectată e în traseul unei echipe care nu se vede, linia de timp derulează la ea
  useEffect(() => {
    const box = boxRef.current;
    if (!box || selectedCy == null || selectedCyRef.current === selectedCy) return;
    selectedCyRef.current = selectedCy;
    const top = selectedCy - ROW_H / 2 - 22; // rândul și eticheta bazei, sub axa orelor
    const visible = top >= box.scrollTop + AXIS_H - 4 && selectedCy + ROW_H / 2 <= box.scrollTop + box.clientHeight;
    if (visible) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // eticheta bazei ajunge chiar sub axa orelor (axa lipită are AXIS_H - 8 px)
    box.scrollTo({ top: Math.max(0, top - (AXIS_H - 8)), behavior: reduce ? "auto" : "smooth" });
  }, [selectedCy]);

  return (
    <section aria-label="Ziua echipelor" className={"flex shrink-0 flex-col border-t border-rule bg-panel" + (highlight ? " spot" : "")}>
      <div ref={boxRef} className="max-h-[244px] overflow-y-auto [@media(max-height:950px)]:max-h-[184px]">
        {routes.length === 0 ? (
          <p className="px-7 py-6 text-[15px] text-muted-foreground">
            Nicio echipă nu are lucrări mâine. Dacă există lucrări, sunt amânate sau așteaptă un om.
          </p>
        ) : (
          <>
            {/* axa orelor rămâne vizibilă când lista echipelor e derulată */}
            <div className="sticky top-0 z-10 bg-panel" style={{ height: AXIS_H - 8 }} aria-hidden="true">
              <svg width={width} height={AXIS_H - 8} className="block font-sans">
                {hours.map((h) => (
                  <text key={h} x={x(h)} y={18} textAnchor="middle" fontSize={13} style={{ fill: "var(--muted-foreground)" }}>
                    {hhmm(h)}
                  </text>
                ))}
              </svg>
            </div>
            <svg
              width={width}
              height={height}
              viewBox={`0 0 ${width} ${height}`}
              role="group"
              aria-label="Linia de timp a echipelor pentru mâine"
              className="block font-sans"
              style={{ marginTop: -(AXIS_H - 8) }}
            >
              {/* tura */}
              <rect x={x(s0)} y={AXIS_H - 6} width={x(s1) - x(s0)} height={height - AXIS_H} fill="var(--canvas)" opacity={0.55} />
              <text x={x(s1) - 6} y={AXIS_H + 12} textAnchor="end" fontSize={12.5} style={{ fill: "var(--muted-foreground)" }}>
                tura {shift?.start ?? "08:00"}–{shift?.end ?? "16:00"}
              </text>
              {hours.map((h) => (
                <line key={h} x1={x(h)} x2={x(h)} y1={AXIS_H} y2={height - 4} style={{ stroke: "var(--grid)" }} strokeWidth={1} />
              ))}

              {layout.map(({ depotId, top, busTop, busBottom, rows: groupRows }) => (
                <g key={depotId}>
                  <text x={28} y={top + 15} fontSize={13.5} fontWeight={600} style={{ fill: "var(--ink)" }}>
                    {depots.find((d) => d.depot_id === depotId)?.label_ro.replace(/\s*\(simulată\)/, "") ?? depotId}
                  </text>
                  <rect x={LEFT - 56} y={busTop} width={7} height={Math.max(20, busBottom - busTop)} style={{ fill: "var(--ink)" }} />
                  {groupRows.map(({ route, tl, cy }) => (
                    <CrewRow
                      scenario={scenario}
                      planDate={planDate}
                      key={route.crew_id}
                      route={route}
                      tl={tl}
                      cy={cy}
                      x={x}
                      rangeEnd={range.end}
                      itemsById={itemsById}
                      decisions={decisions}
                      selectedId={selectedId}
                      onSelect={onSelect}
                    />
                  ))}
                </g>
              ))}
            </svg>
          </>
        )}
      </div>
      <div className="flex h-[52px] shrink-0 items-center gap-7 border-t border-rule px-7 text-[15px]">
        <span className="font-[620] whitespace-nowrap">
          {free.length === 1 ? "1 echipă liberă" : `${free.length} echipe libere`}
        </span>
        {[...freeByDepot.entries()].map(([d, ids]) => (
          <span key={d} className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-muted-foreground">{depotName(d)}</span>
            {ids.map((id) => (
              <span key={id} className="dense flex items-center gap-1.5 font-[560]">
                <svg width="11" height="11" viewBox="0 0 12 12" aria-hidden="true">
                  <rect x="1" y="1" width="10" height="10" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth={1.6} />
                </svg>
                {id}
              </span>
            ))}
          </span>
        ))}
        {quarantine.length ? (
          <>
            <span className="h-6 w-px bg-rule" aria-hidden="true" />
            <span className="flex min-w-0 items-center gap-2">
              <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" className="shrink-0">
                <rect x="1" y="1" width="14" height="14" fill="none" style={{ stroke: "var(--ink)" }} strokeWidth={1.6} />
                <line x1="3.5" y1="12.5" x2="12.5" y2="3.5" style={{ stroke: "var(--ink)" }} strokeWidth={1.6} />
              </svg>
              <span className="truncate">
                <b className="font-[620]">Carantină:</b>{" "}
                {quarantine.length === 1 ? "1 lucrare respinsă la intrare" : `${quarantine.length} lucrări respinse la intrare`},{" "}
                <span translate="no" className="code-id">{quarantine[0].id}</span>: {quarantine[0].reason.replace(/^Intrare greșită:\s*/i, "").replace(/\.$/, "")}
              </span>
            </span>
          </>
        ) : null}
        <span className="flex-1" />
        <ApproveList key={planId} scenario={scenario} planId={planId} approvedAt={approval?.at ?? null} approvedLocal={approval?.local ?? false} />
      </div>
    </section>
  );
}

function CrewRow({
  scenario,
  planDate,
  route,
  tl,
  cy,
  x,
  rangeEnd,
  itemsById,
  decisions,
  selectedId,
  onSelect,
}: {
  scenario: string;
  planDate: string;
  route: ResolvedRoute;
  tl: CrewTimeline;
  cy: number;
  x: (m: number) => number;
  rangeEnd: number;
  itemsById: Record<string, WorkItem>;
  decisions: Record<string, Decision>;
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const busX = LEFT - 56 + 7;
  const stops = tl.blocks.length;
  const sel0 = (id: string) => id === selectedId;
  return (
    <g>
      {/* ferestrele lucrărilor, în spatele rândului */}
      {tl.blocks.map((b) => {
        const w = itemsById[b.workItemId];
        const win = w ? workItemWindow(w, planDate) : null;
        if (!w || !win) return null;
        const storm = w.source === "B";
        const label = storm ? `furtuna ${hhmm(win.start)}–${hhmmDay(win.end)}` : w.source === "C" ? `fereastra de tensiune ${hhmm(win.start)}–${hhmm(win.end)}` : `fereastra ${hhmm(win.start)}–${hhmmDay(win.end)}`;
        return (
          <g key={`win-${b.workItemId}`}>
            <rect
              x={x(win.start)}
              y={cy - 25}
              width={Math.max(0, x(Math.min(win.end, rangeEnd)) - x(win.start))}
              height={50}
              style={{ fill: storm ? "color-mix(in oklab, var(--src-b) 13%, var(--panel))" : "var(--canvas)" }}
            />
            <text x={x(Math.min(win.end, rangeEnd)) - 8} y={cy - 12} textAnchor="end" fontSize={12.5} style={{ fill: storm ? "var(--src-b)" : "var(--muted-foreground)" }}>
              {label}
            </text>
          </g>
        );
      })}

      {/* eticheta echipei: deschide ordinul de lucru (PDF) */}
      <a href={`/ordine/${encodeURIComponent(route.crew_id)}?scenariu=${encodeURIComponent(scenario)}`} target="_blank" rel="noreferrer" aria-label={`Ordinul de lucru al echipei ${route.crew_id}, PDF`}>
        <text x={28} y={cy - 4} fontSize={18} fontWeight={650} style={{ fill: "var(--ink)", textDecoration: "underline", textDecorationColor: "var(--rule)" }}>
          {route.crew_id}
        </text>
        <text x={28 + route.crew_id.length * 11.2 + 8} y={cy - 5} fontSize={12.5} style={{ fill: "var(--muted-foreground)" }}>
          ordin PDF
        </text>
      </a>
      <text x={28} y={cy + 15} fontSize={13.5} style={{ fill: "var(--muted-foreground)" }}>
        {stops === 1 ? "1 oprire" : `${stops} opriri`}, {fmtDec(tl.totalKm, 1)} km, {fmtInt(tl.totalWorkMin)} min lucru
      </text>

      {/* întrerupătorul închis de la bară până la axa timpului */}
      <line x1={busX} x2={LEFT} y1={cy} y2={cy} style={{ stroke: "var(--ink)" }} strokeWidth={2} />
      <rect x={busX + 9} y={cy - 6} width={12} height={12} style={{ fill: "var(--ink)" }} />

      {/* în bază, înainte de plecare și după întoarcere */}
      <line x1={LEFT} x2={x(tl.depart)} y1={cy} y2={cy} style={{ stroke: "var(--idle)" }} strokeWidth={2} strokeDasharray="1 5" strokeLinecap="round" />
      <line x1={x(tl.back)} x2={x(rangeEnd)} y1={cy} y2={cy} style={{ stroke: "var(--idle)" }} strokeWidth={2} strokeDasharray="1 5" strokeLinecap="round" />

      {/* drumurile */}
      {tl.blocks.map((b) => (
        <g key={`leg-${b.workItemId}`}>
          <line x1={x(b.from)} x2={x(b.start)} y1={cy} y2={cy} style={{ stroke: "var(--travel)" }} strokeWidth={2} />
          {x(b.start) - x(b.from) > 54 ? (
            <text x={(x(b.from) + x(b.start)) / 2} y={cy - 9} textAnchor="middle" fontSize={12.5} style={{ fill: "var(--muted-foreground)" }}>
              {fmtDec(b.travelKm, 1)} km
            </text>
          ) : null}
        </g>
      ))}
      {tl.blocks.length ? (
        <line x1={x(tl.blocks[tl.blocks.length - 1].end)} x2={x(tl.back)} y1={cy} y2={cy} style={{ stroke: "var(--travel)" }} strokeWidth={2} />
      ) : null}

      {/* plecare și întoarcere */}
      <circle cx={x(tl.depart)} cy={cy} r={4} style={{ fill: "var(--ink)" }} />
      <text x={x(tl.depart) - 8} y={cy + 23} textAnchor="end" fontSize={12.5} style={{ fill: "var(--muted-foreground)" }}>
        {tl.departApprox ? "cca " : ""}pleacă {hhmm(tl.depart)}
      </text>
      <rect x={x(tl.back) - 5} y={cy - 5} width={10} height={10} style={{ fill: "var(--panel)", stroke: "var(--ink)" }} strokeWidth={2} />
      {/* lângă capătul axei, eticheta se întoarce spre stânga ca să nu iasă din ecran */}
      <text
        x={x(tl.back) + (x(tl.back) > x(rangeEnd) - 150 ? -10 : 10)}
        y={cy + 23}
        textAnchor={x(tl.back) > x(rangeEnd) - 150 ? "end" : "start"}
        fontSize={12.5}
        style={{ fill: "var(--muted-foreground)" }}
      >
        {tl.backApprox ? "cca " : ""}revine {hhmmDay(tl.back)}
      </text>

      {/* lucrul */}
      {tl.blocks.map((b) => {
        const w = itemsById[b.workItemId];
        if (!w) return null;
        const xa = x(b.start);
        const xb = x(b.end);
        const wide = xb - xa > 190;
        // numele și orele apar doar unde încap; altfel rămân în informațiile de la trecerea mouse-ului
        const full = placeName(w);
        // lățimea estimată a textului (Archivo îngust, 14,5 px): ~7,4 px pe caracter; contoarele pierd prefixul când e strâmt
        const name = full.length * 7.4 <= xb - xa - 2 ? full : placeName(w, true);
        const showName = name.length * 7.4 <= xb - xa - 2 || sel0(b.workItemId);
        const showTime = xb - xa >= 84 || sel0(b.workItemId);
        const sel = b.workItemId === selectedId;
        const d = decisions[b.workItemId];
        return (
          <g
            key={`blk-${b.workItemId}`}
            role="button"
            tabIndex={0}
            aria-label={`${full}, ${hhmm(b.start)}–${hhmm(b.end)}, echipa ${route.crew_id}`}
            aria-pressed={sel}
            onClick={() => onSelect(b.workItemId)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect(b.workItemId);
              }
            }}
            className="cursor-pointer outline-none [&:focus-visible>.focus]:opacity-100"
          >
            <title>{`${full}: ${hhmm(b.start)}–${hhmm(b.end)}${d ? `, ${d.reason_ro}` : ""}`}</title>
            <rect x={xa - 18} y={cy - 26} width={xb - xa + 26} height={52} fill="transparent" />
            <rect className="focus opacity-0" x={xa - 20} y={cy - 17} width={xb - xa + 26} height={34} rx={4} fill="none" style={{ stroke: "var(--ring)" }} strokeWidth={2} />
            {sel ? <rect x={xa - 16} y={cy - 15} width={xb - xa + 22} height={30} rx={3} fill="none" style={{ stroke: "var(--ink)" }} strokeWidth={1.5} /> : null}
            <rect
              x={xa}
              y={cy - 7}
              width={Math.max(4, xb - xa)}
              height={14}
              style={{ fill: SRC_FILL[w.source], stroke: w.source === "C" ? "var(--ink)" : "none" }}
              strokeWidth={w.source === "C" ? 1.5 : 0}
            />
            <g transform={`translate(${xa - 18},${cy - 18})`} dangerouslySetInnerHTML={{ __html: markerSvg({ source: w.source }).replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "") }} />
            {showName ? (
              <text x={wide ? xa + 18 : (xa + xb) / 2} y={cy - 19} textAnchor={wide ? "start" : "middle"} fontSize={14.5} fontWeight={600} style={{ fill: "var(--ink)", fontStretch: "88%" }}>
                {name}
              </text>
            ) : null}
            {showTime ? (
              <text x={wide ? xa + 18 : (xa + xb) / 2} y={cy + 25} textAnchor={wide ? "start" : "middle"} fontSize={14} style={{ fill: "var(--ink)", fontStretch: "88%" }}>
                {hhmm(b.start)}–{hhmm(b.end)}
              </text>
            ) : null}
            {w.effort.requires_planned_outage ? (
              <g transform={`translate(${xa + 116},${cy + 20})`}>
                <g transform="scale(1.25)" style={{ stroke: "var(--ink)" }} strokeWidth={1.7} fill="none" strokeLinecap="round">
                  <line x1={0} y1={0} x2={7} y2={0} />
                  <circle cx={8.5} cy={0} r={1.8} style={{ fill: "var(--ink)" }} />
                  <line x1={8.5} y1={0} x2={22} y2={-8} />
                  <line x1={24} y1={-4} x2={24} y2={4} />
                  <line x1={24} y1={0} x2={31} y2={0} />
                </g>
                <text x={48} y={5} fontSize={13.5} style={{ fill: "var(--ink)" }}>
                  cere întrerupere planificată
                </text>
              </g>
            ) : null}
          </g>
        );
      })}
    </g>
  );
}
