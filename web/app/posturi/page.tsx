import { englishText } from "@/lib/english";
import type { Metadata } from "next";
import { UtilityPole } from "lucide-react";
import { connection } from "next/server";
import { Suspense } from "react";
import { PageTitle } from "@/components/ds";
import { PostsScreen } from "@/components/posts/posts-screen";
import { AppShell } from "@/components/shell/app-shell";
import { getPosts, withBilantLoss } from "@/lib/data/posts";
import { postColor, postPlace, regionOfPost, type PostRow, type StatusFilter } from "@/lib/posts-view";
import { loadPlanView, loadShellInfo, resolveScenario } from "@/lib/server/queries";

export const metadata: Metadata = { title: "Substations" };

export default function PostsPage({ searchParams }: PageProps<"/posturi">) {
  return (
    <Suspense fallback={<div role="status" className="min-h-dvh bg-canvas" aria-busy="true">
        <span className="sr-only">Loading substations…</span>
      </div>}>
      <Posts searchParams={searchParams} />
    </Suspense>
  );
}

const one = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v) ?? "";

async function Posts({ searchParams }: { searchParams: PageProps<"/posturi">["searchParams"] }) {
  await connection();
  const sp = await searchParams;
  const scenario = await resolveScenario(searchParams);
  const [{ info }, posts, view] = await Promise.all([loadShellInfo(scenario), getPosts(scenario), loadPlanView(scenario)]);
  const area = view.data?.area.regions ?? {};
  const list = withBilantLoss(posts.data, view.data?.workItemsById ?? {});
  const rows: PostRow[] = list.map((p) => ({
    id: p.post_id,
    lat: p.lat,
    lon: p.lon,
    region: regionOfPost(p, area),
    place: postPlace(p),
    loss: p.loss_lei_month ?? null,
    color: postColor(p, posts.thresholds),
    meters: p.meters_flagged ?? 0,
    diagnosis: p.diagnosis ? englishText(p.diagnosis) : null,
    voltage: p.voltage_p90_pu ?? null,
    title: p.label && p.label !== p.post_id ? `${p.post_id}, ${englishText(p.label.replace(`${p.post_id}, `, ""))}` : p.post_id,
  }));
  // doar regiunile în care există posturi (în datele de azi: toate sunt în Muntenia Sud)
  const present = new Set(rows.map((r) => r.region));
  const regions = Object.entries(area)
    .filter(([id]) => present.has(id))
    .map(([id, r]) => ({ id, label: englishText(r.label_ro ?? id) }));
  const status = one(sp.status);
  const initial = {
    region: one(sp.regiune) || "toate",
    status: (status === "verde" || status === "galben" || status === "roșu" ? status : "toate") as StatusFilter,
    q: one(sp.q),
  };
  return (
    <AppShell info={info}>
      <div className="mx-auto w-full max-w-[1520px] px-8 pt-7 pb-14 max-md:px-4">
        <PageTitle
          icon={UtilityPole}
          title={regions.length ? `Substations: ${regions.map((r) => r.label).join(", ")}` : "Substations"}
          subtitle="Estimated monthly losses and recommended status."
        />
        {rows.length ? (
          <PostsScreen rows={rows} regions={regions} scenario={scenario} thresholds={posts.thresholds} initial={initial} derived={posts.derived} />
        ) : (
          <p role="status" className="mt-8 text-ink-soft">
            No substations in scenario &quot;{scenario}&quot;.{posts.degradedReason ? ` ${englishText(posts.degradedReason)}.` : ""}
          </p>
        )}
        <p className="mt-5 text-[13px] text-muted-foreground">
          Synthetic data simulated from public data for the PPC use case.
          {posts.derived ? " Losses are estimated from flagged meters until the energy balance is available." : ""}
        </p>
      </div>
    </AppShell>
  );
}
