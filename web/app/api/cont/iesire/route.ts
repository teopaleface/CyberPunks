import { originFailure } from "@/lib/operations/policy";
import { signOut } from "@/lib/server/accounts";

export async function POST(request: Request) {
  const rejected = originFailure(request);
  if (rejected) return rejected;
  await signOut();
  return Response.json({ ok: true });
}
