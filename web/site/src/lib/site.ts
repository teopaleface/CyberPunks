import { Activity, Bot, CalendarClock, ScanSearch, type LucideIcon } from "lucide-react"

/** One place to rename the product before the pitch. */
export const SITE = {
  name: "Daybreak",
  fullName: "Daybreak",
  tagline: "Unde merg mâine echipele",
  /** One sentence for the footer and meta tags. */
  pitch: "Un agent care decide unde merg mâine echipele de teren Rețele Electrice și explică fiecare decizie.",
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
  { id: "plan", label: "Planul de mâine", href: "/plan", icon: CalendarClock },
  { id: "bilant", label: "Bilanț", href: "/bilant", icon: Activity },
  { id: "diagnostic", label: "Diagnostic", href: "/diagnostic", icon: ScanSearch },
  { id: "agent", label: "Agent", href: "/agent", icon: Bot },
]

export const ROUTES = {
  home: "/",
  signIn: "/intra",
  app: "/app",
}
