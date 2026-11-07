/**
 * După `next build` (output: "export"), căile spre `/_next/...` sunt absolute. Deschisă de pe disc
 * (file://), pagina le-ar căuta la rădăcina discului. Scriptul le face relative în `out/`:
 * - în HTML (index.html stă la rădăcina lui out/): `/_next/` → `./_next/`;
 * - în CSS (fișierele stau în `out/_next/static/...`): `/_next/static/` → relativ față de fișier.
 * Pe un server obișnuit, căile relative merg la fel.
 */
import { readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

const OUT = path.join(import.meta.dir, "..", "out");

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = path.join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

let changed = 0;
for (const file of walk(OUT)) {
  const ext = path.extname(file);
  if (ext !== ".html" && ext !== ".css") continue;
  const before = readFileSync(file, "utf8");
  let after = before;
  if (ext === ".css") {
    const rel = path.relative(path.dirname(file), path.join(OUT, "_next")).split(path.sep).join("/") || ".";
    after = after.replaceAll("/_next/", `${rel}/`);
  } else {
    const rel = path.relative(path.dirname(file), OUT).split(path.sep).join("/") || ".";
    // doar atributele src/href și url() din <style>; datele interne ale paginii (self.__next_f) rămân
    // neatinse: rescrise, opresc hidratarea. Interacțiunile merg oricum prin scriptul inline (enhance.tsx).
    after = after.replace(/(\s(?:src|href)=")\/_next\//g, `$1${rel}/_next/`).replace(/url\(\/_next\//g, `url(${rel}/_next/`);
  }
  if (after !== before) {
    writeFileSync(file, after);
    changed++;
  }
}
console.log(`relativize: ${changed} fișiere actualizate în out/`);
