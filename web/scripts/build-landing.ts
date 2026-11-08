/**
 * Construiește site-ul de prezentare (web/site, Vite) în web/public/landing/, ca să-l servească consola.
 * Rulează înainte de dev și build. Dacă nimic nu s-a schimbat în web/site de la ultima construire, sare peste.
 */
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, statSync, writeFileSync, readFileSync } from "node:fs";
import path from "node:path";

const web = path.resolve(import.meta.dir, "..");
const site = path.join(web, "site");
const out = path.join(web, "public", "landing");
const stamp = path.join(out, ".built-from");

// Include plan/report changes even when none of the site's source files changed.
const extraction = spawnSync("uv", ["run", "python", "-I", path.join(site, "scripts", "extract-daybreak.py"), path.resolve(web, "../outputs/demo"), path.join(site, "src/data/daybreak.json"), path.resolve(web, "../reports")], { cwd: site, stdio: "inherit" });
if (extraction.status !== 0) process.exit(extraction.status ?? 1);

function newest(dir: string): number {
  let t = 0;
  for (const name of readdirSync(dir)) {
    if (name === "node_modules" || name === "dist" || name.startsWith(".")) continue;
    const p = path.join(dir, name);
    const s = statSync(p);
    t = Math.max(t, s.isDirectory() ? newest(p) : s.mtimeMs);
  }
  return t;
}

const sourceTime = String(Math.round(newest(site)));
if (existsSync(stamp) && readFileSync(stamp, "utf8") === sourceTime && process.argv[2] !== "--force") {
  console.log("site-ul de prezentare e la zi în public/landing/");
  process.exit(0);
}

const run = (cmd: string, args: string[]) => {
  const r = spawnSync(cmd, args, { cwd: site, stdio: "inherit" });
  if (r.status !== 0) process.exit(r.status ?? 1);
};
if (!existsSync(path.join(site, "node_modules", "vite"))) run("bun", ["install", "--no-save"]);
run("bun", ["x", "vite", "build", "--config", "vite.console.config.ts", "--logLevel", "warn"]);
writeFileSync(stamp, sourceTime);
console.log("site-ul de prezentare construit în public/landing/");
