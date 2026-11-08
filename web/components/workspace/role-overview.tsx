"use client";

import { useState, type ReactNode } from "react";
import {
  ArrowRight,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Clock3,
  FileText,
  MapPin,
  Plus,
  RefreshCw,
  Search,
  Waypoints,
  Wrench,
  Zap,
} from "lucide-react";
import { Card, PageTitle, Pill, type Tone } from "@/components/ds";
import {
  findingText,
  text,
  type Action,
  type Context,
  type Row,
} from "@/lib/operations/types";
import {
  canPrepare,
  readableDate,
  requestAssistant as dispatchAssistant,
  selectionOf,
} from "./scope";
import {
  assignedVisits,
  caseNextStep,
  caseStatus,
  dashboardTitle,
  fieldFindingCount,
  findingOutcome,
  isActiveCase,
  matchesDashboardQuery,
  newestCases,
  nextApprovedVisit,
  routeIsApproved,
  shortCaseReference,
  verifiedTimeline,
  workSource,
} from "./role-dashboard-model";
import "./role-dashboard.css";

type Selection = Parameters<typeof dispatchAssistant>[0];
type Request = (selection: Selection, action?: Action, data?: Row) => void;

export function RoleOverview({
  context,
  role,
  onRefresh,
  assistant,
}: {
  context: Context | null;
  role: "customer" | "technician" | "dispatcher";
  onRefresh: () => void;
  /** Workspace supplies the live inline assistant. This component owns its column. */
  assistant?: ReactNode;
}) {
  const [selected, setSelected] = useState<{
    scope: string;
    id: string;
  } | null>(null);
  const scope = `${context?.actor.user_id}/${context?.scenario}`;
  const cases = newestCases(context?.cases ?? []);
  const visits = context ? assignedVisits(context) : [];
  const currentCase =
    cases.find(
      (item) => selected?.scope === scope && item.case_id === selected.id,
    ) ?? cases[0];
  const nextVisit = context ? nextApprovedVisit(context, visits) : null;
  const selectedVisit = visits.find(
    (item) => selected?.scope === scope && item.work_item_id === selected.id,
  );
  const focusVisit = selectedVisit ?? nextVisit;
  const findingTarget =
    focusVisit ?? visits.find((item) => !findingOutcome(item)) ?? visits[0];
  const request: Request = (selection, action, data) =>
    dispatchAssistant(selection, action, data, context?.scenario);
  function select(item: Row, kind: "case" | "work" = "case") {
    const selection =
      kind === "work"
        ? { work_item_id: text(item.work_item_id) }
        : selectionOf(item);
    setSelected({
      scope,
      id: text(
        selection.case_id ?? selection.work_item_id ?? selection.connection_id,
      ),
    });
    request(selection);
  }
  const customer = role === "customer";
  const technician = role === "technician";
  const next = caseNextStep(currentCase);
  const approved = context ? routeIsApproved(context) : false;
  const primaryAction: Action = customer
    ? "create_case"
    : technician
      ? "record_verdict"
      : "approve_plan";
  const primaryAvailable =
    context &&
    canPrepare(context, primaryAction) &&
    (customer
      ? context.connections.length > 0
      : technician
        ? Boolean(findingTarget)
        : Boolean(context.plan.plan_id));
  function primary() {
    if (!context || !primaryAvailable) return;
    if (customer) {
      const connection =
        context.connections.find(
          (item) => item.connection_id === currentCase?.connection_id,
        ) ?? context.connections[0];
      const connectionId = text(connection.connection_id);
      request({ connection_id: connectionId }, "create_case", {
        connection_id: connectionId,
      });
    } else if (technician && findingTarget) {
      const workId = text(findingTarget.work_item_id);
      request({ work_item_id: workId }, "record_verdict", {
        work_item_id: workId,
      });
    } else request({}, "approve_plan", { plan_id: context.plan.plan_id });
  }
  return (
    <div className={`role-dashboard rd-${role}`}>
      <header className="rd-header">
        <div className="rd-heading">
          <PageTitle
            title={
              customer
                ? "Service dashboard"
                : technician
                  ? "Shift dashboard"
                  : "Operations dashboard"
            }
          />
          <p className="rd-demo">
            <span className="rd-demo-dot" aria-hidden="true" />
            Synthetic demo<span aria-hidden="true">·</span>
            {context
              ? readableDate(context.plan.plan_date)
              : "Loading your dashboard…"}
          </p>
        </div>
        <div className="rd-header-actions">
          <button
            type="button"
            className="rd-refresh"
            onClick={onRefresh}
            aria-label="Refresh dashboard"
            title="Refresh dashboard"
          >
            <RefreshCw size={17} />
          </button>
          <button
            type="button"
            className="rd-primary"
            disabled={!primaryAvailable}
            onClick={primary}
          >
            {customer ? (
              <Plus size={17} />
            ) : technician ? (
              <ClipboardList size={17} />
            ) : (
              <CalendarDays size={17} />
            )}
            {customer
              ? "Report a problem"
              : technician
                ? "Record finding"
                : "Review plan"}
          </button>
        </div>
      </header>

      <div
        className="rd-summary"
        aria-label={customer ? "Service summary" : "Shift summary"}
      >
        <Summary
          icon={<Zap size={18} />}
          label={customer ? "Connections" : "Assigned visits"}
          value={
            context
              ? String(customer ? context.connections.length : visits.length)
              : "—"
          }
          note={
            customer ? "Linked to your account" : "In your current assignment"
          }
        />
        <Summary
          icon={customer ? <FileText size={18} /> : <Waypoints size={18} />}
          label={customer ? "Active cases" : "Approved route"}
          value={
            context
              ? customer
                ? String(cases.filter(isActiveCase).length)
                : approved
                  ? "Approved"
                  : "Pending"
              : "—"
          }
          note={
            customer
              ? `${cases.length} ${cases.length === 1 ? "case" : "cases"} in total`
              : approved
                ? "Planned times, not live ETAs"
                : "Waiting for dispatcher approval"
          }
          tone={customer || approved ? "blue" : "amber"}
        />
        <Summary
          icon={customer ? <Clock3 size={18} /> : <Wrench size={18} />}
          label={customer ? "Next step" : "Field findings"}
          value={
            context
              ? customer
                ? next.short
                : String(fieldFindingCount(context))
              : "—"
          }
          note={
            customer
              ? currentCase
                ? `For case ${shortCaseReference(currentCase)}`
                : "Start a service case"
              : "Visits with a recorded finding"
          }
          tone={customer && findingOutcome(currentCase) ? "amber" : "neutral"}
        />
      </div>

      <div className="rd-content">
        <div
          className="rd-focus"
          id={technician ? "route" : undefined}
          aria-live="polite"
        >
          {customer ? (
            <CaseFocus item={currentCase} context={context} request={request} />
          ) : technician ? (
            <VisitFocus
              item={focusVisit}
              context={context}
              isNext={
                !selectedVisit ||
                selectedVisit.work_item_id === nextVisit?.work_item_id
              }
            />
          ) : (
            <Card className="rd-focus-card" title="Current plan">
              <p className="rd-next-copy">
                {approved
                  ? "The plan is approved. Review assigned visits below."
                  : "Review the current plan before approving visits."}
              </p>
            </Card>
          )}
        </div>
        <aside className="rd-assistant" aria-label="Daybreak assistant">
          {assistant ?? (
            <Card title="Daybreak assistant" className="rd-agent-placeholder">
              <p>Select a case or visit to discuss it with Daybreak.</p>
            </Card>
          )}
        </aside>
        {customer && (
          <div className="rd-connections" id="connection">
            <RoleList
              title="Your connections"
              kind="connection"
              items={context?.connections ?? []}
              context={context}
            />
          </div>
        )}
        {!customer && (
          <div className="rd-work" id="work">
            <RoleList
              title={technician ? "Assigned visits" : "Work to review"}
              kind="work"
              items={visits}
              context={context}
              onSelect={(item) => select(item, "work")}
              selectedId={text(focusVisit?.work_item_id)}
            />
          </div>
        )}
        <div className="rd-cases" id="cases">
          <RoleList
            title={customer ? "Recent cases" : "Shared cases"}
            kind="case"
            items={cases}
            context={context}
            onSelect={select}
            selectedId={text(currentCase?.case_id)}
          />
        </div>
      </div>
    </div>
  );
}

