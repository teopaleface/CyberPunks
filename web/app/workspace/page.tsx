import { Suspense } from "react";
import { redirect } from "next/navigation";
import { currentUser, toMembership } from "@/lib/server/accounts";
import {
  parseProposalId,
  proposalSignInPath,
} from "@/lib/operations/proposal-link";
import { Workspace } from "@/components/workspace/workspace";
export const metadata = { title: "Your workspace" };
type Search = Promise<Record<string, string | string[] | undefined>>;
export default function Page({ searchParams }: { searchParams: Search }) {
  return (
    <Suspense fallback={<main className="p-10">Opening your workspace…</main>}>
      <AccountWorkspace searchParams={searchParams} />
    </Suspense>
  );
}
async function AccountWorkspace({ searchParams }: { searchParams: Search }) {
  const query = await searchParams;
  const proposalId = parseProposalId(query.proposal);
  const user = await currentUser();
  if (!user) redirect(proposalSignInPath(proposalId));
  return (
    <Workspace
      key={`${user.id}:${proposalId ?? (query.proposal === undefined ? "workspace" : "invalid-proposal")}`}
      linkedProposalId={proposalId}
      initialError={
        query.proposal !== undefined && !proposalId
          ? "This proposal link is invalid. Open your workspace to prepare a new proposal."
          : undefined
      }
      account={{
        id: user.id,
        email: user.email,
        name: user.full_name,
        membership: toMembership(user),
      }}
    />
  );
}
