/**
 * Numele produsului: Daybreak (decizia lui Teo, 7 nov., 15:30), scris ca pe site-ul de prezentare:
 * Unbounded, fără semn grafic.
 */
export const PRODUCT_NAME = "Daybreak";

export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={className}>
      <span className="font-display text-[19px] font-[700] tracking-[-0.02em] whitespace-nowrap" translate="no">
        {PRODUCT_NAME}
      </span>
    </span>
  );
}
