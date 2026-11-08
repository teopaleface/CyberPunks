import {expect, test} from 'bun:test';
import {checkDeployBackend} from './check-deploy-backend';
const config = {vars: {DATA_SOURCE: 'api', API_BASE: 'https://synthetic.example/api', DAYBREAK_WORKSPACE_ORIGIN: 'https://synthetic.example'}};
const responding = (health: number, auth: number) => (async (url: RequestInfo | URL) => Response.json({status: 'ok'}, {status: String(url).endsWith('/healthz') ? health : auth})) as typeof fetch;
test('an expired backend or a public context blocks deployment', async () => {
  for (const [health, auth] of [[530,401], [502,401], [200,200], [200,302]])
    await expect(checkDeployBackend(config, responding(health,auth))).rejects.toThrow('Deployment stopped');
  await expect(checkDeployBackend(config, async () => {throw new Error('synthetic unreachable origin');})).rejects.toThrow();
});
test('a healthy authenticated backend passes without transmitting credentials', async () => {
  const calls: RequestInit[] = [];
  await checkDeployBackend(config, (async (url: RequestInfo | URL, init?: RequestInit) => {
    calls.push(init!);
    return responding(200,401)(url, init);
  }) as typeof fetch);
  expect(calls).toHaveLength(2);
  expect(calls.every(c => !c.headers && c.redirect === 'manual')).toBe(true);
});
test('local or mismatched origins cannot be shipped as the public backend', async () => {
  for (const vars of [{...config.vars, API_BASE: 'http://127.0.0.1:8720/api'}, {...config.vars, DAYBREAK_WORKSPACE_ORIGIN: 'https://other.example'}])
    await expect(checkDeployBackend({vars}, responding(200,401))).rejects.toThrow();
});
