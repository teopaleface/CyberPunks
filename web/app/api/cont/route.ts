import { currentUser, saveProfile, toProfile, toPublic } from "@/lib/server/accounts";

/** Cine e conectat (sau null) și profilul lui; PATCH salvează numele și echipa. */
export async function GET() {
  const user = await currentUser();
  return Response.json(user ? { user: toPublic(user), profile: toProfile(user) } : { user: null, profile: null }, { headers: { "cache-control": "no-store" } });
}

export async function PATCH(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont ca să îți salvezi profilul." }, { status: 401 });
  const body = (await request.json().catch(() => ({}))) as { full_name?: string | null; team?: string | null };
  const next = await saveProfile(user, body);
  return Response.json({ profile: toProfile(next) });
}
