"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowLeft, ArrowRight, CalendarDays, Check, ChevronLeft, ChevronRight, Clock3, FileText, MapPin, MessageSquare, Plus, RefreshCw, Search, ShieldCheck, Wrench, Zap } from "lucide-react";
import { Card, PageTitle, Pill, KV } from "@/components/ds";
import { DataCard, SimilarCard } from "@/components/item/parts";
import type { WorkItem } from "@/lib/contracts";
import { api, SessionExpired } from "@/lib/operations/client";
import { findingText, rows, text, type Action, type Context, type Row, type WorkspaceAccount } from "@/lib/operations/types";
import { englishText } from "@/lib/english";
import { canPrepare, readableDate, requestAssistant } from "@/components/workspace/scope";
import { assignedVisits, caseNextStep, caseStatus, dashboardTitle, newestCases, nextApprovedVisit, routeIsApproved, shortCaseReference, verifiedTimeline } from "@/components/workspace/role-dashboard-model";
import { EVENT_NAMES, ownRoute, recentEvents, record, routeMap, scopedItem } from "./role-data";
import "./role-area.css";

const PlanMap = dynamic(() => import("@/components/plan/plan-map").then((module) => module.PlanMap), { ssr: false, loading: () => <div className="ra-map-loading" role="status">Loading your route map…</div> });
export type RoleSection = "cases" | "case" | "work" | "work-detail" | "route" | "connections" | "activity";
const titles: Record<RoleSection, string> = { cases: "Service cases", case: "Case details", work: "Assigned work", "work-detail": "Work details", route: "My route", connections: "My connections", activity: "Activity" };

