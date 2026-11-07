import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

// Inter (designul „Noapte”): grotesc geometric, cifre clare; `latin-ext` aduce ș, ț, ă, â, î cu virgulă.
const inter = Inter({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
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
    <html lang="ro" className={`${inter.variable} dark h-full antialiased`}>
      <body className="min-h-full bg-canvas text-ink">
        <TooltipProvider delayDuration={250}>{children}</TooltipProvider>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
