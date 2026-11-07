import type { Metadata, Viewport } from "next";
import { Geist, Unbounded } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

// Aceleași fonturi ca web/site: Geist pentru text, Unbounded pentru titlurile paginilor și numele produsului.
// `latin-ext` aduce ș, ț, ă, â, î cu virgulă.
const geist = Geist({
  variable: "--font-geist",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});
const unbounded = Unbounded({
  variable: "--font-unbounded",
  subsets: ["latin", "latin-ext"],
  weight: ["600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Daybreak",
    template: "%s, Daybreak",
  },
  description:
    "Plan field crew routes from meter faults, storm risks and voltage forecasts. Built by CyberPunks for SmartHack XI 2026.",
  applicationName: "Daybreak",
};

export const viewport: Viewport = {
  themeColor: "#000000",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geist.variable} ${unbounded.variable} dark h-full antialiased`}>
      <body className="min-h-full bg-canvas text-ink">
        <TooltipProvider delayDuration={250}>{children}</TooltipProvider>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
