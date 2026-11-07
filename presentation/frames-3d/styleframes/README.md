# Style frames v2: the target look of the 2D layer (18:30, 7 Nov)

Teo found the Milestone 1 stills "too simple, too basic, too weak" around the planet. These
seven frames are the new target for the 2D layer and the space around the planet. The planet
in them is the AI concept plate (`../../frames-codex/v7/concepts`, cut out with `cutout.py`);
in the film it is the 3D render (Blender) at the same quality.

Rebuild: `python3 presentation/frames-3d/styleframes/build.py` → `frames/*.png`, `sheet.jpg`.

## Rules the animated film must keep

- **Type:** Archivo, display `wdth 112 / wght 800 / tracking −0.035em`, headlines 150–330 px, set
  in a left column (x = 120). Small labels never below 30 px. Text never sits on top of the planet.
- **The night-shift clock** is a bezel around the planet (12 h dial: 22:00 → 06:00 track, a cyan
  progress arc that grows with time, a white moon marker that becomes the orange sun at dawn,
  the live time next to it). It ties the story together and is always moving.
- **Problems:** concentric ping rings in the source colour + elbow leader lines to big labels
  (orange / cyan / electric blue squares).
- **Crews:** solid pills in the route colours (white text, 30 px) tied to the trucks with a
  leader and a small ping.
- **Product:** big "Daybreak" wordmark + tagline, the console as a solid window (radius 30,
  soft shadow, 9° perspective tilt), orange "Plan tomorrow" button, flat map with rounded house
  footprints and the three routes with white-ringed stops, crew cards with route glyphs,
  oversized macOS cursor with click rings.
- **Ask:** close on the house, solid navy on the left third for the headline, solid card
  (#0E2238, radius 30), cyan Approve, leader + ping to the house.
- **Dawn:** a giant solid PPC-orange sun rising behind the planet's horizon (planet in front),
  "+49%" at 330 px, "Same crews. More value.", "30-day simulation", "06:00" with the orange dot.
- **End:** the planet has shrunk into the orange dot above "Daybreak".
- No glow, no glass, no gradient text: solid shapes and real light only. PPC palette:
  navy #000F1E family, orange #FA4616, cyan #00A3E0, electric blue #163FE8.
- Reuse the CSS and SVG helpers in `build.py` (`bezel()`, `ping()`, `leader()`, `chip()`,
  `CURSOR`, `click_rings()`), so film and style frames match exactly.
