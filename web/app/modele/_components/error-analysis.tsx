import type { ReactNode } from "react";
import type { Source } from "@/lib/contracts";
import { markerSvg } from "@/lib/marker-svg";
import { SOURCES } from "@/lib/sources";

/**
 * Prima secțiune din reports/<X>/error_analysis.md, ca text simplu.
 * Nu interpretăm HTML: citim doar paragrafe și tabele cu bare verticale, iar React scapă tot textul.
 */

type Block = { kind: "p"; text: string } | { kind: "table"; head: string[]; rows: string[][] };

interface Parsed {
  intro: Block[];
  title: string | null;
  blocks: Block[];
  /** Câte secțiuni mai are fișierul după prima. */
  more: number;
}

const MAX_CHARS = 200_000;

function cells(line: string): string[] {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((c) => c.trim());
}

function toBlocks(lines: string[]): Block[] {
  const out: Block[] = [];
  let para: string[] = [];
  let table: string[][] = [];
  const flushPara = () => {
    if (para.length) out.push({ kind: "p", text: para.join(" ") });
    para = [];
  };
  const flushTable = () => {
    if (table.length) out.push({ kind: "table", head: table[0], rows: table.slice(1) });
    table = [];
  };
  for (const raw of lines) {
    const line = raw.trim();
    if (line.startsWith("|")) {
      flushPara();
      if (/^\|[\s|:-]+\|?$/.test(line)) continue; // rândul de separare |---|---|
      table.push(cells(line));
      continue;
    }
    flushTable();
    if (!line) {
      flushPara();
      continue;
    }
    para.push(line.replace(/^#{3,6}\s+/, "").replace(/^[-*]\s+/, ""));
  }
  flushPara();
  flushTable();
  return out;
}

export function parseFirstSection(md: string): Parsed {
  const lines = md.slice(0, MAX_CHARS).split(/\r?\n/);
  const intro: string[] = [];
  const section: string[] = [];
  let title: string | null = null;
  let more = 0;
  let stage: "intro" | "section" | "rest" = "intro";
  for (const line of lines) {
    const h2 = /^##\s+(.+)$/.exec(line);
    if (/^#\s+/.test(line)) continue; // titlul documentului
    if (h2) {
      if (stage === "intro") {
        title = h2[1].trim();
        stage = "section";
        continue;
      }
      stage = "rest";
      more++;
      continue;
    }
    if (stage === "intro") intro.push(line);
    else if (stage === "section") section.push(line);
  }
  return { intro: toBlocks(intro), title, blocks: toBlocks(section), more };
}

/** `cod` devine text monospațiat; **gros** își pierde stelele. Totul rămâne text. */
function inline(text: string): ReactNode[] {
  return text
    .replace(/\*\*|__/g, "")
    .split("`")
    .map((part, i) =>
      i % 2 === 1 ? (
        <code key={i} className="dense text-[0.95em]">
          {part}
        </code>
      ) : (
        part
      ),
    );
}

const NUM = /^-?\d+(\.\d+)?$/;
const numFmt = new Intl.NumberFormat("ro-RO", { maximumFractionDigits: 3 });

function cell(text: string): { text: string; numeric: boolean } {
  return NUM.test(text) ? { text: numFmt.format(Number(text)), numeric: true } : { text, numeric: false };
}

function Blocks({ blocks }: { blocks: Block[] }) {
  return (
    <>
      {blocks.map((b, i) =>
        b.kind === "p" ? (
          <p key={i} className="mt-2 max-w-[96ch] text-[15.5px] leading-relaxed">
            {inline(b.text)}
          </p>
        ) : (
          <div key={i} className="mt-3 overflow-x-auto">
            <table className="w-full border-collapse text-[15px]">
              <thead>
                <tr className="text-[13.5px] text-muted-foreground">
                  {b.head.map((h, j) => (
                    <th key={j} scope="col" className={`py-1.5 pr-4 font-[500] ${j === 0 ? "text-left" : "text-right"}`}>
                      {inline(h.charAt(0).toLocaleUpperCase("ro-RO") + h.slice(1))}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {b.rows.map((row, r) => (
                  <tr key={r} className="border-t border-rule">
                    {row.map((c, j) => {
                      const v = cell(c);
                      return j === 0 ? (
                        <th key={j} scope="row" className="py-1.5 pr-4 text-left font-[450]">
                          {inline(c)}
                        </th>
                      ) : (
                        <td key={j} className={`py-1.5 pr-4 ${v.numeric ? "text-right tabular-nums" : "text-right"}`}>
                          {v.numeric ? v.text : inline(c)}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ),
      )}
    </>
  );
}

export function ErrorAnalysis({ source, md }: { source: Source; md: string }) {
  const parsed = parseFirstSection(md);
  const meta = SOURCES[source];
  const file = `reports/${source}/error_analysis.md`;
  return (
    <section id={`erori-${source}`} aria-labelledby={`erori-${source}-title`} className="scroll-mt-6 border-t border-rule pt-5">
      <div className="flex items-center gap-3">
        <span className="size-8 shrink-0" dangerouslySetInnerHTML={{ __html: markerSvg({ source }, 32) }} />
        <h3 id={`erori-${source}-title`} className="text-[19px] font-[650]">
          Modelul {source}, {meta.name}
          {parsed.title ? <span className="font-[500] text-muted-foreground">: {parsed.title.toLocaleLowerCase("ro-RO")}</span> : null}
        </h3>
      </div>
      {parsed.intro.length || parsed.blocks.length ? (
        <>
          <Blocks blocks={parsed.intro} />
          <Blocks blocks={parsed.blocks} />
        </>
      ) : (
        <p className="mt-2 text-[15px] text-muted-foreground">Fișierul există, dar e gol.</p>
      )}
      <p className="mt-2.5 text-[13.5px] text-muted-foreground">
        {parsed.more ? `Aici e prima secțiune; încă ${parsed.more === 1 ? "o secțiune" : `${parsed.more} secțiuni`} în ` : "Din "}
        <span className="dense">{file}</span>.
      </p>
    </section>
  );
}
