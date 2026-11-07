"use client";

import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Series, WorkItem } from "@/lib/contracts";
import { fmtDayMonth, fmtDec, fmtInt, fmtScore, fmtTime, hhmm, isWholeDay, minutesOfDay } from "@/lib/format";
import { clampPercentRo, factorLabelRo } from "@/lib/data/labels";
import { bilantRows, isBilantSeries, seriesTimeMs, type BilantRow } from "@/lib/series-utils";

/**
 * Graficul potrivit sursei:
 *  A: consumul zilnic față de normal, cu zilele de zero evidențiate;
 *  B: rafalele și riscul de avarii (două grafice, câte o axă fiecare), cu fereastra furtunii;
 *  C: tensiunea maximă cu intervalul P10–P90 și limita de 1,10 pu.
 * Textul folosește culorile de text; culoarea sursei stă doar pe semne.
 */

const AXIS = { fontSize: 13, fill: "var(--muted-foreground)" };
const GRID = "var(--grid)";

type Row = Record<string, number | string | null | [number, number]>;

function isDay(t: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(t);
}

function dayLabel(t: string) {
  return fmtDayMonth(t);
}

function TooltipBox({ title, rows }: { title: string; rows: [string, string][] }) {
  return (
    <div className="rounded-[4px] border border-rule bg-popover px-3 py-2 text-[13.5px] shadow-[0_6px_18px_-8px_rgb(19_32_42/0.35)]">
      <div className="mb-1 font-[600]">{title}</div>
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-6">
          <span className="text-muted-foreground">{k}</span>
          <span className="font-[560] tabular-nums">{v}</span>
        </div>
      ))}
    </div>
  );
}

