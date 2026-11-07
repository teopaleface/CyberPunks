import { Suspense } from "react";
import { redirect } from "next/navigation";
import { compatibilityAppPath } from "@/components/shell/compatibility-route";
type Search = Promise<Record<string, string | string[] | undefined>>;
export default function Page({ searchParams }: { searchParams: Search }) {
  return (
    <Suspense fallback={<main className="p-10">Opening Daybreak…</main>}>
      <CompatibilityRedirect searchParams={searchParams} />
    </Suspense>
  );
}
async function CompatibilityRedirect({ searchParams }: { searchParams: Search }) {
  return redirect(compatibilityAppPath(await searchParams));
}
