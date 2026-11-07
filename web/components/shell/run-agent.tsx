"use client";

import { AudioLines } from "lucide-react";
import { Button } from "@/components/ui/button";
import { englishText } from "@/lib/english";

/** The legacy model-run action is disabled. Open the shared assistant without claiming a rerun. */
export function RunAgentButton({ scenario, scenarioLabel }: { scenario: string; scenarioLabel: string }) {
  return (
    <Button size="panel" variant="outline" className="px-4 max-[1600px]:px-3"
      aria-label={`Ask Daybreak about ${englishText(scenarioLabel)}`}
      onClick={() => window.dispatchEvent(new CustomEvent("daybreak:assistant", { detail: { scenario } }))}>
      <AudioLines aria-hidden="true" size={18} />
      Ask Daybreak
    </Button>
  );
}
