import { parseProposalId } from "./proposal-link";
import { actorOf, membershipOf, validOrigin, type Membership } from "./policy";
export interface GatewayUser {
  id: string;
  membership?: Membership;
}
export interface GatewayDependencies {
  user: () => Promise<GatewayUser | null>;
  fetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
  base: string;
  token?: string;
  trustedOrigin?: string;
}
const PRIVATE = {
  "cache-control": "private, no-store",
  vary: "Cookie",
  "x-content-type-options": "nosniff",
};
export function fail(status: number, error: string): Response {
  return Response.json({ error }, { status, headers: PRIVATE });
}
export function allowedPath(
  kind: "operations" | "conversation",
  path: string[],
  method: string,
): boolean {
  if (path.some((p) => !/^[A-Za-z0-9_-]{1,160}$/.test(p))) return false;
  const p = path.join("/");
  if (kind === "conversation")
    return (method === "POST" && (["chat", "voice-session", "tasks"].includes(p) || /^tasks\/[A-Za-z0-9_-]+\/resume$/.test(p) || /^tasks\/[A-Za-z0-9_-]+\/recommendations\/[A-Za-z0-9_-]+\/prepare$/.test(p))) ||
      (method === "GET" && /^tasks\/[A-Za-z0-9_-]+$/.test(p));
  return (
    (method === "GET" &&
      (p === "context" ||
        /^commands\/[A-Za-z0-9_-]+$/.test(p) ||
        (path.length === 2 &&
          path[0] === "proposals" &&
          parseProposalId(path[1]) !== null))) ||
    (method === "POST" &&
      (p === "proposals" ||
        /^proposals\/[A-Za-z0-9_-]+\/confirm$/.test(p) ||
        /^commands\/[A-Za-z0-9_-]+\/recover$/.test(p)))
  );
}
export function backendUrl(base: string, path: string, trustedOrigin?: string): URL {
  const url = new URL(base.replace(/\/+$/, "") + path);
  const loopback = url.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
  let trusted = false;
  if (trustedOrigin) {
    const origin = new URL(trustedOrigin);
    trusted = origin.protocol === "https:" && origin.origin === trustedOrigin &&
      !origin.username && !origin.password && url.origin === origin.origin &&
      !["127.0.0.1", "localhost", "[::1]"].includes(origin.hostname);
  }
  if ((!loopback && !trusted) || url.username || url.password || url.hash ||
      !url.pathname.startsWith("/api/")) throw new Error("Configured private backend required");
  return url;
}
export async function forward(
  request: Request,
  kind: "operations" | "conversation",
  path: string[],
  deps: GatewayDependencies,
): Promise<Response> {
  const user = await deps.user();
  if (!user) return fail(401, "Sign in to continue.");
  if (!membershipOf(user).organization_id)
    return fail(
      403,
      "Your account has no verified service connection. Ask your administrator to link it.",
    );
  if (!validOrigin(request))
    return fail(403, "This request must come from this site.");
  if (!allowedPath(kind, path, request.method))
    return fail(404, "Endpoint not available.");
  const isProposalRead =
    kind === "operations" &&
    path[0] === "proposals" &&
    path.length === 2 &&
    request.method === "GET";
  const isRecovery =
    kind === "operations" &&
    path[0] === "commands" &&
    path[2] === "recover" &&
    request.method === "POST";
  const isRecommendation = kind === "conversation" && path[0] === "tasks" &&
    path[2] === "recommendations" && path[4] === "prepare";
  if (
    isRecovery &&
    (membershipOf(user).role !== "dispatcher" ||
      !membershipOf(user).permissions.includes("recover_commands"))
  )
    return fail(403, "Explicit dispatcher recovery permission is required.");
  if (!deps.token)
    return fail(
      503,
      "The operations service is not configured. No action was sent.",
    );
  let target: URL;
  try {
    target = backendUrl(deps.base, `/${kind}/${path.join("/")}`, deps.trustedOrigin);
  } catch {
    return fail(503, "The operations service is not configured.");
  }
  const input = new URL(request.url);
  // Neacceptarea parametrilor arbitrari împiedică trecerea unei identități/scop alternativ.
  if (request.method === "GET" || (kind === "conversation" && path[0] === "tasks")) {
    if ([...input.searchParams.keys()].some((k) => k !== "scenario"))
      return fail(422, "Unsupported query parameter.");
    const scenario = input.searchParams.get("scenario");
    if (scenario) {
      if (!/^[A-Za-z0-9_-]{1,64}$/.test(scenario))
        return fail(422, "Invalid scenario.");
      target.searchParams.set("scenario", scenario);
    }
  }
  let body: string | undefined;
  if (request.method === "POST") {
    if (!request.headers.get("content-type")?.includes("application/json"))
      return fail(415, "Send JSON data.");
    body = await request.text();
    if (body.length > 65000) return fail(413, "The message is too large.");
    try {
      const data = JSON.parse(body);
      if (!data || typeof data !== "object" || Array.isArray(data))
        return fail(422, "Expected a JSON object.");
      if (isRecommendation && Object.keys(data).length)
        return fail(422, "A saved recommendation cannot be changed in this request.");
      if (
        [
          "actor",
          "user_id",
          "role",
          "organization_id",
          "crew_id",
          "connection_ids",
          "permissions",
        ].some((k) => k in data)
      )
        return fail(422, "Account identity cannot be supplied in a request.");
      if (
        isRecovery &&
        (Object.keys(data).some(
          (key) => !["decision", "reason"].includes(key),
        ) ||
          data.decision !== "cancel" ||
          typeof data.reason !== "string" ||
          data.reason.trim().length < 3 ||
          data.reason.length > 2000)
      )
        return fail(
          422,
          "Provide an explicit cancellation and a reason of 3 to 2000 characters.",
        );
    } catch {
      return fail(422, "Invalid JSON.");
    }
  }
  try {
    const response = await deps.fetch(target, {
      method: request.method,
      cache: "no-store",
      redirect: "manual",
      signal: AbortSignal.timeout(kind === "conversation" ? 125000 : 30000),
      headers: {
        "content-type": "application/json",
        accept: "application/json",
        authorization: `Bearer ${deps.token}`,
        "x-daybreak-actor": JSON.stringify(actorOf(user)),
      },
      body,
    });
    // Erorile interne, inclusiv excepțiile Python și datele de validare, nu ies către browser.
    if (!response.ok) {
      const messages: Record<number, string> = {
        401: "Your session is no longer authorized. Sign in again.",
        403: "This action is outside your account's permissions.",
        404: isProposalRead
          ? "This proposal is unavailable for your account. Open your workspace to prepare a new proposal."
          : "This item was not found in your account.",
        409: isProposalRead
          ? "This proposal has expired or its source data changed. Prepare a new proposal in the workspace."
          : isRecovery
            ? "Command recovery changed or is unavailable. Refresh pending commands before trying again."
            : "This proposal has expired or the data changed. Refresh and prepare it again.",
        422: "Some details are missing or invalid. Review your request.",
        429: "Too many requests. Please wait and try again.",
        503: "The service is unavailable. No success has been confirmed.",
      };
      return fail(
        messages[response.status] ? response.status : 503,
        messages[response.status] ??
          "The service could not complete the request.",
      );
    }
    if (!response.headers.get("content-type")?.includes("application/json")) {
      await response.body?.cancel();
      return fail(503, "The service returned an invalid result.");
    }
    // The authenticated backend already scopes this JSON. Stream it without
    // parsing and serializing the full operational context again at the edge.
    return new Response(response.body, { headers: { ...PRIVATE, "content-type": "application/json" } });
  } catch {
    return fail(
      503,
      isProposalRead
        ? "The proposal could not be loaded. No action was confirmed. Retry opening the link or use your workspace."
        : "The service did not return a result. Confirming the same proposal again will recover its saved command without duplicating it.",
    );
  }
}
