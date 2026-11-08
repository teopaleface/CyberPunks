/**
 * Text care se aprinde cuvânt cu cuvânt pe măsură ce derulezi (ca pe paginile de produs Apple).
 * Doar marcajul; comportamentul e în components/enhance.tsx (merge și de pe disc, fără hidratare).
 * Fără JS sau cu prefers-reduced-motion, textul e aprins de la început.
 */
export function ScrollWords({ text, className }: { text: string; className?: string }) {
  const words = text.split(" ");
  return (
    <p data-scroll-words className={className}>
      {words.map((w, i) => (
        <span key={i} data-w className="transition-opacity duration-150 ease-out">
          {w}
          {i < words.length - 1 ? " " : ""}
        </span>
      ))}
    </p>
  );
}
