import { connection, type NextRequest } from "next/server";
import { getAudit } from "@/lib/data";
import { resolveScenario } from "@/lib/server/queries";

/**
 * Jurnalul deciziilor pentru scenariul cerut (?scenariu=, apoi cookie-ul, apoi cel implicit),
 * câte o linie AuditRecord pe rând (JSON Lines), exact cum l-a scris agentul.
 */
export async function GET(request: NextRequest) {
  await connection();
  const scenario = await resolveScenario(Promise.resolve(Object.fromEntries(request.nextUrl.searchParams.entries())));
  const audit = await getAudit(scenario);
  const body = audit.data.map((r) => JSON.stringify(r)).join("\n");
  return new Response(body ? `${body}\n` : "", {
    headers: {
      "Content-Type": "application/x-ndjson; charset=utf-8",
      // scenariul e validat de resolveScenario (litere, cifre, „_”, „.”, „-”), deci e sigur în numele fișierului
      "Content-Disposition": `attachment; filename="jurnal-${scenario}.jsonl"`,
      "Cache-Control": "no-store",
      "X-Data-Source": audit.source,
    },
  });
}
