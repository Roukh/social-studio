---
name: reel-look
description: The look of this preset - a 15 s motion-designer showreel in the grammar of the 2026 Opus showreels - palette roles, type roles, the HUD frame, texture, shot grammar, transitions, the sound grid and the open and close. Read before planning any shot.
---

# Reel look

This is the house look for the reel preset, studied from the strongest 15-second code-made showreels of September 2026. It describes a grammar. Never copy another reel's words, logos or characters. Every word, number and interface in our film is our own, and every chart, metric and UI is a labelled fictional sample.

## The film in one line

Show what an incredible motion designer this studio is, like a résumé reel. Put a new technique on screen roughly every 1.5 to 2 seconds, put every cut on the music, and spend effort on every frame.

## Palette roles

All colours come from `preset.json` as CSS variables.
- `--ink` #070711 is the default ground: near-black, faintly blue.
- `--signal` #FD4920 is the one constant accent. Use it for the dot, the active progress square, the last bar, the italic payoff on a flood and the wipe colour. It is never body text on a dark ground below 40 px.
- `--cream` #F0EFE6 is the light ground, and the type colour on ink.
- `--blue` #2E49F0 is for lines, the spline, a radial field (`--blue-deep` at the edge) and the dot under a burst.

Each scene owns one full-bleed field, and the fields rotate: ink, signal flood, ink, then cream or blue for one-word beats, cream, ink, blue, signal, and ink at the end. Never put two cream scenes back to back.

## Type roles

- **Reel Sans** (variable, 100-900) is for display, titles and numbers. Use heavy weights (800-900) and tight tracking (-0.04em to -0.06em). Animate `font-weight` or `font-variation-settings: "wght"` as a wave across the letters: the weight is a motion channel, not a static choice.
- **Reel Serif** italic is for one emotional phrase per scene, set under or after a heavy word ("motion designer", "on purpose." style beats). It never carries numbers.
- **Reel Mono** (variable) is for every label, axis, readout and the HUD. Set it uppercase with wide tracking (+0.18em to +0.3em), at 18-24 px in 1080p.

## HUD frame (present on every scene)

- Corner bracket marks, 1-2 px, about 2 % in from each corner.
- Top left: a small signal dot, then a mono label with the studio name and "motion reel" plus the year.
- Top right: "SCENE 0N / 0M" in mono, with the current number bright and the rest dim.
- Bottom left: the scene's section name in mono, e.g. "KINETIC TYPOGRAPHY" or "DATA / INFOGRAPHICS".
- Bottom right: progress squares (the current one signal) and a running SMPTE timecode (`reel.timecode(t, 60)`).
- HUD text sits about 4 % from the edges. It is texture: it may be smaller than reading text. It changes colour with the field: cream on ink, ink on cream.

## Texture

Fine film grain over everything, at 3-6 % opacity, animated by a seeded offset per frame. A radial vignette on every flat field. A soft glow (box-shadow or a blurred duplicate) only on the signal dot. Ghost outline type (1 px stroke, 6-10 % opacity) as background walls behind kinetic words.

## Shot grammar (15 s, 60 fps, ~143 BPM: beat 0.42 s, sixteenth 0.105 s)

1. **Open (0-1.6 s).** A dot-grid on ink. A signal dot drops in and squashes on a sub thump. A mono caption types. The dot stretches into a line, then a travelling sine wave on a riser. The line thickens into a band that floods the frame signal-orange on the downbeat.
2. **Identity (about 1.6 s).** The wordmark drops in letter by letter with a blur that clears. An italic serif phrase slides under it, a mono kicker sets in, and a weight wave runs across the letters. Leave on a blurred circle wipe.
3. **3D (about 1.6 s).** A Three.js voxel grid on a tilted camera. A ripple lifts the blocks in a signal-to-violet gradient, a chrome or glossy sphere with an orbit ring bounces at the centre, and the camera orbits slowly. Render it from `hf-seek` time; seeded heights only.
4. **Kinetic words (about 1.5 s).** One word per beat: four hard cuts, each with its own field and treatment. Use dark on cream, signal on ink over an outline-word wall, cream on blue skewed with motion blur inside viewfinder brackets, and an italic phrase on signal. These are the only hard cuts in the film.
5. **Data (about 1.7 s).** On cream: a big percentage rolls up with blurred digits, a donut fills to its value, 12 bars grow on a stagger with the last bar in signal, and a blue spline draws with a travelling dot and a value pill. Every number is a labelled sample. Leave on a staircase pixel-block wipe.
6. **Particles (about 1.5 s).** A flow field of white, signal and blue streaks converges into a sphere of sticks, collapses into concentric dotted rings with x/y readouts, then bursts radially around a blue dot.
7. **UI (about 1.5 s).** A blue radial field with a dot grid and glass cards stacking. A render-queue card springs up and a cursor flips a toggle and picks an option. A button becomes a signal progress fill and then "Done", and a toast slides in. Leave on a soft-edged signal circle wipe from the centre.
8. **Morph (about 1.7 s).** A metaball splits into 8 blobs inside a thin cream outline. The outline morphs circle, triangle, star, blob, and the blobs merge back into one dot that grows into a wipe to ink.
9. **End card (about 1.8 s).** The signal dot pulses with a glow ring. The wordmark decodes in with a seeded letter scramble, followed by the italic serif line, a hairline, the tagline in signal mono and a small credit line ("made in code" style). The audio fades out.

Shot lengths follow the music, not a template: shorten or merge scenes when the bed calls for it. You may swap a technique for a stronger one. Keep the rhythm of one new idea per bar.

## Transitions

Use spatial transitions: a circle wipe (hard or blurred edge), a staircase pixel-block wipe, a band flood, a dot that grows into the next ground, a morph, and a whip with motion blur. Use no crossfades. Hard cuts belong only to the kinetic-word run. Every scene change lands on a beat from the grid, and the big ones land on downbeats.

## Motion

- Use springs (`reel.spring`, `reel.track`) or `power3`/`expo` eases, never linear except for continuous drift.
- Fast moves get blur. Use the velocity blur helper in `skills/music-to-video/references/templates/logo-split-lockup-pulse/index.html` (`attachMotionBlur`), or a `filter: blur()` that grows with speed along the move.
- Overlap the moves: the next element starts while the last one is settling. Avoid uniform staggers: vary them by 10-30 %.

## Sound

Use a synthesized bed plus effects, and no voice: `node tools/sound.mjs`.
- Start with a sub thump on the dot drop, then a riser into the flood hit.
- Put ticks on the 16th grid under the type, whooshes into each wipe, blips under the data and UI moves, glitches on the pixel wipe and a swell into the end card.
- Fade the bed out over the last 1.5 s.

Write the cue sheet from the shot list, so every scene change has a sound.
