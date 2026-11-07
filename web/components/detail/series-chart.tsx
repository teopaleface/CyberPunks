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
import { fmtDec, fmtInt, fmtScore, fmtTime, hhmm, minutesOfDay } from "@/lib/format";

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
  const [, m, d] = t.slice(0, 10).split("-");
  return `${Number(d)}.${m}`;
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
/** „Ieșit din post” (value) față de „suma clienților” (expected); lipsa dintre ele, colorată unde e peste normal. */
export function isBilantSeries(series: Series): boolean {
  return series.points.some((p) => p.flag === "lipsa_peste_normal") || /ieșit din post|bilan/i.test(series.title_ro);
}

function BilantChart({ series }: { series: Series }) {
  const data: Row[] = series.points.map((p) => ({
    t: String(p.t),
    out: p.value ?? null,
    sum: p.expected ?? null,
    gap: p.value != null && p.expected != null ? [Math.min(p.value, p.expected), Math.max(p.value, p.expected)] : null,
    over: p.flag === "lipsa_peste_normal" && p.value != null && p.expected != null ? [Math.min(p.value, p.expected), Math.max(p.value, p.expected)] : null,
  }));
  const daily = series.points.every((p) => isDay(String(p.t)));
  const tick = (t: string) => (daily || isDay(t) ? dayLabel(t) : fmtTime(t));
  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 18, right: 18, bottom: 4, left: 4 }}>
        <CartesianGrid vertical={false} stroke={GRID} />
        <XAxis dataKey="t" tickFormatter={tick} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={32} />
        <YAxis tick={AXIS} tickLine={false} axisLine={false} width={52} tickFormatter={(v: number) => fmtInt(v)} />
        <Area dataKey="gap" type="monotone" stroke="none" fill="color-mix(in oklab, var(--ink) 9%, transparent)" isAnimationActive={false} />
        <Area dataKey="over" type="monotone" stroke="none" fill="color-mix(in oklab, var(--att) 32%, transparent)" isAnimationActive={false} />
        <Line dataKey="sum" type="monotone" stroke="var(--src-a)" strokeWidth={2.2} dot={false} isAnimationActive={false} />
        <Line dataKey="out" type="monotone" stroke="var(--ink)" strokeWidth={2.2} dot={false} isAnimationActive={false} />
        <Tooltip
          cursor={{ stroke: "var(--ink)", strokeWidth: 1, strokeDasharray: "3 3" }}
          content={({ active, payload }) => {
            if (!active || !payload?.length) return null;
            const r = payload[0].payload as Row;
            const out = r.out == null ? null : Number(r.out);
            const sum = r.sum == null ? null : Number(r.sum);
            return (
              <TooltipBox
                title={tick(String(r.t))}
                rows={[
                  ["ieșit din post", out == null ? "lipsă" : `${fmtDec(out, 1)} ${series.unit}`],
                  ["suma clienților", sum == null ? "lipsă" : `${fmtDec(sum, 1)} ${series.unit}`],
                  ["lipsa", out != null && sum != null ? `${fmtDec(out - sum, 1)} ${series.unit}` : "–"],
                ]}
              />
            );
          }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function SeriesChart({ series, workItem }: { series: Series; workItem: WorkItem }) {
  if (isBilantSeries(series)) return <BilantChart series={series} />;
  if (series.source === "A") return <ConsumptionChart series={series} />;
  if (series.source === "B") return <StormCharts series={series} w={workItem} />;
  return <VoltageChart series={series} />;
}

/** Legenda graficului, cu semnele folosite (identitatea nu stă doar în culoare). */
export function SeriesLegend({ source, bilant = false }: { source: Series["source"]; bilant?: boolean }) {
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
        [box("color-mix(in oklab, var(--att) 32%, transparent)"), "lipsă peste normal"],
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