function Summary({
  icon,
  label,
  value,
  note,
  tone = "neutral",
}: {
  icon: ReactNode;
  label: string;
  value: string;
  note: string;
  tone?: "blue" | "amber" | "neutral";
}) {
  return (
    <section className={`rd-summary-tile rd-tone-${tone}`}>
      <div className="rd-summary-label">
        {label}
        <span aria-hidden="true">{icon}</span>
      </div>
      <strong className="rd-summary-value">{value}</strong>
      <span className="rd-summary-note">{note}</span>
    </section>
  );
}
function CaseFocus({
  item,
  context,
  request,
}: {
  item?: Row;
  context: Context | null;
  request: Request;
}) {
  if (!item)
    return (
      <Card className="rd-focus-card" bodyClassName="rd-focus-body">
        <span className="rd-kicker">Your service</span>
        <h2>{context ? "How can we help?" : "Loading your service…"}</h2>
        <p className="rd-next-copy">
          {context
            ? "Report an issue with a connection. You can follow the case and share your availability here."
            : "Your connections and cases will appear here."}
        </p>
      </Card>
    );
  const status = caseStatus(item);
  const finding = findingText(item);
  return (
    <Card className="rd-focus-card" bodyClassName="rd-focus-body">
      <div className="rd-focus-top">
        <span className="rd-kicker">
          Current case{" "}
          <span className="rd-reference">{shortCaseReference(item)}</span>
        </span>
        <Pill tone={status.tone} size="sm">
          {status.label}
        </Pill>
      </div>
      <h2 className="rd-focus-title">{dashboardTitle(item)}</h2>
      {finding && <p className="rd-finding">{finding}</p>}
      <div className="rd-next">
        <span className="rd-next-label">
          <ArrowRight size={16} aria-hidden="true" />
          What happens next
        </span>
        <p className="rd-next-copy">{caseNextStep(item).detail}</p>
      </div>
      {context && <Timeline context={context} item={item} />}
      <div className="rd-focus-actions">
        {context &&
          canPrepare(context, "set_availability") &&
          isActiveCase(item) && (
            <button
              type="button"
              className="rd-secondary"
              onClick={() =>
                request({ case_id: text(item.case_id) }, "set_availability", {
                  case_id: item.case_id,
                })
              }
            >
              <CalendarDays size={15} />
              Share availability
            </button>
          )}
        <button
          type="button"
          className="rd-text-button"
          onClick={() =>
            request({ case_id: text(item.case_id) }, "request_human", {
              case_id: item.case_id,
            })
          }
        >
          Ask for help
          <ArrowRight size={14} />
        </button>
      </div>
    </Card>
  );
}
function VisitFocus({
  item,
  context,
  isNext,
}: {
  item: Row | null;
  context: Context | null;
  isNext: boolean;
}) {
  if (!item)
    return (
      <Card className="rd-focus-card" bodyClassName="rd-focus-body">
        <div className="rd-focus-top">
          <span className="rd-kicker">Next visit</span>
          <Pill size="sm" tone="amber">
            {context && routeIsApproved(context)
              ? "No next visit"
              : "Awaiting approval"}
          </Pill>
        </div>
        <h2 className="rd-focus-title">
          {context ? "Your assignment at a glance" : "Loading your shift…"}
        </h2>
        <p className="rd-next-copy">
          {context && routeIsApproved(context)
            ? "There is no next visit in the current approved route. You can review your assigned visits below."
            : "The dispatcher needs to approve your route before a next visit is confirmed."}
        </p>
      </Card>
    );
  const relatedCase = context?.cases.find(
    (entry) =>
      entry.work_item_id === item.work_item_id && findingOutcome(entry),
  );
  const finding = findingText(
    findingOutcome(item) ? item : (relatedCase ?? item),
  );
  return (
    <Card className="rd-focus-card" bodyClassName="rd-focus-body">
      <div className="rd-focus-top">
        <span className="rd-kicker">
          {isNext ? "Next approved visit" : "Selected visit"}
        </span>
        <Pill
          size="sm"
          tone={context && routeIsApproved(context) ? "blue" : "amber"}
        >
          {context && routeIsApproved(context)
            ? "Approved route"
            : "Awaiting approval"}
        </Pill>
      </div>
      <h2 className="rd-focus-title">
        {dashboardTitle(item, "Site inspection")}
      </h2>
      <div className="rd-visit-meta">
        <span>
          <MapPin size={15} aria-hidden="true" />
          {text(item.post_id ?? item.asset_id) || workSource(item)}
        </span>
        <span>
          <Clock3 size={15} aria-hidden="true" />
          {item.planned_start
            ? `Planned ${readableDate(item.planned_start)}`
            : "Time not scheduled"}
        </span>
      </div>
      {finding && <p className="rd-finding">{finding}</p>}
      <div className="rd-next">
        <span className="rd-next-label">
          <ArrowRight size={16} aria-hidden="true" />
          At this visit
        </span>
        <p className="rd-next-copy">
          {finding
            ? "The finding is recorded. The dispatcher needs to review any follow-up."
            : "Inspect the site and record what you find. If you cannot get access, record that too."}
        </p>
      </div>
      {context && <Timeline context={context} item={item} />}
    </Card>
  );
}
function Timeline({ context, item }: { context: Context; item: Row }) {
  const entries = verifiedTimeline(context, item);
  if (!entries.length) return null;
  return (
    <ol className="rd-timeline" aria-label="Recorded updates">
      {entries.map((entry) => (
        <li key={entry.key}>
          <span className="rd-timeline-dot" aria-hidden="true" />
          <div>
            <strong>{entry.title}</strong>
            <span>{entry.date}</span>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function RoleList({
  title,
  kind,
  items,
  context,
  onSelect,
  selectedId,
}: {
  title: string;
  kind: "connection" | "case" | "work";
  items: Row[];
  context: Context | null;
  onSelect?: (item: Row) => void;
  selectedId?: string;
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const pageSize = kind === "connection" ? 3 : 4;
  const filtered = items.filter((item) => matchesDashboardQuery(item, query));
  const last = Math.max(0, Math.ceil(filtered.length / pageSize) - 1);
  const currentPage = Math.min(page, last);
  const visible = filtered.slice(
    currentPage * pageSize,
    (currentPage + 1) * pageSize,
  );
  const select = (item: Row) =>
    onSelect
      ? onSelect(item)
      : dispatchAssistant(
          kind === "work"
            ? { work_item_id: text(item.work_item_id) }
            : selectionOf(item),
          undefined,
          undefined,
          context?.scenario,
        );
  const searchable = kind !== "connection" || items.length > pageSize;
  return (
    <Card
      title={
        <>
          {title}
          <span className="rd-section-count">{items.length}</span>
        </>
      }
      className={`rd-list rd-list-${kind}`}
      bodyClassName="rd-list-body"
    >
      {searchable && (
        <label className="rd-search">
          <Search size={15} aria-hidden="true" />
          <input
            type="search"
            aria-label={`Find ${title.toLowerCase()}`}
            placeholder="Search by description or reference"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(0);
            }}
          />
        </label>
      )}
      {kind === "connection" ? (
        <div className="rd-connection-list">
          {visible.map((item, i) => (
            <button
              type="button"
              className="rd-connection"
              key={text(item.connection_id) || i}
              onClick={() => select(item)}
            >
              <span className="rd-connection-icon">
                <Zap size={18} aria-hidden="true" />
              </span>
              <span className="rd-connection-copy">
                <strong>{dashboardTitle(item, "Service connection")}</strong>
                <span>
                  {text(item.meter_id)
                    ? `Meter ${text(item.meter_id)}`
                    : "Linked service connection"}
                  {text(item.post_id) && ` · Site ${text(item.post_id)}`}
                </span>
              </span>
              <ChevronRight size={17} aria-hidden="true" />
            </button>
          ))}
        </div>
      ) : (
        <table className={`rd-table rd-table-${kind}`} aria-label={title}>
          <thead>
            <tr>
              <th scope="col">{kind === "case" ? "Case" : "Visit / asset"}</th>
              <th scope="col" className="rd-status-cell">
                {kind === "case" ? "Status" : "Planned time"}
              </th>
              {kind === "work" && (
                <th scope="col" className="rd-action-cell">
                  <span className="rd-sr-only">Actions</span>
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {visible.map((item, i) => {
              const id = text(
                kind === "case" ? item.case_id : item.work_item_id,
              );
              const status = caseStatus(item);
              const date =
                kind === "case" ? item.created_at : item.planned_start;
              const meta =
                kind === "case"
                  ? `${shortCaseReference(item)}${date ? ` · ${readableDate(date)}` : ""}`
                  : `${workSource(item)}${text(item.asset_id) ? ` · ${text(item.asset_id)}` : ""}`;
              return (
                <tr
                  key={id || i}
                  data-selected={id && id === selectedId ? "true" : undefined}
                >
                  <td>
                    <button
                      type="button"
                      className="rd-item-select"
                      onClick={() => select(item)}
                      aria-current={
                        id && id === selectedId ? "true" : undefined
                      }
                    >
                      <span className="rd-cell-title">
                        {dashboardTitle(
                          item,
                          kind === "case" ? "Service case" : "Assigned visit",
                        )}
                      </span>
                      <span className="rd-cell-meta">{meta}</span>
                      {kind === "work" && (
                        <span className="rd-mobile-time">
                          {date
                            ? `Planned ${readableDate(date)}`
                            : "Time not scheduled"}
                        </span>
                      )}
                    </button>
                  </td>
                  <td className="rd-status-cell">
                    {kind === "case" ? (
                      <Pill tone={status.tone as Tone} size="sm">
                        {status.label}
                      </Pill>
                    ) : (
                      <span className="rd-planned-time">
                        {date ? (
                          <>
                            Planned <span>{readableDate(date)}</span>
                          </>
                        ) : (
                          "Not scheduled"
                        )}
                      </span>
                    )}
                  </td>
                  {kind === "work" && (
                    <td className="rd-action-cell">
                      <button
                        type="button"
                        className="rd-row-action"
                        disabled={
                          !context ||
                          !canPrepare(
                            context,
                            context.actor.role === "dispatcher"
                              ? "review_work_item"
                              : "record_verdict",
                          )
                        }
                        onClick={() =>
                          dispatchAssistant(
                            { work_item_id: id },
                            context?.actor.role === "dispatcher"
                              ? "review_work_item"
                              : "record_verdict",
                            { work_item_id: id },
                            context?.scenario,
                          )
                        }
                      >
                        {context?.actor.role === "dispatcher"
                          ? "Review work"
                          : "Record finding"}
                        <ArrowRight size={13} aria-hidden="true" />
                      </button>
                    </td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
      {!visible.length && (
        <p className="rd-empty" role="status">
          {!context
            ? "Loading your items…"
            : query
              ? "No matches. Try another description or reference."
              : kind === "case"
                ? "No cases to show yet."
                : kind === "work"
                  ? "No visits in your current assignment."
                  : "No connections linked to your account."}
        </p>
      )}
      {(last > 0 || query) && (
        <nav className="rd-pagination" aria-label={`${title} pages`}>
          <span>
            {filtered.length
              ? `${currentPage * pageSize + 1}–${Math.min((currentPage + 1) * pageSize, filtered.length)} of ${filtered.length}`
              : "0 results"}
          </span>
          <div>
            <button
              type="button"
              aria-label={`Previous ${title.toLowerCase()} page`}
              disabled={currentPage === 0}
              onClick={() => setPage(currentPage - 1)}
            >
              <ChevronLeft size={16} />
              <span className="rd-sr-only">Previous</span>
            </button>
            <span>
              {currentPage + 1} of {last + 1}
            </span>
            <button
              type="button"
              aria-label={`Next ${title.toLowerCase()} page`}
              disabled={currentPage === last}
              onClick={() => setPage(currentPage + 1)}
            >
              <ChevronRight size={16} />
              <span className="rd-sr-only">Next</span>
            </button>
          </div>
        </nav>
      )}
    </Card>
  );
}
