import type { Metadata, Viewport } from "next";
import { Archivo } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import "./globals.css";

// Archivo, variabil pe lățime (62–125) și grosime: cifre late pentru panou, ore înguste pentru linia de timp.
// `latin-ext` aduce ș, ț, ă, â, î (verificat: ș/ț cu virgulă, U+0219/U+021B).
const archivo = Archivo({
  variable: "--font-sans",
  subsets: ["latin", "latin-ext"],
  axes: ["wdth"],
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
  themeColor: "#f2f3f1",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="ro" className={`${archivo.variable} h-full antialiased`}>
      <body className="min-h-full bg-canvas text-ink">
        <TooltipProvider delayDuration={250}>{children}</TooltipProvider>
        <Toaster position="bottom-right" />
      </body>
    </html>
  );
}
