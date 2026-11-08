import { Suspense } from "react";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { currentUser, toMembership } from "@/lib/server/accounts";
import { mayReadConsole } from "@/lib/operations/policy";
import { parseProposalId, proposalSignInPath } from "@/lib/operations/proposal-link";
import { resolveScenario } from "@/lib/server/queries";
import { AppShell } from "@/components/shell/app-shell";
import { DashboardAssistant } from "@/components/shell/agent-dock";

export default function AgentPage({ searchParams }: PageProps<"/app">) {
  return <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas p-8 text-ink-soft">Opening Daybreak…</div>}><Agent searchParams={searchParams} /></Suspense>;
}
async function Agent({ searchParams }: { searchParams: PageProps<"/app">["searchParams"] }) {
  const params = await searchParams;
  const user = await currentUser();
  if (!user) redirect(proposalSignInPath(parseProposalId(params.proposal)));
  await connection();
  const scenario = await resolveScenario(searchParams);
  const consoleAllowed = mayReadConsole(user);
  // The old operational plan remains a separate destination; the agent owns the main screen.
  if (consoleAllowed && (params.console === "1" || typeof params.filtru === "string")) {
    const next = new URLSearchParams({ scenariu: scenario });
    if (typeof params.filtru === "string") next.set("filtru", params.filtru);
    redirect(`/planificare?${next}`);
  }
  if (consoleAllowed && ["harta", "zona"].some((key) => typeof params[key] === "string")) {
    const next = new URLSearchParams({ scenariu: scenario });
    for (const key of ["harta", "zona", "lucrare"]) if (typeof params[key] === "string") next.set(key, params[key]);
    redirect(`/harta?${next}`);
  }
  const account = { id: user.id, email: user.email, name: user.full_name, membership: toMembership(user) };
  return <AppShell scenario={scenario} fit><DashboardAssistant account={account} scenario={scenario} presentation="main" /></AppShell>;
}
