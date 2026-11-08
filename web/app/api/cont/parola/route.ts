import { originFailure } from "@/lib/operations/policy";
import { currentUser, setPassword } from "@/lib/server/accounts";

/** Parolă nouă pentru contul conectat (fără email de resetare). */
export async function POST(request: Request) {
  const rejected = originFailure(request);
  if (rejected) return rejected;
  const user = await currentUser();
  if (!user) return Response.json({ error: "Intră în cont ca să schimbi parola." }, { status: 401 });
  const { password = "" } = (await request.json().catch(() => ({}))) as { password?: string };
  const error = await setPassword(user, String(password));
  return error ? Response.json({ error }, { status: 400 }) : Response.json({ ok: true });
}
