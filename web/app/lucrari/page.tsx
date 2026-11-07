import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { PageTitle } from "@/components/ds";
import { OrderPaper } from "@/components/orders/order-paper";
import { OrderSide } from "@/components/orders/order-side";
import { PrintButton } from "@/components/orders/print-button";
import { AppShell } from "@/components/shell/app-shell";
import { buildOrder, pickCrew } from "@/lib/orders-view";
import { itemPlace, itemTitle } from "@/lib/plan-screen";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Work items" };

// la tipărire rămâne doar foaia: restul paginii (cadrul, meniul, coloana din dreapta) se ascunde
const PRINT_CSS = `@media print {
  body * { visibility: hidden !important; }
  #order-paper, #order-paper * { visibility: visible !important; }
  #order-paper { position: absolute; left: 0; top: 0; width: 100%; border-radius: 0; box-shadow: none; }
  html, body { background: #fff !important; }
}`;

export default function OrdersPage({ searchParams }: PageProps<"/lucrari">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true"><span className="sr-only">Loading work order…</span></div>}>
      <Orders searchParams={searchParams} />
    </Suspense>
  );
}

async function Orders({ searchParams }: { searchParams: PageProps<"/lucrari">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info }, view, params] = await Promise.all([loadShellInfo(scenario), loadPlanView(scenario), searchParams]);
  const data = view.data;
  const sc = `scenariu=${encodeURIComponent(scenario)}`;
  const routes = data?.routes.filter((r) => r.stops.length > 0) ?? [];
  const crewId = pickCrew(routes, typeof params.echipa === "string" ? params.echipa : undefined);
  const route = routes.find((r) => r.crew_id === crewId);
  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        {!data || !route || !crewId ? (
          <>
            <PageTitle title="Printable work order" />
            <p className="mt-6 text-[17px] text-ink-soft">No route yet for &quot;{scenario}&quot;. Run the agent from the console, then return here.</p>
          </>
        ) : (
          <Content data={data} route={route} crewId={crewId} routes={routes.map((r) => r.crew_id)} scenario={scenario} sc={sc} stopParam={typeof params.oprire === "string" ? params.oprire : undefined} />
        )}
      </div>
    </AppShell>
  );
}

function Content({
  data,
  route,
  crewId,
  routes,
  scenario,
  sc,
  stopParam,
}: {
  data: NonNullable<Awaited<ReturnType<typeof loadPlanView>>["data"]>;
  route: NonNullable<Awaited<ReturnType<typeof loadPlanView>>["data"]>["routes"][number];
  crewId: string;
  routes: string[];
  scenario: string;
  sc: string;
  stopParam: string | undefined;
}) {
  const order = buildOrder(route, data.workItemsById, data.decisionsByWorkItemId, itemPlace, itemTitle);
  const selected = order.stops.find((s) => s.workItemId === stopParam) ?? order.stops[0] ?? null;
  return (
    <>
      <style>{PRINT_CSS}</style>
      <PageTitle

        title={<>Work order</>}
        subtitle="Crew route and intervention details."
        actions={<PrintButton />}
      />
      <nav aria-label="Choose crew" className="mt-5 flex flex-wrap gap-2.5">
        {routes.map((id) => {
          const on = id === crewId;
          return (
            <Link
              key={id}
              href={`/lucrari?echipa=${encodeURIComponent(id)}&${sc}`}
              aria-current={on ? "page" : undefined}
              translate="no"
              className={
                "inline-flex h-9 items-center rounded-full border px-4 text-[14.5px] font-[520] whitespace-nowrap transition-colors duration-150 " +
                (on ? "border-[#e6e8eb] bg-[#e6e8eb] text-[#0b1322]" : "border-rule text-ink hover:border-ink-soft hover:bg-surface-2")
              }
            >
              {id}
            </Link>
          );
        })}
      </nav>
      <div className="mt-5 grid grid-cols-[minmax(0,1fr)_minmax(320px,380px)] items-start gap-5 max-lg:grid-cols-1">
        <OrderPaper order={order} planDate={data.plan.plan_date} selected={selected} scenario={scenario} />
        <div className="print:hidden">
          <OrderSide order={order} planDate={data.plan.plan_date} selected={selected} />
        </div>
      </div>
    </>
  );
}
