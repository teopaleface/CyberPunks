import type { Metadata } from "next";
import Link from "next/link";
import { connection } from "next/server";
import { Suspense } from "react";
import { SyntheticGlyph } from "@/components/shell/provenance";
import { AppShell } from "@/components/shell/app-shell";
import { getPosts } from "@/lib/data/posts";
import { BILANT_LABEL } from "@/lib/extras";
import { fmtDec, fmtInt, fmtLei } from "@/lib/format";
import { loadShellInfo, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Posturile de transformare" };

const DOT: Record<string, string> = { verde: "#2f8f5b", galben: "#d9a400", roșu: "#c8321e", necunoscut: "#9aa4a9" };
const STATUS: Record<string, string> = { verde: "pierderi mici", galben: "de urmărit", roșu: "pierderi mari", necunoscut: "fără bilanț" };

export default function PostsPage({ searchParams }: PageProps<"/posturi">) {
  return (
    <Suspense fallback={<div className="min-h-dvh bg-canvas" aria-busy="true" aria-label="Se încarcă posturile" />}>
      <Posts searchParams={searchParams} />
    </Suspense>
  );
}

async function Posts({ searchParams }: { searchParams: PageProps<"/posturi">["searchParams"] }) {
  await connection();
  const scenario = await resolveScenario(searchParams);
  const [{ info }, posts] = await Promise.all([loadShellInfo(scenario), getPosts(scenario)]);
  const rows = posts.data.toSorted((a, b) => (b.loss_lei_month ?? -1) - (a.loss_lei_month ?? -1) || (b.meters_flagged ?? 0) - (a.meters_flagged ?? 0));
  const total = rows.reduce((s, p) => s + (p.loss_lei_month ?? 0), 0);
  const byColor = rows.reduce<Record<string, number>>((acc, p) => ((acc[p.color ?? "necunoscut"] = (acc[p.color ?? "necunoscut"] ?? 0) + 1), acc), {});
  return (
    <AppShell info={info}>
      <section className="border-b border-rule bg-panel px-7 pt-5 pb-4">
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-2">
          <div>
            <h1 className="text-[26px] leading-tight font-[650]">Posturile de transformare</h1>
            <p className="mt-1 max-w-[90ch] text-[16px] text-muted-foreground">
              Unde se pierd cei mai mulți bani: lipsa dintre energia ieșită din post și suma contoarelor clienților, în lei pe lună.
              În total {fmtLei(total)} pe lună, pe {fmtInt(rows.length)} posturi.
            </p>
          </div>
          <span className="flex items-center gap-2 text-[14px] text-muted-foreground">
            <SyntheticGlyph size={14} /> {BILANT_LABEL}
          </span>
        </div>
        <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[14.5px]">
          {(["roșu", "galben", "verde", "necunoscut"] as const).map((c) => (
            <li key={c} className="flex items-center gap-2">
              <span className="size-3 rounded-full" style={{ background: DOT[c] }} aria-hidden="true" />
              {STATUS[c]}: <b className="font-[620] tabular-nums">{fmtInt(byColor[c] ?? 0)}</b>
            </li>
          ))}
          <li className="text-muted-foreground">
            praguri de afișare: {posts.thresholds.yellow} și {posts.thresholds.red} lei pe lună
          </li>
        </ul>
      </section>
      <div className="overflow-x-auto px-7 py-4">
        <table className="w-full min-w-[960px] border-collapse text-[15px]">
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
                    <Link href={`/posturi/${encodeURIComponent(p.post_id)}?scenariu=${encodeURIComponent(scenario)}`} className="code-id underline decoration-rule underline-offset-4 hover:decoration-ink" translate="no">
                      {p.post_id}
                    </Link>
                    <span className="truncate text-[13.5px] text-muted-foreground">
                      {(p.label ?? "").replace(/^PT-[\w-]+,\s*/, "").replace(/\s*\(sintetic\)$/, "")}
                      <span className="sr-only">, {STATUS[p.color ?? "necunoscut"]}</span>
                    </span>
                  </span>
                </td>
                <td className="py-2 pr-4 text-right font-[600] tabular-nums">{p.loss_lei_month != null ? fmtInt(p.loss_lei_month) : "–"}</td>
                <td className="py-2 pr-4 text-right tabular-nums">{p.loss_kwh_day != null ? `${fmtDec(p.loss_kwh_day, 1)} kWh` : "–"}</td>
                <td className="py-2 pr-4">{p.diagnosis ?? <span className="text-muted-foreground">{p.derived ? "estimat din contoarele A" : "–"}</span>}</td>
                <td className="py-2 pr-4 text-right tabular-nums">{fmtInt(p.meters_flagged ?? 0)}</td>
                <td className="py-2 text-right tabular-nums">{p.voltage_p90_pu != null ? `${fmtDec(p.voltage_p90_pu, 3)} pu` : "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 ? <p className="py-10 text-center text-[15px] text-muted-foreground">Nu există posturi în planul acestui scenariu.</p> : null}
        <p className="mt-3 text-[13.5px] text-muted-foreground">
          {posts.derived ? "Pierderile sunt estimate din contoarele semnalate de modelul A, până vine bilanțul. " : ""}
          {posts.degradedReason ? `${posts.degradedReason.charAt(0).toUpperCase()}${posts.degradedReason.slice(1)}.` : ""}
        </p>
      </div>
    </AppShell>
  );
}
