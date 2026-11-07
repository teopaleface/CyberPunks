/**
 * Numele produsului: Daybreak (decizia lui Teo, 7 nov., 15:30). Identitatea grafică (semn, culori) se
 * alege separat; până atunci antetul arată doar cuvântul, scris cu fontul interfeței, fără semn grafic.
 */
export const PRODUCT_NAME = "Daybreak";

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={className}>
      <span className="text-[22px] font-[680] tracking-[-0.015em] whitespace-nowrap" translate="no">
        {PRODUCT_NAME}
      </span>
    </span>
  );
}
