"use client";

import { useRouter } from "next/navigation";
import { useId, useRef, useState, useTransition } from "react";
import { toast } from "sonner";
import { Check, Clock, NotebookPen, X } from "lucide-react";
import { btn } from "@/components/ds";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { submitReview } from "@/lib/data/actions";
import type { ReviewDecision } from "@/lib/data/types";

const DONE: Record<ReviewDecision, string> = { approve: "Ai aprobat", reject: "Ai respins", defer: "Ai amânat" };

/** Decizia omului: aprobă, respinge sau amână, cu o notă. Se scrie în jurnal cu actor „om”. */
export function ReviewActions({ workItemId, scenario, layout = "default" }: { workItemId: string; scenario?: string; layout?: "default" | "card" }) {
  const router = useRouter();
  const noteId = useId();
  const itemId = useId();
  const [note, setNote] = useState("");
  const [noteOpen, setNoteOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [acting, setActing] = useState<ReviewDecision | null>(null);
  const [undoing, setUndoing] = useState<ReviewDecision | null>(null);
  const undoTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Respinge și Amână replanifică ziua: 5 secunde în care decizia se poate anula, apoi se trimite
  const act = (d: ReviewDecision) => {
    if (d === "approve") return send(d);
    setUndoing(d);
    const toastId = toast(`${DONE[d]} ${workItemId}`, {
      description: "Se trimite în 5 secunde.",
      duration: 5000,
      action: {
        label: "Anulează",
        onClick: () => {
          if (undoTimer.current) clearTimeout(undoTimer.current);
          undoTimer.current = null;
          setUndoing(null);
        },
      },
    });
    undoTimer.current = setTimeout(() => {
      undoTimer.current = null;
      toast.dismiss(toastId);
      setUndoing(null);
      send(d);
    }, 5000);
  };
  const send = (d: ReviewDecision) => {
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
  if (layout === "card") {
    return (
      <div className="space-y-4">
        <span id={itemId} className="sr-only">
          lucrarea {workItemId}
        </span>
        <div>
          <label htmlFor={noteId} className="mb-2 flex items-center gap-2.5 text-[15.5px] text-ink">
            <NotebookPen aria-hidden="true" size={20} strokeWidth={1.7} className="text-ink-soft" />
            Note
          </label>
          <Textarea
            id={noteId}
            aria-describedby={itemId}
            name="nota"
            autoComplete="off"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            maxLength={2000}
            placeholder="Adaugă o notă…"
            className="min-h-[68px] rounded-[10px] border-[#2a3a52] bg-surface-2 px-4 py-3 text-[15.5px]"
          />
        </div>
        <div className="grid grid-cols-3 gap-3 max-sm:grid-cols-1">
          <button type="button" className={btn("primary", "lg")} onClick={() => act("approve")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <Check aria-hidden="true" size={22} strokeWidth={2.2} />
            {acting === "approve" ? "Se trimite…" : "Aprobă"}
          </button>
          <button type="button" className={btn("danger", "lg")} onClick={() => act("reject")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <X aria-hidden="true" size={22} strokeWidth={2.2} />
            {acting === "reject" || undoing === "reject" ? "Se trimite…" : "Respinge"}
          </button>
          <button type="button" className={btn("outline", "lg")} onClick={() => act("defer")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <Clock aria-hidden="true" size={22} strokeWidth={1.9} />
            {acting === "defer" || undoing === "defer" ? "Se trimite…" : "Amână"}
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4">
      <span id={itemId} className="sr-only">
        lucrarea {workItemId}
      </span>
      <div className="flex flex-wrap items-center gap-3">
        <Button size="panel" className="min-w-[116px] text-[17px]" onClick={() => act("approve")} disabled={pending || undoing !== null} aria-describedby={itemId}>
          {acting === "approve" ? "Se trimite…" : "Aprobă"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("reject")} disabled={pending || undoing !== null} aria-describedby={itemId}>
          {acting === "reject" || undoing === "reject" ? "Se trimite…" : "Respinge"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("defer")} disabled={pending || undoing !== null} aria-describedby={itemId}>
          {acting === "defer" || undoing === "defer" ? "Se trimite…" : "Amână"}
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
