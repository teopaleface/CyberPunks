import {afterAll, afterEach, beforeAll, beforeEach, describe, expect, mock, test} from 'bun:test';
import {act, type ComponentType} from 'react';
import type {Root} from 'react-dom/client';
import type {Context, Proposal, WorkspaceAccount} from '@/lib/operations/types';
import type {TaskView} from '@/lib/agentic/client';
import type {WorkspaceProps} from './workspace';
import {conversationScope} from '@/lib/operations/conversation-store';

// Isolated UI fixtures are synthetic. No backend, live data or real operations are called.
// Run with WORKSPACE_DOM_TEST_MODULE=/absolute/path/to/happy-dom/lib/index.js bun test <this file>.
// happy-dom can be installed in a temporary directory, without changing repository dependencies.
describe.skipIf(!process.env.WORKSPACE_DOM_TEST_MODULE)('workspace turn and recommendation interactions', () => {
  let Workspace: ComponentType<WorkspaceProps>;
  let createRoot: typeof import('react-dom/client').createRoot;
  let root: Root;
  let container: HTMLDivElement;
  let dom: {happyDOM: {abort: () => Promise<void>}};
  const originalFetch = globalThis.fetch;
  const originalGlobals = new Map<string, PropertyDescriptor | undefined>();
  const account: WorkspaceAccount = {id: 'synthetic-dispatcher', email: 'synthetic@example.test', name: 'Synthetic dispatcher', membership: {role: 'dispatcher', organization_id: 'synthetic-org', crew_id: null, connection_ids: [], permissions: ['review_work_item']}};
  const proposal: Proposal = {proposal_id: 'synthetic-proposal', action: 'review_work_item', summary: 'Defer the synthetic work until access is available.', scenario: 'synthetic-scenario', data: {work_item_id: 'synthetic-work', decision: 'defer', note: 'Access is unavailable.', plan_version: 'synthetic-v1'}, expires_at: '2099-01-01T00:00:00Z'};
  const task: TaskView = {task_id: 'synthetic-task', goal: 'recommend_queue', scenario: 'synthetic-scenario', status: 'completed', plan_version: 'synthetic-v1', created_at: '', updated_at: '', error: null, proposal: null, reply: 'Concrete decisions are ready for review.', result: {decision_source: 'llm', items: [{work_item_id: 'synthetic-work', title: 'Synthetic CarasSeverin inspection', suggested_decision: 'defer', agent_reason: 'Access is unavailable.', assessment: {status: 'available'}, decision: {rule_id: 'original-rule'}, evidence: {}}, {work_item_id: 'synthetic-other', title: 'Synthetic other work', suggested_decision: 'approve', agent_reason: 'Evidence supports inspection.', evidence: {}}, {work_item_id: 'synthetic-abstain', title: 'Synthetic insufficient evidence', suggested_decision: null, agent_reason: 'Missing field evidence.', evidence: {}}]}};
  let context: Context;
  let calls: {path: string; body: unknown}[];
  let chatReply: unknown;
  let chatFailure: boolean;
  let pendingChat: (() => void) | undefined;
  let holdChat: boolean;
  let prepareFailure: boolean;
  let voiceTurn: (input: string) => Promise<unknown>;

  beforeAll(async () => {
    const {Window} = await import(process.env.WORKSPACE_DOM_TEST_MODULE!);
    const window = new Window({url: 'http://synthetic.test'});
    dom = window;
    for (const key of ['window', 'document', 'navigator', 'HTMLElement', 'HTMLTextAreaElement', 'Node', 'Event', 'MouseEvent', 'CustomEvent', 'getComputedStyle']) {
      originalGlobals.set(key, Object.getOwnPropertyDescriptor(globalThis, key));
      Object.defineProperty(globalThis, key, {configurable: true, writable: true, value: key === 'window' ? window : key === 'getComputedStyle' ? window.getComputedStyle.bind(window) : window[key]});
    }
    originalGlobals.set('IS_REACT_ACT_ENVIRONMENT', Object.getOwnPropertyDescriptor(globalThis, 'IS_REACT_ACT_ENVIRONMENT'));
    Object.defineProperty(globalThis, 'IS_REACT_ACT_ENVIRONMENT', {configurable: true, value: true});
    window.HTMLElement.prototype.scrollIntoView = () => {};
    mock.module('./voice', () => ({Voice: ({turn}: {turn: typeof voiceTurn}) => {
      voiceTurn = turn;
      return <p>Synthetic voice adapter</p>;
    }}));
    ({createRoot} = await import('react-dom/client'));
    ({Workspace} = await import('./workspace'));
  });
  beforeEach(() => {
    window.sessionStorage.clear();
    context = {actor: {...account.membership, user_id: account.id, organization_id: 'synthetic-org'}, scenario: 'synthetic-scenario', plan: {version: 'synthetic-v1'}, connections: [], cases: [], work_items: [{work_item_id: 'synthetic-work', title: 'Synthetic CarasSeverin inspection'}, {work_item_id: 'synthetic-other'}, {work_item_id: 'synthetic-abstain'}], pending_proposals: [{...proposal}], pending_commands: []};
    calls = [];
    chatReply = {reply: task.reply, task, provider: 'synthetic'};
    chatFailure = false;
    holdChat = false;
    prepareFailure = false;
    pendingChat = undefined;
    globalThis.fetch = (async (input: string | Request | URL, init?: RequestInit) => {
      const path = String(input);
      const body = init?.body ? JSON.parse(String(init.body)) : undefined;
      calls.push({path, body});
      if (path.startsWith('/api/operations/context?')) return Response.json(context);
      if (path === '/api/conversation/chat') {
        if (holdChat) await new Promise<void>((resolve) => {pendingChat = resolve;});
        if (chatFailure) return Response.json({error: 'Synthetic request failed.'}, {status: 503});
        return Response.json(chatReply);
      }
      if (path.includes('/recommendations/')) return prepareFailure ? Response.json({error: 'Snapshot changed.'}, {status: 409}) : Response.json({...task, task_id: 'synthetic-child', goal: 'prepare_operation', status: 'awaiting_confirmation', proposal});
      if (path === '/api/operations/proposals/synthetic-proposal/confirm') {
        context = {...context, plan: {version: 'synthetic-v2'}};
        return Response.json({command_id: 'synthetic-command', status: 'succeeded', result: {decision: 'defer'}});
      }
      if (path === '/api/operations/proposals') return Response.json(proposal);
      throw new Error(`Unexpected UI request: ${path}`);
    }) as typeof fetch;
    container = document.createElement('div');
    document.body.append(container);
    root = createRoot(container);
  });
  afterEach(async () => {
    await act(async () => root.unmount());
    container.remove();
    globalThis.fetch = originalFetch;
  });
  afterAll(async () => {
    await dom.happyDOM.abort();
    for (const [key, descriptor] of originalGlobals) {
      if (descriptor) Object.defineProperty(globalThis, key, descriptor);
      else Reflect.deleteProperty(globalThis, key);
    }
  });
  const content = () => container.textContent ?? '';
  const buttons = (name: string) => [...container.querySelectorAll('button')].filter((button) => button.textContent === name);
  async function waitFor(check: () => boolean) {
    for (let i = 0; i < 100; i++) {
      if (check()) return;
      await act(async () => {await new Promise((resolve) => setTimeout(resolve, 5));});
    }
    throw new Error('UI did not reach expected state.');
  }
  async function mount(presentation: 'main' | 'assistant' = 'main') {
    await act(async () => root.render(<Workspace account={account} presentation={presentation} scenario="synthetic-scenario"/>));
    await waitFor(() => container.querySelector('textarea')?.disabled === false);
  }
  async function click(name: string, index = 0) {
    const button = buttons(name)[index];
    expect(button).toBeDefined();
    expect(button.disabled).toBe(false);
    await act(async () => button.click());
  }
  async function send(input: string) {
    const textarea = container.querySelector('textarea')!;
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value')!.set!.call(textarea, input);
      textarea.dispatchEvent(new Event('input', {bubbles: true}));
    });
    await act(async () => textarea.closest('form')!.dispatchEvent(new Event('submit', {bubbles: true, cancelable: true})));
  }

  test('one-click Romanian request reviews the exact saved decision before the existing Confirm executes it', async () => {
    await mount();
    await click('Recommend decisions');
    await waitFor(() => buttons('Review & apply').length === 3);
    const chat = calls.find((call) => call.path === '/api/conversation/chat')!;
    expect((chat.body as {message: string}).message).toContain('Recomandă decizii concrete pentru întreaga coadă');
    expect(content()).toContain('Recommended decision: defer');
    expect(content()).toContain('Access is unavailable.');
    expect(buttons('Review & apply')[2].disabled).toBe(true);
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
    await click('Review & apply');
    await waitFor(() => buttons('Confirm').length === 1);
    expect(calls.find((call) => call.path.includes('/recommendations/'))).toEqual({path: '/api/conversation/tasks/synthetic-task/recommendations/synthetic-work/prepare?scenario=synthetic-scenario', body: {}});
    expect(calls.some((call) => call.path === '/api/operations/proposals')).toBe(false);
    expect(buttons('Edit')).toHaveLength(0);
    expect(content()).toContain(proposal.summary);
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
    await click('Confirm');
    await waitFor(() => content().includes('Your request was saved.'));
    expect(calls.filter((call) => call.path.endsWith('/confirm'))).toEqual([{path: '/api/operations/proposals/synthetic-proposal/confirm', body: {}}]);
    expect(content()).toContain('Refresh recommendations');
    expect(buttons('Review & apply').every((button) => button.disabled)).toBe(true);
  });

  for (const outcome of ['refusal', 'read', 'error'] as const) test(`new ${outcome} turn clears the old Saved card and task immediately; durable drafts remain`, async () => {
    await mount('assistant');
    await click('Voice');
    await click('Text');
    await send('Recomandă decizii concrete pentru întreaga coadă.');
    await waitFor(() => buttons('Review & apply').length === 3);
    await click('Review & apply');
    await click('Confirm');
    await waitFor(() => content().includes('Your request was saved.'));
    // Replay a turn callback with the old Saved card still mounted. Text and voice
    // share this same turn() path; no Back to chat cleanup can mask the regression.
    expect(content()).toContain('Queue recommendations');
    chatReply = {reply: outcome === 'refusal' ? 'I cannot delete all CarasSeverin tickets.' : 'The queue is unchanged.', provider: 'synthetic'};
    chatFailure = outcome === 'error';
    holdChat = true;
    let nextTurn: Promise<unknown>;
    await act(async () => { nextTurn = voiceTurn('Șterge toate tichetele din CarasSeverin.').catch(() => {}); });
    await waitFor(() => Boolean(pendingChat));
    expect(content()).not.toContain('Queue recommendations');
    expect(container.querySelector('[aria-label="Request result"]')).toBeNull();
    expect(container.querySelector('[aria-label="Action proposal"]')).toBeNull();
    expect(window.sessionStorage.getItem([...Array(window.sessionStorage.length)].map((_, i) => window.sessionStorage.key(i)!).find((key) => key.startsWith('agentic-task:')) ?? 'missing')).toBeNull();
    await act(async () => {pendingChat!(); await nextTurn!;});
    await waitFor(() => outcome === 'error' ? content().includes('Synthetic request failed.') : content().includes((chatReply as {reply: string}).reply));
    expect(container.querySelector('[aria-label="Request result"]')).toBeNull();
    expect(container.querySelector('[aria-label="Action proposal"]')).toBeNull();
    expect(content()).not.toContain('Queue recommendations');
    expect(content()).toContain('Drafts and pending requests');
  });

  test('chat yes never confirms and ordinary proposals retain their Edit flow', async () => {
    chatReply = {reply: 'Review your draft.', proposal, provider: 'synthetic'};
    await mount();
    await send('Prepare a defer decision.');
    await waitFor(() => buttons('Confirm').length === 1);
    expect(buttons('Edit')).toHaveLength(1);
    await click('Edit');
    expect(container.querySelector('form')).not.toBeNull();
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
    await click('Back to chat');
    chatReply = {reply: 'Use Confirm to save your request.', provider: 'synthetic'};
    await send('yes');
    await waitFor(() => content().includes('Use Confirm to save your request.'));
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
    expect(container.querySelector('[aria-label="Action proposal"]')).toBeNull();
  });

  test('changed plan disables old recommendations before any preparation request', async () => {
    context = {...context, plan: {version: 'synthetic-v2'}};
    await mount();
    await click('Recommend decisions');
    await waitFor(() => buttons('Review & apply').length === 3);
    expect(content()).toContain('Refresh recommendations');
    for (const button of buttons('Review & apply')) {
      expect(button.disabled).toBe(true);
      await act(async () => button.click());
    }
    expect(calls.some((call) => call.path.includes('/recommendations/'))).toBe(false);
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
  });

  test('server snapshot rejection disables remaining recommendations and never opens a proposal', async () => {
    prepareFailure = true;
    await mount();
    await click('Recommend decisions');
    await waitFor(() => buttons('Review & apply').length === 3);
    await click('Review & apply');
    await waitFor(() => content().includes('Refresh recommendations'));
    expect(buttons('Review & apply').every((button) => button.disabled)).toBe(true);
    expect(container.querySelector('[aria-label="Action proposal"]')).toBeNull();
    expect(calls.some((call) => call.path.endsWith('/confirm'))).toBe(false);
  });

  test('a delayed saved-task restore cannot reappear after a new read-only turn', async () => {
    window.sessionStorage.setItem(`agentic-task:${conversationScope(account, 'synthetic-scenario')}`, 'synthetic-old-task');
    const regularFetch = globalThis.fetch;
    let restore: (() => void) | undefined;
    globalThis.fetch = (async (input: string | Request | URL, init?: RequestInit) => {
      if (String(input) === '/api/conversation/tasks/synthetic-old-task?scenario=synthetic-scenario') {
        await new Promise<void>((resolve) => {restore = resolve;});
        return Response.json({...task, task_id: 'synthetic-old-task'});
      }
      return regularFetch(input, init);
    }) as typeof fetch;
    chatReply = {reply: 'The queue is unchanged.', provider: 'synthetic'};
    await mount();
    expect(restore).toBeDefined();
    await send('Care este starea cozii?');
    await waitFor(() => content().includes('The queue is unchanged.'));
    await act(async () => {restore!();});
    expect(content()).not.toContain('Queue recommendations');
    expect(container.querySelector('[aria-label="Action proposal"]')).toBeNull();
    expect(window.sessionStorage.getItem(`agentic-task:${conversationScope(account, 'synthetic-scenario')}`)).toBeNull();
  });
});
