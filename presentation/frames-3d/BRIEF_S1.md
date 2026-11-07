# Addendum (17:05): Teo picked the painted miniature look, in 3D

Teo, after seeing all versions: "I like s1 (the miniature world), especially if it is
3D, with more shots and moving viewpoints, a dynamic film with After Effects-style
motion." So the look switches from the white model to the **painted miniature
diorama**. Keep the same procedural world you are building (village, depot, poles,
trucks, threads, cloud): same geometry, new materials and details. If the white-model
stills are already rendered, keep them; the painted miniature is now the priority.

References (AI images, for look only; beat them with real geometry and light):
`../frames-codex/v6/frames/s1_*_gemini.png` (warmest, best map ribbons) and
`../frames-codex/v6/frames/s1_*_codex.png`. World bible: section "s1" of
`../frames-codex/v6/REFINE.md`.

## Look: a handmade 1:87 diorama by a master model maker

- **Plinth:** the village sits on a round walnut-wood plinth with a bevelled edge
  (warm brown, satin finish, visible grain), on a plain seamless backdrop (warm cream
  #EFE6DA by default; pale blue-grey #C9D3DC for the storm).
- **Painted materials** (matte model paint, slightly imperfect, never glossy plastic):
  whitewashed walls #EEE8DD with a little grime at the base, terracotta tile roofs
  #B5523A (tile rows as geometry or a normal/bump pattern), dark green-brown window
  frames, grass as fine flock (Blender: short hair particles or dense instanced blades;
  Three.js: textured/instanced tufts), dirt road #9C8565, asphalt road #5D5A55,
  sunflower field (rows of tiny stalks with yellow #E8B32A heads), walnut trees as
  clumped foliage balls (#4E6B35 / #6C8A45), grey concrete poles with dark wires.
- **Life:** tiny workers in fluorescent orange hi-vis #FF5B1A with white hard hats
  (simple but well-proportioned figures, no faces needed), a dog, a cat on a roof,
  laundry on a line. Trucks: white bucket trucks with a thin orange stripe, no text.
- **Miniature camera:** real depth of field with a short focus distance (this is what
  sells the miniature): razor-sharp subject, soft foreground and background. Warm,
  happy studio light; per-beat moods as in BRIEF.md (overcast storm, warm low sun at
  dawn, with tiny warm window lights and truck headlights).
- **Map ribbons:** route threads become flat satin ribbons (~2–3 mm at model scale)
  laid along the roads, orange / cobalt / green, with tiny round map pins at the houses.

## More shots (Teo wants a dynamic film with many moving viewpoints)

Deliver the five beats from BRIEF.md in this look, plus at least three extra
viewpoints that a camera could move through:
- `street.png` — camera at 1:87 street level between houses, looking down the main
  road towards the depot (strong depth of field, very "inside the miniature").
- `crew_close.png` — close-up of a truck and three workers loading tools, macro.
- `top.png` — straight top-down of the whole plinth, the ribbons and pins reading as a
  map (great for a 2D/3D transition).
Name the files `s1_<beat>.png` (s1_storm, s1_where, s1_problems, s1_map, s1_dawn,
s1_street, s1_crew_close, s1_top) in your `stills/` folder.

## Motion test in the miniature look

Replace the motion test with `motion/s1_flythrough.mp4`: 8 s, 30 fps, 1920×1080.
One continuous camera move: start low at street level (s1_street), rise and arc over
the rooftops while the three ribbons draw themselves along the roads from the depot
and pins drop onto their houses, end on the map view (s1_map). Eased like a real
motion-control rig (slow-in, fast middle, slow-out), no wobble. If render time is a
problem, render at lower samples and say so; motion and look matter more than noise.
