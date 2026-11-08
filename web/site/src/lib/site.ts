import { Activity, Bot, CalendarClock, ScanSearch, type LucideIcon } from "lucide-react"

/** One place to rename the product before the pitch. */
export const SITE = {
  name: "Daybreak",
  fullName: "Daybreak",
  tagline: "Where crews go tomorrow",
  /** One sentence for the footer and meta tags. */
  pitch: "An agent that plans field work for Rețele Electrice and explains every decision.",
  team: "CyberPunks",
}

export interface NavItem {
  id: string
  label: string
  href: string
  icon: LucideIcon
}

/**
 * The navbar shows these same options on every page. Each one leads to a
 * page that presents one function of the product; the account button on
 * the right leads to the workspace, where the services live in a sidebar.
 */
export const NAV_ITEMS: NavItem[] = [
  { id: "plan", label: "Plan", href: "/plan", icon: CalendarClock },
  { id: "bilant", label: "Losses", href: "/bilant", icon: Activity },
  { id: "diagnostic", label: "Causes", href: "/diagnostic", icon: ScanSearch },
  { id: "agent", label: "Agent", href: "/agent", icon: Bot },
]

export const ROUTES = {
  home: "/",
  signIn: "/intra",
  app: "/app",
}
