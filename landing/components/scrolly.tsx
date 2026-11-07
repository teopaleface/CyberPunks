import type { ReactNode } from "react";

/**
 * Povestea pe derulare: figura stă fixă, pașii trec pe lângă ea. Scriptul din components/enhance.tsx
 * scrie pe secțiune `data-step` pentru pasul din mijlocul ecranului; CSS-ul schimbă harta. Fără JS,
 * secțiunea rămâne în starea finală (data-step="4") și toți pașii se citesc normal.
 */
export function Scrolly({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div data-scrolly className={`city ${className ?? ""}`} data-step="4">
      {children}
    </div>
  );
}
