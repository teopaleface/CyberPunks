"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { approvePlan } from "@/lib/data/actions";
import { fmtTime } from "@/lib/format";

/** Omul aprobă lista echipelor pentru mâine; aprobarea intră în jurnal (sau rămâne locală dacă API-ul n-o are încă). */
export function ApproveList({
  scenario,
  planId,
  approvedAt,
  approvedLocal,
}: {
  scenario: string;
  planId: string;
  approvedAt: string | null;
  approvedLocal: boolean;
}) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [state, setState] = useState<{ at: string; local: boolean } | null>(approvedAt ? { at: approvedAt, local: approvedLocal } : null);
  if (state) {
    return (
      <span className="flex items-center gap-2 text-[15px] whitespace-nowrap">
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <circle cx="9" cy="9" r="8" style={{ fill: "var(--ok)" }} />
          <path d="M5 9.3l2.6 2.5L13 6.4" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <b className="font-[620]">Lista aprobată</b>
        <span className="text-muted-foreground">
          la {fmtTime(state.at)}
          {state.local ? ", doar în acest browser" : ", scrisă în jurnal"}
        </span>
      </span>
    );
  }
  return (
    <Button
      size="panel"
      disabled={pending}
      onClick={() =>
        startTransition(async () => {
          const r = await approvePlan(scenario, planId);
          if (r.ok) {
            setState({ at: r.at, local: r.local });
            toast.success("Ai aprobat lista echipelor pentru mâine", {
              description: r.local ? "API-ul nu are încă aprobarea; o păstrez în acest browser." : "Aprobarea a intrat în jurnal.",
            });
            router.refresh();
          } else {
            toast.error("Aprobarea nu s-a salvat", { description: r.error });
          }
        })
      }
    >
      {pending ? "Se trimite…" : "Aprobă lista echipelor"}
    </Button>
  );
}
