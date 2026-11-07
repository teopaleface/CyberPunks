import { signUp, toProfile, toPublic } from "@/lib/server/accounts";

/** Cont nou, activ imediat (fără confirmare pe email), și conectare. */
export async function POST(request: Request) {
  const { email = "", password = "", full_name = "" } = (await request.json().catch(() => ({}))) as { email?: string; password?: string; full_name?: string };
  const r = await signUp(String(email), String(password), String(full_name));
  if (!r.user) return Response.json({ error: r.error }, { status: 400 });
  return Response.json({ user: toPublic(r.user), profile: toProfile(r.user) });
}
