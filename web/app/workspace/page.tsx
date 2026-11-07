import { Suspense } from "react";
import { redirect } from "next/navigation";
import { currentUser, toMembership } from "@/lib/server/accounts";
import { Workspace } from "@/components/workspace/workspace";
export const metadata = { title: "Your workspace" };
export default function Page() {
  return (
    <Suspense fallback={<main className="p-10">Opening your workspace…</main>}>
      <AccountWorkspace />
    </Suspense>
  );
}
async function AccountWorkspace() {
  const user = await currentUser();
  if (!user) redirect("/intra");
  return (
    <Workspace
      account={{
        id: user.id,
        email: user.email,
        name: user.full_name,
        membership: toMembership(user),
      }}
    />
  );
}
