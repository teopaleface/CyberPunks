import type { ComponentType, ReactNode, SVGProps } from "react";
import { cn } from "cn";

export type SolidTone = "green" | "orange" | "blue" | "violet" | "amber" | "grey" | "red";

const BG: Record<SolidTone, string> = {
  green: "bg-[#1a9e4f] text-white",
  orange: "bg-[#e5481a] text-white",
  blue: "bg-[#1f5fd6] text-white",
  violet: "bg-[#8c47b3] text-white",
  amber: "bg-[#b87a12] text-white",
  grey: "bg-[#3a4a63] text-white",
  red: "bg-[#c93a3a] text-white",
};

/** Pastila plină din tabele (decizia, sursa): fundal colorat, text alb. */
export function SolidPill({
  tone,
  icon: Icon,
  children,
  className,
}: {
  tone: SolidTone;
  icon?: ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;
  children: ReactNode;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[14px] font-[600] whitespace-nowrap", BG[tone], className)}>
      {Icon ? <Icon size={15} aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
