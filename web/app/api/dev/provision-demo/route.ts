import { timingSafeEqual } from "node:crypto";
import { provisionDemoAccounts } from "@/lib/server/accounts";
import { backendUrl, fail } from "@/lib/operations/gateway";
import { validOrigin, type Role } from "@/lib/operations/policy";
let provisioning = false;
/** Activare exclusiv locală. Parolele sunt furnizate independent prin mediul privat de pornire. */
export async function POST(request: Request) {
  const host = new URL(
    `http://${request.headers.get("host") ?? new URL(request.url).host}`,
  ).hostname;
  if (
    process.env.NODE_ENV !== "development" ||
    process.env.DAYBREAK_ENABLE_DEMO_PROVISIONING !== "1" ||
    !["127.0.0.1", "localhost", "[::1]"].includes(host) ||
    (request.headers
      .get("x-forwarded-for")
      ?.split(",")
      .some(
        (address) =>
          !["127.0.0.1", "::1", "::ffff:127.0.0.1"].includes(address.trim()),
      ) ??
      false)
  )
    return fail(404, "Not found.");
  if (!validOrigin(request)) return fail(403, "Use this local site's origin.");
  const expected = `Bearer ${process.env.DAYBREAK_INTERNAL_TOKEN ?? ""}`;
  const provided = request.headers.get("authorization") ?? "";
  if (
    !process.env.DAYBREAK_INTERNAL_TOKEN ||
    Buffer.byteLength(expected) !== Buffer.byteLength(provided) ||
    !timingSafeEqual(Buffer.from(expected), Buffer.from(provided))
  )
    return fail(401, "Local provisioning requires service authorization.");
  if (provisioning) return fail(409, "Provisioning is already in progress.");
  provisioning = true;
  try {
    const response = await fetch(
      backendUrl(
        process.env.API_BASE ?? "http://127.0.0.1:8720/api",
        "/operations/demo-bindings",
      ),
      {
        cache: "no-store",
        redirect: "error",
        signal: AbortSignal.timeout(30000),
        headers: {
          authorization: expected,
          "x-daybreak-actor": JSON.stringify({
            user_id: "demo-provisioner",
            role: "dispatcher",
            organization_id: "daybreak-demo",
            crew_id: null,
            connection_ids: [],
            permissions: ["approve_plan", "review_work_item", "create_case"],
          }),
        },
      },
    );
    if (!response.ok)
      return fail(
        503,
        "Cannot verify demo account assignments with the operations service.",
      );
    const binding = (await response.json()) as {
      connection_id?: string;
      connection_ids?: string[];
      crew_id?: string;
    };
    binding.connection_id ??= binding.connection_ids?.[0];
    if (!binding.connection_id || !binding.crew_id)
      return fail(
        503,
        "The operations service did not return a complete demo assignment.",
      );
    const roles: Role[] = ["customer", "technician", "dispatcher"];
    const inputs = roles.map((role) => ({
      email:
        process.env[`DAYBREAK_DEMO_${role.toUpperCase()}_EMAIL`] ??
        `demo-${role}@daybreak.local`,
      password:
        process.env[`DAYBREAK_DEMO_${role.toUpperCase()}_PASSWORD`] ?? "",
      membership: {
        role,
        organization_id: "daybreak-demo",
        crew_id: role === "technician" ? binding.crew_id! : null,
        connection_ids: role === "customer" ? [binding.connection_id!] : [],
        permissions:
          role === "dispatcher"
            ? [
                "approve_plan",
                "review_work_item",
                "create_case",
                "view_console",
              ]
            : [],
      },
    }));
    const users = await provisionDemoAccounts(inputs);
    return Response.json(
      { users, synthetic: true },
      { headers: { "cache-control": "no-store" } },
    );
  } catch (error) {
    if (
      error instanceof Error &&
      /already exists|unique emails|exactly three/.test(error.message)
    )
      return fail(409, error.message);
    return fail(
      503,
      "Local account provisioning could not complete. Existing accounts have not been overwritten.",
    );
  } finally {
    provisioning = false;
  }
}
