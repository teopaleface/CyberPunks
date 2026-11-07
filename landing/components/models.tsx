import type { ModelResult } from "@/lib/data";
import { df, nf, pf } from "@/lib/format";

/**
 * Cele patru modele, ca plăci (bento). Fiecare: ce găsește, cifra principală față de cel mai
 * puternic reper simplu (citite la build din reports/<sursă>/metrics.json) și ce date sunt sintetice.
 * Unde lipsește raportul, placa spune „in progress”, fără cifră.
 */
type Results = Partial<Record<ModelResult["key"], ModelResult>>;

function dataTag(share: number): string {
  if (share >= 0.999) return "Synthetic grids";
  if (share <= 0.001) return "Real public data";
  return `${pf(share)} synthetic`;
}

export function Models({ results }: { results: Results }) {
  const a = results.A;
  const bil = results.bilant;
  const b = results.B;
  const c = results.C;
  const tiles = [
    {
      key: "A",
      color: "#3b82f0",
      name: "Meters",
      headline: "Stolen power.",
      body: "Finds meters that are broken or tampered with, from their readings alone.",
      big: a ? pf(a.ours, 1) : null,
      caption: a ? `of the subtle problems it flags are real, against ${pf(a.baseline, 1)} for the best simple rule.` : null,
      more: a ? `On real theft labels (SGCC): ${pf(a.extra.sgcc, 0)} against ${pf(a.extra.sgccBaseline, 0)}.` : null,
      data: a ? `London smart meters with injected faults, SGCC theft labels. ${dataTag(a.syntheticShare)}.` : null,
      version: a?.version,
    },
    {
      key: "bilant",
      color: "#3b82f0",
      name: "Substation balance",
      headline: "Lost on the way.",
      body: "Compares the energy leaving each substation with what its customers’ meters record, learns the normal loss, and names the cause.",
      big: bil ? `${df(bil.factor, 1)}×` : null,
      caption: bil
        ? `smaller error on the normal loss than the ${bil.baselineName} (${df(bil.ours, 1)} vs ${df(bil.baseline, 1)} kWh a day).`
        : null,
      more: bil
        ? `Names the cause with an F1 of ${df(bil.extra.f1)} against ${df(bil.extra.f1Baseline)} for the rule table, and sees the ${pf(bil.extra.invisibleShare)} of lost energy that meter checks miss.`
        : null,
      data: bil ? `SimBench low-voltage grids, problems hidden by us. ${dataTag(bil.syntheticShare)}.` : null,
      version: bil?.version,
    },
    {
      key: "B",
      color: "#b84fc0",
      name: "Storms",
      headline: "Fallen poles.",
      body: "Predicts which areas lose power in tomorrow’s storm, so crews are in place before it hits.",
      big: b ? `${df(b.factor, 1)}×` : null,
      caption: b ? `better at catching outage days than the ${b.baselineName} (PR-AUC ${df(b.ours, 3)} vs ${df(b.baseline, 3)}).` : null,
      more: b ? `Tested on a year it never saw (2025). Its P10–P90 range holds the real peak ${pf(b.extra.coverage)} of the time.` : null,
      data: b ? `EAGLE-I outages and Open-Meteo weather for 80 US counties. ${dataTag(b.syntheticShare)}.` : null,
      version: b?.version,
    },
    {
      key: "C",
      color: "#c4880a",
      name: "Voltage",
      headline: "Too much sun.",
      body: "Predicts tomorrow’s noon voltage at every substation where rooftop solar pushes it past 253 V.",
      big: c ? `${df(c.factor, 1)}×` : null,
      caption: c ? `smaller error than a ${c.baselineName} (${df(c.ours, 4)} vs ${df(c.baseline, 4)} pu).` : null,
      more: c
        ? `${nf(c.extra.powerflowSeconds / c.extra.surrogateSeconds)}× faster than a full power-flow run: ${df(c.extra.surrogateSeconds, 2)} s instead of ${nf(c.extra.powerflowSeconds)} s for 300 substations.`
        : null,
      data: c ? `SimBench grids and real weather; labels from power-flow physics. ${dataTag(c.syntheticShare)}.` : null,
      version: c?.version,
    },
  ];

  return (
    <section id="sources" aria-labelledby="sources-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[1180px]">
        <div className="mx-auto max-w-[980px] text-center">
          <p className="reveal text-[1.2rem] font-semibold tracking-[-0.015em] text-ppc-blue sm:text-[1.35rem]">Four models, trained by us</p>
          <h2 id="sources-title" className="reveal t-section mt-3 text-balance">
            Fallen poles. Stolen power. Too much sun.
          </h2>
          <p className="reveal t-intro mx-auto mt-6 max-w-[40rem] text-balance text-ink-3">
            Each one runs in our code, is tested on data it never saw, and has to beat the simple way first.
          </p>
        </div>

        <ul className="mt-16 grid gap-5 sm:mt-24 md:grid-cols-2">
          {tiles.map((t) => (
            <li key={t.key} className="reveal flex flex-col rounded-[28px] border border-hairline bg-tile p-7 sm:p-10">
              <p className="flex items-center gap-2.5 text-[1rem] font-semibold text-ink-2">
                <span aria-hidden className="size-2.5 rounded-full" style={{ background: t.color }} />
                {t.name}
              </p>
              <h3 className="t-title mt-5 text-ink">{t.headline}</h3>
              <p className="mt-3 max-w-[30rem] text-[1.06rem] leading-[1.5] text-ink-3">{t.body}</p>
              <div className="mt-auto pt-10">
                {t.big ? (
                  <>
                    <p className="num text-[clamp(3rem,5.4vw,4.5rem)] leading-none font-semibold tracking-[-0.04em] text-ink">{t.big}</p>
                    <p className="mt-3 max-w-[30rem] text-[1rem] leading-snug text-ink-2">{t.caption}</p>
                    <p className="mt-3 max-w-[30rem] text-[0.92rem] leading-snug text-ink-3">{t.more}</p>
                    <p className="mt-6 border-t border-hairline pt-4 text-[0.8rem] leading-snug text-ink-3">
                      {t.data} <span className="whitespace-nowrap">Model {t.version}.</span>
                    </p>
                  </>
                ) : (
                  <p className="text-[1rem] text-ink-3">Results in progress.</p>
                )}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
