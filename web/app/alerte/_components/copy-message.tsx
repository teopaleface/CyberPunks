"use client";

import { CheckIcon, CopyIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { btn } from "@/components/ds";

/** Copiază textul mesajului în clipboard (în demo nu se trimite nimic). */
export function CopyMessage({ text, noteId }: { text: string; noteId: string }) {
  const [state, setState] = useState<"idle" | "ok" | "fail">("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setState("ok");
    } catch {
      setState("fail");
    }
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), 2400);
  };
  return (
    <>
      <button type="button" onClick={copy} aria-describedby={noteId} className={btn("primary")}>
        {state === "ok" ? <CheckIcon size={18} aria-hidden="true" /> : <CopyIcon size={18} aria-hidden="true" />}
        {state === "ok" ? "Mesaj copiat" : "Copiază mesajul"}
      </button>
      <span role="status" className="sr-only">
        {state === "ok" ? "Mesajul a fost copiat." : state === "fail" ? "Copierea nu a reușit." : ""}
      </span>
    </>
  );
}
