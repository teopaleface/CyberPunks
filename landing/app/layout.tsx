import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import { Enhance } from "@/components/enhance";
import "./globals.css";

/*
 * Fontul: pe Mac și iPhone, fontul sistemului (SF Pro, cu dimensiuni optice), ca în stilul Apple cerut
 * de Teo (17:55). Pe celelalte sisteme, Inter (OFL), cel mai apropiat font liber de SF Pro.
 * Inter nu se preîncarcă: pe Mac nu se descarcă deloc. Diacriticele ș/ț (virgulă dedesubt) sunt
 * verificate în ambele (numele „Rețele Electrice” apare pe pagină).
 */
const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
  display: "swap",
  preload: false,
  axes: ["opsz"],
});

export const metadata: Metadata = {
  title: "Daybreak: tomorrow’s crews, planned tonight",
  description:
    "An AI agent that decides every evening where the Rețele Electrice field crews go the next morning. A CyberPunks project for SmartHack XI 2026, PPC track. Not an official PPC product.",
};

export const viewport: Viewport = {
  themeColor: "#000f1e",
  colorScheme: "dark",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={inter.variable}>
      <body>
        {children}
        <Enhance />
      </body>
    </html>
  );
}
