import "server-only";
import { redirect } from "next/navigation";
import { currentUser } from "./accounts";
import { mayReadConsole } from "../operations/policy";
import { forward } from "../operations/gateway";
export async function requireConsole(): Promise<void> {
  const user = await currentUser();
  if (!user) redirect("/intra");
  if (!mayReadConsole(user)) redirect("/app");
}
export async function consoleDenied(): Promise<Response | null> {
  const user = await currentUser();
  if (!user)
    return Response.json({ error: "Sign in to continue." }, { status: 401 });
  if (!mayReadConsole(user))
    return Response.json(
      { error: "This console is restricted to authorized dispatchers." },
      { status: 403 },
    );
  return null;
}
export function proxy(
  request: Request,
  kind: "operations" | "conversation",
  path: string[],
) {
  return forward(request, kind, path, {
    user: currentUser,
    fetch,
    base: process.env.API_BASE ?? "http://127.0.0.1:8720/api",
    token: process.env.DAYBREAK_INTERNAL_TOKEN,
  });
}
