import { expect, test } from "bun:test";
import { assistantIntent, assistantScenarioMatches, assistantSelection, routeSelection } from "./assistant-context";
import { compatibilityAppPath } from "./compatibility-route";
import { availableNav, mobileNav, navigationHref } from "./side-nav";
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

test("navigation exposes real role destinations and no restricted console counts", () => {
  const scoped = {
    customer: ["/app", "/cazuri", "/conexiuni", "/activitate"],
    technician: ["/app", "/traseu", "/sarcini", "/cazuri", "/activitate"],
    dispatcher: ["/app", "/cazuri", "/activitate"],
  };
  for (const role of ["customer", "technician", "dispatcher"] as const) {
    const links = availableNav(false, role);
    expect(links.map((item) => item.href)).toEqual(scoped[role]);
    expect(links[0].label).toBe("Assistant");
    expect(links.every((item) => !("count" in item))).toBe(true);
  }
  expect(availableNav(true, "customer").map((item) => item.href)).toEqual(scoped.customer);
  expect(availableNav(true, "technician").map((item) => item.href)).toEqual(scoped.technician);
  const dispatcher = availableNav(true, "dispatcher");
  expect(dispatcher.map((item) => item.href)).toEqual([
    "/app", "/planificare", "/coada", "/harta", "/lucrari", "/cazuri", "/posturi",
    "/jurnal", "/alerte", "/modele", "/rulare", "/demo",
  ]);
  expect(dispatcher.filter((item) => item.match("/harta")).map((item) => item.href)).toEqual(["/harta"]);
  expect(dispatcher.filter((item) => item.match("/app#assistant")).map((item) => item.href)).toEqual(["/app"]);
  expect(dispatcher.filter((item) => item.match("/lucrari/WORK-1")).map((item) => item.href)).toEqual(["/lucrari"]);
  expect(dispatcher.filter((item) => item.match("/ordine/CREW-1")).map((item) => item.href)).toEqual(["/lucrari"]);
  expect(availableNav(false, "technician").filter((item) => item.match("/sarcini/WORK-1")).map((item) => item.href)).toEqual(["/sarcini"]);
});

test("mobile has four frequent destinations and keeps other destinations in the full menu", () => {
  expect(mobileNav(true, "dispatcher").map((item) => item.href)).toEqual(["/app", "/planificare", "/coada", "/harta"]);
  expect(mobileNav(false, "customer").map((item) => item.href)).toEqual(["/app", "/cazuri", "/conexiuni", "/activitate"]);
  expect(mobileNav(false, "technician").map((item) => item.href)).toEqual(["/app", "/traseu", "/sarcini", "/activitate"]);
  expect(availableNav(false, "technician").map((item) => item.href)).toContain("/cazuri");
  expect(mobileNav(false, "dispatcher").map((item) => item.href)).toEqual(["/app", "/cazuri", "/activitate"]);
});

test("scenario queries stay before anchors and Assistant has no default hash", () => {
  expect(navigationHref("/app", "demo-vara")).toBe("/app?scenariu=demo-vara");
  expect(navigationHref("/planificare#detalii-plan", "demo-vara")).toBe("/planificare?scenariu=demo-vara#detalii-plan");
  expect(navigationHref("/cazuri", null)).toBe("/cazuri");
  expect(navigationHref("/planificare?filtru=echipe#detalii-plan", "storm")).toBe("/planificare?filtru=echipe&scenariu=storm#detalii-plan");
});

