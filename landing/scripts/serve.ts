/** Servește exportul static (`out/`) pe http://localhost:3730, ca verificare înainte de prezentare. */
import path from "node:path";

const OUT = path.join(import.meta.dir, "..", "out");
const port = Number(process.env.PORT ?? 3730);

Bun.serve({
  port,
  async fetch(req) {
    const url = new URL(req.url);
    let p = decodeURIComponent(url.pathname);
    if (p.endsWith("/")) p += "index.html";
    const file = Bun.file(path.join(OUT, path.normalize(p).replace(/^(\.\.[/\\])+/, "")));
    if (await file.exists()) return new Response(file);
    return new Response("Nu există", { status: 404 });
  },
});
console.log(`Landing-ul (export static) pe http://localhost:${port}`);
