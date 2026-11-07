/** Semnele „cine a decis”: agentul (un cip) și omul (o siluetă). Culoarea vine din text. */
export function AgentGlyph({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" className="shrink-0">
      <rect x="3.25" y="3.25" width="9.5" height="9.5" rx="1.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <rect x="6.25" y="6.25" width="3.5" height="3.5" fill="currentColor" />
      <path d="M6 .8v2M10 .8v2M6 13.2v2M10 13.2v2M.8 6h2M.8 10h2M13.2 6h2M13.2 10h2" stroke="currentColor" strokeWidth="1.3" />
    </svg>
  );
}

export function HumanGlyph({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" aria-hidden="true" className="shrink-0">
      <circle cx="8" cy="4.8" r="3.1" fill="currentColor" />
      <path d="M2.2 15.2c0-3.4 2.6-5.7 5.8-5.7s5.8 2.3 5.8 5.7z" fill="currentColor" />
    </svg>
  );
}
