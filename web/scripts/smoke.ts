/**
 * Test de fum: încarcă fiecare ecran pe serverul pornit (implicit http://localhost:3710) și cade dacă
 * vreunul nu răspunde 200 sau conține o eroare de randare. Prinde ce nu prinde tsc (de exemplu funcții
 * de client chemate din paginile de server).
 *
 *   bun scripts/smoke.ts [baseUrl]
 */
const base = (process.argv[2] ?? process.env.SMOKE_BASE ?? "http://localhost:3710").replace(/\/$/, "");
const ERR = /Attempted to call|Application error|Unhandled Runtime Error|Internal Server Error|NEXT_HTTP_ERROR/;

// ID-urile se iau din paginile care le au mereu: lucrarea și echipa din planul mare, postul din lista posturilor
async function firstIds(): Promise<{ item: string | null; post: string | null; crew: string | null }> {
  const [plan, posts] = await Promise.all([
    fetch(`${base}/harta`).then((r) => r.text()),
    fetch(`${base}/posturi`).then((r) => r.text()),
  ]);
  const item = /\/lucrari\/([ABC]-\d{8}-[A-Za-z0-9_.-]+)/.exec(plan)?.[1] ?? null;
  const crew = /\/ordine\/([A-Z]{1,3}-[A-Z0-9]{1,4}-\d{1,3})/.exec(plan)?.[1] ?? null;
  const post = /\/posturi\/(PT-[A-Za-z0-9_-]+)/.exec(posts)?.[1] ?? null;
  return { item, post, crew };
}

const ids = await firstIds();
const routes = ["/", "/bilant", "/app", "/harta", "/coada", "/rulare", "/lucrari", "/alerte", "/jurnal", "/modele", "/posturi", "/demo", "/demo?scena=4", "/debug", "/harta?harta=posturi", "/app?scenariu=maine"];
if (ids.item) routes.push(`/lucrari/${ids.item}`);
if (ids.post) routes.push(`/posturi/${ids.post}`);
if (ids.crew) routes.push(`/lucrari?echipa=${ids.crew}`);
routes.push("/lucrari/A-20991231-NU-EXISTA");

let failed = 0;
for (const r of routes) {
  const t0 = performance.now();
  try {
    const res = await fetch(`${base}${r}`, { signal: AbortSignal.timeout(60_000) });
    const body = await res.text();
    const bad = res.status !== 200 || ERR.test(body);
    if (bad) failed++;
    console.log(`${bad ? "PICĂ" : "ok  "} ${res.status} ${String(Math.round(performance.now() - t0)).padStart(5)} ms  ${r}${bad && ERR.test(body) ? `  (${ERR.exec(body)?.[0]})` : ""}`);
  } catch (e) {
    failed++;
    console.log(`PICĂ  ---        ${r}  (${e instanceof Error ? e.message : String(e)})`);
  }
}
if (ids.crew) {
  const res = await fetch(`${base}/ordine/${ids.crew}`);
  const ok = res.status === 200 && (res.headers.get("content-type") ?? "").includes("pdf");
  console.log(`${ok ? "ok  " : "info"} ${res.status}           /ordine/${ids.crew} (PDF${ok ? "" : " lipsă, acceptat"})`);
}
console.log(failed ? `\n${failed} ecrane au picat.` : `\nToate cele ${routes.length} ecrane merg.`);
process.exit(failed ? 1 : 0);
export {};
