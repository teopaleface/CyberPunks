"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Workspace } from "@/components/workspace/workspace";
import type { WorkspaceAccount } from "@/lib/operations/types";
import { proposalFromSearch } from "@/lib/operations/proposal-link";
import { assistantIntent, assistantScenarioMatches, routeSelection, type AssistantRequest, type AssistantSelection } from "./assistant-context";
import { assistantDashboardPath, consumeAssistantIntent, storeAssistantIntent } from "./assistant-handoff";

type AssistantProps = { account: WorkspaceAccount; scenario: string; presentation?: "assistant" | "main" };

/** Other console pages only transfer an intent. There is no launcher or drawer. */
export function AgentDock({ account, scenario }: AssistantProps) {
  const router = useRouter();
  const pathname = usePathname();
  const query = useSearchParams().toString();
  useEffect(() => {
    if (pathname === "/app") return;
    const onAssistant = (event: Event) => {
      const detail: unknown = (event as CustomEvent<unknown>).detail;
      const intent = assistantIntent(detail);
      if (!intent || !assistantScenarioMatches(detail, scenario)) return;
      const selection = Object.keys(intent.selection).length
        ? intent.selection : routeSelection(pathname, new URLSearchParams(query));
      try {
        const stored = storeAssistantIntent(window.sessionStorage, account.id, scenario, {
          selection,
          ...(intent.requestedAction ? { action: intent.requestedAction.action, data: intent.requestedAction.data } : {}),
          scenario,
        });
        if (!stored) return;
      } catch { /* Storage can be disabled. The dashboard still checks fresh scope. */ }
      router.push(assistantDashboardPath(scenario));
    };
    const onChanged = () => router.refresh();
    window.addEventListener("daybreak:assistant", onAssistant);
    window.addEventListener("daybreak:changed", onChanged);
    return () => {
      window.removeEventListener("daybreak:assistant", onAssistant);
      window.removeEventListener("daybreak:changed", onChanged);
    };
  }, [account.id, pathname, query, router, scenario]);
  useEffect(() => {
    if (pathname === "/app") return;
    const params = new URLSearchParams(query);
    if (!params.has("proposal")) return;
    const next = new URLSearchParams({ scenariu: scenario, proposal: proposalFromSearch(params) ?? "invalid" });
    router.replace(`/app?${next}#assistant`);
  }, [pathname, query, router, scenario]);
  return null;
}

/** Server-verified identity and scenario reset all private conversation/voice state. */
export function DashboardAssistant(props: AssistantProps) {
  return <DashboardAssistantContent key={JSON.stringify([props.account.id, props.account.membership, props.scenario])} {...props} />;
}

function DashboardAssistantContent({ account, scenario, presentation = "assistant" }: AssistantProps) {
  const router = useRouter();
  const query = useSearchParams().toString();
  const params = new URLSearchParams(query);
  const linkedProposalId = proposalFromSearch(params);
  const proposalPresent = params.has("proposal");
  const proposalKey = JSON.stringify(params.getAll("proposal"));
  const panel = useRef<HTMLElement>(null);
  const [selection, setSelection] = useState<AssistantSelection | undefined>(() => {
    const selected = routeSelection("/app", params);
    const explicit = ["case_id", "work_item_id", "connection_id", "lucrare"].some((key) => params.has(key));
    return Object.keys(selected).length || explicit ? selected : undefined;
  });
  const [requestedAction, setRequestedAction] = useState<AssistantRequest>();
  const [scopeError, setScopeError] = useState("");
  const focusPanel = () => {
    panel.current?.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "nearest" });
    panel.current?.focus({ preventScroll: true });
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      let incoming: ReturnType<typeof consumeAssistantIntent> = null;
      try { incoming = consumeAssistantIntent(window.sessionStorage, account.id, scenario); } catch { /* Optional navigation context. */ }
      // A proposal link has priority. Never replace its review with a cached form.
      if (!proposalPresent && incoming) {
        setSelection(incoming.selection);
        setRequestedAction(incoming.requestedAction);
      }
      if (incoming || proposalPresent || window.location.hash === "#assistant") focusPanel();
    }, 0);
    return () => clearTimeout(timer);
  }, [account.id, scenario, proposalPresent]);

  useEffect(() => {
    const onAssistant = (event: Event) => {
      const detail: unknown = (event as CustomEvent<unknown>).detail;
      const intent = assistantIntent(detail);
      if (!intent) return;
      if (!assistantScenarioMatches(detail, scenario)) {
        setScopeError("This request belongs to another scenario. Open that scenario and select it again. No action was taken.");
        setRequestedAction(undefined);
      } else {
        setScopeError("");
        setSelection(intent.selection);
        setRequestedAction(intent.requestedAction);
      }
      focusPanel();
    };
    const onChanged = () => router.refresh();
    window.addEventListener("daybreak:assistant", onAssistant);
    window.addEventListener("daybreak:changed", onChanged);
    return () => {
      window.removeEventListener("daybreak:assistant", onAssistant);
      window.removeEventListener("daybreak:changed", onChanged);
    };
  }, [router, scenario]);

  return (
    <section id="assistant" className={presentation === "main" ? "db-assistant-main" : "db-assistant-card"} aria-label="Daybreak assistant" tabIndex={-1} ref={panel}>
      {scopeError ? <div className="db-workspace db-assistant-error">
        <h2>Daybreak assistant</h2>
        <p role="alert" className="db-alert">{scopeError}</p>
        <button type="button" className="db-button" onClick={() => { setScopeError(""); setSelection({}); }}>Back to chat</button>
      </div> : <Workspace
        key={proposalKey}
        account={account}
        scenario={scenario}
        presentation={presentation}
        initialSelection={selection}
        requestedAction={requestedAction}
        linkedProposalId={linkedProposalId}
        initialError={proposalPresent && !linkedProposalId ? "This proposal link is invalid. Prepare a new request or open a saved draft." : undefined}
      />}
    </section>
  );
}
