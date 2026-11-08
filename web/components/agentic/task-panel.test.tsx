import {expect, test} from 'bun:test';
import {renderToStaticMarkup} from 'react-dom/server';
import {TaskPanel} from './task-panel';
import type {TaskView} from '../../lib/agentic/client';
import {prepareRecommendation, type TaskRequest} from '../../lib/agentic/client';
test('synthetic result shows readable review and keeps evidence in disclosure', () => {
  const task = {goal:'analyze_queue', status:'completed', result:{items:[{work_item_id:'synthetic-long-id', recommendation:'human_review', reason:'Crew capacity requires review', evidence:{source:{title:'Meter inspection'}}}]}} as unknown as TaskView;
  const html = renderToStaticMarkup(<TaskPanel task={task} onReview={()=>{}} onResume={()=>{}}/>);
  expect(html).toContain('Meter inspection');
  expect(html).toContain('Review this case before scheduling work.');
  expect(html).toContain('>Review</button>');
  expect(html.indexOf('synthetic-long-id')).toBeGreaterThan(html.indexOf('<details>'));
  expect(html).not.toContain('Continue task');
});

test('changed source hides stale recommendations and review actions', () => {
  const task = {goal:'analyze_queue', result:{snapshot_outdated:true,items:[{work_item_id:'old',reason:'Old recommendation'}]},proposal:null} as unknown as TaskView;
  const html = renderToStaticMarkup(<TaskPanel task={task} onReview={()=>{}} onResume={()=>{}}/>);
  expect(html).toContain('Plan changed');
  expect(html).not.toContain('Old recommendation');
  expect(html).not.toContain('>Review</button>');
});

const syntheticRecommendations = (result: Record<string, unknown> = {}): TaskView => ({
  task_id: 'synthetic-task', goal: 'recommend_queue', scenario: 'synthetic-scenario', status: 'completed',
  plan_version: 'synthetic-v1', created_at: '', updated_at: '', reply: 'Queue reviewed.', proposal: null, error: null,
  result: {decision_source: 'llm', items: ['approve', 'reject', 'defer', null].map((suggested_decision, index) => ({
    title: `Synthetic case ${index}`, work_item_id: `synthetic-work-${index}`, suggested_decision,
    agent_reason: suggested_decision ? `Evidence supports ${suggested_decision}.` : 'Missing field evidence.',
    assessment: {uncertainty: 'high'}, decision: {rule_id: 'original-rule'}, evidence: {source: {title: 'Original source'}},
  })), ...result},
});

test('LLM decisions and explanations cover every row; abstention cannot be applied', () => {
  const html = renderToStaticMarkup(<TaskPanel task={syntheticRecommendations()} onReview={()=>{}} onResume={()=>{}} onPrepareRecommendation={()=>{}}/>);
  for (const decision of ['approve', 'reject', 'defer']) {
    expect(html).toContain(`Recommended decision: ${decision}`);
    expect(html).toContain(`Evidence supports ${decision}.`);
  }
  expect(html).toContain('Recommended decision: No decision');
  expect(html).toContain('Missing field evidence.');
  expect(html.match(/disabled=""/g)).toHaveLength(1);
  expect(html.match(/Review &amp; apply/g)).toHaveLength(4);
  expect(html).toContain('original-rule');
  expect(html).toContain('Original source');
  expect(html).not.toContain('>Review</button>');
});

test('outdated, busy and non-LLM results disable every recommendation without hiding the queue', () => {
  for (const props of [
    {task: syntheticRecommendations({snapshot_outdated: true})},
    {task: syntheticRecommendations(), taskOutdated: true},
    {task: syntheticRecommendations(), busy: true},
    {task: syntheticRecommendations({decision_source: 'rules'})},
  ]) {
    const html = renderToStaticMarkup(<TaskPanel {...props} onReview={()=>{}} onResume={()=>{}} onPrepareRecommendation={()=>{}}/>);
    expect(html.match(/disabled=""/g)).toHaveLength(4);
    expect(html).toContain('Synthetic case 3');
    if (props.taskOutdated || props.task.result.snapshot_outdated) expect(html).toContain('Refresh recommendations');
  }
});

test('recommendation preparation posts only an empty body to the exact saved-row endpoint', async () => {
  const originalFetch = globalThis.fetch;
  const calls: {url: string; init?: RequestInit}[] = [];
  globalThis.fetch = (async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({url: String(url), init});
    return Response.json(syntheticRecommendations());
  }) as typeof fetch;
  try {
    const goal: TaskRequest['goal'] = 'recommend_queue';
    expect(goal).toBe('recommend_queue');
    const controller = new AbortController();
    await prepareRecommendation('synthetic/task', 'synthetic/work?decision=reject', 'synthetic scenario', controller.signal);
    expect(calls).toHaveLength(1);
    expect(calls[0].url).toBe('/api/conversation/tasks/synthetic%2Ftask/recommendations/synthetic%2Fwork%3Fdecision%3Dreject/prepare?scenario=synthetic%20scenario');
    expect(calls[0].init?.method).toBe('POST');
    expect(calls[0].init?.body).toBe('{}');
    expect(calls[0].init?.signal).toBe(controller.signal);
    expect(calls[0].init?.credentials).toBe('same-origin');
  } finally { globalThis.fetch = originalFetch; }
});
