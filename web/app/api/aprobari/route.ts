import { consoleDenied } from "@/lib/server/operations";
import { originFailure } from "@/lib/operations/policy";
/** Alegerile personale istorice nu sunt aprobări operaționale. */
export async function GET() {
  const denied = await consoleDenied();
  if (denied) return denied;
  return Response.json({ rows: [], legacy: true, message: "Personal selections are retired. Use the shared workspace to review and confirm operations." }, { headers: { "cache-control": "private, no-store" } });
}
async function retired(request: Request) {
  const rejected = originFailure(request);
  if (rejected) return rejected;
  const denied = await consoleDenied();
  return denied ?? Response.json({ error: "Prepare and confirm the action in the shared workspace.", workspace: "/workspace" }, { status: 409 });
}
export const POST = retired;
export const PUT = retired;
