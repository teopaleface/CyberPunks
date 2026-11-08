/**
 * Pentru Cloudflare: copiază în public/_data/ fișierele pe care consola le citește din repo (planul salvat
 * din outputs/demo, configurația, rapoartele, exemplele din contracts/fixtures). Pe Workers nu există disc;
 * lib/server/read-file.ts le cere de acolo (DATA_ASSETS=1). Totul e deja în git și se vede oricum în consolă.
 */
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import path from "node:path";

const web = path.resolve(import.meta.dir, "..");
const repo = path.resolve(web, "..");
const out = path.join(web, "public", "_data");
rmSync(out, { recursive: true, force: true });
for (const rel of ["outputs/demo", "config", "reports", "contracts/fixtures"]) {
  const src = path.join(repo, rel);
  if (!existsSync(src)) continue;
  mkdirSync(path.dirname(path.join(out, rel)), { recursive: true });
  cpSync(src, path.join(out, rel), { recursive: true, filter: (p) => !/\.(png|jpe?g|svg|parquet|joblib)$/i.test(p) || p.includes("work_orders") });
}
console.log("datele pentru Cloudflare copiate în public/_data/");
