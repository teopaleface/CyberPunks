export interface TaskView {
  task_id: string; goal: string; scenario: string;
  status: 'queued' | 'running' | 'needs_information' | 'awaiting_confirmation' | 'completed' | 'failed' | 'cancelled' | 'needs_reconciliation';
  plan_version: string; created_at: string; updated_at: string; reply: string;
  result: Record<string, unknown>; proposal: Record<string, unknown> | null; error: string | null;
}
export interface TaskRequest {
  goal: 'analyze_queue' | 'route_brief' | 'case_brief' | 'prepare_operation';
  scenario: string; language?: 'ro' | 'en'; work_item_id?: string; case_id?: string;
  action?: 'create_case' | 'record_verdict' | 'review_work_item' | 'approve_plan' | 'set_availability' | 'request_human';
  data?: Record<string, unknown>; request_key?: string;
}
async function request(path: string, signal: AbortSignal, body?: unknown): Promise<TaskView> {
  const response = await fetch(`/api/conversation/tasks${path}`, {
    method: body === undefined ? 'GET' : 'POST', signal, credentials: 'same-origin', cache: 'no-store',
    headers: {'Content-Type': 'application/json'}, ...(body === undefined ? {} : {body: JSON.stringify(body)}),
  });
  if (!response.ok) throw new Error(response.status === 401 ? 'Your session ended. Sign in again.' : `Task request failed (${response.status}).`);
  return response.json();
}
export const createTask = (body: TaskRequest, signal: AbortSignal) => request('', signal, body);
export const getTask = (id: string, scenario: string, signal: AbortSignal) => request(`/${encodeURIComponent(id)}?scenario=${encodeURIComponent(scenario)}`, signal);
export const resumeTask = (id: string, scenario: string, signal: AbortSignal) => request(`/${encodeURIComponent(id)}/resume?scenario=${encodeURIComponent(scenario)}`, signal, {});
