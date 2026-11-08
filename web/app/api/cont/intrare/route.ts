import { originFailure } from "@/lib/operations/policy";
import { signIn, toProfile, toPublic, toMembership } from "@/lib/server/accounts";

export async function POST(request: Request) {
  const rejected = originFailure(request);
  if (rejected) return rejected;
  const { email = "", password = "" } = (await request.json().catch(() => ({}))) as { email?: string; password?: string };
  const r = await signIn(String(email), String(password));
  if (!r.user) return Response.json({ error: r.error }, { status: 401 });
  return Response.json({ user: toPublic(r.user), profile: toProfile(r.user), membership: toMembership(r.user) });
}
