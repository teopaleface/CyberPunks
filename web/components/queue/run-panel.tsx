"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { Play, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import { btn } from "@/components/ds";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { runAgent } from "@/lib/data/actions";
import type { RunTimings } from "@/lib/data/types";
import { fmtSeconds } from "@/lib/format";

const STEPS: { key: keyof RunTimings; name: string }[] = [
  { key: "perceive", name: "Percepe" },
  { key: "estimate", name: "Estimează" },
  { key: "decide", name: "Decide" },
  { key: "act", name: "Acționează" },
];

type State = { kind: "idle" } | { kind: "done"; planId: string; timings: RunTimings } | { kind: "error"; message: string };

/** „Rulează agentul”: cheamă acțiunea reală și arată timpii măsurați la fiecare pas. */
export function RunButton({ scenario }: { scenario: string }) {
  const router = useRouter();
  const [state, setState] = useState<State>({ kind: "idle" });
  const [pending, startTransition] = useTransition();
  const start = () => {
    startTransition(async () => {
      const r = await runAgent(scenario);
      if (r.ok) {
        setState({ kind: "done", planId: r.plan_id, timings: r.timings });
        toast.success("Planul de mâine s-a actualizat", { description: `Plan nou: ${r.plan_id}` });
        router.refresh();
      } else {
        setState({ kind: "error", message: r.error });
      }
    });
  };
  const total = state.kind === "done" ? STEPS.reduce((s, x) => s + (Number(state.timings[x.key]) || 0), 0) : 0;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
      <button type="button" onClick={start} disabled={pending} className={btn("primary", "md")}>
        <Play aria-hidden="true" size={17} strokeWidth={2} fill="currentColor" />
        {pending ? "Rulează…" : "Rulează agentul"}
      </button>
      <div aria-live="polite" className="text-[14.5px] text-ink-soft">
        {pending ? "Agentul trece prin cei patru pași…" : null}
        {state.kind === "done" ? (
          <>
            Gata în <b className="text-ink tabular-nums">{fmtSeconds(total)}</b>:{" "}
            {STEPS.map((s, i) => (
              <span key={s.key}>
                {i ? ", " : ""}
                {s.name.toLowerCase()} <span className="tabular-nums">{fmtSeconds(Number(state.timings[s.key]) || 0)}</span>
              </span>
            ))}
            .
          </>
        ) : null}
        {state.kind === "error" ? <span role="alert" className="text-att-ink">Agentul n-a rulat: {state.message}</span> : null}
      </div>
    </div>
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
          Parametri
        </button>
      </DialogTrigger>
      <DialogContent className="max-w-[640px] gap-4 rounded-[14px] border-rule bg-panel p-7">
        <DialogHeader>
          <DialogTitle className="text-[22px] font-[650]">Parametrii agentului</DialogTitle>
          <DialogDescription className="text-[15px]">
            Pragurile din <span className="code-id" translate="no">config/planner.yaml</span>. Se citesc din fișier și nu se schimbă de aici.
          </DialogDescription>
        </DialogHeader>
        {rows.length ? (
          <dl className="divide-y divide-rule border-y border-rule">
            {rows.map((r) => (
              <div key={r.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-6 gap-y-0.5 py-3">
                <dt className="text-[15.5px] font-[560]">{r.label}</dt>
                <dd className="text-right text-[16px] font-[650] tabular-nums">{r.value}</dd>
                <dd className="col-span-2 text-[13.5px] text-ink-soft">{r.note}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-[15px] text-ink-soft">Fișierul de parametri nu a putut fi citit.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}
