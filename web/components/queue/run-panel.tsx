"use client";

import Link from "next/link";
import { MessageSquare, SlidersHorizontal } from "lucide-react";
import { englishText } from "@/lib/english";
import { btn } from "@/components/ds";
import { assistantDashboardPath } from "@/components/shell/assistant-handoff";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

/** Saved run results remain read-only; operational requests go through the assistant. */
export function RunButton({ scenario }: { scenario: string }) {
  return (
    <Link href={assistantDashboardPath(scenario)} className={btn("outline", "md")}>
      <MessageSquare aria-hidden="true" size={17} />
      Ask about this plan
    </Link>
  );
}

export interface ParamRow {
  label: string;
  value: string;
  note: string;
}

/** „Parametri”: pragurile reale din config/planner.yaml, doar de citit. */
export function ParamsButton({ rows }: { rows: ParamRow[] }) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <button type="button" className={btn("outline", "md")}>
          <SlidersHorizontal aria-hidden="true" size={17} strokeWidth={1.8} />

          Parameters
        </button>
      </DialogTrigger>
      <DialogContent className="max-h-[85dvh] overflow-y-auto sm:max-w-[640px] gap-4 rounded-[14px] border-rule bg-panel p-7">
        <DialogHeader>
          <DialogTitle className="text-[22px] font-[650]">Agent parameters</DialogTitle>
          <DialogDescription className="text-[15px]">

            Thresholds from <span className="code-id" translate="no">config/planner.yaml</span>. Read from the file. They cannot be changed here.
          </DialogDescription>
        </DialogHeader>
        {rows.length ? (
          <dl className="divide-y divide-rule border-y border-rule">
            {rows.map((r) => (
              <div key={englishText(r.label)} className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-6 gap-y-0.5 py-3">
                <dt className="text-[15.5px] font-[560]">{englishText(r.label)}</dt>
                <dd className="text-right text-[16px] font-[650] tabular-nums">{r.value}</dd>
                <dd className="col-span-2 text-[13.5px] text-ink-soft">{englishText(r.note)}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-[15px] text-ink-soft">Could not read the parameter file.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}
