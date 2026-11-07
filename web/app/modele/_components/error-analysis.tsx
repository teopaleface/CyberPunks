import type { Source } from "@/lib/contracts";

const FINDINGS: Record<Source, { title: string; points: string[] }> = {
  A: {
    title: "Meter detection limits",
    points: [
      "London fault and theft labels are synthetic. Obvious defects inflate the overall top-K precision; the subtle-anomaly test is the more demanding comparison.",
      "Shifted meter clocks, gradual under-recording and partial bypass remain weak spots. Missing readings reduce performance.",
      "Low consumption is not evidence of theft. Suspected theft in the lowest consumption group requires human review.",
    ],
  },
  B: {
    title: "Storm prediction limits",
    points: [
      "Weather signals can miss ordinary equipment faults and short, local gusts. The model score does not confirm that an outage will occur.",
      "Performance varies by weather type. Snow totals do not show whether snow is heavy and wet enough to damage lines.",
      "Missing EAGLE-I rows can mean either no outage or a collection gap, so some apparent false alarms may be unrecorded outages.",
    ],
  },
  C: {
    title: "Voltage prediction limits",
    points: [
      "Grid and substation data are synthetic; weather is real. Tests hold out network topologies and later months, but real Romanian networks may differ.",
      "Errors are largest on long, weak rural networks, substations with batteries and cases near the 1.10 pu limit. Battery state of charge adds uncertainty.",
      "Hourly simulation smooths short peaks. It does not verify the 10-minute averages used in voltage standards.",
    ],
  },
};

/** Source reports remain intact and are explicitly labelled with their language. */
export function ErrorAnalysis({ source, md }: { source: Source; md: string }) {
  const findings = FINDINGS[source];
  return (
    <section id={`erori-${source}`} aria-labelledby={`erori-${source}-title`} className="scroll-mt-6">
      <h3 id={`erori-${source}-title`} className="text-[16px] font-[600]">{findings.title}</h3>
      <ul className="mt-2 list-disc space-y-2 pl-5 text-[14.5px] leading-relaxed text-ink-soft">
        {findings.points.map((point) => <li key={point}>{point}</li>)}
      </ul>
      <p className="mt-3 text-[12.5px] text-muted-foreground">Source: <code>reports/{source}/error_analysis.md</code></p>
      <a
        href={`data:text/markdown;charset=utf-8,${encodeURIComponent(md)}`}
        download={`model-${source}-error-analysis.ro.md`}
        className="mt-3 inline-block text-[14px] underline decoration-rule underline-offset-4 hover:decoration-ink"
      >
        Download source report, Romanian
      </a>
    </section>
  );
}
