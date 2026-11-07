import path from "node:path";
import { readText } from "@/lib/server/read-file";

/**
 * Pagina HTML a site-ului de prezentare (construit în public/landing/). Next rescrie spre ea adresele
 * site-ului (/, /bilant, /diagnostic, /plan, /agent, /intra; vezi next.config.ts). O rută, nu o rescriere
 * direct spre fișierul static, ca să meargă la fel local și pe Cloudflare (OpenNext).
 */
export async function GET() {
  try {
    const html = await readText(path.join(process.cwd(), "public", "landing", "index.html"));
    return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=60" } });
  } catch {
    return new Response("Site-ul de prezentare nu e construit încă (bun run landing).", { status: 503, headers: { "content-type": "text/plain; charset=utf-8" } });
  }
}
