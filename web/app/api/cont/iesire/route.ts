import { signOut } from "@/lib/server/accounts";

export async function POST() {
  await signOut();
  return Response.json({ ok: true });
}