test("actual server routes gate global reads and serialize shell metadata only for authorized dispatchers", () => {
  // Synthetic IO fixtures. Actual routes and the real authorization policy run unchanged.
  const script = `
    import { mock } from "bun:test";
    import assert from "node:assert/strict";
    let user: any = null;
    let reads = 0;
    let cookieReads = 0;
    let viewData: any = null;
    const info = { scenario: "demo-vara", scenarios: [{id:"demo-vara",label:"Synthetic scenario"}], counts:{review:3,alerts:2,notifications:1}, provenance:{detail:"GLOBAL_PRIVATE_SENTINEL",source:"fixtures",syntheticItems:6,totalItems:6} };
    mock.module("server-only", () => ({}));
    mock.module("./lib/server/accounts", () => ({currentUser: async () => user, toMembership: (u: any) => u.membership}));
    mock.module("next/server", () => ({connection: async () => {}}));
    mock.module("next/headers", () => ({cookies: async () => {cookieReads++; return {get: () => ({value:"synthetic-plan|2026-11-08T11:00:00Z"})};}}));
    mock.module("./lib/server/queries", () => ({resolveScenario: async () => "demo-vara", loadShellInfo: async () => {reads++; return {info,view:{data:viewData,source:"demo"}};}}));
    mock.module("./lib/server/geo", () => ({loadLocatorGeo: async () => {reads++; return {};}}));
    mock.module("./lib/data/posts", () => ({getPosts: async () => {reads++; return null;}}));
    mock.module("./lib/home-dotmap", () => ({getRomaniaDots: async () => {reads++; return {width:0,height:0,pitch:1,dots:[]};}}));
    const {default: Page} = await import("./app/app/page");
    const {default: PlanPage} = await import("./app/planificare/page");
    const {default: MapPage} = await import("./app/harta/page");
    const {default: Compat} = await import("./app/workspace/page");
    const {AppShell} = await import("./components/shell/app-shell");
    const {PlanScreen} = await import("./components/plan/plan-screen");
    const {ApproveButton} = await import("./components/home/approve-button");
    const {requireConsole} = await import("./lib/server/operations");
    async function render(query: any = {}, route: any = Page) {
      const element: any = route({searchParams:Promise.resolve(query)});
      return await element.props.children.type(element.props.children.props);
    }
    function findElement(value: any, component: any, seen = new WeakSet()): any {
      if (!value || typeof value !== "object" || seen.has(value)) return null;
      seen.add(value);
      if (value.type === component) return value;
      for (const child of Object.values(value.props ?? value)) {
        const found = findElement(child,component,seen);
        if (found) return found;
      }
      return null;
    }
    try {await render({proposal:"${proposal}"}); assert.fail("anonymous /app must redirect");}
    catch (error: any) {assert.ok(error.digest.includes("/intra?proposal=${proposal}"));}
    for (const route of [PlanPage,MapPage]) {
      await assert.rejects(() => render({},route), (error: any) => Boolean(error.digest?.includes(";/intra;")));
    }
    assert.equal(reads,0);
    for (const role of ["customer","technician","dispatcher"]) {
      for (const organization_id of ["daybreak-demo","other-organization"]) {
       for (const permissions of [[],["view_console"]]) {
        user = {id:"synthetic-account",email:"synthetic@example.test",full_name:null,hash:"DO_NOT_SERIALIZE",membership:{role,organization_id,crew_id:null,connection_ids:[],permissions}};
        reads = 0;
        const authorized = role === "dispatcher" && organization_id === "daybreak-demo" && permissions.includes("view_console");
        const result: any = await render({case_id:"CASE-1"});
        assert.equal(reads,authorized ? 1 : 0);
        assert.equal(result.props.children.props.presentation,"main");
        assert.equal(result.props.fit,true);
        assert.equal(result.props.children.props.account.membership.role,role);
        if (!authorized) {
          assert.equal(result.props.info,undefined);
          assert.equal(result.props.children.props.scenario,"demo-vara");
          for (const route of [PlanPage,MapPage]) {
            await assert.rejects(() => render({},route), (error: any) => Boolean(error.digest?.includes(";/app;")));
          }
          await render({filtru:"echipe",console:"1",harta:"posturi"});
          assert.equal(reads,0);
          try {await requireConsole(); assert.fail("restricted legacy page must redirect");}
          catch(error: any) {assert.ok(error.digest.includes(";/app;"));}
        } else {
          await requireConsole();
          await render({},PlanPage);
          assert.equal(reads,2);
          await assert.rejects(() => render({filtru:"echipe"}), (error: any) => Boolean(error.digest?.includes("/planificare?scenariu=demo-vara&filtru=echipe")));
        }
        const beforeShell = reads;
        const shell = JSON.stringify(await AppShell({info,children:null}));
        assert.equal(reads,beforeShell,"AppShell cannot read global data implicitly");
        assert.equal(shell.includes("GLOBAL_PRIVATE_SENTINEL"),authorized);
        assert.equal(shell.includes("DO_NOT_SERIALIZE"),false);
        assert.equal(JSON.stringify(await AppShell({children:null})).includes("GLOBAL_PRIVATE_SENTINEL"),false);
       }
      }
    }
    // Cookies, agent actions and approvals of an older plan cannot approve the current plan.
    user = {id:"synthetic-dispatcher",email:"synthetic@example.test",full_name:null,membership:{role:"dispatcher",organization_id:"daybreak-demo",crew_id:null,connection_ids:[],permissions:["view_console"]}};
    const generated = "2026-11-08T10:00:00Z";
    const summary = Object.fromEntries(["items_in","items_valid","items_invalid","assigned","crews_used","human_review","notifications","remote_actions","expected_value_lei","total_km"].map(key => [key,0]));
    viewData = {scenario:"demo-vara",plan:{plan_id:"synthetic-plan",plan_date:"2026-11-09",generated_at:generated,decisions:[],alerts:[],notifications:[],summary},workItems:[],workItemsById:{},decisionsByWorkItemId:{},routes:[],area:{regions:{}},depots:[],crews:[],shift:null,invalidItems:[],audit:[]};
    for (const audit of [
      [],
      [{actor:"agent",action:"approve_plan",ts:"2026-11-08T11:00:00Z"}],
      [{actor:"human",action:"approve_plan",ts:"2026-11-08T09:00:00Z"}],
      [{actor:"human",action:"approve_plan",ts:"2026-11-08T11:00:00Z"}],
    ]) {
      viewData.audit = audit;
      const expected = audit[0]?.actor === "human" && audit[0].ts > generated ? audit[0].ts : null;
      const map = await render({},MapPage);
      assert.deepEqual(findElement(map,PlanScreen).props.approval,expected ? {at:expected,local:false} : null);
      const plan = await render({},PlanPage);
      assert.equal(findElement(plan,ApproveButton).props.approvedAt,expected);
    }
    assert.equal(cookieReads,0,"approval must never consult browser cookies");
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
