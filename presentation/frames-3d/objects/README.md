# Daybreak miniature hero objects

Nine fully modelled props for the navy Daybreak launch film. All writes for this task are inside this `objects/` directory. No git commands or edits to the planet or film teams' directories.

## Deliverables

Each named directory contains `hero.png` at 1600 x 1600, a self-contained `scene.blend`, 72 spin PNGs at 1024 x 1024, 48 tumble PNGs at 1024 x 1024, and `manifest.json`. All PNGs are RGBA with a transparent background, no ground plane, no shadow catcher, and no text or logos.

`contact_navy.jpg` is a 2400 x 2400 composite on #000F1E. Read it left to right, top to bottom: truck, meter, pole, solar, hardhat, pin_orange, pin_cyan, pin_blue, cloud. The contact sheet is a visual catalogue. Its objects have independent product framing, not relative physical scale.

The root `manifest.json` indexes the per-object manifests. Pivots are the projected world origin, exactly [800, 800] for heroes and [512, 512] for sequences. Coordinates use a top-left image origin. Colour is display-referred sRGB with AgX already applied. Import PNGs as straight alpha. Do not apply AgX a second time.

## Models and materials

- Truck: inclined cab glazing, door seams, wipers, wing mirrors, real wheel cutouts, individually modelled tire tread, rim holes and nuts, service lockers, handles and hinges, folded Z boom, pivot caps, hydraulic ram and hoses, open bucket, steps, outriggers, amber beacons, road grime and small chips.
- Meter: lightly weathered grey case, perimeter gasket, blank dark LCD, terminal cover, screws, cable glands and curled feeds. A physical red horseshoe magnet has orange feet and exposed steel pole faces. No labels or display digits.
- Pole: fractured concrete fragment, exposed aggregate and reinforcing bars, galvanised crossarm and braces, two brown ceramic insulators, two broken overhead conductors with frayed strands.
- Solar: 60 chamfered blue wafers, fine conductor traces, subtle cell variation, anodised frame, back rails, junction box, cables and scattered dust. The front glass effect uses a coating on the wafers so the fine grid remains visible.
- Hardhat: thin orange shell, flared brim and visor, reinforcing ribs, accessory slots, inner headband and suspension, small abrasion marks.
- Pins: spherical lacquered heads in the three exact PPC base colours, steel collars, fine needles and sharp tips. Gloss is limited to these explicitly glossy pin heads, glazing and glazed ceramics.
- Cloud: a unified uneven wool core and 42,000 tapered curved filaments. No billboard image or generated image is used.

Materials are authored node shaders with noise for paint grain, roughness, dust and small wear. Geometry provides the visible seams, edges and fibres. The look follows the supplied miniature concept and navy styleframes.

## Render settings

Blender 5.2.1 LTS, Cycles on the Apple M5 Max Metal GPU. One Blender renderer at a time to share the GPU with the separate planet job. Six CPU threads for scene preparation. Profiling found CPU OIDN dominated the initial renders. All final heroes and sequences use GPU OIDN. The final pack was rerendered with perspective macro cameras after the orthographic drafts were reviewed. Three area lights: large warm upper-left key, cool back-right rim, and a gentle front fill. Low neutral-blue world fill. AgX, Medium High Contrast, exposure -0.25.

Heroes use 80 maximum samples, adaptive threshold 0.035, GPU OpenImageDenoise, and a 70 mm perspective macro camera with a 9-blade aperture. Geometry and studio distances are scaled by 1/87; bump distances, subsurface distances and light power are scaled consistently. The truck uses f/32, with focus on the front cab, and the other props use f/64 to keep small parts readable at these close distances. This gives gentle optical falloff without losing the front surfaces. Hero framing fits the actual projected geometry, with approximately 12 percent minimum padding.

Sequences use 24 maximum samples, threshold 0.065, OpenImageDenoise, persistent render data, and no depth of field. Maximum path length is 6 bounces, diffuse and glossy 3 each. Object silhouettes stay sharp enough to scale down over the film.

Spin is a fixed-camera 360-degree turn around world Z. Frame n has Z rotation 360*n/72 degrees. Frames 0 through 71 are one 2.4-second loop at 30 fps; do not append a duplicated endpoint. Frame 0 has the hero orientation, with wider sphere-safe framing.

Tumble uses animated 3D Euler rotations on multiple axes, with decreasing angular speed. For t = clamp(frame/47, 0, 1), q = (1-t)^2; XYZ rotations in radians are [2.4*pi*q, 1.6*pi*q, 2.7*pi*q]. Cycles shutter motion blur is enabled at 0.72 frames. This is rendered temporal blur, not a 2D blur filter. Frames -1 and 48-49 provide shutter-safe holds. Camera framing eases from sphere-safe framing to the hero framing over frames 28-47. Frame 47 lands at the hero orientation. Tumbles last 1.6 seconds at 30 fps and are not loops.

