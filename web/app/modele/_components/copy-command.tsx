"use client";

import { useEffect, useRef, useState } from "react";

/** Comanda care refăce cifrele, pe un rând, cu buton de copiere. */
export function CopyCommand({ cmd, label = "Copiază comanda" }: { cmd: string; label?: string }) {
  const [state, setState] = useState<"idle" | "done" | "failed">("idle");
  const codeRef = useRef<HTMLElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(cmd);
      setState("done");
    } catch {
      // Fără acces la clipboard (de exemplu pe http): selectăm comanda, ca s-o copieze omul.
      const el = codeRef.current;
      if (el) {
        const range = document.createRange();
        range.selectNodeContents(el);
        const sel = window.getSelection();
        sel?.removeAllRanges();
        sel?.addRange(range);
      }
      setState("failed");
    }
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), 2200);
  };

  return (
    <div className="flex min-w-0 items-stretch rounded-[4px] border border-rule bg-panel">
      <code ref={codeRef} translate="no" className="dense min-w-0 flex-1 px-3 py-2 text-[14px] leading-6 break-words whitespace-pre-wrap">
        {cmd}
      </code>
      <button
        type="button"
        onClick={copy}
        className="shrink-0 border-l border-rule px-3 text-[14px] font-[560] whitespace-nowrap transition-colors duration-150 hover:bg-muted focus-visible:outline-2 focus-visible:outline-ink"
        aria-label={label}
      >
        {state === "done" ? "Copiat" : state === "failed" ? "Selectată, copiaz-o" : "Copiază"}
      </button>
      {/* anunțul stă în afara butonului: numele butonului nu-l mai acoperă */}
      <span role="status" className="sr-only">
        {state === "done" ? "Comanda e copiată." : state === "failed" ? "Clipboard indisponibil; comanda e selectată, copiaz-o." : ""}
      </span>
    </div>
  );
}
