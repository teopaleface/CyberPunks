/**
 * Numere „omenești” pentru primul nivel al interfeței: „circa 5.000 de lei”, „încredere mare”.
 * Valoarea exactă rămâne în detaliile tehnice. Fără cod de server: se folosește peste tot.
 */
import { fmtInt, fmtScore } from "@/lib/format";

/** „de” după numerele care cer genitivul în română: 20 de lei, 5.000 de lei, dar 12 lei. */
export function withDe(n: number, noun: string): string {
  const abs = Math.abs(Math.round(n));
  const mod100 = abs % 100;
  const needsDe = abs !== 0 && !(mod100 >= 1 && mod100 <= 19);
  return `${fmtInt(n)} ${needsDe ? "de " : ""}${noun}`;
}

/** Rotunjire pentru citit: două cifre semnificative peste 1.000 (5.019 → 5.000, 71.803 → 72.000, 12.439 → 12.000). */
export function roundForHumans(n: number): number {
  const abs = Math.abs(n);
  if (abs < 100) return Math.round(n);
  if (abs < 1000) return Math.round(n / 10) * 10;
  const digits = Math.floor(Math.log10(abs)) + 1;
  const step = 10 ** Math.max(0, digits - 2);
  return Math.round(n / step) * step;
}

/** „circa 5.000 de lei”; sub 100 de lei, suma exactă („12 lei”). */
export function approxLei(n: number | null | undefined): string {
  if (n == null || !Number.isFinite(n)) return "–";
  const r = roundForHumans(n);
  return `${Math.abs(n) >= 100 && r !== Math.round(n) ? "circa " : ""}${withDe(r, "lei")}`;
}

/** Același număr rotunjit, fără unitate („circa 72.000”), pentru cifrele mari. */
export function approxNumber(n: number): { value: string; approx: boolean } {
  const r = roundForHumans(n);
  return { value: fmtInt(r), approx: r !== Math.round(n) };
}

/** Procente rotunjite la întreg: 0,2178 → „22%”. */
export function roundPct(ratio: number): string {
  return ratio >= 0.995 && ratio < 1.005 ? "peste 99%" : `${Math.round(ratio * 100)}%`;
}

export type ConfidenceWord = "încredere mare" | "încredere medie" | "încredere mică";

/** Încrederea în cuvinte, din câmpul `confidence` (high/medium/low) sau, dacă lipsește, din scor. */
export function confidenceWord(confidence: string | null | undefined, score?: number | null): ConfidenceWord {
  if (confidence === "high") return "încredere mare";
  if (confidence === "medium") return "încredere medie";
  if (confidence === "low") return "încredere mică";
  if (typeof score === "number") return score >= 0.8 ? "încredere mare" : score >= 0.5 ? "încredere medie" : "încredere mică";
  return "încredere medie";
}

/** Scorul exact, pentru detalii: 1,00 devine „peste 0,99”, ca să nu pară certitudine. */
export function scoreText(score: number): string {
  return score >= 0.995 ? "peste 0,99" : fmtScore(score);
}
