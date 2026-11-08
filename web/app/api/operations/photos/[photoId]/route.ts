import { currentUser } from "@/lib/server/accounts";
import { forwardPhoto } from "@/lib/operations/photo-gateway";
type Context = { params: Promise<{ photoId: string }> };
async function handle(request: Request, context: Context) {
  return forwardPhoto(request, await context.params, { user: currentUser, fetch: (input, init) => fetch(input, init), base: process.env.API_BASE ?? "http://127.0.0.1:8720/api", trustedOrigin: process.env.DAYBREAK_WORKSPACE_ORIGIN, token: process.env.DAYBREAK_INTERNAL_TOKEN });
}
export const GET = handle;
export const DELETE = handle;
