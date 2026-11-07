import { expect, test } from "bun:test";
import { assistantIntent, assistantScenarioMatches, assistantSelection, routeSelection } from "./assistant-context";
import { compatibilityAppPath } from "./compatibility-route";
import { availableNav } from "./side-nav";
import { proposalFromSearch, proposalSignInPath, signInModeParams } from "@/lib/operations/proposal-link";

const proposal = "6d57ebca-af8d-4da4-afcb-3080dca9a671";

test("old proposal links reach /app after sign-in without accepting a redirect destination", () => {
  const signIn = new URLSearchParams(proposalSignInPath(proposal).split("?")[1]);
  const afterModeChange = signInModeParams(signIn, "cont-nou");
  const path = compatibilityAppPath({ proposal: proposalFromSearch(afterModeChange)!, console: "1", next: "https://foreign.example" });
  expect(path.startsWith("/app?")).toBe(true);
  expect(new URL(path, "https://daybreak.example").origin).toBe("https://daybreak.example");
  expect(proposalFromSearch(new URLSearchParams(path.split("?")[1]))).toBe(proposal);
  expect(path).not.toContain("console=");
  expect(compatibilityAppPath({})).toBe("/app");
  const ambiguous = compatibilityAppPath({ proposal: [proposal, proposal] });
  expect(proposalFromSearch(new URLSearchParams(ambiguous.split("?")[1]))).toBeNull();
});

test("selection comes from known detail/query IDs, never a substation ID or actor", () => {
  expect(routeSelection("/lucrari/WORK%2F123", new URLSearchParams("work_item_id=other"))).toEqual({ work_item_id: "WORK/123" });
  expect(routeSelection("/coada", new URLSearchParams("caz=WORK-2"))).toEqual({ work_item_id: "WORK-2" });
  expect(routeSelection("/harta", new URLSearchParams("lucrare=WORK-3"))).toEqual({ work_item_id: "WORK-3" });
  expect(routeSelection("/posturi/PT-1", new URLSearchParams())).toEqual({});
  expect(routeSelection("/app", new URLSearchParams("case_id=CASE-1&connection_id=CONN-1"))).toEqual({ case_id: "CASE-1", connection_id: "CONN-1" });
  expect(routeSelection("/app", new URLSearchParams("case_id=one&case_id=two"))).toEqual({});
  expect(assistantSelection({ actor: { role: "dispatcher" }, work_item_id: 12, case_id: "\n" })).toEqual({});
  expect(routeSelection("/lucrari/%zz", new URLSearchParams())).toEqual({});
});

test("all six intents open fresh editable requests and reject unknown actions or non-object data", () => {
  for (const action of ["create_case", "record_verdict", "review_work_item", "approve_plan", "set_availability", "request_human"] as const) {
    const event = { action, data: { work_item_id: "WORK-1" }, actor: { role: "dispatcher" }, selection: { work_item_id: "WORK-1" } };
    const first = assistantIntent(event)!;
    const second = assistantIntent(event)!;
    expect(first.requestedAction?.action).toBe(action);
    expect(first.requestedAction?.data).toEqual(event.data);
    expect(first.requestedAction?.requestId).not.toBe(second.requestedAction?.requestId);
    expect(first).not.toHaveProperty("actor");
  }
  expect(assistantIntent({ action: "delete_everything", data: {} })).toBeNull();
  for (const data of [null, [], "data", 1]) expect(assistantIntent({ action: "approve_plan", data })).toBeNull();
  expect(assistantIntent({})).toEqual({ selection: {} });
  expect(assistantIntent({ scenario: "demo-vara" })).toEqual({ selection: {} });
});

test("assistant intents cannot silently change the current scenario", () => {
  expect(assistantScenarioMatches({}, "maine")).toBe(true);
  expect(assistantScenarioMatches({ scenario: "maine" }, "maine")).toBe(true);
  expect(assistantScenarioMatches({ scenario: "demo-vara" }, "maine")).toBe(false);
  expect(assistantScenarioMatches({ scenario: null }, "maine")).toBe(false);
  expect(assistantScenarioMatches({ scenario: ["maine"] }, "maine")).toBe(false);
});

