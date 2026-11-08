"use client";
import { Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { requestAssistantAction } from "@/lib/operations/assistant-intent";
import { fmtTime } from "@/lib/format";
export function ApproveList({scenario, planId, approvedAt, approvedLocal}: {scenario:string;planId:string;approvedAt:string|null;approvedLocal:boolean}) {
  if (approvedAt && !approvedLocal) return <p role="status" className="flex items-center gap-2 text-ok"><Check size={18} aria-hidden="true"/>Assignments approved at {fmtTime(approvedAt)}</p>;
  return <Button size="panel" onClick={() => requestAssistantAction("approve_plan", {plan_id:planId}, scenario)}><Check size={18} aria-hidden="true"/>Review crew approval</Button>;
}
