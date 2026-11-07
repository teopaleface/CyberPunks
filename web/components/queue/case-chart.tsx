"use client";

import { useId } from "react";
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface CasePoint {
  x: string;
  v: number;
}

/** Grafic de arie în stilul „Noapte”: o singură serie, fără legendă, cu limita punctată dacă există. */
export function CaseChart({ data, unit, color, limit, label }: { data: CasePoint[]; unit: string; color: string; limit?: number | null; label: string }) {
  const gid = `qa${useId().replace(/[^a-z0-9]/gi, "")}`;
  const vals = data.map((d) => d.v);
  const lo = Math.min(...vals, limit ?? Infinity);
  const hi = Math.max(...vals, limit ?? -Infinity);
  const pad = (hi - lo) * 0.1 || 1;
  return (
    <div role="img" aria-label={label} className="h-[170px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 14, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.55} />
              <stop offset="100%" stopColor={color} stopOpacity={0.04} />
            </linearGradient>
          </defs>
          <CartesianGrid vertical={false} stroke="#1c2a3e" />
          <XAxis dataKey="x" tick={{ fontSize: 12.5, fill: "#c3ccd8" }} tickLine={false} axisLine={{ stroke: "#2a3a52" }} minTickGap={36} />
          <YAxis
            tick={{ fontSize: 12.5, fill: "#c3ccd8" }}
            tickLine={false}
            axisLine={false}
            width={44}
            domain={[Math.max(0, Math.floor(lo - pad)), Math.ceil(hi + pad)]}
            tickFormatter={(v: number) => String(Number.isInteger(v) ? v : Math.round(v * 100) / 100).replace(".", ",")}
          />
          {limit != null ? <ReferenceLine y={limit} stroke="var(--att)" strokeDasharray="4 4" /> : null}
          <Tooltip
            cursor={{ stroke: "#3d5170" }}
            contentStyle={{ background: "#0b1626", border: "1px solid #2a3a52", borderRadius: 10, color: "#eef2f7", fontSize: 13 }}
            formatter={(v) => [`${String(v)} ${unit}`, ""]}
            separator=""
          />
          <Area type="monotone" dataKey="v" stroke={color} strokeWidth={2} fill={`url(#${gid})`} dot={false} activeDot={{ r: 4 }} isAnimationActive={false} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
