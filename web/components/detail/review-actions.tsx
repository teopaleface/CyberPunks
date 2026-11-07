"use client";

import { useRouter } from "next/navigation";
import { useId, useState, useTransition } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { submitReview } from "@/lib/data/actions";
import type { ReviewDecision } from "@/lib/data/types";

const DONE: Record<ReviewDecision, string> = { approve: "Ai aprobat", reject: "Ai respins", defer: "Ai amânat" };

/** Decizia omului: aprobă, respinge sau amână, cu o notă. Se scrie în jurnal cu actor „om”. */
export function ReviewActions({ workItemId, scenario }: { workItemId: string; scenario?: string }) {
  const router = useRouter();
  const noteId = useId();
  const [note, setNote] = useState("");
  const [pending, startTransition] = useTransition();
  const [acting, setActing] = useState<ReviewDecision | null>(null);
  const act = (d: ReviewDecision) => {
    setActing(d);
    startTransition(async () => {
      const r = await submitReview(workItemId, d, note, scenario);
      setActing(null);
      if (r.ok) {
        toast.success(`${DONE[d]} ${workItemId}`, { description: "Decizia ta a intrat în jurnal, iar planul se recalculează." });
        setNote("");
        router.refresh();
      } else {
        toast.error("Decizia nu s-a salvat", { description: r.error });
      }
    });
  };
  return (
    <div className="space-y-3">
      <label className="block text-[14px] font-[560]" htmlFor={noteId}>
        Nota ta (opțional, intră în jurnal)
      </label>
      <Textarea
        id={noteId}
        name="nota"
        autoComplete="off"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        maxLength={2000}
        placeholder="De exemplu: am sunat clientul, contorul a fost înlocuit acum două săptămâni…"
        className="min-h-[76px] rounded-[4px] bg-panel text-[15px]"
      />
      <div className="flex flex-wrap gap-2.5">
        <Button size="panel" onClick={() => act("approve")} disabled={pending}>
          {acting === "approve" ? "Se trimite…" : "Aprobă"}
        </Button>
        <Button size="panel" variant="outline" onClick={() => act("reject")} disabled={pending}>
          {acting === "reject" ? "Se trimite…" : "Respinge"}
        </Button>
        <Button size="panel" variant="outline" onClick={() => act("defer")} disabled={pending}>
          {acting === "defer" ? "Se trimite…" : "Amână"}
        </Button>
      </div>
    </div>
  );
}
