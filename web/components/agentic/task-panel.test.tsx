import {expect, test} from 'bun:test';
import {renderToStaticMarkup} from 'react-dom/server';
import {TaskPanel} from './task-panel';
import type {TaskView} from '../../lib/agentic/client';
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
