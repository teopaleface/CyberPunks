"use client";

import Link from "next/link";
import type { ComponentProps } from "react";

/** Rândul listei: schimbă cazul fără salt pe ecrane late; pe ecrane înguste, duce la cardul „Aprobare”. */
export function CaseLink({ onClick, ...props }: ComponentProps<typeof Link>) {
  return (
    <Link
      {...props}
      scroll={false}
      onClick={(e) => {
        onClick?.(e);
        if (window.matchMedia("(max-width: 1023px)").matches) {
          window.setTimeout(() => document.getElementById("aprobare")?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
        }
      }}
    />
  );
}
