"use client";

import { CloudLightning, X } from "lucide-react";
import { useSyncExternalStore } from "react";

const EVENT = "home-banner";
const subscribe = (cb: () => void) => {
  window.addEventListener(EVENT, cb);
  return () => window.removeEventListener(EVENT, cb);
};

/** Avertizarea cea mai importantă a planului; se poate închide, iar alegerea ține cât durează sesiunea. */
export function AlertBanner({ id, lead, text }: { id: string; lead: string; text: string }) {
  const key = `banner:${id}`;
  const dismissed = useSyncExternalStore(
    subscribe,
    () => sessionStorage.getItem(key) === "1",
    () => true,
  );
  if (dismissed) return null;
  return (
    <div role="status" className="mb-5 flex items-center gap-3.5 rounded-[14px] border border-[#6a3fb0] bg-[#1b0f33] px-5 py-3.5 max-md:items-start max-md:px-4">
      <CloudLightning aria-hidden="true" size={30} strokeWidth={1.5} className="shrink-0 text-violet max-md:mt-0.5" />
      <p className="min-w-0 flex-1 text-[17px] text-ink-soft max-md:text-[15px]">
        <b className="font-[620] text-ink">{lead}</b> — {text}
      </p>
      <button
        type="button"
        aria-label="Închide avertizarea"
        onClick={() => {
          sessionStorage.setItem(key, "1");
          window.dispatchEvent(new Event(EVENT));
        }}
        className="grid size-9 shrink-0 place-items-center rounded-full text-ink-soft transition-colors hover:bg-white/10 hover:text-ink focus-visible:outline-2 focus-visible:outline-ring"
      >
        <X aria-hidden="true" size={22} />
      </button>
    </div>
  );
}
