/**
 * Semnul „Tura de mâine”: un soare care răsare în spatele traseului unei echipe (conceptul A, desenat de
 * Codex, web/public/brand/logo-a.svg). Traseul folosește culoarea textului, ca să meargă pe orice fundal.
 */
export function LogoMark({ size = 24, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="9 10 46 46" aria-hidden="true" className={className}>
      <path fill="#F2A20C" d="M18 36a14 14 0 0 1 28 0Z" />
      <path
        d="M16 40h12l8-6h12"
        fill="none"
        stroke="currentColor"
        strokeWidth={5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <g fill="currentColor">
        <circle cx="16" cy="40" r="4" />
        <circle cx="36" cy="34" r="4" />
        <circle cx="48" cy="34" r="4" />
      </g>
    </svg>
  );
}

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={className}>
      <span className="flex items-center gap-2.5">
        <LogoMark size={26} />
        <span className="text-[21px] font-[650] tracking-[-0.005em] whitespace-nowrap">Tura de mâine</span>
      </span>
    </span>
  );
}