// ------------------------------------------------------------------ A: consum
function ConsumptionChart({ series }: { series: Series }) {
  const data: Row[] = series.points.map((p) => ({
    t: String(p.t),
    value: p.value ?? null,
    expected: p.expected ?? null,
    zero: p.flag === "zero" ? (p.value ?? 0) : null,
  }));
  const zeroDays = series.points.filter((p) => p.flag === "zero").map((p) => String(p.t));
  const z0 = zeroDays[0];
  const z1 = zeroDays[zeroDays.length - 1];
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 22, right: 18, bottom: 4, left: 4 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="t" tickFormatter={dayLabel} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={28} />
        <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(v: number) => fmtInt(v)} unit="" />
        {z0 && z1 ? (
          <ReferenceArea
            x1={z0}
            x2={z1}
            fill="color-mix(in oklab, var(--att) 14%, var(--panel))"
            stroke="none"
            label={{ value: `${zeroDays.length} ${zeroDays.length === 1 ? "zi" : "zile"} cu consum zero`, position: "insideTop", fontSize: 13, fill: "var(--att-ink)", fontWeight: 600 }}
          />
        ) : null}
        <Line dataKey="expected" name="normal" type="monotone" stroke="var(--idle)" strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} />
        <Line dataKey="value" name="consum" type="monotone" stroke="var(--src-a)" strokeWidth={2.2} dot={false} isAnimationActive={false} />
        <Line dataKey="zero" name="zero" stroke="none" dot={{ r: 3.5, fill: "var(--att)", stroke: "var(--panel)", strokeWidth: 1.5 }} isAnimationActive={false} legendType="none" />
        <Tooltip
          cursor={{ stroke: "var(--ink)", strokeWidth: 1, strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const r = payload[0].payload as Row;
            return (
              <TooltipBox
                title={dayLabel(String(r.t))}
                rows={[
                  ["consum", r.value == null ? "lipsă" : `${fmtDec(Number(r.value), 2)} kWh`],
                  ["normal", r.expected == null ? "–" : `${fmtDec(Number(r.expected), 2)} kWh`],
                ]}
              />
            );
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ------------------------------------------------------------------ B: furtună
function StormCharts({ series, w }: { series: Series; w: WorkItem }) {
  const data: Row[] = series.points.map((p) => ({ t: String(p.t), gust: p.value ?? null, risk: p.expected ?? null }));
  const gustLimit = series.thresholds?.rafala_prag_kmh;
  const win = w.time_window;
  const inWindow = (t: string) => win && new Date(t) >= new Date(win.start) && new Date(t) <= new Date(win.end);
  const firstIn = data.find((r) => inWindow(String(r.t)))?.t as string | undefined;
  const lastIn = data.toReversed().find((r) => inWindow(String(r.t)))?.t as string | undefined;
  const tick = (t: string) => (isDay(t) ? dayLabel(t) : fmtTime(t));
  const winLabel = win ? `furtuna, ${hhmm(minutesOfDay(win.start))}–${hhmm(minutesOfDay(win.end))}` : "";
  const area = firstIn && lastIn ? (
    <ReferenceArea x1={firstIn} x2={lastIn} fill="color-mix(in oklab, var(--src-b) 12%, var(--panel))" stroke="none" />
  ) : null;
  const tooltip = (
    <Tooltip
      cursor={{ stroke: "var(--ink)", strokeWidth: 1, strokeDasharray: "3 3" }}
      content={({ active, payload }) => {
        if (!active || !payload?.length) return null;
        const r = payload[0].payload as Row;
        return (
          <TooltipBox
            title={`${dayLabel(String(r.t))}, ${fmtTime(String(r.t))}`}
            rows={[
              ["rafale", r.gust == null ? "lipsă" : `${fmtInt(Number(r.gust))} km/h`],
              ["risc de avarii", r.risk == null ? "–" : fmtScore(Number(r.risk))],
            ]}
          />
        );
      }}
    />
  );
  return (
    <div className="space-y-1">
      <p className="text-[14px] text-muted-foreground">Rafale de vânt, km/h</p>
      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart data={data} syncId="storm" margin={{ top: 16, right: 18, bottom: 0, left: 4 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          {area}
          <XAxis dataKey="t" tickFormatter={tick} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={36} hide />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} />
          {typeof gustLimit === "number" ? (
            <ReferenceLine y={gustLimit} stroke="var(--ink)" strokeDasharray="4 4" label={{ value: `prag ${fmtInt(gustLimit)} km/h`, position: "insideTopRight", fontSize: 12.5, fill: "var(--ink)" }} />
          ) : null}
          <Line dataKey="gust" type="monotone" stroke="var(--src-b)" strokeWidth={2.2} dot={false} isAnimationActive={false} />
          {tooltip}
        </ComposedChart>
      </ResponsiveContainer>
      <p className="pt-2 text-[14px] text-muted-foreground">Riscul de avarii estimat de model (probabilitate)</p>
      <ResponsiveContainer width="100%" height={160}>
        <ComposedChart data={data} syncId="storm" margin={{ top: 8, right: 18, bottom: 4, left: 4 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          {firstIn && lastIn ? (
            <ReferenceArea x1={firstIn} x2={lastIn} fill="color-mix(in oklab, var(--src-b) 12%, var(--panel))" stroke="none" label={{ value: winLabel, position: "insideTopLeft", fontSize: 12.5, fill: "var(--src-b)" }} />
          ) : null}
          <XAxis dataKey="t" tickFormatter={tick} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={36} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={44} domain={[0, 1]} tickFormatter={(v: number) => fmtDec(v, 1)} />
          <Area dataKey="risk" type="monotone" stroke="var(--src-b)" fill="color-mix(in oklab, var(--src-b) 22%, transparent)" strokeWidth={1.8} isAnimationActive={false} />
          {tooltip}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

// ------------------------------------------------------------------ C: tensiune
function VoltageChart({ series }: { series: Series }) {
  const limit = series.thresholds?.limita_tensiune_pu ?? 1.1;
  const data: Row[] = series.points.map((p) => ({
    t: String(p.t),
    band: p.low != null && p.high != null ? [p.low, p.high] : null,
    p50: p.expected ?? null,
    value: p.value ?? null,
    over: p.flag === "peste_limita" ? (p.high ?? p.expected ?? null) : null,
    low: p.low ?? null,
    high: p.high ?? null,
  }));
  const values = series.points.flatMap((p) => [p.low, p.high, p.expected, p.value].filter((v): v is number => typeof v === "number"));
  const lo = Math.min(0.98, ...values) - 0.005;
  const hi = Math.max(limit + 0.02, ...values) + 0.005;
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 22, right: 18, bottom: 4, left: 4 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="t" tickFormatter={(t: string) => fmtTime(t)} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={40} />
        <YAxis tick={AXIS} tickLine={false} axisLine={false} width={48} domain={[lo, hi]} tickFormatter={(v: number) => fmtDec(v, 2)} />
        <Area dataKey="band" type="monotone" stroke="none" fill="color-mix(in oklab, var(--src-c) 30%, transparent)" isAnimationActive={false} />
        <ReferenceLine
          y={limit}
          stroke="var(--att)"
          strokeWidth={1.8}
          label={{ value: `limita ${fmtDec(limit, 2)} pu (EN 50160)`, position: "insideTopRight", fontSize: 13, fill: "var(--att-ink)", fontWeight: 600 }}
        />
        <Line dataKey="p50" type="monotone" stroke="var(--src-c-ink)" strokeWidth={2.2} dot={false} isAnimationActive={false} />
        <Line dataKey="value" type="monotone" stroke="var(--ink)" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line dataKey="over" stroke="none" dot={{ r: 3, fill: "var(--att)", stroke: "var(--panel)", strokeWidth: 1.2 }} isAnimationActive={false} legendType="none" />
        <Tooltip
          cursor={{ stroke: "var(--ink)", strokeWidth: 1, strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const r = payload[0].payload as Row;
            const rows: [string, string][] = [];
            if (r.p50 != null) rows.push(["estimat (P50)", `${fmtDec(Number(r.p50), 3)} pu`]);
            if (r.low != null && r.high != null) rows.push(["interval P10–P90", `${fmtDec(Number(r.low), 3)}–${fmtDec(Number(r.high), 3)}`]);
            if (r.value != null) rows.push(["măsurat", `${fmtDec(Number(r.value), 3)} pu`]);
            return <TooltipBox title={fmtTime(String(r.t))} rows={rows} />;
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ------------------------------------------------------------------ bilanț pe post

const DAY_MS = 86_400_000;
const OVER_FILL = "color-mix(in oklab, var(--att) 34%, transparent)";
const UNDER_FILL = "color-mix(in oklab, var(--src-a) 24%, transparent)";
const BAND_FILL = "color-mix(in oklab, var(--ink) 10%, transparent)";

/** Eticheta adnotării („Lipsa crește de aici”), spre interiorul graficului, lizibilă peste linii. */
function AnnotationLabel({ viewBox, text, end }: { viewBox?: { x?: number; y?: number }; text: string; end: boolean }) {
  const x = (viewBox?.x ?? 0) + (end ? -8 : 8);
  const y = (viewBox?.y ?? 0) + 16;
  return (
    <text x={x} y={y} textAnchor={end ? "end" : "start"} fontSize={13.5} fontWeight={600} fill="var(--ink)" stroke="var(--panel)" strokeWidth={5} paintOrder="stroke">
      {text}
    </text>
  );
}

function BilantChart({ series }: { series: Series }) {
  const rows = bilantRows(series);
  const real = rows.filter((r) => !r.crossing);
  const first = real[0]?.x ?? 0;
  const last = real[real.length - 1]?.x ?? 0;
  const days = Math.max(1, Math.round((last - first) / DAY_MS));
  const step = days <= 14 ? 2 : days <= 31 ? 4 : days <= 70 ? 7 : 14;
  const ticks = real.filter((r) => Math.round((r.x - first) / DAY_MS) % step === 0).map((r) => r.x);
  const tick = (x: number) => dayLabel(new Date(x).toISOString());
  const negative = real.some((r) => (r.out ?? 0) < 0 || (r.sum ?? 0) < 0);
  const unit = series.unit;
  const notes = (series.annotations ?? [])
    .map((a) => ({ x: seriesTimeMs(String(a.t)), text: factorLabelRo(clampPercentRo(a.label_ro)) }))
    .filter((a) => Number.isFinite(a.x) && a.x >= first && a.x <= last);
  return (
    <>
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={rows} margin={{ top: 14, right: 18, bottom: 4, left: 4 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis
            dataKey="x"
            type="number"
            scale="time"
            domain={[first, last]}
            ticks={ticks}
            tickFormatter={tick}
            tick={AXIS}
            tickLine={false}
            axisLine={{ stroke: "var(--rule)" }}
          />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} width={58} domain={["auto", "auto"]} tickFormatter={(v: number) => fmtInt(v)} />
          <Area dataKey="band" type="linear" stroke="none" fill={BAND_FILL} isAnimationActive={false} activeDot={false} />
          <Area dataKey="over" type="linear" stroke="none" fill={OVER_FILL} isAnimationActive={false} activeDot={false} />
          <Area dataKey="under" type="linear" stroke="none" fill={UNDER_FILL} isAnimationActive={false} activeDot={false} />
          <Line dataKey="sum" type="linear" stroke="var(--src-a)" strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line dataKey="out" type="linear" stroke="var(--ink)" strokeWidth={2.4} dot={false} isAnimationActive={false} />
          {notes.map((a) => (
            <ReferenceLine
              key={a.x}
              x={a.x}
              stroke="var(--ink)"
              strokeDasharray="4 4"
              strokeWidth={1.2}
              label={<AnnotationLabel text={a.text} end={a.x > first + (last - first) * 0.6} />}
            />
          ))}
          <Tooltip
            cursor={{ stroke: "var(--ink)", strokeWidth: 1, strokeDasharray: "3 3" }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const hovered = payload[0].payload as BilantRow;
              const r = hovered.ref ?? hovered;
              const kwh = (v: number | null) => (v == null ? "lipsă" : `${fmtDec(v, 1)} ${unit}`);
              const rowsTip: [string, string][] = [
                ["ieșit din post", kwh(r.out)],
                ["suma clienților", kwh(r.sum)],
                ["diferența", r.out != null && r.sum != null ? kwh(r.out - r.sum) : "–"],
              ];
              if (r.low != null && r.high != null && r.sum != null) {
                rowsTip.push(["pierderea normală", `${fmtDec(r.low - r.sum, 1)}–${fmtDec(r.high - r.sum, 1)} ${unit}`]);
              }
              if (r.out != null && r.high != null && r.out > r.high) rowsTip.push(["lipsă peste normal", kwh(r.out - r.high)]);
              if (r.out != null && r.low != null && r.out < r.low) rowsTip.push(["surplus sub normal", kwh(r.low - r.out)]);
              return <TooltipBox title={tick(seriesTimeMs(r.t))} rows={rowsTip} />;
            }}
          />
        </ComposedChart>
      </ResponsiveContainer>
      {negative ? (
        <p className="mt-1 text-[13.5px] text-muted-foreground">
          Sub zero sunt zilele în care panourile clienților au dat energie înapoi în rețea, prin post. Lipsa se citește la fel: cât
          trece linia neagră peste banda gri.
        </p>
      ) : null}
    </>
  );
}

/** Ce arată graficul, în cuvinte: numele accesibil al graficului (datele detaliate sunt în tooltip). */
export function chartSummaryRo(series: Series): string {
  const pts = series.points;
  const first = pts[0] ? String(pts[0].t) : "";
  const last = pts.length ? String(pts[pts.length - 1].t) : "";
  const when = (t: string) => (isWholeDay(t) ? fmtDayMonth(t) : fmtTime(t));
  const span = first && last ? `, de la ${when(first)} la ${when(last)}` : "";
  const title = series.title_ro.replace(/\.$/, "");
  if (isBilantSeries(series)) {
    const over = pts.filter((p) => p.value != null && p.high != null && p.value > p.high).length;
    const under = pts.filter((p) => p.value != null && p.low != null && p.value < p.low).length;
    const negative = pts.some((p) => (p.value ?? 0) < 0 || (p.expected ?? 0) < 0);
    return `${title}${span}. Lipsă peste normal în ${over} din ${pts.length} zile${under ? `, surplus sub normal în ${under}` : ""}.${negative ? " Sub zero sunt zilele în care panourile clienților au dat energie înapoi în rețea, prin post." : ""}`;
  }
  if (series.source === "A") {
    const zero = pts.filter((p) => p.flag === "zero").length;
    return `${title}${span}. ${zero ? `${zero} zile cu consum zero.` : "Fără zile cu consum zero."}`;
  }
  if (series.source === "C") {
    const top = Math.max(...pts.map((p) => p.high ?? p.value ?? Number.NEGATIVE_INFINITY));
    const limit = series.thresholds?.limita_tensiune_pu ?? 1.1;
    return `${title}${span}. ${Number.isFinite(top) ? `Maximul P90 ${fmtDec(top, 3)} pu, limita ${fmtDec(limit, 2)} pu.` : ""}`;
  }
  return `${title}${span}.`;
}

export function SeriesChart({ series, workItem }: { series: Series; workItem: WorkItem }) {
  const chart = isBilantSeries(series) ? (
    <BilantChart series={series} />
  ) : series.source === "A" ? (
    <ConsumptionChart series={series} />
  ) : series.source === "B" ? (
    <StormCharts series={series} w={workItem} />
  ) : (
    <VoltageChart series={series} />
  );
  return (
    <div role="img" aria-label={chartSummaryRo(series)}>
      {chart}
    </div>
  );
}

/** Legenda graficului, cu semnele folosite (identitatea nu stă doar în culoare). */
export function SeriesLegend({ source, bilant = false, series }: { source: Series["source"]; bilant?: boolean; series?: Series }) {
  const line = (color: string, dashed = false) => (
    <svg width="26" height="10" aria-hidden="true">
      <line x1="1" y1="5" x2="25" y2="5" style={{ stroke: color }} strokeWidth={2.4} strokeDasharray={dashed ? "5 4" : undefined} />
    </svg>
  );
  const box = (color: string) => <span className="inline-block h-3 w-5" style={{ background: color }} aria-hidden="true" />;
  const items: [React.ReactNode, string][] = bilant
    ? [
        [line("var(--ink)"), "ieșit din post"],
        [line("var(--src-a)"), "suma clienților"],
        [box(BAND_FILL), "banda pierderii normale"],
        [box(OVER_FILL), "lipsă peste normal"],
        ...(series?.points.some((p) => p.value != null && p.low != null && p.value < p.low)
          ? ([[box(UNDER_FILL), "surplus sub normal"]] as [React.ReactNode, string][])
          : []),
      ]
    : source === "A"
      ? [
          [line("var(--src-a)"), "consumul zilnic"],
          [line("var(--idle)", true), "ce ar fi fost normal"],
          [box("color-mix(in oklab, var(--att) 14%, var(--panel))"), "zile cu consum zero"],
        ]
      : source === "B"
        ? [
            [line("var(--src-b)"), "rafale și risc"],
            [box("color-mix(in oklab, var(--src-b) 12%, var(--panel))"), "fereastra furtunii"],
            [line("var(--ink)", true), "pragul de rafale"],
          ]
        : [
            [line("var(--src-c-ink)"), "tensiunea estimată (P50)"],
            [box("color-mix(in oklab, var(--src-c) 30%, transparent)"), "interval P10–P90"],
            [line("var(--att)"), "limita 1,10 pu"],
          ];
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[14px] text-muted-foreground">
      {items.map(([sym, label]) => (
        <span key={label} className="flex items-center gap-2">
          {sym}
          {label}
        </span>
      ))}
    </div>
  );
}