test("restricted desktop/mobile navigation exposes only the role home", () => {
  for (const role of ["customer", "technician", "dispatcher"] as const) {
    expect(availableNav(false, role).map((item) => item.href)).toEqual(["/app"]);
    expect(availableNav(false, role)[0]).not.toHaveProperty("count");
  }
  expect(availableNav(true, "dispatcher").map((item) => item.href)).toContain("/coada");
  expect(availableNav(true, "dispatcher").map((item) => item.href)).toContain("/posturi");
});

test("actual server routes gate global reads and serialize shell metadata only for authorized dispatchers", () => {
  // Isolate module mocks so these tests cannot alter other suites or read real account/data stores.
  const script = `
    import { mock } from "bun:test";
    import assert from "node:assert/strict";
    let user: any = null;
    let reads = 0;
    const info = { scenario: "demo-vara", scenarios: [{id:"demo-vara",label:"Demo"}], counts:{review:42,alerts:9,notifications:1}, provenance:{detail:"GLOBAL_PRIVATE_SENTINEL",source:"fixtures",syntheticItems:689,totalItems:689} };
    mock.module("server-only", () => ({}));
    mock.module("./lib/server/accounts", () => ({currentUser: async () => user, toMembership: (u: any) => u.membership}));
    mock.module("next/server", () => ({connection: async () => {}}));
    mock.module("./lib/server/queries", () => ({resolveScenario: async () => "demo-vara", loadShellInfo: async () => {reads++; return {info,view:{data:null,source:"fixtures"}};}}));
    const {default: Page} = await import("./app/app/page");
    const {default: Compat} = await import("./app/workspace/page");
    const {AppShell} = await import("./components/shell/app-shell");
    const {requireConsole} = await import("./lib/server/operations");
    async function render(query: any = {}) {
      const element: any = Page({searchParams:Promise.resolve(query)});
      return await element.props.children.type(element.props.children.props);
    }
    try {await render({proposal:"${proposal}"}); assert.fail("anonymous /app must redirect");}
    catch (error: any) {assert.ok(error.digest.includes("/intra?proposal=${proposal}"));}
    assert.equal(reads,0);
    for (const role of ["customer","technician","dispatcher"]) {
      for (const organization_id of ["daybreak-demo","other-organization"]) {
        user = {id:"synthetic-account",email:"synthetic@example.test",full_name:null,hash:"DO_NOT_SERIALIZE",membership:{role,organization_id,crew_id:null,connection_ids:[],permissions: role === "dispatcher" ? ["view_console"] : []}};
        reads = 0;
        const authorized = role === "dispatcher" && organization_id === "daybreak-demo";
        const result: any = await render({case_id:"CASE-1"});
        assert.equal(reads,authorized ? 1 : 0);
        if (!authorized) {
          assert.equal(result.props.info,undefined);
          assert.equal(result.props.children.props.presentation,"role");
          assert.equal(result.props.children.props.scenario,"demo-vara");
          assert.deepEqual(result.props.children.props.initialSelection,{case_id:"CASE-1"});
          try {await requireConsole(); assert.fail("restricted legacy page must redirect");}
          catch(error: any) {assert.ok(error.digest.includes(";/app;"));}
        } else await requireConsole();
        const shell = JSON.stringify(await AppShell({info,children:null}));
        assert.equal(shell.includes("GLOBAL_PRIVATE_SENTINEL"),authorized);
        assert.equal(shell.includes("DO_NOT_SERIALIZE"),false);
      }
    }
    const compat: any = Compat({searchParams:Promise.resolve({proposal:"${proposal}"})});
    try {await compat.props.children.type(compat.props.children.props); assert.fail("compat route must redirect");}
    catch(error: any) {assert.ok(error.digest.includes("/app?proposal=${proposal}"));}
    console.log("server routing checks passed");
  `;
  const result = Bun.spawnSync([process.execPath, "-e", script], { cwd: `${import.meta.dir}/../..`, env: { ...process.env, DAYBREAK_TEST_ORIGIN: undefined } });
  expect(result.stderr.toString()).toBe("");
  expect(result.stdout.toString()).toContain("server routing checks passed");
  expect(result.exitCode).toBe(0);
});
