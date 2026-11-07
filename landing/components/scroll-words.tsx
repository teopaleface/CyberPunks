"use client";

import { useEffect, useRef } from "react";

/**
 * Text care se aprinde cuvânt cu cuvânt pe măsură ce derulezi (ca pe paginile de produs Apple).
 * Fără JS sau cu prefers-reduced-motion, textul e aprins de la început.
 * Bucățile marcate cu *...* rămân albe tot timpul (prima propoziție, ideea principală).
 */
export function ScrollWords({ text, className }: { text: string; className?: string }) {
  const ref = useRef<HTMLParagraphElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const words = Array.from(el.querySelectorAll<HTMLSpanElement>("[data-w]"));
    let raf = 0;
    const update = () => {
      raf = 0;
      const r = el.getBoundingClientRect();
      const vh = window.innerHeight;
      const start = vh * 0.82; // începe când paragraful intră în ecran
      const end = vh * 0.35; // e aprins tot când ajunge spre mijloc
      const p = Math.min(1, Math.max(0, (start - r.top) / (r.height + start - end)));
      const lit = p * words.length;
      for (let i = 0; i < words.length; i++) {
        words[i].style.opacity = String(Math.min(1, Math.max(0.2, lit - i + 0.2)));
      }
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  const words = text.split(" ");
  return (
    <p ref={ref} className={className}>
      {words.map((w, i) => (
        <span key={i} data-w className="transition-opacity duration-150 ease-out">
          {w}
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </p>
  );
}
