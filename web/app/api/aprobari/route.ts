import { currentUser, readApprovals, writeApprovals, type ApprovalRow } from "@/lib/server/accounts";

const VERDICTS = new Set(["approved", "deferred", "rejected"]);

/** Deciziile contului conectat pe cazurile „decide un om” din site. */
export async function GET() {
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont." }, { status: 401 });
  return Response.json({ rows: await readApprovals(user.id) }, { headers: { "cache-control": "no-store" } });
}

/** Un caz: { post_id, decision | null, crew_id? } (decision null șterge decizia). */
export async function PUT(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont." }, { status: 401 });
  const b = (await request.json().catch(() => ({}))) as { post_id?: string; decision?: string | null; crew_id?: string | null };
  const postId = String(b.post_id ?? "").slice(0, 80);
  if (!postId) return Response.json({ error: "Lipsește cazul." }, { status: 400 });
  const rows = (await readApprovals(user.id)).filter((r) => r.post_id !== postId);
  if (b.decision && VERDICTS.has(b.decision)) {
    rows.push({ post_id: postId, decision: b.decision as ApprovalRow["decision"], crew_id: b.decision === "approved" ? (b.crew_id ?? null) : null });
  }
  await writeApprovals(user.id, rows);
  return Response.json({ rows });
}

/** Toată lista: { ids } aprobate, restul șterse. */
export async function POST(request: Request) {
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont." }, { status: 401 });
  const b = (await request.json().catch(() => ({}))) as { ids?: string[] };
  const rows: ApprovalRow[] = (b.ids ?? []).map((id) => ({ post_id: String(id).slice(0, 80), decision: "approved", crew_id: null }));
  await writeApprovals(user.id, rows);
  return Response.json({ rows });
}
