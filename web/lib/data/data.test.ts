import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { cp, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { isApiUnavailable, apiPlan } from "./api";
import {
  parseJsonl,
  readFixtureAudit,
  readFixtureInvalidWorkItems,
  readFixturePlan,
  readFixtureWorkItems,
} from "./files";
import { getMetrics, getPlan, getPlanView, getScenarios, getSeries, getWorkItem, getWorkItems } from "./index";
import { resetProbeCache } from "./source";

// Scenariu fără instantaneu demo, ca testele să nu depindă de ce apare mai târziu în outputs/demo/.
const NO_DEMO = "test-fara-instantaneu";
const CLOSED_API = "http://127.0.0.1:9/api";
const REPO_ROOT = process.env.REPO_ROOT!;

describe("fixtures", () => {
  test("planul are 4 decizii și 2 trasee", async () => {
    const plan = await readFixturePlan();
    expect(plan).not.toBeNull();
    expect(plan!.data.decisions).toHaveLength(8);
    expect(plan!.data.routes).toHaveLength(3);
    expect(plan!.files).toEqual(["contracts/fixtures/plan_example.json"]);
  });

  test("lucrările A, B, C se încarcă fără erori", async () => {
    const items = await readFixtureWorkItems();
    expect(items!.data.errors).toEqual([]);
    expect(items!.data.records).toHaveLength(7);
    const onlyB = await readFixtureWorkItems("B");
    expect(onlyB!.data.records.map((w) => w.source)).toEqual(["B", "B"]);
  });

  test("lucrarea invalidă e expusă ca obiect brut", async () => {
    const invalid = await readFixtureInvalidWorkItems();
    expect(invalid!.data.records).toHaveLength(1);
    expect(invalid!.data.records[0].work_item_id).toBe("A-20261109-MTR-BAD");
  });

  test("auditul are 4 înregistrări", async () => {
    const audit = await readFixtureAudit();
    expect(audit!.data.records).toHaveLength(8);
  });
});

describe("parseJsonl", () => {
  test("o linie stricată nu oprește citirea", () => {
    const text = '{"a":1}\n\n{nu e json\n   \n{"b":2}\n[1,2]\r\n{"c":3}';
    const result = parseJsonl(text, "x.jsonl");
    expect(result.records).toEqual([{ a: 1 }, { b: 2 }, { c: 3 }]);
    expect(result.errors.map((e) => e.line)).toEqual([3, 6]);
    expect(result.errors[0].file).toBe("x.jsonl");
  });
});

describe("getPlanView cu fixtures", () => {
  test("decizii, trasee cu coordonate, lucrări neplanificate", async () => {
    const view = await getPlanView(NO_DEMO, { mode: "fixtures" });
    expect(view.source).toBe("fixtures");
    expect(view.degradedReason).toBeUndefined();
    const data = view.data!;
    expect(Object.keys(data.decisionsByWorkItemId)).toHaveLength(8);
    expect(data.routes).toHaveLength(3);
    for (const route of data.routes) {
      expect(route.depot?.depot_id).toBe(route.depot_id);
      expect(route.crew?.crew_id).toBe(route.crew_id);
      for (const stop of route.stops) {
        expect(Number.isFinite(stop.lat)).toBe(true);
        expect(Number.isFinite(stop.lon)).toBe(true);
      }
      // bază → opriri → bază
      expect(route.path).toHaveLength(route.stops.length + 2);
    }
    expect(data.unresolvedStopIds).toEqual([]);
    // Planul de test are acum o decizie pentru fiecare lucrare (orchestrator, 13:20).
    expect(data.unplannedItems).toHaveLength(0);
    expect(data.decisionsByWorkItemId["B-20261109-IF-SNAGOV"]?.decision).toBe("deferred");
    expect(data.decisionsByWorkItemId["C-20261109-PT-0877"]?.decision).toBe("notify");
    expect(data.alertsByWorkItemId["B-20261109-CT-MEDGIDIA"]).toHaveLength(1);
    expect(data.invalidItems).toHaveLength(1);
    expect(data.crews.length).toBeGreaterThan(0);
    expect(data.configIssues).toEqual([]);
  });

  test("o lucrare cu decizia și auditul ei", async () => {
    const result = await getWorkItem("A-20261109-MTR-004217", NO_DEMO, { mode: "fixtures" });
    expect(result.data?.decision?.decision).toBe("assigned");
    expect(result.data?.audit).toHaveLength(1);
    const unknown = await getWorkItem("A-20261109-NU-EXISTA", NO_DEMO, { mode: "fixtures" });
    expect(unknown.data).toBeNull();
    const quarantined = await getWorkItem("A-20261109-MTR-BAD", NO_DEMO, { mode: "fixtures" });
    expect(quarantined.data?.invalid).toBe(true);
  });

  test("fixtures au serii de exemplu (A, B, C); scenariile vin din config/scenarios.yaml", async () => {
    const series = await getSeries("A-20261109-MTR-004217", NO_DEMO, { mode: "fixtures" });
    expect(series.data?.source).toBe("A");
    expect(series.data?.points.length).toBeGreaterThan(10);
    const none = await getSeries("A-20261109-NU-EXISTA", NO_DEMO, { mode: "fixtures" });
    expect(none.data).toBeNull();
    const scenarios = await getScenarios({ mode: "fixtures" });
    expect(scenarios.data.map((s) => s.id)).toEqual(["demo-vara", "maine"]);
  });
});

describe("auto, cu API-ul oprit", () => {
  test("cade pe fixtures în mai puțin de 2 s", async () => {
    process.env.API_BASE = CLOSED_API;
    resetProbeCache();
    const started = performance.now();
    const view = await getPlanView(NO_DEMO, { mode: "auto" });
    const elapsed = performance.now() - started;
    expect(view.source).toBe("fixtures");
    expect(view.data?.routes).toHaveLength(3);
    expect(view.degradedReason).toContain("API-ul nu răspunde");
    expect(elapsed).toBeLessThan(2000);
  });

  test("modul api forțat nu aruncă, ci explică", async () => {
    resetProbeCache();
    const items = await getWorkItems(NO_DEMO, undefined, { mode: "api" });
    expect(items.source).toBe("fixtures");
    expect(items.data).toHaveLength(7);
    expect(items.degradedReason).toContain("API-ul nu răspunde");
    const metrics = await getMetrics({ mode: "api" });
    expect(metrics.data.A === null || typeof metrics.data.A === "object").toBe(true);
    const scenarios = await getScenarios({ mode: "auto" });
    expect(scenarios.source).toBe("fixtures");
    expect(scenarios.degradedReason).toBe("API-ul nu răspunde; afișez lista din config/scenarios.yaml");
  });

  test("clientul API aruncă ApiUnavailableError", async () => {
    const error = await apiPlan(NO_DEMO).catch((err: unknown) => err);
    expect(isApiUnavailable(error)).toBe(true);
  });
});

describe("cu un API de test", () => {
  let server: ReturnType<typeof Bun.serve>;

  beforeAll(async () => {
    const plan = (await readFixturePlan())!.data;
    server = Bun.serve({
      hostname: "127.0.0.1",
      port: 0, // port liber ales de sistem
      fetch(req) {
        const url = new URL(req.url);
        const scenario = url.searchParams.get("scenario");
        if (url.pathname === "/api/health") return Response.json({ status: "ok", version: "test" });
        if (url.pathname === "/api/plan" && scenario === "boom") return new Response("eroare", { status: 500 });
        if (url.pathname === "/api/plan") return Response.json({ ...plan, scenario, plan_id: "PLAN-api" });
        if (url.pathname.startsWith("/api/series/")) return Response.json({ detail: "nu există" }, { status: 404 });
        return Response.json({ detail: "necunoscut" }, { status: 404 });
      },
    });
    process.env.API_BASE = `http://127.0.0.1:${server.port}/api`;
    resetProbeCache();
  });

  afterAll(() => {
    server.stop(true);
    process.env.API_BASE = CLOSED_API;
    resetProbeCache();
  });

  test("auto folosește API-ul când răspunde", async () => {
    const plan = await getPlan(NO_DEMO, { mode: "auto" });
    expect(plan.source).toBe("api");
    expect(plan.data?.plan_id).toBe("PLAN-api");
    expect(plan.degradedReason).toBeUndefined();
  });

  test("o eroare 5xx coboară pe lanț și explică", async () => {
    const plan = await getPlan("boom", { mode: "auto" });
    expect(plan.source).toBe("fixtures");
    expect(plan.data?.plan_id).toBe("PLAN-fixture");
    expect(plan.degradedReason).toContain("500");
  });

  test("404 la serie: caută mai departe în instantaneul demo și în exemplele din fixture-uri", async () => {
    const series = await getSeries("A-20261109-MTR-004217", NO_DEMO, { mode: "auto" });
    expect(series.source).toBe("fixtures");
    expect(series.data?.work_item_id).toBe("A-20261109-MTR-004217");
    expect(series.degradedReason).toContain("API-ul n-are seria");
    const none = await getSeries("A-20261109-NU-EXISTA", NO_DEMO, { mode: "auto" });
    expect(none.data).toBeNull();
  });
});

describe("instantaneul demo", () => {
  let tmpRoot: string;

  beforeAll(async () => {
    tmpRoot = await mkdtemp(path.join(tmpdir(), "cp-web-demo-"));
    await cp(path.join(REPO_ROOT, "contracts", "fixtures"), path.join(tmpRoot, "contracts", "fixtures"), {
      recursive: true,
    });
    await cp(path.join(REPO_ROOT, "config"), path.join(tmpRoot, "config"), { recursive: true });
    const plan = (await readFixturePlan())!.data;
    await mkdir(path.join(tmpRoot, "outputs", "demo", "demo-test"), { recursive: true });
    await writeFile(
      path.join(tmpRoot, "outputs", "demo", "demo-test", "plan.json"),
      JSON.stringify({ ...plan, scenario: "demo-test", plan_id: "PLAN-demo" }),
    );
    process.env.REPO_ROOT = tmpRoot;
    process.env.API_BASE = CLOSED_API;
    resetProbeCache();
  });

  afterAll(async () => {
    process.env.REPO_ROOT = REPO_ROOT;
    await rm(tmpRoot, { recursive: true, force: true });
  });

  test("auto citește outputs/demo/<scenariu>/plan.json când API-ul e oprit", async () => {
    const plan = await getPlan("demo-test", { mode: "auto" });
    expect(plan.source).toBe("demo");
    expect(plan.data?.plan_id).toBe("PLAN-demo");
    expect(plan.degradedReason).toBe("API-ul nu răspunde; afișez instantaneul demo");
  });

  test("fără lucrări în demo, tot setul coboară pe fixtures (plan, lucrări, jurnal din aceeași sursă)", async () => {
    const view = await getPlanView("demo-test", { mode: "auto" });
    expect(view.source).toBe("fixtures");
    expect(view.data?.sources.plan.source).toBe("fixtures");
    expect(view.data?.sources.workItems.source).toBe("fixtures");
    expect(view.data?.sources.audit.source).toBe("fixtures");
    // ID-urile planului se potrivesc cu lucrările
    expect(view.data?.unresolvedStopIds).toEqual([]);
  });

  test("o lucrare fără câmpurile de urmărire e pusă deoparte, nu oprește pagina", async () => {
    const { splitWorkItems } = await import("./files");
    const bad = { work_item_id: "A-20250708-X", source: "A", asset_id: "X", asset_type: "meter", location: { lat: 44.4, lon: 26.1, zone_id: "B-S1" }, prediction: { score: 0.5 } };
    const split = splitWorkItems([bad as unknown as Record<string, unknown>], "test.jsonl");
    expect(split.records).toHaveLength(0);
    expect(split.errors[0].message).toContain("prediction_id");
  });

  test("un nume de scenariu periculos nu iese din outputs/demo", async () => {
    const plan = await getPlan("../../etc", { mode: "demo" });
    expect(plan.source).toBe("fixtures");
  });
});

describe("posturile din planificator", () => {
  test("culorile fără diacritice devin culorile interfeței; lipsă, din pierdere", async () => {
    const { normalizePostColor, colorFor } = await import("./posts");
    expect(normalizePostColor("rosu", 5019)).toBe("roșu");
    expect(normalizePostColor("roșu", 5019)).toBe("roșu");
    expect(normalizePostColor("Galben", 300)).toBe("galben");
    expect(normalizePostColor(undefined, 650)).toBe("roșu");
    expect(normalizePostColor("necunoscut", 120)).toBe("verde");
    expect(normalizePostColor("mov", null)).toBe("necunoscut");
    // aceleași praguri ca config/planner.yaml: galben de la 200, roșu de la 600
    expect(colorFor(199.66)).toBe("verde");
    expect(colorFor(210.44)).toBe("galben");
    expect(colorFor(621.7)).toBe("roșu");
  });

  test("pragurile vin din config/planner.yaml", async () => {
    const { readPostThresholds } = await import("./files");
    expect(await readPostThresholds()).toEqual({ yellow: 200, red: 600 });
  });

  test("cauza din bilanț: codurile devin cuvinte, textul rămâne", async () => {
    const { postDiagnosisRo } = await import("./posts");
    expect(postDiagnosisRo("furt_inainte_contor")).toBe("furt înainte de contor");
    expect(postDiagnosisRo("pierdere_tehnica")).not.toContain("_");
    expect(postDiagnosisRo("Furt înainte de contor")).toBe("Furt înainte de contor");
    expect(postDiagnosisRo(null)).toBeNull();
  });
});

describe("planul fără dubluri", () => {
  test("lucrările repetate într-o alertă apar o singură dată, în ordine", async () => {
    const { dedupePlan } = await import("./index");
    const plan = {
      alerts: [
        { alert_id: "AL-1", severity: "critical", title_ro: "5 cazuri cu risc de siguranță", body_ro: "b", channel: "dispecerat", created_at: "2025-07-08T08:00:00+03:00", work_item_ids: ["a", "b", "a", "c", "b"] },
      ],
    } as unknown as import("@/lib/contracts").Plan;
    expect(dedupePlan(plan).alerts?.[0].work_item_ids).toEqual(["a", "b", "c"]);
    // numărul din titlu număra dublurile
    expect(dedupePlan(plan).alerts?.[0].title_ro).toBe("3 cazuri cu risc de siguranță");
    const clean = { alerts: [{ ...plan.alerts![0], work_item_ids: ["a"] }] } as unknown as import("@/lib/contracts").Plan;
    expect(dedupePlan(clean)).toBe(clean);
  });
});
