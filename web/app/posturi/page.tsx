import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { AppShell } from "@/components/shell/app-shell";
import { getPosts, withBilantLoss } from "@/lib/data/posts";
import { BILANT_LABEL } from "@/lib/extras";
import { Disclosure } from "@/components/simple/disclosure";
import { fmtDec, fmtInt, plural, sentence } from "@/lib/format";
import { approxLei } from "@/lib/human";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Posturile de transformare" };

const DOT: Record<string, string> = { verde: "#2f8f5b", galben: "#d9a400", roșu: "#c8321e", necunoscut: "#9aa4a9" };
const STATUS: Record<string, string> = { verde: "pierderi mici", galben: "de urmărit", roșu: "pierderi mari", necunoscut: "fără bilanț" };

export default function PostsPage({ searchParams }: PageProps<"/posturi">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Se încarcă posturile…</span>
      </div>}>
      <Posts searchParams={searchParams} />
    </Suspense>
  );
}

async function Posts({ searchParams }: { searchParams: PageProps<"/posturi">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info }, posts, view] = await Promise.all([loadShellInfo(scenario), getPosts(scenario), loadPlanView(scenario)]);
  const rows = withBilantLoss(posts.data, view.data?.workItemsById ?? {}).toSorted((a, b) => (b.loss_lei_month ?? -1) - (a.loss_lei_month ?? -1) || (b.meters_flagged ?? 0) - (a.meters_flagged ?? 0));
  const total = rows.reduce((s, p) => s + (p.loss_lei_month ?? 0), 0);
  const byColor = rows.reduce<Record<string, number>>((acc, p) => ((acc[p.color ?? "necunoscut"] = (acc[p.color ?? "necunoscut"] ?? 0) + 1), acc), {});
  const red = rows.filter((p) => p.color === "roșu");
  const top = rows.filter((p) => (p.loss_lei_month ?? 0) > 0).slice(0, 8);
  const href = (id: string) => `/posturi/${encodeURIComponent(id)}?scenariu=${encodeURIComponent(scenario)}`;
  const place = (p: (typeof rows)[number]) => (p.label ?? "").replace(/^PT-[\w-]+,\s*/, "").replace(/\s*\(sintetic\)$/, "");
  const signals = (p: (typeof rows)[number]) =>
    [
      p.meters_flagged ? plural(p.meters_flagged, "contor semnalat", "contoare semnalate") : null,
      p.voltage_p90_pu != null && p.voltage_p90_pu > 1.1 ? "tensiune peste limită la prânz" : null,
    ]
      .filter(Boolean)
      .join(", ");
  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1180px] px-10 pt-12 pb-20 text-[18px] leading-[1.5]">
        <p className="flex items-center gap-2 text-[16px] text-muted-foreground">
          <SyntheticGlyph size={14} /> {BILANT_LABEL}
        </p>
        <h1 className="mt-3 max-w-[30ch] text-[40px] leading-[1.15] font-[620] tracking-[-0.015em] text-balance">
          {red.length
            ? `${plural(red.length, "post pierde", "posturi pierd")} mult: peste ${fmtInt(posts.thresholds.red)} de lei pe lună.`
            : "Niciun post nu pierde mult."}
        </h1>
        <p className="mt-3 max-w-[64ch] text-[20px] text-ink-soft">
          Pierderea e lipsa dintre energia ieșită din post și suma contoarelor clienților. În total, {approxLei(total)} pe lună, pe{" "}
          {plural(rows.length, "post", "posturi")}.
        </p>
        <p className="mt-6">
          <Link
            href={`/harta?harta=posturi&scenariu=${encodeURIComponent(scenario)}`}
            className="text-[17px] underline decoration-rule underline-offset-[5px] hover:decoration-ink"
          >
            Vezi posturile pe hartă
          </Link>
        </p>

        <section aria-labelledby="top" className="mt-12">
          <h2 id="top" className="text-[22px] font-[620]">
            Unde se pierd cei mai mulți bani, pe lună
          </h2>
          {top.length ? (
            <ol className="mt-4 divide-y divide-rule border-y border-rule">
              {top.map((p) => (
                <li key={p.post_id} className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-8 py-4">
                  <span className="min-w-0">
                    <span className="flex items-center gap-3">
                      <span className="size-3 shrink-0 rounded-full" style={{ background: DOT[p.color ?? "necunoscut"] ?? DOT.necunoscut }} aria-hidden="true" />
                      <Link href={href(p.post_id)} className="text-[20px] font-[600] underline decoration-rule underline-offset-4 hover:decoration-ink" translate="no">
                        {p.post_id}
                      </Link>
                      <span className="truncate text-muted-foreground">{place(p)}</span>
                    </span>
                    <span className="mt-1 block pl-6 text-ink-soft">
                      {p.diagnosis ? sentence(p.diagnosis).replace(/\.$/, "") : p.derived ? "Estimat din contoarele semnalate" : "Cauză necunoscută"}
                      {signals(p) ? <span className="text-muted-foreground">; {signals(p)}</span> : null}
                    </span>
                  </span>
                  <span className="text-right text-[19px] font-[600] whitespace-nowrap tabular-nums">{approxLei(p.loss_lei_month)}</span>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-4 text-muted-foreground">Nu există posturi cu pierderi în planul acestui scenariu.</p>
          )}
        </section>

        <Disclosure className="mt-12" title={`Toate cele ${plural(rows.length, "post", "posturi")}`} hint="tabelul complet, cu cifrele exacte">
          <ul className="mb-3 flex flex-wrap gap-x-6 gap-y-1 text-[15px]">
            {(["roșu", "galben", "verde", "necunoscut"] as const).map((c) => (
              <li key={c} className="flex items-center gap-2">
                <span className="size-3 rounded-full" style={{ background: DOT[c] }} aria-hidden="true" />
                {STATUS[c]}: <b className="font-[620] tabular-nums">{fmtInt(byColor[c] ?? 0)}</b>
              </li>
            ))}
            <li className="text-muted-foreground">
              praguri de afișare: {fmtInt(posts.thresholds.yellow)} și {fmtInt(posts.thresholds.red)} lei pe lună
            </li>
          </ul>
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] border-collapse text-[15px]">
              <thead>
                <tr className="border-y border-rule text-left text-[13.5px] text-muted-foreground">
                  <th className="py-2 pr-4 font-[500]">Postul</th>
                  <th className="py-2 pr-4 text-right font-[500]">Lei pe lună</th>
                  <th className="py-2 pr-4 text-right font-[500]">Lipsă pe zi</th>
                  <th className="py-2 pr-4 font-[500]">Cauza probabilă</th>
                  <th className="py-2 pr-4 text-right font-[500]">Contoare semnalate</th>
                  <th className="py-2 text-right font-[500]">Tensiune P90</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.post_id} className="border-b border-rule" style={{ contentVisibility: "auto", containIntrinsicSize: "auto 44px" }}>
                    <td className="py-2 pr-4">
                      <span className="flex items-center gap-2.5">
                        <span className="size-3 shrink-0 rounded-full" style={{ background: DOT[p.color ?? "necunoscut"] ?? DOT.necunoscut }} aria-hidden="true" />
                        <Link href={href(p.post_id)} className="code-id underline decoration-rule underline-offset-4 hover:decoration-ink" translate="no">
                          {p.post_id}
                        </Link>
                        <span className="truncate text-[13.5px] text-muted-foreground">
                          {place(p)}
                          <span className="sr-only">, {STATUS[p.color ?? "necunoscut"]}</span>
                        </span>
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-right font-[600] tabular-nums">{p.loss_lei_month != null ? fmtInt(p.loss_lei_month) : "–"}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{p.loss_kwh_day == null ? "–" : p.loss_kwh_day >= 0 ? `${fmtDec(p.loss_kwh_day, 1)} kWh` : "surplus"}</td>
                    <td className="py-2 pr-4">{p.diagnosis ?? <span className="text-muted-foreground">{p.derived ? "estimat din contoarele A" : "–"}</span>}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{fmtInt(p.meters_flagged ?? 0)}</td>
                    <td className="py-2 text-right tabular-nums">{p.voltage_p90_pu != null ? `${fmtDec(p.voltage_p90_pu, 3)} pu` : "–"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-[13.5px] text-muted-foreground">
            {posts.derived ? "Pierderile sunt estimate din contoarele semnalate de modelul A, până vine bilanțul. " : ""}
            {posts.degradedReason ? `${posts.degradedReason.charAt(0).toUpperCase()}${posts.degradedReason.slice(1)}.` : ""}
          </p>
        </Disclosure>
      </div>
    </AppShell>
  );
}
