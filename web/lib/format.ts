/**
 * Formatare în română (ro-RO): 2.741 lei, 0,87, 31,4 km, 08:25, „Luni, 9 noiembrie 2026”.
 * Fără cod de server: se folosește și în componentele client.
 */

export const TZ = "Europe/Bucharest";

const intFmt = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 0 });
const decFmts = new Map<number, Intl.NumberFormat>();
function decFmt(digits: number): Intl.NumberFormat {
  let f = decFmts.get(digits);
  if (!f) {
    f = new Intl.NumberFormat("ro-RO", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    decFmts.set(digits, f);
  }
  return f;
}

export function fmtInt(n: number): string {
  return intFmt.format(n);
}

export function fmtDec(n: number, digits = 1): string {
  return decFmt(digits).format(n);
}

/** Probabilitate sau scor: 0,87. */
export function fmtScore(p: number): string {
  return decFmt(2).format(p);
}

/** Lei fără zecimale peste 100, cu două zecimale sub (costurile mici contează la centime). */
export function fmtLei(n: number, opts: { decimals?: number } = {}): string {
  const d = opts.decimals ?? (Math.abs(n) >= 100 ? 0 : 2);
  return `${d === 0 ? fmtInt(n) : fmtDec(n, d)} lei`;
}

export function fmtKm(n: number): string {
  return `${fmtDec(n, 1)} km`;
}

export function fmtPercent(ratio: number, digits = 0): string {
  return `${fmtDec(ratio * 100, digits)}%`;
}

const timeFmt = new Intl.DateTimeFormat("ro-RO", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: TZ });
const dateLongFmt = new Intl.DateTimeFormat("ro-RO", {
  weekday: "long",
  day: "numeric",
  month: "long",
  year: "numeric",
  timeZone: TZ,
});
const dateShortFmt = new Intl.DateTimeFormat("ro-RO", { weekday: "long", day: "numeric", month: "long", timeZone: TZ });
const partsFmt = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: TZ });

/** Ora la București: „08:25”. */
export function fmtTime(iso: string): string {
  return timeFmt.format(new Date(iso));
}

function capitalize(s: string): string {
  return s.charAt(0).toLocaleUpperCase("ro-RO") + s.slice(1);
}

/** O zi calendaristică (YYYY-MM-DD) fără să alunece din cauza fusului orar. */
function dayAnchor(date: string): Date {
  return new Date(`${date.slice(0, 10)}T12:00:00Z`);
}

/** „Luni, 9 noiembrie 2026”. */
export function fmtDateLong(date: string): string {
  return capitalize(dateLongFmt.format(dayAnchor(date)));
}

/** „luni, 9 noiembrie”. */
export function fmtDateShort(date: string): string {
  return dateShortFmt.format(dayAnchor(date));
}

/** Data și ora unui moment: „duminică, 8 noiembrie, la 06:00”. */
export function fmtMoment(iso: string): string {
  const d = new Date(iso);
  return `${dateShortFmt.format(d)}, la ${timeFmt.format(d)}`;
}

/** Minutul zilei la București (0–1439) pentru un moment ISO. */
// ziua și luna („10.05”), din partea de dată a textului, fără conversie de fus orar
const dayMonthFmt = new Intl.DateTimeFormat("ro-RO", { day: "2-digit", month: "2-digit", timeZone: "UTC" });

/** „2025-05-10” sau „2025-05-10T00:00:00” → „10.05”. */
export function fmtDayMonth(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  return m ? dayMonthFmt.format(new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])))) : iso;
}

/** Punctele zilnice vin fie ca dată, fie la miezul nopții („…T00:00:00”). */
export function isWholeDay(iso: string): boolean {
  return /^\d{4}-\d{2}-\d{2}(?:[T ]00:00(?::00(?:\.0+)?)?(?:Z|[+-]\d{2}:?\d{2})?)?$/.test(iso);
}

export function minutesOfDay(iso: string): number {
  const [h, m] = partsFmt.format(new Date(iso)).split(":").map(Number);
  return (h % 24) * 60 + m;
}

const dayFmt = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" });

/**
 * Minutul față de miezul nopții din ziua planului (București): o întoarcere a doua zi la 00:15 devine 1455,
 * nu 15, ca să rămână după plecare.
 */
export function minutesOfPlanDay(iso: string, planDate: string): number {
  const day = dayFmt.format(new Date(iso));
  const diffDays = Math.round((Date.parse(`${day}T00:00:00Z`) - Date.parse(`${planDate.slice(0, 10)}T00:00:00Z`)) / 86_400_000);
  return minutesOfDay(iso) + diffDays * 1440;
}

/** „08:05”, iar a doua zi „00:15 (+1 zi)”. */
export function hhmmDay(min: number): string {
  const extra = Math.floor(min / 1440);
  return extra > 0 ? `${hhmm(min)} (+${extra} zi)` : hhmm(min);
}

/** „HH:MM” → minutul zilei. */
export function parseHHMM(s: string): number {
  const [h, m] = s.split(":").map(Number);
  return h * 60 + (m || 0);
}

/** Minutul zilei → „08:05”. */
export function hhmm(min: number): string {
  const m = ((Math.round(min) % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

/** „40 min”, „2 h”, „1 h 35 min”. */
export function fmtDuration(min: number): string {
  const m = Math.round(min);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const r = m % 60;
  return r ? `${h} h ${r} min` : `${h} h`;
}

/** Secunde măsurate: „0,42 s”, „12 s”. */
export function fmtSeconds(s: number): string {
  if (s < 10) return `${fmtDec(s, 2)} s`;
  return `${fmtInt(s)} s`;
}

/** Prima literă mare, restul neatins (pentru motive care vin cu literă mică din date). */
export function sentence(s: string): string {
  const t = s.trim();
  if (!t) return t;
  const out = capitalize(t);
  return /[.!?…]$/.test(out) ? out : `${out}.`;
}

/** Plural românesc simplu: 1 lucrare, 2 lucrări, 20 de lucrări. */
export function plural(n: number, one: string, few: string, many = `de ${few}`): string {
  if (n === 1) return `1 ${one}`;
  const mod100 = n % 100;
  if (n === 0 || (mod100 >= 1 && mod100 <= 19)) return `${fmtInt(n)} ${few}`;
  return `${fmtInt(n)} ${many}`;
}
