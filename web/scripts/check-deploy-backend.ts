import {readFile} from 'node:fs/promises';
import {parseConfigFileTextToJson} from 'typescript';

type Configuration = {vars?: Record<string, unknown>};
type Fetcher = (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
export async function checkDeployBackend(config: Configuration, fetcher: Fetcher = fetch): Promise<void> {
  if (config.vars?.DATA_SOURCE !== 'api') return;
  const base = config.vars.API_BASE;
  const trusted = config.vars.DAYBREAK_WORKSPACE_ORIGIN;
  if (typeof base !== 'string' || typeof trusted !== 'string')
    throw new Error('Configure the current public backend before deploying the API workspace.');
  const url = new URL(base);
  if (url.protocol !== 'https:' || url.origin !== trusted || url.pathname !== '/api' || url.search || url.hash || url.username || url.password)
    throw new Error('The deployment needs a public HTTPS API and its matching trusted origin.');
  const [health, protectedRead] = await Promise.all([
    fetcher(new URL('/healthz', url), {redirect: 'manual', signal: AbortSignal.timeout(15000)}),
    fetcher(new URL('/api/operations/context', url), {redirect: 'manual', signal: AbortSignal.timeout(15000)}),
  ]);
  if (health.status !== 200 || (await health.json()).status !== 'ok' || protectedRead.status !== 401)
    throw new Error('The configured backend is unavailable or does not enforce authentication. Deployment stopped.');
}

if (import.meta.main) {
  try {
    const path = new URL('../wrangler.jsonc', import.meta.url);
    const parsed = parseConfigFileTextToJson(path.pathname, await readFile(path, 'utf8'));
    if (parsed.error) throw new Error('Invalid deployment configuration.');
    await checkDeployBackend(parsed.config);
    console.log('Backend health and authentication checked before deployment.');
  } catch {
    console.error('Deployment stopped: the configured backend could not be verified. Check the current backend origin.');
    process.exitCode = 1;
  }
}
