import { readBytes } from "@/lib/server/read-file";
import path from "node:path";
import { connection } from "next/server";
import { API_BASE, DEFAULT_SCENARIO } from "@/lib/data";
import { getConfig, isSafeSegment } from "@/lib/data/config";
import { demoDir } from "@/lib/data/files";

/**
 * Ordinul de lucru al unei echipe, ca PDF: întâi de la API (GET /work-orders/{crew}.pdf), apoi din
 * instantaneul demo (plans/<s>/work_orders/<crew>.pdf). Așa butonul merge și fără API.
 */
const CREW_RE = /^[A-Z]{1,3}-[A-Z0-9]{1,4}-\d{1,3}$/;

export async function GET(request: Request, ctx: RouteContext<"/ordine/[crew]">) {
  await connection();
  let crew: string;
  try {
    crew = decodeURIComponent((await ctx.params).crew).replace(/\.pdf$/i, "");
  } catch {
    return new Response("Adresă greșită.", { status: 400 });
  }
  const url = new URL(request.url);
  const requested = url.searchParams.get("scenariu") ?? "";
  const scenario = requested && isSafeSegment(requested) ? requested : DEFAULT_SCENARIO;
  if (!CREW_RE.test(crew)) return new Response("Echipă necunoscută.", { status: 400 });

  // pe planul salvat (de exemplu pe Cloudflare, fără API) nu mai întrebăm API-ul
  if (getConfig().dataSource !== "demo") try {
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
  const root = path.resolve(demoDir());
  for (const file of [
    path.join(root, "plans", scenario, "work_orders", `${crew}.pdf`),
    path.join(root, scenario, "work_orders", `${crew}.pdf`),
  ]) {
    // calea trebuie să rămână în dosarul instantaneului
    if (!path.resolve(/*turbopackIgnore: true*/ file).startsWith(root + path.sep)) continue;
    try {
      const pdf = await readBytes(file);
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
