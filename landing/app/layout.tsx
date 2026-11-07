import type { Metadata, Viewport } from "next";
import { Figtree } from "next/font/google";
import "./globals.css";

/*
 * Fontul: Figtree (OFL), ales ca alternativă liberă la PingLCG, fontul proprietar PPC.
 * Verificat în fișierele woff2: ș, ț, Ș, Ț cu virgulă (U+0219, U+021B, U+0218, U+021A) în
 * subsetul latin-ext, ă, â, î în latin; cifre tabulare (tnum).
 */
const figtree = Figtree({
  subsets: ["latin", "latin-ext"],
  variable: "--font-figtree",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Daybreak: echipele de mâine, planificate în seara asta",
  description:
    "Agentul care decide în fiecare seară unde merg mâine echipele de teren Rețele Electrice. Proiect CyberPunks pentru SmartHack XI 2026, tema PPC. Nu este un produs oficial PPC.",
};

export const viewport: Viewport = {
  themeColor: "#000f1e",
  colorScheme: "dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ro" className={figtree.variable}>
      <body>{children}</body>
    </html>
  );
}
