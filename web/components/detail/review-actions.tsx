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
  const itemId = useId();
  const [note, setNote] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
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
        setNoteOpen(false);
        router.refresh();
      } else {
        toast.error("Decizia nu s-a salvat", { description: r.error });
      }
    });
  };
  return (
    <div className="space-y-4">
      <span id={itemId} className="sr-only">
        lucrarea {workItemId}
      </span>
      <div className="flex flex-wrap items-center gap-3">
        <Button size="panel" className="min-w-[116px] text-[17px]" onClick={() => act("approve")} disabled={pending} aria-describedby={itemId}>
          {acting === "approve" ? "Se trimite…" : "Aprobă"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("reject")} disabled={pending} aria-describedby={itemId}>
          {acting === "reject" ? "Se trimite…" : "Respinge"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("defer")} disabled={pending} aria-describedby={itemId}>
          {acting === "defer" ? "Se trimite…" : "Amână"}
        </Button>
      </div>
      {noteOpen ? (
        <div className="space-y-2">
          <label className="block text-[15px] text-muted-foreground" htmlFor={noteId}>
            Nota ta (opțional, intră în jurnal)
          </label>
          <Textarea
            id={noteId}
            aria-describedby={itemId}
            name="nota"
            autoComplete="off"
            autoFocus
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={2000}
            placeholder="De exemplu: am sunat clientul, contorul a fost înlocuit acum două săptămâni…"
            className="min-h-[84px] rounded-[4px] bg-panel text-[16px]"
          />
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setNoteOpen(true)}
          aria-expanded={false}
          aria-describedby={itemId}
          className="text-[16px] text-muted-foreground underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
        >
          {note.trim() ? "Arată nota" : "Adaugă o notă"}
        </button>
      )}
    </div>
  );
}
