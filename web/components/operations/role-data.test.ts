import { expect, test } from "bun:test";
import type { Context } from "@/lib/operations/types";
import { recentEvents, routeMap, scopedItem } from "./role-data";

const context: Context = {
  actor: { user_id: "synthetic-tech", role: "technician", organization_id: "synthetic-org", crew_id: "crew-one", connection_ids: [], permissions: [] },
  scenario: "synthetic", plan: { routes: [
    { crew_id: "crew-other", stops: [{ work_item_id: "other-work" }] },
    { crew_id: "crew-one", stops: [{ work_item_id: "my-work" }, { work_item_id: "not-in-assignment" }, { work_item_id: "invalid-location" }] },
  ] },
  cases: [{ case_id: "own-case", symptom: "Synthetic report" }], connections: [],
  work_items: [
    { work_item_id: "my-work", source: "A", asset_id: "MTR-1", location: { lat: 45, lon: 25 } },
    { work_item_id: "other-work", source: "C", asset_id: "PT-2", location: { lat: 46, lon: 26 } },
    { work_item_id: "invalid-location", source: "B", location: { lat: NaN, lon: 21 } },
  ],
};
test("role details resolve only records in the server-authorized context", () => {
  expect(scopedItem(context, "case", "own-case")?.symptom).toBe("Synthetic report");
  expect(scopedItem(context, "case", "foreign-case")).toBeUndefined();
  expect(scopedItem(context, "work", "not-in-assignment")).toBeUndefined();
  expect(scopedItem(context, "work", "own-case")).toBeUndefined();
});
test("the technician map joins only own crew stops to authorized work and rejects invalid coordinates", () => {
  const map = routeMap(context);
  expect(map.items.map((item) => item.id)).toEqual(["my-work"]);
  expect(map.bounds.every(Number.isFinite)).toBe(true);
  expect(routeMap({ ...context, work_items: [] }).items).toEqual([]);
  expect(routeMap({ ...context, actor: { ...context.actor, crew_id: "not-assigned" } }).items).toEqual([]);
});
test("activity sorts recorded timestamps without mutating the authorized response", () => {
  const events = [{ event_id: "old", created_at: "2026-11-07T10:00:00Z" }, { event_id: "new", created_at: "2026-11-08T10:00:00Z" }];
  expect(recentEvents({ ...context, events }).map((item) => item.event_id)).toEqual(["new", "old"]);
  expect(events[0].event_id).toBe("old");
});
test("server route gates run before any global queries and never serialize private account fields", () => {
  const script = `
    import {mock} from 'bun:test'; import assert from 'node:assert/strict';
    let user:any=null, globals=0;
    mock.module('server-only',()=>({}));
    mock.module('./lib/server/accounts',()=>({currentUser:async()=>user,toMembership:(u:any)=>u.membership}));
    mock.module('next/server',()=>({connection:async()=>{}}));
    mock.module('./lib/server/queries',()=>({resolveScenario:async()=>"synthetic",loadShellInfo:async()=>{globals++;return{info:{private_global_sentinel:true}}}}));
    const {ScopedPage}=await import('./components/operations/scoped-page');
    const render=async(section:string)=>{const e:any=ScopedPage({section,searchParams:Promise.resolve({})});return e.props.children.type(e.props.children.props)};
    try{await render('cases');assert.fail('anonymous must redirect')}catch(e:any){assert.ok(e.digest.includes('/intra'))}
    assert.equal(globals,0);
    for(const role of ['customer','technician','dispatcher']){
      user={id:'synthetic-account',email:'synthetic@example.test',full_name:null,hash:'PRIVATE_PASSWORD_HASH_SENTINEL',membership:{role,organization_id:'daybreak-demo',crew_id:role==='technician'?'crew-one':null,connection_ids:[],permissions:role==='dispatcher'?['view_console']:[]}};
      for(const section of ['cases','case','activity','work','work-detail','route','connections']){
        globals=0;const allowed=['cases','case','activity'].includes(section)||(role==='technician'&&['work','work-detail','route'].includes(section))||(role==='customer'&&section==='connections');
        if(!allowed){try{await render(section);assert.fail('role must redirect')}catch(e:any){assert.ok(e.digest.includes('/app'))}assert.equal(globals,0);continue}
        const e:any=await render(section);assert.equal(globals,role==='dispatcher'?1:0);assert.equal(e.props.children.props.account.membership.role,role);assert.equal(JSON.stringify(e).includes('PRIVATE_PASSWORD_HASH_SENTINEL'),false);
        if(role!=='dispatcher')assert.equal(e.props.info,undefined);
      }
    }
    console.log('scoped page gates verified');
  `;
  const result = Bun.spawnSync([process.execPath, "-e", script], { cwd: `${import.meta.dir}/../..` });
  expect(result.stderr.toString()).toBe("");
  expect(result.stdout.toString()).toContain("scoped page gates verified");
  expect(result.exitCode).toBe(0);
});
