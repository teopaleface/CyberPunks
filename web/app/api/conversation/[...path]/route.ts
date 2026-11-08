import { proxy } from "@/lib/server/operations";
type Context = { params: Promise<{ path: string[] }> };
export async function POST(request: Request, context: Context) {
  return proxy(request, "conversation", (await context.params).path);
}

export async function GET(request: Request, context: Context) {
  return proxy(request, "conversation", (await context.params).path);
}
