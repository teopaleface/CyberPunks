import { signIn, toProfile, toPublic } from "@/lib/server/accounts";

export async function POST(request: Request) {
  const { email = "", password = "" } = (await request.json().catch(() => ({}))) as { email?: string; password?: string };
  const r = await signIn(String(email), String(password));
  if (!r.user) return Response.json({ error: r.error }, { status: 401 });
  return Response.json({ user: toPublic(r.user), profile: toProfile(r.user) });
}
