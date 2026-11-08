import { Moon, Sun } from "lucide-react"
import { applyTheme, currentTheme, useTheme } from "@/lib/theme"

export function ThemeToggle() {
  const theme = useTheme()
  const dark = theme === "dark"
  const Icon = dark ? Moon : Sun

  return (
    <button
      type="button"
      aria-label="Dark mode"
      aria-pressed={dark}
      title={`Switch to ${dark ? "light" : "dark"} mode`}
      onClick={() => applyTheme(currentTheme() === "dark" ? "light" : "dark")}
      className="site-glass inline-flex h-11 cursor-pointer items-center justify-center gap-2 rounded-full px-4 text-sm font-medium text-foreground ring-1 ring-foreground/15 hover:ring-foreground/40"
    >
      <Icon className="size-4" aria-hidden />
      <span>{dark ? "Dark" : "Light"}</span>
    </button>
  )
}
