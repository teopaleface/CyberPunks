"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { AudioLines } from "lucide-react";
import { Sheet, SheetContent, SheetDescription, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Workspace } from "@/components/workspace/workspace";
import type { WorkspaceAccount } from "@/lib/operations/types";
import { proposalFromSearch } from "@/lib/operations/proposal-link";
import { assistantIntent, assistantScenarioMatches, routeSelection, type AssistantRequest, type AssistantSelection } from "./assistant-context";

/** All legacy pages share this drawer through AppShell. Account comes from the server. */
export function AgentDock({ account, scenario }: { account: WorkspaceAccount; scenario: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const search = useSearchParams();
  const query = search.toString();
  const linkedProposalId = proposalFromSearch(new URLSearchParams(query));
  const proposalPresent = search.has("proposal");
  const proposalKey = proposalPresent ? search.getAll("proposal").join(",") : null;
  const [open, setOpen] = useState(proposalPresent);
  const [selection, setSelection] = useState<AssistantSelection>(() => routeSelection(pathname, new URLSearchParams(query)));
  const [requestedAction, setRequestedAction] = useState<AssistantRequest>();
  const [scopeError, setScopeError] = useState("");
  const restoreFocus = useRef<HTMLElement | null>(null);
  const trigger = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setSelection(routeSelection(pathname, new URLSearchParams(query)));
    }, 0);
    return () => clearTimeout(timer);
  }, [pathname, query]);

  useEffect(() => {
    if (proposalKey === null) return;
    const timer = setTimeout(() => {
      restoreFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      setRequestedAction(undefined);
      setScopeError("");
      setOpen(true);
    }, 0);
    return () => clearTimeout(timer);
  }, [proposalKey]);

  useEffect(() => {
    const onAssistant = (event: Event) => {
      const detail: unknown = (event as CustomEvent<unknown>).detail;
      const intent = assistantIntent(detail);
      if (!intent) return;
      if (!open) restoreFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
      if (!assistantScenarioMatches(detail, scenario)) {
        setScopeError("This request belongs to another scenario. Open that scenario and try again.");
        setRequestedAction(undefined);
        setOpen(true);
        return;
      }
      setScopeError("");
      setSelection(Object.keys(intent.selection).length ? intent.selection : routeSelection(pathname, new URLSearchParams(query)));
      setRequestedAction(intent.requestedAction);
      setOpen(true);
    };
    const onChanged = () => router.refresh();
    window.addEventListener("daybreak:assistant", onAssistant);
    window.addEventListener("daybreak:changed", onChanged);
    return () => {
      window.removeEventListener("daybreak:assistant", onAssistant);
      window.removeEventListener("daybreak:changed", onChanged);
    };
  }, [open, pathname, query, router, scenario]);

  return (
    <Sheet open={open} onOpenChange={(next) => {
      if (next) {
        restoreFocus.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        setSelection(routeSelection(pathname, new URLSearchParams(query)));
        setRequestedAction(undefined);
        setScopeError("");
      }
      setOpen(next);
    }}>
      <SheetTrigger asChild>
        <button ref={trigger} type="button" className="fixed right-4 bottom-[calc(5rem+env(safe-area-inset-bottom))] z-40 inline-flex min-h-11 items-center gap-2 rounded-xl border border-action/30 bg-action px-4 py-2.5 text-[14px] font-semibold text-primary-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring md:right-6 md:bottom-6">
          <AudioLines aria-hidden="true" size={18} />
          Ask Daybreak
        </button>
      </SheetTrigger>
      <SheetContent side="right" className="gap-0 border-rule bg-canvas text-ink data-[side=right]:w-full data-[side=right]:sm:max-w-[560px]" onCloseAutoFocus={(event) => {
        event.preventDefault();
        const previous = restoreFocus.current;
        (previous?.isConnected && previous !== document.body ? previous : trigger.current)?.focus();
      }}>
        <div className="shrink-0 border-b border-rule px-5 py-4 pr-14">
          <SheetTitle className="text-ink">Ask Daybreak</SheetTitle>
          <SheetDescription className="mt-1 text-ink-soft">Chat or use voice. Review every proposed change before confirming.</SheetDescription>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain p-4 pb-[calc(1rem+env(safe-area-inset-bottom))]">
          {scopeError ? <p role="alert" className="rounded-xl border border-rule bg-panel p-4 text-ink">{scopeError}</p> : <Workspace
            key={`${account.id}:${scenario}:${linkedProposalId ?? "assistant"}`}
            account={account}
            scenario={scenario}
            presentation="assistant"
            initialSelection={selection}
            requestedAction={requestedAction}
            linkedProposalId={linkedProposalId}
            initialError={proposalPresent && !linkedProposalId ? "This proposal link is invalid. Prepare a new request or open a saved draft." : undefined}
          />}
        </div>
      </SheetContent>
    </Sheet>
  );
}
