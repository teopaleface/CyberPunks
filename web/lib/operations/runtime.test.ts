import { afterAll, describe, expect, test } from "bun:test";
const origin = process.env.DAYBREAK_TEST_ORIGIN;
const roles = ["customer", "technician", "dispatcher"] as const;
const jars = new Map<string, string>();
const ids = new Map<string, string>();
async function request(
  path: string,
  role?: string,
  method = "GET",
  body?: unknown,
  crossOrigin?: string,
) {
  return fetch(`${origin}/api/${path}`, {
    method,
    redirect: "manual",
    headers: {
      origin: crossOrigin ?? origin!,
      "content-type": "application/json",
      ...(role && jars.get(role) ? { cookie: jars.get(role)! } : {}),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
}
describe.skipIf(!origin)("private local runtime account/API seams", () => {
  test("three accounts log in with independent session cookies and verified roles", async () => {
    if (origin !== "http://127.0.0.1:3870")
      throw new Error("Runtime tests are restricted to local port 3870.");
    for (const role of roles) {
      const key = role.toUpperCase();
      const email = process.env[`DAYBREAK_DEMO_${key}_EMAIL`];
      const password = process.env[`DAYBREAK_DEMO_${key}_PASSWORD`];
      if (!email || !password)
        throw new Error(
          "Load the private runtime environment before this test.",
        );
      const response = await request("cont/intrare", undefined, "POST", {
        email,
        password,
      });
      expect(response.status).toBe(200);
      const cookie = response.headers.get("set-cookie")?.split(";")[0];
      expect(Boolean(cookie)).toBe(true);
      jars.set(role, cookie!);
      const result = await response.json();
      expect(result.membership.role).toBe(role);
      ids.set(role, result.user.id);
      expect(Object.keys(result.user).sort()).toEqual(["email", "id"]);
      expect(JSON.stringify(result)).not.toContain(password);
    }
    expect(new Set(jars.values()).size).toBe(3);
    expect(new Set(ids.values()).size).toBe(3);
  });
  test("each context is scoped before data reaches the browser", async () => {
    for (const role of roles) {
      const response = await request(
        "operations/context?scenario=demo-vara",
        role,
      );
      expect(response.status).toBe(200);
      const data = await response.json();
      expect(data.actor.user_id).toBe(ids.get(role));
      expect(data.actor.role).toBe(role);
      expect(data.plan.source).toBe("local_run");
      if (role === "customer") {
        expect(data.work_items).toHaveLength(0);
        expect(data.plan.routes).toBeUndefined();
        expect(
          data.connections.map(
            (c: { connection_id: string }) => c.connection_id,
          ),
        ).toEqual(["CONN-DEMO-001"]);
      }
      if (role === "technician") {
        expect(
          data.plan.routes.every(
            (r: { crew_id: string }) => r.crew_id === data.actor.crew_id,
          ),
        ).toBe(true);
        expect(data.work_items.length).toBeGreaterThan(0);
      }
    }
  });
  test("profile fields and request actor cannot promote a customer", async () => {
    expect(
      (
        await request("cont", "customer", "PATCH", {
          role: "dispatcher",
          team: "Dispatcher",
        })
      ).status,
    ).toBe(422);
    const response = await request("cont", "customer");
    expect((await response.json()).membership.role).toBe("customer");
    expect(
      (
        await request("operations/proposals", "customer", "POST", {
          actor: { role: "dispatcher" },
          action: "approve_plan",
          data: {},
        })
      ).status,
    ).toBe(422);
  });
  test("legacy private exports and approvals reject customer and technician accounts", async () => {
    for (const role of ["customer", "technician"]) {
      for (const path of ["../jurnal/descarca", "../ordine/E-BV-3", "aprobari"])
        expect((await request(path, role)).status).toBe(403);
      expect(
        (
          await request("aprobari", role, "PUT", {
            post_id: "PT-1182",
            decision: "approved",
          })
        ).status,
      ).toBe(403);
    }
    expect(
      (
        await request("aprobari", "dispatcher", "PUT", {
          post_id: "PT-1182",
          decision: "approved",
        })
      ).status,
    ).toBe(409);
  });
  test("a foreign origin cannot mutate or read scoped operations", async () => {
    expect(
      (
        await request(
          "cont/iesire",
          "customer",
          "POST",
          {},
          "https://foreign.example",
        )
      ).status,
    ).toBe(403);
    expect(
      (
        await request(
          "operations/context",
          "customer",
          "GET",
          undefined,
          "https://foreign.example",
        )
      ).status,
    ).toBe(403);
  });
  test("logging out one account revokes only that cookie", async () => {
    expect((await request("cont/iesire", "customer", "POST", {})).status).toBe(
      200,
    );
    expect((await request("operations/context", "customer")).status).toBe(401);
    for (const role of ["technician", "dispatcher"])
      expect((await request("operations/context", role)).status).toBe(200);
  });
  afterAll(async () => {
    for (const role of ["technician", "dispatcher"])
      if (jars.has(role)) await request("cont/iesire", role, "POST", {});
  });
});
