---
name: technique-library
description: The library of proven motion-graphics techniques and shots every video draws from, plus the principles every video applies. Read it before writing brief.json; pick the set of techniques and shots for this film from it, and record the set in video.json.
---

# Technique library

Every film is built from techniques: a 3D voxel field, a particle flow, a kinetic word run, a morph, a wipe.
This library holds the ones that have proven themselves on screen. Each entry gives what it looks like, how
long it wants, how it was built, and where its working code is. They were grown from reference films the
operator chose, and more are added as new references arrive.

A brand gives a film its colours and fonts. Everything else (the shots, the techniques, the motion, the
layout) comes from here and from your own direction, and is yours to push as far as the film can take.

## How to use it

1. Read `principles.md`. It applies to every video.
2. Read the index below, then the entries that could carry this film's idea.
3. Pick the set: for a 20 to 25 s film, usually six to nine shot techniques, plus the transitions and texture
   that tie them together. Choose for the idea and for range: no two neighbouring shots from the same family, and
   at least one shot that only code can do (3D, particles, generative). `history.json` lists the sets used
   recently. Do not reuse the same set; a technique may come back with a new treatment.
4. Adapt each technique to this film: the brand's colours and fonts, this format (a 9:16 frame stacks
   vertically what a 16:9 frame spreads sideways), this message. An entry is a recipe, not a script: never copy
   another film's words.
5. Invent when the film needs it. A shot of your own is welcome. Name it in `brief.json` and add it to
   `techniques` in `video.json` under a new slug; good ones become entries.
6. Record it. Each shot in `brief.json` names its technique by slug. `video.json` carries `"techniques": [slugs]`
   for the set the film uses.

## Index

| Slug | Family | What it is | Wants |
|---|---|---|---|
| [dot-drop-flood](techniques/dot-drop-flood.md) | open, physics | a dot drops in perspective, squashes, rings out, stretches into a line, a wave, a band that floods the frame | 1.5-2.5 s |
| [wordmark-assemble](techniques/wordmark-assemble.md) | identity, type | letters drop centre-out with blur clearing, a serif phrase wipes under, a weight wave runs across | 1.3-2.5 s |
| [voxel-ripple-3d](techniques/voxel-ripple-3d.md) | 3D | a three.js voxel grid on a tilted camera, a ripple lifts it, a glossy sphere bounces, the camera orbits | 2-2.5 s |
| [kinetic-word-run](techniques/kinetic-word-run.md) | type | one word per beat, hard cuts, each word with its own field and its own motion (glide, slam, whip, cascade) | 1.7-2.5 s |
| [data-infographic](techniques/data-infographic.md) | data | a number rolls up, a donut fills, bars grow on a stagger, a spline draws with a travelling dot | 2-2.5 s |
| [particle-flow-sphere](techniques/particle-flow-sphere.md) | particles, generative | streaks ride a flow field, converge into a sphere, collapse into rings with readouts, burst | 1.5-2.5 s |
| [glass-ui-flow](techniques/glass-ui-flow.md) | interface | glass cards spring up on a radial field, a cursor works the controls, a button fills to Done, a toast slides in | 1.7-2.5 s |
| [metaball-morph](techniques/metaball-morph.md) | morph, shape | a metaball splits into blobs inside an outline that morphs circle, triangle, star, blob, then merges into a dot | 2-2.5 s |
| [end-card-decode](techniques/end-card-decode.md) | close, type | the dot pulses, the name decodes from a seeded scramble, a serif line, a hairline, the call to action | 1.7-3 s |
| [transitions](techniques/transitions.md) | transition | circle wipe, pixel-staircase wipe, band flood, dot-into-ground, whip, match cut; no crossfades | 0.2-0.5 s each |
| [through-line](techniques/through-line.md) | structure | one mark (a dot, a line) carries from scene to scene, so the cuts read as one continuous move | the whole film |
| [hud-frame](techniques/hud-frame.md) | frame | corner brackets, scene counter, section label, progress squares, a running timecode | the whole film |
| [grain-vignette](techniques/grain-vignette.md) | texture | seeded per-frame grain, a radial vignette per field, ghost outline type walls | the whole film |
| [master-clock](techniques/master-clock.md) | build pattern | one clock on the timeline drives every canvas and 3D scene as a pure function of time | the whole film |

## The worked example

`examples/reel-2026-10-06.html` is the composition of the first film built this way (a 15 s, 16:9 showreel
judged "a major improvement" by the operator on 2026-10-06). It uses every technique above. Each entry points to
its section there: search for the `<!-- S1 · ...` markup comment or the `// ===== S1 · ...` code comment. It
reads `assets/reel-kit.js` as `window.reel`; in your composition the same helpers are `window.kit` (also
`window.reel`), from `assets/motion-kit.js`.

## Growing the library

A new entry is written from a reference film the operator shares, studied shot by shot (contact sheet, cut
times, beat grid). It gives the technique a slug, says what it looks like and how long it wants, how to build it
in this stack, the sound under it, and its source. A technique the operator rejects is removed, not kept as a
warning.
