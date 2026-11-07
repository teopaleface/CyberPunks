"use client";

import { useRouter } from "next/navigation";
import { useEffect, useId, useMemo, useState } from "react";
import { Search } from "lucide-react";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import type { ShellInfo } from "@/lib/server/queries";

/** Căutarea din bara de sus: un post, o lucrare sau o echipă, după ID sau loc (⌘K / Ctrl K). */
export function SearchButton({ index }: { index: ShellInfo["search"] }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const listId = useId();
  const optId = (i: number) => `${listId}-o${i}`;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const results = useMemo(() => {
    const t = q.trim().toLowerCase();
    if (!t) return index.filter((r) => r.kind !== "lucrare").slice(0, 8);
    return index
      .filter((r) => r.id.toLowerCase().includes(t) || r.label.toLowerCase().includes(t))
      .sort((a, b) => Number(!a.id.toLowerCase().startsWith(t)) - Number(!b.id.toLowerCase().startsWith(t)))
      .slice(0, 10);
  }, [q, index]);
  useEffect(() => {
    if (open) document.getElementById(optId(active))?.scrollIntoView({ block: "nearest" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, open]);
  const go = (href: string) => {
    setOpen(false);
    setQ("");
    router.push(href);
  };
  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <button type="button" aria-label="Caută un post, o lucrare sau o echipă" className="grid size-10 place-items-center rounded-[10px] border border-[#2a3a52] text-ink hover:bg-[#0f1a2b]">
          <Search aria-hidden="true" size={19} strokeWidth={1.8} />
        </button>
      </DialogTrigger>
      <DialogContent className="top-[18%] translate-y-0 gap-0 rounded-[14px] border border-rule bg-panel p-0 sm:max-w-[620px]" showCloseButton={false}>
        <DialogTitle className="sr-only">Caută</DialogTitle>
        <DialogDescription className="sr-only">Un post, o lucrare sau o echipă, după ID sau loc.</DialogDescription>
        <div className="flex items-center gap-3 border-b border-rule px-4">
          <Search aria-hidden="true" size={19} strokeWidth={1.8} className="text-ink-soft" />
          <input
            autoFocus
            role="combobox"
            aria-expanded="true"
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={results[active] ? optId(active) : undefined}
            name="cauta"
            autoComplete="off"
            spellCheck={false}
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setActive(0);
            }}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setActive((a) => Math.min(a + 1, results.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setActive((a) => Math.max(a - 1, 0));
              } else if (e.key === "Enter" && results[active]) {
                go(results[active].href);
              }
            }}
            placeholder="Caută (ex. PT-1269, MTR-011050, E-BV-1, Ineu)…"
            aria-label="Caută un post, o lucrare sau o echipă"
            className="h-14 flex-1 bg-transparent text-[16.5px] outline-none placeholder:text-ink-soft/70"
          />
        </div>
        <p role="status" className="sr-only">
          {results.length ? `${results.length} rezultate` : "Niciun rezultat"}
        </p>
        <ul id={listId} role="listbox" aria-label="Rezultate" className="max-h-[50vh] overflow-y-auto p-2">
          {results.length ? (
            results.map((r, i) => (
              <li
                key={`${r.kind}:${r.id}`}
                id={optId(i)}
                role="option"
                aria-selected={i === active}
                onMouseEnter={() => setActive(i)}
                onClick={() => go(r.href)}
                className={`flex cursor-pointer items-center gap-3 rounded-[10px] px-3 py-2.5 text-left ${i === active ? "bg-[#16233a]" : ""}`}
              >
                <span className="w-16 shrink-0 text-[12.5px] text-ink-soft">{r.kind}</span>
                <span className="font-[600]" translate="no">
                  {r.id}
                </span>
                <span className="min-w-0 truncate text-ink-soft">{r.label}</span>
              </li>
            ))
          ) : (
            <li role="presentation" className="px-3 py-6 text-center text-ink-soft">Nimic nu se potrivește cu „{q}”.</li>
          )}
        </ul>
      </DialogContent>
    </Dialog>
  );
}
