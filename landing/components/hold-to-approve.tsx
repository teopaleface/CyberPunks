/**
 * „Ține apăsat ca să aprobi”: aprobarea unui om nu se dă dintr-un clic scăpat. Umplerea merge liniar
 * cât ții apăsat (mouse, deget, Space sau Enter) și se retrage repede dacă dai drumul. Doar marcajul;
 * comportamentul e în components/enhance.tsx. Pe pagină nu se trimite nimic, iar „Undo” readuce cazul.
 */
export function HoldToApprove() {
  return (
    <div data-hold-root>
      <div data-controls className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          data-hold
          aria-label="Hold to approve"
          className="group relative h-12 touch-none overflow-hidden rounded-full bg-tile-2 px-6 text-[1.02rem] font-medium text-ink transition-transform duration-150 ease-out select-none active:scale-[0.97]"
        >
          <span>Hold to approve</span>
          <span
            aria-hidden
            className="absolute inset-0 flex items-center justify-center bg-ppc-blue text-night transition-[clip-path] duration-200 ease-out [clip-path:inset(0_100%_0_0)] group-data-[holding]:[clip-path:inset(0_0_0_0)] group-data-[holding]:duration-[1200ms] group-data-[holding]:ease-linear"
          >
            Hold to approve
          </span>
        </button>
        <button
          type="button"
          data-skip
          className="h-12 rounded-full px-5 text-[1.02rem] text-ink-2 transition-colors duration-150 hover:bg-tile-2 hover:text-ink"
        >
          Skip
        </button>
      </div>
      <div data-status hidden className="flex flex-wrap items-center justify-between gap-3" role="status">
        <p className="flex items-center gap-2 text-[1rem] text-ink">
          <span
            aria-hidden
            data-status-icon
            className="grid size-6 place-items-center rounded-full bg-tile-2 text-ink-2 data-[kind=approved]:bg-ppc-blue data-[kind=approved]:text-night"
          />
          <span data-status-text />
        </p>
        <button type="button" data-undo className="rounded-full px-3 py-1.5 text-[0.92rem] text-ppc-blue transition-colors hover:bg-tile-2">
          Undo
        </button>
      </div>
    </div>
  );
}
