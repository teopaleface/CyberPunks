"use client";

import { useEffect, useRef, type ReactNode } from "react";

/**
 * Povestea pe derulare: figura stă fixă, pașii trec pe lângă ea. Pasul din mijlocul ecranului
 * devine activ și scrie `data-step` pe secțiune; CSS-ul schimbă harta. Fără JS, secțiunea rămâne
 * în starea finală (data-step="4") și toți pașii se citesc normal.
 */
export function Scrolly({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const steps = Array.from(root.querySelectorAll<HTMLElement>("[data-scrolly-step]"));
    if (steps.length === 0) return;
    root.dataset.js = "1";
    root.dataset.step = "0";
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) root.dataset.step = (e.target as HTMLElement).dataset.scrollyStep ?? "0";
        }
      },
      { rootMargin: "-48% 0px -48% 0px", threshold: 0 },
    );
    steps.forEach((s) => io.observe(s));
    return () => io.disconnect();
  }, []);

  return (
    <div ref={ref} className={className} data-step="4">
      {children}
    </div>
  );
}
