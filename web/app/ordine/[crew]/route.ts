import { readFile } from "node:fs/promises";
import path from "node:path";
import { connection } from "next/server";
import { API_BASE, DEFAULT_SCENARIO } from "@/lib/data";
import { demoDir } from "@/lib/data/files";

/**
 * Ordinul de lucru al unei echipe, ca PDF: întâi de la API (GET /work-orders/{crew}.pdf), apoi din
 * instantaneul demo (plans/<s>/work_orders/<crew>.pdf). Așa butonul merge și fără API.
 */
const CREW_RE = /^[A-Z]{1,3}-[A-Z0-9]{1,4}-\d{1,3}$/;
const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;

export async function GET(request: Request, ctx: RouteContext<"/ordine/[crew]">) {
  await connection();
  const crew = decodeURIComponent((await ctx.params).crew).replace(/\.pdf$/i, "");
  const url = new URL(request.url);
  const requested = url.searchParams.get("scenariu") ?? "";
  const scenario = SCENARIO_RE.test(requested) ? requested : DEFAULT_SCENARIO;
  if (!CREW_RE.test(crew)) return new Response("Echipă necunoscută.", { status: 400 });

  try {
    const res = await fetch(`${API_BASE}/work-orders/${encodeURIComponent(crew)}.pdf?scenario=${encodeURIComponent(scenario)}`, {
      signal: AbortSignal.timeout(4000),
      cache: "no-store",
    });
    if (res.ok && res.headers.get("content-type")?.includes("pdf")) {
      return new Response(res.body, {
        headers: { "content-type": "application/pdf", "content-disposition": `inline; filename="ordin-de-lucru-${crew}.pdf"` },
      });
    }
  } catch {
    // API-ul nu răspunde: încercăm instantaneul
  }
  for (const file of [
    path.join(demoDir(), "plans", scenario, "work_orders", `${crew}.pdf`),
    path.join(demoDir(), scenario, "work_orders", `${crew}.pdf`),
  ]) {
    try {
      const pdf = await readFile(file);
      return new Response(new Uint8Array(pdf), {
        headers: { "content-type": "application/pdf", "content-disposition": `inline; filename="ordin-de-lucru-${crew}.pdf"` },
      });
    } catch {
      // următorul
    }
  }
  return new Response(`Ordinul de lucru pentru ${crew} nu există încă (nici în API, nici în ultimul plan salvat).`, {
    status: 404,
    headers: { "content-type": "text/plain; charset=utf-8" },
  });
}
