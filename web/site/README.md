# Bilanț pe post · site demo

Landing page pentru demo-ul SmartHack 2026 (Rețele Electrice / PPC).
Vite + React 19 + TypeScript + Tailwind 4, structură shadcn (`src/components/ui`, alias `@/`).

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # dist/
```

## Unde schimbi ce

| Ce | Unde |
| --- | --- |
| Numele produsului, opțiunile din navbar | `src/lib/site.ts` |
| Conturile (Supabase, proiect `bilant-pe-post`) | `.env.local` (vezi `.env.example`), `src/lib/auth.tsx` |
| Scroll-ul ecran cu ecran de pe landing | `src/components/section-snap.tsx` |
| Datele simulate (posturi, cauze, lei) | `src/data/posts.ts` |
| Animațiile respectă „reduce motion” din OS? | `src/lib/motion.ts` (`HONOR_REDUCED_MOTION`, oprit pentru demo) |
| Fundalul hero: shader propriu sau scena Unicorn Studio | `src/sections/hero.tsx` (`USE_UNICORN_SCENE`) |

## Componente

- `energy-beam.tsx`, `cobe-globe.tsx`: din 21st.dev, ca în brief.
- `energy-beam-shader.tsx`: beam-ul din hero, desenat ca în cadrul de referință
  (scena Unicorn `hRFfUymDGOHwtFe7evR2` arată acum o eclipsă).
- `liquid-glass-navbar.tsx`, `liquid-glass-button.tsx`, `liquid-glass-logo-reveal.tsx`,
  `halftone-wordmark-footer.tsx`, `tilted-grid.tsx`: refăcute după descrierile de pe 21st.dev
  (codul original e în spatele planului plătit).

Toate cifrele de pe pagină sunt simulare, nu date PPC.

## Pagini

`/` landing · `/bilant` · `/diagnostic` · `/clasament` · `/agent` · `/intra` (cont) · `/app` (serviciile, în sidebar).
Revizuirea anti-slop și excepțiile: `REVIEW.md`.
