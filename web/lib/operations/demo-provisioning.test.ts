import { describe, expect, test } from "bun:test";
import { DEMO_DISPATCHER_PERMISSIONS } from "./demo-permissions";
import {
  provisionDemoAccountsInStore,
  type DemoAccountInput,
  type KV,
  type StoredUser,
} from "../server/accounts";
function fixture() {
  const records = new Map<string, string>();
  const writes: string[] = [];
  const store: KV = {
    get: async (key) => records.get(key) ?? null,
    put: async (key, value) => {
      writes.push(key);
      records.set(key, value);
    },
    delete: async (key) => {
      records.delete(key);
    },
  };
  const inputs: DemoAccountInput[] = (
    ["customer", "technician", "dispatcher"] as const
  ).map((role) => ({
    email: `synthetic-${role}@example.test`,
    password: `${crypto.randomUUID()}${crypto.randomUUID()}`,
    membership: {
      role,
      organization_id: "daybreak-demo",
      crew_id: role === "technician" ? "test-crew" : null,
      connection_ids: role === "customer" ? ["test-connection"] : [],
      permissions:
        role === "dispatcher" ? [...DEMO_DISPATCHER_PERMISSIONS] : [],
    },
  }));
  return { records, writes, store, inputs };
}
async function legacyFixture() {
  const f = fixture();
  const users = await provisionDemoAccountsInStore(f.store, f.inputs);
  const dispatcherId = users[2].id;
  const old = JSON.parse(f.records.get(`u:${dispatcherId}`)!) as StoredUser;
  old.membership!.permissions = old.membership!.permissions.filter(
    (x) => x !== "recover_commands",
  );
  f.records.set(`u:${dispatcherId}`, JSON.stringify(old));
  f.writes.length = 0;
  return { ...f, users, dispatcherId };
}
describe("credential-verified local synthetic capability upgrade", () => {
  test("new synthetic dispatcher gets explicit recovery permission", async () => {
    const f = fixture();
    const users = await provisionDemoAccountsInStore(f.store, f.inputs);
    expect(users[2].membership.permissions).toEqual(
      DEMO_DISPATCHER_PERMISSIONS,
    );
    expect(users[0].membership.permissions).toEqual([]);
    expect(users[1].membership.permissions).toEqual([]);
    for (const input of f.inputs)
      expect(JSON.stringify([...f.records.values()])).not.toContain(
        input.password,
      );
  });
  test("adds only recover_commands, preserves IDs, credentials, other accounts and audit", async () => {
    const f = await legacyFixture();
    const before = new Map(f.records);
    const users = await provisionDemoAccountsInStore(f.store, f.inputs);
    expect(users.map((u) => u.id)).toEqual(f.users.map((u) => u.id));
    expect(f.writes).toEqual([`u:${f.dispatcherId}`]);
    const previous = JSON.parse(before.get(`u:${f.dispatcherId}`)!);
    const current = JSON.parse(f.records.get(`u:${f.dispatcherId}`)!);
    expect({
      ...current,
      membership: previous.membership,
      capability_grants: undefined,
    }).toEqual({ ...previous, capability_grants: undefined });
    expect(current.membership.permissions).toEqual([
      ...previous.membership.permissions,
      "recover_commands",
    ]);
    expect(current.capability_grants).toHaveLength(1);
    expect(current.capability_grants[0]).toMatchObject({
      permission: "recover_commands",
      source: "local_demo_provisioning",
      credentials_verified: true,
    });
    expect(
      Number.isNaN(Date.parse(current.capability_grants[0].granted_at)),
    ).toBe(false);
    for (const [key, value] of before)
      if (key !== `u:${f.dispatcherId}`) expect(f.records.get(key)).toBe(value);
    f.writes.length = 0;
    await provisionDemoAccountsInStore(f.store, f.inputs);
    expect(f.writes).toEqual([]);
    expect(f.records.get(`u:${f.dispatcherId}`)).toBe(JSON.stringify(current));
  });
  test.each([0, 1, 2])(
    "credential %s must verify before the capability can change",
    async (index) => {
      const f = await legacyFixture();
      const before = [...f.records];
      f.inputs[index].password = crypto.randomUUID();
      await expect(
        provisionDemoAccountsInStore(f.store, f.inputs),
      ).rejects.toThrow("never overwritten");
      expect([...f.records]).toEqual(before);
      expect(f.writes).toEqual([]);
    },
  );
  test.each([
    "not_synthetic",
    "customer_role",
    "foreign_org",
    "changed_crew",
    "extra_permission",
    "missing_permission",
    "wrong_email",
    "wrong_id",
  ])("refuses mismatched or general account %s", async (mutation) => {
    const f = await legacyFixture();
    const key = `u:${f.dispatcherId}`;
    const stored = JSON.parse(f.records.get(key)!) as StoredUser;
    if (mutation === "not_synthetic") stored.synthetic_demo = false;
    if (mutation === "customer_role") stored.membership!.role = "customer";
    if (mutation === "foreign_org")
      stored.membership!.organization_id = "other-organization";
    if (mutation === "changed_crew")
      stored.membership!.crew_id = "another-crew";
    if (mutation === "extra_permission")
      stored.membership!.permissions.push("admin");
    if (mutation === "missing_permission")
      stored.membership!.permissions = ["approve_plan"];
    if (mutation === "wrong_email") stored.email = "another@example.test";
    if (mutation === "wrong_id") stored.id = "another-id";
    f.records.set(key, JSON.stringify(stored));
    const before = [...f.records];
    await expect(
      provisionDemoAccountsInStore(f.store, f.inputs),
    ).rejects.toThrow("never overwritten");
    expect(f.writes).toEqual([]);
    expect([...f.records]).toEqual(before);
  });
  test("a technician cannot receive the dispatcher capability through expected input", async () => {
    const f = await legacyFixture();
    f.inputs[1].membership.permissions = ["recover_commands"];
    const before = [...f.records];
    await expect(
      provisionDemoAccountsInStore(f.store, f.inputs),
    ).rejects.toThrow("never overwritten");
    expect(f.writes).toEqual([]);
    expect([...f.records]).toEqual(before);
  });
});
