import type { Metadata, Viewport } from "next";
import { Geist, Unbounded } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

// Aceleași fonturi ca site-ul de prezentare (web/site): Geist pentru text, Unbounded pentru numele produsului.
// `latin-ext` aduce ș, ț, ă, â, î cu virgulă.
const geist = Geist({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});
const unbounded = Unbounded({
  variable: "--font-display",
  subsets: ["latin", "latin-ext"],
  weight: ["600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Daybreak, consola dispecerului",
    template: "%s, Daybreak",
  },
  description:
    "Agentul care decide unde merg mâine echipele de teren Rețele Electrice, din trei modele ML antrenate de echipa CyberPunks (SmartHack XI 2026, tema PPC).",
  applicationName: "Daybreak",
};

export const viewport: Viewport = {
  themeColor: "#000c1e",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ro" className={`${geist.variable} ${unbounded.variable} dark h-full antialiased`}>
      <body className="min-h-full bg-canvas text-ink">
        <TooltipProvider delayDuration={250}>{children}</TooltipProvider>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