## Commands

Run from the repository root. These commands write only below `objects/`. The saved scenes are the authoritative sources for reproducing this delivered geometry, camera and wear. Rerender a hero from its scene with Blender after setting the output path; the hero render settings are saved in that scene.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 6 -P presentation/frames-3d/objects/render_sequences.py
python3 presentation/frames-3d/objects/package_objects.py
python3 presentation/frames-3d/objects/write_readme.py
```

The sequence renderer accepts object names after `--`, for example `-- truck meter`. It skips existing frames. Set `OBJECTS_FORCE_OBJECTS=truck,meter` to rerender those objects and replace their sequence frames. Move an old sequence directory aside before changing animation or settings; existing frames are not silently replaced.

To rebuild procedural geometry and heroes, use the authoring script. It resets the scene before each object. The random seed is fixed for the invocation, so the order of requested objects affects the placement of fine wear and wool fibres. All delivered scenes preserve the exact delivered geometry independently of rebuild order.

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b -t 6 -P presentation/frames-3d/objects/build_objects.py -- truck meter pole solar hardhat pin_orange pin_cyan pin_blue cloud
```

`build_objects.py` and `more_objects.py` contain all authoring code. `device_probe.py` checks Metal availability. `package_objects.py` decodes and checks every output, then writes the manifests, contact and `validation.json`. `timings.json` retains build and render measurements; `render_report.json` sums the last render of each delivered frame from the logs.

## Measured render times

The following are wall-clock seconds around Blender's render calls, including denoising, PNG writing and any first-frame Metal kernel compilation. They reflect contention with the other GPU job, not an isolated benchmark. Spin/tumble totals cover every delivered frame. Source modelling, visual review, cancelled in-progress frames and rejected drafts are excluded.

| Object | Hero, 80 samples | Spin, 72 frames | Tumble, 48 frames |
|---|---:|---:|---:|
| truck | 4.05 s | 17.32 s | 17.78 s |
| meter | 2.13 s | 18.30 s | 15.96 s |
| pole | 3.46 s | 21.60 s | 15.64 s |
| solar | 2.31 s | 18.32 s | 16.89 s |
| hardhat | 2.08 s | 17.75 s | 16.21 s |
| pin_orange | 2.38 s | 15.76 s | 11.74 s |
| pin_cyan | 1.39 s | 14.49 s | 11.60 s |
| pin_blue | 1.56 s | 17.12 s | 10.90 s |
| cloud | 2.54 s | 32.01 s | 18.55 s |

Total for the final 9 heroes and 1,080 sequence frames: 329.8 seconds, or 5.5 minutes. The log-based sequence render attempts total 1207.8 seconds, including the orthographic drafts, renderer restarts and initial CPU-denoised versions. This is the sum of completed render calls, not the full authoring-session duration. Individual times are in `render_report.json`.

## Review and limits

Truck and meter were built, rendered, inspected and corrected first. The meter's first framing clipped the case; the final framing preserves padding. A duplicated section in the magnet path was removed and hard bevel shading was softened. Additional review caught an opaque solar front layer, a pole texture stretched along its length, and overly regular cloud fibres; each was corrected before the final sequence rendering. The final review also replaced orthographic cameras with 70 mm perspective macro cameras, with focus tuned to preserve the cab and meter front.

The pack is detailed authored CGI, not a photographed physical model. The truck and meter carry the most convincing miniature detail. The pole fracture remains a simplified mesh. The helmet's abrasion is subtle. The cloud reads as a sculpted wool prop, with a visible underlying form; it does not fully match the loose cotton of the concept image. Sparse high-contrast details can soften under 24-sample denoising during fast tumbles. The perspective macro revision adds optical depth, but these isolated props still have less contextual realism than the complete photographed diorama. No claim is made that every frame is indistinguishable from a physical model.

`validation.json` records PNG decoding, exact dimensions, RGBA mode, nonempty alpha and edge clearance for every image. Selected front, side, back and tumble frames were also inspected visually. A completed file count does not by itself establish the photographic quality bar. Integration, scale, animation timing and readability in the finished film remain for the film compositor to verify.

## Licences and sources

No Poly Haven asset, HDRI, stock texture, downloaded model, font or image-generation output is embedded in the pack. All delivered geometry, procedural material graphs and render lights were authored for this task. There are no external asset URLs or third-party asset licences to clear. The two provided reference sheets were viewed for art direction only and are not copied into the assets. Blender and OpenImageDenoise are render tools, not included third-party artwork.
