/** Linie mică cu umplere, din valori reale; punctul final marchează valoarea maximă. */
export function Sparkline({ values, color = "var(--src-b)", label, className }: { values: number[]; color?: string; label: string; className?: string }) {
  if (values.length < 2) return null;
  const w = 300;
  const h = 70;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const xy = values.map((v, i) => [(i / (values.length - 1)) * w, h - 6 - ((v - min) / span) * (h - 14)] as const);
  const line = xy.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const top = xy[values.indexOf(max)];
  return (
    <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" role="img" aria-label={label} className={className ?? "h-[70px] w-full"}>
      <path d={`${line} L${w} ${h} L0 ${h} Z`} fill={color} fillOpacity={0.18} />
      <path d={line} fill="none" stroke={color} strokeWidth={2.2} vectorEffect="non-scaling-stroke" />
      <circle cx={top[0]} cy={top[1]} r={4} fill={color} />
    </svg>
  );
}
