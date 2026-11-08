/** Funcții despre serii, fără cod de client: se pot chema și din paginile de server. */
import type { Series } from "@/lib/contracts";

/** Seria bilanțului pe post: „ieșit din post” (value) față de „suma clienților” (expected). */
export function isBilantSeries(series: Series): boolean {
  return (
    series.points.some((p) => p.flag === "lipsa_peste_normal" || p.flag === "surplus_sub_normal") ||
    /ieșit din post|bilan/i.test(series.title_ro)
  );
}

/** Ora unui punct, în milisecunde UTC; fusul orar din text e ignorat (graficul numără doar zile). */
export function seriesTimeMs(t: string): number {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?)?/.exec(t);
  if (!m) return Number.NaN;
  return Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4] ?? 0), Number(m[5] ?? 0), Number(m[6] ?? 0));
}

/**
 * Un rând din graficul bilanțului. `band` e unde ar trebui să fie „ieșit din post” cu pierderea normală
 * (`low`–`high`); `over` e lipsa peste normal (de la `high` până la valoare), `under` e surplusul sub normal
 * (de la valoare până la `low`). În afara lor, `over` și `under` au înălțime zero, ca zona colorată să înceapă
 * exact unde linia trece de bandă.
 */
export interface BilantRow {
  x: number;
  t: string;
  out: number | null;
  sum: number | null;
  low: number | null;
  high: number | null;
  band: [number, number] | null;
  over: [number, number] | null;
  under: [number, number] | null;
  /** Punct adăugat la trecerea liniei prin marginea benzii; tooltip-ul arată punctul real cel mai apropiat. */
  crossing?: boolean;
  ref?: BilantRow;
}

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

function makeRow(x: number, t: string, out: number | null, sum: number | null, low: number | null, high: number | null): BilantRow {
  return {
    x,
    t,
    out,
    sum,
    low,
    high,
    band: low != null && high != null ? [Math.min(low, high), Math.max(low, high)] : null,
    over: out != null && high != null ? [high, Math.max(out, high)] : null,
    under: out != null && low != null ? [Math.min(out, low), low] : null,
  };
}

const lerp = (a: number | null, b: number | null, f: number) => (a != null && b != null ? a + (b - a) * f : null);

/**
 * Rândurile graficului, cu puncte în plus acolo unde „ieșit din post” intră sau iese din banda normală.
 * Liniile se desenează drept între puncte, așa că punctele adăugate stau exact pe ele.
 */
export function bilantRows(series: Series): BilantRow[] {
  const real = series.points
    .map((p) => makeRow(seriesTimeMs(String(p.t)), String(p.t), num(p.value), num(p.expected), num(p.low), num(p.high)))
    .filter((r) => Number.isFinite(r.x))
    .sort((a, b) => a.x - b.x);
  const rows: BilantRow[] = [];
  real.forEach((a, i) => {
    rows.push(a);
    const b = real[i + 1];
    if (!b || a.out == null || b.out == null) return;
    const fractions: number[] = [];
    for (const edge of ["high", "low"] as const) {
      const ea = a[edge];
      const eb = b[edge];
      if (ea == null || eb == null) continue;
      const da = a.out - ea;
      const db = b.out - eb;
      if ((da > 0 && db < 0) || (da < 0 && db > 0)) fractions.push(da / (da - db));
    }
    for (const f of fractions.sort((p, q) => p - q)) {
      const row = makeRow(
        a.x + (b.x - a.x) * f,
        f < 0.5 ? a.t : b.t,
        lerp(a.out, b.out, f),
        lerp(a.sum, b.sum, f),
        lerp(a.low, b.low, f),
        lerp(a.high, b.high, f),
      );
      rows.push({ ...row, crossing: true, ref: f < 0.5 ? a : b });
    }
  });
  return rows;
}
