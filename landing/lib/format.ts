/** Formatarea românească: virgulă zecimală, punct la mii, luni cu nume. */

const intFmt = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 0 });

/** număr întreg cu punct la mii: 385791 → „385.791” (și pentru 4 cifre: 1407 → „1.407”) */
export function nf(n: number): string {
  // Intl pune separatorul de mii abia de la 5 cifre în ro-RO; îl vrem și la 4
  const s = intFmt.format(Math.round(n));
  return Math.abs(Math.round(n)) >= 1000 && !s.includes(".") ? s.replace(/^(-?\d)(\d{3})$/, "$1.$2") : s;
}

/** zecimale cu virgulă: 0.6251 → „0,63” */
export function df(n: number, digits = 2): string {
  return new Intl.NumberFormat("ro-RO", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n);
}

/** procent din fracție: 0.4927 → „49%” */
export function pf(frac: number, digits = 0): string {
  return `${df(frac * 100, digits)}%`;
}

const MONTHS = ["ianuarie", "februarie", "martie", "aprilie", "mai", "iunie", "iulie", "august", "septembrie", "octombrie", "noiembrie", "decembrie"];

/** „2025-07-08” → „8 iulie 2025” */
export function formatDateRo(iso: string): string {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return iso;
  return `${d} ${MONTHS[m - 1]} ${y}`;
}

/**
 * Numărul cu „de” când româna îl cere (de la 20 în sus, dacă ultimele două cifre sunt 00 sau ≥ 20):
 * 630 → „630 de”, 26 → „26 de”, 8 → „8”, 101 → „101”.
 */
export function nDe(n: number): string {
  const a = Math.abs(Math.round(n));
  const r = a % 100;
  return `${nf(n)}${a >= 20 && (r === 0 || r >= 20) ? " de" : ""}`;
}
