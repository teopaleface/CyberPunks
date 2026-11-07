import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { CloudLightning, Gauge as GaugeIcon, UtilityPole, Zap } from "lucide-react";
import { PageTitle, Pill } from "@/components/ds";
import { layoutA } from "@/components/item/layout-a";
import { layoutB } from "@/components/item/layout-b";
import { layoutC } from "@/components/item/layout-c";
import { CardGrid, ItemChips, type CardDef, type ItemCtx } from "@/components/item/parts";
import { AppShell } from "@/components/shell/app-shell";
import { getMetrics, getSeries, getWorkItem } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";
import { getRemedies } from "@/lib/data/remedies";
import { isBilantPost } from "@/lib/extras";
import { localityOf, parseTag, postOf, stopFor, type Tag } from "@/lib/item-data";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";

const PAGE = "mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4";

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default function WorkItemPage({ params, searchParams }: PageProps<"/lucrari/[id]">) {
  return (
    <Suspense
      fallback={
        <div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
          <span className="sr-only">Se încarcă lucrarea…</span>
        </div>
      }
    >
      <Detail params={params} searchParams={searchParams} />
    </Suspense>
  );
}

async function Detail({ params, searchParams }: Pick<PageProps<"/lucrari/[id]">, "params" | "searchParams">) {
  await connection();
  const id = safeDecode((await params).id);
  const scenario = await resolveScenario(searchParams);
  const filter: Tag | null = parseTag((await searchParams).vedere);
  const [{ info }, result, series, view, metrics, remedies] = await Promise.all([
    loadShellInfo(scenario),
    getWorkItem(id, scenario),
    getSeries(id, scenario),
    loadPlanView(scenario),
    getMetrics(),
    id.startsWith("C-") ? getRemedies(scenario).catch(() => null) : Promise.resolve(null),
  ]);
  const detail = result.data;

  if (!detail) {
    return (
      <AppShell info={info}>
        <div className={PAGE}>
          <div className="mx-auto max-w-[680px] py-14">
            <Link href={`/?scenariu=${encodeURIComponent(scenario)}`} className="text-[15px] underline decoration-rule underline-offset-4 hover:text-ink">
              Înapoi la planul de mâine
            </Link>
            <h1 className="mt-6 text-[28px] font-[700] tracking-[-0.02em]">
              Lucrarea <span translate="no">{id}</span> nu există în scenariul „{scenario}”
            </h1>
            <p className="mt-3 text-[16px] text-ink-soft">
              Poate a fost respinsă la intrare sau vine din alt scenariu. Verifică jurnalul deciziilor sau alege alt scenariu din antet.
            </p>
          </div>
        </div>
      </AppShell>
    );
  }

  const { workItem: w, decision, audit, invalid } = detail;
  const ctx: ItemCtx = {
    w,
    decision,
    audit,
    invalid,
    scenario,
    series: series.data,
    report: metrics.data[w.source] ?? null,
    remedy: remedies?.data.find((r) => r.work_item_id === w.work_item_id) ?? null,
    stop: stopFor(view.data?.routes, w.work_item_id),
    notifications: view.data?.plan.notifications ?? [],
  };

  const cards: CardDef[] = w.source === "B" ? layoutB(ctx) : w.source === "C" ? layoutC(ctx) : layoutA(ctx);
  const tags = new Set(cards.flatMap((c) => c.tags));
  const active = filter && tags.has(filter) ? filter : null;
  const visible = active ? cards.filter((c) => c.tags.includes(active)) : cards;

  const syn = w.data_quality.synthetic ? " (sintetic)" : "";
  const id_ = (s: string) => <span translate="no">{s}</span>;
  const post = postOf(w);
  const bilant = isBilantPost(w);
  const title =
    w.source === "B" ? (
      <>Lucrare furtună: {localityOf(w)}.</>
    ) : w.source === "C" || bilant ? (
      <>
        {id_(w.asset_id)} {localityOf(w)}
        {syn}
      </>
    ) : (
      <>
        {id_(w.asset_id)} {post ? <>{id_(post)} </> : null}
        {localityOf(w)}
        {syn}
      </>
    );
  const subtitle =
    w.source === "B" ? (
      "Lucrare generată sintetic pentru planificarea intervențiilor în context de furtună."
    ) : w.source === "C" ? (
      "Analiză tensiuni, risc și soluții pentru ziua de mâine."
    ) : (
      <>
        Predicții, recomandări, rute, urme de decizie. Model: {id_(w.prediction.model_version)}.
      </>
    );
  const Icon = w.source === "B" ? CloudLightning : w.source === "C" ? Zap : bilant ? GaugeIcon : UtilityPole;

  return (
    <AppShell info={info}>
      <div className={PAGE}>
        <PageTitle title={title} subtitle={subtitle} icon={Icon} />
        {invalid ? (
          <p className="mt-4">
            <Pill tone="orange" size="lg">Respinsă la intrare: date greșite</Pill>
          </p>
        ) : null}
        <div className="mt-5">
          <ItemChips id={w.work_item_id} scenario={scenario} active={active} tags={tags} />
        </div>
        <CardGrid cards={visible} />
        <p className="mt-6 text-[13px] text-ink-soft">
          Lucrarea <span translate="no">{w.work_item_id}</span>. Datele vin din: {SOURCE_LABEL_RO[result.source]}
          {result.degradedReason ? `. ${result.degradedReason}` : ""}.
        </p>
      </div>
    </AppShell>
  );
}
