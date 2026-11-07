"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

/** Alegerea scenariului. Se ține minte într-un cookie, ca toate ecranele să arate același scenariu. */
export function ScenarioSwitch({
  scenario,
  scenarios,
}: {
  scenario: string;
  scenarios: { id: string; label: string; detail: string }[];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();
  return (
    <Select
      value={scenario}
      onValueChange={(id) => {
        document.cookie = `scenariu=${encodeURIComponent(id)}; path=/; max-age=${60 * 60 * 24 * 7}; samesite=lax`;
        startTransition(() => router.replace(`${pathname}?scenariu=${encodeURIComponent(id)}`));
      }}
    >
      <SelectTrigger
        aria-label="Scenariul"
        data-pending={pending ? "" : undefined}
        className="h-auto min-h-10 w-full gap-2 rounded-[10px] border-[#2a3a52] bg-transparent px-3 py-2 text-left text-[13.5px] font-[520] whitespace-normal data-pending:opacity-70 *:data-[slot=select-value]:line-clamp-2 *:data-[slot=select-value]:min-w-0 *:data-[slot=select-value]:flex-1"
      >
        {/* eticheta întreagă, niciodată tăiată („Zi de vară cu furtuni”, „Mâine, cu prognoza reală”) */}
        <SelectValue>{scenarios.find((s) => s.id === scenario)?.label ?? scenario}</SelectValue>
      </SelectTrigger>
      <SelectContent align="end">
        {scenarios.map((s) => (
          <SelectItem key={s.id} value={s.id} className="text-[15px]">
            <span className="flex flex-col py-0.5">
              <span className="font-[560]">{s.label}</span>
              <span className="text-[13px] text-muted-foreground">{s.detail}</span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
