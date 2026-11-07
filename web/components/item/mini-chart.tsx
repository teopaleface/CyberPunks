"use client";

import { Area, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fmtDayMonth, fmtDec } from "@/lib/format";

export interface MiniPoint {
  t: string;
  value?: number | null;
  expected?: number | null;
  low?: number | null;
  high?: number | null;
}

const AXIS = { fontSize: 12, fill: "var(--muted-foreground)" };

function tickLabel(t: string, hours: boolean) {
  if (hours) return /T(\d{2}:\d{2})/.exec(t)?.[1] ?? t;
  return fmtDayMonth(t.slice(0, 10));
}

/**
 * Grafic mic pentru cardurile lucrării: linia observată (sau P50), banda P10–P90, linia de limită.
 * Valorile sosesc deja în unitatea de afișat (kWh, volți); culoarea e a sursei.
 */
export function MiniChart({
  points,
  unit,
  color,
  hours = false,
  limit,
  limitLabel,
  height = 190,
  label,
}: {
  points: MiniPoint[];
  unit: string;
  color: string;
  hours?: boolean;
  limit?: number;
  limitLabel?: string;
  height?: number;
  label: string;
}) {
  const data = points.map((p) => ({
    t: p.t,
    value: p.value ?? null,
    expected: p.expected ?? null,
    band: p.low != null && p.high != null ? [p.low, p.high] : null,
  }));
  const hasValue = data.some((d) => d.value != null);
  const vals = points.flatMap((p) => [p.value, p.expected, p.low, p.high]).filter((v): v is number => typeof v === "number");
  const lo = Math.min(...vals, limit ?? Infinity);
  const hi = Math.max(...vals, limit ?? -Infinity);
  const step = 10 ** Math.floor(Math.log10(((hi - lo) || 1) / 4));
  const dLo = Math.floor(lo / step) * step;
  const dHi = Math.ceil(hi / step) * step;
  const every = Math.max(0, Math.ceil(data.length / (hours ? 6 : 5)) - 1);
  return (
    <div role="img" aria-label={label} style={{ height }} className="w-full min-w-0">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="t" tickFormatter={(t: string) => tickLabel(t, hours)} interval={every} tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--rule)" }} minTickGap={16} />
          <YAxis domain={[dLo, dHi]} tickCount={5} tick={AXIS} tickLine={false} axisLine={false} width={44} tickFormatter={(v: number) => fmtDec(v, Math.abs(hi - lo) < 5 ? 1 : 0)} />
          <Tooltip
            cursor={{ stroke: "var(--rule)" }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const row = payload[0].payload as (typeof data)[number];
              const v = row.value ?? row.expected;
              return (
                <div className="rounded-[10px] border border-rule bg-popover px-3 py-2 text-[13px] shadow-lg">
                  <div className="font-[600]">{tickLabel(row.t, hours)}</div>
                  {v != null ? <div className="tabular-nums">{fmtDec(v, 1)} {unit}</div> : null}
                  {row.band ? <div className="text-muted-foreground tabular-nums">P10–P90: {fmtDec(row.band[0], 0)}–{fmtDec(row.band[1], 0)} {unit}</div> : null}
                </div>
              );
            }}
          />
          <Area dataKey="band" stroke="none" fill={color} fillOpacity={0.22} isAnimationActive={false} connectNulls />
          {hasValue ? <Line dataKey="expected" stroke="var(--idle)" strokeWidth={1.4} strokeDasharray="4 4" dot={false} isAnimationActive={false} connectNulls /> : null}
          <Line dataKey={hasValue ? "value" : "expected"} stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} connectNulls />
          {limit != null ? (
            <ReferenceLine y={limit} stroke="var(--src-c)" strokeDasharray="5 4" strokeWidth={1.6} label={limitLabel ? { value: limitLabel, position: "insideTopLeft", fill: "var(--src-c)", fontSize: 12 } : undefined} />
          ) : null}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
