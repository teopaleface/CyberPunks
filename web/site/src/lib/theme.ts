import { useEffect, useState } from "react"

export type Theme = "dark" | "light"
const STORAGE_KEY = "daybreak-theme"

export function currentTheme(): Theme {
  return document.documentElement.classList.contains("light") ? "light" : "dark"
}

export function applyTheme(theme: Theme, persist = true) {
  const root = document.documentElement
  root.classList.remove("dark", "light")
  root.classList.add(theme)
  root.dataset.theme = theme
  root.style.colorScheme = theme
  document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme === "dark" ? "#000000" : "#ffffff")
  if (persist) {
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // The theme still works for this page when browser storage is blocked.
    }
  }
}

/** Follow the shared initializer and changes made by another Daybreak tab. */
export function useTheme() {
  const [theme, setTheme] = useState(currentTheme)

  useEffect(() => {
    const sync = () => setTheme(currentTheme())
    const observer = new MutationObserver(sync)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] })
    const onStorage = (event: StorageEvent) => {
      if (event.key !== STORAGE_KEY && event.key !== null) return
      applyTheme(event.newValue === "light" ? "light" : "dark", false)
    }
    const onPageShow = () => {
      try {
        applyTheme(localStorage.getItem(STORAGE_KEY) === "light" ? "light" : "dark", false)
      } catch {
        sync()
      }
    }
    window.addEventListener("storage", onStorage)
    window.addEventListener("pageshow", onPageShow)
    sync()
    return () => {
      observer.disconnect()
      window.removeEventListener("storage", onStorage)
      window.removeEventListener("pageshow", onPageShow)
    }
  }, [])

  return theme
}
