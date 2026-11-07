"use client";

import { ThemeProvider as NextThemeProvider, useTheme } from "next-themes";
import { useEffect, type ReactNode } from "react";

function BrowserTheme() {
  const { resolvedTheme } = useTheme();
  useEffect(() => {
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", resolvedTheme === "light" ? "#ffffff" : "#000000");
  }, [resolvedTheme]);
  return null;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemeProvider attribute={["class", "data-theme"]} storageKey="daybreak-theme" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
      <BrowserTheme />
      {children}
    </NextThemeProvider>
  );
}
