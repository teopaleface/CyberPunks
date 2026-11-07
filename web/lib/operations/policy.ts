/** Identitatea operațională vine exclusiv din contul salvat de server. */
export type Role = "customer" | "technician" | "dispatcher";
export interface Membership {
  role: Role;
  organization_id: string | null;
  crew_id: string | null;
  connection_ids: string[];
  permissions: string[];
}
export interface Actor extends Omit<Membership, "organization_id"> {
  user_id: string;
  organization_id: string;
}
export const unboundCustomer = (): Membership => ({
  role: "customer",
  organization_id: null,
  crew_id: null,
  connection_ids: [],
  permissions: [],
});
export function membershipOf(user: { membership?: Membership }): Membership {
  const m = user.membership;
  if (
    !m ||
    !["customer", "technician", "dispatcher"].includes(m.role) ||
    typeof m.organization_id !== "string" ||
    !m.organization_id ||
    !Array.isArray(m.connection_ids) ||
    !Array.isArray(m.permissions)
  )
    return unboundCustomer();
  return {
    role: m.role,
    organization_id: m.organization_id,
    crew_id: m.crew_id ?? null,
    connection_ids: m.connection_ids.filter((x) => typeof x === "string"),
    permissions: m.permissions.filter((x) => typeof x === "string"),
  };
}
export function actorOf(user: { id: string; membership?: Membership }): Actor {
  const m = membershipOf(user);
  return {
    ...m,
    user_id: user.id,
    organization_id: m.organization_id ?? `unbound:${user.id}`,
  };
}
export function mayReadConsole(user: { membership?: Membership }): boolean {
  const m = membershipOf(user);
  // Consola veche citește întregul scenariu sintetic. Alte organizații folosesc numai API-ul filtrat.
  return (
    m.role === "dispatcher" &&
    m.organization_id === "daybreak-demo" &&
    m.permissions.includes("view_console")
  );
}
export function validOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  const site = request.headers.get("sec-fetch-site");
  if (!origin && request.method === "GET") return site === "same-origin";
  if (!origin || (site && site !== "same-origin" && site !== "none"))
    return false;
  try {
    // Next dev normalizează request.url la localhost. Host este autoritatea cererii browserului;
    // browserul nu poate falsifica Host pentru o cerere cross-origin. Nu folosim X-Forwarded-Host.
    const target = new URL(request.url);
    const host = request.headers.get("host");
    if (host) target.host = host;
    return new URL(origin).origin === target.origin;
  } catch {
    return false;
  }
}
export function originFailure(request: Request): Response | null {
  return validOrigin(request)
    ? null
    : Response.json(
        { error: "This request must come from this site." },
        { status: 403, headers: { "cache-control": "no-store" } },
      );
}
