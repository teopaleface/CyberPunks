import { expect, test } from "bun:test";
import { POST } from "../../app/api/dev/provision-demo/route";
const origin = "http://127.0.0.1:3870";
const token = crypto.randomUUID();
async function gate(
  values: Record<string, string>,
  headers: Record<string, string> = {},
) {
  const next = {
    NODE_ENV: "development",
    DAYBREAK_ENABLE_DEMO_PROVISIONING: "1",
    DAYBREAK_INTERNAL_TOKEN: token,
    ...values,
  };
  const previous = Object.fromEntries(
    Object.keys(next).map((key) => [key, process.env[key]]),
  );
  Object.assign(process.env, next);
  try {
    return await POST(
      new Request(`${origin}/api/dev/provision-demo`, {
        method: "POST",
        headers: {
          host: "127.0.0.1:3870",
          origin,
          authorization: `Bearer ${token}`,
          ...headers,
        },
      }),
    );
  } finally {
    for (const [key, value] of Object.entries(previous))
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
  }
}
test("administrative provisioning and capability upgrade stay disabled in production and without the local flag", async () => {
  expect((await gate({ NODE_ENV: "production" })).status).toBe(404);
  expect((await gate({ DAYBREAK_ENABLE_DEMO_PROVISIONING: "0" })).status).toBe(
    404,
  );
});
test("a cookie or public caller cannot substitute for the internal service bearer", async () => {
  expect((await gate({}, { authorization: "" })).status).toBe(401);
  expect(
    (
      await gate(
        {},
        {
          authorization: "Bearer incorrect",
          cookie: "daybreak_operations_session=synthetic-test-cookie",
        },
      )
    ).status,
  ).toBe(401);
});
test("local administrative authorization rejects foreign origins and remote hosts/addresses", async () => {
  expect((await gate({}, { origin: "https://foreign.example" })).status).toBe(
    403,
  );
  expect((await gate({}, { host: "public.example" })).status).toBe(404);
  expect((await gate({}, { "x-forwarded-for": "192.0.2.5" })).status).toBe(404);
});
