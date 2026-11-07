import { ScrollWords } from "./scroll-words";

/**
 * Problema: o frază mare care se aprinde la derulare, patru cifre publice cu sursa în note
 * (subsolul paginii) și citatul din tema PPC. Cifrele publice sunt scrise aici, cu sursa și data;
 * cifrele modelelor nu apar aici (ele vin doar din reports/).
 */
const STATS = [
  { value: "3.18M", label: "customers on the Rețele Electrice network", note: 1 },
  { value: "385,791", label: "prosumers in Romania, and the count keeps rising", note: 2 },
  { value: "8.66%", label: "of the energy entering the Muntenia grid lost on the way", note: 3 },
  { value: "≈85%", label: "of Romania’s automatic outage compensation paid by Rețele Electrice", note: 4 },
];

export function Problem() {
  return (
    <section id="problem" aria-labelledby="problem-title" className="px-5 py-28 sm:px-8 sm:py-40">
      <div className="mx-auto max-w-[980px]">
        <h2 id="problem-title" className="sr-only">
          The problem
        </h2>
        <ScrollWords
          className="text-[clamp(1.9rem,4.2vw,3.5rem)] leading-[1.12] font-semibold tracking-[-0.028em] text-ink"
          text="Every evening, someone at Rețele Electrice decides where tomorrow’s crews go. Hundreds of meters that may be broken or tampered with. A storm heading for Banat. Streets where rooftop solar pushes the voltage past the limit at noon. And only a handful of crews."
        />
      </div>

      <dl className="mx-auto mt-28 grid max-w-[1180px] grid-cols-1 gap-x-10 gap-y-14 sm:mt-36 sm:grid-cols-2 lg:grid-cols-4">
        {STATS.map((s) => (
          <div key={s.value} className="reveal border-t border-hairline-strong pt-6">
            <dt className="sr-only">{s.label}</dt>
            <dd>
              <span className="num block text-[clamp(2.6rem,4.4vw,3.75rem)] leading-none font-semibold tracking-[-0.035em] text-ink">{s.value}</span>
              <span className="mt-4 block max-w-[17rem] text-[1.05rem] leading-snug text-ink-3">
                {s.label}
                <a href={`#note-${s.note}`} className="ml-0.5 align-super text-[0.7em] text-ink-3 hover:text-ink" aria-label={`Source ${s.note}`}>
                  {s.note}
                </a>
              </span>
            </dd>
          </div>
        ))}
      </dl>

      <figure className="mx-auto mt-32 max-w-[980px] text-center sm:mt-48">
        <blockquote className="reveal t-title mx-auto max-w-[24ch] text-balance text-ink-2">
          “An anomaly score of 0.87 doesn’t tell a technician where to go tomorrow morning.”
        </blockquote>
        <figcaption className="mt-5 text-[0.95rem] text-ink-3">
          PPC, SmartHack XI 2026 brief (translated)
          <a href="#note-5" className="ml-0.5 align-super text-[0.7em] hover:text-ink" aria-label="Source 5">
            5
          </a>
        </figcaption>
        <p className="reveal sunrise-text t-section mt-14 pb-2">Daybreak does.</p>
      </figure>
    </section>
  );
}
