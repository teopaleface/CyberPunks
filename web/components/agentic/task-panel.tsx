'use client';
import './task-panel.css';
import type {TaskView} from '../../lib/agentic/client';
type Row = Record<string, unknown>;
const record = (v: unknown): Row => v && typeof v === 'object' ? v as Row : {};
const text = (v: unknown, fallback = 'Not available') => typeof v === 'string' || typeof v === 'number' ? String(v).replaceAll('_', ' ') : fallback;
function Data({value}: {value: unknown}) {
  return <pre className="db-agent-evidence">{JSON.stringify(value, null, 2)}</pre>;
}
export function TaskPanel({task, onReview, onResume}: {task: TaskView; onReview: (work_item_id: string) => void; onResume: (task_id: string) => void}) {
  if (task.result.snapshot_outdated && !task.proposal) return <section className="db-agent-task" role="status"><h3>Plan changed</h3><p>Ask Daybreak for a fresh analysis or route. Previous recommendations are no longer current.</p></section>;
  const rows = Array.isArray(task.result.items) ? task.result.items : [];
  const routes = Array.isArray(task.result.routes) ? task.result.routes : [];
  const cases = Array.isArray(task.result.cases) ? task.result.cases : [];
  return <section aria-label="Task progress and results" className="db-agent-task" style={{overflowWrap: 'anywhere'}}>
    <h3>{text(task.goal)}</h3><p role="status">{text(task.status)}</p><p>{task.reply}</p>
    {task.error && <p role="alert">{task.error}</p>}
    {'complete' in task.result && <p>Coverage: {Array.isArray(task.result.analyzed_ids) ? task.result.analyzed_ids.length : 0} / {text(task.result.total)}. {task.result.complete ? 'Complete' : 'Partial results'}</p>}
    {rows.map((value, index) => {
      const row = record(value), source = record(record(row.evidence).source), assessment = record(row.assessment), decision = record(row.decision);
      return <article key={index} className="db-agent-case">
        <h4>{text(row.title ?? source.title ?? source.name, `Case ${index + 1}`)}</h4>
        <p>{({human_review:'Review this case before scheduling work.', abstain:'Request more evidence before deciding.', request_additional_crews:'Request additional crews; current regional capacity is exhausted.', inspect_on_site:'Recommend an inspection to establish the cause.', preposition_crew:'Consider positioning a crew before the event.', measurement_campaign:'Recommend additional field measurements.'} as Record<string,string>)[typeof row.recommendation === "string" ? row.recommendation : ""] ?? `Proposed action: ${text(row.recommendation).replaceAll('_',' ')}`}</p>
        <p>Reason: {text(row.reason)}</p>
        <p>Uncertainty: {text(assessment.uncertainty ?? assessment.confidence ?? assessment.status)}</p>
        <p>Capacity: {text(decision.capacity_reason ?? decision.capacity_status, decision.rule_id === 'R-B-REGION-CAP' ? 'Additional crews require dispatcher approval' : 'Check capacity before scheduling')}</p>
        {typeof row.work_item_id === 'string' && <button type="button" onClick={() => onReview(row.work_item_id as string)}>Review</button>}
        <details><summary>Technical evidence</summary><Data value={row}/></details>
      </article>;
    })}
    {routes.map((value, index) => {const route = record(value); return <article key={index}><h4>Route {index + 1}</h4><p>{text(route.name ?? route.title, 'Planned technician route')}</p><p>Stops: {Array.isArray(route.stops) ? route.stops.length : 'Not available'}</p><ol>{(Array.isArray(route.stops) ? route.stops : []).map((value, stopIndex) => { const stop = record(value); return <li key={stopIndex}><p>{stopIndex + 1}. {text(stop.title ?? stop.asset_id, 'Planned visit')}</p><p>Planned arrival: {text(stop.eta)}</p><p>{text(stop.reason)}</p></li>; })}</ol><details><summary>Route evidence</summary><Data value={route}/></details></article>;})}
    {cases.map((value, index) => {const c = record(value); return <article key={index}><h4>{text(c.title ?? c.subject, `Case ${index + 1}`)}</h4><p>{text(c.status)}</p><p>{text(c.summary ?? c.description)}</p><details><summary>Case evidence</summary><Data value={c}/></details></article>;})}
    {task.proposal && <p>Proposal prepared. Confirm in the authenticated application.</p>}
    <details><summary>All technical evidence</summary><p>Historical scenario: {task.scenario}. Plan version: {task.plan_version}</p><Data value={task.result}/><Data value={task.proposal}/></details>
    {task.status === 'awaiting_confirmation' && <button type="button" onClick={() => onResume(task.task_id)}>Check confirmed result</button>}
    {['running', 'queued'].includes(task.status) && <button type="button" onClick={() => onResume(task.task_id)}>Resume authorized task</button>}
    {task.status === 'failed' && <p>Start a fresh task after checking the error.</p>}
  </section>;
}
