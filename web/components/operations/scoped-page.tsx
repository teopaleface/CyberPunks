import { Suspense } from "react";
import { redirect } from "next/navigation";
import { connection } from "next/server";
import { currentUser, toMembership } from "@/lib/server/accounts";
import { mayReadConsole } from "@/lib/operations/policy";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";
import { AppShell } from "@/components/shell/app-shell";
import { RoleArea, type RoleSection } from "./role-area";

export type ScopedSearchParams = Promise<Record<string, string | string[] | undefined>>;
type Props = { section: RoleSection; searchParams: ScopedSearchParams; params?: Promise<{ id: string }> };
export function ScopedPage(props: Props) {
  return <Suspense fallback={<div role="status" className="p-8 text-ink-soft">Opening your workspace…</div>}><Content {...props} /></Suspense>;
}
async function Content({ section, searchParams, params }: Props) {
  const user = await currentUser();
  if (!user) redirect("/intra");
  const membership = toMembership(user);
  // These pages never reuse the global dispatcher endpoints for a restricted account.
  if ((["work", "work-detail", "route"].includes(section) && membership.role !== "technician") ||
      (section === "connections" && membership.role !== "customer")) redirect("/app");
  await connection();
  const scenario = await resolveScenario(searchParams);
  const info = mayReadConsole(user) ? (await loadShellInfo(scenario)).info : undefined;
  const id = params ? (await params).id : undefined;
  const account = { id: user.id, email: user.email, name: user.full_name, membership };
  return <AppShell info={info} scenario={scenario}><RoleArea key={`${account.id}:${scenario}:${section}:${id ?? ""}`} account={account} scenario={scenario} section={section} itemId={id} /></AppShell>;
}
