---
name: motion-canon
description: Working method and principle checklist for building premium-feeling motion-graphics videos in code (HTML/CSS + paused GSAP timeline, optional Three.js, frame-by-frame render). Use when planning, animating, or critiquing a HyperFrames-style motion-graphics composition — beat-synced social videos, title sequences, launch films, kinetic typography, data-viz beats, 3D/voxel shots, transitions, or sound design on a timeline. Draws on the non-AI motion-design canon (Disney's 12 principles, Material/Carbon/Apple motion tokens, broadcast editing grammar, sound-for-picture practice).
---

# Motion Canon

A working method for building 10–30s motion-graphics videos as paused-GSAP-timeline compositions, plus the numbers that separate premium motion from template motion. Defaults below are starting points with a stated reason — break them deliberately, not by accident.

## Working method

1. **Study.** Before building, name 2-3 reference pieces (see `references/study-list.md`) whose techniques match the brief. Identify the *one thing* each beat is teaching the viewer — a technique shown without a reason to look at it is decoration.
2. **Plan beats on a grid.** Convert the track's BPM to a cut grid: `secPerBeat = 60 / BPM`. At 143 BPM that's ~0.42s/beat, or ~0.21s on the half-beat. Write the full video as a beat sheet: `[0.00–1.63s: beat 1 — hook]`, `[1.63–3.26s: beat 2 — technique]`, etc. Pick cut points *on* that grid, then deliberately skip a beat here and there — perfectly uniform per-beat cuts read as mechanical (see `references/transitions-and-editing.md`).
3. **Key poses first.** For every beat, define the hold frame (the "in" pose, fully legible, nothing moving) before animating the transition into and out of it. If the hold frame doesn't work as a still screenshot, the beat has no idea in it yet.
4. **Motion.** Animate between key poses. Every frame is rendered one at a time, so runtime performance does not limit you: animate `font-weight`, `clip-path`, filters, SVG paths or canvas when the look needs them. Pick an easing curve by *why the thing is moving*, not by habit (`references/easing-and-timing.md`). Stagger children instead of moving them in unison.
5. **Sound.** Write the cue sheet from the shot list. Every hit, whoosh and riser lands on the beat grid at its visual cue. Build the soundtrack with `tools/sound.mjs`, or place `<audio>` files on the same timeline (`references/sound-for-motion.md`).
6. **Critique.** Render a draft, then judge the sampler's strips (one move, frame by frame) and its settled frames. Run the checklist below and `references/critique-checklist.md` before calling a beat done.

## Principle checklist (with numbers)

**Timing, in frames.** At 30fps / 60fps: a UI-scale micro-motion is 8–20f / 16–40f (0.25–0.67s, Apple HIG's 0.25–1.0s range (developer.apple.com/design/human-interface-guidelines)); a broadcast-scale hero move is 20–45f / 40–90f (0.67–1.5s). Kinetic type in a fast reel holds one beat per word, 0.33-0.45 s (10-14f / 20-27f), because the beat carries it and each word is a single shape. A line the viewer must *read* as a sentence holds about 0.5 s plus 0.25 s per word. A key message the viewer must remember holds 2-3 s. Pick by the job the words are doing.

**Easing, as GSAP strings.** Entrances/reveals: `"power2.out"` (default — decelerates into rest, reads as arriving under its own weight) or `"power3.out"` for a snappier arrival. Exits/dismissals: `"power2.in"`. Elements that pass through (not stopping): `"none"` (linear) is *correct* here, not cheap — reserve the "linear reads cheap" rule for things that start or stop on screen. Overshoot/bounce accents: `"back.out(1.7)"`. Springy UI (cards, cursor, progress fill): a spring ease (stiffness 300–400, damping 20–25 for snappy-but-controlled; stiffness 100–200, damping 10–15 for playful/bouncy). Never default every tween to the same ease — vary it per element class, that variation *is* the "ease in/out" and "secondary action" principles from Disney's 12.

**Stagger.** Default `stagger: {each: 0.04-0.08, from: "start"}` for reading-order reveals (text, list items); `{each: 0.02-0.05, from: "center", grid: "auto"}` for a 2D wave (variable-font weight wave, voxel ripple, card grid). Larger `each` (0.1-0.15s) reads as deliberate/dramatic; smaller (<0.03s) reads as a single soft-edged event.

**Cut length vs. BPM.** `cutsPerBeat = 60 / (BPM / beatMultiple)`. At 143 BPM one beat is about 0.42 s (25f at 60 fps). A strong 15 s showreel changes scene about every 4 beats (about 1.6 s). It cuts on every beat only in a short kinetic run, and sync points for effects fall on the half-beat grid (about 0.21 s). Don't cut on every beat for 15 s straight: hold a beat 2-4× longer at the midpoint and at the end, to give the eye a landing spot.

**Hold lengths.** A pure data/number beat (counter roll-up, donut fill) needs ≥0.8-1.2s of settled, non-moving read time before the next cut, even inside a fast-cut piece — the number must be legible, not just present.

**Motion blur / shutter.** Simulate 180°-shutter blur on fast moves with a short multi-copy trail or a CSS `filter: blur()` ramped up only during the high-velocity portion of the move (not statically) — 1-3px blur at 60fps for a 200-400px/s move is a reasonable start. Skip blur entirely on UI-card and HUD elements; blur there reads as bugs, not cinema.

**Stagger/grid for HUD + typography.** Corner brackets and SMPTE-style counters update per-frame with no easing (`ease: "none"`, duration = 1 frame) — HUD readouts that ease read as decorative, not functional.

**Sound sync tolerance.** Place hit/whoosh markers within ±1 frame (60fps) / ±2 frames (30fps) of the visual impact frame — looser than that and the hit reads as late. Risers should resolve *into* the hit, not stop just before it.

**Loudness.** Mix dialogue/music bed to roughly -14 LUFS integrated for social delivery; don't rely on the platform's normalizer to fix an overly hot or quiet mix.

## Tells of cheap motion — hunt these in critique

- Every element eases with the same curve (usually default linear or a single power2) regardless of what kind of motion it is.
- Every element has the same duration regardless of size, distance traveled, or role.
- "Fade" is the only transition verb used anywhere in the piece.
- Subject sits dead-center on a gradient with no off-center staging, no foreground/midground/background separation.
- A particle system or glow is present but not motivated by anything the content is saying.
- Grain/vignette/chromatic-aberration applied uniformly and statically rather than driven by the moment (e.g. a glitch beat, an impact frame).
- A HUD/counter element that eases instead of snapping — breaks the "this is live data" illusion.
- Kinetic type holds every word for the exact same duration regardless of word length or importance.
- Cuts land exactly on every single beat for the whole piece with no variation in hold length.

## References

- `references/easing-and-timing.md` — GSAP ease catalog, spring configs, duration tables by context.
- `references/typography-in-motion.md` — kinetic type rules, variable-font weight-wave recipe.
- `references/transitions-and-editing.md` — cut grammar, BPM-to-frame math, wipe/morph techniques in code.
- `references/sound-for-motion.md` — hit/whoosh/riser placement, sync tolerance, loudness targets.
- `references/3d-and-camera.md` — Three.js camera language, voxel/particle/metaball recipes.
- `references/critique-checklist.md` — the full frame-freeze critique pass.
- `references/study-list.md` — the 20 landmark pieces and what to take from each.
