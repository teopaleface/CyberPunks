import type { ReactNode } from "react";
import type { DecisionType } from "@/lib/contracts";
import { fmtInt, plural } from "@/lib/format";
import { ACTION_ORDER, DECISION_HINT_RO } from "./build-rows";
import type { JournalRow } from "./types";

interface Cell {
  key: string;
  value: number;
  label: ReactNode;
  hint: ReactNode;
  attention?: boolean;
}

/**
 * Cifrele jurnalului, ca afișajele de pe ecranul planului: cifre late, despărțite de linii subțiri.
 * „Decide un om” e portocaliu, ca peste tot în consolă.
 */
export function JournalSummary({ rows }: { rows: JournalRow[] }) {
  const decisions = rows.filter((r) => r.kind !== "run");
  const runs = rows.filter((r) => r.kind === "run").length;
  const agent = decisions.filter((r) => r.actor === "agent");
  const human = decisions.filter((r) => r.actor === "human");

  const count = (list: JournalRow[], action: string) => list.filter((r) => r.action === action).length;
  const humanParts = [
    [count(human, "review_approve"), "aprobare", "aprobări"],
    [count(human, "review_reject"), "respingere", "respingeri"],
    [count(human, "review_defer"), "amânare", "amânări"],
  ] as const;
  const humanHint = humanParts
    .filter(([n]) => n > 0)
    .map(([n, one, few]) => plural(n, one, few))
    .join(", ");

  const typeCells: Cell[] = ACTION_ORDER.filter((a): a is DecisionType => a in DECISION_HINT_RO)
    .map((a) => ({ a, n: count(agent, a), label: agent.find((r) => r.action === a)?.actionLabel ?? a }))
    .filter((t) => t.n > 0)
    .map((t) => ({
      key: t.a,
      value: t.n,
      label: t.label.toLocaleLowerCase("ro-RO"),
      hint: DECISION_HINT_RO[t.a],
      attention: t.a === "human_review",
    }));

  const cells: Cell[] = [
    {
      key: "all",
      value: decisions.length,
      label: decisions.length === 1 ? "decizie" : "decizii",
      hint: runs ? `din ${plural(runs, "rulare", "rulări")} ${runs === 1 ? "a" : "ale"} agentului` : "în jurnal",
    },
    { key: "agent", value: agent.length, label: "ale agentului", hint: "singur, după reguli" },
    { key: "human", value: human.length, label: "ale omului", hint: humanHint || "nicio decizie încă" },
    ...typeCells,
  ];

  return (
    <section aria-label="Cifrele jurnalului" className="flex h-[88px] shrink-0 overflow-hidden border-b border-rule bg-canvas">
      <dl className="flex min-w-0 flex-1">
        {cells.map((c, i) => (
          <div
            key={c.key}
            className={
              "flex min-w-0 flex-auto items-center gap-3 border-l border-rule px-6 first:border-l-0 first:pl-7 " +
              (i === 3 ? "border-l-2 border-l-ink/25" : "")
            }
          >
            <dd className={"num-wide order-1 text-[clamp(28px,2.1vw,40px)] whitespace-nowrap " + (c.attention ? "text-att" : "")}>
              {fmtInt(c.value)}
            </dd>
            <dt className="order-2 min-w-0 text-[14px] leading-[1.3] text-muted-foreground">
              <b className="block truncate font-[560] text-ink">{c.label}</b>
              <span className="block truncate">{c.hint}</span>
            </dt>
          </div>
        ))}
      </dl>
    </section>
  );
}
