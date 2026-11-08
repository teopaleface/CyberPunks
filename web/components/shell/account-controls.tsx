"use client";

import { useState } from "react";
import { LogOut, UserRound } from "lucide-react";
import { api } from "@/lib/operations/client";

export function AccountControls({ name }: { name: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function logout() {
    setBusy(true);
    setError("");
    try {
      await api("cont/iesire", {});
      window.location.assign(new URL("/intra", window.location.origin).href);
    } catch {
      setError("Sign out failed. Try again.");
      setBusy(false);
    }
  }
  return (
    <div className="space-y-1">
      <a href="/intra" className="flex min-h-11 items-center gap-3 rounded-xl px-3 text-[15px] text-ink-soft hover:bg-surface-2 hover:text-ink">
        <UserRound aria-hidden="true" size={20} strokeWidth={1.6} />
        <span className="truncate">{name}</span>
      </a>
      <button type="button" disabled={busy} onClick={() => void logout()} className="flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-[15px] text-ink-soft hover:bg-surface-2 hover:text-ink disabled:opacity-50">
        <LogOut aria-hidden="true" size={20} strokeWidth={1.6} />
        {busy ? "Signing out…" : "Sign out"}
      </button>
      {error ? <p role="alert" className="px-3 text-sm text-ink-soft">{error}</p> : null}
    </div>
  );
}
