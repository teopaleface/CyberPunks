"use client";
import { useId, useState } from "react";
import { Check, Clock, NotebookPen, X } from "lucide-react";
import { btn } from "@/components/ds";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { requestAssistantAction, requestAssistantContext } from "@/lib/operations/assistant-intent";
import type { ReviewDecision } from "@/lib/data/types";
export function ReviewActions({workItemId, scenario, layout="default"}: {workItemId:string;scenario?:string;layout?:"default"|"card"}) {
 const noteId=useId(), itemId=useId();
 const [note,setNote]=useState("");
 const [noteOpen,setNoteOpen]=useState(false);
 const act=(decision:ReviewDecision)=>requestAssistantAction("review_work_item",{work_item_id:workItemId,decision,note},scenario);
  if (layout === "card") {
    return (
      <div className="space-y-4">
        <Button variant="outline" onClick={() => requestAssistantContext(workItemId, scenario)}>Ask about this work</Button>
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
          <button type="button" className={btn("primary", "lg")} onClick={() => act("approve")} aria-describedby={itemId}>
            <Check aria-hidden="true" size={22} strokeWidth={2.2} />
            Approve
          </button>
          <button type="button" className={btn("danger", "lg")} onClick={() => act("reject")} aria-describedby={itemId}>
            <X aria-hidden="true" size={22} strokeWidth={2.2} />
            Reject
          </button>
          <button type="button" className={btn("outline", "lg")} onClick={() => act("defer")} aria-describedby={itemId}>
            <Clock aria-hidden="true" size={22} strokeWidth={1.9} />
            Defer
          </button>
        </div>
      </div>
    );
  }
  return (
    <div className="space-y-4">
        <Button variant="outline" onClick={() => requestAssistantContext(workItemId, scenario)}>Ask about this work</Button>
      <span id={itemId} className="sr-only">
        lucrarea {workItemId}
      </span>
      <div className="flex flex-wrap items-center gap-3">
        <Button size="panel" className="min-w-[116px] text-[17px]" onClick={() => act("approve")} aria-describedby={itemId}>
          Approve
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("reject")} aria-describedby={itemId}>
          Reject
        </Button>
        <Button size="panel" variant="outline" className="text-[17px]" onClick={() => act("defer")} aria-describedby={itemId}>
          Defer
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
