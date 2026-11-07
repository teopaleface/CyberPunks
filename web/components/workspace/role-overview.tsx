"use client";
import { useState } from "react";
import { ArrowUpRight, RefreshCw } from "lucide-react";
import { Card, PageTitle, Pill } from "@/components/ds";
import { englishText } from "@/lib/english";
import {
  findingText,
  label,
  rows,
  text,
  type Action,
  type Context,
  type Row,
} from "@/lib/operations/types";
import {
  canPrepare,
  itemTitle,
  readableDate,
  requestAssistant as dispatchAssistant,
  selectionOf,
} from "./scope";

export function RoleOverview({
  context,
  role,
  onRefresh,
}: {
  context: Context | null;
  role: "customer" | "technician" | "dispatcher";
  onRefresh: () => void;
}) {
  const requestAssistant = (
    selection: Parameters<typeof dispatchAssistant>[0],
    action?: Action,
    data?: Row,
  ) => dispatchAssistant(selection, action, data, context?.scenario);
  const nextStop =
    context?.next_stop && typeof context.next_stop === "object"
      ? (context.next_stop as Row)
      : null;
  const nextWork = context?.work_items.find(
    (item) => item.work_item_id === nextStop?.work_item_id,
  );
  const stops = rows(context?.routes ?? context?.plan.routes).flatMap((route) =>
    rows(route.stops),
  );
  const assignedWork = (context?.work_items ?? []).map((item) => {
    const stop = stops.find(
      (candidate) => candidate.work_item_id === item.work_item_id,
    );
    return stop
      ? {
          ...item,
          planned_start:
            item.planned_start ??
            stop.eta ??
            stop.arrival ??
            stop.planned_start,
        }
      : item;
  });
  return (
    <div className="db-role-view">
      <div className="db-page-title">
        <PageTitle
          title={
            role === "customer"
              ? "Your service"
              : role === "technician"
                ? "Your shift"
                : "Operations"
          }
          subtitle={
            role === "customer"
              ? "Your connections and service cases."
              : role === "technician"
                ? "Your assigned visits and findings."
                : "Work and cases in your authorized scope."
          }
          actions={
            <button className="db-button" onClick={onRefresh}>
              <RefreshCw size={16} /> Refresh
            </button>
          }
        />
      </div>
      <p className="db-muted">
        Synthetic demo ·{" "}
        {context
          ? readableDate(context.plan.plan_date)
          : "Loading current plan…"}{" "}
        · Planned times, not live arrival estimates.
      </p>
      {role === "technician" && context && (
        <Card
          title="Next visit"
          className="db-role-card"
          action={
            <Pill size="sm" tone={nextStop ? "blue" : "grey"}>
              {nextStop ? "Approved route" : "Awaiting approval"}
            </Pill>
          }
        >
          {nextStop ? (
            <>
              <h3>
                {nextWork
                  ? itemTitle(nextWork, "Assigned visit")
                  : "Next approved visit"}
              </h3>
              <p className="db-muted">
                Planned arrival{" "}
                {readableDate(
                  nextStop.eta ?? nextStop.arrival ?? nextStop.planned_start,
                )}
              </p>
              <button
                className="db-button"
                onClick={() =>
                  requestAssistant({
                    work_item_id: text(nextStop.work_item_id),
                  })
                }
              >
                Ask about this visit <ArrowUpRight size={16} />
              </button>
            </>
          ) : (
            <p className="db-muted">
              Your route needs dispatcher approval before a next visit is
              confirmed.
            </p>
          )}
        </Card>
      )}
      {role === "dispatcher" &&
        context &&
        canPrepare(context, "approve_plan") && (
          <Card title="Current plan" className="db-role-card">
            <p>
              {context.work_items.length} work items · {context.cases.length}{" "}
              shared cases
            </p>
            <div className="db-actions">
              <Pill size="sm" tone={context.plan.approved ? "green" : "amber"}>
                {context.plan.approved ? "Approved" : "Needs review"}
              </Pill>
              <button
                className="db-button"
                disabled={!context.plan.plan_id}
                onClick={() =>
                  requestAssistant({}, "approve_plan", {
                    plan_id: context.plan.plan_id,
                  })
                }
              >
                Review plan
              </button>
            </div>
          </Card>
        )}
      {role === "customer" && (
        <RoleList
          title="Your connections"
          kind="connection"
          items={context?.connections ?? []}
          context={context}
        />
      )}
      <RoleList
        title={role === "customer" ? "Your cases" : "Shared cases"}
        kind="case"
        items={context?.cases ?? []}
        context={context}
      />
      {role !== "customer" && (
        <RoleList
          title={
            role === "technician" ? "Your assigned work" : "Work to review"
          }
          kind="work"
          items={assignedWork}
          context={context}
        />
      )}
    </div>
  );
}
export function RoleList({
  title,
  kind,
  items,
  context,
}: {
  title: string;
  kind: "connection" | "case" | "work";
  items: Row[];
  context: Context | null;
}) {
  const requestAssistant = (
    selection: Parameters<typeof dispatchAssistant>[0],
    action?: Action,
    data?: Row,
  ) => dispatchAssistant(selection, action, data, context?.scenario);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const filtered = items.filter((item) =>
    [
      itemTitle(item),
      item.status,
      item.post_id,
      item.crew_id,
      item.work_item_id,
      item.case_id,
    ].some((value) => text(value).toLowerCase().includes(query.toLowerCase())),
  );
  const last = Math.max(0, Math.ceil(filtered.length / 8) - 1);
  const currentPage = Math.min(page, last);
  const visible = filtered.slice(currentPage * 8, currentPage * 8 + 8);
  return (
    <Card
      title={title}
      className="db-role-card"
      action={<Pill size="sm">{items.length}</Pill>}
    >
      {items.length > 8 && (
        <label className="db-filter">
          Find {title.toLowerCase()}
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="Search by description or reference"
          />
        </label>
      )}
      {visible.map((item, index) => {
        const selection = selectionOf(item);
        const key = text(
          selection.case_id ??
            selection.work_item_id ??
            selection.connection_id,
        );
        return (
          <article className="db-role-row" key={key || index}>
            <button
              className="db-row"
              onClick={() => requestAssistant(selection)}
            >
              <div>
                <strong>
                  {itemTitle(
                    item,
                    kind === "case"
                      ? "Service case"
                      : kind === "work"
                        ? "Assigned visit"
                        : "Service connection",
                  )}
                </strong>
                <p>
                  {kind === "connection"
                    ? "Verified service connection"
                    : label(item.status ?? item.source) || "Open"}
                  {text(item.post_id) ? ` · Site ${text(item.post_id)}` : ""}
                </p>
                {text(item.planned_start ?? item.created_at) && (
                  <p>
                    {item.planned_start ? "Planned " : "Opened "}
                    {readableDate(item.planned_start ?? item.created_at)}
                  </p>
                )}
                {findingText(item) && <p>{findingText(item)}</p>}
                {text(item.customer_summary ?? item.next_step) && (
                  <p>
                    {englishText(text(item.customer_summary ?? item.next_step))}
                  </p>
                )}
              </div>
              <ArrowUpRight size={18} aria-label="Open in assistant" />
            </button>
            <div className="db-actions">
              {context &&
                kind === "connection" &&
                canPrepare(context, "create_case") && (
                  <button
                    className="db-button"
                    onClick={() =>
                      requestAssistant(selection, "create_case", {
                        connection_id: selection.connection_id,
                      })
                    }
                  >
                    Report a problem
                  </button>
                )}
              {context &&
                kind === "case" &&
                canPrepare(context, "set_availability") && (
                  <button
                    className="db-button"
                    onClick={() =>
                      requestAssistant(selection, "set_availability", {
                        case_id: selection.case_id,
                      })
                    }
                  >
                    Share availability
                  </button>
                )}
              {context &&
                kind === "work" &&
                canPrepare(context, "record_verdict") && (
                  <button
                    className="db-button"
                    onClick={() =>
                      requestAssistant(selection, "record_verdict", {
                        work_item_id: selection.work_item_id,
                      })
                    }
                  >
                    Record finding
                  </button>
                )}
              {context &&
                kind === "work" &&
                canPrepare(context, "review_work_item") && (
                  <button
                    className="db-button"
                    onClick={() =>
                      requestAssistant(selection, "review_work_item", {
                        work_item_id: selection.work_item_id,
                      })
                    }
                  >
                    Review work
                  </button>
                )}
              <button
                className="db-button"
                onClick={() =>
                  requestAssistant(selection, "request_human", {
                    ...(selection.case_id
                      ? { case_id: selection.case_id }
                      : {}),
                    ...(text(item.connection_id)
                      ? { connection_id: item.connection_id }
                      : {}),
                  })
                }
              >
                Ask for help
              </button>
            </div>
            <details className="db-details">
              <summary>Details and history</summary>
              {text(item.reason ?? item.next_step) && (
                <p>{englishText(text(item.reason ?? item.next_step))}</p>
              )}
              {context?.actor.role !== "customer" && (
                <>
                  <Assessment value={item.assessment} />
                  <WorkExplanation value={item.explanation} />
                </>
              )}
              {rows(item.events).map((event, i) => (
                <p className="db-event" key={i}>
                  {readableDate(event.created_at ?? event.ts)} ·{" "}
                  {label(event.event_type ?? event.type ?? event.action)}{" "}
                  {text(event.summary ?? event.message)}
                </p>
              ))}
              <p className="db-muted">Reference: {key}</p>
            </details>
          </article>
        );
      })}
      {!visible.length && (
        <p className="db-muted" role="status">
          {context
            ? query
              ? "No matching items."
              : "No items in your current scope."
            : "Loading your current scope…"}
        </p>
      )}
      {last > 0 && (
        <nav className="db-pagination" aria-label={`${title} pages`}>
          <button
            className="db-button"
            disabled={currentPage === 0}
            onClick={() => setPage(currentPage - 1)}
          >
            Previous
          </button>
          <span className="db-muted">
            {currentPage + 1} of {last + 1}
          </span>
          <button
            className="db-button"
            disabled={currentPage === last}
            onClick={() => setPage(currentPage + 1)}
          >
            Next
          </button>
        </nav>
      )}
    </Card>
  );
}
function Assessment({ value }: { value: unknown }) {
  if (!value || typeof value !== "object") return null;
  const data = value as Row;
  return (
    <div className="db-assessment">
      <h3>Model evidence</h3>
      <p>
        {label(data.status)}
        {text(data.reason) && ` · ${text(data.reason)}`}
      </p>
      <dl>
        {["model_version", "source", "score", "confidence", "generated_at"]
          .filter((key) => data[key] !== undefined && data[key] !== null)
          .map((key) => (
            <div key={key}>
              <dt>{label(key)}</dt>
              <dd>
                {key === "generated_at"
                  ? readableDate(data[key])
                  : text(data[key])}
              </dd>
            </div>
          ))}
      </dl>
      {rows(data.top_factors ?? data.reasons).map((factor, i) => (
        <p key={i}>
          {text(factor.feature ?? factor.name ?? factor.description)}{" "}
          {text(factor.value ?? factor.contribution)}
        </p>
      ))}
      {Array.isArray(data.limitations) &&
        data.limitations.map((item, i) => (
          <p className="db-muted" key={i}>
            {text(item)}
          </p>
        ))}
    </div>
  );
}
function WorkExplanation({ value }: { value: unknown }) {
  if (!value || typeof value !== "object") return null;
  const data = value as Row;
  return (
    <div>
      <h3>Why this work matters</h3>
      <p>{englishText(text(data.summary_ro ?? data.summary))}</p>
      {rows(data.top_factors).map((factor, i) => (
        <p key={i}>
          {englishText(
            text(factor.label_ro ?? factor.description ?? factor.feature),
          )}{" "}
          {text(factor.value)}
        </p>
      ))}
    </div>
  );
}
