# particle-flow-comet

**Family:** particles, generative. **Wants:** 2-2.5 s. **Source:** Himanshu's 15 s showreel
(x.com/himanshutwtxs/status/2103495232637882858), studied 2026-10-07.

## Looks

A dark, dotted field with a faint vector-flow pattern behind it. A comet of coloured dots traces a looping
path through it (a figure-8 reads well), its tail tapering in size and opacity, labelled with the idea it
carries.

## Build

- A 2D canvas, or three.js points, drawn from the master clock.
- The comet's head follows a parametric loop, such as `x = A sin(t)` and `y = B sin(2t)` for a figure-8.
- The tail is the head's position at the last N times, each point smaller and fainter.
- The flow field is short strokes along a seeded vector field, at low opacity.

## Sound

A riser under the loop.

## Adapting

A lighter alternative to `particle-flow-sphere.md` when a film needs motion without a big particle set
piece.
