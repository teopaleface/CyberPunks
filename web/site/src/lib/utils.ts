import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Romanian number formatting: 1.234,5 */
export const fmt = (n: number, digits = 0) =>
  new Intl.NumberFormat("ro-RO", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(n)

export const lei = (n: number) => `${fmt(Math.round(n))} lei`
