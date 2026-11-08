"use client";

import type { ReactNode } from "react";
import { Dialog, DialogContent, DialogDescription, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

/** Buton care deschide un dialog cu detaliile (tabelul întreg, ținut pe server și trecut ca `children`). */
export function DetailDialog({
  trigger,
  title,
  description,
  triggerClassName,
  children,
}: {
  trigger: ReactNode;
  title: string;
  description?: string;
  triggerClassName?: string;
  children: ReactNode;
}) {
  return (
    <Dialog>
      <DialogTrigger className={triggerClassName}>{trigger}</DialogTrigger>
      <DialogContent className="max-h-[85dvh] overflow-y-auto border border-rule bg-panel p-0 sm:max-w-[1100px]">
        <div className="px-6 pt-5">
          <DialogTitle className="text-[20px] font-[650]">{title}</DialogTitle>
          {description ? <DialogDescription className="mt-1 text-[15px] text-ink-soft">{description}</DialogDescription> : null}
        </div>
        {children}
      </DialogContent>
    </Dialog>
  );
}
