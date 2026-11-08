/** Formatarea în engleză (pagina e în engleză, decizia lui Teo de la 17:55): 385,791 și 8.66%. */

const intFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

/** număr întreg cu virgulă la mii: 385791 → „385,791” */
export function nf(n: number): string {
  return intFmt.format(Math.round(n));
}

/** zecimale fixe: 0.6251 → „0.63” */
export function df(n: number, digits = 2): string {
  return new Intl.NumberFormat("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n);
}

/** procent din fracție: 0.4927 → „49%” */
export function pf(frac: number, digits = 0): string {
  return `${df(frac * 100, digits)}%`;
}

const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];

/** „2025-07-08” → „July 8, 2025” */
export function formatDate(iso: string): string {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  if (!y || !m || !d) return iso;
  return `${MONTHS[m - 1]} ${d}, ${y}`;
}
