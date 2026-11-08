"use client";
import { useCallback, useEffect, useState } from "react";
import { Camera, UserRoundPen } from "lucide-react";
import { api } from "@/lib/operations/client";
import { requestAssistantAction } from "@/lib/operations/assistant-intent";
import { rows, text, type Context, type Row } from "@/lib/operations/types";
import { canPrepare, readableDate } from "@/components/workspace/scope";
import { fieldValueLabel } from "@/components/workspace/proposal-form";
import { DecisionHistory } from "./decision-correction";
import { FindingPhotoGallery, findingPhotos } from "./finding-photos";
export function WorkEvidence({ workItemId, scenario }: { workItemId:string;scenario:string }) {
  const [context,setContext]=useState<Context|null>(null);
  const [error,setError]=useState(false);
  const refresh=useCallback(async()=>{try{const next=await api<Context>(`operations/context?scenario=${encodeURIComponent(scenario)}`);if(next.scenario!==scenario)throw Error();setContext(next);setError(false);}catch{setContext(null);setError(true);}},[scenario]);
  useEffect(()=>{let active=true;const run=()=>{if(active)void refresh();};const timer=setTimeout(run,0);window.addEventListener("daybreak:changed",run);return()=>{active=false;clearTimeout(timer);window.removeEventListener("daybreak:changed",run);};},[refresh]);
  const work=context?.work_items.find((item)=>item.work_item_id===workItemId);
  if(error)return <p className="mt-4 text-sm text-ink-soft">Field evidence and human history could not load. <button type="button" className="underline underline-offset-4" onClick={()=>void refresh()}>Retry</button></p>;
  if(!context||!work)return null;
  const corrections=rows(work.manual_corrections),findings=rows(work.findings);
  return <section aria-label="Field evidence and human decisions" className="mt-5 space-y-4">
    {canPrepare(context,"review_work_item")&&text((work.decision as Row|undefined)?.decision)!=="rejected_invalid"?<div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-rule bg-panel px-5 py-4"><div><p className="text-sm font-medium">{corrections.at(-1)?.is_correction===true?"Corrected by dispatcher":"Human oversight"}</p><p className="mt-1 text-xs text-ink-soft">Review the AI decision when field evidence or local knowledge changes the next step.</p></div><button type="button" className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-rule px-4 text-sm font-medium hover:bg-surface-2" onClick={()=>requestAssistantAction("review_work_item",{work_item_id:workItemId,decision:"defer",is_correction:true},scenario)}><UserRoundPen size={17}/>Correct AI decision</button></div>:null}
    {corrections.length?<DecisionHistory corrections={corrections}/>:null}
    {findings.length?<div className="rounded-xl border border-rule bg-panel p-5"><h2 className="mb-4 flex items-center gap-2 text-base font-semibold"><Camera size={18}/>Field findings</h2><div className="grid gap-4 md:grid-cols-2">{[...findings].reverse().map((finding,index)=><article key={text(finding.finding_id)||index} className="min-w-0 rounded-lg border border-rule bg-surface-2 p-4"><strong className="text-sm">{fieldValueLabel("outcome",finding.outcome)}</strong><p className="my-2 whitespace-pre-wrap text-sm leading-relaxed">{text(finding.note)}</p><FindingPhotoGallery photos={findingPhotos(finding.photos)} scenario={scenario}/><p className="mt-3 text-xs text-ink-soft">Technician · {text(finding.actor_id).slice(0,8)} · {readableDate(finding.created_at)}</p></article>)}</div><p className="mt-4 text-xs text-ink-soft">Findings record observed conditions. They do not confirm a repair or close a case.</p></div>:null}
  </section>;
}
