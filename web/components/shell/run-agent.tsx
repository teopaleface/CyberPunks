"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { runAgent } from "@/lib/data/actions";
import type { RunTimings } from "@/lib/data/types";
import { fmtSeconds } from "@/lib/format";

const STEPS: { key: keyof RunTimings; name: string; what: string }[] = [
  { key: "perceive", name: "Perceive", what: "Citește datele: consumul contoarelor, prognoza meteo, rețelele." },
  { key: "estimate", name: "Estimate", what: "Modelele A, B și C estimează riscul pentru fiecare lucrare." },
  { key: "decide", name: "Decide", what: "Regulile din cod aleg: echipă, acțiune ieftină, amânare sau om." },
  { key: "act", name: "Act", what: "Trasee, ordine de lucru, alerte, mesaje și jurnalul deciziilor." },
];

type RunState =
  | { kind: "idle" }
  | { kind: "running"; startedAt: number }
  | { kind: "done"; planId: string; timings: RunTimings }
  | { kind: "error"; message: string };

export function RunAgentButton({ scenario, scenarioLabel }: { scenario: string; scenarioLabel: string }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<RunState>({ kind: "idle" });
  const [pending, startTransition] = useTransition();

  const start = () => {
    setState({ kind: "running", startedAt: performance.now() });
    startTransition(async () => {
      const result = await runAgent(scenario);
      if (result.ok) {
        setState({ kind: "done", planId: result.plan_id, timings: result.timings });
        router.refresh();
        toast.success("Planul de mâine s-a actualizat", { description: `Plan nou: ${result.plan_id}` });
      } else {
        setState({ kind: "error", message: result.error });
      }
    });
  };

  const total =
    state.kind === "done" ? STEPS.reduce((sum, s) => sum + (Number(state.timings[s.key]) || 0), 0) : null;

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        setOpen(v);
        if (!v && !pending) setState({ kind: "idle" });
      }}
    >
      <DialogTrigger asChild>
        <Button size="panel" className="px-5">
          <svg width="12" height="14" viewBox="0 0 12 14" aria-hidden="true">
            <path d="M1 1.2v11.6a.6.6 0 0 0 .9.5l9.4-5.8a.6.6 0 0 0 0-1L1.9.7a.6.6 0 0 0-.9.5Z" fill="currentColor" />
          </svg>
          Rulează agentul
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-[600px] gap-5 overscroll-contain rounded-[6px] p-7">
        <DialogHeader>
          <DialogTitle className="text-[22px] font-[650]">Rulează agentul</DialogTitle>
          <DialogDescription className="text-[15px] leading-relaxed">
            Agentul trece singur prin cei patru pași, pentru scenariul „{scenarioLabel}”. Nimeni nu intervine între
            pași; la final, ce nu e sigur ajunge la tine, în „Nu sunt sigur”.
          </DialogDescription>
        </DialogHeader>

        <ol className="divide-y divide-rule border-y border-rule" aria-live="polite">
          {STEPS.map((s, i) => {
            const t = state.kind === "done" ? Number(state.timings[s.key]) : null;
            return (
              <li key={s.key} className="grid grid-cols-[32px_1fr_auto] items-center gap-x-4 py-3">
                <span
                  className={
                    "grid size-7 place-items-center rounded-full border text-[14px] font-[650] transition-colors duration-200 " +
                    (state.kind === "done" ? "border-ink bg-ink text-panel" : "border-input text-ink")
                  }
                  aria-hidden="true"
                >
                  {i + 1}
                </span>
                <span>
                  <span className="block text-[16px] font-[620]">{s.name}</span>
                  <span className="block text-[14px] text-muted-foreground">{s.what}</span>
                </span>
                <span className="min-w-[72px] text-right text-[16px] font-[600] tabular-nums">
                  {state.kind === "running" ? (
                    <span className="inline-block h-1.5 w-12 overflow-hidden rounded-full bg-muted" aria-label="rulează">
                      <span className="block h-full w-1/2 animate-[runbar_1.1s_ease-in-out_infinite] rounded-full bg-ink" />
                    </span>
                  ) : t !== null && Number.isFinite(t) ? (
                    <span
                      className="inline-block animate-in fade-in slide-in-from-bottom-1 fill-mode-both"
                      style={{ animationDelay: `${i * 110}ms`, animationDuration: "260ms" }}
                    >
                      {fmtSeconds(t)}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">–</span>
                  )}
                </span>
              </li>
            );
          })}
        </ol>

        {state.kind === "done" ? (
          <p className="text-[15px]">
            Gata în <b className="tabular-nums">{fmtSeconds(total ?? 0)}</b>. Plan nou:{" "}
            <span className="code-id">{state.planId}</span>. Timpii sunt măsurați de agent la fiecare pas.
          </p>
        ) : null}
        {state.kind === "error" ? (
          <div role="alert" className="border-l-[3px] border-att bg-att-surface px-4 py-3 text-[15px]">
            <p className="font-[600] text-att-ink">Agentul n-a rulat.</p>
            <p className="mt-1">{state.message}</p>
            <p className="mt-1 text-muted-foreground">Planul de pe ecran rămâne cel de dinainte.</p>
          </div>
        ) : null}

        <DialogFooter className="gap-2 sm:justify-between">
          <Button variant="outline" size="panel" onClick={() => setOpen(false)}>
            Închide
          </Button>
          <Button size="panel" onClick={start} disabled={pending}>
            {pending ? "Rulează…" : state.kind === "done" || state.kind === "error" ? "Rulează din nou" : "Pornește agentul"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