export function RoleArea({ account, scenario, section, itemId }: { account: WorkspaceAccount; scenario: string; section: RoleSection; itemId?: string }) {
  const [context, setContext] = useState<Context | null>(null);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const [loading, setLoading] = useState(true);
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const next = await api<Context>(`operations/context?scenario=${encodeURIComponent(scenario)}`);
      if (next.scenario !== scenario || next.actor.user_id !== account.id || next.actor.role !== account.membership.role)
        throw new Error("Your access changed. Return to the assistant and open this page again.");
      setContext(next);
      setError("");
    } catch (issue) {
      setContext(null);
      setExpired(issue instanceof SessionExpired);
      setError(issue instanceof Error ? issue.message : "Your workspace could not load. Try again.");
    } finally { setLoading(false); }
  }, [account.id, account.membership.role, scenario]);
  useEffect(() => { const timer = setTimeout(() => { void refresh(); }, 0); return () => clearTimeout(timer); }, [refresh]);
  useEffect(() => {
    const changed = () => { void refresh(); };
    window.addEventListener("daybreak:changed", changed);
    return () => window.removeEventListener("daybreak:changed", changed);
  }, [refresh]);
  const role = account.membership.role;
  const request = (selection: { case_id?: string; work_item_id?: string; connection_id?: string }, action?: Action, data?: Row) => requestAssistant(selection, action, data, scenario);
  const path = (url: string) => `${url}?scenariu=${encodeURIComponent(scenario)}`;
  const title = section === "cases" ? role === "customer" ? "My cases" : role === "technician" ? "Shared cases" : "Service cases" : titles[section];
  const subtitle = section === "work" ? "Your crew’s assignments and the evidence for each visit." : section === "cases" ? role === "customer" ? "Follow your reports and what happens next." : "Reports, field findings and follow-up in one place." : section === "route" ? "Your crew’s planned stops, in order." : section === "connections" ? "The service connections linked to your account." : section === "activity" ? "Recorded updates for the cases you can access." : "Current information, verified for your account.";
  return <div className="role-area">
    <PageTitle title={title} subtitle={subtitle} actions={<div className="ra-actions"><button className="ra-icon" onClick={() => void refresh()} disabled={loading} aria-label="Refresh this page"><RefreshCw size={17} /></button>{section === "cases" && role === "customer" && context && canPrepare(context, "create_case") ? <button className="ra-primary" onClick={() => request({}, "create_case", {})}><Plus size={16} />Report a problem</button> : null}<Link className="ra-button" href={path("/app")}><MessageSquare size={16} />Ask Daybreak</Link></div>} />
    <p className="ra-provenance"><span className="ra-demo-dot" />Synthetic demo{context ? ` · ${readableDate(context.plan.plan_date)}` : ""}{role === "technician" && account.membership.crew_id ? ` · Crew ${account.membership.crew_id}` : ""}</p>
    {error ? <div className="ra-error" role="alert"><p>{error}</p>{expired ? <Link href="/intra">Sign in again</Link> : <button className="ra-button" onClick={() => void refresh()}>Try again</button>}</div> : null}
    {!context && !error ? <div className="ra-loading" role="status">Loading your authorized information…</div> : null}
    {context ? <>
      {section === "cases" ? <Cases context={context} path={path} /> : null}
      {section === "case" ? <CaseDetail context={context} item={scopedItem(context, "case", itemId)} path={path} request={request} /> : null}
      {section === "work" ? <WorkList context={context} path={path} /> : null}
      {section === "work-detail" ? <WorkDetail context={context} item={scopedItem(context, "work", itemId)} path={path} request={request} /> : null}
      {section === "route" ? <Route context={context} path={path} request={request} /> : null}
      {section === "connections" ? <Connections context={context} path={path} request={request} /> : null}
      {section === "activity" ? <Activity context={context} path={path} /> : null}
    </> : null}
  </div>;
}
type Shared = { context: Context; path: (url: string) => string };
type Request = (selection: { case_id?: string; work_item_id?: string; connection_id?: string }, action?: Action, data?: Row) => void;
function SearchBox({ value, onChange, label }: { value: string; onChange: (value: string) => void; label: string }) {
  return <label className="ra-search"><Search size={17} aria-hidden="true" /><input type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={label} aria-label={label} /></label>;
}
function Pager({ count, page, onPage, size = 8 }: { count: number; page: number; onPage: (page: number) => void; size?: number }) {
  const max = Math.max(0, Math.ceil(count / size) - 1);
  return <nav className="ra-pagination" aria-label="Results pages"><span>{count ? `${page * size + 1}–${Math.min(count, (page + 1) * size)} of ${count}` : "0 results"}</span><div><button className="ra-icon" aria-label="Previous page" disabled={!page} onClick={() => onPage(page - 1)}><ChevronLeft size={17} /></button><span>{page + 1} / {max + 1}</span><button className="ra-icon" aria-label="Next page" disabled={page >= max} onClick={() => onPage(page + 1)}><ChevronRight size={17} /></button></div></nav>;
}
function Cases({ context, path }: Shared) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [page, setPage] = useState(0);
  const all = newestCases(context.cases);
  const items = all.filter((item) => `${dashboardTitle(item)} ${text(item.case_id)} ${caseStatus(item).label}`.toLowerCase().includes(query.toLowerCase()) && (status === "all" || caseStatus(item).label === status));
  const currentPage = Math.min(page, Math.max(0, Math.ceil(items.length / 8) - 1));
  return <Card title={<span>Cases <span className="ra-count">{all.length}</span></span>} bodyClassName="ra-table-body"><div className="ra-table-toolbar"><SearchBox value={query} onChange={(value) => { setQuery(value); setPage(0); }} label="Search cases" /><label className="ra-status-filter">Status<select value={status} onChange={(event) => { setStatus(event.target.value); setPage(0); }}><option value="all">All statuses</option>{[...new Set(all.map((item) => caseStatus(item).label))].map((value) => <option key={value}>{value}</option>)}</select></label></div>
    <div className="ra-table-scroll"><table className="ra-table"><thead><tr><th>Case</th><th>Status</th><th>Next step</th><th>Opened</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{items.slice(currentPage * 8, currentPage * 8 + 8).map((item) => <tr key={text(item.case_id)}><td><Link className="ra-row-title" href={path(`/cazuri/${encodeURIComponent(text(item.case_id))}`)}>{dashboardTitle(item)}</Link><span className="ra-row-meta">{shortCaseReference(item)}</span></td><td><Status item={item} /></td><td>{caseNextStep(item).short}</td><td className="ra-soft">{readableDate(item.created_at)}</td><td><Link className="ra-icon" aria-label={`Open case ${shortCaseReference(item)}`} href={path(`/cazuri/${encodeURIComponent(text(item.case_id))}`)}><ArrowRight size={17} /></Link></td></tr>)}</tbody></table></div>
    {!items.length ? <Empty title={query || status !== "all" ? "No matching cases" : "No cases yet"}>Your reports and their updates will appear here.</Empty> : null}<Pager count={items.length} page={currentPage} onPage={setPage} />
  </Card>;
}
function Status({ item }: { item: Row }) { const status = caseStatus(item); return <Pill size="sm" tone={status.tone}>{status.label}</Pill>; }
function Empty({ title, children }: { title: string; children: ReactNode }) { return <div className="ra-empty"><FileText size={25} aria-hidden="true" /><h2>{title}</h2><p>{children}</p></div>; }
function CaseDetail({ context, item, path, request }: Shared & { item?: Row; request: Request }) {
  if (!item) return <Empty title="Case unavailable">This case is not available to your account. <Link href={path("/cazuri")}>Back to cases</Link></Empty>;
  const caseId = text(item.case_id), outcome = findingText(item), next = caseNextStep(item), assessment = record(item.assessment);
  const connection = context.connections.find((entry) => entry.connection_id === item.connection_id);
  return <><Link className="ra-back" href={path("/cazuri")}><ArrowLeft size={15} />All cases</Link><div className="ra-detail-grid"><Card className="ra-detail-main"><div className="ra-detail-top"><span className="ra-kicker">{shortCaseReference(item)}</span><Status item={item} /></div><h2 className="ra-detail-title">{dashboardTitle(item)}</h2><p className="ra-soft ra-spaced">Reported {readableDate(item.created_at)}</p>{outcome ? <div className="ra-finding"><ShieldCheck size={19} /><p>{outcome}</p></div> : null}<div className="ra-next"><h3>What happens next</h3><p>{next.detail}</p></div><div className="ra-actions ra-spaced">{canPrepare(context, "set_availability") ? <button className="ra-button" onClick={() => request({ case_id: caseId }, "set_availability", { case_id: caseId })}><CalendarDays size={16} />Share availability</button> : null}<button className="ra-button" onClick={() => request({ case_id: caseId }, "request_human", { case_id: caseId })}>Ask for human help</button><button className="ra-text" onClick={() => request({ case_id: caseId })}>Ask Daybreak<ArrowRight size={14} /></button></div></Card>
      <Card title="Case information"><KV k="Connection" v={connection ? dashboardTitle(connection, "Service connection") : "Linked service connection"} /><KV k="Problem" v={text(item.symptom_type) || "Not specified"} /><KV k="Opened" v={readableDate(item.created_at)} /><KV k="Last update" v={readableDate(item.updated_at ?? item.created_at)} />{item.human_requested ? <p className="ra-help-note">Human follow-up has been requested.</p> : null}</Card>
      <Card title="Recorded updates"><CaseTimeline context={context} item={item} />{rows(item.availability).length ? <div className="ra-spaced"><h3 className="ra-small-title">Access availability</h3>{rows(item.availability).map((slot, index) => <p className="ra-soft" key={index}>{readableDate(slot.start)} – {readableDate(slot.end)}</p>)}</div> : null}</Card>
      <Card title="Assessment"><p>{assessment.status === "available" ? "An assessment is available for this report. It helps the team decide the next action." : "The team needs to review the available information before relying on a model assessment."}</p>{text(assessment.reason) ? <p className="ra-soft ra-spaced">{englishText(text(assessment.reason))}</p> : null}<p className="ra-soft ra-spaced">An estimate is not a confirmed fault, repair or arrival time.</p></Card>
    </div></>;
}
function CaseTimeline({ context, item }: { context: Context; item: Row }) {
  const entries = verifiedTimeline(context, item);
  return entries.length ? <ol className="ra-timeline">{entries.map((entry) => <li key={entry.key}><span className="ra-timeline-mark"><Check size={12} /></span><div><strong>{entry.title}</strong><span>{entry.date}</span></div></li>)}</ol> : <p className="ra-soft">No recorded updates yet.</p>;
}
function WorkList({ context, path }: Shared) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const all = assignedVisits(context);
  const items = all.filter((item) => `${dashboardTitle(item)} ${text(item.work_item_id)} ${text(record(item.location).label)}`.toLowerCase().includes(query.toLowerCase()));
  const currentPage = Math.min(page, Math.max(0, Math.ceil(items.length / 8) - 1));
  return <Card title={<span>Visits <span className="ra-count">{all.length}</span></span>} bodyClassName="ra-table-body"><div className="ra-table-toolbar"><SearchBox value={query} onChange={(value) => { setQuery(value); setPage(0); }} label="Search your assigned work" /><span className="ra-soft">Crew {context.actor.crew_id}</span></div><div className="ra-table-scroll"><table className="ra-table"><thead><tr><th>Work / asset</th><th>Location</th><th>Planned arrival</th><th>Decision</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>{items.slice(currentPage * 8, currentPage * 8 + 8).map((item) => <tr key={text(item.work_item_id)}><td><Link className="ra-row-title" href={path(`/sarcini/${encodeURIComponent(text(item.work_item_id))}`)}>{dashboardTitle(item)}</Link><span className="ra-row-meta">{text(item.work_item_id)}</span></td><td>{text(record(item.location).label) || text(record(item.location).zone_id) || "Not provided"}</td><td>{item.planned_start ? readableDate(item.planned_start) : "Not scheduled"}</td><td><Pill size="sm" tone="grey">{decisionName(text(record(item.decision).decision))}</Pill></td><td><Link className="ra-icon" aria-label={`Open ${dashboardTitle(item)}`} href={path(`/sarcini/${encodeURIComponent(text(item.work_item_id))}`)}><ArrowRight size={17} /></Link></td></tr>)}</tbody></table></div>{!items.length ? <Empty title="No assigned work to show">Assignments appear after the dispatcher includes them in your crew’s plan.</Empty> : null}<Pager count={items.length} page={currentPage} onPage={setPage} /></Card>;
}
function decisionName(value: string) { return ({ assigned: "Assigned", human_review: "Needs review", deferred: "Deferred", remote_action: "Remote action", notify: "Notification planned", rejected_invalid: "Invalid data" } as Record<string, string>)[value] ?? "Awaiting decision"; }
function WorkDetail({ context, item, path, request }: Shared & { item?: Row; request: Request }) {
  if (!item) return <Empty title="Work unavailable">This work is not in your current assignment. <Link href={path("/sarcini")}>Back to assigned work</Link></Empty>;
  const id = text(item.work_item_id), work = assignedVisits(context).find((entry) => entry.work_item_id === id) ?? item;
  const explanation = record(item.explanation), assessment = record(item.assessment), decision = record(item.decision), location = record(item.location);
  const cases = context.cases.filter((entry) => entry.work_item_id === id);
  const validTechnical = ["A", "B", "C"].includes(text(item.source)) && Array.isArray(explanation.top_factors) && Array.isArray(record(item.data_quality).data_sources) && typeof record(item.data_quality).missing_ratio === "number";
  return <><Link className="ra-back" href={path("/sarcini")}><ArrowLeft size={15} />Assigned work</Link><div className="ra-detail-grid"><Card><div className="ra-detail-top"><span className="ra-kicker">{text(item.asset_id)}</span><Pill tone="blue" size="sm">{decisionName(text(decision.decision))}</Pill></div><h2 className="ra-detail-title">{dashboardTitle(item)}</h2><p className="ra-soft ra-spaced"><MapPin size={15} className="ra-inline" />{text(location.label) || text(location.zone_id) || "Location not provided"}</p><p className="ra-soft"><Clock3 size={15} className="ra-inline" />{work.planned_start ? `Planned arrival ${readableDate(work.planned_start)}` : "No planned arrival time"}</p><div className="ra-next"><h3>Why this visit?</h3><p>{englishText(text(decision.reason_ro) || text(explanation.summary_ro) || "Inspect the assigned asset and record what you find.")}</p></div><div className="ra-actions ra-spaced">{canPrepare(context, "record_verdict") ? <button className="ra-primary" onClick={() => request({ work_item_id: id }, "record_verdict", { work_item_id: id })}><Wrench size={16} />Record finding</button> : null}<button className="ra-button" onClick={() => request({ work_item_id: id })}>Ask about this visit</button></div></Card>
      <Card title="Model evidence"><KV k="Assessment" v={assessment.status === "available" ? "Available" : "Needs human review"} /><KV k="Model" v={text(assessment.model_version) || "Not available"} /><KV k="Target date" v={readableDate(assessment.target_date)} />{assessment.status === "available" && typeof assessment.score === "number" && Number.isFinite(assessment.score) && assessment.score >= 0 && assessment.score <= 1 ? <KV k="Model score" v={assessment.score.toFixed(2)} /> : null}{text(assessment.reason) ? <p className="ra-soft ra-spaced">{englishText(text(assessment.reason))}</p> : null}<p className="ra-soft ra-spaced">This estimate does not confirm that a repair has been made.</p></Card>
      {validTechnical ? <><DataCard w={item as unknown as WorkItem} /><SimilarCard w={item as unknown as WorkItem} /></> : null}
      <Card title="Contributing factors"><ul className="ra-factor-list">{rows(explanation.top_factors).slice(0, 6).map((factor, index) => <li key={text(factor.feature) || index}><span>{englishText(text(factor.label_ro) || text(factor.feature))}</span>{typeof factor.value === "number" || typeof factor.value === "string" ? <strong>{text(factor.value)}</strong> : null}</li>)}</ul>{!rows(explanation.top_factors).length ? <p className="ra-soft">No contributing factors are available for this assessment.</p> : null}</Card>
      <Card title="Linked service cases">{cases.length ? <ul className="ra-link-list">{cases.map((entry) => <li key={text(entry.case_id)}><Link href={path(`/cazuri/${encodeURIComponent(text(entry.case_id))}`)}><div><strong>{dashboardTitle(entry)}</strong><span>{shortCaseReference(entry)}</span></div><Status item={entry} /></Link>{findingText(entry) ? <p className="ra-soft">{findingText(entry)}</p> : null}</li>)}</ul> : <p className="ra-soft">No service case is linked to this visit.</p>}</Card>
    </div></>;
}
function Route({ context, path, request }: Shared & { request: Request }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const visits = assignedVisits(context), route = ownRoute(context), next = nextApprovedVisit(context, visits), approved = routeIsApproved(context), map = routeMap(context);
  const stops = rows(route?.stops).flatMap((stop) => { const work = visits.find((item) => item.work_item_id === stop.work_item_id); return work ? [{ ...work, ...stop }] : []; });
  const current = visits.find((item) => item.work_item_id === selectedId) ?? next;
  return <><div className="ra-route-summary"><div><Pill size="sm" tone={approved ? "blue" : "amber"}>{approved ? "Approved route" : "Awaiting approval"}</Pill><h2>{context.actor.crew_id ? `Crew ${context.actor.crew_id}` : "No crew linked"}</h2><p className="ra-soft">{stops.length} planned stops · {readableDate(context.plan.plan_date)}</p></div>{next ? <div><span className="ra-kicker">Next approved visit</span><strong>{dashboardTitle(next)}</strong><span className="ra-soft">Planned {readableDate(next.planned_start)}</span></div> : <p className="ra-soft">{approved ? "No next stop is available in the approved plan." : "A dispatcher must approve the route before a next stop is confirmed."}</p>}</div>
    <div className="ra-route-grid"><Card title="Planned stops"><ol className="ra-stops">{stops.map((stop, index) => <li key={text(stop.work_item_id)} data-selected={stop.work_item_id === current?.work_item_id ? "true" : undefined}><span className="ra-stop-number">{index + 1}</span><div><button className="ra-stop-select" onClick={() => setSelectedId(text(stop.work_item_id))}>{dashboardTitle(stop)}</button><p className="ra-soft">Planned {readableDate(stop.eta ?? stop.planned_start)}</p><Link className="ra-text" href={path(`/sarcini/${encodeURIComponent(text(stop.work_item_id))}`)}>Open visit<ArrowRight size={14} /></Link></div></li>)}</ol>{!stops.length ? <Empty title="No route yet">Your planned stops will appear here after assignment.</Empty> : null}</Card>
      <div className="ra-route-map-column">{map.items.length ? <div className="ra-route-map"><PlanMap items={map.items} routes={[]} depots={[]} bounds={map.bounds} selectedId={current ? text(current.work_item_id) : null} onSelect={setSelectedId} className="h-full w-full" padding={{ top: 40, right: 35, bottom: 45, left: 35 }} /></div> : <Card title="Route map"><Empty title="No verified map locations">Stop descriptions remain available in the route list.</Empty></Card>}<p className="ra-map-note">Planned locations only. Times are not live arrival estimates, and this map is not road navigation.</p>{current ? <Card title="Selected visit"><h3 className="ra-small-title">{dashboardTitle(current)}</h3><p className="ra-soft ra-spaced">{englishText(text(record(current.decision).reason_ro)) || "Open this visit to review the evidence and record a finding."}</p><div className="ra-actions ra-spaced"><Link className="ra-button" href={path(`/sarcini/${encodeURIComponent(text(current.work_item_id))}`)}>View work details</Link><button className="ra-text" onClick={() => request({ work_item_id: text(current.work_item_id) })}>Ask Daybreak<ArrowRight size={14} /></button></div></Card> : null}</div>
    </div></>;
}
function Connections({ context, path, request }: Shared & { request: Request }) {
  return context.connections.length ? <div className="ra-connection-grid">{context.connections.map((item) => { const id = text(item.connection_id), cases = context.cases.filter((entry) => entry.connection_id === id); return <Card key={id} title={dashboardTitle(item, "Service connection")} icon={Zap} iconTone="grey"><KV k="Meter" v={text(item.meter_id) || "Not provided"} /><KV k="Site" v={text(item.post_id) || "Not provided"} /><KV k="Service cases" v={cases.length} /><p className="ra-soft ra-spaced">This connection is linked to your account. A current supply status is not available in this demo.</p><div className="ra-actions ra-spaced">{canPrepare(context, "create_case") ? <button className="ra-primary" onClick={() => request({ connection_id: id }, "create_case", { connection_id: id })}><Plus size={16} />Report a problem</button> : null}<button className="ra-button" onClick={() => request({ connection_id: id })}>Ask about this connection</button></div>{cases.length ? <ul className="ra-link-list ra-spaced">{newestCases(cases).slice(0, 3).map((entry) => <li key={text(entry.case_id)}><Link href={path(`/cazuri/${encodeURIComponent(text(entry.case_id))}`)}><div><strong>{dashboardTitle(entry)}</strong><span>{shortCaseReference(entry)}</span></div><ArrowRight size={15} /></Link></li>)}</ul> : null}</Card>; })}</div> : <Empty title="No service connections linked">Ask your administrator to verify the connection for your account.</Empty>;
}
function Activity({ context, path }: Shared) {
  const [page, setPage] = useState(0);
  const events = recentEvents(context), currentPage = Math.min(page, Math.max(0, Math.ceil(events.length / 8) - 1));
  return <Card title="Recorded activity" bodyClassName="ra-table-body"><ul className="ra-activity">{events.slice(currentPage * 8, currentPage * 8 + 8).map((event, index) => { const item = context.cases.find((entry) => entry.case_id === event.case_id); return <li key={text(event.event_id) || index}><span className="ra-activity-icon"><Check size={16} /></span><div><strong>{EVENT_NAMES[text(event.action)] ?? "Case updated"}</strong>{item ? <Link href={path(`/cazuri/${encodeURIComponent(text(item.case_id))}`)}>{dashboardTitle(item)} <span>{shortCaseReference(item)}</span></Link> : <p className="ra-soft">Recorded operation</p>}<time>{readableDate(event.created_at ?? event.ts)}</time></div></li>; })}</ul>{!events.length ? <Empty title="No recorded activity yet">Confirmed requests and case updates will appear here.</Empty> : null}<Pager count={events.length} page={currentPage} onPage={setPage} /></Card>;
}
