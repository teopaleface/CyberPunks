/**
 * Scala unui scor (0–1): intervalul de încredere ca bandă, scorul ca linie, pragul regulii ca semn punctat.
 * Se vede dintr-o privire dacă intervalul trece de prag (de ce agentul n-a fost sigur).
 */
export function ScoreScale({
  score,
  low,
  high,
  threshold,
  width = 150,
  tone = "ink",
}: {
  score: number;
  low?: number | null;
  high?: number | null;
  threshold?: number | null;
  width?: number;
  tone?: "ink" | "att";
}) {
  const X = (v: number) => +(1 + Math.max(0, Math.min(1, v)) * (width - 2)).toFixed(1);
  const color = tone === "att" ? "var(--att)" : "var(--ink)";
  return (
    <svg width={width} height={22} viewBox={`0 0 ${width} 22`} aria-hidden="true" className="shrink-0">
      <line x1={1} x2={width - 1} y1={11} y2={11} style={{ stroke: "var(--idle)" }} strokeWidth={2} />
      <line x1={1} x2={1} y1={7} y2={15} style={{ stroke: "var(--idle)" }} strokeWidth={1.5} />
      <line x1={width - 1} x2={width - 1} y1={7} y2={15} style={{ stroke: "var(--idle)" }} strokeWidth={1.5} />
      {low != null && high != null ? (
        <rect
          x={X(low)}
          y={6}
          width={Math.max(2, X(high) - X(low))}
          height={10}
          style={{ fill: tone === "att" ? "color-mix(in oklab, var(--att) 28%, var(--panel))" : "color-mix(in oklab, var(--ink) 18%, var(--panel))" }}
        />
      ) : null}
      {threshold != null ? (
        <line x1={X(threshold)} x2={X(threshold)} y1={1} y2={21} style={{ stroke: "var(--ink)" }} strokeWidth={1.2} strokeDasharray="2 2" />
      ) : null}
      <rect x={X(score) - 1.5} y={2} width={3} height={18} style={{ fill: color }} />
    </svg>
  );
}
