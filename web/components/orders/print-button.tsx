"use client";

import { Printer } from "lucide-react";
import { btn } from "@/components/ds";

export function PrintButton() {
  return (
    <button type="button" onClick={() => window.print()} className={btn("outline")}>
      <Printer aria-hidden="true" size={19} strokeWidth={1.8} />
      Tipărește
    </button>
  );
}
