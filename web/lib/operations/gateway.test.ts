import { describe, expect, test } from "bun:test";
import {
  allowedPath,
  forward,
  type GatewayDependencies,
  type GatewayUser,
} from "./gateway";
import {
  actorOf,
  mayReadConsole,
  membershipOf,
  type Membership,
  type Role,
} from "./policy";
const ORIGIN = "http://127.0.0.1:3870";
function member(role: Role, userId = role): GatewayUser {
  return {
    id: userId,
    membership: {
      role,
      organization_id: "daybreak-demo",
      crew_id: role === "technician" ? "crew-1" : null,
      connection_ids: role === "customer" ? ["conn-1"] : [],
      permissions:
        role === "dispatcher" ? ["approve_plan", "view_console"] : [],
    },
  };
}
function request(
  path = "proposals",
  body: unknown = {
    action: "create_case",
    data: { connection_id: "conn-1", symptom: "Power cuts" },
    scenario: "demo-vara",
  },
  headers: Record<string, string> = {},
) {
  return new Request(`${ORIGIN}/api/operations/${path}`, {
    method: "POST",
    headers: { origin: ORIGIN, "content-type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
}
function setup(
  user: GatewayUser | null = member("customer"),
  responder?: (url: string, init?: RequestInit) => Response | Promise<Response>,
) {
  const calls: { url: string; init?: RequestInit }[] = [];
  const deps: GatewayDependencies = {
    user: async () => user,
    base: "http://127.0.0.1:8720/api",
    token: "test-only-private-token",
    fetch: (async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return responder
        ? responder(String(url), init)
        : Response.json({ proposal_id: "p-one", status: "prepared" });
    }) as typeof fetch,
  };
  return { deps, calls };
}
describe("same-origin operations API gateway", () => {
  test("rejects an anonymous caller before contacting Python", async () => {
    const { deps, calls } = setup(null);
    expect(
      (await forward(request(), "operations", ["proposals"], deps)).status,
    ).toBe(401);
    expect(calls).toHaveLength(0);
  });
  test("unbound signups cannot obtain operational context", async () => {
    const { deps, calls } = setup({ id: "new-account" });
    expect(
      (await forward(request(), "operations", ["proposals"], deps)).status,
    ).toBe(403);
    expect(calls).toHaveLength(0);
  });
  test.each(["https://attacker.test", "null", "http://127.0.0.1:3710"])(
    "rejects foreign origin %s",
    async (origin) => {
      const { deps, calls } = setup();
      expect(
        (
          await forward(
            request("proposals", {}, { origin }),
            "operations",
            ["proposals"],
            deps,
          )
        ).status,
      ).toBe(403);
      expect(calls).toHaveLength(0);
    },
  );
  test("requires an origin for a mutation and rejects cross-site fetch metadata", async () => {
    const { deps, calls } = setup();
    const input = request();
    input.headers.delete("origin");
    expect(
      (await forward(input, "operations", ["proposals"], deps)).status,
    ).toBe(403);
    expect(
      (
        await forward(
          request("proposals", {}, { "sec-fetch-site": "cross-site" }),
          "operations",
          ["proposals"],
          deps,
        )
      ).status,
    ).toBe(403);
    expect(calls).toHaveLength(0);
  });
  test.each(["customer", "technician", "dispatcher"] as Role[])(
    "uses the stored %s membership and strips all browser auth headers",
    async (role) => {
      const account = member(role);
      const { deps, calls } = setup(account);
      const response = await forward(
        request(
          "proposals",
          { action: "request_human", data: { reason: "Need help" } },
          {
            authorization: "Bearer attacker",
            "x-daybreak-actor": '{"role":"dispatcher"}',
            cookie: "private-browser-cookie",
          },
        ),
        "operations",
        ["proposals"],
        deps,
      );
      expect(response.status).toBe(200);
      expect(calls).toHaveLength(1);
      const headers = new Headers(calls[0].init?.headers);
      expect(headers.get("authorization")).toBe(
        "Bearer test-only-private-token",
      );
      expect(JSON.parse(headers.get("x-daybreak-actor")!)).toEqual(
        actorOf(account),
      );
      expect(headers.get("cookie")).toBeNull();
      expect(response.headers.get("cache-control")).toContain("no-store");
      expect(await response.text()).not.toContain("test-only-private-token");
    },
  );
  test.each([
    "actor",
    "user_id",
    "role",
    "organization_id",
    "permissions",
    "connection_ids",
    "crew_id",
  ])("rejects body identity field %s", async (key) => {
    const { deps, calls } = setup();
    expect(
      (
        await forward(
          request("proposals", { [key]: "forged" }),
          "operations",
          ["proposals"],
          deps,
        )
      ).status,
    ).toBe(422);
    expect(calls).toHaveLength(0);
  });
  test("same-origin browser context reads work without an Origin header", async () => {
    const { deps, calls } = setup();
    const response = await forward(
      new Request(`${ORIGIN}/api/operations/context?scenario=demo-vara`, {
        headers: { "sec-fetch-site": "same-origin" },
      }),
      "operations",
      ["context"],
      deps,
    );
    expect(response.status).toBe(200);
    expect(calls[0].url).toBe(
      "http://127.0.0.1:8720/api/operations/context?scenario=demo-vara",
    );
  });
  test("query identity injection and arbitrary upstream routes are refused", async () => {
    const { deps, calls } = setup();
    expect(
      (
        await forward(
          new Request(`${ORIGIN}/api/operations/context?role=dispatcher`, {
            headers: { origin: ORIGIN },
          }),
          "operations",
          ["context"],
          deps,
        )
      ).status,
    ).toBe(422);
    for (const path of [
      ["demo-bindings"],
      ["..", "run"],
      ["run"],
      ["proposals", "one", "cancel"],
      ["context?role=dispatcher"],
    ])
      expect((await forward(request(), "operations", path, deps)).status).toBe(
        404,
      );
    expect(calls).toHaveLength(0);
  });
  test("a prepared proposal never implicitly calls confirm; retries keep the same ID", async () => {
    const { deps, calls } = setup();
    await forward(request(), "operations", ["proposals"], deps);
    expect(calls.map((x) => x.url)).toEqual([
      "http://127.0.0.1:8720/api/operations/proposals",
    ]);
    for (let i = 0; i < 2; i++)
      await forward(
        request("proposals/p-one/confirm", {}),
        "operations",
        ["proposals", "p-one", "confirm"],
        deps,
      );
    expect(calls.slice(1).map((x) => x.url)).toEqual(
      Array(2).fill(
        "http://127.0.0.1:8720/api/operations/proposals/p-one/confirm",
      ),
    );
  });
  test("conversation endpoints use the same account and never accept arbitrary endpoints", async () => {
    const { deps, calls } = setup(member("technician"));
    expect(
      (
        await forward(
          request("chat", { message: "What is next?" }),
          "conversation",
          ["chat"],
          deps,
        )
      ).status,
    ).toBe(200);
    expect(
      JSON.parse(new Headers(calls[0].init?.headers).get("x-daybreak-actor")!)
        .crew_id,
    ).toBe("crew-1");
    expect(
      (await forward(request(), "conversation", ["whatsapp-send"], deps))
        .status,
    ).toBe(404);
  });
  test.each([
    "http://evil.test/api",
    "https://127.0.0.1/api",
    "http://user:password@localhost/api",
  ])("rejects non-loopback or credentialed backend %s", async (base) => {
    const { deps, calls } = setup();
    deps.base = base;
    expect(
      (await forward(request(), "operations", ["proposals"], deps)).status,
    ).toBe(503);
    expect(calls).toHaveLength(0);
  });
  test("does not fall back to demo success when the service or token is missing", async () => {
    const { deps, calls } = setup();
    deps.token = undefined;
    expect(
      (await forward(request(), "operations", ["proposals"], deps)).status,
    ).toBe(503);
    expect(calls).toHaveLength(0);
    deps.token = "test";
    deps.fetch = (() => {
      throw new Error("private upstream failure");
    }) as unknown as typeof fetch;
    const response = await forward(
      request(),
      "operations",
      ["proposals"],
      deps,
    );
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("private upstream failure");
  });
  test.each([401, 403, 404, 409, 422, 503])(
    "preserves safe domain error %s without leaking backend objects",
    async (status) => {
      const { deps } = setup(undefined, () =>
        Response.json(
          { detail: { private_account: "not-for-browser", token: "secret" } },
          { status },
        ),
      );
      const response = await forward(
        request(),
        "operations",
        ["proposals"],
        deps,
      );
      expect(response.status).toBe(status);
      expect(await response.text()).not.toContain("not-for-browser");
    },
  );
});
test("Next dev Host authority is checked without trusting forwarded hosts", async () => {
  const { deps } = setup();
  const local = new Request("http://localhost:3870/api/operations/context", {
    headers: { host: "127.0.0.1:3870", origin: ORIGIN },
  });
  expect((await forward(local, "operations", ["context"], deps)).status).toBe(
    200,
  );
  const foreign = new Request("http://localhost:3870/api/operations/context", {
    headers: {
      host: "127.0.0.1:3870",
      origin: "https://foreign.example",
      "x-forwarded-host": "foreign.example",
    },
  });
  expect((await forward(foreign, "operations", ["context"], deps)).status).toBe(
    403,
  );
});
describe("stored membership policy", () => {
  test("a profile team name cannot grant a role, crew or permissions", () => {
    const user = { id: "new", team: "Dispatcher", membership: undefined };
    expect(membershipOf(user).role).toBe("customer");
    expect(actorOf(user).connection_ids).toEqual([]);
    expect(actorOf(user).crew_id).toBeNull();
    expect(mayReadConsole(user)).toBe(false);
  });
  test("legacy users remain unbound customers and dispatcher access is scoped", () => {
    expect(actorOf({ id: "preserved-id" }).user_id).toBe("preserved-id");
    const dispatcher = member("dispatcher");
    expect(mayReadConsole(dispatcher)).toBe(true);
    expect(
      mayReadConsole({
        membership: { ...dispatcher.membership!, organization_id: "other-org" },
      }),
    ).toBe(false);
    expect(mayReadConsole(member("technician"))).toBe(false);
    expect(
      mayReadConsole({
        membership: { ...dispatcher.membership!, permissions: [] },
      }),
    ).toBe(false);
  });
  test("malformed stored membership fails closed", () => {
    expect(
      membershipOf({ membership: { role: "admin" } as unknown as Membership })
        .organization_id,
    ).toBeNull();
  });
});

test("only the exact command recovery POST is allowlisted", () => {
  expect(
    allowedPath("operations", ["commands", "cmd-one", "recover"], "POST"),
  ).toBe(true);
  for (const method of ["GET", "PUT", "DELETE"])
    expect(
      allowedPath("operations", ["commands", "cmd-one", "recover"], method),
    ).toBe(false);
  for (const path of [
    ["commands", "cmd-one", "cancel"],
    ["commands", "cmd-one", "recover", "extra"],
    ["recover"],
    ["commands", "..", "recover"],
  ])
    expect(allowedPath("operations", path, "POST")).toBe(false);
});
test("saved LLM recommendations have a preparation route with no editable action data", async () => {
  const path = ["tasks", "task-one", "recommendations", "A-20250708-PT-1182", "prepare"];
  expect(allowedPath("conversation", path, "POST")).toBe(true);
  for (const method of ["GET", "DELETE", "PUT"])
    expect(allowedPath("conversation", path, method)).toBe(false);
  expect(allowedPath("conversation", [...path, "confirm"], "POST")).toBe(false);
  const { deps, calls } = setup(member("dispatcher"));
  const send = (body: unknown) => forward(new Request(`${ORIGIN}/api/conversation/${path.join("/")}?scenario=demo-vara`, {
    method: "POST", headers: { origin: ORIGIN, "content-type": "application/json" }, body: JSON.stringify(body),
  }), "conversation", path, deps);
  expect((await send({ decision: "approve" })).status).toBe(422);
  expect(calls).toHaveLength(0);
  expect((await send({})).status).toBe(200);
  expect(calls).toHaveLength(1);
  expect(calls[0].url).toEndWith("/api/conversation/tasks/task-one/recommendations/A-20250708-PT-1182/prepare?scenario=demo-vara");
  expect(calls[0].init?.body).toBe("{}");
});
test("recovery requires a verified dispatcher permission and an explicit reason", async () => {
  for (const role of ["customer", "technician", "dispatcher"] as Role[]) {
    const { deps, calls } = setup(member(role));
    expect(
      (
        await forward(
          request("commands/cmd-one/recover", {
            decision: "cancel",
            reason: "No effect published",
          }),
          "operations",
          ["commands", "cmd-one", "recover"],
          deps,
        )
      ).status,
    ).toBe(403);
    expect(calls).toHaveLength(0);
  }
  const dispatcher = member("dispatcher");
  dispatcher.membership!.permissions.push("recover_commands");
  const { deps, calls } = setup(dispatcher);
  for (const body of [
    {},
    { decision: "cancel", reason: " " },
    { decision: "execute", reason: "Do it" },
    { decision: "cancel", reason: "Safe reason", permission: "admin" },
  ])
    expect(
      (
        await forward(
          request("commands/cmd-one/recover", body),
          "operations",
          ["commands", "cmd-one", "recover"],
          deps,
        )
      ).status,
    ).toBe(422);
  expect(calls).toHaveLength(0);
  const body = {
    decision: "cancel",
    reason: "No effect was published and the original membership was revoked.",
  };
  expect(
    (
      await forward(
        request("commands/cmd-one/recover", body),
        "operations",
        ["commands", "cmd-one", "recover"],
        deps,
      )
    ).status,
  ).toBe(200);
  expect(calls).toHaveLength(1);
  expect(calls[0].url).toBe(
    "http://127.0.0.1:8720/api/operations/commands/cmd-one/recover",
  );
  expect(JSON.parse(calls[0].init!.body as string)).toEqual(body);
  expect(
    JSON.parse(new Headers(calls[0].init!.headers).get("x-daybreak-actor")!)
      .permissions,
  ).toContain("recover_commands");
});

test("proposal lookup allows only a UUID GET and never confirms as a side effect", async () => {
  const id = "6d57ebca-af8d-4da4-afcb-3080dca9a671";
  expect(allowedPath("operations", ["proposals", id], "GET")).toBe(true);
  expect(allowedPath("operations", ["proposals", id], "POST")).toBe(false);
  for (const invalid of [
    "p-one",
    `${id}/confirm`,
    "..",
    "https://foreign.example",
    `${id}?confirm=true`,
  ])
    expect(allowedPath("operations", ["proposals", invalid], "GET")).toBe(
      false,
    );
  const { deps, calls } = setup();
  const response = await forward(
    new Request(`${ORIGIN}/api/operations/proposals/${id}`, {
      headers: { origin: ORIGIN },
    }),
    "operations",
    ["proposals", id],
    deps,
  );
  expect(response.status).toBe(200);
  expect(calls).toHaveLength(1);
  expect(calls[0].url).toBe(
    `http://127.0.0.1:8720/api/operations/proposals/${id}`,
  );
  expect(calls[0].init!.method).toBe("GET");
  expect(calls[0].init!.body).toBeUndefined();
});
test.each([403, 404, 409])(
  "linked proposal refusal %s is safe and cannot expose a foreign proposal",
  async (status) => {
    const id = "6d57ebca-af8d-4da4-afcb-3080dca9a671";
    const { deps } = setup(undefined, () =>
      Response.json(
        {
          detail: {
            private_proposal: "foreign secret",
            reason: "private actor signature",
          },
        },
        { status },
      ),
    );
    const response = await forward(
      new Request(`${ORIGIN}/api/operations/proposals/${id}`, {
        headers: { origin: ORIGIN },
      }),
      "operations",
      ["proposals", id],
      deps,
    );
    expect(response.status).toBe(status);
    const error = await response.text();
    expect(error).not.toContain("foreign secret");
    expect(error).not.toContain("private actor signature");
    if (status === 409)
      expect(error).toContain("expired or its source data changed");
  },
);

test("a failed linked-proposal read reports no confirmation and offers a read retry", async () => {
  const id = "6d57ebca-af8d-4da4-afcb-3080dca9a671";
  const { deps } = setup(undefined, () => {
    throw new Error("private upstream failure");
  });
  const response = await forward(
    new Request(`${ORIGIN}/api/operations/proposals/${id}`, {
      headers: { origin: ORIGIN },
    }),
    "operations",
    ["proposals", id],
    deps,
  );
  expect(response.status).toBe(503);
  const error = await response.text();
  expect(error).toContain("No action was confirmed");
  expect(error).not.toContain("private upstream failure");
});

 test("only explicitly pinned HTTPS origin can receive private credentials", async () => {
  const { deps, calls } = setup();
  deps.base = "https://workspace.example.test/api";
  deps.trustedOrigin = "https://workspace.example.test";
  expect((await forward(request(), "operations", ["proposals"], deps)).status).toBe(200);
  expect(calls).toHaveLength(1);
  deps.base = "https://another.example.test/api";
  expect((await forward(request(), "operations", ["proposals"], deps)).status).toBe(503);
  expect(calls).toHaveLength(1);
});

test("upstream redirects are never followed with service credentials", async () => {
  const { deps, calls } = setup();
  deps.fetch = (async (_input, init) => {
    expect(init?.redirect).toBe("manual");
    return new Response(null, { status: 302, headers: { location: "https://foreign.test/" } });
  });
  expect((await forward(request(), "operations", ["proposals"], deps)).status).toBe(503);
  expect(calls).toHaveLength(0);
});
