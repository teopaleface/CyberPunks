import { currentUser } from "@/lib/server/accounts";
import { forwardPhoto } from "@/lib/operations/photo-gateway";
export async function POST(request: Request, context: { params: Promise<{ workId: string }> }) {
  return forwardPhoto(request, await context.params, { user: currentUser, fetch, base: process.env.API_BASE ?? "http://127.0.0.1:8720/api", token: process.env.DAYBREAK_INTERNAL_TOKEN });
}
