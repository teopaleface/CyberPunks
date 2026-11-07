import type { ReactNode } from "react";
import type { Verdict } from "@/lib/verdict";

/**
 * Verdictul, primul lucru de pe pagină: o frază mare (titlul paginii), apoi detaliul, apoi ce urmează
 * (eticheta deciziei, butoanele omului). Fără cifre tehnice: acelea stau în secțiunile care se deschid.
 */
export function VerdictBlock({ verdict, children }: { verdict: Verdict; children?: ReactNode }) {
  return (
    <section aria-labelledby="verdict-title" className="space-y-4">
      <h1 id="verdict-title" className="max-w-[34ch] text-[30px] leading-[1.2] font-[620] text-balance">
        {verdict.headline}
      </h1>
      {verdict.detail ? <p className="max-w-[52ch] text-[19px] leading-[1.5] text-muted-foreground">{verdict.detail}</p> : null}
      {children ? <div className="space-y-5 pt-1">{children}</div> : null}
    </section>
  );
}

/** Titlul unui grafic, scurtat dacă e foarte lung; titlul întreg rămâne la trecerea mouse-ului. */
export function shortTitle(title: string, max = 64): string {
  if (title.length <= max) return title;
  const cut = title.search(/[:;(–—]| - /);
  if (cut >= 20 && cut <= max) return title.slice(0, cut).trim();
  const slice = title.slice(0, max);
  return `${slice.slice(0, slice.lastIndexOf(" ")).trim()}…`;
}
