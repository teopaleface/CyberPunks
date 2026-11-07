"use client";

import { englishText } from "@/lib/english";
import { useRouter } from "next/navigation";
import { useId, useRef, useState, useTransition } from "react";
import { toast } from "sonner";
import { Check, Clock, NotebookPen, X } from "lucide-react";
import { btn } from "@/components/ds";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { submitReview } from "@/lib/data/actions";
import type { ReviewDecision } from "@/lib/data/types";

const DONE: Record<ReviewDecision, string> = { approve: "Approved", reject: "Rejected", defer: "Deferred" };

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
      description: "Sends in 5 seconds.",
      duration: 5000,
      action: {
        label: "Undo",
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
        toast.success(`${DONE[d]} ${workItemId}`, { description: "Your decision was recorded. The plan is being recalculated." });
        setNote("");
        setNoteOpen(false);
        router.refresh();
      } else {
        toast.error("Decision was not saved", { description: englishText(r.error) });
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
            placeholder="Add a note…"
            className="min-h-[68px] rounded-[10px] border-rule bg-surface-2 px-4 py-3 text-[15.5px]"
          />
        </div>
        <div className="grid grid-cols-3 gap-3 max-sm:grid-cols-1">
          <button type="button" className={btn("primary", "lg")} onClick={() => act("approve")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <Check aria-hidden="true" size={22} strokeWidth={2.2} />
            {acting === "approve" ? "Sending…" : "Approve"}
          </button>
          <button type="button" className={btn("danger", "lg")} onClick={() => act("reject")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <X aria-hidden="true" size={22} strokeWidth={2.2} />
            {acting === "reject" || undoing === "reject" ? "Sending…" : "Reject"}
          </button>
          <button type="button" className={btn("outline", "lg")} onClick={() => act("defer")} disabled={pending || undoing !== null} aria-describedby={itemId}>
            <Clock aria-hidden="true" size={22} strokeWidth={1.9} />
            {acting === "defer" || undoing === "defer" ? "Sending…" : "Defer"}
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
          {acting === "approve" ? "Sending…" : "Approve"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("reject")} disabled={pending || undoing !== null} aria-describedby={itemId}>
          {acting === "reject" || undoing === "reject" ? "Sending…" : "Reject"}
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("defer")} disabled={pending || undoing !== null} aria-describedby={itemId}>
          {acting === "defer" || undoing === "defer" ? "Sending…" : "Defer"}
        </Button>
      </div>
      {noteOpen ? (
        <div className="space-y-2">
          <label className="block text-[15px] text-muted-foreground" htmlFor={noteId}>

            Your note (optional, recorded in the audit log)
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
            placeholder="For example: called the customer; the meter was replaced two weeks ago…"
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
          {note.trim() ? "Show note" : "Add a note"}
        </button>
      )}
    </div>
  );
}
