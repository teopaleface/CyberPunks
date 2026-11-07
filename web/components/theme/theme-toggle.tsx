"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

/** Both labels render on the server; CSS selects the active state before hydration. */
export function ThemeToggle() {
  const { setTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={() => setTheme(document.documentElement.classList.contains("light") ? "dark" : "light")}
      className="flex min-h-11 w-full items-center justify-between gap-3 rounded-xl border border-rule bg-panel px-3 py-2 text-[14px] text-ink hover:bg-surface-2"
    >
      <span aria-hidden="true" className="flex items-center gap-2"><Sun size={18} /><span>Light</span></span>
      <span aria-hidden="true" className="relative h-5 w-9 rounded-full bg-track after:absolute after:top-0.5 after:left-0.5 after:size-4 after:rounded-full after:bg-ink after:transition-transform dark:after:translate-x-4" />
      <span aria-hidden="true" className="flex items-center gap-2"><Moon size={18} /><span>Dark</span></span>
      <span className="sr-only"><span className="dark:hidden">Light mode active. Switch to dark mode.</span><span className="hidden dark:inline">Dark mode active. Switch to light mode.</span></span>
    </button>
  );
}
