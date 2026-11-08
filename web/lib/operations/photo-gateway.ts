import { actorOf, membershipOf, validOrigin } from "./policy";
import { backendUrl, fail, type GatewayDependencies } from "./gateway";

const PHOTO_ID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
const WORK_ID = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$/;
export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
const MIME = new Set(["image/jpeg", "image/png", "image/webp"]);
const PRIVATE = { "cache-control": "private, no-store", vary: "Cookie", "x-content-type-options": "nosniff" };

/** Enforce the limit while reading, including requests without Content-Length. */
export async function limitedBytes(stream: ReadableStream<Uint8Array> | null, limit: number): Promise<Uint8Array> {
  if (!stream) return new Uint8Array();
  const reader = stream.getReader(), chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      size += next.value.byteLength;
      if (size > limit) { await reader.cancel(); throw new RangeError("Image too large"); }
      chunks.push(next.value);
    }
  } finally { reader.releaseLock(); }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) { result.set(chunk, offset); offset += chunk.byteLength; }
  return result;
}
export async function forwardPhoto(request: Request, item: { photoId: string } | { workId: string }, deps: GatewayDependencies): Promise<Response> {
  const user = await deps.user();
  if (!user) return fail(401, "Sign in to view or add photos.");
  const membership = membershipOf(user);
  if (!membership.organization_id || !["technician", "dispatcher"].includes(membership.role)) return fail(403, "Photos are available only to the authorized field team and dispatcher.");
  if (!validOrigin(request)) return fail(403, "This request must come from this site.");
  const upload = "workId" in item;
  if ((upload && (!WORK_ID.test(item.workId) || request.method !== "POST")) ||
      (!upload && (!PHOTO_ID.test(item.photoId) || !["GET", "DELETE"].includes(request.method)))) return fail(404, "Photo endpoint unavailable.");
  if (request.method !== "GET" && membership.role !== "technician") return fail(403, "Only the assigned technician can add or remove draft photos.");
  const query = new URL(request.url).searchParams;
  if ([...query.keys()].some((key) => key !== "scenario") || query.getAll("scenario").length > 1) return fail(422, "Invalid photo request.");
  const scenario = query.get("scenario") ?? "demo-vara";
  if (!/^[a-z0-9][a-z0-9_-]{0,63}$/.test(scenario)) return fail(422, "Invalid scenario.");
  if (!deps.token) return fail(503, "The photo service is not configured.");
  const mime = request.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase() ?? "";
  if (upload && !MIME.has(mime)) return fail(415, "Choose a JPG, PNG or WebP photo.");
  if (upload && Number(request.headers.get("content-length")) > MAX_PHOTO_BYTES) return fail(413, "Each photo must be 5 MB or smaller.");
  let body: Uint8Array | undefined;
  try { if (upload) body = await limitedBytes(request.body, MAX_PHOTO_BYTES); }
  catch (issue) { return fail(issue instanceof RangeError ? 413 : 422, "The photo could not be read. Choose a file of 5 MB or less."); }
  if (upload && !body?.length) return fail(422, "Choose a photo to upload.");
  let target: URL;
  try {
    target = backendUrl(deps.base, upload ? `/operations/work-items/${encodeURIComponent(item.workId)}/photos` : `/operations/photos/${item.photoId}`);
    target.searchParams.set("scenario", scenario);
  } catch { return fail(503, "The photo service is not configured."); }
  try {
    const response = await deps.fetch(target, { method: request.method, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(30000),
      headers: { authorization: `Bearer ${deps.token}`, "x-daybreak-actor": JSON.stringify(actorOf(user)), ...(upload ? { "content-type": mime } : {}) },
      ...(body ? { body: body as BodyInit } : {}) });
    if (!response.ok) {
      const status = [401, 403, 404, 409, 413, 415, 422, 429].includes(response.status) ? response.status : 503;
      const messages: Record<number, string> = { 401: "Your session ended. Sign in again.", 403: "This photo is outside your current assignment.", 404: "This photo or work item is unavailable.", 409: "This photo is already linked to a review or finding. It cannot be deleted.", 413: "Each photo must be 5 MB or smaller.", 415: "Choose a valid JPG, PNG or WebP photo.", 422: "This image could not be accepted. Choose a valid JPG, PNG or WebP photo.", 429: "Too many draft photos. Remove an unused draft or try again later.", 503: "The photo service could not complete the request." };
      if (status === 409 && upload) {
        let code = "";
        try {
          const detail = JSON.parse(new TextDecoder().decode(await limitedBytes(response.body, 8000)));
          code = typeof detail?.detail?.code === "string" ? detail.detail.code : "";
        } catch { /* Never surface private upstream diagnostics. */ }
        return fail(409, code === "photo_quota"
          ? "You have reached the limit of 20 active draft photos. Remove unused photos from open finding forms, or wait for abandoned drafts to expire after 24 hours."
          : "This photo could not be added to the current work. Refresh your assigned work and try again.");
      }
      await response.body?.cancel();
      return fail(status, messages[status]);
    }
    if (request.method === "GET") {
      const type = response.headers.get("content-type")?.split(";", 1)[0] ?? "";
      if (!MIME.has(type)) return fail(503, "The photo service returned an invalid image.");
      const bytes = await limitedBytes(response.body, 8 * 1024 * 1024);
      return new Response(bytes as BodyInit, { headers: { ...PRIVATE, "content-type": type, "content-disposition": 'inline; filename="finding-photo"' } });
    }
    if (response.status === 204) return new Response(null, { status: 204, headers: PRIVATE });
    const payload = JSON.parse(new TextDecoder().decode(await limitedBytes(response.body, 32000)));
    return Response.json(payload, { status: response.status, headers: PRIVATE });
  } catch { return fail(503, "The photo request did not complete. Check your draft before trying again."); }
}
