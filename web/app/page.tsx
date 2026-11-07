import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { DEFAULT_SCENARIO, getPlanView } from "@/lib/data";
import { DECISION_LABEL_RO, SOURCE_LABEL_RO } from "@/lib/data/labels";

// Pagină provizorie: arată că stratul de date merge cap-coadă. Interfața reală vine separat.

const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;

export default function Home({ searchParams }: PageProps<"/">) {
  return (
    <main className="mx-auto w-full max-w-4xl space-y-6 p-6 text-sm">
      <header>
        <h1 className="text-xl font-semibold">Consola dispecerului (schelet)</h1>
        <p>
          Rezumatul planului, citit prin stratul de date. <Link href="/debug">Diagnostic</Link>
        </p>
      </header>
      <Suspense fallback={<p>Se încarcă planul…</p>}>
        <PlanSummary searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function PlanSummary({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  await connection();
  const params = await searchParams;
  const requested = typeof params.scenariu === "string" ? params.scenariu : undefined;
  const scenario = requested && SCENARIO_RE.test(requested) ? requested : DEFAULT_SCENARIO;
  const result = await getPlanView(scenario);
  const view = result.data;

  return (
    <section className="space-y-4">
      <p>
        Scenariu: <strong>{scenario}</strong> · Sursa datelor:{" "}
        <strong data-source={result.source}>{SOURCE_LABEL_RO[result.source]}</strong> · citit la{" "}
        {new Date(result.fetchedAt).toLocaleTimeString("ro-RO", { timeZone: "Europe/Bucharest" })}
      </p>
      {result.degradedReason ? <p role="status">Atenție: {result.degradedReason}</p> : null}

      {!view ? (
        <p>Nu există încă un plan de afișat.</p>
      ) : (
        <>
          <div>
            <h2 className="font-semibold">Planul {view.plan.plan_id}</h2>
            <p>
              Ziua {view.plan.plan_date}, generat de {view.plan.planner_version}
            </p>
            <dl className="grid grid-cols-2 gap-x-6 sm:grid-cols-4">
              <dt>Lucrări primite</dt>
              <dd>{view.plan.summary.items_in}</dd>
              <dt>Valide</dt>
              <dd>{view.plan.summary.items_valid}</dd>
              <dt>Respinse la intrare</dt>
              <dd>{view.plan.summary.items_invalid}</dd>
              <dt>În trasee</dt>
              <dd>{view.plan.summary.assigned}</dd>
              <dt>Amânate</dt>
              <dd>{view.plan.summary.deferred}</dd>
              <dt>Decide un om</dt>
              <dd>{view.plan.summary.human_review}</dd>
              <dt>Echipe folosite</dt>
              <dd>{view.plan.summary.crews_used}</dd>
              <dt>Valoare așteptată</dt>
              <dd>{view.plan.summary.expected_value_lei.toLocaleString("ro-RO")} lei</dd>
              <dt>Kilometri</dt>
              <dd>{view.plan.summary.total_km.toLocaleString("ro-RO")} km</dd>
              <dt>Trasee</dt>
              <dd>{view.routes.length}</dd>
            </dl>
          </div>

          <div>
            <h2 className="font-semibold">Trasee</h2>
            <ul className="list-disc pl-5">
              {view.routes.map((route) => (
                <li key={route.crew_id}>
                  {route.crew_id} pleacă din {route.depot?.label_ro ?? route.depot_id}:{" "}
                  {route.stops.map((stop, i) => (
                    <span key={stop.work_item_id}>
                      {i > 0 ? " → " : ""}
                      <Link href={`/lucrari/${stop.work_item_id}`}>{stop.label ?? stop.work_item_id}</Link>
                      {stop.lat !== null && stop.lon !== null
                        ? ` (${stop.lat.toFixed(4)}, ${stop.lon.toFixed(4)})`
                        : " (fără coordonate)"}
                    </span>
                  ))}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="font-semibold">Decizii</h2>
            <ul className="list-disc pl-5">
              {view.plan.decisions.map((d) => (
                <li key={d.work_item_id}>
                  <Link href={`/lucrari/${d.work_item_id}`}>{d.work_item_id}</Link>: {DECISION_LABEL_RO[d.decision]}{" "}
                  ({d.reason_ro})
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="font-semibold">Fără decizie în plan ({view.unplannedItems.length})</h2>
            <ul className="list-disc pl-5">
              {view.unplannedItems.map((w) => (
                <li key={w.work_item_id}>
                  <Link href={`/lucrari/${w.work_item_id}`}>{w.work_item_id}</Link> · {w.location.label ?? w.asset_id}
                  {view.alertsByWorkItemId[w.work_item_id] ? " · are alertă" : ""}
                </li>
              ))}
            </ul>
          </div>

          {view.invalidItems.length ? (
            <p>Respinse la intrare (date greșite): {view.invalidItems.map((i) => String(i.work_item_id)).join(", ")}</p>
          ) : null}
          {result.parseErrors?.length ? <p>Linii care nu au putut fi citite: {result.parseErrors.length}</p> : null}
        </>
      )}
    </section>
  );
}
