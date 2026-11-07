import { originFailure } from "@/lib/operations/policy";
import { currentUser, saveProfile, toProfile, toPublic, toMembership } from "@/lib/server/accounts";

/** Cine e conectat (sau null) și profilul lui; PATCH salvează numele și echipa. */
export async function GET() {
  const user = await currentUser();
  return Response.json(user ? { user: toPublic(user), profile: toProfile(user), membership: toMembership(user) } : { user: null, profile: null }, { headers: { "cache-control": "no-store" } });
}

export async function PATCH(request: Request) {
  const rejected = originFailure(request);
  if (rejected) return rejected;
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont ca să îți salvezi profilul." }, { status: 401 });
  const body = (await request.json().catch(() => ({}))) as { full_name?: string | null; team?: string | null };
  if (!body || typeof body !== "object" || Object.keys(body).some(k => !["full_name", "team"].includes(k)) || Object.values(body).some(v => v !== null && typeof v !== "string")) return Response.json({ error: "Only your name and profile team can be edited." }, { status: 422 });
  const next = await saveProfile(user, body);
  return Response.json({ profile: toProfile(next) });
}
