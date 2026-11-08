import "server-only";
import { readFile } from "node:fs/promises";
import path from "node:path";

/**
 * Citirea fișierelor de date (planul salvat, configurația, rapoartele, conturul județelor).
 * Local, de pe disc. Pe Cloudflare (DATA_ASSETS=1) nu există disc: aceleași fișiere sunt publicate
 * ca statice (scripts/cloudflare-data.ts le copiază în public/_data/), iar aici le cerem prin
 * legătura ASSETS a workerului. Un fișier care lipsește aruncă ENOENT, ca pe disc.
 */

const onAssets = () => process.env.DATA_ASSETS === "1";

function repoRoot(): string {
  return path.resolve(process.env.REPO_ROOT ?? path.resolve(process.cwd(), ".."));
}

/** Adresa statică a unui fișier: ce e în web/public rămâne la rădăcină, restul repo-ului sub /_data/. */
export function assetPathFor(abs: string): string | null {
  const root = repoRoot();
  const publics = [path.join(root, "web", "public"), path.join(process.cwd(), "public")];
  for (const pub of publics) {
    const rel = path.relative(pub, abs);
    if (rel && !rel.startsWith("..") && !path.isAbsolute(rel)) return "/" + rel.split(path.sep).join("/");
  }
  const rel = path.relative(root, abs);
  if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) return null;
  return "/_data/" + rel.split(path.sep).join("/");
}

function missing(abs: string): NodeJS.ErrnoException {
  const err = new Error(`ENOENT: lipsește ${abs}`) as NodeJS.ErrnoException;
  err.code = "ENOENT";
  return err;
}

async function fetchAsset(abs: string): Promise<Response> {
  const url = assetPathFor(abs);
  if (!url) throw missing(abs);
  const { getCloudflareContext } = await import("@opennextjs/cloudflare");
  const { env } = await getCloudflareContext({ async: true });
  const assets = (env as unknown as { ASSETS?: { fetch: (r: Request | URL | string) => Promise<Response> } }).ASSETS;
  if (!assets) throw missing(abs);
  const res = await assets.fetch(new URL(url, "https://assets.local"));
  if (!res.ok) throw missing(abs);
  return res;
}

export async function readText(abs: string): Promise<string> {
  if (onAssets()) return (await fetchAsset(abs)).text();
  return readFile(/*turbopackIgnore: true*/ abs, "utf8");
}

export async function readBytes(abs: string): Promise<Uint8Array> {
  if (onAssets()) return new Uint8Array(await (await fetchAsset(abs)).arrayBuffer());
  return new Uint8Array(await readFile(/*turbopackIgnore: true*/ abs));
}
