"use client";

import { Check } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { toast } from "sonner";
import { approvePlan } from "@/lib/data/actions";
import { fmtTime } from "@/lib/format";

/** Aprobarea listei echipelor: aceeași acțiune de server ca înainte; aprobarea intră în jurnal (sau rămâne în acest browser). */
export function ApproveButton({
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
  // ultima bucată a ID-ului planului (ex. „043b”), ca să se vadă ce versiune aprobi
  const tag = planId.split("-").pop() ?? planId.slice(-6);

  if (state) {
    return (
      <p role="status" className="flex min-h-12 items-center justify-center gap-2.5 rounded-[10px] border border-[#1f8a4a] bg-[#0b2a18] px-4 py-2 text-center text-[15px] text-[#7ee2a0]">
        <Check aria-hidden="true" size={20} strokeWidth={2.2} className="shrink-0" />
        <span>
          <b className="font-[620]">Lista aprobată</b> la {fmtTime(state.at)}
          <span className="block text-[13px] opacity-80">{state.local ? "doar în acest browser" : "scrisă în jurnal"}</span>
        </span>
      </p>
    );
  }
  return (
    <button
      type="button"
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
      className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-[10px] bg-[#ffc502] px-5 py-3 text-[15px] leading-snug font-[600] text-black transition-colors hover:bg-[#ffdc6b] disabled:pointer-events-none disabled:opacity-50 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring"
    >
      <Check aria-hidden="true" size={22} strokeWidth={2.2} className="shrink-0" />
      <span>
        {pending ? "Se trimite…" : "Aprobă lista echipelor"}
        <span className="ml-1 text-black/65" translate="no">
          {" "}
          #{tag}
        </span>
      </span>
    </button>
  );
}
