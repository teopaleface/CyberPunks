import Link from "next/link";
import { Suspense } from "react";
import { DEFAULT_SCENARIO, getWorkItem } from "@/lib/data";
import { SOURCE_LABEL_RO } from "@/lib/data/labels";

// Pagină provizorie: lucrarea, decizia și auditul ei, ca JSON.

const SCENARIO_RE = /^[A-Za-z0-9_.-]{1,64}$/;

function safeDecode(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

export default function WorkItemPage({ params, searchParams }: PageProps<"/lucrari/[id]">) {
  return (
    <main className="mx-auto w-full max-w-4xl space-y-4 p-6 text-sm">
      <Link href="/">Înapoi la plan</Link>
      <Suspense fallback={<p>Se încarcă lucrarea…</p>}>
        <WorkItemJson params={params} searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function WorkItemJson({
  params,
  searchParams,
}: Pick<PageProps<"/lucrari/[id]">, "params" | "searchParams">) {
  const id = safeDecode((await params).id);
  const query = await searchParams;
  const requested = typeof query.scenariu === "string" ? query.scenariu : undefined;
  const scenario = requested && SCENARIO_RE.test(requested) ? requested : DEFAULT_SCENARIO;
  const result = await getWorkItem(id, scenario);

  return (
    <section className="space-y-2">
      <h1 className="text-xl font-semibold">Lucrarea {id}</h1>
      <p>
        Sursa datelor: <strong data-source={result.source}>{SOURCE_LABEL_RO[result.source]}</strong>
      </p>
      {result.degradedReason ? <p role="status">Atenție: {result.degradedReason}</p> : null}
      {result.data ? (
        <>
          {result.data.invalid ? <p>Lucrare respinsă la intrare: datele nu respectă contractul.</p> : null}
          <pre className="overflow-x-auto whitespace-pre-wrap">{JSON.stringify(result.data, null, 2)}</pre>
        </>
      ) : (
        <p>Lucrarea nu există în scenariul „{scenario}”.</p>
      )}
    </section>
  );
}
