# Daybreak film: premium 3D hero objects for the 2D motion layer

18:30, 7 Nov. Teo: the 2D motion must be "mega premium", like the reference film (a Trust
Wallet launch replica, analysed in `presentation/research/REFERINTA-trust.md`): 3D objects fly
in around the key words at different depths with motion blur, then shrink and land exactly on
the product UI ("the object becomes the world"). Our film needs its own hero objects for that.

## Look (must match the planet)

- The same painted 1:87 miniature world as the planet (`BRIEF_S1.md`, `FILM_SPEC.md` §7, bar:
  `../frames-codex/v7/concepts/concept_sheet.jpg`): props made by a master model maker,
  photographed. Real materials with slight wear (CC0 PBR textures from Poly Haven where useful),
  tiny bevels, nothing perfectly clean, nothing plastic-shiny.
- Light for a navy film (#000F1E): a large warm softbox key from top-left, a cool thin rim from
  back-right so every edge separates from navy, gentle fill. AgX, denoise.
- Transparent background (RGBA PNG). No ground, no shadow catcher (they fly), except where noted.
- PPC accents only on real parts: orange #FA4616, cyan #00A3E0, electric blue #163FE8.
- No text, letters, digits or logos anywhere.

## Objects

1. `truck` — white utility bucket truck, thin orange stripe along the side, folded boom, black
   tyres, slightly weathered (mud on the lower panels).
2. `meter` — a residential electricity meter in a light-grey box, blank dark display, with a
   strong red-and-orange horseshoe magnet stuck on its front (meter tampering).
3. `pole` — the top of a snapped concrete utility pole with a crossarm, two brown ceramic
   insulators and two broken wire ends.
4. `solar` — a residential solar panel (dark blue cells, silver frame), a tiny bit dusty.
5. `hardhat` — a safety helmet in PPC orange, scuffed.
6. `pin` — a map pin (round glossy head on a thin steel needle) in three colours:
   `pin_orange`, `pin_cyan`, `pin_blue`.
7. `cloud` — a cotton-wool storm cloud, grey, fibrous edges (the same cloud as the planet).

## Deliverables per object (in `presentation/frames-3d/objects/<name>/`)

- `hero.png` — 1600×1600, three-quarter view, centred, ~12% padding.
- `spin/0000.png … 0071.png` — 1024×1024, one full 360° turn on the vertical axis (72 frames,
  loops at 30 fps), same light.
- `tumble/0000.png … 0047.png` — 1024×1024, a fast tumble on two axes with real motion blur
  (for fly-ins), ending on the hero angle at frame 47.
- `manifest.json` — frame counts, pixel size, pivot (in px) and the hero angle frame.
- One `contact_navy.jpg` with all objects on #000F1E, to check how they read in the film.

## Bar

Every object must look like a photographed handmade miniature prop, at the quality of the
concept sheet. Review each hero hard before moving on (would a photo editor believe it is a
real model?). Keep renders practical: the GPU is shared with the planet render; use moderate
samples + denoise for spins/tumbles, more for heroes. Record timings and asset licences in
`objects/README.md`.
