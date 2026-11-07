import { Coins, MapPin, Network, ClipboardCheck, Layers, UserRound } from "lucide-react";
import type { ComponentType, SVGProps } from "react";
import { TONE, type Tone } from "@/components/ds";
import { fmtInt } from "@/lib/format";
import type { PlanSummary } from "@/lib/contracts";

type Icon = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string; strokeWidth?: number | string }>;

function Tile({ icon: I, tone, value, label, unit }: { icon: Icon; tone: Tone; value: string; label?: string; unit?: string }) {
  return (
    <div className={`flex min-w-0 items-center gap-3 rounded-[14px] border border-rule bg-panel px-4 py-4 max-md:px-3.5 max-md:py-3 min-[1700px]:gap-3.5 min-[1700px]:px-5`}>
      <I aria-hidden="true" size={36} strokeWidth={1.4} className={`shrink-0 max-md:size-8 max-[1500px]:size-8 ${TONE[tone].text}`} />
      <div className="min-w-0">
        <p className="text-[27px] leading-tight font-[700] tracking-[-0.02em] whitespace-nowrap tabular-nums max-[1500px]:text-[23px] max-md:text-[22px]">
          {value}
          {unit ? <span className="ml-1.5">{unit}</span> : null}
        </p>
        {label ? <p className="truncate text-[15px] text-ink-soft max-md:text-[14px]">{label}</p> : null}
      </div>
    </div>
  );
}

/** Cele șase cifre ale zilei, din rezumatul planului. */
export function KpiRow({ s }: { s: PlanSummary }) {
  return (
    <div className="grid grid-cols-2 gap-3.5 min-[768px]:grid-cols-3 min-[1340px]:grid-cols-6">
      <Tile icon={ClipboardCheck} tone="blue" value={fmtInt(s.items_in)} label="lucrări primite" />
      <Tile icon={Network} tone="violet" value={fmtInt(s.assigned)} label="în trasee" />
      <Tile icon={Layers} tone="blue" value={fmtInt(s.remote_actions)} label="la distanță" />
      <Tile icon={UserRound} tone="amber" value={fmtInt(s.human_review)} label="la om" />
      <Tile icon={MapPin} tone="blue" value={fmtInt(Math.round(s.total_km))} unit="km" />
      <Tile icon={Coins} tone="amber" value={fmtInt(Math.round(s.expected_value_lei))} unit="lei" />
    </div>
  );
}

