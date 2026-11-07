# Daybreak: the white architectural model, built in real 3D

Date: 2026-11-07, Bucharest. For Teo (team lead).

## Why

Teo liked the "white architectural model" look (see the AI images in
`../frames-codex/v6/frames/g2_*_gemini.png` and `../frames-codex/v5/plates/g2_*.jpg`).
He wants it built for real in 3D, so the film can mix 2D motion (type, UI, overlays,
set in HyperFrames) with true 3D motion (camera moves through the model, trucks driving,
route threads drawing themselves along the streets). Two teams build it in parallel:
Blender (Cycles) and Three.js. Same world, same five keyframes, so we can compare.

A white architectural model is made of simple geometry; its beauty is light, shadow,
precision and restraint. That makes it ideal for procedural 3D: boxes, gable roofs,
cylinders, faceted trees, all in matte white, lit beautifully.

## World bible

A competition-grade architectural model, as built by the best architecture studios,
of a small flat village on the Banat plain in western Romania, plus a small utility
depot at its edge.
- **Materials:** matte white card and white 3D-printed resin. Base white #F3F1EC,
  roughness ~0.85, no visible texture except, at most, a hint of paper grain. Tiny
  bevels on edges (laser-cut crispness), perfect joints.
- **Village:** ~40–70 simple houses (rectangular footprint, pitched gable roof, a few
  with L-shaped plans, window recesses as shallow insets), arranged along a main road
  and 3–4 side streets on an irregular rural grid; fences as hair-thin strips;
  faceted low-poly white trees (walnut-like, rounded); a field area with fine parallel
  grooves (sunflower field, still white); concrete utility poles as thin white
  cylinders with a crossarm, connected by hair-thin dark-grey wires (the only non-white
  neutral); streets slightly recessed (0.5–1 mm at model scale) so they read as lines.
- **Depot:** a small white yard with a shed, at the village edge on the main road.
- **Colour, only where it matters:** crew trucks fluorescent orange #FF5B1A (simple but
  precise bucket-truck shape: cab, bed, folded boom); route threads and pin heads in
  orange #FF5B1A, cobalt #1E4FD8 and green #1FA35B; a felt storm cloud in warm mid-grey
  #8E8C88; nothing else coloured.
- **Table and backdrop:** a plain pale warm-grey table and seamless backdrop
  (#E7E3DC), the model sits on a thin white base board with a crisp edge.
- **Look:** Apple-level product photography of a real model. Big soft key light, deep
  clean contact shadows and ambient occlusion in every corner, crisp focus on the
  subject with a gentle shallow depth of field, physically plausible exposure, AgX or
  ACES-like filmic tone mapping. Calm, precise, luxurious.
- **Bans:** no purple/pink, no neon, no bloom/glow, no lens flare, no text, letters,
  digits or logos anywhere, no toy/plastic shine, no grey-on-grey mud (the model must
  read as bright white with clean shadows), no visible lamps, rigs or cables.

Build the world deterministically (fixed seed), so every render is identical and the
keyframes are views of one single scene.

## The five keyframes (16:9, 1920×1080; headline added later in code, never render text)

1. **storm** — cool overcast light (large soft key, cool white ~6500K, low contrast).
   Low camera at village eye level, close. A large felt storm cloud (soft lumpy cluster
   of spheres with fine noise) hangs above the village on an almost invisible thin wire;
   rain as many fine clear/very-light rods; one pole snapped and lying across the main
   road with wires down; one orange truck stopped beside it. Village in the lower right;
   keep the top-left 45% plain (backdrop).
2. **where** — the depot, camera about 35° above and close: five orange bucket trucks
   parked at slight angles in the yard, large and crisp in frame; low warm side light,
   long soft shadows. Depot in the lower 55%; top 45% plain.
3. **problems** — three white square plinths side by side on the table, each a small
   vignette: (1) a snapped pole with wires down; (2) a house wall with a small meter box
   and an orange horseshoe magnet on it; (3) a roof with dark blue solar panels (#1C2A4A,
   slightly glossy) and a small polished brass sphere on a thin rod above it as the sun.
   Plinths in the upper 75%; bottom 22% plain table.
4. **map** — the whole village from ~60° above, low warm morning sun from the right,
   long shadows. From the depot three bold threads (orange, cobalt, green) run along the
   streets, each to 3–4 houses marked by round map pins with coloured heads; a small
   orange truck at the start of each thread. Threads thick enough to read instantly.
   Model in the lower 65%; top 35% plain.
5. **dawn** — low warm sunrise light (~3000K) raking from the right, long golden
   shadows across the white village; the five orange trucks driving out in a line along
   the main road. Low three-quarter camera. Model in the lower 50%; top 50% plain.

## Motion test (proves the 3D is worth it)

One clip of 6 seconds, 30 fps, 1920×1080, of the **map** beat: the camera slowly moves
from the "where" depot view up to the "map" view while the three threads draw
themselves along the streets from the depot, pins drop onto their houses as each thread
reaches them, and the three trucks start moving along their threads. Smooth eased
motion, no wobble. H.264 MP4, yuv420p.

## Deliverables (each team in its own folder only)

- `stills/storm.png`, `where.png`, `problems.png`, `map.png`, `dawn.png` — 1920×1080, text-free.
- `stills/contact_sheet.jpg` — the five in order.
- `motion/map_test.mp4` — the 6 s motion test.
- The source that rebuilds everything from scratch, plus `README.md` with the exact
  commands, render settings and the measured render time per still and per frame.
